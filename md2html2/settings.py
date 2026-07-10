"""Configuration loading and path policy."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
from pathlib import Path
from typing import Any

import yaml


CONFIG_NAMES = ("md2html.json", "md2html.yml", "md2html.yaml", "md2html.config")


@dataclass(frozen=True)
class MathSettings:
    backend: str = "mathjax"
    chtml_fonts: str = "auto"


@dataclass(frozen=True)
class Settings:
    input: Path
    output: Path
    output_mode: str = "pages"
    project_root: Path = field(default_factory=Path.cwd)
    templates: Path | None = None
    template: str = "page.html"
    css: tuple[str, ...] | None = None
    math: MathSettings = field(default_factory=MathSettings)
    execute: bool = False
    regenerate: bool = False
    recursive: bool = False
    clean: bool = False
    exclude: tuple[str, ...] = ()
    site_data: dict[str, Any] = field(default_factory=dict)
    commands: dict[str, str] = field(default_factory=dict)

    @classmethod
    def single(cls, source: Path, output: Path | None = None) -> "Settings":
        source = source.resolve()
        return cls(
            input=source,
            output=(output or source.with_suffix(".html")).resolve(),
            project_root=source.parent,
        )

    def with_cli(self, **changes: Any) -> "Settings":
        return replace(self, **{key: value for key, value in changes.items() if value is not None})


def find_config(start: Path) -> Path | None:
    directory = start if start.is_dir() else start.parent
    for directory in (directory, *directory.parents):
        for name in CONFIG_NAMES:
            candidate = directory / name
            if candidate.is_file():
                return candidate
    return None


def read_mapping(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        value = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (OSError, ValueError, yaml.YAMLError) as error:
        raise ValueError(f"could not read configuration {path}: {error}") from error
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"configuration must contain an object: {path}")
    return value


def load_settings(config_path: Path) -> Settings:
    config_path = config_path.resolve()
    root = config_path.parent
    raw = read_mapping(config_path)

    def path_value(name: str, default: str) -> Path:
        value = Path(str(raw.get(name, default))).expanduser()
        return value if value.is_absolute() else (root / value).resolve()

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
    mode = str(raw.get("output_mode", "pages"))
    if mode not in {"pages", "site"}:
        raise ValueError("output_mode must be 'pages' or 'site'")
    reserved = {
        "input", "output", "output_mode", "templates", "template", "css", "math",
        "execute", "regenerate", "recursive", "clean", "exclude", "commands", "site",
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
        math=MathSettings(backend=str(math_value.get("backend", "mathjax")), chtml_fonts=font_mode),
        execute=bool(raw.get("execute", False)),
        regenerate=bool(raw.get("regenerate", False)),
        recursive=bool(raw.get("recursive", mode == "site")),
        clean=bool(raw.get("clean", False)),
        exclude=tuple(str(item) for item in raw.get("exclude", ())),
        site_data=site_data,
        commands={str(key): str(value) for key, value in (raw.get("commands") or {}).items()},
    )


EXAMPLE_CONFIG = """# md2html.config
input: .
output: _site
output_mode: site
templates: templates
math:
  backend: mathjax
exclude:
  - drafts
"""

EXAMPLE_JSON = """{
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
