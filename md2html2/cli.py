"""Command-line interface, rebuilding, and local preview."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import metadata
from importlib.resources import files
import os
from pathlib import Path
from queue import Empty, SimpleQueue
import shutil
import sys
import threading
import time
from urllib.parse import unquote, urlsplit

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound

from . import __version__
from .project import BuildResult, Project, syntax_css
from .settings import EXAMPLE_CONFIG, Settings, find_config, load_settings, normal_path

PAGE_CSS = (
    "page-base.css", "feature-code.css", "feature-math.css",
    "feature-toc.css", "feature-image.css", "feature-warning.css",
)


def _pygments_style(name: str) -> str:
    try:
        get_style_by_name(name)
    except ClassNotFound as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    return name


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="md2html",
        description="Build an excellent standalone page or a native Markdown website.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  md2html article.md
  md2html -es article.md
  md2html -erf notes -o html
  md2html --config md2html.json --serve
  md2html --example-template templates/page.html
""",
    )
    result.add_argument("input", nargs="*", type=Path, help="Markdown files or source directories")
    result.add_argument("-o", "--output", type=Path, help="output file or directory")
    result.add_argument("-e", "--execute", action="store_true", help="run executable @src content and show its output")
    result.add_argument("-r", "--recursive", action="store_true", help="render Markdown in subdirectories")
    result.add_argument("-f", "--force", action="store_true", help="rerun executable content or replace an existing example file")
    result.add_argument("-s", "--serve", action="store_true", help="serve the output and rebuild when source files change")
    result.add_argument("-w", "--watch", action="store_true", help="rebuild when source files change without starting a server")
    result.add_argument("--port", type=int, default=8000, help="preview server port (default: 8000)")
    result.add_argument("--config", type=Path, help="JSON configuration file; relative paths inside it are resolved from that file")
    result.add_argument("--output-mode", choices=("pages", "site"), help="build independent pages or a native static site")
    result.add_argument("--templates", type=Path, help="directory searched before built-in templates")
    result.add_argument("--template", help="standalone HTML template name or path")
    result.add_argument("--css", action="append", help="CSS file to embed; repeat to combine files")
    result.add_argument("--stylesheet", action="append", help="external stylesheet URL; repeat to add more")
    result.add_argument("--shared-assets", action="store_true", help="write shared page CSS instead of embedding it")
    result.add_argument("--no-css", action="store_true", help="do not embed CSS in standalone pages")
    result.add_argument("--no-feature-css", action="store_true", help="omit CSS for generated code, math, TOCs, images, and warnings")
    result.add_argument("--highlight-style", type=_pygments_style, help="Pygments style name for light syntax highlighting")
    result.add_argument("--highlight-dark-style", type=_pygments_style, help="Pygments style name for dark syntax highlighting")
    result.add_argument("--math", choices=("mathjax", "mathjax-chtml", "svg", "mathml", "raw"), help="math rendering backend")
    result.add_argument("--math-fonts", choices=("auto", "all", "inline", "remote", "none"), help="CHTML font asset mode (default: auto)")
    result.add_argument("--timeout", type=float, help="execution timeout in seconds")
    result.add_argument("--clean", action="store_true", help="remove a site output directory before building")
    result.add_argument("--readme", action="store_true", help="print the complete installed README")
    result.add_argument("--example-config", nargs="?", const="md2html.json", metavar="PATH", help="write a starter JSON config; use - for stdout")
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


def _apply_cli(settings: Settings, args: argparse.Namespace) -> Settings:
    changes = {}
    for name in ("output_mode", "template", "highlight_style", "highlight_dark_style"):
        if value := getattr(args, name):
            changes[name] = value
    for name in ("execute", "force", "recursive", "clean", "shared_assets"):
        if getattr(args, name):
            changes[name] = True
    if args.templates:
        changes["templates"] = normal_path(args.templates)
    if args.css is not None:
        changes["css"] = tuple(args.css)
    if args.stylesheet is not None:
        changes["stylesheets"] = tuple(args.stylesheet)
    if args.no_css:
        changes.update(css=(), feature_css=False)
    elif args.no_feature_css:
        changes["feature_css"] = False
    if args.math:
        changes["math"] = replace(settings.math, backend=args.math)
    if args.math_fonts:
        changes["math"] = replace(changes.get("math", settings.math), chtml_fonts=args.math_fonts)
    if args.timeout is not None:
        if args.timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        changes["timeout"] = args.timeout
    return replace(settings, **changes)


