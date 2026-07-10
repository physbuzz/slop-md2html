from __future__ import annotations

import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest

from md2html2.cli import WatchGraph, _server, main, parser, settings_from_args
from md2html2.project import Project
from md2html2.render import parse_frontmatter
from md2html2.settings import MathSettings, Settings, load_settings, normal_path


def build_one(tmp_path: Path, text: str, **changes) -> str:
    source = tmp_path / "article.md"
    source.write_text(text, encoding="utf-8")
    settings = Settings.single(source)
    if changes:
        from dataclasses import replace
        settings = replace(settings, **changes)
    result = Project(settings).build()
    assert result.written == [tmp_path / "article.html"]
    return result.written[0].read_text(encoding="utf-8")


def page_cache(tmp_path: Path, relative: str = "article.html") -> Path:
    return tmp_path / ".md2html-cache" / "pages" / relative


def workspaces(page: Path) -> list[Path]:
    return sorted(path for path in page.iterdir() if path.is_dir())


def test_single_file_writes_only_sibling_html(tmp_path: Path):
    output = build_one(tmp_path, "# A useful title\n\nHello.\n")
    assert sorted(path.name for path in tmp_path.iterdir()) == ["article.html", "article.md"]
    assert "<title>article.md</title>" in output
    assert "<h1 id=\"a-useful-title\">" in output
    assert "tex-mml-chtml.js" not in output
    assert "Measure" in output and 'name="width"' in output and 'name="type"' in output
    assert "Text" in output and 'name="text"' in output
    assert output.count(":has(") == 8
    assert '<details class="reader-widget">' in output and '<form aria-label="reader controls">' in output
    assert "border-radius: 4px" in output and ".reader-widget form" in output


def test_frontmatter_title_and_yaml_types(tmp_path: Path):
    metadata, body = parse_frontmatter("---\ntitle: Named\ntags: [one, two]\n---\nBody\n")
    assert metadata == {"title": "Named", "tags": ["one", "two"]}
    assert body == "Body\n"
    output = build_one(tmp_path, "---\ntitle: Named\n---\n# Different\n")
    assert "<title>Named</title>" in output
    assert '<div class="page-title">article.md</div>' in output


def test_math_is_shielded_and_only_adds_assets_when_used(tmp_path: Path):
    output = build_one(
        tmp_path,
        "# Math\n\n$x_i$ and $$a_b^2$$\n\n\\begin{align*}x&=1\\\\y&=2\\end{align*}\n",
    )
    assert "MathJax" in output
    assert '<span class="math inline-math"' in output
    assert '<div class="math display-math"' in output
    assert "data-md2html-token" not in output
    assert "<em>" not in output


@pytest.mark.parametrize("backend, marker", [("mathml", "<math"), ("svg", "<svg")])
def test_build_time_math_backends(tmp_path: Path, backend: str, marker: str):
    output = build_one(tmp_path, "# Math\n\n$x+1$\n", math=MathSettings(backend))
    assert marker in output
    assert "tex-mml-chtml.js" not in output


def test_mathjax_chtml_is_static_and_standalone(tmp_path: Path):
    output = build_one(tmp_path, "# Math\n\n$$x^2+1$$\n", math=MathSettings("mathjax-chtml"))
    assert "<mjx-container" in output
    assert "@font-face" in output
    assert "mjx-c.mjx-c" in output
    assert "cdn.jsdelivr.net/npm/@mathjax/mathjax-tex-font" in output
    assert "data-tex=" in output and "data-latex=" not in output
    assert "tex-mml-chtml.js" not in output
    assert sorted(path.name for path in tmp_path.iterdir()) == ["article.html", "article.md"]


def test_code_and_comments_do_not_become_liquid(tmp_path: Path):
    output = build_one(
        tmp_path,
        """# Braces

```wl
f[{{x_, y_}}] := {x, y}
```

`{{ still_code }}`

<!-- Export[Mean/@{{1,2},{3,4}}] -->
""",
    )
    assert "unexpected" not in output
    assert "still_code" in output
    assert "Export[Mean/@{{1,2},{3,4}}]" in output
    assert "data-md2html-token" not in output


