"""The shared content-rendering pipeline.

Content is protected before Liquid sees it, then Markdown is rendered exactly
once. This keeps code, Mathematica braces, and TeX independent of both engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any, Callable, Iterable

import mistune
from liquid import Environment, FileSystemLoader
from liquid.exceptions import LiquidError
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.util import ClassNotFound

from .settings import Settings, atomic_write, normal_path


FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
FENCE = re.compile(r"^([ \t]*)(`{3,}|~{3,})[ \t]*([^\n]*)\n(.*?)^\1\2[ \t]*$", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`)([^\n]*?(?:\n[^\n]*?)?)(?<!`)\1(?!`)")
RAW_CODE = re.compile(r"<(pre|code)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
RAW_HIGHLIGHT = re.compile(r"<div\b[^>]*class=[\"'][^\"']*(?:codehilite|highlight)[^\"']*[\"'][^>]*>.*?</div>", re.IGNORECASE | re.DOTALL)
RAW_COMMENT = re.compile(r"<!--[\s\S]*?-->")
OBSIDIAN_IMAGE = re.compile(r"!\[\[([^\]\n]+)\]\]")
HIGHLIGHT = re.compile(r"{%\s*highlight\s+([\w+.-]+)\s*%}(.*?){%\s*endhighlight\s*%}", re.DOTALL)
SRC_BLOCK = re.compile(r"^@src-begin\(([^)]*)\)[ \t]*\r?\n(.*?)^@src-end[ \t]*$", re.MULTILINE | re.DOTALL)
SRC_BEGIN_LINE = re.compile(r"^[ \t]*@src-begin\([^)]*\)[ \t]*$")
SRC_END_LINE = re.compile(r"^[ \t]*@src-end[ \t]*$")
DIRECTIVE = re.compile(r"^[ \t]*@(include|src)\(([^)]*)\)[ \t]*$", re.MULTILINE)
MALFORMED_SRC = re.compile(r"^[ \t]*@src\([^\n)]*$", re.MULTILINE)
TOC = re.compile(r"^[ \t]*@toc[ \t]*$", re.MULTILINE)
HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)
EXERCISE = re.compile(r"^exercise\b", re.IGNORECASE)
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
    ".c": "cc {source} -o {executable} && {executable}",
    ".cc": "c++ {source} -o {executable} && {executable}",
    ".cpp": "c++ {source} -o {executable} && {executable}",
    ".cxx": "c++ {source} -o {executable} && {executable}",
}


class TrackingLoader(FileSystemLoader):
    def __init__(self, paths: Iterable[Path]) -> None:
        super().__init__(paths)
        self.dependencies: set[Path] = set()

    def get_source(self, env: Environment, template_name: str, **kwargs: Any):
        try:
            source = super().get_source(env, template_name, **kwargs)
        except LiquidError:
            self.dependencies.update(normal_path(Path(path) / template_name) for path in self.search_path)
            raise
        self.dependencies.add(normal_path(Path(source.name)))
        return source


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
    def __init__(self, features: Features | None = None) -> None:
        super().__init__(escape=False)
        self.seen: dict[str, int] = {}
        self.features = features

    def image(self, text: str, url: str, title: str | None = None) -> str:
        if self.features:
            self.features.images = True
        return super().image(text, url, title)

    def heading(self, text: str, level: int, **attrs: Any) -> str:
        base = slugify(text)
        count = self.seen.get(base, 0)
        self.seen[base] = count + 1
        identifier = base if count == 0 else f"{base}-{count + 1}"
        return f'<h{level} id="{identifier}">{text}</h{level}>\n'


@dataclass(frozen=True)
class TocHeading:
    level: int
    label: str
    identifier: str


@dataclass
class TocNode:
    heading: TocHeading
    children: list["TocNode"] = field(default_factory=list)


@dataclass
class Features:
    code: bool = False
    math: bool = False
    math_copy: bool = False
    toc: bool = False
    images: bool = False
    warning: bool = False
    math_css: str = ""
    math_font_dir: Path | None = None
    math_fonts: set[str] = field(default_factory=set)


@dataclass
class Rendered:
    content: str
    features: Features
    dependencies: set[Path] = field(default_factory=set)
    assets: dict[Path, Path] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    executor: Executor | None = field(default=None, repr=False)


class Stash:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.serial = 0

    def put(self, value: str, *, block: bool) -> str:
        self.serial += 1
        tag = "div" if block else "span"
        placeholder = f'<{tag} data-md2html-token="m{self.serial}"></{tag}>'
        self.values[placeholder] = value
        suffix = "\n" if block else ""
        return placeholder + suffix

    def restore(self, text: str) -> str:
        for placeholder, value in self.values.items():
            text = text.replace(placeholder, value)
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
    return highlight(code.rstrip("\n") + "\n", _lexer(language, filename), HtmlFormatter(cssclass="codehilite"))


def _multiline_math(source: str) -> bool:
    compact = re.sub(r"\s+", "", source)
    return "\\\\" in source or any(f"\\begin{{{name}" in compact for name in ("align", "aligned", "gather", "split", "multline"))


def _svg_math(source: str, display: bool) -> str:
    import ziamath
    from latex2mathml.converter import convert

    svg = ziamath.Math(convert(source, display="block" if display else "inline")).svg()
    identifiers = sorted(set(re.findall(r'\bid="([^"]+)"', svg)), key=len, reverse=True)
    prefix = "md2html-math-" + hashlib.sha1(source.encode()).hexdigest()[:10]
    for identifier in identifiers:
        replacement = f"{prefix}-{identifier}"
        svg = svg.replace(f'id="{identifier}"', f'id="{replacement}"')
        svg = svg.replace(f'href="#{identifier}"', f'href="#{replacement}"')
        svg = svg.replace(f'xlink:href="#{identifier}"', f'xlink:href="#{replacement}"')
    match = re.search(r'\bviewBox="([^"]+)"', svg)
    try:
        _, minimum_y, _, height = (float(part) for part in match.group(1).split()) if match else (0, 0, 0, 0)
    except ValueError:
        minimum_y = height = 0
    depth = max(0.0, min(1.0, (minimum_y + height) / height)) if height > 0 else .15
    inline_height = max(1.05, min(1.7, height * .049)) if height > 0 else 1.15
    display_height = max(1.0, height * (.82 if _multiline_math(source) else .72) / 16) if height > 0 else 1.0
    style = (
        f"--md2html-math-svg-depth:{depth:.4f};"
        f"--md2html-math-svg-inline-height:{inline_height:.4f}em;"
        f"--md2html-math-svg-inline-align:{-inline_height * depth:.4f}em;"
        f"--md2html-math-svg-display-height:{display_height:.4f}em"
    )
    svg = svg.replace('fill="black"', 'fill="currentColor"').replace('stroke="black"', 'stroke="currentColor"')
    return re.sub(r"<svg\b", f'<svg class="md2html-math-svg-image" fill="currentColor" style="{style}"', svg, count=1)


def _mathml(source: str, display: bool) -> str:
    from latex2mathml.converter import convert

    markup = convert(source, display="block" if display else "inline")
    if display:
        if _multiline_math(source):
            scale = 1.12
        elif re.search(r"\\(?:int|iint|iiint|oint|sum|prod)(?![A-Za-z])", source) and ("_" in source or "^" in source):
            scale = 1.45
        else:
            scale = 1.18 if len(re.sub(r"\s+", "", source)) > 140 else 1.12
        style = f' style="--md2html-mathml-display-scale:{scale:.2f}"'
    else:
        style = ""
    return re.sub(r"<math\b", f'<math class="md2html-mathml"{style}', markup, count=1)


def split_args(value: str) -> tuple[str, set[str]]:
    parts = [part.strip() for part in value.split(",")]
    return (parts[0] if parts else ""), {part.lower() for part in parts[1:] if part}


class Executor:
    def __init__(self, settings: Settings, page: Path, warn: Callable[[str], None]) -> None:
        self.settings = settings
        self.warn = warn
        self.page = page
        self.cache = self.page_root(settings, page)
        self.active: set[Path] = set()
        self.cleanup_safe = True

    @staticmethod
    def _slug(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-.") or "source"

    @classmethod
    def pages_root(cls, settings: Settings) -> Path:
        return settings.project_root / ".md2html-cache" / "pages"

    @classmethod
    def page_root(cls, settings: Settings, page: Path) -> Path:
        parts = [cls._slug(part) for part in page.parts if part not in {"", ".", "..", page.anchor}]
        return cls.pages_root(settings).joinpath(*(parts or ["index.html"]))

    def _workspace(self, source: Path, code: str, language: str, inline: bool) -> tuple[Path, str]:
        slug = self._slug(language or "source") if inline else self._slug(source.stem)
        name = self._slug(language or source.suffix.lstrip(".") or "source")
        builddir = self.cache / f"{name}-{hashlib.sha256(code.encode()).hexdigest()[:12]}"
        self.active.add(builddir)
        return builddir, slug

    def run(self, source: Path, code: str, language: str, inline: bool, *, enabled: bool, use_cache: bool) -> str | None:
        custom = self.settings.commands.get(language) or self.settings.commands.get(source.suffix.lstrip("."))
        suffix = LANGUAGE_SUFFIXES.get(language.lower(), "." + language) if inline else (source.suffix or "." + language)
        command = custom or COMMANDS.get(suffix.lower())
        builddir, slug = self._workspace(source, code, language, inline)
        output_path = builddir / "output.txt"
        complete = builddir / ".complete"
        if use_cache and output_path.is_file() and complete.is_file() and (not self.settings.force or not enabled):
            complete.touch()
            return output_path.read_text(encoding="utf-8")
        if not enabled:
            return None
        if command is None:
            self.warn(f"no execution command is configured for {language or suffix}")
            return None
        run_source = source
        try:
            if builddir.exists():
                shutil.rmtree(builddir)
            builddir.mkdir(parents=True)
            if inline:
                run_source = builddir / (slug + suffix)
                run_source.write_text(code, encoding="utf-8")
            executable = builddir / f"{slug}.md2html-out"

            def relative(path: Path) -> str:
                return shlex.quote(os.path.relpath(path, builddir))

            try:
                formatted = command.format(
                    source=relative(run_source), filename=relative(run_source),
                    python=shlex.quote(sys.executable),
                    sourcedir=relative(source.parent), builddir=".", slug=shlex.quote(slug),
                    executable=shlex.quote("./" + os.path.relpath(executable, builddir)), output=relative(output_path),
                )
            except (KeyError, ValueError) as error:
                self.warn(f"invalid execution command for {source}: {error}")
                return None
            result = subprocess.run(
                ["sh", "-c", formatted], cwd=builddir, text=True, capture_output=True, timeout=self.settings.timeout,
            )
            if result.returncode:
                detail = result.stderr.strip() or result.stdout.strip() or f"exit status {result.returncode}"
                self.warn(f"execution failed for {source}: {detail}")
                return None
            if output_path.exists():
                output = output_path.read_text(encoding="utf-8")
            else:
                output = result.stdout
                output_path.write_text(output, encoding="utf-8")
            complete.touch()
            return output
        except (OSError, subprocess.TimeoutExpired) as error:
            self.warn(f"could not execute {source}: {error}")
            return None

    def finish(self) -> None:
        if not self.cleanup_safe:
            return
        try:
            if not self.cache.exists():
                return
            for path in self.cache.iterdir():
                if path.is_dir() and path not in self.active:
                    try:
                        shutil.rmtree(path)
                    except OSError as error:
                        self.warn(f"could not remove stale execution workspace {path}: {error}")
            existing = sorted(path.name for path in self.active if path.is_dir())
            manifest = self.cache / "manifest.json"
            if existing:
                value = {"page": self.page.as_posix(), "workspaces": existing}
                atomic_write(manifest, json.dumps(value, indent=2, sort_keys=True) + "\n")
            else:
                manifest.unlink(missing_ok=True)
                self._remove_empty_parents(self.cache, self.pages_root(self.settings))
        except OSError as error:
            self.warn(f"could not clean execution cache for {self.page}: {error}")

    @staticmethod
    def _remove_empty_parents(path: Path, stop: Path) -> None:
        while path != stop.parent:
            try:
                path.rmdir()
            except OSError:
                break
            path = path.parent


class ContentRenderer:
    def __init__(self, settings: Settings, liquid: Environment) -> None:
        self.settings = settings
        self.liquid = liquid

    def render(
        self, source: Path, body: str, context: dict[str, Any], *, cache_page: Path,
        parse_liquid: bool = True,
    ) -> Rendered:
        output_markdown = self.settings.markdown_mode
        self._validate_source_blocks(source, body)
        stash = Stash()
        features = Features()
        dependencies: set[Path] = {source}
        assets: dict[Path, Path] = {}
        warnings: list[str] = []
        executor = Executor(self.settings, cache_page, warnings.append)

        def malformed_src(match: re.Match[str]) -> str:
            line = body.count("\n", 0, match.start()) + 1
            message = f"error at {source}:{line}: malformed @src tag"
            warnings.append(message)
            executor.cleanup_safe = False
            return f'<p style="color:red;font-weight:bold;font-size:20px;">{html.escape(message)}</p>'

        body = MALFORMED_SRC.sub(malformed_src, body)

        def protect_raw(match: re.Match[str]) -> str:
            return stash.put(match.group(0), block=match.group(1).lower() == "pre")

        body = RAW_COMMENT.sub(lambda match: stash.put(match.group(0), block=True), body)
        body = RAW_HIGHLIGHT.sub(lambda match: stash.put(match.group(0), block=True), body)
        body = RAW_CODE.sub(protect_raw, body)

        def protect_fence(match: re.Match[str]) -> str:
            features.code = True
            if output_markdown:
                return stash.put(match.group(0), block=True)
            language = match.group(3).strip().split(maxsplit=1)[0] if match.group(3).strip() else "text"
            return stash.put(code_html(match.group(4), language), block=True)

        body = FENCE.sub(protect_fence, body)
        body = INLINE_CODE.sub(
            lambda match: stash.put(match.group(0) if output_markdown else f"<code>{html.escape(match.group(2).strip())}</code>", block=False),
            body,
        )

        def protect_highlight(match: re.Match[str]) -> str:
            features.code = True
            markup = match.group(0) if output_markdown else code_html(match.group(2), match.group(1))
            return stash.put(markup, block=True)

        body = HIGHLIGHT.sub(protect_highlight, body)

        def inline_block(match: re.Match[str]) -> str:
            language, flags = split_args(match.group(1))
            code = match.group(2)
            return self._source_box(source, code, language, flags, True, executor, stash, features)

        body = SRC_BLOCK.sub(inline_block, body)
        body = self._expand_directives(body, source, source, context, stash, features, dependencies, assets, warnings, executor, ())

        def obsidian_image(match: re.Match[str]) -> str:
            features.images = True
            name, attributes = self._image_parts(match.group(1))
            path = self._resolve_reference(name, source)
            href = Path(name)
            dependencies.add(path)
            assets[path] = href
            alt = attributes.get("alt") or Path(name).stem.replace("-", " ").replace("_", " ")
            classes = " ".join(filter(None, ("obsidian-image", self.settings.images.class_name, attributes.get("class"))))
            width = attributes.get("width") or self.settings.images.width
            if width and width.isdigit():
                width += "px"
            width_attr = f' style="width:{html.escape(width, quote=True)}"' if width else ""
            markup = f'<img class="{html.escape(classes, quote=True)}" src="{html.escape(href.as_posix(), quote=True)}" alt="{html.escape(alt, quote=True)}"{width_attr}>'
            return stash.put(markup, block=True)

        body = OBSIDIAN_IMAGE.sub(obsidian_image, body)
        if not output_markdown:
            body = self._protect_math(body, stash, features, warnings)

        if TOC.search(body):
            features.toc = True
            toc = self._toc(body, markdown=output_markdown)
            body = TOC.sub(stash.put(toc, block=True), body)

        if parse_liquid and not output_markdown:
            try:
                body = self.liquid.from_string(liquid_source(body)).render(**context)
            except LiquidError as error:
                warnings.append(f"template expression failed in {source}: {error}")
                features.warning = True
                body += f'\n<aside class="warning">Template cycle or error: {html.escape(str(error))}</aside>'

        if output_markdown:
            output = body
        else:
            renderer = HeadingRenderer(features)
            md = mistune.create_markdown(renderer=renderer, plugins=["strikethrough", "table", "task_lists", "url"])
            output = md(body)
        output = stash.restore(output)
        return Rendered(output, features, dependencies, assets, warnings, executor)

    def render_liquid(self, source: Path, body: str, context: dict[str, Any], *, parse_liquid: bool = True) -> Rendered:
        warnings: list[str] = []
        if parse_liquid:
            try:
                body = self.liquid.from_string(liquid_source(body)).render(**context)
            except LiquidError as error:
                warnings.append(f"template expression failed in {source}: {error}")
        return Rendered(body, Features(), {source}, warnings=warnings)

    def _resolve_reference(self, name: str, origin: Path) -> Path:
        path = normal_path(Path(name).expanduser())
        if path.is_absolute():
            return path
        local = normal_path(origin.parent / path)
        return local if local.exists() else normal_path(self.settings.project_root / path)

    @staticmethod
    def _image_parts(value: str) -> tuple[str, dict[str, str]]:
        parts = [part.strip() for part in value.split("|")]
        attributes: dict[str, str] = {}
        for part in parts[1:]:
            if "=" in part:
                key, item = part.split("=", 1)
                attributes[key.strip().lower()] = item.strip().strip("'\"")
            elif re.fullmatch(r"\d+(?:\.\d+)?(?:%|px|em|rem)?", part):
                attributes["width"] = part
            elif part:
                attributes.setdefault("alt", part)
        return parts[0], attributes

    @staticmethod
    def _validate_source_blocks(source: Path, body: str) -> None:
        begin = None
        for number, line in enumerate(body.splitlines(), 1):
            if SRC_BEGIN_LINE.match(line):
                if begin is not None:
                    raise ValueError(f"nested @src-begin in {source}:{number}")
                begin = number
            elif SRC_END_LINE.match(line):
                if begin is None:
                    raise ValueError(f"unexpected @src-end in {source}:{number}")
                begin = None
        if begin is not None:
            raise ValueError(f"missing @src-end for {source}:{begin}")

    def _expand_directives(
        self, body: str, origin: Path, page_source: Path, context: dict[str, Any], stash: Stash, features: Features,
        dependencies: set[Path], assets: dict[Path, Path], warnings: list[str], executor: Executor, stack: tuple[Path, ...],
    ) -> str:
        origin = normal_path(origin)

        def replace(match: re.Match[str]) -> str:
            kind, raw = match.group(1), match.group(2)
            name, flags = split_args(raw)
            path = self._resolve_reference(name, origin)
            dependencies.add(path)
            if path in stack or path == origin and kind == "include":
                chain = " -> ".join(str(item) for item in (*stack, path))
                warnings.append(f"include cycle: {chain}")
                features.warning = True
                return stash.put('<aside class="warning">Include cycle omitted.</aside>', block=True)
            try:
                value = path.read_text(encoding="utf-8")
            except OSError as error:
                warnings.append(f"could not read {path}: {error}")
                features.warning = True
                return stash.put(f'<aside class="warning">Could not read {html.escape(name)}.</aside>', block=True)
            if kind == "include":
                _, value = parse_frontmatter(value)
                self._validate_source_blocks(path, value)
                return self._expand_directives(
                    value, path, page_source, context, stash, features, dependencies, assets, warnings, executor, (*stack, origin),
                )
            language = path.suffix.lstrip(".") or "text"
            root = self.settings.input if self.settings.input.is_dir() else self.settings.project_root
            if self.settings.site_mode and path.is_relative_to(root):
                baseurl = str(context.get("site", {}).get("baseurl") or "").rstrip("/")
                href = baseurl + "/" + path.relative_to(root).as_posix()
            else:
                href = (Path(name) if origin == page_source else Path(os.path.relpath(path, page_source.parent))).as_posix()
            assets[path] = Path(href)
            return self._source_box(path, value, language, flags, False, executor, stash, features, name, href)

        previous = None
        while previous != body:
            previous = body
            body = DIRECTIVE.sub(replace, body)
        return body

    def _source_box(
        self, source: Path, code: str, language: str, flags: set[str], inline: bool,
        executor: Executor, stash: Stash, features: Features, label: str | None = None, href: str | None = None,
    ) -> str:
        features.code = True
        code_markup = code_html(code, language, source)
        collapsible = bool(flags & {"collapsed", "collapsible", "expanded"})
        label = html.escape(label or ("Source" if collapsible else f"{language} source"))
        if href:
            link = f'<a href="{html.escape(href, quote=True)}">{label}</a>'
        else:
            link = f"<span>{label}</span>" if collapsible else label
        if collapsible:
            open_attr = "" if "collapsed" in flags else " open"
            code_markup = (
                f'<details class="collapsible-code"{open_attr}>\n'
                f'<summary class="code-summary">{link} <span class="expand-hint">(click to expand)</span></summary>\n'
                f"{code_markup}</details>\n"
            )
        else:
            header = f'<div class="code-header">{link}</div>\n' if link else ""
            code_markup = header + code_markup
        should_run = self.settings.execute and "noexecute" not in flags
        output = executor.run(source, code, language, inline, enabled=should_run, use_cache="noexecute" not in flags)
        if output is None and "execute" in flags and not self.settings.execute:
            executor.warn(f"no cached output for {source}; rerun with --execute")
        if output is not None:
            code_markup += f'<div class="code-output">\n<span>Output:</span>\n<pre>{html.escape(output)}</pre>\n</div>\n'
        classes = "code-box inline-source" if inline else "code-box"
        return stash.put(f'<div class="{classes}">\n{code_markup}</div>\n', block=True)

    def _protect_math(self, body: str, stash: Stash, features: Features, warnings: list[str]) -> str:
        backend = self.settings.math.backend.lower()

        def mark_rendered(markup: str) -> str:
            def attributes(match: re.Match[str]) -> str:
                tag = match.group(0)
                if 'class="' in tag:
                    tag = tag.replace('class="', 'class="math-rendered ', 1)
                else:
                    tag = tag[:-1] + ' class="math-rendered">'
                return tag[:-1] + ' aria-hidden="true">'
            return re.sub(r"^<[^>]+>", attributes, markup, count=1)

        def emit(tex: str, display: bool) -> str:
            features.math = True
            try:
                if backend == "mathml":
                    markup = _mathml(tex, display)
                elif backend == "svg":
                    markup = _svg_math(tex, display)
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
            mode = "display" if display else "inline"
            class_name = f"math {mode}-math math-{backend}"
            tag = "div" if display else "span"
            if backend in {"mathml", "svg", "mathjax-chtml"} and not markup.startswith(("$", "\\")):
                features.math_copy = True
                delimiter = "$$" if display else "$"
                source = html.escape(delimiter + tex + delimiter)
                markup = f'<span class="math-copy-source">{source}</span>{mark_rendered(markup)}'
            return stash.put(f'<{tag} class="{class_name}">{markup}</{tag}>', block=display)

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
    def _toc(body: str, *, markdown: bool = False) -> str:
        headings: list[TocHeading] = []
        seen: dict[str, int] = {}
        for match in HEADING.finditer(body):
            level = len(match.group(1))
            label = html.unescape(re.sub(r"<[^>]+>|[*_`~]", "", match.group(2))).strip()
            label = re.sub(r"!?\[([^]]+)]\([^)]*\)", r"\1", label)
            if not label or label.lower() == "solution":
                continue
            base = slugify(label)
            count = seen.get(base, 0)
            seen[base] = count + 1
            identifier = base if count == 0 else f"{base}-{count + 1}"
            headings.append(TocHeading(level, label, identifier))
        exercises = [heading for heading in headings if EXERCISE.match(heading.label)]
        exercise_ids = {heading.identifier for heading in exercises}
        roots: list[TocNode] = []
        stack: list[tuple[int, list[TocNode]]] = [(0, roots)]
        for heading in (heading for heading in headings if heading.identifier not in exercise_ids):
            while heading.level <= stack[-1][0]:
                stack.pop()
            node = TocNode(heading)
            stack[-1][1].append(node)
            stack.append((heading.level, node.children))

        if markdown:
            lines = ["## Directory"]

            def render_markdown(nodes: list[TocNode], depth: int = 0) -> None:
                for node in nodes:
                    heading = node.heading
                    lines.append("  " * depth + f"- [{heading.label}](#{heading.identifier})")
                    if heading.label.lower() == "exercises" and exercises:
                        links = ", ".join(f"[{item.label}](#{item.identifier})" for item in exercises)
                        lines.append("  " * (depth + 1) + f"- *Exercises:* ({links})")
                    render_markdown(node.children, depth + 1)

            render_markdown(roots)
            return "\n".join(lines)

        def link(heading: TocHeading, class_name: str = "") -> str:
            attribute = f' class="{class_name}"' if class_name else ""
            return f'<a href="#{heading.identifier}"{attribute}>{html.escape(heading.label)}</a>'

        lines = ['<div class="table-of-contents">', "<h2>Directory</h2>"]

        def render(nodes: list[TocNode], root: bool = False) -> None:
            lines.append('<ul class="toc-list">' if root else "<ul>")
            for node in nodes:
                heading = node.heading
                lines.append(f'<li>{link(heading, "toc-exercises")}' if heading.label.lower() == "exercises" else f"<li>{link(heading)}")
                if heading.label.lower() == "exercises" and exercises:
                    items = "\n".join(f"<span>{link(item)}</span>" for item in exercises)
                    lines.append(f'<div class="exercise-container">(<span class="exercise-list">\n{items}\n</span>)\n</div>')
                if node.children:
                    render(node.children)
                lines.append("</li>")
            lines.append("</ul>")

        render(roots, True)
        lines.append("</div>")
        return "\n".join(lines)


def make_liquid(template_dirs: Iterable[Path], site: dict[str, Any]) -> Environment:
    directories = [path for path in template_dirs if path.is_dir()]
    environment = Environment(loader=TrackingLoader(directories), strict_filters=False, autoescape=False)

    def relative_url(value: Any) -> str:
        path = str(value or "")
        base = str(site.get("baseurl", "")).rstrip("/")
        return base + "/" + path.lstrip("/")

    def absolute_url(value: Any) -> str:
        return str(site.get("url", "")).rstrip("/") + relative_url(value)

    environment.add_filter("relative_url", relative_url)
    environment.add_filter("absolute_url", absolute_url)
    return environment