def _common_root(inputs: list[Path]) -> Path:
    paths = [path.absolute() if path.is_dir() else path.absolute().parent for path in inputs]
    return normal_path(Path(os.path.commonpath(paths)))


def settings_list_from_args(args: argparse.Namespace) -> list[Settings]:
    inputs = [normal_path(path) for path in args.input]
    config = normal_path(args.config) if args.config else None
    if config is None and not inputs:
        config = find_config(Path("."))
        if config is None:
            raise ValueError("give Markdown files, source directories, or --config")
    elif config is None and len(inputs) == 1 and inputs[0].is_dir():
        config = find_config(inputs[0])
    if config:
        if not config.is_file():
            raise ValueError(f"configuration does not exist: {config}")
        base = load_settings(config)
        if not inputs:
            return [_apply_cli(replace(base, output=normal_path(args.output) if args.output else base.output), args)]
        if len(inputs) == 1:
            source = inputs[0]
            output = normal_path(args.output) if args.output else base.output
            if source.is_file() and output.is_dir():
                output = output / source.with_suffix(".html").name
            return [_apply_cli(replace(base, input=source, output=output), args)]
    elif len(inputs) == 1:
        source = inputs[0]
        if source.is_file():
            output = normal_path(args.output) if args.output else None
            if output and output.is_dir():
                output = output / source.with_suffix(".html").name
            return [_apply_cli(Settings.single(source, output), args)]
        else:
            output = normal_path(args.output or Path("html"))
            return [_apply_cli(Settings(input=source, output=output, project_root=source, recursive=args.recursive, shared_assets=True), args)]

    if not inputs:
        raise ValueError("configuration has no input")
    root = base.project_root if config else _common_root(inputs)
    if config:
        base = replace(base, project_root=root)
    else:
        base = Settings(input=inputs[0], output=Path("html"), project_root=root)
    shared = args.shared_assets or any(path.is_dir() for path in inputs)
    collection = len(inputs) > 1 and (args.output is not None or shared)
    output_root = normal_path(args.output or (base.output if config else Path("html")))
    common = _common_root(inputs)
    planned: list[Settings] = []
    for source in inputs:
        if collection:
            relative = source.absolute().relative_to(common.absolute())
            output = output_root / (relative.with_suffix(".html") if source.is_file() else relative)
        else:
            output = source.with_suffix(".html")
        settings = replace(
            base, input=source, output=normal_path(output), recursive=base.recursive or args.recursive,
            shared_assets=base.shared_assets or shared,
        )
        planned.append(_apply_cli(settings, args))
    return planned


def settings_from_args(args: argparse.Namespace) -> Settings:
    settings = settings_list_from_args(args)
    if len(settings) != 1:
        raise ValueError("this operation requires one input")
    return settings[0]


def describe(result: BuildResult) -> None:
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    noun = "file" if result.output_count == 1 else "files"
    suffix = f"; skipped {len(result.skipped)} unchanged" if result.skipped else ""
    print(f"built {result.output_count} {noun}{suffix}")


class WatchGraph:
    def __init__(self) -> None:
        self.edges: dict[Path, set[Path]] = {}
        self.seen: set[Path] = set()

    def update(self, pages: dict[Path, set[Path]], *, reset: bool = False) -> None:
        if reset:
            self.edges.clear()
            self.seen.clear()
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


@dataclass
class BuildSession:
    settings: list[Settings]

    def __post_init__(self) -> None:
        self.owners: dict[Path, Settings] = {}
        self.assets: dict[Path, Path] = {}

    @staticmethod
    def _merge(total: BuildResult, result: BuildResult) -> None:
        total.written.extend(result.written)
        total.copied.extend(result.copied)
        total.warnings.extend(result.warnings)
        total.page_dependencies.update(result.page_dependencies)
        total.asset_dependencies.update(result.asset_dependencies)
        total.skipped.extend(result.skipped)

    def build(self, only: set[Path] | None = None, *, skip_unchanged: bool = False) -> BuildResult:
        total = BuildResult()
        owners: dict[Path, Settings] = {}
        for settings in self.settings:
            affected = None if only is None else {page for page in only if self.owners.get(page.absolute()) == settings}
            if only is not None and not affected:
                continue
            selected = None if settings.shared_math_assets else affected
            result = Project(settings).build(selected, skip_unchanged=skip_unchanged)
            owners.update({page.absolute(): settings for page in result.page_dependencies})
            self._merge(total, result)
        if only is None:
            self.owners = owners
            self.assets.clear()
        self.assets.update({source.absolute(): target.absolute() for source, target in total.asset_dependencies.items()})
        return total


