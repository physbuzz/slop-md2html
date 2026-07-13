"""Syntax-highlighting backends and their generated CSS."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import threading

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound

from .worker import JsonWorker


HIGHLIGHTERS = ("pygments", "rouge")
LANGUAGE_ALIASES = {"wl": "mathematica", "mma": "mathematica", "rkt": "racket", "py": "python", "js": "javascript"}
DEFAULT_STYLES = {"pygments": ("default", "github-dark"), "rouge": ("github.light", "github.dark")}


class Rouge:
    def __init__(self) -> None:
        script = files("md2html").joinpath("scripts/rouge.rb")
        self.worker = JsonWorker(
            ["ruby", Path(str(script))], missing="Rouge needs Ruby",
            unavailable="Rouge is unavailable; install it with gem install rouge",
        )
        self.styles = set(self.worker.ready["styles"])
        self.cached_css: dict[tuple[str, str], str] = {}

    def highlight(self, code: str, language: str, filename: Path | None) -> str:
        response = self.worker.request({
            "operation": "highlight", "code": code,
            "language": language, "filename": filename.name if filename else None,
        })
        return f'<div class="codehilite"><pre>{response["value"]}</pre></div>\n'

    def css(self, style: str, scope: str) -> str:
        key = style, scope
        if key not in self.cached_css:
            self.cached_css[key] = str(self.worker.request({"operation": "css", "style": style, "scope": scope})["value"])
        return self.cached_css[key]


_rouge: Rouge | None = None
_lock = threading.Lock()


def rouge() -> Rouge:
    global _rouge
    with _lock:
        if _rouge is None:
            _rouge = Rouge()
    return _rouge


def styles(highlighter: str, light: str | None, dark: str | None) -> tuple[str, str]:
    if highlighter not in HIGHLIGHTERS:
        raise ValueError("highlighter must be " + " or ".join(HIGHLIGHTERS))
    defaults = DEFAULT_STYLES[highlighter]
    return light or defaults[0], dark or defaults[1]


def validate_styles(highlighter: str, light: str | None, dark: str | None) -> tuple[str, str]:
    light, dark = styles(highlighter, light, dark)
    if highlighter == "rouge":
        available = rouge().styles
        for style in (light, dark):
            if style not in available:
                raise ValueError(f"unknown Rouge style: {style}")
    else:
        try:
            get_style_by_name(light)
            get_style_by_name(dark)
        except ClassNotFound as error:
            raise ValueError(str(error)) from error
    return light, dark


def code_html(code: str, language: str = "text", filename: Path | None = None, highlighter: str = "pygments") -> str:
    language = LANGUAGE_ALIASES.get(language.lower(), language.lower())
    code = code.rstrip("\n") + "\n"
    if highlighter == "rouge":
        return rouge().highlight(code, language, filename)
    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        try:
            lexer = get_lexer_for_filename(filename.name) if filename else get_lexer_by_name("text")
        except ClassNotFound:
            lexer = get_lexer_by_name("text")
    return highlight(code, lexer, HtmlFormatter(cssclass="codehilite"))


def syntax_css(highlighter: str = "pygments", light: str | None = None, dark: str | None = None) -> str:
    light, dark = validate_styles(highlighter, light, dark)
    if highlighter == "rouge":
        generate = rouge().css
    else:
        generate = lambda style, scope: HtmlFormatter(style=style).get_style_defs(scope)
    light_css = generate(light, ".codehilite")
    dark_css = generate(dark, 'html[data-theme="dark"] .codehilite')
    automatic = generate(dark, 'html:not([data-theme="light"]) .codehilite')
    return light_css + "\n" + dark_css + "\n@media (prefers-color-scheme:dark){\n" + automatic + "\n}\n"
