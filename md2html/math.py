from __future__ import annotations

import html
import re
from dataclasses import dataclass

from .config import MathConfig


@dataclass(frozen=True)
class MathSpan:
    placeholder: str
    text: str
    display: bool


_FENCE_RE = re.compile(r"(```.*?```|~~~.*?~~~)", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"(`+)(.*?)(?<!`)\1", re.DOTALL)


def _protect_code(text: str) -> tuple[str, dict[str, str]]:
    """Temporarily remove code spans/fences so dollar parsing ignores them."""
    stored: dict[str, str] = {}

    def store(match: re.Match[str]) -> str:
        key = f"@@MD2HTML_CODE_{len(stored)}@@"
        stored[key] = match.group(0)
        return key

    text = _FENCE_RE.sub(store, text)
    text = _INLINE_CODE_RE.sub(store, text)
    return text, stored


def _restore_code(text: str, stored: dict[str, str]) -> str:
    for key, value in stored.items():
        text = text.replace(key, value)
    return text


def protect_math(text: str) -> tuple[str, list[MathSpan]]:
    """Replace TeX math with placeholders before Markdown parsing.

    This prevents Markdown emphasis/link parsing inside expressions like
    ``$x_1,x_2$`` and multiline display environments.
    """
    text, code = _protect_code(text)
    spans: list[MathSpan] = []
    out: list[str] = []
    i = 0
    n = len(text)

    def add_span(raw: str, display: bool) -> str:
        placeholder = f"@@MD2HTML_MATH_{len(spans)}@@"
        spans.append(MathSpan(placeholder, raw, display))
        return placeholder

    while i < n:
        if text.startswith("$$", i) and (i == 0 or text[i - 1] != "\\"):
            end = text.find("$$", i + 2)
            if end != -1:
                raw = text[i : end + 2]
                out.append(add_span(raw, True))
                i = end + 2
                continue
        if text[i] == "$" and (i == 0 or text[i - 1] != "\\"):
            # Avoid treating currency-ish "$ 10" or a display delimiter as inline math.
            if i + 1 < n and text[i + 1] not in " \t\n$":
                j = i + 1
                matched_inline = False
                while True:
                    end = text.find("$", j)
                    if end == -1:
                        break
                    if text[end - 1] != "\\" and end > i + 1:
                        raw = text[i : end + 1]
                        if "\n\n" not in raw:
                            out.append(add_span(raw, False))
                            i = end + 1
                            matched_inline = True
                            break
                    j = end + 1
                if matched_inline:
                    continue
        out.append(text[i])
        i += 1

    protected = "".join(out)
    protected = _restore_code(protected, code)
    return protected, spans


def render_math_span(span: MathSpan, config: MathConfig, *, output_mode: str = "html") -> str:
    raw = span.text
    source = raw[2:-2].strip() if span.display and raw.startswith("$$") else raw[1:-1]
    data_tex = html.escape(source, quote=True).replace("\n", "&#10;")
    rendered_source = html.escape(raw)

    if output_mode == "jekyll" and span.display:
        return f'<div class="math display" data-tex="{data_tex}">{rendered_source}</div>'
    if span.display:
        return f'<div class="math display" data-tex="{data_tex}">{rendered_source}</div>'
    return f'<span class="math inline" data-tex="{data_tex}">{rendered_source}</span>'


def restore_math(html_text: str, spans: list[MathSpan], config: MathConfig, *, output_mode: str = "html") -> str:
    for span in spans:
        rendered = render_math_span(span, config, output_mode=output_mode)
        if span.display:
            # Markdown parsers wrap unknown placeholder text in <p>; display math must be block-level.
            pattern = re.compile(r"<p>\s*" + re.escape(span.placeholder) + r"\s*</p>")
            html_text = pattern.sub(lambda _m, rendered=rendered: rendered, html_text)
        html_text = html_text.replace(span.placeholder, rendered)
    return html_text
