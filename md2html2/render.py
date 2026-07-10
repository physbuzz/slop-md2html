"""The shared content-rendering pipeline.

Content is protected before Liquid sees it, then Markdown is rendered exactly
once. This keeps code, Mathematica braces, and TeX independent of both engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import html
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
from typing import Any, Callable, Iterable

import mistune
from liquid import Environment, FileSystemLoader
from liquid.exceptions import LiquidError
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.util import ClassNotFound

from .settings import Settings


FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
FENCE = re.compile(r"^([ \t]*)(`{3,}|~{3,})[ \t]*([^\n]*)\n(.*?)^\1\2[ \t]*$", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`)([^\n]*?(?:\n[^\n]*?)?)(?<!`)\1(?!`)")
RAW_CODE = re.compile(r"<(pre|code)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
RAW_HIGHLIGHT = re.compile(r"<div\b[^>]*class=[\"'][^\"']*(?:codehilite|highlight)[^\"']*[\"'][^>]*>.*?</div>", re.IGNORECASE | re.DOTALL)
RAW_COMMENT = re.compile(r"<!--[\s\S]*?-->")
HIGHLIGHT = re.compile(r"{%\s*highlight\s+([\w+.-]+)\s*%}(.*?){%\s*endhighlight\s*%}", re.DOTALL)
SRC_BLOCK = re.compile(r"^@src-begin\(([^)]*)\)[ \t]*\r?\n(.*?)^@src-end[ \t]*$", re.MULTILINE | re.DOTALL)
DIRECTIVE = re.compile(r"^[ \t]*@(include|src)\(([^)]*)\)[ \t]*$", re.MULTILINE)
TOC = re.compile(r"^[ \t]*@toc[ \t]*$", re.MULTILINE)
HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)
ALIGN = re.compile(r"\\begin\{(align\*?|gather\*?|multline\*?|equation\*?)\}.*?\\end\{\1\}", re.DOTALL)

LANGUAGE_ALIASES = {"wl": "mathematica", "mma": "mathematica", "rkt": "racket", "py": "python", "js": "javascript"}
LANGUAGE_SUFFIXES = {"python": ".py", "py": ".py", "javascript": ".js", "js": ".js", "racket": ".rkt", "cpp": ".cpp", "c++": ".cpp", "c": ".c", "bash": ".sh", "shell": ".sh", "sh": ".sh", "wl": ".wl", "mathematica": ".wl"}
COMMANDS = {
    ".py": "{python} {source}",
    ".sh": "bash {source}",
    ".bash": "bash {source}",
    ".rkt": "racket {source}",
    ".js": "node {source}",
    ".wl": "wolframscript -file {source}",
    ".m": "wolframscript -file {source}",
}


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER.match(text)
    if not match:
        return {}, text
    import yaml

    try:
        metadata = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as error:
        raise ValueError(f"invalid front matter: {error}") from error
    if not isinstance(metadata, dict):
        raise ValueError("front matter must contain a mapping")
    return metadata, text[match.end():]


def slugify(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE).strip().lower()
    return re.sub(r"[-\s]+", "-", value) or "section"


def liquid_source(value: str) -> str:
    """Accept Jekyll's convenient unquoted static include names."""
    return re.sub(
        r"{%\s*include\s+([A-Za-z0-9_./-]+)\s*%}",
        lambda match: "{% include '" + match.group(1) + "' %}",
        value,
    )


class HeadingRenderer(mistune.HTMLRenderer):
    def __init__(self) -> None:
        super().__init__(escape=False)
        self.seen: dict[str, int] = {}

    def heading(self, text: str, level: int, **attrs: Any) -> str:
        base = slugify(text)
        count = self.seen.get(base, 0)
        self.seen[base] = count + 1
        identifier = base if count == 0 else f"{base}-{count + 1}"
        return f'<h{level} id="{identifier}">{text}</h{level}>\n'


@dataclass
class Features:
    code: bool = False
    output: bool = False
    math: bool = False
    toc: bool = False
    images: bool = False
    warning: bool = False
    math_css: str = ""
    math_font_dir: Path | None = None
    math_fonts: set[str] = field(default_factory=set)


@dataclass
class Rendered:
    html: str
    title: str
    features: Features
    dependencies: set[Path] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)


