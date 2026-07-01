from __future__ import annotations

import html

import mistune

from .context import BuildContext
from .highlighting import highlight_code
from .slug import Slugger


class Md2HtmlRenderer(mistune.HTMLRenderer):
    def __init__(self, ctx: BuildContext | None = None) -> None:
        super().__init__(escape=False)
        self.ctx = ctx
        self.slugger = Slugger()

    def heading(self, text: str, level: int, **attrs) -> str:
        ident = attrs.get("id") or self.slugger.slug(text)
        return f'<h{level} id="{html.escape(ident, quote=True)}">{text}</h{level}>\n'

    def block_code(self, code: str, info: str | None = None) -> str:
        lang = None
        if info:
            lang = info.strip().split(None, 1)[0]
        return highlight_code(code, lang)

    def image(self, text: str, url: str, title: str | None = None) -> str:
        final_url = url
        if self.ctx is not None:
            final_url = self.ctx.asset_url(url, current_file=self.ctx.source_path)
        attrs = [f'src="{html.escape(final_url, quote=True)}"', f'alt="{html.escape(text or "", quote=True)}"']
        if title:
            attrs.append(f'title="{html.escape(title, quote=True)}"')
        return "<img " + " ".join(attrs) + ">"


def render_markdown(markdown_text: str, ctx: BuildContext | None = None) -> str:
    renderer = Md2HtmlRenderer(ctx)
    markdown = mistune.create_markdown(
        renderer=renderer,
        plugins=["table", "strikethrough", "task_lists", "url"],
        escape=False,
    )
    return markdown(markdown_text)
