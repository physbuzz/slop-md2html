from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .code import parse_src_directive
from .config import BuildOptions
from .errors import IncludeCycleError
from .frontmatter import split_frontmatter

_INCLUDE_RE = re.compile(r"^\s*@include\((?P<path>[^)]+)\)\s*$", re.MULTILINE)
_SRC_RE = re.compile(r"^\s*@src\((?P<args>[^)]*)\)\s*$", re.MULTILINE)


def _resolve_lenient(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _resolve_reference(raw: str, *, current_file: Path, project_root: Path) -> Path:
    raw_path = Path(raw).expanduser()
    if raw_path.is_absolute():
        return _resolve_lenient(raw_path)
    candidate = _resolve_lenient(current_file.parent / raw_path)
    if candidate.exists():
        return candidate
    return _resolve_lenient(project_root / raw_path)


def _source_output_path(src: Path, suffix: str) -> Path:
    if suffix.startswith("."):
        return src.with_suffix(suffix)
    return src.with_name(src.name + suffix)


@dataclass(frozen=True)
class DependencyEdge:
    upstream: Path
    downstream: Path
    kind: str


@dataclass
class DependencyGraph:
    """Small graph for article-level rebuild notifications.

    Edges point upstream -> downstream. So a Markdown page containing
    ``@src(main.cpp)`` creates a ``main.cpp -> page.md`` edge. We intentionally
    do not scan language-level dependencies such as ``#include \"file.h\"``.
    """

    page_outputs: dict[Path, Path]
    edges: list[DependencyEdge] = field(default_factory=list)
    reverse: dict[Path, set[Path]] = field(default_factory=lambda: defaultdict(set))
    dependencies_by_page: dict[Path, set[Path]] = field(default_factory=lambda: defaultdict(set))
    missing: set[Path] = field(default_factory=set)

    def add_edge(self, upstream: Path, downstream: Path, kind: str) -> None:
        upstream = _resolve_lenient(upstream)
        downstream = _resolve_lenient(downstream)
        self.edges.append(DependencyEdge(upstream, downstream, kind))
        self.reverse[upstream].add(downstream)

    def add_page_dependency(self, page: Path, dependency: Path) -> None:
        self.dependencies_by_page[_resolve_lenient(page)].add(_resolve_lenient(dependency))

    def affected_sources(self, changed_paths: Iterable[Path]) -> set[Path]:
        affected: set[Path] = set()
        seen: set[Path] = set()
        queue: deque[Path] = deque(_resolve_lenient(path) for path in changed_paths)
        while queue:
            node = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            if node in self.page_outputs:
                affected.add(node)
            for downstream in self.reverse.get(node, set()):
                if downstream not in seen:
                    queue.append(downstream)
        return affected

    def affected_jobs(self, changed_paths: Iterable[Path]) -> list[tuple[Path, Path]]:
        sources = self.affected_sources(changed_paths)
        return [(src, self.page_outputs[src]) for src in sorted(sources, key=lambda p: str(p))]

    def as_dict(self) -> dict[str, object]:
        return {
            "edges": [
                {"from": str(edge.upstream), "to": str(edge.downstream), "kind": edge.kind}
                for edge in self.edges
            ],
            "missing": sorted(str(path) for path in self.missing),
            "page_dependencies": {
                str(page): sorted(str(dep) for dep in deps)
                for page, deps in sorted(self.dependencies_by_page.items(), key=lambda item: str(item[0]))
            },
        }


def build_dependency_graph(jobs: Iterable[tuple[Path, Path]], options: BuildOptions) -> DependencyGraph:
    page_outputs = {_resolve_lenient(src): _resolve_lenient(out) for src, out in jobs}
    graph = DependencyGraph(page_outputs=page_outputs)
    scanned: set[Path] = set()

    def scan_markdown(markdown_file: Path, stack: tuple[Path, ...], root_page: Path) -> None:
        markdown_file = _resolve_lenient(markdown_file)
        if markdown_file in scanned:
            return
        scanned.add(markdown_file)

        if not markdown_file.exists():
            graph.missing.add(markdown_file)
            graph.add_page_dependency(root_page, markdown_file)
            return

        text = markdown_file.read_text(encoding="utf-8")
        _metadata, body = split_frontmatter(text)

        for match in _INCLUDE_RE.finditer(body):
            raw_path = match.group("path").strip().strip('"\'')
            include_path = _resolve_reference(raw_path, current_file=markdown_file, project_root=options.project_root)
            graph.add_edge(include_path, markdown_file, "@include")
            graph.add_page_dependency(root_page, include_path)
            if include_path in stack:
                chain = " -> ".join(str(p) for p in (*stack, include_path))
                raise IncludeCycleError(f"include cycle detected: {chain}")
            scan_markdown(include_path, (*stack, include_path), root_page)

        for match in _SRC_RE.finditer(body):
            directive = parse_src_directive(match.group("args"))
            src_path = _resolve_reference(directive.path, current_file=markdown_file, project_root=options.project_root)
            graph.add_edge(src_path, markdown_file, "@src")
            graph.add_page_dependency(root_page, src_path)
            if not src_path.exists():
                graph.missing.add(src_path)

            out_path = _source_output_path(src_path, options.code.output_suffix)
            if out_path.exists() or options.execute:
                graph.add_edge(out_path, markdown_file, "@src-output")
                graph.add_page_dependency(root_page, out_path)

    for source in page_outputs:
        graph.add_page_dependency(source, source)
        scan_markdown(source, (source,), source)
    return graph