class Stash:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.serial = 0

    def put(self, value: str, *, block: bool) -> str:
        self.serial += 1
        key = f"m{self.serial}"
        self.values[key] = value
        tag = "div" if block else "span"
        return f'<{tag} data-md2html-token="{key}"></{tag}>'

    def restore(self, text: str) -> str:
        for key, value in self.values.items():
            for tag in ("div", "span"):
                text = text.replace(f'<{tag} data-md2html-token="{key}"></{tag}>', value)
        return text


def _lexer(language: str, filename: Path | None = None):
    language = LANGUAGE_ALIASES.get(language.lower(), language.lower())
    try:
        return get_lexer_by_name(language)
    except ClassNotFound:
        if filename:
            try:
                return get_lexer_for_filename(filename.name)
            except ClassNotFound:
                pass
    return get_lexer_by_name("text")


def code_html(code: str, language: str = "text", filename: Path | None = None) -> str:
    return highlight(code.rstrip("\n") + "\n", _lexer(language, filename), HtmlFormatter(cssclass="highlight"))


def split_args(value: str) -> tuple[str, set[str]]:
    parts = [part.strip() for part in value.split(",")]
    return (parts[0] if parts else ""), {part.lower() for part in parts[1:] if part}


class Executor:
    def __init__(self, settings: Settings, warn: Callable[[str], None]) -> None:
        self.settings = settings
        self.warn = warn
        self.cache = settings.project_root / ".md2html-cache"

    def run(self, source: Path, code: str, language: str, inline: bool) -> str | None:
        custom = self.settings.commands.get(language) or self.settings.commands.get(source.suffix.lstrip("."))
        suffix = LANGUAGE_SUFFIXES.get(language.lower(), "." + language) if inline else (source.suffix or "." + language)
        cache_key = hashlib.sha256((str(source.resolve()) + "\0" + code + "\0" + str(custom)).encode()).hexdigest()
        cache_file = self.cache / f"{cache_key}.out"
        if self.settings.output_mode == "site" and cache_file.exists() and not self.settings.regenerate:
            return cache_file.read_text(encoding="utf-8")
        temporary: tempfile.TemporaryDirectory[str] | None = None
        run_source = source
        workdir = source.parent
        try:
            if inline:
                temporary = tempfile.TemporaryDirectory(prefix="md2html-")
                run_source = Path(temporary.name) / ("source" + suffix)
                run_source.write_text(code, encoding="utf-8")
            command = custom or COMMANDS.get(suffix.lower())
            if suffix.lower() in {".cc", ".cpp", ".cxx", ".c"} and custom is None:
                compiler = "cc" if suffix.lower() == ".c" else "c++"
                executable = run_source.with_suffix(".bin")
                compile_result = subprocess.run(
                    [compiler, str(run_source), "-o", str(executable)], cwd=workdir,
                    text=True, capture_output=True, timeout=60,
                )
                if compile_result.returncode:
                    self.warn(f"could not compile {source}: {compile_result.stderr.strip()}")
                    return None
                argv = [str(executable)]
            elif command:
                formatted = command.format(
                    source=shlex.quote(str(run_source)), python=shlex.quote(sys.executable),
                    output=shlex.quote(str(run_source.with_suffix(".out"))),
                )
                argv = ["sh", "-c", formatted]
            else:
                self.warn(f"no execution command is configured for {language or suffix}")
                return None
            result = subprocess.run(argv, cwd=workdir, text=True, capture_output=True, timeout=120)
            if result.returncode:
                detail = result.stderr.strip() or f"exit status {result.returncode}"
                self.warn(f"execution failed for {source}: {detail}")
                return None
            output = result.stdout
            if self.settings.output_mode == "site":
                self.cache.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(output, encoding="utf-8")
            return output
        except (OSError, subprocess.TimeoutExpired) as error:
            self.warn(f"could not execute {source}: {error}")
            return None
        finally:
            if temporary:
                temporary.cleanup()


