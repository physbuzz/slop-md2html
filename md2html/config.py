from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class MathConfig:
    backend: str = "mathjax"  # future extension point: mathml, svg
    wrap_display: bool = True


@dataclass
class CodeConfig:
    commands: dict[str, Any] = field(default_factory=dict)
    timeout: float = 15.0
    output_suffix: str = ".out"


@dataclass
class ImageConfig:
    class_name: str | None = None
    width: str | None = None


@dataclass
class BuildOptions:
    project_root: Path = field(default_factory=lambda: Path.cwd())
    template_dirs: list[Path] = field(default_factory=list)
    template: str = "page.html"
    output_mode: str = "html"  # html or jekyll
    math: MathConfig = field(default_factory=MathConfig)
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


def options_from_mapping(data: dict[str, Any], *, cwd: Path | None = None) -> BuildOptions:
    cwd = cwd or Path.cwd()
    project_root = Path(data.get("project_root", data.get("root", cwd))).expanduser()
    if not project_root.is_absolute():
        project_root = (cwd / project_root).resolve()

    template_dirs = []
    for raw in data.get("template_dirs", data.get("templates", [])) or []:
        p = Path(raw).expanduser()
        template_dirs.append(p if p.is_absolute() else (project_root / p))

    math_data = data.get("math", {}) or {}
    code_data = data.get("code", {}) or {}
    image_data = data.get("images", data.get("obsidian_images", {})) or {}

    return BuildOptions(
        project_root=project_root,
        template_dirs=template_dirs,
        template=data.get("template", "page.html"),
        output_mode=data.get("output_mode", data.get("format", "html")),
        math=MathConfig(
            backend=math_data.get("backend", data.get("math_backend", "mathjax")),
            wrap_display=math_data.get("wrap_display", True),
        ),
        code=CodeConfig(
            commands=code_data.get("commands", {}),
            timeout=float(code_data.get("timeout", data.get("timeout", 15.0))),
            output_suffix=code_data.get("output_suffix", ".out"),
        ),
        images=ImageConfig(
            class_name=image_data.get("class", image_data.get("class_name")),
            width=image_data.get("width"),
        ),
        execute=bool(data.get("execute", False)),
        embed_assets=bool(data.get("embed_assets", data.get("embed_styles", True))),
        copy_assets=bool(data.get("copy_assets", True)),
        no_overwrite=bool(data.get("no_overwrite", False)),
        force_rebuild=bool(data.get("force_rebuild", False)),
        strict=bool(data.get("strict", False)),
        verbose=bool(data.get("verbose", False)),
    )