def test_directives_resolve_from_including_file_and_make_toc(tmp_path: Path):
    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "more.md").write_text("## Included\n\n@src(example.py, collapsed)\n", encoding="utf-8")
    (parts / "example.py").write_text("print('hello')\n", encoding="utf-8")
    output = build_one(tmp_path, "# Notes\n\n@toc\n\n@include(parts/more.md)\n")
    assert '<a href="#included">Included</a>' in output
    assert "print" in output and "hello" in output
    assert '<div class="code-box">' in output
    assert '<details class="collapsible-code">' in output
    assert '<summary class="code-summary"><a href="parts/example.py">example.py</a>' in output
    assert '<div class="codehilite"><pre>' in output
    assert 'class="source"' not in output and 'class="highlight"' not in output
    assert 'content: "►"' in output
    assert '<div class="table-of-contents">' in output


def test_toc_compacts_exercises_like_the_original_page(tmp_path: Path):
    output = build_one(
        tmp_path,
        "# Book\n\n@toc\n\n## Exercises\n\n### Exercise 1.1\n\n#### Solution\n\n### Exercise 1.2\n",
    )
    assert '<ul class="toc-list">' in output
    assert 'class="toc-exercises"' in output
    assert output.count('class="exercise-list"') == 1
    assert "Exercise 1.1</a></span>" in output and "Exercise 1.2</a></span>" in output
    assert '>Solution</a>' not in output
    assert ".table-of-contents h2" not in output


def test_adjacent_blockquotes_match_kramdown(tmp_path: Path):
    output = build_one(tmp_path, "> First note.\n\n> Second note.\n")
    assert output.count("<blockquote>") == 1
    assert output.count("<p>") == 2


def test_highlighted_code_uses_one_box(tmp_path: Path):
    output = build_one(tmp_path, "# Code\n\n```python\nprint('hello')\n```\n")
    assert '<div class="codehilite"><pre>' in output
    assert '<div class="code-box">' not in output
    assert ".codehilite .k { color: #008000; font-weight: bold }" in output
    assert 'html[data-theme="dark"] .codehilite .k' in output


def test_inline_source_uses_the_code_box_contract(tmp_path: Path):
    output = build_one(tmp_path, "@src-begin(python)\nprint('hello')\n@src-end\n")
    assert '<div class="code-box inline-source">' in output
    assert '<div class="code-header">python source</div>' in output
    assert '<div class="codehilite"><pre>' in output
    assert '<details class="source"' not in output


def test_obsidian_images_and_embedded_video_are_responsive(tmp_path: Path):
    output = build_one(tmp_path, "![[diagram one.png]]\n")
    assert '<img class="obsidian-image" src="diagram one.png" alt="diagram one">' in output
    assert ".obsidian-image{display:block;margin:1rem auto}" in output
    video = build_one(tmp_path, '<iframe src="https://www.youtube.com/embed/example"></iframe>\n')
    assert 'iframe[src*="youtube.com"]' in video
    assert "aspect-ratio:16/9" in video.replace(" ", "")


