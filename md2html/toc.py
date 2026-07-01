from __future__ import annotations

import html
import re
from dataclasses import dataclass

from .slug import Slugger, plain_text

_HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*#*\s*$")
_TOC_RE = re.compile(r"^\s*@toc\s*$", re.MULTILINE)
_EXERCISE_RE = re.compile(r"^exercise\b", re.IGNORECASE)


@dataclass(frozen=True)
class TocHeading:
    level: int
    title: str
    id: str
    line: int

    @property
    def text(self) -> str:
        return plain_text(self.title).strip()


def collect_headings(markdown_text: str) -> list[TocHeading]:
    slugger = Slugger()
    headings: list[TocHeading] = []
    in_fence = False
    fence_marker = ""

    for lineno, line in enumerate(markdown_text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
            continue
        if in_fence:
            continue
        match = _HEADING_RE.match(line)
        if not match:
            continue
        raw_title = match.group("title").strip()
        text_title = plain_text(raw_title).strip()
        if not text_title or text_title.lower() == "solution":
            continue
        headings.append(
            TocHeading(
                level=len(match.group("marks")),
                title=raw_title,
                id=slugger.slug(raw_title),
                line=lineno,
            )
        )
    return headings


def _link(heading: TocHeading, *, extra_class: str | None = None) -> str:
    klass = f' class="{html.escape(extra_class, quote=True)}"' if extra_class else ""
    return f'<a href="#{html.escape(heading.id, quote=True)}"{klass}>{html.escape(heading.text)}</a>'


def _exercise_list(headings: list[TocHeading]) -> str:
    if not headings:
        return ""
    links = "\n".join(f'<span>{_link(h)}</span>' for h in headings)
    return (
        '<div class="exercise-container">('
        '<span class="exercise-list">\n'
        f'{links}\n'
        '</span>)\n'
        '</div>'
    )


def generate_toc(headings: list[TocHeading], *, title: str = "Directory") -> str:
    if not headings:
        return ""

    exercises = [h for h in headings if _EXERCISE_RE.match(h.text)]
    exercise_ids = {h.id for h in exercises}
    lines = ['<div class="table-of-contents">', f'<h2>{html.escape(title)}</h2>', '<ul class="toc-list">']
    stack: list[int] = []

    def close_to(level: int) -> None:
        while stack and stack[-1] >= level:
            lines.append("</ul>")
            stack.pop()

    for heading in headings:
        if heading.id in exercise_ids:
            continue
        text = heading.text.lower()
        is_exercises = text == "exercises"
        level = heading.level
        if not stack:
            lines.append("<ul>")
            stack.append(level)
        elif level > stack[-1]:
            while stack[-1] < level:
                lines.append("<ul>")
                stack.append(stack[-1] + 1)
        elif level < stack[-1]:
            close_to(level + 1)
        if is_exercises:
            lines.append(f'<li>{_link(heading, extra_class="toc-exercises")}')
            lines.append(_exercise_list(exercises))
            lines.append("</li>")
        else:
            lines.append(f"<li>{_link(heading)}</li>")

    while stack:
        lines.append("</ul>")
        stack.pop()
    lines.extend(["</ul>", "</div>"])
    return "\n".join(lines)


def replace_toc(markdown_text: str, toc_html: str) -> str:
    return _TOC_RE.sub(lambda _m: "\n" + toc_html + "\n", markdown_text)


def prepare_toc(markdown_text: str) -> tuple[str, list[TocHeading], str]:
    headings = collect_headings(markdown_text)
    toc_html = generate_toc(headings)
    return replace_toc(markdown_text, toc_html), headings, toc_html
