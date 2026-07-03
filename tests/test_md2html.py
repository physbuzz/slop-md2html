from __future__ import annotations

from pathlib import Path
import errno
import sys

from md2html.builder import MarkdownSiteBuilder
from md2html.code import _default_command
from md2html.cli import build_jobs, discover_sources, filter_jekyll_sources, make_parser, output_exclusions
from md2html.config import BuildOptions
from md2html.directives import iter_include_paths, iter_src_directives, parse_src_directive
from md2html.frontmatter import dump_frontmatter, split_frontmatter
from md2html.paths import source_output_path
from md2html.rendering import Slugger, collect_headings, generate_toc, generate_toc_markdown, protect_math, restore_math
from md2html.watch import (
    WatchExclusions,
    _initial_build_message,
    _jobs_needing_build,
    _make_http_server,
    _rebuild_message,
    _stop_observer,
    _watch_root_message,
    local_server_url,
)


def test_slug_policy_matches_examples():
    s = Slugger()
    assert s.slug("Section 2.5") == "section-25"
    assert s.slug("Exercise 2.77") == "exercise-277"


def test_math_is_protected_from_markdown_emphasis():
    text, spans = protect_math("Inline $x_1,x_2$ and **bold**")
    assert "@@MD2HTML_MATH_0@@" in text
    restored = restore_math("<p>" + text + "</p>", spans, BuildOptions().math)
    assert "$x_1,x_2$" in restored
    assert "data-tex=\"x_1,x_2\"" in restored


def test_stray_double_backticks_do_not_swallow_fences():
    md = (
        "The ``implicit'' definition of `integral`:\n"
        "\n"
        "```rkt\n"
        "(define (integral x) x)\n"
        "```\n"
        "\n"
        "More prose with $x_1$ math.\n"
    )
    text, spans = protect_math(md)
    assert "@@MD2HTML_CODE_" not in text
    assert "(define (integral x) x)" in text
    restored = restore_math(text, spans, BuildOptions().math)
    assert "@@MD2HTML_" not in restored


def test_toc_compacts_exercises():
    md = """# Title

@toc

## Section 1

## Exercises

### Exercise 2.77

### Solution

### Exercise 2.78
"""
    headings = collect_headings(md)
    toc = generate_toc(headings)
    assert "Directory" in toc
    assert "toc-exercises" in toc
    assert "#exercise-277" in toc
    assert "#exercise-278" in toc
    assert "Solution" not in toc


def test_markdown_toc_compacts_exercises():
    md = """# Title

@toc

## Section 1

## Exercises

### Exercise 2.77

### Solution

### Exercise 2.78
"""
    headings = collect_headings(md)
    toc = generate_toc_markdown(headings)
    assert "## Directory" in toc
    assert "- [Section 1](#section-1)" in toc
    assert "- *Exercises:* ([Exercise 2.77](#exercise-277), [Exercise 2.78](#exercise-278))" in toc
    assert "Solution" not in toc


def test_frontmatter_without_metadata_returns_original_body():
    body = "# Plain note\n\nNo metadata.\n"
    metadata, parsed = split_frontmatter(body)

    assert metadata == {}
    assert parsed == body


def test_frontmatter_parses_yaml_metadata_through_wrapper():
    metadata, body = split_frontmatter("---\ntitle: Test\nstylesheets:\n  - a.css\n---\n\n# Body\n")

    assert metadata == {"title": "Test", "stylesheets": ["a.css"]}
    assert body == "\n# Body\n"


def test_dump_frontmatter_round_trips_common_metadata():
    dumped = dump_frontmatter({"title": "Round Trip", "draft": False, "tags": ["one", "two"]})
    metadata, body = split_frontmatter(dumped + "Body\n")

    assert metadata == {"title": "Round Trip", "draft": False, "tags": ["one", "two"]}
    assert body == "\nBody\n"


def test_included_files_ignore_frontmatter_metadata(tmp_path: Path):
    partial = tmp_path / "partial.md"
    page = tmp_path / "page.md"
    partial.write_text("---\ntitle: Included Title\n---\n\nIncluded body\n", encoding="utf-8")
    page.write_text("---\ntitle: Page Title\n---\n\n@include(partial.md)\n", encoding="utf-8")

    result = MarkdownSiteBuilder(BuildOptions(project_root=tmp_path)).build_file(page, tmp_path / "page.html")
    html = (tmp_path / "page.html").read_text(encoding="utf-8")

    assert result.metadata == {"title": "Page Title"}
    assert "Included body" in html
    assert "Included Title" not in html


