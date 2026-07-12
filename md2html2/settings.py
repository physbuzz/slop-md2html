"""Configuration loading and path policy."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
import os
from pathlib import Path
from typing import Any

CONFIG_NAME = "md2html.json"
MARKDOWN_SUFFIXES = {".md", ".markdown"}
LIQUID_SUFFIXES = {".html", ".htm", ".xml"}
PAGE_SUFFIXES = MARKDOWN_SUFFIXES | LIQUID_SUFFIXES
OUTPUT_MODES = ("pages", "site", "jekyll", "jekyll-markdown")
SITE_MODES = {"site", "jekyll"}


def normal_path(path: Path) -> Path:
    return Path(os.path.normpath(path.expanduser()))


def page_output(path: Path) -> Path:
    return path.with_suffix(".html") if path.suffix.lower() in MARKDOWN_SUFFIXES else path


def default_output(mode: str) -> Path:
    return Path("_site" if mode in SITE_MODES else "markdown" if mode == "jekyll-markdown" else "html")


@dataclass(frozen=True)
class MathSettings:
    backend: str = "mathjax-chtml"
    chtml_fonts: str = "auto"


@dataclass(frozen=True)
class ImageSettings:
    class_name: str | None = None
    width: str | None = None


@dataclass(frozen=True)
class Settings:
    input: Path
    output: Path
    output_mode: str = "pages"
    project_root: Path = field(default_factory=lambda: Path("."))
    templates: tuple[Path, ...] = ()
    template: str = "page.html"
    css: tuple[str, ...] | None = None
    stylesheets: tuple[str, ...] = ()
    feature_css: bool = True
    minify_css: bool = True
    parse_liquid: bool = True
    shared_assets: bool = False
    math: MathSettings = field(default_factory=MathSettings)
    images: ImageSettings = field(default_factory=ImageSettings)
    execute: bool = False
    timeout: float = 120.0
    force: bool = False
    recursive: bool = False
    clean: bool = False
    exclude: tuple[str, ...] = ()
    frontmatter: dict[str, Any] = field(default_factory=dict)
    site_data: dict[str, Any] = field(default_factory=dict)
    commands: dict[str, str] = field(default_factory=dict)
    highlight_style: str = "default"
    highlight_dark_style: str = "github-dark"

    @classmethod
    def single(cls, source: Path, output: Path | None = None) -> "Settings":
        source = normal_path(source)
        return cls(
            input=source,
            output=normal_path(output or page_output(source)),
            project_root=source.parent,
        )

    def with_cli(self, **changes: Any) -> "Settings":
        return replace(self, **{key: value for key, value in changes.items() if value is not None})

    @property
    def shared_math_assets(self) -> bool:
        return self.input.is_dir() and self.math.backend == "mathjax-chtml" and (self.site_mode or self.shared_assets)

    @property
    def site_mode(self) -> bool:
        return self.output_mode in SITE_MODES

    @property
    def jekyll_mode(self) -> bool:
        return self.output_mode == "jekyll"

    @property
    def markdown_mode(self) -> bool:
        return self.output_mode == "jekyll-markdown"


def find_config(start: Path) -> Path | None:
    relative = not start.is_absolute()
    directory = (start if start.is_dir() else start.parent).absolute()
    for directory in (directory, *directory.parents):
        candidate = directory / CONFIG_NAME
        if candidate.is_file():
            return normal_path(Path(os.path.relpath(candidate))) if relative else candidate
    return None


def read_mapping(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"could not read configuration {path}: {error}") from error
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"configuration must contain an object: {path}")
    return value


def load_settings(config_path: Path) -> Settings:
    config_path = normal_path(config_path)
    if config_path.suffix.lower() != ".json":
        raise ValueError(f"configuration must be a JSON file: {config_path}")
    root = config_path.parent
    raw = read_mapping(config_path)

    def path_value(name: str, default: str) -> Path:
        value = normal_path(Path(str(raw.get(name, default))))
        return value if value.is_absolute() else normal_path(root / value)

    math_value = raw.get("math", {})
    if isinstance(math_value, str):
        math_value = {"backend": math_value}
    if not isinstance(math_value, dict):
        raise ValueError("math must be a backend name or an object")
    font_mode = str(math_value.get("chtml_fonts", "auto"))
    if font_mode not in {"auto", "all", "inline", "remote", "none"}:
        raise ValueError("math.chtml_fonts must be auto, all, inline, remote, or none")
    templates = raw.get("templates", [])
    if isinstance(templates, str):
        templates = [templates]
    if not isinstance(templates, list):
        raise ValueError("templates must be a path or a list of paths")
    def rooted(value: Any) -> Path:
        path = normal_path(Path(str(value)))
        return path if path.is_absolute() else normal_path(root / path)

    template_paths = tuple(rooted(value) for value in templates)
    css = raw.get("css")
    if isinstance(css, str):
        css = [css]
    if css is not None and not isinstance(css, list):
        raise ValueError("css must be a path, a list of paths, or null")
    stylesheets = raw.get("stylesheets", [])
    if isinstance(stylesheets, str):
        stylesheets = [stylesheets]
    if not isinstance(stylesheets, list):
        raise ValueError("stylesheets must be a path or a list of paths")
    frontmatter = raw.get("frontmatter") or {}
    if not isinstance(frontmatter, dict):
        raise ValueError("frontmatter must contain an object")
    images = raw.get("images", {}) or {}
    if not isinstance(images, dict):
        raise ValueError("images must contain an object")
    timeout = float(raw.get("timeout", 120))
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    mode = str(raw.get("output_mode", "pages"))
    if mode not in OUTPUT_MODES:
        raise ValueError("output_mode must be " + ", ".join(OUTPUT_MODES))
    reserved = {
        "input", "output", "output_mode", "templates", "template", "css", "stylesheets",
        "feature_css", "minify_css", "parse_liquid", "shared_assets", "math", "images", "execute", "timeout", "force", "recursive", "clean",
        "exclude", "frontmatter", "commands", "highlight_style", "highlight_dark_style", "site",
    }
    site_data = dict(raw.get("site") or {})
    site_data.update({key: value for key, value in raw.items() if key not in reserved})
    return Settings(
        input=path_value("input", "."),
        output=path_value("output", str(default_output(mode))),
        output_mode=mode,
        project_root=root,
        templates=template_paths,
        template=str(raw.get("template", "page.html")),
        css=None if css is None else tuple(str(item) for item in css),
        stylesheets=tuple(str(item) for item in stylesheets),
        feature_css=bool(raw.get("feature_css", True)),
        minify_css=bool(raw.get("minify_css", True)),
        parse_liquid=bool(raw.get("parse_liquid", True)),
        shared_assets=bool(raw.get("shared_assets", mode == "pages" and path_value("input", ".").is_dir())),
        math=MathSettings(backend=str(math_value.get("backend", "mathjax-chtml")), chtml_fonts=font_mode),
        images=ImageSettings(
            class_name=str(images["class"]) if images.get("class") is not None else None,
            width=str(images["width"]) if images.get("width") is not None else None,
        ),
        execute=bool(raw.get("execute", False)),
        timeout=timeout,
        force=bool(raw.get("force", False)),
        recursive=bool(raw.get("recursive", mode != "pages")),
        clean=bool(raw.get("clean", False)),
        exclude=tuple(str(item) for item in raw.get("exclude", ())),
        frontmatter=dict(frontmatter),
        site_data=site_data,
        commands={str(key): str(value) for key, value in (raw.get("commands") or {}).items()},
        highlight_style=str(raw.get("highlight_style", "default")),
        highlight_dark_style=str(raw.get("highlight_dark_style", "github-dark")),
    )


EXAMPLE_CONFIG = """{
  "input": ".",
  "output": "_site",
  "output_mode": "site",
  "templates": ["templates"],
  "minify_css": true,
  "parse_liquid": true,
  "math": {
    "backend": "mathjax-chtml"
  },
  "images": {
    "class": null,
    "width": null
  },
  "exclude": [
    "drafts"
  ]
}
"""
