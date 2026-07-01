from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Iterable
from pathlib import Path

from .builder import MarkdownSiteBuilder, load_options
from .config import load_config_file
from .errors import Md2HtmlError
from .paths import dedupe_paths, has_private_path_part, is_ignored
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
    raw_inputs = data.get("files", data.get("inputs", data.get("input", [])))
    raw_output = data.get("output")
    recursive = bool(data.get("recursive", False))
    return _path_list(raw_inputs), Path(raw_output) if raw_output else None, recursive


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="md2html", description="Markdown page builder with advanced article-writing features.")
    parser.add_argument("files", nargs="*", help="Markdown files or directories to process")
    parser.add_argument("-o", "--output", type=Path, help="Output file for one input or output directory for many inputs")
    parser.add_argument("-r", "--recursive", action="store_true", help="Process directories recursively")
    parser.add_argument("-w", "--watch", action="store_true", help="Start a local development server, watch inputs, and rebuild on change")
    parser.add_argument("-s", "--serve", action="store_true", help="Alias for --watch")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    cwd = Path.cwd()
    config_path = args.config or (cwd / "md2html.json")
    config_inputs, config_output, config_recursive = _config_inputs(config_path)

    input_roots = [Path(p) for p in args.files] if args.files else config_inputs
    if not input_roots:
        input_roots = [cwd]
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
        builder = MarkdownSiteBuilder(options)

        pre_excludes = []
        explicit_dir = _explicit_output_dir(output)
        if explicit_dir is not None:
            pre_excludes.append(explicit_dir)
        pre_excludes = dedupe_paths(pre_excludes)
        output_suffix = ".md" if options.output_mode == "jekyll" else ".html"

        def make_jobs() -> list[tuple[Path, Path]]:
            current_sources = discover_sources(input_roots, recursive=recursive, exclude_dirs=pre_excludes)
            if options.output_mode == "jekyll":
                current_sources = filter_jekyll_sources(current_sources, input_roots, recursive=recursive)
            current_jobs = build_jobs(current_sources, input_roots, output, recursive=recursive, output_suffix=output_suffix)
            ignored_roots, _ignored_files = output_exclusions(output, current_sources, current_jobs)
            if any(root not in pre_excludes for root in ignored_roots):
                # Handles the edge case where multiple inputs make an .html-looking
                # output path behave like a directory.
                current_sources = discover_sources(input_roots, recursive=recursive, exclude_dirs=ignored_roots)
                if options.output_mode == "jekyll":
                    current_sources = filter_jekyll_sources(current_sources, input_roots, recursive=recursive)
                current_jobs = build_jobs(current_sources, input_roots, output, recursive=recursive, output_suffix=output_suffix)
            return current_jobs

        sources = discover_sources(input_roots, recursive=recursive, exclude_dirs=pre_excludes)
        if options.output_mode == "jekyll":
            sources = filter_jekyll_sources(sources, input_roots, recursive=recursive)
        jobs = build_jobs(sources, input_roots, output, recursive=recursive, output_suffix=output_suffix)
        ignored_roots, ignored_files = output_exclusions(output, sources, jobs)
        if ignored_roots != pre_excludes:
            sources = discover_sources(input_roots, recursive=recursive, exclude_dirs=ignored_roots)
            if options.output_mode == "jekyll":
                sources = filter_jekyll_sources(sources, input_roots, recursive=recursive)
            jobs = build_jobs(sources, input_roots, output, recursive=recursive, output_suffix=output_suffix)
            ignored_roots, ignored_files = output_exclusions(output, sources, jobs)
        if options.output_mode == "jekyll":
            options.jekyll_output_root = jekyll_output_root(output, jobs)

        if args.dry_run:
            print(builder.dry_run_json(jobs))
            return 0
        if args.watch or args.serve:
            if options.output_mode == "jekyll" and options.jekyll_output_root is not None:
                builder.write_jekyll_assets(options.jekyll_output_root)
            serve_and_watch(
                builder,
                jobs,
                job_provider=make_jobs,
                watch_roots=watch_roots_from_inputs(input_roots),
                ignored_roots=ignored_roots,
                ignored_files=ignored_files,
                port=args.port,
                verbose=args.verbose,
            )
            return 0
        failures = 0
        for src, out in jobs:
            result = builder.build_file(src, out)
            for diagnostic in result.diagnostics:
                print(diagnostic.format(), file=sys.stderr)
                if diagnostic.level == "error":
                    failures += 1
            if args.verbose or options.verbose:
                action = "skipped" if result.skipped else "built"
                print(f"{action}: {src} -> {out}")
        if options.output_mode == "jekyll" and options.jekyll_output_root is not None and failures == 0:
            builder.write_jekyll_assets(options.jekyll_output_root)
        return 1 if failures else 0
    except (Md2HtmlError, OSError, FileNotFoundError, RuntimeError) as exc:
        print(f"md2html: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
