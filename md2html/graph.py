from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .config import BuildOptions
from .directives import iter_include_paths, iter_src_directives
from .errors import IncludeCycleError
from .frontmatter import split_frontmatter
from .paths import resolve_lenient, resolve_markdown_reference, source_output_path


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
        upstream = resolve_lenient(upstream)
        downstream = resolve_lenient(downstream)
        self.edges.append(DependencyEdge(upstream, downstream, kind))
        self.reverse[upstream].add(downstream)

    def add_page_dependency(self, page: Path, dependency: Path) -> None:
        self.dependencies_by_page[resolve_lenient(page)].add(resolve_lenient(dependency))

    def affected_sources(self, changed_paths: Iterable[Path]) -> set[Path]:
        affected: set[Path] = set()
        seen: set[Path] = set()
        queue: deque[Path] = deque(resolve_lenient(path) for path in changed_paths)
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
    page_outputs = {resolve_lenient(src): resolve_lenient(out) for src, out in jobs}
    graph = DependencyGraph(page_outputs=page_outputs)
    scanned: set[Path] = set()

    def scan_markdown(markdown_file: Path, stack: tuple[Path, ...], root_page: Path) -> None:
        markdown_file = resolve_lenient(markdown_file)
        if markdown_file in scanned:
            return
        scanned.add(markdown_file)

        if not markdown_file.exists():
            graph.missing.add(markdown_file)
            graph.add_page_dependency(root_page, markdown_file)
            return

        text = markdown_file.read_text(encoding="utf-8")
        _metadata, body = split_frontmatter(text)

        for raw_path in iter_include_paths(body):
            include_path = resolve_markdown_reference(raw_path, current_file=markdown_file, project_root=options.project_root)
            graph.add_edge(include_path, markdown_file, "@include")
            graph.add_page_dependency(root_page, include_path)
            if include_path in stack:
                chain = " -> ".join(str(p) for p in (*stack, include_path))
                raise IncludeCycleError(f"include cycle detected: {chain}")
            scan_markdown(include_path, (*stack, include_path), root_page)

        for directive in iter_src_directives(body):
            src_path = resolve_markdown_reference(directive.path, current_file=markdown_file, project_root=options.project_root)
            graph.add_edge(src_path, markdown_file, "@src")
            graph.add_page_dependency(root_page, src_path)
            if not src_path.exists():
                graph.missing.add(src_path)

            out_path = source_output_path(src_path, options.code.output_suffix)
            if out_path.exists() or options.execute:
                graph.add_edge(out_path, markdown_file, "@src-output")
                graph.add_page_dependency(root_page, out_path)

    for source in page_outputs:
        graph.add_page_dependency(source, source)
        scan_markdown(source, (source,), source)
    return graph
