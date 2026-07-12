"""Project discovery, site modeling, and output."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import base64
import html
from importlib.resources import files
import mimetypes
import os
from pathlib import Path
import re
import shutil
from typing import Any

from liquid.exceptions import LiquidError
import yaml

from .highlighting import syntax_css, validate_styles
from .render import FRONTMATTER, ContentRenderer, Features, Rendered, TrackingLoader, liquid_source, make_liquid, parse_frontmatter, slugify
from .settings import MARKDOWN_SUFFIXES, PAGE_SUFFIXES, Settings, atomic_write, normal_path, page_output


PROJECT_FILES = {"md2html.json"}
JEKYLL_EXCLUDES = {".bundle", ".git", ".jekyll-cache", ".jekyll-metadata", ".sass-cache", ".svn", "_site", "Gemfile", "Gemfile.lock", "node_modules"}
MARKDOWN_EXCLUDES = JEKYLL_EXCLUDES - {"Gemfile", "Gemfile.lock"} | {".md2html-cache", "__pycache__"}
CHTML_CDN = "https://cdn.jsdelivr.net/npm/@mathjax/mathjax-tex-font@4.1.3/chtml/woff2"
MATHJAX_CDN = "https://cdn.jsdelivr.net/npm/mathjax@4.1.3/tex-mml-chtml.js"
FONT_FACE = re.compile(r"@font-face\s*/\*\s*(MJX(?:-TEX)?-[A-Z0-9]+)\s*\*/\s*\{.*?\}\s*", re.DOTALL)
CSS_IMPORT = re.compile(r"@import\s+(?:url\()?['\"]?([^'\")\s;]+)", re.IGNORECASE)
CSS_IMPORT_RULE = re.compile(r"@import\s+(?:url\()?['\"]?([^'\")\s;]+)['\"]?\)?\s*;", re.IGNORECASE)
CSS_URL = re.compile(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)", re.IGNORECASE)
STYLESHEET = re.compile(r"<link\b(?=[^>]*\brel=(?:['\"][^'\"]*stylesheet[^'\"]*['\"]|stylesheet\b))(?=[^>]*\bhref=['\"]([^'\"]+))[^>]*>", re.IGNORECASE)
MEDIA_ASSET = re.compile(r"<(?:img|source|video|audio|track|embed|object)\b[^>]*\b(?:src|poster|data)=['\"]([^'\"]+)['\"]", re.IGNORECASE)
LINK_ASSET = re.compile(r"<link\b(?=[^>]*\bhref=['\"]([^'\"]+)['\"])[^>]*>", re.IGNORECASE)
SCRIPT_ASSET = re.compile(r"<script\b(?=[^>]*\bsrc=['\"]([^'\"]+)['\"])[^>]*>\s*</script>", re.IGNORECASE)


def minify_css(value: str) -> str:
    output: list[str] = []
    quote: str | None = None
    escaped = pending_space = False
    index = 0
    while index < len(value):
        char = value[index]
        if quote:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if value.startswith("/*", index):
            end = value.find("*/", index + 2)
            index = len(value) if end < 0 else end + 2
            pending_space = True
            continue
        if char in "'\"":
            if pending_space and output and output[-1] not in "{}:;,> ":
                output.append(" ")
            pending_space = False
            quote = char
            output.append(char)
        elif char.isspace():
            pending_space = True
        else:
            if char in "{}:;,>":
                while output and output[-1] == " ":
                    output.pop()
                if char == "}" and output and output[-1] == ";":
                    output.pop()
            elif pending_space and output and output[-1] not in "{}:;,> ":
                output.append(" ")
            pending_space = False
            output.append(char)
        index += 1
    return "".join(output).strip()


@dataclass
class Page:
    source: Path
    relative: Path
    metadata: dict[str, Any]
    body: str
    url: str
    output_relative: Path

    def data(self) -> dict[str, Any]:
        self.metadata.setdefault("title", self.source.name)
        data = dict(self.metadata)
        data["name"] = self.source.name
        data["url"] = self.url
        data.setdefault("path", self.relative.as_posix())
        data["tags"] = names(data.get("tags") or data.get("tag"))
        data["categories"] = names(data.get("categories") or data.get("category"))
        data.setdefault("excerpt", self._excerpt())
        return data

    def _excerpt(self) -> str:
        for paragraph in re.split(r"\n\s*\n", self.body):
            value = re.sub(r"<[^>]+>|^[#>*-]+\s*", "", paragraph.strip())
            if value and not value.startswith(("@", "{%")):
                return value
        return ""


def names(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part for part in re.split(r"\s*,\s*|\s+", value) if part]
    return [str(item) for item in value]


@dataclass
class BuildResult:
    written: list[Path] = field(default_factory=list)
    copied: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    page_dependencies: dict[Path, set[Path]] = field(default_factory=dict)
    asset_dependencies: dict[Path, Path] = field(default_factory=dict)
    skipped: list[Path] = field(default_factory=list)

    @property
    def output_count(self) -> int:
        return len(self.written) + len(self.copied)


class Project:
    """A complete build, whether it contains one page or a native site."""

    def __init__(self, settings: Settings) -> None:
        validate_styles(settings.highlighter, settings.highlighter_style, settings.highlighter_dark_style)
        self.settings = settings
        self.source_root = settings.input if settings.input.is_dir() else settings.input.parent
        self.site_config = self.source_root / "_config.yml"
        self.bundled_templates = Path(str(files("md2html2").joinpath("default_templates")))
        self.bundled_assets = Path(str(files("md2html2").joinpath("assets")))
        self.site = self._site_data()
        template_dirs = [
            *settings.templates,
            settings.project_root / "_templates",
            self.source_root / "_includes",
            self.source_root / "_layouts",
            self.bundled_templates,
        ]
        self.liquid = make_liquid((path for path in template_dirs if path is not None), self.site)
        self.loader = self.liquid.loader
        assert isinstance(self.loader, TrackingLoader)
        self.renderer = ContentRenderer(settings, self.liquid)
        self.math_fonts: set[str] = set()
        self.browser_mathjax = False
        self.shared_dependencies: set[Path] = set()
        self.post_sources: set[Path] = set()
        self.ignored_sources: set[Path] = set()

    def build(self, only: set[Path] | None = None, *, skip_unchanged: bool = False) -> BuildResult:
        self._validate_paths()
        result = BuildResult()
        pages = self._discover_pages()
        self._populate_site(pages)
        wanted = None if only is None else {path.absolute() for path in only}
        selected = pages if wanted is None else [page for page in pages if page.source.absolute() in wanted]
        if skip_unchanged and self.settings.shared_math_assets and any(
            self.settings.force or not self._current(self._target(page, output), page, paginator)
            for page in selected for output, _, paginator in self._page_outputs(page)
        ):
            skip_unchanged = False
        if only is None and self.settings.clean and self.settings.input.is_dir() and self.settings.output.exists():
            shutil.rmtree(self.settings.output)
        if self.settings.asset_mode == "shared" and self.settings.output_mode == "pages":
            self._write_shared_css(result)
        for page in selected:
            for output_relative, url, paginator in self._page_outputs(page):
                target = self._target(page, output_relative)
                if page.source.absolute() == target.absolute():
                    result.warnings.append(f"skipping {page.source}: source and output are the same file")
                    continue
                if skip_unchanged and not self.settings.force and self._current(target, page, paginator):
                    result.skipped.append(target)
                    result.page_dependencies.setdefault(page.source, set()).update(self._content_sources(page, paginator) | self.shared_dependencies)
                    continue
                rendered = self._render_page(page, output_relative, url, paginator, target, result)
                target.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(target, rendered.content)
                if self.settings.input.is_file():
                    self._copy_page_assets(target, rendered, result)
                if rendered.executor:
                    rendered.executor.finish()
                result.written.append(target)
                result.warnings.extend(rendered.warnings)
                result.page_dependencies.setdefault(page.source, set()).update(rendered.dependencies)
        if only is None and not result.skipped and not (self.settings.jekyll_mode or self.settings.markdown_mode):
            self._prune_math_assets()
            self._prune_browser_mathjax()
            if self.settings.asset_mode != "shared":
                (self._output_root() / "assets/md2html/page.css").unlink(missing_ok=True)
        if only is None and self.settings.input.is_dir():
            self._copy_static(pages, result)
        if self.settings.site_mode and (only is None or any(page.relative.parts[:1] == ("_posts",) for page in selected)):
            self._write_feed(pages, result)
        return result

    def _validate_paths(self) -> None:
        if not self.settings.input.exists():
            raise ValueError(f"input does not exist: {self.settings.input}")
        if self.settings.input.is_dir():
            source = self.settings.input.absolute()
            output = self.settings.output.absolute()
            if source == output:
                raise ValueError("site output cannot be the input directory")
            if self.settings.clean and source.is_relative_to(output):
                raise ValueError("clean site output cannot contain the input directory")

    def _site_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.settings.jekyll_mode and self.site_config.is_file():
            try:
                loaded = yaml.safe_load(self.site_config.read_text(encoding="utf-8")) or {}
            except (OSError, yaml.YAMLError) as error:
                raise ValueError(f"could not read Jekyll configuration {self.site_config}: {error}") from error
            if not isinstance(loaded, dict):
                raise ValueError(f"Jekyll configuration must contain a mapping: {self.site_config}")
            data.update(loaded)
        data.update(self.settings.site_data)
        data.setdefault("title", self.source_root.name)
        data.setdefault("description", "")
        data.setdefault("url", "")
        data.setdefault("baseurl", "")
        data["time"] = datetime.now(timezone.utc)
        return data

    def _discover_pages(self) -> list[Page]:
        source = self.settings.input
        if source.is_file():
            if source.suffix.lower() not in PAGE_SUFFIXES:
                raise ValueError(f"unsupported page type: {source}")
            text = source.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(text)
            relative = Path(source.name)
            output_relative = Path(self.settings.output.name)
            return [Page(source, relative, metadata, body, "/" + output_relative.name, output_relative)]

        pattern = "**/*" if self.settings.recursive or self.settings.site_mode or self.settings.markdown_mode else "*"
        pages: list[Page] = []
        for path in sorted(source.glob(pattern)):
            if not path.is_file() or self._excluded(path):
                continue
            relative = path.relative_to(source)
            suffixes = MARKDOWN_SUFFIXES if self.settings.markdown_mode else PAGE_SUFFIXES
            if path.suffix.lower() in suffixes:
                text = path.read_text(encoding="utf-8")
                metadata, body = parse_frontmatter(text)
                post = relative.parts[:1] == ("_posts",)
                if self.settings.jekyll_mode and not post and not FRONTMATTER.match(text):
                    continue
                if self.settings.jekyll_mode and metadata.get("published", True) is False:
                    self.ignored_sources.add(path)
                    continue
                url, output = ("/" + relative.as_posix(), relative) if self.settings.markdown_mode else self._output_policy(relative, metadata)
                pages.append(Page(path, relative, metadata, body, url, output))
        return pages

    def _excluded(self, path: Path) -> bool:
        relative = path.relative_to(self.source_root)
        parts = relative.parts
        if self.settings.output.is_relative_to(self.source_root) and path.is_relative_to(self.settings.output):
            return True
        if self.settings.markdown_mode and (any(part in MARKDOWN_EXCLUDES for part in parts) or parts[:2] == ("vendor", "bundle")):
            return True
        include_value = self.site.get("include") or ()
        includes = [str(include_value)] if isinstance(include_value, str) else [str(value) for value in include_value]
        if any(relative.match(pattern.strip("/")) for pattern in includes):
            return False
        if relative.name.startswith("_"):
            return True
        if any(part.startswith(".") for part in parts):
            return True
        if any(part.startswith("_") and part not in {"_posts"} for part in parts[:-1]):
            return True
        exclude_value = self.site.get("exclude") or ()
        excludes = [*self.settings.exclude, *([exclude_value] if isinstance(exclude_value, str) else exclude_value)]
        if self.settings.jekyll_mode:
            vendor = len(parts) > 1 and parts[0] == "vendor" and parts[1] in {"bundle", "cache", "gems", "ruby"}
            if any(part in JEKYLL_EXCLUDES for part in parts) or vendor:
                return True
        for pattern in excludes:
            normalized = str(pattern).strip("/")
            if relative.as_posix() == normalized or relative.as_posix().startswith(normalized + "/") or relative.match(normalized):
                return True
        return False

    def _output_policy(self, relative: Path, metadata: dict[str, Any]) -> tuple[str, Path]:
        permalink = metadata.get("permalink")
        post = relative.parts and relative.parts[0] == "_posts" and relative.suffix.lower() != ".xml"
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})-(.+)", relative.stem) if post else None
        if permalink:
            url = str(permalink)
        elif match:
            year, month, day, slug = match.groups()
            default = "/:categories/:year/:month/:day/:title.html" if self.settings.jekyll_mode else "/:year/:month/:day/:title.html"
            pattern = str(self.site.get("permalink", default))
            categories = "/".join(names(metadata.get("categories") or metadata.get("category")))
            url = pattern.replace(":year", year).replace(":month", month).replace(":day", day)
            url = url.replace(":title", slugify(slug)).replace(":slug", slugify(slug)).replace(":categories", categories)
            url = re.sub(r"/{2,}", "/", url)
        else:
            normal = page_output(relative)
            if normal.name == "index.html":
                url = "/" if normal.parent == Path(".") else f"/{normal.parent.as_posix()}/"
            else:
                url = "/" + normal.as_posix()
        if not url.startswith("/"):
            url = "/" + url
        return url, self._url_output(url)

    @staticmethod
    def _url_output(url: str) -> Path:
        return Path(url.lstrip("/")) / "index.html" if url.endswith("/") else Path(url.lstrip("/"))

    def _populate_site(self, pages: list[Page]) -> None:
        post_pages = [page for page in pages if page.relative.parts and page.relative.parts[0] == "_posts"]
        self.post_sources = {page.source for page in post_pages}
        post_pages.sort(key=lambda page: self._date(page), reverse=True)
        post_data = [page.data() for page in post_pages]
        self.site["posts"] = post_data
        self.site["pages"] = [page.data() for page in pages if not self.settings.jekyll_mode or page not in post_pages]
        tags: dict[str, list[dict[str, Any]]] = {}
        categories: dict[str, list[dict[str, Any]]] = {}
        for post, data in zip(post_pages, post_data):
            post.metadata["date"] = data["date"] = self._date(post)
            data["slug"] = post.relative.stem[11:] if re.match(r"\d{4}-\d{2}-\d{2}-", post.relative.stem) else post.relative.stem
            data["id"] = post.url.rstrip("/") or "/"
            for name in data["tags"]:
                tags.setdefault(name, []).append(data)
            for name in data["categories"]:
                categories.setdefault(name, []).append(data)
        self.site["tags"] = tags
        self.site["categories"] = categories
        self.site["tag_list"] = [
            {"name": name, "slug": slugify(name), "posts": values, "size": len(values)}
            for name, values in sorted(tags.items(), key=lambda item: item[0].lower())
        ]
        self.site["category_list"] = [
            {"name": name, "slug": slugify(name), "posts": values, "size": len(values)}
            for name, values in sorted(categories.items(), key=lambda item: item[0].lower())
        ]

    @staticmethod
    def _date(page: Page) -> datetime:
        value = page.metadata.get("date")
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
        if value:
            try:
                parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})-", page.source.name)
        return datetime(*map(int, match.groups()), tzinfo=timezone.utc) if match else datetime.fromtimestamp(page.source.stat().st_mtime, timezone.utc)

    def _page_outputs(self, page: Page) -> list[tuple[Path, str, dict[str, Any] | None]]:
        if not self.settings.site_mode or page.relative.name != "index.html":
            return [(page.output_relative, page.url, None)]
        per_page = int(self.site.get("paginate") or 0)
        if per_page <= 0:
            return [(page.output_relative, page.url, None)]
        path = str(self.site.get("paginate_path") or "/page:num/")
        if ":num" not in path:
            raise ValueError("paginate_path must contain :num")
        posts = [post for post in self.site["posts"] if not post.get("hidden")]
        total_pages = max(1, (len(posts) + per_page - 1) // per_page)

        def page_path(number: int) -> str:
            value = page.url if number == 1 else path.replace(":num", str(number))
            return value if value.startswith("/") else "/" + value

        outputs = []
        for number in range(1, total_pages + 1):
            url = page_path(number)
            paginator = {
                "page": number, "per_page": per_page,
                "posts": posts[(number - 1) * per_page:number * per_page],
                "total_posts": len(posts), "total_pages": total_pages,
                "previous_page": number - 1 or None,
                "previous_page_path": page_path(number - 1) if number > 1 else None,
                "next_page": number + 1 if number < total_pages else None,
                "next_page_path": page_path(number + 1) if number < total_pages else None,
            }
            outputs.append((page.output_relative if number == 1 else self._url_output(url), url, paginator))
        return outputs

    def _content_sources(self, page: Page, paginator: dict[str, Any] | None) -> set[Path]:
        sources = {page.source}
        if self.settings.jekyll_mode and self.site_config.is_file():
            sources.add(self.site_config)
        if paginator is not None:
            sources.update(self.post_sources)
        return sources

    def _current(self, target: Path, page: Page, paginator: dict[str, Any] | None) -> bool:
        if not target.is_file():
            return False
        modified = target.stat().st_mtime_ns
        return all(modified >= source.stat().st_mtime_ns for source in self._content_sources(page, paginator))

    def _render_page(
        self, page: Page, output_relative: Path, url: str, paginator: dict[str, Any] | None,
        target: Path, result: BuildResult,
    ) -> Rendered:
        self.loader.dependencies.clear()
        page_data = page.data()
        page_data["url"] = url
        context = {"site": self.site, "page": page_data}
        if paginator is not None:
            context["paginator"] = paginator
        parse_liquid = self.settings.parse_liquid and page.metadata.get("render_with_liquid", True) is not False
        markdown = page.source.suffix.lower() in MARKDOWN_SUFFIXES
        rendered = (
            self.renderer.render(page.source, page.body, context, parse_liquid=parse_liquid)
            if markdown else self.renderer.render_liquid(page.source, page.body, context, parse_liquid=parse_liquid)
        )
        context["content"] = rendered.content
        context["md2html"] = self._renderer_context(rendered, target, result)
        if not (self.settings.jekyll_mode or self.settings.markdown_mode):
            context["md2html"]["stylesheets"] = [*self.settings.stylesheets, *self._values(page_data.get("stylesheets"))]
        content = rendered.content
        if self.settings.markdown_mode:
            metadata = {**self.settings.frontmatter, **page.metadata}
            content = "---\n" + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True) + "---\n\n" + rendered.content
        elif self.settings.site_mode:
            content = self._apply_layouts(page.source, rendered, context)
        elif markdown:
            content = self._page_template(rendered, target, context)
        rendered.content = content.rstrip() + "\n"
        rendered.dependencies.update(self.loader.dependencies)
        rendered.dependencies.update(self.shared_dependencies)
        rendered.dependencies.update(self._content_sources(page, paginator))
        if self.settings.asset_mode == "standalone" and not self.settings.jekyll_mode:
            rendered.content = self._embed_local_assets(rendered.content, page.source, rendered)
        for pattern in (STYLESHEET, MEDIA_ASSET):
            for href in pattern.findall(rendered.content):
                name = href.split("?", 1)[0].split("#", 1)[0]
                if name and "://" not in name and not name.startswith(("//", "data:", "mailto:")):
                    path = (self.source_root if name.startswith("/") else page.source.parent) / name.lstrip("/")
                    if not path.exists():
                        path = self.settings.project_root / name.lstrip("/")
                    if pattern is STYLESHEET:
                        self._track_css(path, rendered.dependencies)
                    rendered.assets[normal_path(path)] = Path(name.lstrip("/"))
        return rendered

    def _local_asset(self, name: str, source: Path) -> Path | None:
        clean = name.split("?", 1)[0].split("#", 1)[0]
        if not clean or "://" in clean or clean.startswith(("//", "data:", "mailto:", "#")):
            return None
        relative = Path(clean.lstrip("/"))
        roots = (
            (self.settings.project_root, self.source_root, source.parent, *source.parent.parents)
            if clean.startswith("/") else (source.parent, self.settings.project_root)
        )
        return next((normal_path(root / relative) for root in roots if (root / relative).is_file()), None)

    @staticmethod
    def _data_url(path: Path) -> str:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")

    def _embedded_css(self, path: Path, rendered: Rendered, seen: set[Path] | None = None) -> str:
        seen = set() if seen is None else seen
        path = normal_path(path)
        if path in seen:
            return ""
        seen.add(path)
        rendered.dependencies.add(path)
        value = path.read_text(encoding="utf-8")

        def include(match: re.Match[str]) -> str:
            source = self._local_asset(match.group(1), path)
            return self._embedded_css(source, rendered, seen) if source else match.group(0)

        def resource(match: re.Match[str]) -> str:
            source = self._local_asset(match.group(2), path)
            if source:
                rendered.dependencies.add(source)
                return f'url("{self._data_url(source)}")'
            return match.group(0)

        return CSS_URL.sub(resource, CSS_IMPORT_RULE.sub(include, value))

    def _embed_local_assets(self, content: str, source: Path, rendered: Rendered) -> str:
        def stylesheet(match: re.Match[str]) -> str:
            path = self._local_asset(match.group(1), source)
            return f"<style>{self._embedded_css(path, rendered)}</style>" if path else match.group(0)

        def script(match: re.Match[str]) -> str:
            path = self._local_asset(match.group(1), source)
            if not path:
                return match.group(0)
            rendered.dependencies.add(path)
            value = path.read_text(encoding="utf-8").replace("</script", "<\\/script")
            return f"<script>{value}</script>"

        def media(match: re.Match[str]) -> str:
            path = self._local_asset(match.group(1), source)
            if not path:
                return match.group(0)
            rendered.dependencies.add(path)
            return match.group(0).replace(match.group(1), self._data_url(path), 1)

        value = STYLESHEET.sub(stylesheet, content)
        value = LINK_ASSET.sub(media, value)
        return MEDIA_ASSET.sub(media, SCRIPT_ASSET.sub(script, value))

    def _apply_layouts(self, source: Path, rendered: Rendered, context: dict[str, Any]) -> str:
        page = context["page"]
        content = context["content"]
        layout_name = page.get("layout")
        seen: set[str] = set()
        while layout_name:
            name = str(layout_name)
            if name in seen:
                rendered.warnings.append(f"layout cycle while rendering {source}: {name}")
                content += f'<aside class="warning">Layout cycle omitted: {html.escape(name)}</aside>'
                break
            seen.add(name)
            path = self._find_template(name, site_layout=True)
            if not path:
                rendered.warnings.append(f"layout not found for {source}: {name}")
                break
            rendered.dependencies.add(path)
            metadata, template = parse_frontmatter(path.read_text(encoding="utf-8"))
            try:
                context["content"] = content
                content = self.liquid.from_string(liquid_source(template)).render(**context, layout=metadata)
            except LiquidError as error:
                rendered.warnings.append(f"layout failed for {source}: {error}")
                content += f'<aside class="warning">Layout cycle or error: {html.escape(str(error))}</aside>'
                break
            layout_name = metadata.get("layout")
        return content

    def _find_template(self, name: str, *, site_layout: bool = False) -> Path | None:
        filename = name if Path(name).suffix else name + ".html"
        candidates = [
            *(directory / filename for directory in self.settings.templates),
            self.settings.project_root / "_templates" / filename,
            self.source_root / "_layouts" / filename if site_layout else None,
            self.bundled_templates / filename,
        ]
        return next((path for path in candidates if path and path.is_file()), None)

    def _page_template(self, rendered: Rendered, target: Path, context: dict[str, Any]) -> str:
        page = context["page"]
        name = str(page.get("template") or self.settings.template)
        path = self._find_template(name)
        if path is None:
            raise ValueError(f"template not found: {name}")
        rendered.dependencies.add(path)
        css = self._css(rendered, path, page)
        page_stylesheets = []
        if self.settings.asset_mode == "shared" and "css" not in page and "template" not in page:
            stylesheet = self._output_root() / "assets/md2html/page.css"
            page_stylesheets.append(Path(os.path.relpath(stylesheet, target.parent)).as_posix())
        context["md2html"].update(css=css, page_stylesheets=page_stylesheets)
        try:
            return self.liquid.from_string(liquid_source(path.read_text(encoding="utf-8"))).render(**context)
        except LiquidError as error:
            rendered.warnings.append(f"template failed: {error}")
            return rendered.content + f'<aside class="warning">Template cycle or error: {html.escape(str(error))}</aside>'

    def _feature_context(self, features: Features) -> dict[str, bool]:
        backend = self.settings.math.backend.lower()
        return {
            "jekyll_compatibility": self.settings.jekyll_mode,
            "uses_mathjax": features.math and backend == "mathjax",
            "uses_mathjax_chtml": features.math and backend == "mathjax-chtml",
            "uses_svg_math": features.math and backend == "svg",
            "uses_mathml": features.math and backend == "mathml",
            "has_code": features.code,
            "has_toc": features.toc,
            "has_images": features.images,
            "has_warnings": features.warning,
            "has_math_copy": features.math_copy,
        }

    @staticmethod
    def _values(value: Any) -> list[str]:
        if value is None:
            return []
        return [value] if isinstance(value, str) else [str(item) for item in value]

    def _css(self, rendered: Rendered, template: Path, page: dict[str, Any], *, shared: bool | None = None) -> str:
        features = rendered.features
        paths: list[Path] = []
        shared = self.settings.asset_mode == "shared" if shared is None else shared
        shared = shared and "css" not in page and "template" not in page
        configured = page.get("css") if "css" in page else self.settings.css
        companion_css = False
        if shared:
            configured = ()
        if configured is None:
            companion = template.with_suffix(".css")
            if companion.is_file():
                paths.append(companion)
                companion_css = True
            elif template.name == "page.html":
                paths.append(self.bundled_assets / "page-base.css")
            elif template.name == "barebones.html":
                paths.append(self.bundled_assets / "barebones.css")
        else:
            for name in self._values(configured):
                path = Path(name).expanduser()
                paths.append(path if path.is_absolute() else self.settings.project_root / path)
        feature_css = bool(page.get("feature_css", self.settings.feature_css)) and not shared and not companion_css
        if feature_css:
            for used, name in (
                (features.code, "code"), (features.math, "math"),
                (features.toc, "toc"), (features.images, "image"), (features.warning, "warning"),
            ):
                if used:
                    paths.append(self.bundled_assets / f"feature-{name}.css")
        values = []
        for path in paths:
            try:
                value = path.read_text(encoding="utf-8")
                values.append(value)
                self._track_css(path, rendered.dependencies, value)
            except OSError as error:
                raise ValueError(f"could not read CSS {path}: {error}") from error
        if feature_css and features.code:
            values.insert(1 if values else 0, syntax_css(
                self.settings.highlighter, self.settings.highlighter_style, self.settings.highlighter_dark_style,
            ))
        css = "\n".join(values)
        return minify_css(css) if self.settings.minify_css else css

    def _write_shared_css(self, result: BuildResult) -> None:
        template = self._find_template(self.settings.template)
        if template is None:
            raise ValueError(f"template not found: {self.settings.template}")
        features = Features(code=True, math=True, toc=True, images=True, warning=True)
        rendered = Rendered("", features)
        css = self._css(rendered, template, {}, shared=False).rstrip() + "\n"
        relative = Path("assets/md2html/page.css")
        root = self.settings.output if self.settings.input.is_dir() else self.settings.output.parent
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or target.read_text(encoding="utf-8") != css:
            atomic_write(target, css)
            result.written.append(target)
        self.shared_dependencies = rendered.dependencies

    def _track_css(self, path: Path, dependencies: set[Path], value: str | None = None) -> None:
        path = normal_path(path)
        if path in dependencies:
            return
        dependencies.add(path)
        try:
            value = value if value is not None else path.read_text(encoding="utf-8")
        except OSError:
            return
        for name in CSS_IMPORT.findall(value):
            if "://" not in name and not name.startswith("//"):
                self._track_css((self.source_root if name.startswith("/") else path.parent) / name.lstrip("/"), dependencies)

    def _math_css(self, features: Features, fonts: set[str], delivery: str) -> str:
        families = {"MJX-BRK" if name == "brk" else "MJX-TEX-" + name.upper() for name in fonts}
        css = FONT_FACE.sub(lambda match: match.group(0) if match.group(1) in families else "", features.math_css)
        if self.settings.math.chtml_fonts == "none":
            return FONT_FACE.sub("", css)
        if delivery == "remote":
            return css.replace("mathjax/woff2", CHTML_CDN)
        if delivery == "inline" and features.math_font_dir:
            for name in fonts:
                filename = f"mjx-tex-{name}.woff2"
                encoded = base64.b64encode((features.math_font_dir / filename).read_bytes()).decode("ascii")
                css = css.replace(f'url("mathjax/woff2/{filename}")', f'url("data:font/woff2;base64,{encoded}")')
        return css

    def _renderer_context(self, rendered: Rendered, target: Path, result: BuildResult) -> dict[str, Any]:
        context: dict[str, Any] = {
            **self._feature_context(rendered.features),
            "css": None,
            "page_stylesheets": [],
            "stylesheets": [],
            "math_css": None,
            "math_stylesheets": [],
            "font_preloads": [],
            "mathjax_config": None,
            "mathjax_src": None,
        }
        if self.settings.jekyll_mode or self.settings.markdown_mode:
            return context
        if self.settings.site_mode and self.settings.feature_css and rendered.features.code:
            css = syntax_css(self.settings.highlighter, self.settings.highlighter_style, self.settings.highlighter_dark_style)
            context["css"] = minify_css(css) if self.settings.minify_css else css
        if rendered.features.math_css:
            if self.settings.asset_mode == "shared":
                stylesheet, fonts = self._write_math_assets(rendered.features, result, target)
                context["math_stylesheets"].append(stylesheet)
                context["font_preloads"] = fonts
            else:
                css = self._standalone_math_css(rendered.features)
                if self.settings.site_mode:
                    css = (self.bundled_assets / "feature-math.css").read_text(encoding="utf-8") + "\n" + css
                context["math_css"] = minify_css(css) if self.settings.minify_css else css
        if rendered.features.math and self.settings.math.backend == "mathjax":
            context.update(self._browser_mathjax_context(rendered, target, result))
        return context

    def _npm_asset(self, name: str) -> Path:
        package_root = Path(str(files("md2html2"))).parent
        path = next((root / name for root in (package_root / "node_modules", Path.cwd() / "node_modules") if (root / name).exists()), None)
        if path is None:
            raise ValueError("browser MathJax assets are unavailable; run npm install in the md2html2 package")
        return path

    def _browser_mathjax_bundle(self) -> Path:
        return self._npm_asset("mathjax/tex-mml-chtml.js")

    def _browser_mathjax_fonts(self) -> Path:
        return self._npm_asset("@mathjax/mathjax-newcm-font/chtml")

    def _copy_tree(self, source: Path, target: Path, result: BuildResult) -> None:
        for path in source.rglob("*"):
            if path.is_file():
                self._copy_asset(path, target / path.relative_to(source), result)

    def _asset_url(self, target: Path, page_target: Path) -> str:
        if self.settings.site_mode:
            base = str(self.site.get("baseurl", "")).rstrip("/")
            return base + "/" + target.relative_to(self._output_root()).as_posix()
        return Path(os.path.relpath(target, page_target.parent)).as_posix()

    def _browser_mathjax_context(
        self, rendered: Rendered, page_target: Path, result: BuildResult,
    ) -> dict[str, str]:
        first = not self.browser_mathjax
        self.browser_mathjax = True
        mode = self.settings.asset_mode
        config = "window.MathJax={tex:{inlineMath:[['$','$']],displayMath:[['$$','$$']],processEscapes:true}"
        if mode == "shared":
            bundle = self._browser_mathjax_bundle()
            target = self._output_root() / "assets/md2html/mathjax.js"
            self._copy_asset(bundle, target, result)
            font_target = self._output_root() / "assets/md2html/mathjax-newcm-font/chtml"
            if first:
                for old in (font_target.parent, self._output_root() / "assets/md2html/sre"):
                    if old.exists():
                        shutil.rmtree(old)
            self._copy_tree(self._browser_mathjax_fonts(), font_target, result)
            self._copy_tree(self._npm_asset("mathjax/sre"), self._output_root() / "assets/md2html/sre", result)
            font_root = self._asset_url(font_target.parent.parent, page_target)
            config += f',loader:{{paths:{{fonts:"{font_root}"}}}},output:{{fontPath:"[fonts]/%%FONT%%-font"}}'
            source = self._asset_url(target, page_target)
        else:
            source = MATHJAX_CDN
            if mode == "standalone":
                rendered.warnings.append("standalone browser MathJax assets are not implemented; using the CDN")
        return {"mathjax_config": config + "};", "mathjax_src": source}

    def _prune_browser_mathjax(self) -> None:
        if not self.browser_mathjax or self.settings.asset_mode != "shared":
            asset_root = self._output_root() / "assets/md2html"
            (asset_root / "mathjax.js").unlink(missing_ok=True)
            for path in (asset_root / "mathjax-newcm-font", asset_root / "sre"):
                if path.exists():
                    shutil.rmtree(path)

    def _standalone_math_css(self, features: Features) -> str:
        mode = self.settings.math.chtml_fonts
        fonts = set(features.math_fonts)
        if mode == "all" and features.math_font_dir:
            fonts = {path.stem.removeprefix("mjx-tex-") for path in features.math_font_dir.glob("mjx-tex-*.woff2")}
        local = mode in {"all", "inline", "local"} or mode == "auto" and self.settings.asset_mode == "standalone"
        return self._math_css(features, fonts, "inline" if local else "remote")

    def _write_math_assets(self, features: Features, result: BuildResult, page_target: Path) -> tuple[str, list[str]]:
        mode = self.settings.math.chtml_fonts
        root = self._output_root()

        first = not self.math_fonts
        self.math_fonts.update(features.math_fonts)
        fonts = set(self.math_fonts)
        if mode in {"auto", "all", "local"} and features.math_font_dir:
            fonts = {path.stem.removeprefix("mjx-tex-") for path in features.math_font_dir.glob("mjx-tex-*.woff2")}
        delivery = mode if mode in {"inline", "remote"} else "local"
        css = self._math_css(features, fonts, delivery)
        if self.settings.site_mode:
            css = (self.bundled_assets / "feature-math.css").read_text(encoding="utf-8") + "\n" + css
        if delivery == "local" and mode != "none" and features.math_font_dir:
            if first:
                old = root / "assets/md2html/mathjax"
                if old.exists():
                    shutil.rmtree(old)
            for name in fonts:
                source = features.math_font_dir / f"mjx-tex-{name}.woff2"
                target = root / "assets/md2html/mathjax/woff2" / source.name
                self._copy_asset(source, target, result)

        relative = Path("assets/md2html/mathjax-chtml.css")
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        css = minify_css(css) if self.settings.minify_css else css.rstrip()
        atomic_write(target, css + "\n")
        if target not in result.written:
            result.written.append(target)
        stylesheet = self._asset_url(target, page_target)
        preload_names = features.math_fonts if mode in {"auto", "all", "local"} else set()
        preload = [self._asset_url(root / f"assets/md2html/mathjax/woff2/mjx-tex-{name}.woff2", page_target) for name in sorted(preload_names)]
        return stylesheet, preload

    def _prune_math_assets(self) -> None:
        stylesheet = self._output_root() / "assets/md2html/mathjax-chtml.css"
        font_root = self._output_root() / "assets/md2html/mathjax/woff2"
        mode = self.settings.math.chtml_fonts
        if not self.math_fonts:
            stylesheet.unlink(missing_ok=True)
        if not self.math_fonts or mode in {"remote", "inline", "none"}:
            if font_root.parent.exists():
                shutil.rmtree(font_root.parent)

    def _target(self, page: Page, output_relative: Path | None = None) -> Path:
        if self.settings.input.is_file():
            return self.settings.output
        return self.settings.output / (output_relative or page.output_relative)

    def _output_root(self) -> Path:
        return self.settings.output if self.settings.input.is_dir() else self.settings.output.parent

    @staticmethod
    def _copy_asset(source: Path, target: Path, result: BuildResult) -> None:
        result.asset_dependencies[source] = target
        if not source.is_file() or source.absolute() == target.absolute():
            return
        if target.is_file() and target.stat().st_mtime_ns >= source.stat().st_mtime_ns:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        result.copied.append(target)

    def _copy_page_assets(self, page_target: Path, rendered: Rendered, result: BuildResult) -> None:
        for source, relative in rendered.assets.items():
            self._copy_asset(source, normal_path(page_target.parent / relative), result)

    def _copy_static(self, pages: list[Page], result: BuildResult) -> None:
        page_sources = {page.source for page in pages}
        for source in sorted(self.source_root.rglob("*")):
            if not source.is_file() or source in page_sources or source in self.ignored_sources or source.is_relative_to(self.settings.output):
                continue
            relative = source.relative_to(self.source_root)
            if self.settings.markdown_mode:
                private = any(part in MARKDOWN_EXCLUDES for part in relative.parts) or relative.parts[:2] == ("vendor", "bundle")
                excluded = any(relative.match(pattern) for pattern in self.settings.exclude)
            else:
                private, excluded = False, self._excluded(source)
            if private or excluded or relative.name in PROJECT_FILES:
                continue
            if not self.settings.markdown_mode and any(part in {"_layouts", "_includes", "_posts"} for part in relative.parts):
                continue
            target = self.settings.output / relative
            if source.absolute() == target.absolute():
                continue
            self._copy_asset(source, target, result)

    def _write_feed(self, pages: list[Page], result: BuildResult) -> None:
        target = self.settings.output / "feed.xml"
        if target.exists() and any(page.output_relative == Path("feed.xml") for page in pages):
            return
        posts = [page for page in pages if page.relative.parts and page.relative.parts[0] == "_posts"]
        posts.sort(key=self._date, reverse=True)
        root_url = str(self.site.get("url", "")).rstrip("/") + str(self.site.get("baseurl", "")).rstrip("/")
        entries = []
        for post in posts[:20]:
            data = post.data()
            title = html.escape(str(data.get("title", post.source.stem)))
            url = root_url + post.url
            entries.append(f'<entry><title>{title}</title><link href="{html.escape(url)}"/><id>{html.escape(url)}</id><updated>{self._date(post).isoformat()}</updated></entry>')
        feed = f'<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom"><title>{html.escape(str(self.site.get("title", "")))}</title>{"".join(entries)}</feed>\n'
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(target, feed)
        result.written.append(target)
