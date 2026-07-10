"""Project discovery, site modeling, and output."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import base64
import html
from importlib.resources import files
from pathlib import Path
import re
import shutil
from typing import Any

import yaml
from liquid.exceptions import LiquidError

from .render import ContentRenderer, Features, Rendered, liquid_source, make_liquid, parse_frontmatter, slugify
from .settings import Settings


SOURCE_SUFFIXES = {".md", ".markdown"}
PROJECT_FILES = {"md2html.config", "md2html.json", "md2html.yml", "md2html.yaml", "_config.yml", "_config.yaml"}
CHTML_CDN = "https://cdn.jsdelivr.net/npm/@mathjax/mathjax-tex-font@4.1.3/chtml/woff2"
FONT_FACE = re.compile(r"@font-face\s*/\*\s*(MJX(?:-TEX)?-[A-Z0-9]+)\s*\*/\s*\{.*?\}\s*", re.DOTALL)


@dataclass
class Page:
    source: Path
    relative: Path
    metadata: dict[str, Any]
    body: str
    markdown: bool
    url: str
    output_relative: Path
    rendered: Rendered | None = None

    def data(self) -> dict[str, Any]:
        data = dict(self.metadata)
        data.setdefault("title", self._source_title())
        data["url"] = self.url
        data.setdefault("path", self.relative.as_posix())
        data.setdefault("tags", [])
        data.setdefault("categories", [])
        data.setdefault("excerpt", self._excerpt())
        return data

    def _source_title(self) -> str:
        match = re.search(r"^#[ \t]+(.+?)[ \t]*#*[ \t]*$", self.body, re.MULTILINE)
        if match:
            return re.sub(r"<[^>]+>|[*_`]", "", match.group(1)).strip()
        return self.source.stem.replace("-", " ").title()

    def _excerpt(self) -> str:
        for paragraph in re.split(r"\n\s*\n", self.body):
            value = re.sub(r"<[^>]+>|^[#>*-]+\s*", "", paragraph.strip())
            if value and not value.startswith(("@", "{%")):
                return value
        return ""


@dataclass
class BuildResult:
    written: list[Path] = field(default_factory=list)
    copied: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dependencies: set[Path] = field(default_factory=set)

    @property
    def output_count(self) -> int:
        return len(self.written) + len(self.copied)


class Project:
    """A complete build, whether it contains one page or a native site."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.source_root = settings.input if settings.input.is_dir() else settings.input.parent
        self.bundled_templates = Path(str(files("md2html2").joinpath("default_templates")))
        self.bundled_assets = Path(str(files("md2html2").joinpath("assets")))
        self.site = self._site_data()
        template_dirs = [
            self.source_root / "_includes",
            self.source_root / "_layouts",
            *( [settings.templates] if settings.templates else []),
            self.bundled_templates,
        ]
        self.liquid = make_liquid((path for path in template_dirs if path is not None), self.site)
        self.renderer = ContentRenderer(settings, self.liquid)
        self.math_fonts: set[str] = set()
        self.has_chtml = False

    def build(self) -> BuildResult:
        self._validate_paths()
        result = BuildResult()
        pages = self._discover_pages()
        self._populate_site(pages)
        if self.settings.clean and self.settings.output_mode == "site" and self.settings.output.exists():
            shutil.rmtree(self.settings.output)
        for page in pages:
            rendered = self._render_page(page)
            page.rendered = rendered
            if self.settings.output_mode == "site" and rendered.features.math_css:
                self.has_chtml = True
                stylesheet, fonts = self._write_math_assets(rendered.features, result)
                tags = [
                    *(f'  <link rel="preload" href="{font}" as="font" type="font/woff2" crossorigin>' for font in fonts),
                    f'  <link rel="stylesheet" href="{stylesheet}">',
                ]
                assets = "\n".join(tags) + "\n"
                head_end = rendered.html.find("</head>")
                head = rendered.html[:head_end] if head_end >= 0 else rendered.html
                external_script = re.search(r"<script\b[^>]*\bsrc\s*=", head, re.IGNORECASE)
                if external_script:
                    line_start = rendered.html.rfind("\n", 0, external_script.start()) + 1
                    insertion = line_start if rendered.html[line_start:external_script.start()].isspace() else external_script.start()
                    rendered.html = rendered.html[:insertion] + assets + rendered.html[insertion:]
                elif head_end >= 0:
                    rendered.html = rendered.html[:head_end] + assets + rendered.html[head_end:]
                else:
                    rendered.html = assets + rendered.html
            target = self._target(page)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered.html, encoding="utf-8")
            result.written.append(target)
            result.warnings.extend(rendered.warnings)
            result.dependencies.update(rendered.dependencies)
        if self.settings.output_mode == "site":
            self._prune_math_assets()
        if self.settings.input.is_dir():
            self._copy_static(pages, result)
        if self.settings.output_mode == "site":
            self._write_feed(pages, result)
        return result

    def _validate_paths(self) -> None:
        if not self.settings.input.exists():
            raise ValueError(f"input does not exist: {self.settings.input}")
        if self.settings.input.is_dir():
            source = self.settings.input.resolve()
            output = self.settings.output.resolve()
            if source == output:
                raise ValueError("site output cannot be the input directory")
            if self.settings.clean and source.is_relative_to(output):
                raise ValueError("clean site output cannot contain the input directory")

    def _site_data(self) -> dict[str, Any]:
        data = dict(self.settings.site_data)
        for name in ("_config.yml", "_config.yaml"):
            path = self.source_root / name
            if path.is_file():
                try:
                    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                except (OSError, yaml.YAMLError) as error:
                    raise ValueError(f"could not read site data {path}: {error}") from error
                if isinstance(loaded, dict):
                    loaded.update(data)
                    data = loaded
                break
        data.setdefault("title", self.source_root.name)
        data.setdefault("description", "")
        data.setdefault("url", "")
        data.setdefault("baseurl", "")
        data["time"] = datetime.now(timezone.utc)
        return data

    def _discover_pages(self) -> list[Page]:
        source = self.settings.input
        if source.is_file():
            metadata, body = parse_frontmatter(source.read_text(encoding="utf-8"))
            relative = Path(source.name)
            output_relative = Path(self.settings.output.name)
            return [Page(source, relative, metadata, body, source.suffix.lower() in SOURCE_SUFFIXES, "/" + output_relative.name, output_relative)]

        pattern = "**/*" if self.settings.recursive or self.settings.output_mode == "site" else "*"
        pages: list[Page] = []
        for path in sorted(source.glob(pattern)):
            if not path.is_file() or self._excluded(path):
                continue
            relative = path.relative_to(source)
            if path.suffix.lower() in SOURCE_SUFFIXES:
                metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
                url, output = self._output_policy(relative, metadata)
                pages.append(Page(path, relative, metadata, body, True, url, output))
            elif path.suffix.lower() in {".html", ".htm", ".xml"}:
                text = path.read_text(encoding="utf-8")
                metadata, body = parse_frontmatter(text)
                if metadata:
                    url, output = self._output_policy(relative, metadata)
                    pages.append(Page(path, relative, metadata, body, False, url, output))
        return pages

    def _excluded(self, path: Path) -> bool:
        relative = path.relative_to(self.source_root)
        parts = relative.parts
        if self.settings.output.is_relative_to(self.source_root) and path.is_relative_to(self.settings.output):
            return True
        if relative.name.startswith("_"):
            return True
        if any(part.startswith(".") for part in parts):
            return True
        if any(part.startswith("_") and part not in {"_posts"} for part in parts[:-1]):
            return True
        excludes = [*self.settings.exclude, *(self.site.get("exclude") or [])]
        for pattern in excludes:
            normalized = str(pattern).strip("/")
            if relative.as_posix() == normalized or relative.as_posix().startswith(normalized + "/") or relative.match(normalized):
                return True
        return False

    def _output_policy(self, relative: Path, metadata: dict[str, Any]) -> tuple[str, Path]:
        permalink = metadata.get("permalink")
        post = relative.parts and relative.parts[0] == "_posts"
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})-(.+)", relative.stem) if post else None
        if permalink:
            url = str(permalink)
        elif match:
            year, month, day, slug = match.groups()
            pattern = str(self.site.get("permalink", "/:year/:month/:day/:title.html"))
            url = pattern.replace(":year", year).replace(":month", month).replace(":day", day).replace(":title", slugify(slug))
        else:
            normal = relative.with_suffix(".html")
            url = "/" + normal.as_posix()
        if not url.startswith("/"):
            url = "/" + url
        if url.endswith("/"):
            output = Path(url.lstrip("/")) / "index.html"
        else:
            output = Path(url.lstrip("/"))
        return url, output

    def _populate_site(self, pages: list[Page]) -> None:
        post_pages = [page for page in pages if page.relative.parts and page.relative.parts[0] == "_posts"]
        post_pages.sort(key=lambda page: self._date(page), reverse=True)
        post_data = [page.data() for page in post_pages]
        self.site["posts"] = post_data
        self.site["pages"] = [page.data() for page in pages]
        tags: dict[str, list[dict[str, Any]]] = {}
        categories: dict[str, list[dict[str, Any]]] = {}
        for post, data in zip(post_pages, post_data):
            post.metadata["date"] = data["date"] = self._date(post)
            for name in self._names(data.get("tags")):
                tags.setdefault(name, []).append(data)
            for name in self._names(data.get("categories")):
                categories.setdefault(name, []).append(data)
        self.site["tags"] = tags
        self.site["categories"] = categories
        self.site["tag_list"] = [
            {"name": name, "slug": slugify(name), "posts": values}
            for name, values in sorted(tags.items(), key=lambda item: item[0].lower())
        ]

    @staticmethod
    def _names(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [part for part in re.split(r"\s*,\s*|\s+", value) if part]
        return [str(item) for item in value]

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

    def _render_page(self, page: Page) -> Rendered:
        page_data = page.data()
        context = {"site": self.site, "page": page_data}
        rendered = self.renderer.render(page.source, page.body, context, markdown=page.markdown)
        page_data["title"] = rendered.title
        page.metadata["title"] = rendered.title
        if self.settings.output_mode == "site":
            content = self._apply_layouts(rendered.html, page_data, page.source, rendered.warnings)
        else:
            content = self._page_template(rendered, page_data)
        rendered.html = content.rstrip() + "\n"
        return rendered

    def _apply_layouts(self, content: str, page: dict[str, Any], source: Path, warnings: list[str]) -> str:
        layout_name = page.get("layout")
        seen: set[str] = set()
        while layout_name:
            name = str(layout_name)
            if name in seen:
                warnings.append(f"layout cycle while rendering {source}: {name}")
                break
            seen.add(name)
            path = self._find_layout(name)
            if not path:
                warnings.append(f"layout not found for {source}: {name}")
                break
            metadata, template = parse_frontmatter(path.read_text(encoding="utf-8"))
            try:
                content = self.liquid.from_string(liquid_source(template)).render(site=self.site, page=page, content=content, layout=metadata)
            except LiquidError as error:
                warnings.append(f"layout failed for {source}: {error}")
                break
            layout_name = metadata.get("layout")
        return content

    def _find_layout(self, name: str) -> Path | None:
        filename = name if Path(name).suffix else name + ".html"
        candidates = [
            self.source_root / "_layouts" / filename,
            *(([self.settings.templates / filename]) if self.settings.templates else []),
            self.bundled_templates / filename,
        ]
        return next((path for path in candidates if path.is_file()), None)

    def _page_template(self, rendered: Rendered, page: dict[str, Any]) -> str:
        path = self._find_layout(self.settings.template)
        if path is None:
            raise ValueError(f"template not found: {self.settings.template}")
        css = self._css(rendered.features, path)
        backend = self.settings.math.backend.lower()
        context = {
            "site": self.site,
            "page": page,
            "content": rendered.html,
            "md2html": {"css": css, "use_mathjax": rendered.features.math and backend == "mathjax"},
        }
        try:
            return self.liquid.from_string(liquid_source(path.read_text(encoding="utf-8"))).render(**context)
        except LiquidError as error:
            raise ValueError(f"template failed: {error}") from error

    def _css(self, features: Features, template: Path) -> str:
        paths: list[Path] = []
        if self.settings.css is None:
            companion = template.with_suffix(".css")
            if companion.is_file():
                paths.append(companion)
            elif template.name == "page.html":
                paths.append(self.bundled_assets / "page-base.css")
                if features.code or features.output:
                    paths.append(self.bundled_assets / "feature-code.css")
                if features.math:
                    paths.append(self.bundled_assets / "feature-math.css")
                if features.toc:
                    paths.append(self.bundled_assets / "feature-toc.css")
                if features.images:
                    paths.append(self.bundled_assets / "feature-image.css")
                if features.warning:
                    paths.append(self.bundled_assets / "feature-warning.css")
            elif template.name == "barebones.html":
                paths.append(self.bundled_assets / "barebones.css")
        else:
            for name in self.settings.css:
                path = Path(name).expanduser()
                paths.append(path if path.is_absolute() else self.settings.project_root / path)
        values = []
        for path in paths:
            try:
                values.append(path.read_text(encoding="utf-8"))
            except OSError as error:
                raise ValueError(f"could not read CSS {path}: {error}") from error
        if features.math_css:
            values.append(self._standalone_math_css(features))
        return "\n".join(values)

    @staticmethod
    def _font_family(name: str) -> str:
        return "MJX-BRK" if name == "brk" else "MJX-TEX-" + name.upper()

    def _selected_math_css(self, features: Features, fonts: set[str]) -> str:
        families = {self._font_family(name) for name in fonts}
        return FONT_FACE.sub(lambda match: match.group(0) if match.group(1) in families else "", features.math_css)

    def _standalone_math_css(self, features: Features) -> str:
        mode = self.settings.math.chtml_fonts
        fonts = set(features.math_fonts)
        css = self._selected_math_css(features, fonts)
        if mode == "none":
            return FONT_FACE.sub("", css)
        if mode == "inline" and features.math_font_dir:
            for name in fonts:
                filename = f"mjx-tex-{name}.woff2"
                source = features.math_font_dir / filename
                encoded = base64.b64encode(source.read_bytes()).decode("ascii")
                css = css.replace(f'url("mathjax/woff2/{filename}")', f'url("data:font/woff2;base64,{encoded}")')
            return css
        return css.replace("mathjax/woff2", CHTML_CDN)

    def _write_math_assets(self, features: Features, result: BuildResult) -> tuple[str, list[str]]:
        mode = self.settings.math.chtml_fonts
        self.math_fonts.update(features.math_fonts)
        fonts = set(self.math_fonts)
        if mode == "all" and features.math_font_dir:
            fonts = {path.stem.removeprefix("mjx-tex-") for path in features.math_font_dir.glob("mjx-tex-*.woff2")}
        css = self._selected_math_css(features, fonts)
        if mode == "none":
            css = FONT_FACE.sub("", css)
        elif mode == "remote":
            css = css.replace("mathjax/woff2", CHTML_CDN)
        elif mode == "inline" and features.math_font_dir:
            for name in fonts:
                filename = f"mjx-tex-{name}.woff2"
                encoded = base64.b64encode((features.math_font_dir / filename).read_bytes()).decode("ascii")
                css = css.replace(f'url("mathjax/woff2/{filename}")', f'url("data:font/woff2;base64,{encoded}")')
        elif features.math_font_dir:
            for name in fonts:
                source = features.math_font_dir / f"mjx-tex-{name}.woff2"
                target = self.settings.output / "assets/md2html/mathjax/woff2" / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists() or target.read_bytes() != source.read_bytes():
                    shutil.copy2(source, target)
                if target not in result.copied:
                    result.copied.append(target)

        relative = Path("assets/md2html/mathjax-chtml.css")
        target = self.settings.output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(css.rstrip() + "\n", encoding="utf-8")
        if target not in result.written:
            result.written.append(target)
        base = str(self.site.get("baseurl", "")).rstrip("/")
        stylesheet = base + "/" + relative.as_posix()
        preload_names = features.math_fonts if mode in {"auto", "all"} else set()
        preload = [base + f"/assets/md2html/mathjax/woff2/mjx-tex-{name}.woff2" for name in sorted(preload_names)]
        return stylesheet, preload

    def _prune_math_assets(self) -> None:
        stylesheet = self.settings.output / "assets/md2html/mathjax-chtml.css"
        font_root = self.settings.output / "assets/md2html/mathjax/woff2"
        mode = self.settings.math.chtml_fonts
        if not self.has_chtml:
            stylesheet.unlink(missing_ok=True)
            if font_root.parent.exists():
                shutil.rmtree(font_root.parent)
            return
        if mode in {"remote", "inline", "none"}:
            if font_root.parent.exists():
                shutil.rmtree(font_root.parent)
            return
        if mode == "auto" and font_root.exists():
            keep = {f"mjx-tex-{name}.woff2" for name in self.math_fonts}
            for path in font_root.glob("*.woff2"):
                if path.name not in keep:
                    path.unlink()

    def _target(self, page: Page) -> Path:
        if self.settings.input.is_file():
            return self.settings.output
        return self.settings.output / page.output_relative

    def _copy_static(self, pages: list[Page], result: BuildResult) -> None:
        page_sources = {page.source.resolve() for page in pages}
        for source in sorted(self.source_root.rglob("*")):
            if not source.is_file() or source.resolve() in page_sources or self._excluded(source):
                continue
            relative = source.relative_to(self.source_root)
            if relative.name in PROJECT_FILES or any(part in {"_layouts", "_includes", "_posts"} for part in relative.parts):
                continue
            if source.suffix.lower() in SOURCE_SUFFIXES:
                continue
            target = self.settings.output / relative
            if source.resolve() == target.resolve():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            result.copied.append(target)

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
        target.write_text(feed, encoding="utf-8")
        result.written.append(target)
