"""Configuration loading and path policy."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
import os
from pathlib import Path
from typing import Any

CONFIG_NAME = "md2html.json"


def normal_path(path: Path) -> Path:
    return Path(os.path.normpath(path.expanduser()))


@dataclass(frozen=True)
class MathSettings:
    backend: str = "mathjax"
    chtml_fonts: str = "auto"


@dataclass(frozen=True)
class Settings:
    input: Path
    output: Path
    output_mode: str = "pages"
    project_root: Path = field(default_factory=lambda: Path("."))
    templates: Path | None = None
    template: str = "page.html"
    css: tuple[str, ...] | None = None
    stylesheets: tuple[str, ...] = ()
    feature_css: bool = True
    shared_assets: bool = False
    math: MathSettings = field(default_factory=MathSettings)
    execute: bool = False
    timeout: float = 120.0
    force: bool = False
    recursive: bool = False
    clean: bool = False
    exclude: tuple[str, ...] = ()
    site_data: dict[str, Any] = field(default_factory=dict)
    commands: dict[str, str] = field(default_factory=dict)
    highlight_style: str = "default"
    highlight_dark_style: str = "github-dark"

    @classmethod
    def single(cls, source: Path, output: Path | None = None) -> "Settings":
        source = normal_path(source)
        return cls(
            input=source,
            output=normal_path(output or source.with_suffix(".html")),
            project_root=source.parent,
        )

    def with_cli(self, **changes: Any) -> "Settings":
        return replace(self, **{key: value for key, value in changes.items() if value is not None})

    @property
    def shared_math_assets(self) -> bool:
        return self.input.is_dir() and self.math.backend == "mathjax-chtml" and (self.output_mode == "site" or self.shared_assets)


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
    templates = raw.get("templates")
    template_path = None if templates is None else path_value("templates", str(templates))
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
    timeout = float(raw.get("timeout", 120))
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    mode = str(raw.get("output_mode", "pages"))
    if mode not in {"pages", "site"}:
        raise ValueError("output_mode must be 'pages' or 'site'")
    reserved = {
        "input", "output", "output_mode", "templates", "template", "css", "stylesheets",
        "feature_css", "shared_assets", "math", "execute", "timeout", "force", "recursive", "clean",
        "exclude", "commands", "highlight_style", "highlight_dark_style", "site",
    }
    site_data = dict(raw.get("site") or {})
    site_data.update({key: value for key, value in raw.items() if key not in reserved})
    return Settings(
        input=path_value("input", "."),
        output=path_value("output", "_site" if mode == "site" else "html"),
        output_mode=mode,
        project_root=root,
        templates=template_path,
        template=str(raw.get("template", "page.html")),
        css=None if css is None else tuple(str(item) for item in css),
        stylesheets=tuple(str(item) for item in stylesheets),
        feature_css=bool(raw.get("feature_css", True)),
        shared_assets=bool(raw.get("shared_assets", mode == "pages" and path_value("input", ".").is_dir())),
        math=MathSettings(backend=str(math_value.get("backend", "mathjax")), chtml_fonts=font_mode),
        execute=bool(raw.get("execute", False)),
        timeout=timeout,
        force=bool(raw.get("force", False)),
        recursive=bool(raw.get("recursive", mode == "site")),
        clean=bool(raw.get("clean", False)),
        exclude=tuple(str(item) for item in raw.get("exclude", ())),
        site_data=site_data,
        commands={str(key): str(value) for key, value in (raw.get("commands") or {}).items()},
        highlight_style=str(raw.get("highlight_style", "default")),
        highlight_dark_style=str(raw.get("highlight_dark_style", "github-dark")),
    )


EXAMPLE_CONFIG = """{
  "input": ".",
  "output": "_site",
  "output_mode": "site",
  "templates": "templates",
  "math": {
    "backend": "mathjax"
  },
  "exclude": [
    "drafts"
  ]
}
"""
