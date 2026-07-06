from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from collections.abc import Iterable
from pathlib import Path

from .builder import MarkdownSiteBuilder, load_options
from .config import load_config_file
from .errors import Md2HtmlError
from .paths import dedupe_paths, has_private_path_part, is_ignored
from .resources import read_project_readme
from .scaffold import example_config_json, example_layout_html
from .watch import serve_and_watch

_HTML_SUFFIXES = {".html", ".htm"}
_MARKDOWN_SUFFIXES = {".md", ".markdown"}
_FILE_SUFFIXES = _HTML_SUFFIXES | _MARKDOWN_SUFFIXES


def _path_list(value) -> list[Path]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        return [Path(value)]
    return [Path(v) for v in value]


def _resolve_config_path(path: Path, base_dir: Path) -> Path:
    path = path.expanduser()
    if path.is_absolute():
        return path
    return base_dir / path


def _normalize_config_path(path: Path, cwd: Path) -> Path:
    path = path.expanduser()
    if not path.is_absolute():
        path = cwd / path
    return path.resolve(strict=False)


def _write_example(path: Path, text: str, *, force: bool = False) -> None:
    if str(path) == "-":
        print(text, end="" if text.endswith("\n") else "\n")
        return
    path = path.expanduser()
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; use --force-rebuild to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote: {path}")


def _format_path_list(paths: Iterable[Path]) -> str:
    return ", ".join(str(path.expanduser()) for path in paths)


def _output_label(output: Path | None, jobs: list[tuple[Path, Path]]) -> str:
    if output is not None:
        return str(output.expanduser())
    if not jobs:
        return str(Path.cwd())
    parents = [out.parent for _src, out in jobs]
    try:
        return os.path.commonpath([str(parent) for parent in parents])
    except ValueError:
        return str(parents[0])


def _print_build_context(input_roots: list[Path], output: Path | None, jobs: list[tuple[Path, Path]]) -> None:
    print(f"Source: {_format_path_list(input_roots)}", flush=True)
    print(f"Destination: {_output_label(output, jobs)}", flush=True)


def _format_duration(seconds: float) -> str:
    return f"{seconds:.3f} seconds"


def _explicit_output_dir(output: Path | None) -> Path | None:
    if output is None:
        return None
    # With the md2html CLI, a suffixed .html/.htm path means "single output
    # file" when there is one source. A suffixless path such as html/ or _site/
    # is an output directory and must not be watched/discovered as source.
    return output if output.suffix.lower() not in _FILE_SUFFIXES else None


def discover_sources(paths: list[Path], *, recursive: bool, exclude_dirs: Iterable[Path] = ()) -> list[Path]:
    sources: list[Path] = []
    excludes = dedupe_paths(exclude_dirs)
    for path in paths:
        path = path.expanduser()
        if is_ignored(path, excludes):
            continue
        if path.is_dir():
            pattern = "**/*.md" if recursive else "*.md"
            candidates = sorted(path.glob(pattern))
            sources.extend(src for src in candidates if src.is_file() and not is_ignored(src, excludes))
        elif path.exists():
            if not is_ignored(path, excludes):
                sources.append(path)
        else:
            raise FileNotFoundError(path)
    return sources


def _root_for(source: Path, input_roots: list[Path], *, recursive: bool) -> Path:
    dirs = [p.resolve() for p in input_roots if p.is_dir()]
    if recursive and len(dirs) == 1:
        return dirs[0]
    for root in dirs:
        try:
            source.resolve().relative_to(root.parent)
            return root.parent
        except ValueError:
            continue
    return source.parent


def build_jobs(
    sources: list[Path],
    input_roots: list[Path],
    output: Path | None,
    *,
    recursive: bool,
    output_suffix: str = ".html",
) -> list[tuple[Path, Path]]:
    if not sources:
        return []
    if output is None:
        return [(src, src.with_suffix(output_suffix)) for src in sources]
    output = output.expanduser()
    file_suffixes = _FILE_SUFFIXES | {output_suffix}
    if len(sources) == 1 and output.suffix.lower() in file_suffixes:
        return [(sources[0], output)]
    jobs: list[tuple[Path, Path]] = []
    for src in sources:
        root = _root_for(src, input_roots, recursive=recursive)
        try:
            rel = src.resolve().relative_to(root.resolve())
        except ValueError:
            rel = Path(src.name)
        jobs.append((src, output / rel.with_suffix(output_suffix)))
    return jobs


