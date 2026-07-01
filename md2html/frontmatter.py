from __future__ import annotations

import re
from typing import Any

import yaml

_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.S)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw = match.group(1)
    metadata = yaml.safe_load(raw) or {}
    if not isinstance(metadata, dict):
        metadata = {"frontmatter": metadata}
    return metadata, text[match.end():]


def dump_frontmatter(metadata: dict[str, Any]) -> str:
    if not metadata:
        return ""
    return "---\n" + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).strip() + "\n---\n\n"


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    return parse_frontmatter(text)
