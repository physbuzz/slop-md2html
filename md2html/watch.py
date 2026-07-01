from __future__ import annotations

import functools
import http.server
import socketserver
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from .builder import MarkdownSiteBuilder
from .errors import Md2HtmlError
from .graph import build_dependency_graph

Job = tuple[Path, Path]
JobProvider = Callable[[], list[Job]]

_IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}


def _resolve_lenient(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        resolved = _resolve_lenient(path)
        if resolved not in seen:
            out.append(resolved)
            seen.add(resolved)
    return out


def _prune_nested_roots(paths: Iterable[Path]) -> list[Path]:
    roots = sorted(_dedupe_paths(paths), key=lambda p: (len(p.parts), str(p)))
    pruned: list[Path] = []
    for root in roots:
        if any(_is_relative_to(root, existing) for existing in pruned):
            continue
        pruned.append(root)
    return pruned


@dataclass(frozen=True)
class WatchExclusions:
    ignored_roots: tuple[Path, ...] = ()
    ignored_files: tuple[Path, ...] = ()
    ignored_suffixes: tuple[str, ...] = ()

    @classmethod
    def from_paths(
        cls,
        *,
        roots: Iterable[Path] = (),
        files: Iterable[Path] = (),
        suffixes: Iterable[str] = (),
    ) -> "WatchExclusions":
        return cls(
            ignored_roots=tuple(_prune_nested_roots(roots)),
            ignored_files=tuple(_dedupe_paths(files)),
            ignored_suffixes=tuple(s for s in suffixes if s),
        )

    def ignores(self, raw_path: str | Path | None) -> bool:
        if raw_path is None:
            return False
        path = _resolve_lenient(Path(raw_path))
        if any(part in _IGNORED_DIR_NAMES for part in path.parts):
            return True
        if any(str(path).endswith(suffix) for suffix in self.ignored_suffixes):
            return True
        if any(path == file for file in self.ignored_files):
            return True
        return any(_is_relative_to(path, root) for root in self.ignored_roots)


class _ChangeBuffer:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._paths: set[Path] = set()

    def add_many(self, paths: Iterable[str | Path | None]) -> None:
        with self._lock:
            for raw_path in paths:
                if raw_path is not None:
                    self._paths.add(_resolve_lenient(Path(raw_path)))

    def pop_all(self) -> list[Path]:
        with self._lock:
            paths = sorted(self._paths, key=lambda p: str(p))
            self._paths.clear()
            return paths


class _ExclusionState:
    def __init__(self, exclusions: WatchExclusions) -> None:
        self._lock = threading.Lock()
        self._exclusions = exclusions

    def update(self, exclusions: WatchExclusions) -> None:
        with self._lock:
            self._exclusions = exclusions

    def ignores(self, path: str | Path | None) -> bool:
        with self._lock:
            return self._exclusions.ignores(path)


def plan_affected_jobs(builder: MarkdownSiteBuilder, jobs: list[Job], changed_paths: Iterable[Path]) -> list[Job]:
    graph = build_dependency_graph(jobs, builder.options)
    return graph.affected_jobs(changed_paths)


class _RebuildSignalHandler:
    def __new__(cls, signal: threading.Event, exclusions: _ExclusionState, changes: _ChangeBuffer):
        try:
            from watchdog.events import FileSystemEventHandler
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError("watch mode requires the 'watchdog' package; run `python -m pip install -e \".[dev]\"`") from exc

        class Handler(FileSystemEventHandler):  # type: ignore[misc]
            def on_any_event(self, event):  # type: ignore[no-untyped-def]
                if event.event_type in {"opened", "closed_no_write"}:
                    return
                paths = [getattr(event, "src_path", None), getattr(event, "dest_path", None)]
                interesting_paths = [path for path in paths if path and not exclusions.ignores(path)]
                if not interesting_paths:
                    return
                changes.add_many(interesting_paths)
                signal.set()

        return Handler()


def _build_all(builder: MarkdownSiteBuilder, jobs: list[Job], *, verbose: bool = False) -> None:
    for src, out in jobs:
        result = builder.build_file(src, out)
        if verbose:
            print(f"built: {src} -> {out}")
        for diagnostic in result.diagnostics:
            print(diagnostic.format())


def _dependencies_from_dry_run(builder: MarkdownSiteBuilder, jobs: list[Job]) -> set[Path]:
    dependencies: set[Path] = set()
    for src, out in jobs:
        try:
            result = builder.build_file(src, out, dry_run=True)
            dependencies.update(result.dependencies)
            dependencies.update(src for src, _rel in result.assets)
        except Exception:
            dependencies.add(src)
    return dependencies


def _planned_generated_code_outputs(builder: MarkdownSiteBuilder, jobs: list[Job]) -> list[Path]:
    if not builder.options.execute:
        return []
    suffix = builder.options.code.output_suffix
    return [dep for dep in _dependencies_from_dry_run(builder, jobs) if str(dep).endswith(suffix)]


def _watch_roots_from_jobs(builder: MarkdownSiteBuilder, jobs: list[Job]) -> list[Path]:
    roots: set[Path] = set()
    for src, _out in jobs:
        roots.add(src.parent if src.is_file() else src)
    roots.update(path.parent for path in _dependencies_from_dry_run(builder, jobs) if path.suffix)
    roots.add(builder.options.project_root)
    return _prune_nested_roots(root for root in roots if root.exists())


def _make_observer():
    try:
        from watchdog.observers import Observer
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("watch mode requires the 'watchdog' package; run `python -m pip install -e \".[dev]\"`") from exc
    return Observer()


def watch_jobs(
    builder: MarkdownSiteBuilder,
    jobs: list[Job],
    *,
    job_provider: JobProvider | None = None,
    watch_roots: Iterable[Path] | None = None,
    ignored_roots: Iterable[Path] = (),
    ignored_files: Iterable[Path] = (),
    verbose: bool = False,
    debounce: float = 0.25,
) -> None:
    """Watch source trees with watchdog and rebuild affected pages.

    The dependency model is intentionally small: Markdown include edges and
    article-level source/output edges. It is not a general language build DAG.
    """

    current_jobs = job_provider() if job_provider else jobs
    _build_all(builder, current_jobs, verbose=verbose)

    roots = _prune_nested_roots([*(watch_roots or []), *_watch_roots_from_jobs(builder, current_jobs)])
    base_ignored_roots = list(ignored_roots)
    base_ignored_files = list(ignored_files)

    def make_exclusions(active_jobs: list[Job]) -> WatchExclusions:
        generated_outputs = [out for _src, out in active_jobs]
        generated_outputs.extend(_planned_generated_code_outputs(builder, active_jobs))
        ignored_suffixes = [builder.options.code.output_suffix] if builder.options.execute else []
        return WatchExclusions.from_paths(
            roots=base_ignored_roots,
            files=[*base_ignored_files, *generated_outputs],
            suffixes=ignored_suffixes,
        )

    exclusions = make_exclusions(current_jobs)
    exclusion_state = _ExclusionState(exclusions)
    changes = _ChangeBuffer()
    signal = threading.Event()
    handler = _RebuildSignalHandler(signal, exclusion_state, changes)
    observer = _make_observer()

    scheduled = 0
    for root in roots:
        if exclusions.ignores(root):
            continue
        if root.exists():
            observer.schedule(handler, str(root), recursive=True)
            scheduled += 1

    if scheduled == 0:
        raise RuntimeError("no watchable roots found")

    observer.start()
    if verbose:
        watched = ", ".join(str(root) for root in roots if not exclusions.ignores(root))
        ignored = ", ".join(str(root) for root in exclusions.ignored_roots)
        print(f"watching with watchdog: {watched}")
        if ignored:
            print(f"ignoring generated output under: {ignored}")

    try:
        while True:
            signal.wait()
            time.sleep(debounce)
            signal.clear()
            changed_paths = changes.pop_all()
            current_jobs = job_provider() if job_provider else jobs
            exclusion_state.update(make_exclusions(current_jobs))
            try:
                jobs_to_build = plan_affected_jobs(builder, current_jobs, changed_paths)
            except Md2HtmlError as exc:
                print(f"ERROR: {exc}")
                continue
            if verbose:
                changed = ", ".join(str(path) for path in changed_paths)
                print(f"changed: {changed}")
                print(f"rebuilding {len(jobs_to_build)} affected page(s)" if jobs_to_build else "no md2html page dependencies matched this change")
            _build_all(builder, jobs_to_build, verbose=verbose)
    except KeyboardInterrupt:
        return
    finally:
        observer.stop()
        observer.join()


def serve_and_watch(
    builder: MarkdownSiteBuilder,
    jobs: list[Job],
    *,
    job_provider: JobProvider | None = None,
    watch_roots: Iterable[Path] | None = None,
    ignored_roots: Iterable[Path] = (),
    ignored_files: Iterable[Path] = (),
    port: int = 8000,
    verbose: bool = False,
) -> None:
    output_dirs = {out.parent.resolve() for _src, out in jobs}
    serve_dir = sorted(output_dirs, key=lambda p: len(str(p)))[0] if output_dirs else Path.cwd()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(serve_dir))
    with socketserver.TCPServer(("", port), handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        print(f"serving {serve_dir} at http://localhost:{port}/")
        try:
            watch_jobs(
                builder,
                jobs,
                job_provider=job_provider,
                watch_roots=watch_roots,
                ignored_roots=ignored_roots,
                ignored_files=ignored_files,
                verbose=verbose,
            )
        finally:
            httpd.shutdown()