def test_src_flag_policy():
    plain = parse_src_directive("code/example.py")
    assert not plain.collapsed
    assert not plain.collapsible
    assert not plain.expanded_by_default

    collapsible = parse_src_directive("code/example.py, collapsible")
    assert not collapsible.collapsed
    assert collapsible.collapsible
    assert collapsible.expanded_by_default

    collapsed = parse_src_directive("code/example.py, collapsed")
    assert collapsed.collapsed
    assert collapsed.collapsible
    assert not collapsed.expanded_by_default


def test_directive_scanning_uses_shared_parsers():
    md = '@include("partials/intro.md")\n\n@src("code/example.py", collapsed, caption="Example")\n'

    assert list(iter_include_paths(md)) == ["partials/intro.md"]
    src_directives = list(iter_src_directives(md))
    assert len(src_directives) == 1
    assert src_directives[0].path == "code/example.py"
    assert src_directives[0].collapsed
    assert src_directives[0].options["caption"] == "Example"


def test_builder_renders_includes_images_toc_and_code(tmp_path: Path):
    (tmp_path / "partials").mkdir()
    (tmp_path / "partials" / "intro.md").write_text("Included $x_1,x_2$\n", encoding="utf-8")
    (tmp_path / "code").mkdir()
    (tmp_path / "code" / "hello.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "code" / "hello.out").write_text("hello\n", encoding="utf-8")
    (tmp_path / "img").mkdir()
    (tmp_path / "img" / "pic.svg").write_text("<svg></svg>", encoding="utf-8")
    (tmp_path / "img" / "_private.svg").write_text("<svg></svg>", encoding="utf-8")
    source = tmp_path / "note.md"
    source.write_text(
        """---
title: Test Note
---
@include(partials/intro.md)

@toc

## Section 2.5

![[img/pic.svg|width=70%|alt=Picture]]

### Exercises

#### Exercise 2.77

@src(code/hello.py, collapsed)
""",
        encoding="utf-8",
    )
    out = tmp_path / "note.html"
    options = BuildOptions(project_root=tmp_path)
    result = MarkdownSiteBuilder(options).build_file(source, out)
    html = out.read_text(encoding="utf-8")
    assert result.written
    assert "Test Note" in html
    assert "section-25" in html
    assert "exercise-277" in html
    assert "data-tex=\"x_1,x_2\"" in html
    assert "collapsible-code" in html
    assert '<details class="collapsible-code">' in html
    assert '<details class="collapsible-code" open>' not in html
    assert "hello" in html
    assert "width: 70%" in html


def test_jekyll_output_is_markdown_with_frontmatter_and_directive_expansion(tmp_path: Path):
    (tmp_path / "code").mkdir()
    (tmp_path / "code" / "hello.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "code" / "hello.out").write_text("hello\n", encoding="utf-8")
    (tmp_path / "img").mkdir()
    (tmp_path / "img" / "pic.svg").write_text("<svg></svg>", encoding="utf-8")
    source = tmp_path / "note.md"
    source.write_text(
        """---
title: Test Note
layout: post
render_with_liquid: false
---
@toc

## Section 1

![[img/pic.svg|width=70%|alt=Picture]]

<div style="text-align: center;">
  <img src="img/pic.svg" style="width: 50%;" alt="Raw picture">
  <img src="img/_private.svg" alt="Private picture">
</div>

## Exercises

### Exercise 2.77

@src(code/hello.py)

@src(code/hello.py, collapsed)
""",
        encoding="utf-8",
    )
    output_root = tmp_path / "jekyll"
    out = output_root / "notes" / "note.md"
    builder = MarkdownSiteBuilder(BuildOptions(project_root=tmp_path, output_mode="jekyll", jekyll_output_root=output_root))
    result = builder.build_file(source, out)
    builder.write_jekyll_assets(output_root)
    text = out.read_text(encoding="utf-8")

    assert result.written
    assert "layout: post" in text
    assert "title: Test Note" in text
    assert "render_with_liquid: false" in text
    assert "md2html_styles" not in text
    assert "pygments: true" not in text
    assert "## Directory" in text
    assert "- *Exercises:* ([Exercise 2.77](#exercise-277))" in text
    assert "![Picture](img/pic.svg){: .obsidian-image style=\"width: 70%;\"}" in text
    assert '<div style="text-align: center;">' in text
    assert '<img src="img/pic.svg" style="width: 50%;" alt="Raw picture">' in text
    assert '<img src="img/_private.svg" alt="Private picture">' in text
    assert '<div class="code-box" markdown="1">' in text
    assert '<div class="code-header"><a href="code/hello.py">code/hello.py</a></div>' in text
    assert '<details class="collapsible-code">' in text
    assert '<summary class="code-summary"><a href="code/hello.py">code/hello.py</a>' in text
    assert '<div class="codehilite">' in text
    assert '<div class="code-output">' in text
    assert '<pre>hello\n</pre>' in text
    assert "```python" not in text
    css = output_root / "assets" / "css" / "md2html.css"
    assert css.exists()
    assert ".codehilite" in css.read_text(encoding="utf-8")
    assert (out.parent / "img" / "pic.svg").exists()
    assert not (out.parent / "img" / "_private.svg").exists()


def test_jekyll_cli_jobs_use_markdown_suffix(tmp_path: Path):
    site = tmp_path / "site"
    site.mkdir()
    page = site / "index.md"
    page.write_text("# Home\n", encoding="utf-8")

    jobs = build_jobs([page], [site], site / "jekyll", recursive=True, output_suffix=".md")

    assert jobs == [(page, site / "jekyll" / "index.md")]


def test_jekyll_source_filter_skips_private_paths(tmp_path: Path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.md").write_text("# Home\n", encoding="utf-8")
    (site / "_draft.md").write_text("# Draft\n", encoding="utf-8")
    (site / "_partials").mkdir()
    (site / "_partials" / "card.md").write_text("# Card\n", encoding="utf-8")

    sources = discover_sources([site], recursive=True)
    filtered = filter_jekyll_sources(sources, [site], recursive=True)

    assert filtered == [site / "index.md"]


def test_src_collapsible_is_expanded_and_plain_src_is_not_collapsible(tmp_path: Path):
    (tmp_path / "code").mkdir()
    (tmp_path / "code" / "plain.py").write_text("print('plain')\n", encoding="utf-8")
    (tmp_path / "code" / "collapsible.py").write_text("print('collapsible')\n", encoding="utf-8")
    source = tmp_path / "note.md"
    source.write_text(
        """@src(code/plain.py)

@src(code/collapsible.py, collapsible)
""",
        encoding="utf-8",
    )
    out = tmp_path / "note.html"
    MarkdownSiteBuilder(BuildOptions(project_root=tmp_path)).build_file(source, out)
    html = out.read_text(encoding="utf-8")

    assert '<div class="code-header"><a href="code/plain.py">code/plain.py</a></div>' in html
    assert html.count('<details class="collapsible-code" open>') == 1
    assert '<summary class="code-summary"><a href="code/collapsible.py">code/collapsible.py</a>' in html


def test_full_site_build_preserves_relative_paths_and_excludes_output_dir(tmp_path: Path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.md").write_text("# Home\n", encoding="utf-8")
    (site / "chapter").mkdir()
    (site / "chapter" / "page.md").write_text("# Page\n", encoding="utf-8")
    (site / "html").mkdir()
    (site / "html" / "stale.md").write_text("# Should not be rebuilt\n", encoding="utf-8")

    sources = discover_sources([site], recursive=True, exclude_dirs=[site / "html"])
    assert site / "html" / "stale.md" not in sources

    output = site / "html"
    jobs = build_jobs(sources, [site], output, recursive=True)
    ignored_roots, ignored_files = output_exclusions(output, sources, jobs)
    assert output.resolve() in ignored_roots
    assert all(out.resolve() in ignored_files for _src, out in jobs)

    builder = MarkdownSiteBuilder(BuildOptions(project_root=site))
    for src, out in jobs:
        builder.build_file(src, out)

    assert (output / "index.html").exists()
    assert (output / "chapter" / "page.html").exists()
    assert not (output / "html" / "stale.html").exists()


def test_watch_exclusions_ignore_output_dir_and_files(tmp_path: Path):
    source_root = tmp_path / "site"
    output_root = source_root / "html"
    source_root.mkdir()
    output_root.mkdir()
    exclusions = WatchExclusions.from_paths(roots=[output_root], files=[source_root / "single.html"])

    assert exclusions.ignores(output_root / "index.html")
    assert exclusions.ignores(output_root / "sub" / "page.html")
    assert exclusions.ignores(source_root / "single.html")
    assert not exclusions.ignores(source_root / "index.md")


def test_dry_run_with_execute_does_not_create_out_file(tmp_path: Path):
    (tmp_path / "code").mkdir()
    src = tmp_path / "code" / "hello.py"
    src.write_text("print('hello')\n", encoding="utf-8")
    note = tmp_path / "note.md"
    note.write_text("@src(code/hello.py)\n", encoding="utf-8")
    out = tmp_path / "note.html"

    options = BuildOptions(project_root=tmp_path, execute=True)
    result = MarkdownSiteBuilder(options).build_file(note, out, dry_run=True)

    assert not out.exists()
    assert not (tmp_path / "code" / "hello.out").exists()
    assert (tmp_path / "code" / "hello.out").resolve() in result.dependencies


def test_execute_creates_missing_out_file(tmp_path: Path):
    (tmp_path / "code").mkdir()
    src = tmp_path / "code" / "hello.py"
    src.write_text("print('hello from execute')\n", encoding="utf-8")
    page = tmp_path / "page.md"
    page.write_text("@src(code/hello.py)\n", encoding="utf-8")
    html_out = tmp_path / "page.html"
    out_file = tmp_path / "code" / "hello.out"

    result = MarkdownSiteBuilder(BuildOptions(project_root=tmp_path, execute=True)).build_file(page, html_out)

    assert result.written
    assert out_file.read_text(encoding="utf-8") == "hello from execute\n"
    assert out_file.resolve() in result.dependencies
    assert "hello from execute" in html_out.read_text(encoding="utf-8")


def test_default_python_execution_uses_external_python_when_frozen(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    command = _default_command(tmp_path / "hello.py")

    assert command is not None
    assert Path(command[0]).name in {"python", "python3"}


def test_source_output_path_uses_configured_suffix_consistently(tmp_path: Path):
    src = tmp_path / "code" / "hello.py"
    assert source_output_path(src, ".run") == tmp_path / "code" / "hello.run"
    assert source_output_path(src, ".out") == tmp_path / "code" / "hello.out"
    assert source_output_path(src, "-output.txt") == tmp_path / "code" / "hello.py-output.txt"


def test_watch_exclusions_ignore_generated_code_outputs_when_execute_is_enabled(tmp_path: Path):
    exclusions = WatchExclusions.from_paths(suffixes=[".out"])
    assert exclusions.ignores(tmp_path / "code" / "hello.out")
    assert not exclusions.ignores(tmp_path / "code" / "hello.py")


def test_initial_watch_build_skips_up_to_date_page(tmp_path: Path):
    page = tmp_path / "page.md"
    out = tmp_path / "html" / "page.html"
    page.write_text("# Page\n", encoding="utf-8")
    out.parent.mkdir()
    out.write_text("<h1>Page</h1>\n", encoding="utf-8")
    import os

    os.utime(page, (1000, 1000))
    os.utime(out, (2000, 2000))

    stale, skipped = _jobs_needing_build(MarkdownSiteBuilder(BuildOptions(project_root=tmp_path)), [(page, out)])

    assert stale == []
    assert skipped == 1


def test_initial_watch_build_rebuilds_when_dependency_is_newer(tmp_path: Path):
    page = tmp_path / "page.md"
    partial = tmp_path / "partial.md"
    out = tmp_path / "html" / "page.html"
    page.write_text("@include(partial.md)\n", encoding="utf-8")
    partial.write_text("new partial\n", encoding="utf-8")
    out.parent.mkdir()
    out.write_text("old html\n", encoding="utf-8")
    import os

    os.utime(page, (1000, 1000))
    os.utime(out, (2000, 2000))
    os.utime(partial, (3000, 3000))

    stale, skipped = _jobs_needing_build(MarkdownSiteBuilder(BuildOptions(project_root=tmp_path)), [(page, out)])

    assert stale == [(page, out)]
    assert skipped == 0


def test_initial_watch_build_rebuilds_when_generated_out_is_stale(tmp_path: Path):
    (tmp_path / "code").mkdir()
    src = tmp_path / "code" / "hello.py"
    out_file = tmp_path / "code" / "hello.out"
    page = tmp_path / "page.md"
    html_out = tmp_path / "html" / "page.html"
    src.write_text("print('new')\n", encoding="utf-8")
    out_file.write_text("old\n", encoding="utf-8")
    page.write_text("@src(code/hello.py)\n", encoding="utf-8")
    html_out.parent.mkdir()
    html_out.write_text("old html built after source\n", encoding="utf-8")
    import os

    os.utime(page, (1000, 1000))
    os.utime(out_file, (1500, 1500))
    os.utime(src, (2000, 2000))
    os.utime(html_out, (3000, 3000))

    stale, skipped = _jobs_needing_build(MarkdownSiteBuilder(BuildOptions(project_root=tmp_path, execute=True)), [(page, html_out)])

    assert stale == [(page, html_out)]
    assert skipped == 0


def test_local_server_url_is_clickable_loopback_url():
    assert local_server_url(8000) == "http://127.0.0.1:8000/"


def test_watch_help_describes_serving_behavior():
    actions = {option: action for action in make_parser()._actions for option in action.option_strings}
    assert actions["--watch"].help == "Start a local development server, watch inputs, and rebuild on change"
    assert actions["--serve"].help == "Alias for --watch"


def test_watch_status_message_hides_implementation_detail(tmp_path: Path):
    message = _watch_root_message([tmp_path], WatchExclusions())
    assert message == f"Watching for changes in {tmp_path}"
    assert "watchdog" not in message


def test_watch_build_messages_are_human_readable():
    assert _initial_build_message(0, 6) == "Site is already up to date (6 pages)."
    assert _initial_build_message(2, 4) == "Built 2 pages; 4 unchanged."
    assert _initial_build_message(1, 0) == "Built 1 page."
    assert _initial_build_message(6, 0) == "Built 6 pages."
    assert _rebuild_message(1) == "Regenerated 1 page."
    assert _rebuild_message(2) == "Regenerated 2 pages."
    assert _rebuild_message(0) == "Change detected, no pages needed rebuilding."


def test_http_server_reports_busy_requested_port(monkeypatch):
    calls: list[int] = []

    class Server:
        def __init__(self, address, handler):
            port = address[1]
            calls.append(port)
            raise OSError(errno.EADDRINUSE, "Address already in use")

    monkeypatch.setattr("md2html.watch._ReusableTCPServer", Server)

    try:
        _make_http_server(object(), 8000)
    except RuntimeError as exc:
        assert str(exc) == "port 8000 is already in use"
    else:
        raise AssertionError("expected busy port to fail")

    assert calls == [8000]


def test_stop_observer_suppresses_watchdog_shutdown_race():
    class Observer:
        def stop(self):
            return None

        def join(self):
            raise RuntimeError("release unlocked lock")

    _stop_observer(Observer())


def test_dependency_graph_records_src_edge_but_not_cpp_header(tmp_path: Path):
    from md2html.graph import build_dependency_graph

    page = tmp_path / "page.md"
    main_cpp = tmp_path / "main.cpp"
    header = tmp_path / "file.h"
    out = tmp_path / "page.html"
    page.write_text("@src(main.cpp)\n", encoding="utf-8")
    main_cpp.write_text('#include "file.h"\nint main(){return 0;}\n', encoding="utf-8")
    header.write_text("// deliberately not part of the md2html graph\n", encoding="utf-8")

    graph = build_dependency_graph([(page, out)], BuildOptions(project_root=tmp_path))

    assert any(edge.kind == "@src" and edge.upstream == main_cpp.resolve() and edge.downstream == page.resolve() for edge in graph.edges)
    assert not any(edge.upstream == header.resolve() for edge in graph.edges)
    assert graph.affected_jobs([main_cpp]) == [(page.resolve(), out.resolve())]
    assert graph.affected_jobs([header]) == []


def test_dependency_graph_tracks_src_output_when_out_exists(tmp_path: Path):
    from md2html.graph import build_dependency_graph

    page = tmp_path / "page.md"
    main_cpp = tmp_path / "main.cpp"
    main_out = tmp_path / "main.out"
    out = tmp_path / "page.html"
    page.write_text("@src(main.cpp)\n", encoding="utf-8")
    main_cpp.write_text("int main(){return 0;}\n", encoding="utf-8")
    main_out.write_text("cached output\n", encoding="utf-8")

    graph = build_dependency_graph([(page, out)], BuildOptions(project_root=tmp_path))

    assert any(edge.kind == "@src-output" and edge.upstream == main_out.resolve() and edge.downstream == page.resolve() for edge in graph.edges)
    assert graph.affected_jobs([main_out]) == [(page.resolve(), out.resolve())]


def test_dependency_graph_tracks_nested_include_and_src(tmp_path: Path):
    from md2html.graph import build_dependency_graph

    (tmp_path / "partials").mkdir()
    (tmp_path / "code").mkdir()
    page = tmp_path / "page.md"
    mid = tmp_path / "partials" / "mid.md"
    leaf = tmp_path / "partials" / "leaf.md"
    src = tmp_path / "code" / "snippet.py"
    out = tmp_path / "page.html"
    page.write_text("# Page\n\n@include(partials/mid.md)\n", encoding="utf-8")
    mid.write_text("@include(leaf.md)\n\n@src(../code/snippet.py)\n", encoding="utf-8")
    leaf.write_text("leaf\n", encoding="utf-8")
    src.write_text("print('hello')\n", encoding="utf-8")

    graph = build_dependency_graph([(page, out)], BuildOptions(project_root=tmp_path))

    assert graph.affected_jobs([leaf]) == [(page.resolve(), out.resolve())]
    assert graph.affected_jobs([src]) == [(page.resolve(), out.resolve())]


def test_dependency_graph_detects_include_cycles(tmp_path: Path):
    from md2html.errors import IncludeCycleError
    from md2html.graph import build_dependency_graph

    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("@include(b.md)\n", encoding="utf-8")
    b.write_text("@include(a.md)\n", encoding="utf-8")

    try:
        build_dependency_graph([(a, tmp_path / "a.html")], BuildOptions(project_root=tmp_path))
    except IncludeCycleError as exc:
        assert "include cycle detected" in str(exc)
    else:
        raise AssertionError("expected an include cycle error")


def test_execute_uses_fresh_out_file_without_rerunning(tmp_path: Path):
    import os

    (tmp_path / "code").mkdir()
    src = tmp_path / "code" / "hello.py"
    out_file = tmp_path / "code" / "hello.out"
    page = tmp_path / "page.md"
    html_out = tmp_path / "page.html"
    src.write_text("print('new output')\n", encoding="utf-8")
    out_file.write_text("cached output\n", encoding="utf-8")
    os.utime(src, (1000, 1000))
    os.utime(out_file, (2000, 2000))
    page.write_text("@src(code/hello.py)\n", encoding="utf-8")

    MarkdownSiteBuilder(BuildOptions(project_root=tmp_path, execute=True)).build_file(page, html_out)

    assert out_file.read_text(encoding="utf-8") == "cached output\n"
    assert "cached output" in html_out.read_text(encoding="utf-8")


def test_resource_lookup_finds_packaged_assets():
    from md2html.resources import package_resource_path

    assert package_resource_path("assets/base.css").exists()


def test_src_inside_include_resolves_relative_to_included_file(tmp_path: Path):
    (tmp_path / "partials").mkdir()
    (tmp_path / "code").mkdir()
    page = tmp_path / "page.md"
    partial = tmp_path / "partials" / "snippet.md"
    src = tmp_path / "code" / "snippet.py"
    out_file = tmp_path / "code" / "snippet.out"
    page.write_text("@include(partials/snippet.md)\n", encoding="utf-8")
    partial.write_text("@src(../code/snippet.py)\n", encoding="utf-8")
    src.write_text("print('hello from include')\n", encoding="utf-8")
    out_file.write_text("hello from include\n", encoding="utf-8")

    result = MarkdownSiteBuilder(BuildOptions(project_root=tmp_path)).build_file(page, tmp_path / "page.html")
    html = (tmp_path / "page.html").read_text(encoding="utf-8")

    assert not result.diagnostics
    assert "hello from include" in html
    assert "code/snippet.py" in html
