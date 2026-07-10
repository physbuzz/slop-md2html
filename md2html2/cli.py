"""Command-line interface, rebuilding, and local preview."""

from __future__ import annotations

import argparse
from dataclasses import replace
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import metadata
from importlib.resources import files
from pathlib import Path
from queue import Empty, SimpleQueue
import shutil
import sys
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import __version__
from .project import BuildResult, Project
from .settings import EXAMPLE_CONFIG, EXAMPLE_JSON, MathSettings, Settings, find_config, load_settings, normal_path

PAGE_CSS = (
    "page-base.css", "feature-syntax.css", "feature-code.css", "feature-math.css",
    "feature-toc.css", "feature-image.css", "feature-warning.css",
)


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
    result.add_argument("-f", "--force", action="store_true", help="rerun executable content or replace an existing example file")
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
    config = normal_path(args.config) if args.config else None
    if config is None and args.input is None:
        config = find_config(Path("."))
        if config is None:
            raise ValueError("give a Markdown file, a directory, or --config")
    elif config is None and args.input and args.input.is_dir():
        config = find_config(normal_path(args.input))
    if config:
        if not config.is_file():
            raise ValueError(f"configuration does not exist: {config}")
        settings = load_settings(config)
        if args.input is not None:
            settings = replace(settings, input=normal_path(args.input))
    else:
        source = normal_path(args.input)
        if source.is_file():
            output = normal_path(args.output) if args.output else None
            if output and output.is_dir():
                output = output / source.with_suffix(".html").name
            settings = Settings.single(source, output)
        else:
            output = normal_path(args.output or Path("html"))
            settings = Settings(input=source, output=output, project_root=source, recursive=args.recursive)
    changes = {}
    if args.output is not None and not (args.input and args.input.is_file() and not config):
        changes["output"] = normal_path(args.output)
    if args.output_mode:
        changes["output_mode"] = args.output_mode
    if args.templates:
        changes["templates"] = normal_path(args.templates)
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
    if args.force:
        changes["force"] = True
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


class WatchGraph:
    def __init__(self) -> None:
        self.edges: dict[Path, set[Path]] = {}
        self.seen: set[Path] = set()

    def update(self, pages: dict[Path, set[Path]], *, reset: bool = False) -> None:
        if reset:
            self.edges.clear()
        else:
            for linked in self.edges.values():
                linked.difference_update(pages)
        self.edges = {dependency: linked for dependency, linked in self.edges.items() if linked}
        for page, dependencies in pages.items():
            for dependency in dependencies:
                dependency = dependency.absolute()
                self.seen.add(dependency)
                self.edges.setdefault(dependency, set()).add(page.absolute())

    def affected(self, paths: set[Path]) -> set[Path]:
        return set().union(*(self.edges.get(path.absolute(), set()) for path in paths))

    @property
    def pages(self) -> set[Path]:
        return set().union(*self.edges.values()) if self.edges else set()


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
    graph = WatchGraph()
    graph.update(result.page_dependencies, reset=True)
    server = None
    if serve:
        root = settings.output if settings.input.is_dir() else settings.output.parent
        server, _ = _server(root, port)
        path = "/" if settings.input.is_dir() else "/" + settings.output.name
        print(f"preview: http://127.0.0.1:{port}{path}")
    changes: SimpleQueue[Path] = SimpleQueue()

    def ignored(path: Path) -> bool:
        generated = path.is_relative_to(settings.output) if settings.input.is_dir() else path == settings.output
        return generated or ".md2html-cache" in path.parts or any(part in {".git", "node_modules", "__pycache__"} for part in path.parts)

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event) -> None:
            if event.is_directory or event.event_type in {"opened", "closed_no_write"}:
                return
            for name in (getattr(event, "src_path", None), getattr(event, "dest_path", None)):
                if name:
                    path = Path(name).absolute()
                    if not ignored(path):
                        changes.put(path)

    observer = Observer()
    watched: list[Path] = []

    def add_roots() -> None:
        source = settings.input if settings.input.is_dir() else settings.input.parent
        roots = {settings.project_root, source, *(path.parent for path in graph.edges)}
        for root in sorted((path.absolute() for path in roots if path.exists()), key=lambda path: len(path.parts)):
            if not any(root.is_relative_to(existing) for existing in watched):
                observer.schedule(Handler(), str(root), recursive=True)
                watched.append(root)

    add_roots()
    observer.start()
    print(f"watching {settings.input}")

    def copy_changed(paths: set[Path]) -> None:
        if not settings.input.is_dir():
            return
        for source in paths:
            try:
                relative = source.relative_to(settings.input)
            except ValueError:
                continue
            if (settings.templates and source.is_relative_to(settings.templates)) or source.suffix.lower() in {".md", ".markdown"} or any(part.startswith(("_", ".")) for part in relative.parts):
                continue
            target = settings.output / relative
            if source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            elif not source.exists():
                target.unlink(missing_ok=True)

    try:
        while True:
            changed = {changes.get()}
            time.sleep(.15)
            while True:
                try:
                    changed.add(changes.get_nowait())
                except Empty:
                    break
            print(f"change: {sorted(map(str, changed))[0]}")
            try:
                copy_changed(changed)
                full = any(path not in graph.seen or path in graph.pages and not path.exists() for path in changed)
                affected = graph.affected(changed)
                if not full and not affected:
                    continue
                result = Project(settings).build(None if full else affected)
                describe(result)
                graph.update(result.page_dependencies, reset=full)
                add_roots()
            except (OSError, ValueError) as error:
                print(f"error: {error}", file=sys.stderr)
    except KeyboardInterrupt:
        print("stopped")
    finally:
        observer.stop()
        observer.join()
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
        return _write_example("\n".join(_resource(f"assets/{name}") for name in PAGE_CSS), args.example_css, args.force)
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
