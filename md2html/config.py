from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class MathConfig:
    backend: str = "mathjax"


@dataclass
class JekyllConfig:
    # "passthrough" emits $...$ / $$...$$ verbatim (pair with kramdown's
    # math_engine: ~ so the delimiters reach the browser for MathJax).
    # "html" emits the same data-tex span/div wrappers as html output mode,
    # which kramdown passes through untouched.
    math: str = "passthrough"
    # Layout applied when a page's frontmatter has none; None omits the key.
    layout: str | None = "post"
    # Path of the generated stylesheet relative to the output root; None skips it.
    stylesheet: str | None = "assets/css/md2html.css"
    # Convert Markdown fenced code blocks to highlighted HTML before Jekyll
    # processes them, matching md2html's HTML output and @src embeds.
    highlight_fences: bool = False
    # Extra frontmatter merged into every page; page frontmatter wins.
    frontmatter: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeConfig:
    commands: dict[str, Any] = field(default_factory=dict)
    timeout: float = 15.0
    output_suffix: str = ".out"
    highlight_style: str = "default"
    highlight_dark_style: str | None = "github-dark"


@dataclass
class ImageConfig:
    class_name: str | None = None
    width: str | None = None


@dataclass
class BuildOptions:
    project_root: Path = field(default_factory=lambda: Path.cwd())
    template_dirs: list[Path] = field(default_factory=list)
    template: str = "page.html"
    css: list[str] | None = None
    stylesheets: list[str] = field(default_factory=list)
    feature_css: bool = True
    output_mode: str = "html"  # html or jekyll
    math: MathConfig = field(default_factory=MathConfig)
    jekyll: JekyllConfig = field(default_factory=JekyllConfig)
    code: CodeConfig = field(default_factory=CodeConfig)
    images: ImageConfig = field(default_factory=ImageConfig)
    execute: bool = False
    embed_assets: bool = True
    copy_assets: bool = True
    no_overwrite: bool = False
    force_rebuild: bool = False
    strict: bool = False
    verbose: bool = False
    config_file: Path | None = None
    jekyll_output_root: Path | None = None


def load_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text) or {}
    return json.loads(text)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        elif value is not None:
            merged[key] = value
    return merged


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        return [str(value)]
    return [str(item) for item in value]


def options_from_mapping(data: dict[str, Any], *, cwd: Path | None = None) -> BuildOptions:
    cwd = cwd or Path.cwd()
    project_root = Path(data.get("project_root", cwd)).expanduser()
    if not project_root.is_absolute():
        project_root = (cwd / project_root).resolve()

    template_dirs = []
    for raw in data.get("template_dirs", []) or []:
        p = Path(raw).expanduser()
        template_dirs.append(p if p.is_absolute() else (project_root / p))

    math_data = data.get("math", {}) or {}
    code_data = data.get("code", {}) or {}
    image_data = data.get("images", {}) or {}
    jekyll_data = data.get("jekyll", {}) or {}

    return BuildOptions(
        project_root=project_root,
        template_dirs=template_dirs,
        template=data.get("template", "page.html"),
        css=_string_list(data["css"]) if data.get("css") is not None else None,
        stylesheets=_string_list(data.get("stylesheets", [])),
        feature_css=bool(data.get("feature_css", True)),
        output_mode=data.get("output_mode", "html"),
        math=MathConfig(
            backend=math_data.get("backend", "mathjax"),
        ),
        jekyll=JekyllConfig(
            math=jekyll_data.get("math", "passthrough"),
            layout=jekyll_data.get("layout", "post"),
            stylesheet=jekyll_data.get("stylesheet", "assets/css/md2html.css"),
            highlight_fences=bool(jekyll_data.get("highlight_fences", False)),
            frontmatter=dict(jekyll_data.get("frontmatter", {}) or {}),
        ),
        code=CodeConfig(
            commands=code_data.get("commands", {}),
            timeout=float(code_data.get("timeout", 15.0)),
            output_suffix=code_data.get("output_suffix", ".out"),
            highlight_style=code_data.get("highlight_style", "default"),
            highlight_dark_style=code_data.get("highlight_dark_style", "github-dark"),
        ),
        images=ImageConfig(
            class_name=image_data.get("class"),
            width=image_data.get("width"),
        ),
        execute=bool(data.get("execute", False)),
        embed_assets=bool(data.get("embed_assets", True)),
        copy_assets=bool(data.get("copy_assets", True)),
        no_overwrite=bool(data.get("no_overwrite", False)),
        force_rebuild=bool(data.get("force_rebuild", False)),
        strict=bool(data.get("strict", False)),
        verbose=bool(data.get("verbose", False)),
    )