class ContentRenderer:
    def __init__(self, settings: Settings, liquid: Environment) -> None:
        self.settings = settings
        self.liquid = liquid

    def render(self, source: Path, body: str, context: dict[str, Any], *, markdown: bool = True) -> Rendered:
        stash = Stash()
        features = Features()
        dependencies: set[Path] = {source}
        warnings: list[str] = []
        executor = Executor(self.settings, warnings.append)

        def protect_raw(match: re.Match[str]) -> str:
            return stash.put(match.group(0), block=match.group(1).lower() == "pre")

        body = RAW_COMMENT.sub(lambda match: stash.put(match.group(0), block=True), body)
        body = RAW_HIGHLIGHT.sub(lambda match: stash.put(match.group(0), block=True), body)
        body = RAW_CODE.sub(protect_raw, body)

        def protect_highlight(match: re.Match[str]) -> str:
            features.code = True
            return stash.put(code_html(match.group(2), match.group(1)), block=True)

        body = HIGHLIGHT.sub(protect_highlight, body)

        def inline_block(match: re.Match[str]) -> str:
            language, flags = split_args(match.group(1))
            code = match.group(2)
            return self._source_box(source, code, language, flags, True, executor, stash, features)

        body = SRC_BLOCK.sub(inline_block, body)
        body = self._expand_directives(body, source, context, stash, features, dependencies, warnings, executor, ())

        def protect_fence(match: re.Match[str]) -> str:
            features.code = True
            language = match.group(3).strip().split(maxsplit=1)[0] if match.group(3).strip() else "text"
            return stash.put(code_html(match.group(4), language), block=True)

        body = FENCE.sub(protect_fence, body)
        body = INLINE_CODE.sub(lambda m: stash.put(f"<code>{html.escape(m.group(2).strip())}</code>", block=False), body)
        body = self._protect_math(body, stash, features, warnings)

        if TOC.search(body):
            features.toc = True
            toc = self._toc(body)
            body = TOC.sub(stash.put(toc, block=True), body)

        try:
            body = self.liquid.from_string(liquid_source(body)).render(**context)
        except LiquidError as error:
            warnings.append(f"template expression failed in {source}: {error}")

        if markdown:
            renderer = HeadingRenderer()
            md = mistune.create_markdown(renderer=renderer, plugins=["strikethrough", "table", "task_lists", "url"])
            output = md(body)
        else:
            output = body
        output = stash.restore(output)
        features.images = bool(re.search(r"<img\b", output, re.IGNORECASE))
        features.warning = 'class="warning"' in output
        title = str(context.get("page", {}).get("title") or self._first_title(body) or source.stem)
        return Rendered(output, title, features, dependencies, warnings)

    def _expand_directives(
        self, body: str, origin: Path, context: dict[str, Any], stash: Stash, features: Features,
        dependencies: set[Path], warnings: list[str], executor: Executor, stack: tuple[Path, ...],
    ) -> str:
        def replace(match: re.Match[str]) -> str:
            kind, raw = match.group(1), match.group(2)
            name, flags = split_args(raw)
            path = (origin.parent / name).resolve()
            if path in stack or path == origin.resolve() and kind == "include":
                chain = " -> ".join(str(item) for item in (*stack, path))
                warnings.append(f"include cycle: {chain}")
                return stash.put('<aside class="warning">Include cycle omitted.</aside>', block=True)
            try:
                value = path.read_text(encoding="utf-8")
            except OSError as error:
                warnings.append(f"could not read {path}: {error}")
                return stash.put(f'<aside class="warning">Could not read {html.escape(name)}.</aside>', block=True)
            dependencies.add(path)
            if kind == "include":
                _, value = parse_frontmatter(value)
                return self._expand_directives(
                    value, path, context, stash, features, dependencies, warnings, executor, (*stack, origin.resolve()),
                )
            language = path.suffix.lstrip(".") or "text"
            return self._source_box(path, value, language, flags, False, executor, stash, features)

        previous = None
        while previous != body:
            previous = body
            body = DIRECTIVE.sub(replace, body)
        return body

    def _source_box(
        self, source: Path, code: str, language: str, flags: set[str], inline: bool,
        executor: Executor, stash: Stash, features: Features,
    ) -> str:
        features.code = True
        code_markup = code_html(code, language, source)
        collapsible = bool(flags & {"collapsed", "collapsible", "expanded"})
        if collapsible:
            open_attr = " open" if "expanded" in flags else ""
            label = html.escape(source.name if not inline else f"{language} source")
            code_markup = f'<details class="source"{open_attr}><summary>{label}</summary>{code_markup}</details>'
        should_run = self.settings.execute and "noexecute" not in flags
        if "execute" in flags and not self.settings.execute:
            executor.warn(f"execution requested for {source}; rerun with --execute")
        output = executor.run(source, code, language, inline) if should_run else None
        if output is not None:
            features.output = True
            code_markup += f'<pre class="code-output"><code>{html.escape(output)}</code></pre>'
        return stash.put(code_markup, block=True)

    def _protect_math(self, body: str, stash: Stash, features: Features, warnings: list[str]) -> str:
        backend = self.settings.math.backend.lower()

        def emit(tex: str, display: bool) -> str:
            features.math = True
            try:
                if backend == "mathml":
                    from latex2mathml.converter import convert
                    markup = convert(tex)
                elif backend == "svg":
                    import ziamath
                    markup = ziamath.Latex(tex, inline=not display).svg()
                elif backend == "mathjax-chtml":
                    from .mathjax import render_chtml
                    rendered = render_chtml(tex, display)
                    markup = rendered.html
                    features.math_css = rendered.css
                    features.math_font_dir = rendered.font_dir
                    features.math_fonts.add("zero")
                    features.math_fonts.update(name.lower() for name in re.findall(r"\bTEX-([A-Z0-9]+)\b", markup))
                    if "mjx-break" in markup:
                        features.math_fonts.add("brk")
                else:
                    delimiter = "$$" if display else "$"
                    markup = delimiter + tex + delimiter
            except Exception as error:
                warnings.append(f"could not render TeX; leaving source in place: {error}")
                delimiter = "$$" if display else "$"
                markup = delimiter + tex + delimiter
            class_name = "math display-math" if display else "math inline-math"
            tag = "div" if display else "span"
            return stash.put(f'<{tag} class="{class_name}" data-tex="{html.escape(tex, quote=True)}">{markup}</{tag}>', block=display)

        result: list[str] = []
        index = 0
        while index < len(body):
            if body[index] == "\\" and index + 1 < len(body):
                result.append(body[index:index + 2])
                index += 2
                continue
            if body[index] != "$":
                result.append(body[index])
                index += 1
                continue
            display = index + 1 < len(body) and body[index + 1] == "$"
            width = 2 if display else 1
            end = index + width
            while True:
                end = body.find("$" * width, end)
                if end < 0:
                    result.append(body[index:index + width])
                    index += width
                    break
                if end == 0 or body[end - 1] != "\\":
                    tex = body[index + width:end]
                    if tex and (display or "\n" not in tex):
                        result.append(emit(tex, display))
                        index = end + width
                        break
                end += width
        return ALIGN.sub(lambda match: emit(match.group(0), True), "".join(result))

    @staticmethod
    def _first_title(body: str) -> str | None:
        match = HEADING.search(body)
        return re.sub(r"[*_`<>{}]", "", match.group(2)).strip() if match else None

    @staticmethod
    def _toc(body: str) -> str:
        rows: list[str] = []
        seen: dict[str, int] = {}
        for match in HEADING.finditer(body):
            level = len(match.group(1))
            if level == 1:
                continue
            label = re.sub(r"<[^>]+>|[*_`]", "", match.group(2)).strip()
            base = slugify(label)
            count = seen.get(base, 0)
            seen[base] = count + 1
            identifier = base if count == 0 else f"{base}-{count + 1}"
            rows.append(f'<li class="toc-level-{level}"><a href="#{identifier}">{html.escape(label)}</a></li>')
        return '<nav class="toc" aria-label="Table of contents"><ol>' + "".join(rows) + "</ol></nav>"


def make_liquid(template_dirs: Iterable[Path], site: dict[str, Any]) -> Environment:
    directories = [path for path in template_dirs if path.is_dir()]
    environment = Environment(loader=FileSystemLoader(directories), strict_filters=False, autoescape=False)

    def relative_url(value: Any) -> str:
        path = str(value or "")
        base = str(site.get("baseurl", "")).rstrip("/")
        return base + "/" + path.lstrip("/")

    def absolute_url(value: Any) -> str:
        return str(site.get("url", "")).rstrip("/") + relative_url(value)

    environment.add_filter("relative_url", relative_url)
    environment.add_filter("absolute_url", absolute_url)
    return environment