def test_page_dependencies_follow_includes_templates_and_css_but_not_source_internals(tmp_path: Path):
    templates = tmp_path / "templates"
    parts = tmp_path / "parts"
    css = templates / "css"
    templates.mkdir()
    parts.mkdir()
    css.mkdir()
    (templates / "page.html").write_text("{% include 'outer.html' %}{{ content }}", encoding="utf-8")
    (templates / "outer.html").write_text("{% include 'inner.html' %}", encoding="utf-8")
    (templates / "inner.html").write_text("template", encoding="utf-8")
    (templates / "page.css").write_text("@import 'css/one.css';", encoding="utf-8")
    (css / "one.css").write_text("@import 'two.css';", encoding="utf-8")
    (css / "two.css").write_text("body { color: black; }", encoding="utf-8")
    (parts / "one.md").write_text("@include(two.md)\n", encoding="utf-8")
    (parts / "two.md").write_text("included\n", encoding="utf-8")
    (tmp_path / "file.cpp").write_text('#include "header.h"\n', encoding="utf-8")
    (tmp_path / "header.h").write_text("// deliberately not followed\n", encoding="utf-8")
    source = tmp_path / "article.md"
    source.write_text("@include(parts/one.md)\n\n@src(file.cpp)\n", encoding="utf-8")
    settings = Settings.single(source).with_cli(templates=templates)
    result = Project(settings).build()
    dependencies = result.page_dependencies[source]
    expected = {source, parts / "one.md", parts / "two.md", tmp_path / "file.cpp",
                templates / "page.html", templates / "outer.html", templates / "inner.html",
                templates / "page.css", css / "one.css", css / "two.css"}
    assert expected <= dependencies
    assert tmp_path / "header.h" not in dependencies


def test_watch_graph_replaces_stale_page_edges_after_partial_build(tmp_path: Path):
    source = tmp_path / "content"
    output = tmp_path / "public"
    source.mkdir()
    shared = source / "_shared.md"
    shared.write_text("shared\n", encoding="utf-8")
    first = source / "first.md"
    second = source / "second.md"
    first.write_text("@include(_shared.md)\n", encoding="utf-8")
    second.write_text("@include(_shared.md)\n", encoding="utf-8")
    settings = Settings(input=source, output=output, project_root=tmp_path, recursive=True)
    graph = WatchGraph()
    graph.update(Project(settings).build().page_dependencies, reset=True)
    assert graph.affected({shared}) == {first, second}

    first.write_text("independent\n", encoding="utf-8")
    partial = Project(settings).build({first})
    assert partial.written == [output / "first.html"]
    graph.update(partial.page_dependencies)
    assert graph.affected({shared}) == {second}
    second.write_text("also independent\n", encoding="utf-8")
    graph.update(Project(settings).build({second}).page_dependencies)
    assert shared in graph.seen
    assert not graph.affected({shared})


