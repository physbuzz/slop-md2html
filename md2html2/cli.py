"""Command-line interface, rebuilding, and local preview."""

from __future__ import annotations

import argparse
from dataclasses import replace
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import metadata
from importlib.resources import files
from pathlib import Path
import sys
import threading
import time
from typing import Iterable

from . import __version__
from .project import BuildResult, Project
from .settings import EXAMPLE_CONFIG, EXAMPLE_JSON, MathSettings, Settings, find_config, load_settings


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="md2html",
        description="Build an excellent standalone page or a native Markdown website.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  md2html article.md
  md2html -es article.md
  md2html -erf notes -o html
  md2html --config md2html.config --serve
  md2html --example-template templates/page.html
""",
    )
    result.add_argument("input", nargs="?", type=Path, help="Markdown file or source directory")
    result.add_argument("-o", "--output", type=Path, help="output file or directory")
    result.add_argument("-e", "--execute", action="store_true", help="run executable @src content and show its output")
    result.add_argument("-r", "--recursive", action="store_true", help="render Markdown in subdirectories")
    result.add_argument("-f", "--regenerate", action="store_true", help="rerun executable content instead of using fresh results")
    result.add_argument("-s", "--serve", action="store_true", help="serve the output and rebuild when source files change")
    result.add_argument("-w", "--watch", action="store_true", help="rebuild when source files change without starting a server")
    result.add_argument("--port", type=int, default=8000, help="preview server port (default: 8000)")
    result.add_argument("--config", type=Path, help="configuration file; relative paths inside it are resolved from that file")
    result.add_argument("--output-mode", choices=("pages", "site"), help="build independent pages or a native static site")
    result.add_argument("--templates", type=Path, help="directory searched before built-in templates")
    result.add_argument("--template", help="standalone HTML template name or path")
    result.add_argument("--css", action="append", help="CSS file to embed; repeat to combine files")
    result.add_argument("--no-css", action="store_true", help="do not embed CSS in standalone pages")
    result.add_argument("--math", choices=("mathjax", "mathjax-chtml", "svg", "mathml", "raw"), help="math rendering backend")
    result.add_argument("--math-fonts", choices=("auto", "all", "inline", "remote", "none"), help="CHTML font asset mode (default: auto)")
    result.add_argument("--clean", action="store_true", help="remove a site output directory before building")
    result.add_argument("--readme", action="store_true", help="print the complete installed README")
    result.add_argument("--example-config", nargs="?", const="md2html.config", metavar="PATH", help="write a documented starter config; use - for stdout")
    result.add_argument("--example-json", nargs="?", const="md2html.json", metavar="PATH", help="write a starter JSON config; use - for stdout")
    result.add_argument("--example-template", nargs="?", const="templates/page.html", metavar="PATH", help="write the default page template; use - for stdout")
    result.add_argument("--example-css", nargs="?", const="templates/page.css", metavar="PATH", help="write the default page CSS; use - for stdout")
    result.add_argument("--force", action="store_true", help="replace an existing example file")
    result.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return result


def _resource(name: str) -> str:
    return files("md2html2").joinpath(name).read_text(encoding="utf-8")


def _write_example(value: str, destination: str, force: bool) -> int:
    if destination == "-":
        print(value, end="" if value.endswith("\n") else "\n")
        return 0
    path = Path(destination).expanduser()
    if path.exists() and not force:
        print(f"error: {path} already exists; use --force to replace it", file=sys.stderr)
        return 2
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    print(f"wrote {path}")
    return 0


def settings_from_args(args: argparse.Namespace) -> Settings:
    config = args.config.resolve() if args.config else None
    if config is None and args.input is None:
        config = find_config(Path.cwd())
        if config is None:
            raise ValueError("give a Markdown file, a directory, or --config")
    elif config is None and args.input and args.input.is_dir():
        config = find_config(args.input.resolve())
    if config:
        if not config.is_file():
            raise ValueError(f"configuration does not exist: {config}")
        settings = load_settings(config)
        if args.input is not None:
            settings = replace(settings, input=args.input.expanduser().resolve())
    else:
        source = args.input.expanduser().resolve()
        if source.is_file():
            output = args.output.expanduser().resolve() if args.output else None
            if output and output.is_dir():
                output = output / source.with_suffix(".html").name
            settings = Settings.single(source, output)
        else:
            output = (args.output or Path("html")).expanduser().resolve()
            settings = Settings(input=source, output=output, project_root=source, recursive=args.recursive)
    changes = {}
    if args.output is not None and not (args.input and args.input.is_file() and not config):
        changes["output"] = args.output.expanduser().resolve()
    if args.output_mode:
        changes["output_mode"] = args.output_mode
    if args.templates:
        changes["templates"] = args.templates.expanduser().resolve()
    if args.template:
        changes["template"] = args.template
    if args.css is not None:
        changes["css"] = tuple(args.css)
    if args.no_css:
        changes["css"] = ()
    if args.math:
        changes["math"] = replace(settings.math, backend=args.math)
    if args.math_fonts:
        changes["math"] = replace(changes.get("math", settings.math), chtml_fonts=args.math_fonts)
    if args.execute:
        changes["execute"] = True
    if args.regenerate:
        changes["regenerate"] = True
    if args.recursive:
        changes["recursive"] = True
    if args.clean:
        changes["clean"] = True
    return replace(settings, **changes)


def describe(result: BuildResult) -> None:
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    noun = "file" if result.output_count == 1 else "files"
    print(f"built {result.output_count} {noun}")


def _snapshot(settings: Settings, dependencies: Iterable[Path]) -> dict[Path, int]:
    paths = set(dependencies)
    if settings.input.is_file():
        paths.add(settings.input)
    else:
        for path in settings.input.rglob("*"):
            if path.is_file() and not path.is_relative_to(settings.output) and ".md2html-cache" not in path.parts:
                paths.add(path)
    snapshot: dict[Path, int] = {}
    for path in paths:
        try:
            snapshot[path] = path.stat().st_mtime_ns
        except OSError:
            snapshot[path] = -1
    return snapshot


def _server(root: Path, port: int) -> tuple[ThreadingHTTPServer, threading.Thread]:
    class QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *values, **keywords):
            super().__init__(*values, directory=str(root), **keywords)

        def log_message(self, format: str, *args) -> None:
            print(f"request: {format % args}")

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
    except OSError as error:
        raise ValueError(f"could not start preview on port {port}: {error}") from error
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def watch(settings: Settings, *, serve: bool, port: int) -> int:
    result = Project(settings).build()
    describe(result)
    server = None
    if serve:
        root = settings.output if settings.input.is_dir() else settings.output.parent
        server, _ = _server(root, port)
        path = "/" if settings.input.is_dir() else "/" + settings.output.name
        print(f"preview: http://127.0.0.1:{port}{path}")
    print(f"watching {settings.input}")
    previous = _snapshot(settings, result.dependencies)
    try:
        while True:
            time.sleep(.35)
            current = _snapshot(settings, result.dependencies)
            if current == previous:
                continue
            changed = sorted(str(path) for path in set(current) | set(previous) if current.get(path) != previous.get(path))
            print(f"change: {changed[0] if changed else settings.input}")
            try:
                result = Project(settings).build()
                describe(result)
            except (OSError, ValueError) as error:
                print(f"error: {error}", file=sys.stderr)
            previous = _snapshot(settings, result.dependencies)
    except KeyboardInterrupt:
        print("stopped")
    finally:
        if server:
            server.shutdown()
            server.server_close()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.readme:
        print(metadata("md2html2").get_payload(), end="")
        return 0
    if args.example_config is not None:
        return _write_example(EXAMPLE_CONFIG, args.example_config, args.force)
    if args.example_json is not None:
        return _write_example(EXAMPLE_JSON, args.example_json, args.force)
    if args.example_template is not None:
        return _write_example(_resource("default_templates/page.html"), args.example_template, args.force)
    if args.example_css is not None:
        return _write_example(_resource("assets/page.css"), args.example_css, args.force)
    try:
        settings = settings_from_args(args)
        if args.serve or args.watch:
            return watch(settings, serve=args.serve, port=args.port)
        describe(Project(settings).build())
        return 0
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