def _server(root: Path, port: int, routes: dict[str, Path] | None = None) -> tuple[ThreadingHTTPServer, threading.Thread]:
    class QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *values, **keywords):
            super().__init__(*values, directory=str(root), **keywords)

        def translate_path(self, path: str) -> str:
            if routes is None:
                return super().translate_path(path)
            name = unquote(urlsplit(path).path).strip("/")
            return str(routes.get(name, root / ".md2html-not-found"))

        def log_message(self, format: str, *args) -> None:
            print(f"request: {format % args}")

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
    except OSError as error:
        raise ValueError(f"could not start preview on port {port}: {error}") from error
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _serve_root(settings: list[Settings]) -> Path:
    roots = [item.output.absolute() if item.input.is_dir() else item.output.absolute().parent for item in settings]
    return Path(os.path.commonpath(roots))


def _update_routes(routes: dict[str, Path], root: Path, session: BuildSession, result: BuildResult) -> None:
    files = {*result.written, *result.copied, *result.skipped, *session.assets.values()}
    for path in files:
        path = path.absolute()
        if path.is_file() and path.is_relative_to(root):
            routes[path.relative_to(root).as_posix()] = path
    indexes = [name for name in routes if name.endswith("/index.html") or name == "index.html"]
    if len(indexes) == 1:
        routes[""] = routes[indexes[0]]


def watch(settings: Settings | list[Settings], *, serve: bool, port: int) -> int:
    settings_list = [settings] if isinstance(settings, Settings) else settings
    session = BuildSession(settings_list)
    result = session.build(skip_unchanged=True)
    describe(result)
    graph = WatchGraph()
    graph.update(result.page_dependencies, reset=True)
    graph.seen.update(session.assets)
    server = None
    routes: dict[str, Path] | None = {} if len(settings_list) > 1 else None
    serve_root = _serve_root(settings_list)
    if serve:
        if routes is not None:
            _update_routes(routes, serve_root, session, result)
        server, _ = _server(serve_root, port, routes)
        pages = sorted({*result.written, *result.skipped})
        for page in pages:
            if page.suffix.lower() in {".html", ".htm"} and page.absolute().is_relative_to(serve_root):
                path = page.absolute().relative_to(serve_root).as_posix()
                print(f"preview: http://127.0.0.1:{port}/{path}")
    changes: SimpleQueue[Path] = SimpleQueue()

    def ignored(path: Path) -> bool:
        generated = any(
            path.is_relative_to(item.output.absolute()) if item.input.is_dir() else path == item.output.absolute()
            for item in settings_list
        )
        copied = any(source != target and path == target for source, target in session.assets.items())
        return generated or copied or ".md2html-cache" in path.parts or any(part in {".git", "node_modules", "__pycache__"} for part in path.parts)

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
        roots = {
            *(item.project_root for item in settings_list),
            *((item.input if item.input.is_dir() else item.input.parent) for item in settings_list),
            *(path.parent for path in graph.edges),
        }
        for root in sorted((path.absolute() for path in roots if path.exists()), key=lambda path: len(path.parts)):
            if not any(root.is_relative_to(existing) for existing in watched):
                observer.schedule(Handler(), str(root), recursive=True)
                watched.append(root)

    add_roots()
    observer.start()
    print("watching " + ", ".join(str(item.input) for item in settings_list))

    def copy_changed(paths: set[Path]) -> None:
        for source in paths:
            target = session.assets.get(source.absolute())
            if target is None:
                continue
            if source.absolute() == target:
                continue
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
                result = session.build(None if full else affected)
                describe(result)
                graph.update(result.page_dependencies, reset=full)
                graph.seen.update(session.assets)
                if routes is not None:
                    _update_routes(routes, serve_root, session, result)
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
        source_readme = Path(__file__).resolve().parent.parent / "readme.md"
        text = source_readme.read_text(encoding="utf-8") if source_readme.is_file() else metadata("md2html2").get_payload()
        print(text, end="")
        return 0
    if args.example_config is not None:
        return _write_example(EXAMPLE_CONFIG, args.example_config, args.force)
    if args.example_template is not None:
        return _write_example(_resource("default_templates/page.html"), args.example_template, args.force)
    if args.example_css is not None:
        values = [_resource(f"assets/{name}") for name in PAGE_CSS]
        values.insert(1, syntax_css())
        return _write_example("\n".join(values), args.example_css, args.force)
    try:
        settings = settings_list_from_args(args)
        if args.serve or args.watch:
            return watch(settings, serve=args.serve, port=args.port)
        describe(BuildSession(settings).build())
        return 0
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
