from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

_TAG_RE = re.compile(r"<[^>]+>")
_LINK_RE = re.compile(r"!?\[([^\]]+)\]\([^\)]*\)")
_MARKDOWN_MARK_RE = re.compile(r"[`*_~]+")


def plain_text(value: str) -> str:
    """Convert a small Markdown/HTML fragment into stable human text."""
    value = html.unescape(value)
    value = _TAG_RE.sub("", value)
    value = _LINK_RE.sub(lambda m: m.group(1), value)
    value = _MARKDOWN_MARK_RE.sub("", value)
    return value.strip()


def slugify(value: str) -> str:
    """Slug policy used by both the TOC pass and the HTML heading renderer.

    The policy is intentionally close to the examples in the spec:
    ``Section 2.5`` -> ``section-25`` and ``Exercise 2.77`` ->
    ``exercise-277``.
    """
    value = plain_text(value).lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "section"


@dataclass
class Slugger:
    """Stateful unique slug generator."""

    counts: dict[str, int] = field(default_factory=dict)

    def slug(self, value: str) -> str:
        base = slugify(value)
        count = self.counts.get(base, 0)
        self.counts[base] = count + 1
        if count == 0:
            return base
        return f"{base}-{count + 1}"
