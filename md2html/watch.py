from __future__ import annotations

import functools
import http.server
import contextlib
import errno
import socketserver
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from .builder import MarkdownSiteBuilder
from .errors import Md2HtmlError
from .graph import build_dependency_graph
from .paths import dedupe_paths, is_relative_to, resolve_lenient, source_output_path

Job = tuple[Path, Path]
JobProvider = Callable[[], list[Job]]
StaticCopier = Callable[[list[Job]], None]

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


def _prune_nested_roots(paths: Iterable[Path]) -> list[Path]:
    roots = sorted(dedupe_paths(paths), key=lambda p: (len(p.parts), str(p)))
    pruned: list[Path] = []
    for root in roots:
        if any(is_relative_to(root, existing) for existing in pruned):
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
            ignored_files=tuple(dedupe_paths(files)),
            ignored_suffixes=tuple(s for s in suffixes if s),
        )

    def ignores(self, raw_path: str | Path | None) -> bool:
        if raw_path is None:
            return False
        path = resolve_lenient(Path(raw_path))
        if any(part in _IGNORED_DIR_NAMES for part in path.parts):
            return True
        if any(str(path).endswith(suffix) for suffix in self.ignored_suffixes):
            return True
        if any(path == file for file in self.ignored_files):
            return True
        return any(is_relative_to(path, root) for root in self.ignored_roots)


class _ChangeBuffer:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._paths: set[Path] = set()

    def add_many(self, paths: Iterable[str | Path | None]) -> None:
        with self._lock:
            for raw_path in paths:
                if raw_path is not None:
                    self._paths.add(resolve_lenient(Path(raw_path)))

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


def _dependency_is_newer_than_output(dependency: Path, output: Path) -> bool:
    if not dependency.exists():
        return True
    try:
        return dependency.stat().st_mtime > output.stat().st_mtime
    except OSError:
        return True


def _generated_output_is_stale(source: Path, dependencies: set[Path], builder: MarkdownSiteBuilder) -> bool:
    if not builder.options.execute:
        return False
    generated = source_output_path(source, builder.options.code.output_suffix)
    if generated not in dependencies:
        return False
    if not generated.exists():
        return True
    try:
        return source.exists() and source.stat().st_mtime > generated.stat().st_mtime
    except OSError:
        return True


def _job_needs_build(builder: MarkdownSiteBuilder, job: Job, dependencies: set[Path]) -> bool:
    source, output = (resolve_lenient(job[0]), resolve_lenient(job[1]))
    if builder.options.force_rebuild or not output.exists():
        return True
    for dependency in dependencies:
        if _dependency_is_newer_than_output(dependency, output):
            return True
        if _generated_output_is_stale(dependency, dependencies, builder):
            return True
    return False


def _jobs_needing_build(builder: MarkdownSiteBuilder, jobs: list[Job]) -> tuple[list[Job], int]:
    graph = build_dependency_graph(jobs, builder.options)
    stale: list[Job] = []
    for source, output in jobs:
        dependencies = graph.dependencies_by_page.get(resolve_lenient(source), {resolve_lenient(source)})
        if _job_needs_build(builder, (source, output), dependencies):
            stale.append((source, output))
    return stale, len(jobs) - len(stale)


def _plural(count: int, singular: str, plural: str | None = None) -> str:
    return singular if count == 1 else plural or f"{singular}s"


def _initial_build_message(built: int, skipped: int) -> str:
    total = built + skipped
    if total == 0:
        return "No pages found."
    if built == 0:
        return f"Site is already up to date ({total} {_plural(total, 'page')})."
    if skipped == 0:
        return f"Built {built} {_plural(built, 'page')}."
    return f"Built {built} {_plural(built, 'page')}; {skipped} unchanged."


def _rebuild_message(count: int) -> str:
    if count == 0:
        return "Change detected, no pages needed rebuilding."
    return f"Regenerated {count} {_plural(count, 'page')}."


