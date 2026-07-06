from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .code import expand_code_directives
from .config import BuildOptions, deep_merge, load_config_file, options_from_mapping
from .context import BuildContext, Diagnostic
from .directives import expand_includes
from .errors import BuildError
from .frontmatter import split_frontmatter
from .graph import build_dependency_graph
from .rendering import (
    TocHeading,
    jekyll_compat_css,
    plain_text,
    prepare_toc,
    process_obsidian_images_markdown,
    process_obsidian_images,
    preserve_escaped_dollars_markdown,
    protect_math,
    queue_html_image_assets,
    render_fenced_code_blocks,
    render_jekyll_markdown,
    render_markdown,
    render_template,
    restore_math,
    restore_math_markdown,
)


@dataclass
class BuildResult:
    source: Path
    output: Path
    written: bool
    skipped: bool = False
    dependencies: set[Path] = field(default_factory=set)
    assets: list[tuple[Path, Path]] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    headings: list[TocHeading] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": str(self.source),
            "output": str(self.output),
            "written": self.written,
            "skipped": self.skipped,
            "dependencies": sorted(str(p) for p in self.dependencies),
            "assets": [[str(src), str(rel)] for src, rel in self.assets],
            "diagnostics": [d.format() for d in self.diagnostics],
            "metadata": self.metadata,
            "headings": [{"level": h.level, "title": h.text, "id": h.id, "line": h.line} for h in self.headings],
        }


_HEADING1_PREFIX = "# "


def _first_heading_title(markdown_text: str) -> str | None:
    in_fence = False
    fence = ""
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence = marker
            elif marker == fence:
                in_fence = False
            continue
        if in_fence:
            continue
        if line.startswith(_HEADING1_PREFIX):
            return plain_text(line[2:].strip().strip("# "))
    return None


def render_markdown_document(source_text: str, ctx: BuildContext) -> tuple[str, dict[str, Any], list[TocHeading]]:
    metadata, body = split_frontmatter(source_text)
    ctx.metadata.update(metadata)

    body = expand_includes(body, ctx, current_file=ctx.source_path, stack=(ctx.source_path.resolve(),))
    if ctx.options.output_mode == "jekyll":
        queue_html_image_assets(body, ctx, current_file=ctx.source_path)
        body = process_obsidian_images_markdown(body, ctx, current_file=ctx.source_path)
    else:
        body = process_obsidian_images(body, ctx, current_file=ctx.source_path)
    body, headings, _toc = prepare_toc(body, output_mode=ctx.options.output_mode)
    # Titles are plain text, so extract before math protection replaces TeX
    # spans with placeholders.
    title = str(metadata.get("title") or _first_heading_title(body) or ctx.source_path.name)
    body, math_spans = protect_math(body)
    if ctx.options.output_mode == "jekyll":
        body = preserve_escaped_dollars_markdown(body)
    body = expand_code_directives(body, ctx)

    if ctx.options.output_mode == "jekyll":
        if ctx.options.jekyll.math == "html":
            content_markdown = restore_math(body, math_spans, ctx.options.math)
        else:
            content_markdown = restore_math_markdown(body, math_spans)
        if ctx.options.jekyll.highlight_fences:
            content_markdown = render_fenced_code_blocks(content_markdown)
        document = render_jekyll_markdown(
            content=content_markdown,
            title=title,
            metadata=metadata,
            options=ctx.options,
        )
        return document, metadata, headings

    content_html = render_markdown(body, ctx)
    content_html = restore_math(content_html, math_spans, ctx.options.math)

    document = render_template(
        content=content_html,
        title=title,
        metadata=metadata,
        options=ctx.options,
        template_name=metadata.get("template"),
    )
    return document, metadata, headings


class MarkdownSiteBuilder:
    def __init__(self, options: BuildOptions | None = None) -> None:
        self.options = options or BuildOptions()

    @classmethod
    def from_config_file(cls, path: Path) -> "MarkdownSiteBuilder":
        data = load_config_file(path)
        options = options_from_mapping(data, cwd=path.parent)
        options.config_file = path
        return cls(options)

    def build_file(self, source: Path, output: Path, *, dry_run: bool = False) -> BuildResult:
        source = source.resolve()
        output = output.resolve()
        if not source.exists():
            raise BuildError(f"source does not exist: {source}")
        if output.exists() and self.options.no_overwrite and not self.options.force_rebuild:
            return BuildResult(source=source, output=output, written=False, skipped=True)

        ctx = BuildContext(source_path=source, output_path=output, options=self.options, dry_run=dry_run)
        ctx.add_dependency(source)
        source_text = source.read_text(encoding="utf-8")
        document, metadata, headings = render_markdown_document(source_text, ctx)
        result = BuildResult(
            source=source,
            output=output,
            written=False,
            dependencies=set(ctx.dependencies),
            assets=list(ctx.assets),
            diagnostics=list(ctx.diagnostics),
            metadata=dict(metadata),
            headings=headings,
        )
        if dry_run:
            return result
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document, encoding="utf-8")
        ctx.copy_queued_assets()
        result.written = True
        return result

    def write_jekyll_assets(self, output_root: Path) -> None:
        if not self.options.jekyll.stylesheet:
            return
        stylesheet = output_root / self.options.jekyll.stylesheet
        stylesheet.parent.mkdir(parents=True, exist_ok=True)
        stylesheet.write_text(jekyll_compat_css(), encoding="utf-8")

    def dry_run_json(self, jobs: list[tuple[Path, Path]]) -> str:
        graph = build_dependency_graph(jobs, self.options)
        results = [self.build_file(src, out, dry_run=True).as_dict() for src, out in jobs]
        return json.dumps({"jobs": results, "graph": graph.as_dict()}, indent=2)


def load_options(cwd: Path, config_path: Path | None = None, overrides: dict[str, Any] | None = None) -> BuildOptions:
    data: dict[str, Any] = {}
    path = config_path or (cwd / "md2html.json")
    if path.exists():
        data = load_config_file(path)
    if overrides:
        data = deep_merge(data, overrides)
    options = options_from_mapping(data, cwd=cwd)
    options.config_file = path if path.exists() else None
    return options