def test_include_cycle_warns_without_aborting(tmp_path: Path):
    (tmp_path / "a.md").write_text("@include(b.md)\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("@include(a.md)\n", encoding="utf-8")
    source = tmp_path / "a.md"
    result = Project(Settings.single(source)).build()
    assert any("include cycle" in warning for warning in result.warnings)
    assert "Include cycle omitted" in result.written[0].read_text(encoding="utf-8")


def test_liquid_include_cycle_warns_without_aborting(tmp_path: Path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "page.html").write_text("{% include 'loop.html' %}{{ content }}", encoding="utf-8")
    (templates / "loop.html").write_text("{% include 'loop.html' %}", encoding="utf-8")
    source = tmp_path / "article.md"
    source.write_text("# Still built\n", encoding="utf-8")
    result = Project(Settings.single(source).with_cli(templates=templates)).build()
    assert any("recursive include" in warning for warning in result.warnings)
    assert "Template cycle or error" in result.written[0].read_text(encoding="utf-8")


def test_executable_inline_content_uses_a_persistent_workspace(tmp_path: Path):
    output = build_one(
        tmp_path,
        "# Run\n\n@src-begin(python, execute, expanded)\nprint(6 * 7)\n@src-end\n",
        execute=True,
    )
    assert "code-output" in output and "42" in output
    cached = workspaces(page_cache(tmp_path))
    assert len(cached) == 1
    assert (cached[0] / "output.txt").read_text() == "42\n"
    assert (cached[0] / ".complete").is_file()
    assert list(cached[0].glob("*.py"))


def test_committed_cache_is_portable_and_used_without_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    first = tmp_path / "first-checkout"
    second = tmp_path / "github-checkout"
    first.mkdir()
    monkeypatch.chdir(first)
    Path("article.md").write_text(
        "# Cached\n\n@src-begin(python, execute)\nprint('portable output')\n@src-end\n", encoding="utf-8",
    )
    settings = Settings.single(Path("article.md")).with_cli(execute=True)
    Project(settings).build()
    first_workspace = workspaces(page_cache(Path(".")))[0].name
    cache_text = "".join(path.read_text(encoding="utf-8") for path in Path(".md2html-cache").rglob("*") if path.is_file())
    assert str(first) not in cache_text and "execution.json" not in cache_text
    shutil.copytree(first, second)

    monkeypatch.chdir(second)
    assert main(["article.md"]) == 0
    assert "portable output" in Path("article.html").read_text(encoding="utf-8")
    restored = Settings.single(Path("article.md")).with_cli(
        force=True, commands={"python": "exit 99"}, site_data={"unrelated": "change"},
    )
    result = Project(restored).build()
    output = Path("article.html").read_text(encoding="utf-8")
    assert "portable output" in output
    assert not result.warnings
    assert workspaces(page_cache(Path(".")))[0].name == first_workspace
    assert restored.input == Path("article.md") and restored.project_root == Path(".")


def test_only_source_content_invalidates_cached_output(tmp_path: Path):
    source = tmp_path / "article.md"
    source.write_text(
        "@src-begin(python, execute)\nprint('old output')\n@src-end\n", encoding="utf-8",
    )
    Project(Settings.single(source).with_cli(execute=True)).build()
    source.write_text(
        "@src-begin(python, execute)\nprint('new output')\n@src-end\n", encoding="utf-8",
    )
    result = Project(Settings.single(source)).build()
    output = result.written[0].read_text(encoding="utf-8")
    assert '<div class="code-output">' not in output
    assert any("no cached output" in warning for warning in result.warnings)


def test_strict_legacy_cache_is_migrated_without_execution(tmp_path: Path):
    code = "print('legacy output')\n"
    source = tmp_path / "article.md"
    source.write_text(f"@src-begin(python, execute)\n{code}@src-end\n", encoding="utf-8")
    legacy = page_cache(tmp_path) / "python-1-machine-specific-hash"
    legacy.mkdir(parents=True)
    (legacy / "output.txt").write_text("legacy output\n", encoding="utf-8")
    (legacy / "execution.json").write_text(json.dumps({"code": code, "source": "/old/checkout/article.md"}))
    result = Project(Settings.single(source)).build()
    output = result.written[0].read_text(encoding="utf-8")
    migrated = workspaces(page_cache(tmp_path))[0]
    assert "legacy output" in output and not result.warnings
    assert migrated != legacy and (migrated / ".complete").is_file()


def test_cached_output_survives_page_output_move(tmp_path: Path):
    source = tmp_path / "article.md"
    source.write_text(
        "@src-begin(python, execute)\nprint('moved page output')\n@src-end\n", encoding="utf-8",
    )
    Project(Settings.single(source, tmp_path / "old.html").with_cli(execute=True)).build()
    result = Project(Settings.single(source, tmp_path / "new.html")).build()
    assert "moved page output" in result.written[0].read_text(encoding="utf-8")
    assert not result.warnings
    assert workspaces(page_cache(tmp_path, "new.html"))[0].name == workspaces(page_cache(tmp_path, "old.html"))[0].name


def test_file_execution_runs_in_a_stable_clean_workspace(tmp_path: Path):
    source = tmp_path / "program.py"
    source.write_text(
        "from pathlib import Path\nPath('old-image.txt').write_text('old')\nprint(Path.cwd().name)\n",
        encoding="utf-8",
    )
    output = build_one(tmp_path, "# Run\n\n@src(program.py, execute)\n", execute=True)
    cached = workspaces(page_cache(tmp_path))
    assert len(cached) == 1
    workspace = cached[0]
    assert workspace.name in output
    assert (workspace / "old-image.txt").read_text() == "old"
    assert not (tmp_path / "old-image.txt").exists()

    (workspace / "cache-hit.txt").write_text("preserved", encoding="utf-8")
    build_one(tmp_path, "# Run\n\n@src(program.py, execute)\n", execute=True)
    assert (workspace / "cache-hit.txt").read_text() == "preserved"

    source.write_text(
        "from pathlib import Path\nPath('new-image.txt').write_text('new')\nprint('changed')\n",
        encoding="utf-8",
    )
    output = build_one(tmp_path, "# Run\n\n@src(program.py, execute)\n", execute=True)
    changed = workspaces(page_cache(tmp_path))
    assert len(changed) == 1 and changed[0] != workspace
    assert "changed" in output
    assert not workspace.exists()
    assert (changed[0] / "new-image.txt").read_text() == "new"


def test_custom_command_can_write_output_and_inspect_workspace(tmp_path: Path):
    (tmp_path / "example.demo").write_text("ignored\n", encoding="utf-8")
    command = "printf '%s' {slug} > {output}; printf '%s' {builddir} > workspace.txt; printf '%s' {sourcedir} > sourcedir.txt"
    output = build_one(
        tmp_path, "# Run\n\n@src(example.demo, execute)\n", execute=True,
        commands={"demo": command},
    )
    workspace = workspaces(page_cache(tmp_path))[0]
    assert "example" in output
    assert (workspace / "output.txt").read_text() == "example"
    assert (workspace / "workspace.txt").read_text() == "."
    assert normal_path(workspace / (workspace / "sourcedir.txt").read_text()) == tmp_path
    assert not (tmp_path / "example.out").exists()


def test_force_refreshes_cached_output_when_execution_is_enabled(tmp_path: Path):
    (tmp_path / "example.demo").write_text("source\n", encoding="utf-8")
    page = "@src(example.demo, execute)\n"
    build_one(tmp_path, page, execute=True, commands={"demo": "printf old > {output}"})
    output = build_one(
        tmp_path, page, execute=True, force=True, commands={"demo": "printf new > {output}"},
    )
    assert '<div class="code-output">\n<span>Output:</span>\n<pre>new</pre>' in output


@pytest.mark.skipif(shutil.which("c++") is None, reason="c++ is required")
def test_cpp_build_products_stay_in_workspace(tmp_path: Path):
    (tmp_path / "message.h").write_text('#define MESSAGE "cpp output\\n"\n', encoding="utf-8")
    (tmp_path / "a.cpp").write_text(
        '#include <iostream>\n#include "message.h"\nint main() { std::cout << MESSAGE; }\n', encoding="utf-8",
    )
    output = build_one(tmp_path, "# Run\n\n@src(a.cpp, execute)\n", execute=True)
    workspace = workspaces(page_cache(tmp_path))[0]
    assert "cpp output" in output
    assert (workspace / "a.md2html-out").is_file()
    assert not (tmp_path / "a.out").exists()
    assert not (tmp_path / "a.bin").exists()


def test_page_rebuild_prunes_removed_inline_workspace(tmp_path: Path):
    build_one(
        tmp_path,
        "# Run\n\n@src-begin(python, execute)\nprint('one')\n@src-end\n\n"
        "@src-begin(python, execute)\nprint('two')\n@src-end\n",
        execute=True,
    )
    cache = page_cache(tmp_path)
    original = workspaces(cache)
    assert len(original) == 2

    build_one(
        tmp_path, "# Run\n\n@src-begin(python, execute)\nprint('one')\n@src-end\n", execute=True,
    )
    remaining = workspaces(cache)
    assert len(remaining) == 1
    assert remaining[0] == original[0]
    assert not original[1].exists()


def test_failed_execution_still_allows_website_shaped_cache_cleanup(tmp_path: Path):
    source = tmp_path / "content"
    output = tmp_path / "public"
    for section in ("guide", "reference"):
        directory = source / section
        directory.mkdir(parents=True)
        (directory / "index.md").write_text(
            "# Failure\n\n@src-begin(fail, execute)\nnot valid\n@src-end\n", encoding="utf-8",
        )
    settings = Settings(
        input=source, output=output, output_mode="site", project_root=tmp_path,
        recursive=True, execute=True,
        commands={"fail": "printf 'kept for inspection' > failed.txt; printf 'intentional failure' >&2; exit 1"},
    )
    result = Project(settings).build()
    assert len(result.warnings) == 2
    guide = page_cache(tmp_path, "guide/index.html")
    reference = page_cache(tmp_path, "reference/index.html")
    assert (workspaces(guide)[0] / "failed.txt").is_file()
    assert (workspaces(reference)[0] / "failed.txt").is_file()

    (source / "reference" / "index.md").unlink()
    result = Project(settings).build()
    assert any("intentional failure" in warning for warning in result.warnings)
    assert guide.is_dir()
    assert not reference.exists()


def test_unterminated_source_block_preserves_page_cache(tmp_path: Path):
    source = tmp_path / "article.md"
    build_one(
        tmp_path, "# Run\n\n@src-begin(python, execute)\nprint('valid')\n@src-end\n", execute=True,
    )
    cache = page_cache(tmp_path)
    cached = workspaces(cache)
    source.write_text("# Run\n\n@src-begin(python, execute)\nprint('unfinished')\n", encoding="utf-8")
    settings = Settings.single(source).with_cli(execute=True)
    with pytest.raises(ValueError, match="missing @src-end"):
        Project(settings).build()
    assert workspaces(cache) == cached


def test_malformed_src_tag_is_a_visible_error_and_preserves_cache(tmp_path: Path):
    (tmp_path / "program.py").write_text("print('valid')\n", encoding="utf-8")
    build_one(tmp_path, "# Run\n\n@src(program.py, execute)\n", execute=True)
    cache = page_cache(tmp_path)
    cached = workspaces(cache)
    source = tmp_path / "article.md"
    source.write_text("# Run\n\n@src(program.py, execute\n", encoding="utf-8")
    result = Project(Settings.single(source).with_cli(execute=True)).build()
    output = result.written[0].read_text(encoding="utf-8")
    assert 'style="color:red;font-weight:bold;font-size:20px;"' in output
    assert "error at" in output and "malformed @src tag" in output
    assert any("article.md:3" in warning for warning in result.warnings)
    assert workspaces(cache) == cached


def site_fixture(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "site"
    output = tmp_path / "public"
    (source / "_posts").mkdir(parents=True)
    (source / "_layouts").mkdir()
    (source / "_includes").mkdir()
    (source / "assets").mkdir()
    (source / "_config.yml").write_text(
        "title: Native site\nurl: https://example.test\npermalink: /:year/:month/:day/:title.html\n",
        encoding="utf-8",
    )
    (source / "_includes" / "head.html").write_text(
        '<title>{{ page.title }} | {{ site.title }}</title><script>document.documentElement.setAttribute("data-hash-pending", "")</script><script defer src="/site.js"></script>',
        encoding="utf-8",
    )
    (source / "site.js").write_text("// reader controls\n", encoding="utf-8")
    (source / "_layouts" / "default.html").write_text(
        "<!doctype html><html><head>{% include head.html %}</head><body>{{ content }}</body></html>", encoding="utf-8"
    )
    (source / "_layouts" / "post.html").write_text(
        "---\nlayout: default\n---\n<article><h1>{{ page.title }}</h1>{{ content }}</article>", encoding="utf-8"
    )
    (source / "_posts" / "2026-05-18-gaussianintegral.md").write_text(
        "---\nlayout: post\ntitle: Gaussian Integral\ntags: [math]\n---\nBody $x^2$.\n", encoding="utf-8"
    )
    (source / "_posts" / "_2026-05-17-private.md").write_text("---\nlayout: post\ntitle: Private\n---\nHidden.\n")
    (source / "index.html").write_text(
        "---\nlayout: default\ntitle: Home\n---\n{% for post in site.posts %}<a href=\"{{ post.url | relative_url }}\">{{ post.title }}</a>{% endfor %}", encoding="utf-8"
    )
    (source / "assets" / "plain.txt").write_text("asset", encoding="utf-8")
    return source, output


def test_native_site_model_layouts_includes_assets_and_dated_urls(tmp_path: Path):
    source, output = site_fixture(tmp_path)
    settings = Settings(input=source, output=output, output_mode="site", project_root=source, recursive=True)
    result = Project(settings).build()
    post = output / "2026/05/18/gaussianintegral.html"
    assert post in result.written
    assert not (output / "gaussianintegral/index.html").exists()
    assert not (output / "_posts/_2026-05-17-private.html").exists()
    post_text = post.read_text(encoding="utf-8")
    assert "<title>Gaussian Integral | Native site</title>" in post_text
    assert "<article><h1>Gaussian Integral</h1>" in post_text
    assert (output / "assets/plain.txt").read_text() == "asset"
    index = (output / "index.html").read_text()
    assert 'href="/2026/05/18/gaussianintegral.html"' in index
    assert "Private" not in index
    assert not result.warnings


def test_native_site_deduplicates_mathjax_styles(tmp_path: Path):
    source, output = site_fixture(tmp_path)
    settings = Settings(
        input=source, output=output, output_mode="site", project_root=source,
        recursive=True, math=MathSettings("mathjax-chtml"),
    )
    Project(settings).build()
    post = (output / "2026/05/18/gaussianintegral.html").read_text()
    stylesheet = output / "assets/md2html/mathjax-chtml.css"
    css = stylesheet.read_text()
    assert stylesheet.is_file() and "@font-face" in css
    assert "mjx-c.mjx-c" in css
    assert "cdn.jsdelivr.net" not in css
    assert 'url("mathjax/woff2/mjx-tex-n.woff2")' in css
    assert (output / "assets/md2html/mathjax/woff2/mjx-tex-n.woff2").is_file()
    assert (output / "assets/md2html/mathjax/woff2/mjx-tex-zero.woff2").is_file()
    assert '<link rel="stylesheet" href="/assets/md2html/mathjax-chtml.css">' in post
    assert 'rel="preload" href="/assets/md2html/mathjax/woff2/mjx-tex-n.woff2"' in post
    assert post.index("data-hash-pending") < post.index("mathjax-chtml.css") < post.index('src="/site.js"')
    assert "<mjx-container" in post
    assert "MJX-CHTML-styles" not in post


@pytest.mark.parametrize("mode, marker", [("remote", "cdn.jsdelivr.net"), ("inline", "data:font/woff2;base64,"), ("none", None)])
def test_native_site_chtml_font_modes(tmp_path: Path, mode: str, marker: str | None):
    source, output = site_fixture(tmp_path)
    settings = Settings(
        input=source, output=output, output_mode="site", project_root=source,
        recursive=True, math=MathSettings("mathjax-chtml", mode),
    )
    Project(settings).build()
    css = (output / "assets/md2html/mathjax-chtml.css").read_text()
    post = (output / "2026/05/18/gaussianintegral.html").read_text()
    if marker:
        assert marker in css
    else:
        assert "@font-face" not in css
    assert not (output / "assets/md2html/mathjax/woff2").exists()
    assert 'rel="preload"' not in post


def test_native_site_all_font_mode_copies_without_preloading_every_font(tmp_path: Path):
    source, output = site_fixture(tmp_path)
    settings = Settings(
        input=source, output=output, output_mode="site", project_root=source,
        recursive=True, math=MathSettings("mathjax-chtml", "all"),
    )
    Project(settings).build()
    fonts = list((output / "assets/md2html/mathjax/woff2").glob("*.woff2"))
    post = (output / "2026/05/18/gaussianintegral.html").read_text()
    assert len(fonts) == 22
    assert post.count('rel="preload"') < len(fonts)


def test_config_paths_are_relative_to_config(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    config = root / "md2html.json"
    config.write_text('{"input":"content","output":"public","output_mode":"site","math":{"backend":"mathml","chtml_fonts":"inline"}}')
    settings = load_settings(config)
    assert settings.input == root / "content"
    assert settings.output == root / "public"
    assert settings.math.backend == "mathml"
    assert settings.math.chtml_fonts == "inline"


def test_relative_config_keeps_relative_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    Path("md2html.json").write_text('{"input":"content","output":"public","templates":"templates"}')
    settings = load_settings(Path("md2html.json"))
    assert settings.project_root == Path(".")
    assert settings.input == Path("content")
    assert settings.output == Path("public")
    assert settings.templates == Path("templates")


def test_template_directory_and_companion_css_take_priority(tmp_path: Path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "page.html").write_text("<title>{{ page.title }}</title><style>{{ md2html.css }}</style>{{ content }}")
    (templates / "page.css").write_text("body{color:rebeccapurple}")
    output = build_one(tmp_path, "# Custom\n", templates=templates)
    assert "rebeccapurple" in output
    assert "reader-controls" not in output


def test_cli_short_flags_and_scaffolds(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    source = Path("one.md")
    source.write_text("# One\n")
    args = parser().parse_args(["-erf", str(source)])
    settings = settings_from_args(args)
    assert settings.execute and settings.recursive and settings.force
    assert settings.input == source and settings.output == Path("one.html")
    assert main(["--example-config"]) == 0
    assert (tmp_path / "md2html.config").is_file()
    assert main(["--example-config"]) == 2
    assert main(["--example-config", "--force"]) == 0
    assert main(["--example-json"]) == 0
    assert (tmp_path / "md2html.json").read_text().startswith("{")
    assert main(["--example-template", "-"]) == 0
    assert "<!doctype html>" in capsys.readouterr().out.lower()
    assert main(["--example-css"]) == 0
    example_css = (tmp_path / "templates/page.css").read_text()
    assert ".reader-widget form" in example_css
    assert ".table-of-contents" in example_css
    assert ".code-box .codehilite" in example_css
    assert ".code-output pre" in example_css
    assert ".codehilite .kc { color: #008000; font-weight: bold }" in example_css


def test_help_and_readme_explain_watch_serve_and_examples(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit):
        parser().parse_args(["--help"])
    help_text = capsys.readouterr().out
    assert "rebuild when source files change" in help_text
    assert "md2html -erf notes -o html" in help_text
    assert main(["--readme"]) == 0
    readme = capsys.readouterr().out
    assert "@src-begin" in readme
    assert "2026/05/18/gaussianintegral.html" in readme


def test_preview_server_serves_selected_root(tmp_path: Path):
    (tmp_path / "index.html").write_text("ok")
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    server, thread = _server(tmp_path, port)
    try:
        assert thread.is_alive()
        with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
            client.sendall(b"GET / HTTP/1.0\r\nHost: localhost\r\n\r\n")
            response = client.recv(4096)
        assert b"200 OK" in response
    finally:
        server.shutdown()
        server.server_close()


def test_serve_rebuilds_a_standalone_page(tmp_path: Path):
    source = tmp_path / "live.md"
    included = tmp_path / "_included.md"
    included.write_text("Before include\n")
    source.write_text("# Live\n\n@include(_included.md)\n")
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    process = subprocess.Popen(
        [sys.executable, "-m", "md2html2", str(source), "--serve", "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )

    def page_contains(value: str) -> bool:
        try:
            with urlopen(f"http://127.0.0.1:{port}/live.html", timeout=.3) as response:
                return value in response.read().decode()
        except OSError:
            return False

    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not page_contains("Before include"):
            time.sleep(.05)
        assert page_contains("Before include")
        included.write_text("After include\n")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not page_contains("After include"):
            time.sleep(.05)
        assert page_contains("After include")

        source.write_text("# Independent\n")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not page_contains("Independent"):
            time.sleep(.05)
        assert page_contains("Independent")
        time.sleep(.25)
        modified = source.with_suffix(".html").stat().st_mtime_ns
        included.write_text("Stale include\n")
        time.sleep(.5)
        assert source.with_suffix(".html").stat().st_mtime_ns == modified
    finally:
        process.terminate()
        process.wait(timeout=3)
