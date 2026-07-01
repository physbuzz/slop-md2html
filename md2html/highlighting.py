from __future__ import annotations

import html
from pathlib import Path

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name, get_lexer_for_filename
from pygments.util import ClassNotFound


_SUFFIX_LANG = {
    ".py": "python",
    ".rkt": "rkt",
    ".scm": "scheme",
    ".ss": "scheme",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".js": "javascript",
    ".ts": "typescript",
    ".sh": "bash",
    ".bash": "bash",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
}


def language_for_path(path: str | Path) -> str:
    return _SUFFIX_LANG.get(Path(path).suffix.lower(), "text")


def _lexer(lang: str | None, *, filename: str | None = None):
    if lang:
        lang = lang.strip().split()[0]
        if lang:
            try:
                return get_lexer_by_name(lang)
            except ClassNotFound:
                pass
    if filename:
        try:
            return get_lexer_for_filename(filename)
        except ClassNotFound:
            pass
    return TextLexer()


def highlight_code(code: str, lang: str | None = None, *, filename: str | None = None) -> str:
    lexer = _lexer(lang, filename=filename)
    formatter = HtmlFormatter(cssclass="codehilite")
    try:
        return highlight(code, lexer, formatter)
    except Exception:
        escaped = html.escape(code)
        return f'<div class="codehilite"><pre><code>{escaped}</code></pre></div>\n'


def pygments_css(style: str = "default") -> str:
    return HtmlFormatter(style=style, cssclass="codehilite").get_style_defs(".codehilite")