def _initial_build(builder: MarkdownSiteBuilder, jobs: list[Job], *, verbose: bool = False) -> None:
    stale_jobs, up_to_date = _jobs_needing_build(builder, jobs)
    _build_all(builder, stale_jobs, verbose=verbose)
    print(_initial_build_message(len(stale_jobs), up_to_date), flush=True)


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


class _ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def local_server_url(port: int, *, host: str = "127.0.0.1") -> str:
    return f"http://{host}:{port}/"


def _watch_root_message(roots: Iterable[Path], exclusions: WatchExclusions) -> str:
    watched = ", ".join(str(root) for root in roots if not exclusions.ignores(root))
    return f"Watching for changes in {watched}"


def _stop_observer(observer) -> None:  # type: ignore[no-untyped-def]
    with contextlib.suppress(RuntimeError):
        observer.stop()
    try:
        observer.join()
    except RuntimeError as exc:
        if "release unlocked lock" not in str(exc):
            raise


def _make_http_server(handler, port: int):  # type: ignore[no-untyped-def]
    try:
        return _ReusableTCPServer(("", port), handler)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            raise RuntimeError(f"port {port} is already in use") from exc
        raise


def watch_jobs(
    builder: MarkdownSiteBuilder,
    jobs: list[Job],
    *,
    job_provider: JobProvider | None = None,
    static_copier: StaticCopier | None = None,
    watch_roots: Iterable[Path] | None = None,
    ignored_roots: Iterable[Path] = (),
    ignored_files: Iterable[Path] = (),
    verbose: bool = False,
    debounce: float = 0.25,
    initial_build: bool = True,
) -> None:
    """Watch source trees and rebuild affected pages.

    The dependency model is intentionally small: Markdown include edges and
    article-level source/output edges. It is not a general language build DAG.
    """

    current_jobs = job_provider() if job_provider else jobs
    if initial_build:
        _initial_build(builder, current_jobs, verbose=verbose)
        if static_copier is not None:
            static_copier(current_jobs)

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
    print(_watch_root_message(roots, exclusions), flush=True)
    ignored = ", ".join(str(root) for root in exclusions.ignored_roots)
    if ignored and verbose:
        print(f"ignoring generated output under: {ignored}", flush=True)

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
            print(_rebuild_message(len(jobs_to_build)), flush=True)
            if verbose:
                changed = ", ".join(str(path) for path in changed_paths)
                print(f"changed: {changed}")
            _build_all(builder, jobs_to_build, verbose=verbose)
            if static_copier is not None:
                static_copier(current_jobs)
    except KeyboardInterrupt:
        return
    finally:
        _stop_observer(observer)


def serve_and_watch(
    builder: MarkdownSiteBuilder,
    jobs: list[Job],
    *,
    job_provider: JobProvider | None = None,
    static_copier: StaticCopier | None = None,
    watch_roots: Iterable[Path] | None = None,
    ignored_roots: Iterable[Path] = (),
    ignored_files: Iterable[Path] = (),
    port: int = 8000,
    verbose: bool = False,
) -> None:
    current_jobs = job_provider() if job_provider else jobs
    _initial_build(builder, current_jobs, verbose=verbose)
    if static_copier is not None:
        static_copier(current_jobs)

    output_dirs = {out.parent.resolve() for _src, out in current_jobs}
    serve_dir = sorted(output_dirs, key=lambda p: len(str(p)))[0] if output_dirs else Path.cwd()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(serve_dir))
    httpd = _make_http_server(handler, port)
    with httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        print(f"Server running at {local_server_url(port)}", flush=True)
        print("Press Ctrl+C to stop.", flush=True)
        try:
            watch_jobs(
                builder,
                jobs,
                job_provider=job_provider,
                static_copier=static_copier,
                watch_roots=watch_roots,
                ignored_roots=ignored_roots,
                ignored_files=ignored_files,
                verbose=verbose,
                initial_build=False,
            )
        finally:
            httpd.shutdown()
