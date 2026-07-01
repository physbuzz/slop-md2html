from __future__ import annotations

import html
import re
from pathlib import Path

from .context import BuildContext

_OBSIDIAN_IMAGE_RE = re.compile(r"!\[\[(?P<body>[^\]]+)\]\]")


def _parse_parts(body: str) -> tuple[str, dict[str, str]]:
    parts = [p.strip() for p in body.split("|")]
    target = parts[0]
    attrs: dict[str, str] = {}
    for part in parts[1:]:
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
            attrs[key.strip().lower()] = value.strip().strip('"\'')
        elif part.isdigit() or part.endswith("%") or part.endswith("px"):
            attrs["width"] = part
        else:
            attrs.setdefault("alt", part)
    return target, attrs


def _looks_like_percent(value: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+)?%", value.strip()))


def _normalize_width(value: str) -> str:
    value = value.strip()
    if value.isdigit():
        return f"{value}px"
    return value


def process_obsidian_images(text: str, ctx: BuildContext, *, current_file: Path | None = None) -> str:
    def repl(match: re.Match[str]) -> str:
        target, attrs = _parse_parts(match.group("body"))
        url = ctx.asset_url(target, current_file=current_file)
        alt = attrs.get("alt") or Path(target).stem.replace("-", " ").replace("_", " ")
        classes = ["obsidian-image"]
        default_class = ctx.options.images.class_name
        if default_class:
            classes.append(default_class)
        if attrs.get("class"):
            classes.extend(attrs["class"].split())
        width = attrs.get("width") or ctx.options.images.width
        attr_bits = [f'src="{html.escape(url, quote=True)}"', f'alt="{html.escape(alt, quote=True)}"']
        if classes:
            attr_bits.append(f'class="{html.escape(" ".join(classes), quote=True)}"')
        if width:
            width = _normalize_width(width)
            if _looks_like_percent(width) or width.endswith("px") or width.endswith("em") or width.endswith("rem"):
                attr_bits.append(f'style="width: {html.escape(width, quote=True)};"')
            else:
                attr_bits.append(f'width="{html.escape(width, quote=True)}"')
        return "<img " + " ".join(attr_bits) + ">"

    return _OBSIDIAN_IMAGE_RE.sub(repl, text)
