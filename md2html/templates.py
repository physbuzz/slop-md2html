from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import BuildOptions
from .highlighting import pygments_css
from .resources import package_resource_path

_ASSETS_DIR = package_resource_path("assets")
_DEFAULT_TEMPLATE_DIR = package_resource_path("default_templates")


def base_css() -> str:
    return (_ASSETS_DIR / "base.css").read_text(encoding="utf-8")


def make_environment(options: BuildOptions) -> Environment:
    dirs = [*(str(p) for p in options.template_dirs), str(_DEFAULT_TEMPLATE_DIR)]
    env = Environment(
        loader=FileSystemLoader(dirs),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def render_template(
    *,
    content: str,
    title: str,
    metadata: dict[str, Any],
    options: BuildOptions,
    template_name: str | None = None,
) -> str:
    env = make_environment(options)
    name = template_name or ("jekyll.html" if options.output_mode == "jekyll" else options.template)
    template = env.get_template(name)
    css = ""
    stylesheets: list[str] = []
    if options.embed_assets:
        css = pygments_css() + "\n\n" + base_css()
    else:
        stylesheets = metadata.get("stylesheets", []) or []
    return template.render(
        content=content,
        title=title,
        frontmatter=metadata,
        metadata=metadata,
        embedded_css=css,
        stylesheets=stylesheets,
        use_mathjax=options.math.backend == "mathjax",
        lang=metadata.get("lang", "en"),
        layout=metadata.get("layout", "post"),
    )