def output_exclusions(output: Path | None, sources: list[Path], jobs: list[tuple[Path, Path]]) -> tuple[list[Path], list[Path]]:
    ignored_roots: list[Path] = []
    ignored_files: list[Path] = []
    if output is not None:
        if len(sources) != 1 or output.suffix.lower() not in _FILE_SUFFIXES:
            ignored_roots.append(output)
        else:
            ignored_files.append(output)
    ignored_files.extend(out for _src, out in jobs)
    return dedupe_paths(ignored_roots), dedupe_paths(ignored_files)


def jekyll_output_root(output: Path | None, jobs: list[tuple[Path, Path]]) -> Path | None:
    if not jobs:
        return None
    if output is not None and output.suffix.lower() not in _FILE_SUFFIXES:
        return output.expanduser()
    parents = [out.parent for _src, out in jobs]
    try:
        return Path(os.path.commonpath([str(parent) for parent in parents]))
    except ValueError:
        return parents[0]


def static_output_root(output: Path | None, jobs: list[tuple[Path, Path]]) -> Path | None:
    if output is None or not jobs:
        return None
    output = output.expanduser()
    if len(jobs) == 1 and output.suffix.lower() in _FILE_SUFFIXES:
        return None
    return output


def static_copy_jobs(
    input_roots: list[Path],
    output: Path | None,
    jobs: list[tuple[Path, Path]],
    *,
    recursive: bool,
    output_mode: str,
    exclude_dirs: Iterable[Path] = (),
) -> list[tuple[Path, Path]]:
    output_root = static_output_root(output, jobs)
    if output_root is None:
        return []
    rendered_sources = {src.resolve() for src, _out in jobs}
    excludes = dedupe_paths([output_root, *exclude_dirs])
    copies: list[tuple[Path, Path]] = []

    for root in input_roots:
        root = root.expanduser()
        if not root.is_dir() or is_ignored(root, excludes):
            continue
        candidates = root.rglob("*") if recursive else root.glob("*")
        for src in sorted(candidates):
            if not src.is_file() or is_ignored(src, excludes):
                continue
            resolved = src.resolve()
            if resolved in rendered_sources:
                continue
            copy_root = _root_for(src, input_roots, recursive=recursive)
            try:
                rel = resolved.relative_to(copy_root.resolve())
            except ValueError:
                rel = Path(src.name)
            if output_mode == "html" and has_private_path_part(rel):
                continue
            dest = output_root / rel
            if resolved != dest.resolve():
                copies.append((src, dest))
    return copies


def copy_static_files(
    copies: list[tuple[Path, Path]],
    *,
    no_overwrite: bool = False,
    force_rebuild: bool = False,
) -> None:
    for src, dest in copies:
        if no_overwrite and dest.exists() and not force_rebuild:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def filter_jekyll_sources(sources: list[Path], input_roots: list[Path], *, recursive: bool) -> list[Path]:
    out: list[Path] = []
    for src in sources:
        root = _root_for(src, input_roots, recursive=recursive)
        try:
            rel = src.resolve().relative_to(root.resolve())
        except ValueError:
            rel = Path(src.name)
        if not has_private_path_part(rel):
            out.append(src)
    return out


def filter_html_sources(sources: list[Path], input_roots: list[Path], *, recursive: bool) -> list[Path]:
    out: list[Path] = []
    for src in sources:
        root = _root_for(src, input_roots, recursive=recursive)
        try:
            rel = src.resolve().relative_to(root.resolve())
        except ValueError:
            rel = Path(src.name)
        if not has_private_path_part(rel):
            out.append(src)
    return out


def watch_roots_from_inputs(input_roots: list[Path]) -> list[Path]:
    roots: list[Path] = []
    for root in input_roots:
        expanded = root.expanduser()
        if expanded.is_dir():
            roots.append(expanded)
        elif expanded.exists():
            roots.append(expanded.parent)
    return dedupe_paths(roots or [Path.cwd()])


