from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import mistune
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name, get_lexer_for_filename
from pygments.util import ClassNotFound

from .config import BuildOptions, MathConfig
from .context import BuildContext
from .frontmatter import dump_frontmatter
from .resources import package_resource_path

_TAG_RE = re.compile(r"<[^>]+>")
_LINK_RE = re.compile(r"!?\[([^\]]+)\]\([^\)]*\)")
_MARKDOWN_MARK_RE = re.compile(r"[`*_~]+")
_HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*#*\s*$")
_TOC_RE = re.compile(r"^\s*@toc\s*$", re.MULTILINE)
_EXERCISE_RE = re.compile(r"^exercise\b", re.IGNORECASE)
_FENCE_RE = re.compile(r"(```.*?```|~~~.*?~~~)", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"(`+)(.*?)(?<!`)\1", re.DOTALL)
_OBSIDIAN_IMAGE_RE = re.compile(r"!\[\[(?P<body>[^\]]+)\]\]")
_HTML_IMAGE_RE = re.compile(r"<img\b(?P<attrs>[^>]*)>", re.IGNORECASE)
_HTML_ATTR_RE = re.compile(r"""(?P<key>[-:\w]+)(?:\s*=\s*(?P<quote>["'])(?P<quoted>.*?)(?P=quote)|\s*=\s*(?P<bare>[^\s"'>]+))?""")
_FENCE_START_RE = re.compile(r"^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
_ESCAPED_DOLLAR_RE = re.compile(r"(?<!\\)\\\$")
_ASSETS_DIR = package_resource_path("assets")
_DEFAULT_TEMPLATE_DIR = package_resource_path("default_templates")
_TEMPLATE_CSS = {
    "super-barebones.html": "super-barebones.css",
    "barebones.html": "barebones.css",
    "page.html": "page.css",
}

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


def plain_text(value: str) -> str:
    value = html.unescape(value)
    value = _TAG_RE.sub("", value)
    value = _LINK_RE.sub(lambda m: m.group(1), value)
    value = _MARKDOWN_MARK_RE.sub("", value)
    return value.strip()


def slugify(value: str) -> str:
    value = plain_text(value).lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "section"


@dataclass
class Slugger:
    counts: dict[str, int] = field(default_factory=dict)

    def slug(self, value: str) -> str:
        base = slugify(value)
        count = self.counts.get(base, 0)
        self.counts[base] = count + 1
        if count == 0:
            return base
        return f"{base}-{count + 1}"


@dataclass(frozen=True)
class TocHeading:
    level: int
    title: str
    id: str
    line: int

    @property
    def text(self) -> str:
        return plain_text(self.title).strip()


@dataclass
class _TocNode:
    heading: TocHeading
    children: list["_TocNode"] = field(default_factory=list)


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
        headings.append(TocHeading(level=len(match.group("marks")), title=raw_title, id=slugger.slug(raw_title), line=lineno))
    return headings


def _link(heading: TocHeading, *, extra_class: str | None = None) -> str:
    klass = f' class="{html.escape(extra_class, quote=True)}"' if extra_class else ""
    return f'<a href="#{html.escape(heading.id, quote=True)}"{klass}>{html.escape(heading.text)}</a>'


def _exercise_list(headings: list[TocHeading]) -> str:
    if not headings:
        return ""
    links = "\n".join(f'<span>{_link(h)}</span>' for h in headings)
    return '<div class="exercise-container">(<span class="exercise-list">\n' f'{links}\n' '</span>)\n</div>'


def _markdown_link(heading: TocHeading) -> str:
    return f"[{heading.text}](#{heading.id})"


def _exercise_markdown_list(headings: list[TocHeading]) -> str:
    if not headings:
        return ""
    links = ", ".join(_markdown_link(h) for h in headings)
    return f"  - *Exercises:* ({links})"


def _toc_tree(headings: list[TocHeading]) -> list[_TocNode]:
    roots: list[_TocNode] = []
    stack: list[tuple[int, list[_TocNode]]] = [(0, roots)]
    for heading in headings:
        while stack and heading.level <= stack[-1][0]:
            stack.pop()
        node = _TocNode(heading)
        stack[-1][1].append(node)
        stack.append((heading.level, node.children))
    return roots


def generate_toc(headings: list[TocHeading], *, title: str = "Directory") -> str:
    if not headings:
        return ""

    exercises = [h for h in headings if _EXERCISE_RE.match(h.text)]
    exercise_ids = {h.id for h in exercises}
    tree = _toc_tree([h for h in headings if h.id not in exercise_ids])
    lines = ['<div class="table-of-contents">', f'<h2>{html.escape(title)}</h2>']

    def render_nodes(nodes: list[_TocNode], *, root: bool = False) -> None:
        lines.append('<ul class="toc-list">' if root else "<ul>")
        for node in nodes:
            heading = node.heading
            if heading.text.lower() == "exercises":
                lines.append(f'<li>{_link(heading, extra_class="toc-exercises")}')
                lines.append(_exercise_list(exercises))
            else:
                lines.append(f"<li>{_link(heading)}")
            if node.children:
                render_nodes(node.children)
            lines.append("</li>")
        lines.append("</ul>")

    render_nodes(tree, root=True)
    lines.append("</div>")
    return "\n".join(lines)


def generate_toc_markdown(headings: list[TocHeading], *, title: str = "Directory") -> str:
    if not headings:
        return ""

    exercises = [h for h in headings if _EXERCISE_RE.match(h.text)]
    exercise_ids = {h.id for h in exercises}
    lines = [f"## {title}"]
    for heading in headings:
        if heading.id in exercise_ids:
            continue
        indent = "  " * max(0, heading.level - 2)
        lines.append(f"{indent}- {_markdown_link(heading)}")
        if heading.text.lower() == "exercises":
            exercise_line = _exercise_markdown_list(exercises)
            if exercise_line:
                lines.append(f"{indent}{exercise_line}")
    return "\n".join(lines)


def replace_toc(markdown_text: str, toc: str) -> str:
    return _TOC_RE.sub(lambda _m: "\n" + toc + "\n", markdown_text)


def prepare_toc(markdown_text: str, *, output_mode: str = "html") -> tuple[str, list[TocHeading], str]:
    headings = collect_headings(markdown_text)
    toc = generate_toc_markdown(headings) if output_mode == "jekyll" else generate_toc(headings)
    return replace_toc(markdown_text, toc), headings, toc


@dataclass(frozen=True)
class MathSpan:
    placeholder: str
    text: str
    display: bool


def _protect_code(text: str) -> tuple[str, dict[str, str]]:
    stored: dict[str, str] = {}

    def store(match: re.Match[str]) -> str:
        key = f"@@MD2HTML_CODE_{len(stored)}@@"
        stored[key] = match.group(0)
        return key

    def store_inline(match: re.Match[str]) -> str:
        # A stray backtick pair (e.g. TeX-style ``quotes'') can pair up with a
        # much later backtick. A real code span never contains a blank line or
        # an already-protected fence, so leave those matches alone.
        content = match.group(0)
        if "\n\n" in content or "@@MD2HTML_CODE_" in content:
            return content
        return store(match)

    text = _FENCE_RE.sub(store, text)
    text = _INLINE_CODE_RE.sub(store_inline, text)
    return text, stored


def _restore_code(text: str, stored: dict[str, str]) -> str:
    # Inline spans are stored after fences and may contain fence placeholders,
    # so restore newest-first to resolve nesting.
    for key, value in reversed(stored.items()):
        text = text.replace(key, value)
    return text


def protect_math(text: str) -> tuple[str, list[MathSpan]]:
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


def render_math_span(span: MathSpan, config: MathConfig) -> str:
    raw = span.text
    source = raw[2:-2].strip() if span.display and raw.startswith("$$") else raw[1:-1]
    data_tex = html.escape(source, quote=True).replace("\n", "&#10;")
    rendered_source = html.escape(raw)

    if span.display:
        return f'<div class="math display" data-tex="{data_tex}">{rendered_source}</div>'
    return f'<span class="math inline" data-tex="{data_tex}">{rendered_source}</span>'


def restore_math(html_text: str, spans: list[MathSpan], config: MathConfig) -> str:
    for span in spans:
        rendered = render_math_span(span, config)
        if span.display:
            pattern = re.compile(r"<p>\s*" + re.escape(span.placeholder) + r"\s*</p>")
            html_text = pattern.sub(lambda _m, rendered=rendered: rendered, html_text)
        html_text = html_text.replace(span.placeholder, rendered)
    return html_text


def restore_math_markdown(markdown_text: str, spans: list[MathSpan]) -> str:
    for span in spans:
        markdown_text = markdown_text.replace(span.placeholder, span.text)
    return markdown_text


def preserve_escaped_dollars_markdown(markdown_text: str) -> str:
    code, stored = _protect_code(markdown_text)
    code = _ESCAPED_DOLLAR_RE.sub(lambda _m: r"\\$", code)
    return _restore_code(code, stored)


def _parse_image_parts(body: str) -> tuple[str, dict[str, str]]:
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


@dataclass(frozen=True)
class _ObsidianImage:
    url: str
    alt: str
    classes: list[str]
    style: str | None
    width: str | None


def _resolve_obsidian_image(match: re.Match[str], ctx: BuildContext, current_file: Path | None) -> _ObsidianImage:
    target, attrs = _parse_image_parts(match.group("body"))
    url = ctx.asset_url(target, current_file=current_file)
    alt = attrs.get("alt") or Path(target).stem.replace("-", " ").replace("_", " ")
    classes = ["obsidian-image"]
    default_class = ctx.options.images.class_name
    if default_class:
        classes.append(default_class)
    if attrs.get("class"):
        classes.extend(attrs["class"].split())
    width = attrs.get("width") or ctx.options.images.width
    style = width_attr = None
    if width:
        width = _normalize_width(width)
        if _looks_like_percent(width) or width.endswith(("px", "em", "rem")):
            style = f"width: {width};"
        else:
            width_attr = width
    return _ObsidianImage(url=url, alt=alt, classes=classes, style=style, width=width_attr)


def process_obsidian_images(text: str, ctx: BuildContext, *, current_file: Path | None = None) -> str:
    def repl(match: re.Match[str]) -> str:
        image = _resolve_obsidian_image(match, ctx, current_file)
        attr_bits = [f'src="{html.escape(image.url, quote=True)}"', f'alt="{html.escape(image.alt, quote=True)}"']
        if image.classes:
            attr_bits.append(f'class="{html.escape(" ".join(image.classes), quote=True)}"')
        if image.style:
            attr_bits.append(f'style="{html.escape(image.style, quote=True)}"')
        elif image.width:
            attr_bits.append(f'width="{html.escape(image.width, quote=True)}"')
        return "<img " + " ".join(attr_bits) + ">"

    return _OBSIDIAN_IMAGE_RE.sub(repl, text)


def process_obsidian_images_markdown(text: str, ctx: BuildContext, *, current_file: Path | None = None) -> str:
    def repl(match: re.Match[str]) -> str:
        image = _resolve_obsidian_image(match, ctx, current_file)
        attr_bits = [f".{klass}" for klass in image.classes]
        if image.style:
            attr_bits.append(f'style="{image.style}"')
        elif image.width:
            attr_bits.append(f'width="{image.width}"')
        attrs_text = "{: " + " ".join(attr_bits) + "}" if attr_bits else ""
        return f"![{image.alt}]({image.url}){attrs_text}"

    return _OBSIDIAN_IMAGE_RE.sub(repl, text)


def _parse_html_attrs(raw_attrs: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in _HTML_ATTR_RE.finditer(raw_attrs):
        key = match.group("key").lower()
        value = match.group("quoted")
        if value is None:
            value = match.group("bare")
        attrs[key] = value or ""
    return attrs


def queue_html_image_assets(text: str, ctx: BuildContext, *, current_file: Path | None = None) -> None:
    for match in _HTML_IMAGE_RE.finditer(text):
        src = _parse_html_attrs(match.group("attrs")).get("src")
        if src:
            ctx.asset_url(src, current_file=current_file)


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


def render_fenced_code_blocks(markdown_text: str) -> str:
    lines = markdown_text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = _FENCE_START_RE.match(line.rstrip("\r\n"))
        if not match:
            out.append(line)
            i += 1
            continue

        fence = match.group("fence")
        fence_char = fence[0]
        fence_len = len(fence)
        info = match.group("info").strip()
        lang = info.split(None, 1)[0] if info else None
        code_lines: list[str] = []
        i += 1
        closed = False
        close_re = re.compile(rf"^[ \t]{{0,3}}{re.escape(fence_char)}{{{fence_len},}}\s*$")

        while i < len(lines):
            candidate = lines[i]
            if close_re.match(candidate.rstrip("\r\n")):
                closed = True
                i += 1
                break
            code_lines.append(candidate)
            i += 1

        if closed:
            out.append(highlight_code("".join(code_lines), lang))
        else:
            out.append(line)
            out.extend(code_lines)

    return "".join(out)


def pygments_css(style: str = "default") -> str:
    return HtmlFormatter(style=style, cssclass="codehilite").get_style_defs(".codehilite")


def jekyll_compat_css() -> str:
    return pygments_css() + "\n\n" + "\n".join(
        [
            ".codehilite { background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px; margin: 1rem 0 1.5rem; overflow-x: auto; }",
            ".codehilite pre { margin: 0; padding: 1rem; overflow-x: auto; }",
            ".codehilite code { padding: 0; background: transparent; }",
            ".code-box { background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px; overflow: hidden; margin: 1rem 0 1.5rem; }",
            ".code-box .codehilite { margin: 0; border: none; border-radius: 0; }",
            ".code-box .codehilite pre { padding: .25rem .4rem .35rem; }",
            ".code-header, .code-summary, .code-output { font-family: SFMono-Regular, Consolas, \"Liberation Mono\", Menlo, monospace; font-size: .75rem; color: #6a737d; background: #fafbfc; }",
            ".code-header { padding: .3rem .4rem; border-bottom: 1px solid #e1e4e8; }",
            ".code-output { padding: .3rem .4rem; border-top: 1px solid #e1e4e8; }",
            ".code-output pre { margin: .25rem 0 0; white-space: pre-wrap; }",
            ".code-output span { color: #aa2da5; }",
            ".collapsible-code { border: none; margin: 0; }",
            ".code-summary { padding: .5rem .8rem .5rem 2rem; border-bottom: 1px solid #e1e4e8; cursor: pointer; list-style: none; position: relative; }",
            ".code-summary::before { content: '►'; position: absolute; left: .8rem; top: 50%; transform: translateY(-50%); font-size: .7em; transition: transform .15s ease; }",
            ".collapsible-code[open] > .code-summary::before { transform: translateY(-50%) rotate(90deg); }",
            ".expand-hint { font-style: italic; color: #888; margin-left: .5rem; }",
            ".table-of-contents { margin: 0 0 .8rem; padding: 0; font-size: .9rem; line-height: 1.2; }",
            ".table-of-contents h2 { margin: 0 0 .25rem; font-size: 1.1rem; }",
            ".toc-list, .toc-list ul { margin: 0; padding-left: 1rem; }",
            ".toc-list li { margin-bottom: 2px; }",
            ".exercise-container { display: inline-block; margin-left: .25rem; line-height: 1.2; }",
            ".exercise-list { display: inline; padding-left: 0; font-size: .95em; }",
            ".exercise-list span:not(:last-child)::after { content: ', '; color: #777; }",
            ".toc-exercises { font-style: italic; color: #555; }",
            ".obsidian-image { display: block; margin: 1rem auto; }",
            ".md2html-warning { border-left: 4px solid #d29922; background: #fff8c5; padding: .75rem 1rem; margin: 1rem 0; }",
        ]
    ) + "\n"


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


def bundled_template_text(template_name: str) -> str:
    return (_DEFAULT_TEMPLATE_DIR / template_name).read_text(encoding="utf-8")


def asset_css(name: str) -> str:
    return (_ASSETS_DIR / name).read_text(encoding="utf-8")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        return [value]
    return list(value)


def _companion_css_path(template_name: str, options: BuildOptions) -> Path | None:
    css_name = Path(template_name).with_suffix(".css")
    for directory in options.template_dirs:
        candidate = directory / css_name
        if candidate.exists():
            return candidate
    return None


def _default_css_refs(template_name: str, options: BuildOptions) -> list[str | Path]:
    companion = _companion_css_path(template_name, options)
    if companion is not None:
        return [companion]
    bundled = _TEMPLATE_CSS.get(Path(template_name).name)
    if bundled:
        return [bundled]
    return ["super-barebones.css"]


def _configured_css_refs(metadata: dict[str, Any], options: BuildOptions, template_name: str) -> list[str | Path]:
    if metadata.get("css") is not None:
        return _as_list(metadata["css"])
    if options.css is not None:
        return list(options.css)
    return _default_css_refs(template_name, options)


def _read_css_ref(ref: str | Path, options: BuildOptions) -> str:
    path = Path(ref).expanduser()
    if path.is_absolute():
        candidates = [path]
    else:
        candidates = [options.project_root / path, *[directory / path for directory in options.template_dirs], _ASSETS_DIR / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    raise FileNotFoundError(f"CSS file does not exist: {ref}")


def embedded_css_for_template(template_name: str, options: BuildOptions, metadata: dict[str, Any] | None = None) -> str:
    metadata = metadata or {}
    parts = [pygments_css()]
    parts.extend(_read_css_ref(ref, options) for ref in _configured_css_refs(metadata, options, template_name))
    return "\n\n".join(part.rstrip() for part in parts if part.strip()) + "\n"


def make_environment(options: BuildOptions) -> Environment:
    dirs = [*(str(p) for p in options.template_dirs), str(_DEFAULT_TEMPLATE_DIR)]
    return Environment(
        loader=FileSystemLoader(dirs),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_template(
    *,
    content: str,
    title: str,
    metadata: dict[str, Any],
    options: BuildOptions,
    template_name: str | None = None,
) -> str:
    env = make_environment(options)
    name = template_name or options.template
    template = env.get_template(name)
    css = ""
    stylesheets = [*options.stylesheets, *_as_list(metadata.get("stylesheets"))]
    if options.embed_assets:
        css = embedded_css_for_template(name, options, metadata)
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


def render_jekyll_markdown(
    *,
    content: str,
    title: str,
    metadata: dict[str, Any],
    options: BuildOptions,
) -> str:
    frontmatter = dict(options.jekyll.frontmatter)
    frontmatter.update({key: value for key, value in metadata.items() if key != "template"})
    if options.jekyll.layout and "layout" not in frontmatter:
        frontmatter["layout"] = options.jekyll.layout
    frontmatter["title"] = title
    return dump_frontmatter(frontmatter) + content