def _config_inputs(config_path: Path) -> tuple[list[Path], Path | None, bool]:
    if not config_path.exists():
        return [], None, False
    data = load_config_file(config_path)
    raw_inputs = data.get("input", [])
    raw_output = data.get("output")
    recursive = bool(data.get("recursive", False))
    base_dir = config_path.parent
    inputs = [_resolve_config_path(path, base_dir) for path in _path_list(raw_inputs)]
    output = _resolve_config_path(Path(raw_output), base_dir) if raw_output else None
    return inputs, output, recursive


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="md2html", description="Markdown page builder with advanced article-writing features.")
    parser.add_argument("files", nargs="*", help="Markdown files or directories to process")
    parser.add_argument("-o", "--output", type=Path, help="Output file for one input or output directory for many inputs")
    parser.add_argument("-r", "--recursive", action="store_true", help="Process directories recursively")
    parser.add_argument("-w", "--watch", action="store_true", help="Start a local development server, watch inputs, and rebuild on change")
    parser.add_argument("-s", "--serve", action="store_true", help="Start a local development server, watch inputs, and rebuild on change")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Development server port (default: 8000)")
    parser.add_argument("-e", "--execute", action="store_true", help="Execute @src code embeds and refresh .out files")
    parser.add_argument("-n", "--no-overwrite", action="store_true", help="Do not overwrite existing files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print diagnostics and built files")
    parser.add_argument("-f", "--force-rebuild", action="store_true", help="Force rebuild even if outputs exist")
    parser.add_argument("--dry-run", action="store_true", help="Print build DAG as JSON without writing files")
    parser.add_argument("--templates", type=Path, help="Templates directory")
    parser.add_argument("--config", type=Path, help="Configuration file (default: ./md2html.json when present)")
    parser.add_argument("--format", choices=["html", "jekyll"], dest="output_mode", help="Output mode")
    parser.add_argument("--strict", action="store_true", help="Treat missing includes/sources as errors")
    parser.add_argument("--readme", action="store_true", help="Print the full README and exit")
    parser.add_argument(
        "--example-config",
        nargs="?",
        const=Path("md2html.json"),
        type=Path,
        metavar="PATH",
        help="Write an example config file and exit (default: md2html.json; use - for stdout)",
    )
    parser.add_argument(
        "--example-layout",
        nargs="?",
        const=Path("templates/page.html"),
        type=Path,
        metavar="PATH",
        help="Write an example layout with inline page and feature CSS and exit (default: templates/page.html; use - for stdout)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.readme:
        try:
            text = read_project_readme()
        except OSError as exc:
            print(f"md2html: error: could not read README: {exc}", file=sys.stderr)
            return 2
        print(text, end="" if text.endswith("\n") else "\n")
        return 0
    if args.example_config is not None or args.example_layout is not None:
        try:
            if args.example_config is not None:
                _write_example(args.example_config, example_config_json(), force=args.force_rebuild)
            if args.example_layout is not None:
                _write_example(args.example_layout, example_layout_html(), force=args.force_rebuild)
        except OSError as exc:
            print(f"md2html: error: {exc}", file=sys.stderr)
            return 2
        return 0

    cwd = Path.cwd()
    config_path = _normalize_config_path(args.config or (cwd / "md2html.json"), cwd)
    if args.config and not config_path.exists():
        print(f"md2html: error: configuration file does not exist: {config_path}", file=sys.stderr)
        return 2
    config_inputs, config_output, config_recursive = _config_inputs(config_path)

    input_roots = [Path(p) for p in args.files] if args.files else config_inputs
    using_default_input = not input_roots
    if using_default_input and not config_path.exists():
        config_recursive = False
    recursive = args.recursive or config_recursive
    output = args.output or config_output

    overrides = {}
    if args.execute:
        overrides["execute"] = True
    if args.no_overwrite:
        overrides["no_overwrite"] = True
    if args.verbose:
        overrides["verbose"] = True
    if args.force_rebuild:
        overrides["force_rebuild"] = True
    if args.strict:
        overrides["strict"] = True
    if args.templates:
        overrides["template_dirs"] = [str(args.templates)]
    if args.output_mode:
        overrides["output_mode"] = args.output_mode

    try:
        options = load_options(cwd, config_path if config_path.exists() else None, overrides)
        if using_default_input:
            input_roots = [options.project_root]
        builder = MarkdownSiteBuilder(options)

        pre_excludes = []
        explicit_dir = _explicit_output_dir(output)
        if explicit_dir is not None:
            pre_excludes.append(explicit_dir)
        pre_excludes = dedupe_paths(pre_excludes)
        output_suffix = ".md" if options.output_mode == "jekyll" else ".html"

        def discover_and_pair(exclude_dirs: list[Path]) -> tuple[list[Path], list[tuple[Path, Path]]]:
            current_sources = discover_sources(input_roots, recursive=recursive, exclude_dirs=exclude_dirs)
            if options.output_mode == "jekyll":
                current_sources = filter_jekyll_sources(current_sources, input_roots, recursive=recursive)
            else:
                current_sources = filter_html_sources(current_sources, input_roots, recursive=recursive)
            current_jobs = build_jobs(current_sources, input_roots, output, recursive=recursive, output_suffix=output_suffix)
            return current_sources, current_jobs

        def plan_jobs() -> tuple[list[tuple[Path, Path]], list[Path], list[Path]]:
            current_sources, current_jobs = discover_and_pair(pre_excludes)
            ignored_roots, ignored_files = output_exclusions(output, current_sources, current_jobs)
            if any(root not in pre_excludes for root in ignored_roots):
                # Handles the edge case where multiple inputs make an .html-looking
                # output path behave like a directory.
                current_sources, current_jobs = discover_and_pair(ignored_roots)
                ignored_roots, ignored_files = output_exclusions(output, current_sources, current_jobs)
            return current_jobs, ignored_roots, ignored_files

        def make_jobs() -> list[tuple[Path, Path]]:
            return plan_jobs()[0]

        def copy_static_for(current_jobs: list[tuple[Path, Path]]) -> None:
            if not options.copy_assets:
                return
            static_copies = static_copy_jobs(
                input_roots,
                output,
                current_jobs,
                recursive=recursive,
                output_mode=options.output_mode,
                exclude_dirs=ignored_roots,
            )
            copy_static_files(
                static_copies,
                no_overwrite=options.no_overwrite,
                force_rebuild=options.force_rebuild,
            )

        jobs, ignored_roots, ignored_files = plan_jobs()
        if options.output_mode == "jekyll":
            options.jekyll_output_root = jekyll_output_root(output, jobs)

        if args.dry_run:
            print(builder.dry_run_json(jobs))
            return 0
        if args.watch or args.serve:
            _print_build_context(input_roots, output, jobs)
            if options.output_mode == "jekyll" and options.jekyll_output_root is not None:
                builder.write_jekyll_assets(options.jekyll_output_root)
            serve_and_watch(
                builder,
                jobs,
                job_provider=make_jobs,
                static_copier=copy_static_for if options.copy_assets else None,
                watch_roots=watch_roots_from_inputs(input_roots),
                ignored_roots=ignored_roots,
                ignored_files=ignored_files,
                port=args.port,
                verbose=args.verbose,
            )
            return 0
        _print_build_context(input_roots, output, jobs)
        print("Generating...", flush=True)
        start = time.perf_counter()
        failures = 0
        built = 0
        skipped = 0
        for src, out in jobs:
            result = builder.build_file(src, out)
            if result.skipped:
                skipped += 1
            else:
                built += 1
            for diagnostic in result.diagnostics:
                print(diagnostic.format(), file=sys.stderr)
                if diagnostic.level == "error":
                    failures += 1
            if args.verbose or options.verbose:
                action = "skipped" if result.skipped else "built"
                print(f"{action}: {src} -> {out}")
        if options.output_mode == "jekyll" and options.jekyll_output_root is not None and failures == 0:
            builder.write_jekyll_assets(options.jekyll_output_root)
        if failures == 0 and options.copy_assets:
            copy_static_for(jobs)
        elapsed = time.perf_counter() - start
        if failures:
            print(f"finished with {failures} error{'s' if failures != 1 else ''} in {_format_duration(elapsed)}.", flush=True)
        else:
            print(f"done in {_format_duration(elapsed)}.", flush=True)
            if not jobs:
                print("No pages found.", flush=True)
            elif skipped:
                print(f"Built {built} page{'s' if built != 1 else ''}; {skipped} unchanged.", flush=True)
            else:
                print(f"Built {built} page{'s' if built != 1 else ''}.", flush=True)
        return 1 if failures else 0
    except (Md2HtmlError, OSError, FileNotFoundError, RuntimeError) as exc:
        print(f"md2html: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
