from __future__ import annotations

import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest

from md2html2.cli import WatchGraph, _server, main, parser, settings_from_args, settings_list_from_args
from md2html2.project import CHTML_CDN, MATHJAX_CDN, Project
from md2html2.render import parse_frontmatter
from md2html2.settings import ImageSettings, MathSettings, Settings, find_config, load_settings, normal_path


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


def page_cache(tmp_path: Path, relative: str = "article.md") -> Path:
    source = tmp_path / relative
    return source.parent / ".md2html-cache" / source.stem


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
    assert "border-radius:4px" in output and ".reader-widget form" in output
    assert "--reader-text-size:.9rem" in output
    assert 'html[data-text="small"]{--reader-text-size:.8rem}' in output
    assert 'html[data-text="large"]{--reader-text-size:1rem}' in output


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
    assert '<span class="math inline-math' in output
    assert '<div class="math display-math' in output
    assert "data-md2html-token" not in output
    assert "<em>" not in output
    assert ".math-copy-source{position:absolute" in output


@pytest.mark.parametrize("backend, marker", [("mathml", "<math"), ("svg", "<svg")])
def test_build_time_math_backends(tmp_path: Path, backend: str, marker: str):
    output = build_one(tmp_path, "# Math\n\n$x+1$\n", math=MathSettings(backend))
    assert marker in output
    assert '<span class="math-copy-source">$x+1$</span>' in output
    assert "math-rendered" in output and 'aria-hidden="true"' in output
    assert "data-md2html-math-copy" in output
    assert output.index("</article>") < output.index("data-md2html-math-copy")
    assert "tex-mml-chtml.js" not in output
    if backend == "svg":
        assert "--md2html-math-svg-inline-align:" in output and 'fill="currentColor"' in output
    else:
        assert "md2html-mathml" in output and "display:inline-block" in output and "vertical-align:baseline" in output


def test_mathjax_chtml_is_static_and_standalone(tmp_path: Path):
    output = build_one(tmp_path, "# Math\n\n$$x^2+1$$\n", math=MathSettings("mathjax-chtml"))
    assert "<mjx-container" in output
    assert "@font-face" in output
    assert "mjx-c.mjx-c" in output
    assert "data:font/woff2;base64," in output
    assert "cdn.jsdelivr.net/npm/@mathjax/mathjax-tex-font" not in output
    assert "data-tex=" not in output and "data-latex=" not in output
    assert '<span class="math-copy-source">$$x^2+1$$</span>' in output
    assert "tex-mml-chtml.js" not in output
    assert sorted(path.name for path in tmp_path.iterdir()) == ["article.html", "article.md"]


@pytest.mark.parametrize("backend, expected, absent", [
    ("mathjax", "mathjax@4.1.3/tex-mml-chtml.js", "<mjx-container"),
    ("raw", "$x+1$", "tex-mml-chtml.js"),
])
def test_browser_and_raw_math_backends(tmp_path: Path, backend: str, expected: str, absent: str):
    output = build_one(tmp_path, "$x+1$\n", math=MathSettings(backend))
    assert expected in output and absent not in output
    if backend == "mathjax":
        assert '.math.display-math.math-mathjax mjx-container[display="true"]{margin:0}' in output


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
    assert 'content:"►"' in output
    assert '<div class="table-of-contents">' in output


def test_toc_compacts_exercise_sections(tmp_path: Path):
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


def test_adjacent_blockquotes_follow_markdown_renderer_output(tmp_path: Path):
    output = build_one(tmp_path, "> First note.\n\n> Second note.\n")
    assert output.count("<blockquote>") == 2
    assert output.count("<p>") == 2


def test_highlighted_code_uses_one_box(tmp_path: Path):
    output = build_one(tmp_path, "# Code\n\n```python\nprint('hello')\n```\n")
    assert '<div class="codehilite"><pre>' in output
    assert '<div class="code-box">' not in output
    assert ".codehilite .k{color:#008000;font-weight:bold}" in output
    assert 'html[data-theme="dark"] .codehilite .k' in output


def test_inline_source_uses_the_code_box_contract(tmp_path: Path):
    output = build_one(tmp_path, "@src-begin(python)\nprint('hello')\n@src-end\n")
    assert '<div class="code-box inline-source">' in output
    assert '<div class="code-header">python source</div>' in output
    assert '<div class="codehilite"><pre>' in output
    assert '<details class="source"' not in output


def test_obsidian_images_and_embedded_video_are_responsive(tmp_path: Path):
    (tmp_path / "diagram one.png").write_bytes(b"image")
    output = build_one(tmp_path, "![[diagram one.png|width=70%|alt=A diagram|class=centered]]\n")
    assert '<img class="obsidian-image centered" src="data:image/png;base64,' in output
    assert 'alt="A diagram" style="width:70%">' in output
    numeric = build_one(tmp_path, "![[diagram one.png|320]]\n")
    assert 'alt="diagram one" style="width:320px"' in numeric
    assert ".obsidian-image{display:block;max-width:100%;height:auto;margin:1rem auto}" in output
    video = build_one(tmp_path, '<iframe src="https://www.youtube.com/embed/example"></iframe>\n')
    assert 'iframe[src*="youtube.com"]' in video
    assert "aspect-ratio:16/9" in video.replace(" ", "")


def test_obsidian_images_use_configured_defaults_with_local_overrides(tmp_path: Path):
    (tmp_path / "diagram.png").write_bytes(b"image")
    defaults = ImageSettings(class_name="centered shadow", width="45%")
    output = build_one(tmp_path, "![[diagram.png]]\n", images=defaults)
    assert 'class="obsidian-image centered shadow"' in output and 'style="width:45%"' in output
    output = build_one(tmp_path, "![[diagram.png|width=20em|class=wide]]\n", images=defaults)
    assert 'class="obsidian-image centered shadow wide"' in output and 'style="width:20em"' in output


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
    settings = Settings.single(source).with_cli(templates=(templates,))
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
    result = Project(Settings.single(source).with_cli(templates=(templates,))).build()
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
    assert cached[0].name.startswith("python-inline-")
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
    assert str(first) not in cache_text
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
        "@src-begin(python, execute)\nprint('cached output')\n@src-end\n", encoding="utf-8",
    )
    Project(Settings.single(source).with_cli(execute=True)).build()
    source.write_text(
        "@src-begin(python, execute)\nprint('new output')\n@src-end\n", encoding="utf-8",
    )
    result = Project(Settings.single(source)).build()
    output = result.written[0].read_text(encoding="utf-8")
    assert '<div class="code-output">' not in output
    assert any("no cached output" in warning for warning in result.warnings)


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
    assert workspace.name.startswith("py-program-")
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


def test_execution_disabled_preserves_unused_workspaces(tmp_path: Path):
    first = "@src-begin(python, execute)\nprint('one')\n@src-end\n"
    second = "@src-begin(python, execute)\nprint('two')\n@src-end\n"
    build_one(tmp_path, first + "\n" + second, execute=True)
    cache = page_cache(tmp_path)
    original = workspaces(cache)
    timestamps = {path.relative_to(cache): path.stat().st_mtime_ns for path in cache.rglob("*")}

    output = build_one(tmp_path, first)

    assert "one" in output
    assert workspaces(cache) == original
    assert {path.relative_to(cache): path.stat().st_mtime_ns for path in cache.rglob("*")} == timestamps


def test_failed_execution_still_prunes_stale_workspaces_for_that_page(tmp_path: Path):
    command = "printf 'kept for inspection' > failed.txt; printf 'intentional failure' >&2; exit 1"
    build_one(
        tmp_path, "@src-begin(fail, execute)\nfirst\n@src-end\n",
        execute=True, commands={"fail": command},
    )
    cache = page_cache(tmp_path)
    original = workspaces(cache)

    build_one(
        tmp_path, "@src-begin(fail, execute)\nsecond\n@src-end\n",
        execute=True, commands={"fail": command},
    )

    remaining = workspaces(cache)
    assert len(remaining) == 1 and remaining != original
    assert not original[0].exists()
    assert (remaining[0] / "failed.txt").is_file()


def test_source_directory_owns_each_page_cache(tmp_path: Path):
    source = tmp_path / "a"
    output = tmp_path / "public"
    source.mkdir()
    (source / "mysource.py").write_text("print('shared output')\n", encoding="utf-8")
    for name in ("index1.md", "index2.md"):
        (source / name).write_text("@src(mysource.py, execute)\n", encoding="utf-8")
    settings = Settings(
        input=source, output=output, project_root=tmp_path, recursive=True, execute=True,
    )

    Project(settings).build()

    for name in ("index1", "index2"):
        cached = workspaces(source / ".md2html-cache" / name)
        assert len(cached) == 1
        assert cached[0].name.startswith("py-mysource-")
        assert (cached[0] / "output.txt").read_text() == "shared output\n"
    assert not (tmp_path / ".md2html-cache").exists()


def test_deleted_page_cache_waits_for_explicit_cleanup(tmp_path: Path):
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
    guide = page_cache(source, "guide/index.md")
    reference = page_cache(source, "reference/index.md")
    assert (workspaces(guide)[0] / "failed.txt").is_file()
    assert (workspaces(reference)[0] / "failed.txt").is_file()

    (source / "reference" / "index.md").unlink()
    result = Project(settings).build()
    assert any("intentional failure" in warning for warning in result.warnings)
    assert guide.is_dir()
    assert reference.is_dir()


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
    (source / "_includes" / "head.html").write_text(
        '<title>{{ page.title }} | {{ site.title }}</title>'
        '<script>document.documentElement.setAttribute("data-hash-pending", "")</script>'
        '{% for font in md2html.font_preloads %}<link rel="preload" href="{{ font }}" as="font" type="font/woff2" crossorigin>{% endfor %}'
        '{% for stylesheet in md2html.page_stylesheets %}<link rel="stylesheet" href="{{ stylesheet }}">{% endfor %}'
        '{% if md2html.css %}<style>{{ md2html.css }}</style>{% endif %}'
        '{% for stylesheet in md2html.math_stylesheets %}<link rel="stylesheet" href="{{ stylesheet }}">{% endfor %}'
        '{% if md2html.math_css %}<style>{{ md2html.math_css }}</style>{% endif %}'
        '{% for stylesheet in md2html.stylesheets %}<link rel="stylesheet" href="{{ stylesheet }}">{% endfor %}'
        '{% if md2html.mathjax_src %}<script>{{ md2html.mathjax_config }}</script><script defer src="{{ md2html.mathjax_src }}"></script>{% endif %}'
        '<script defer src="/site.js"></script>',
        encoding="utf-8",
    )
    (source / "site.js").write_text("// reader controls\n", encoding="utf-8")
    (source / "_layouts" / "default.html").write_text(
        "<!doctype html><html><head>{% include head.html %}</head><body>{% if md2html.jekyll_compatibility %}md2html compatibility{% endif %}{{ content }}{% if md2html.has_math_copy %}{% include 'math-copy.html' %}{% endif %}</body></html>", encoding="utf-8"
    )
    (source / "_layouts" / "post.html").write_text(
        "---\nlayout: default\n---\n<article><h1>{{ page.title }}</h1>{{ content }}</article>", encoding="utf-8"
    )
    (source / "_posts" / "2026-05-18-gaussianintegral.md").write_text(
        "---\nlayout: post\ntitle: Gaussian Integral\ntags: [math]\n---\nBody $x^2$.\n", encoding="utf-8"
    )
    (source / "_posts" / "2026-05-19-liquid.html").write_text(
        "---\nlayout: post\ntitle: Liquid Post\n---\n{{ site.title }} @toc", encoding="utf-8",
    )
    (source / "_posts" / "_2026-05-17-private.md").write_text("---\nlayout: post\ntitle: Private\n---\nHidden.\n")
    (source / "index.html").write_text(
        "---\nlayout: default\ntitle: Home\n---\n{% for post in site.posts %}<a href=\"{{ post.url | relative_url }}\">{{ post.title }}</a>{% endfor %}", encoding="utf-8"
    )
    (source / "assets" / "plain.txt").write_text("asset", encoding="utf-8")
    return source, output


def site_settings(source: Path, output: Path, **changes) -> Settings:
    settings = Settings(
        input=source, output=output, output_mode="site", project_root=source, recursive=True,
        site_data={
            "title": "Native site",
            "url": "https://example.test",
            "permalink": "/:year/:month/:day/:title.html",
        },
    )
    from dataclasses import replace
    return replace(settings, **changes)


def test_native_site_model_layouts_includes_assets_and_dated_urls(tmp_path: Path):
    source, output = site_fixture(tmp_path)
    settings = site_settings(source, output)
    result = Project(settings).build()
    post = output / "2026/05/18/gaussianintegral.html"
    assert post in result.written
    assert "Native site @toc" in (output / "2026/05/19/liquid.html").read_text()
    assert not (output / "gaussianintegral/index.html").exists()
    assert not (output / "_posts/_2026-05-17-private.html").exists()
    post_text = post.read_text(encoding="utf-8")
    assert "<title>Gaussian Integral | Native site</title>" in post_text
    assert "<article><h1>Gaussian Integral</h1>" in post_text
    assert "md2html compatibility" not in post_text
    assert (output / "assets/plain.txt").read_text() == "asset"
    index = (output / "index.html").read_text()
    assert 'href="/2026/05/18/gaussianintegral.html"' in index
    assert "Private" not in index
    assert "Gaussian Integral" in (output / "feed.xml").read_text()
    assert not result.warnings


def test_site_pagination_builds_jekyll_paginator_pages(tmp_path: Path):
    source = tmp_path / "site"
    output = tmp_path / "public"
    (source / "_layouts").mkdir(parents=True)
    (source / "_posts").mkdir()
    (source / "_layouts" / "default.html").write_text(
        "layout-page={{ paginator.page }} page-url={{ page.url }} | {{ content }}",
    )
    (source / "index.html").write_text(
        """---
layout: default
---
page={{ paginator.page }} per={{ paginator.per_page }} total={{ paginator.total_posts }} pages={{ paginator.total_pages }}
previous={{ paginator.previous_page }} previous-path={{ paginator.previous_page_path }}
next={{ paginator.next_page }} next-path={{ paginator.next_page_path }} site-posts={{ site.posts | size }}
{% for post in paginator.posts %}{{ post.title }}|{% endfor %}
""",
    )
    for day, title, hidden in [
        ("05", "Hidden", True), ("04", "Four", False), ("03", "Three", False),
        ("02", "Two", False), ("01", "One", False),
    ]:
        (source / "_posts" / f"2026-01-{day}-{title.lower()}.md").write_text(
            f"---\ntitle: {title}\nhidden: {str(hidden).lower()}\n---\n{title}\n",
        )
    (source / "md2html.json").write_text(
        '{"input":".","output":"../public","output_mode":"site",'
        '"paginate":2,"paginate_path":"/notes/page:num/"}',
    )
    settings = load_settings(source / "md2html.json")

    result = Project(settings).build()

    first = (output / "index.html").read_text()
    second = (output / "notes/page2/index.html").read_text()
    assert "layout-page=1 page-url=/" in first
    assert "page=1 per=2 total=4 pages=2" in first
    assert "previous= previous-path=" in first
    assert "next=2 next-path=/notes/page2/ site-posts=5" in first
    assert "Four|Three|" in first and "Two|" not in first and "Hidden|" not in first
    assert "layout-page=2 page-url=/notes/page2/" in second
    assert "previous=1 previous-path=/" in second
    assert "next= next-path=" in second
    assert "Two|One|" in second and "Four|" not in second
    assert output / "notes/page2/index.html" in result.written
    assert source / "_posts/2026-01-01-one.md" in result.page_dependencies[source / "index.html"]

    unchanged = Project(settings).build(skip_unchanged=True)
    assert output / "index.html" in unchanged.skipped
    assert output / "notes/page2/index.html" in unchanged.skipped
    post = source / "_posts/2026-01-01-one.md"
    post.write_text(post.read_text() + "changed\n")
    modified = max((output / "index.html").stat().st_mtime_ns, (output / "notes/page2/index.html").stat().st_mtime_ns) + 1
    os.utime(post, ns=(modified, modified))
    rebuilt = Project(settings).build(skip_unchanged=True)
    assert output / "index.html" in rebuilt.written
    assert output / "notes/page2/index.html" in rebuilt.written


def test_pagination_requires_an_html_index_and_numbered_path(tmp_path: Path):
    source = tmp_path / "site"
    output = tmp_path / "public"
    (source / "_posts").mkdir(parents=True)
    (source / "_posts/2026-01-01-post.md").write_text("---\ntitle: Post\n---\nPost\n")
    (source / "index.md").write_text("{{ paginator.page }}")
    settings = Settings(
        input=source, output=output, output_mode="site", project_root=source,
        recursive=True, site_data={"paginate": 1, "paginate_path": "/pages/"},
    )
    Project(settings).build()
    assert not (output / "pages/index.html").exists()

    (source / "index.md").unlink()
    (source / "index.html").write_text("{{ paginator.page }}")
    with pytest.raises(ValueError, match="paginate_path must contain :num"):
        Project(settings).build()


def test_jekyll_mode_uses_config_conventions_and_shared_features(tmp_path: Path):
    source = tmp_path / "site"
    output = tmp_path / "public"
    (source / "_layouts").mkdir(parents=True)
    (source / "_posts").mkdir()
    (source / "_config.yml").write_text(
        "title: Jekyll Site\nurl: https://example.test\nbaseurl: /notes\n",
    )
    (source / "_layouts/default.html").write_text(
        "<title>{{ site.title }} | {{ page.title }}</title>"
        "{% if md2html.jekyll_compatibility %}md2html compatibility{% endif %}{{ content }}",
    )
    (source / "program.py").write_text("print('executed')\n")
    post = source / "_posts/2026-07-11-feature.md"
    post.write_text(
        "---\nlayout: default\ntitle: Feature\ncategories: physics\ntags: Math Code\n---\n"
        "@src(program.py, execute)\n",
    )
    (source / "index.html").write_text(
        "---\nlayout: default\ntitle: Home\n---\n"
        "{% for post in site.posts %}{{ post.url }} {{ post.tags | join: ',' }}{% endfor %}",
    )
    (source / "plain.md").write_text("No front matter means static Markdown.\n")
    (source / "draft.md").write_text("---\npublished: false\n---\nNot published.\n")
    (source / "Gemfile").write_text("excluded\n")
    settings = Settings(
        input=source, output=output, output_mode="jekyll", project_root=source,
        recursive=True, execute=True,
    )

    result = Project(settings).build()

    post_output = output / "physics/2026/07/11/feature.html"
    assert "<title>Jekyll Site | Feature</title>" in post_output.read_text()
    assert "md2html compatibility" in post_output.read_text()
    assert "codehilite" in post_output.read_text() and "executed" in post_output.read_text()
    assert 'href="/notes/program.py"' in post_output.read_text()
    assert "/physics/2026/07/11/feature.html Math,Code" in (output / "index.html").read_text()
    assert (output / "plain.md").read_text() == "No front matter means static Markdown.\n"
    assert not (output / "draft.html").exists()
    assert not (output / "Gemfile").exists()
    assert post in result.page_dependencies


def test_jekyll_layout_assets_are_not_discovered_or_rewritten(tmp_path: Path):
    source, output = tmp_path / "site", tmp_path / "public"
    (source / "_layouts").mkdir(parents=True)
    (source / "assets/md2html").mkdir(parents=True)
    (source / "_layouts/default.html").write_text(
        '<link rel="stylesheet" href="/theme.css">'
        '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>'
        "{{ content }}",
    )
    (source / "theme.css").write_text("body { color: navy; }")
    (source / "assets/md2html/mathjax.js").write_text("site-owned")
    (source / "index.md").write_text("---\nlayout: default\n---\n$x+1$\n")
    settings = Settings(
        input=source, output=output, output_mode="jekyll", project_root=source,
        recursive=True, assets="standalone", math=MathSettings("mathjax"),
    )
    result = Project(settings).build()
    page = (output / "index.html").read_text()
    assert '<link rel="stylesheet" href="/theme.css">' in page
    assert 'mathjax@3/es5/tex-mml-chtml.js' in page
    assert MATHJAX_CDN not in page and "<style>body { color: navy; }</style>" not in page
    assert (output / "assets/md2html/mathjax.js").read_text() == "site-owned"
    assert not result.warnings


def test_jekyll_markdown_preserves_markdown_and_expands_md2html_syntax(tmp_path: Path):
    source = tmp_path / "notes"
    output = tmp_path / "jekyll"
    (source / "_layouts").mkdir(parents=True)
    (source / "_layouts/default.html").write_text("{{ content }}")
    (source / "parts").mkdir()
    (source / "parts/more.md").write_text("## Included\n")
    (source / "program.py").write_text("print('markdown execution')\n")
    (source / "image.png").write_bytes(b"image")
    page = source / "index.md"
    page.write_text(
        "# Notes\n\n@toc\n\n@include(parts/more.md)\n\n@src(program.py, execute)\n\n"
        "@src-begin(python, execute)\nprint('inline markdown')\n@src-end\n\n"
        "```text\n@src(not-a-directive.py)\n{{ untouched_code }}\n```\n\n"
        "## Exercises\n\n### Exercise 1.1\n\n"
        "Liquid stays {{ site.title }} and math stays $x^2$.\n\n![[image.png|200]]\n",
    )
    settings = Settings(
        input=source, output=output, output_mode="jekyll-markdown", project_root=source,
        recursive=True, execute=True, frontmatter={"layout": "default", "render_with_liquid": False},
    )

    result = Project(settings).build()

    markdown = (output / "index.md").read_text()
    assert markdown.startswith("---\nlayout: default\nrender_with_liquid: false\ntitle: index.md\n---")
    assert '<div class="table-of-contents">' in markdown
    assert '<a href="#included">Included</a>' in markdown
    assert markdown.count('class="toc-exercises"') == 1 and "*Exercises:*" not in markdown
    assert '<div class="codehilite"><pre>' in markdown and "markdown execution" in markdown
    assert "inline-source" in markdown and "inline markdown" in markdown
    assert "@src(program.py" not in markdown and "@src-begin" not in markdown and "@src-end" not in markdown
    assert "```text\n@src(not-a-directive.py)\n{{ untouched_code }}\n```" in markdown
    assert "Liquid stays {{ site.title }} and math stays $x^2$." in markdown
    assert '<img class="obsidian-image" src="image.png" alt="image" style="width:200px">' in markdown
    assert (output / "program.py").read_text() == "print('markdown execution')\n"
    assert (output / "_layouts/default.html").read_text() == "{{ content }}"
    assert {page, source / "parts/more.md", source / "program.py", source / "image.png"} <= result.page_dependencies[page]

    cached_output = tmp_path / "cached-jekyll"
    cached = Project(settings.with_cli(output=cached_output, execute=False)).build()
    assert "markdown execution" in (cached_output / "index.md").read_text()
    assert not cached.warnings


def test_liquid_only_pages_preserve_suffix_and_special_syntax(tmp_path: Path):
    source = tmp_path / "site"
    output = tmp_path / "public"
    (source / "_includes").mkdir(parents=True)
    (source / "_includes" / "value.html").write_text("included")
    literal = "# Not Markdown\n@toc\n@src-begin(python)\n$x^2$ ![[image.png]]"
    (source / "page.html").write_text(
        "{{ site.title }} {% include value.html %} {% raw %}{{ untouched }}{% endraw %}\n" + literal,
    )
    (source / "short.htm").write_text("{{ site.title }}")
    (source / "feed.xml").write_text("<feed><title>{{ site.title }}</title><text>@toc</text></feed>")
    settings = Settings(
        input=source, output=output, output_mode="site", project_root=source,
        recursive=True, site_data={"title": "Liquid site"},
    )
    result = Project(settings).build()
    page = (output / "page.html").read_text()
    assert "Liquid site included {{ untouched }}" in page
    assert literal in page and "table-of-contents" not in page and "MathJax" not in page
    assert (output / "short.htm").read_text() == "Liquid site\n"
    assert (output / "feed.xml").read_text() == "<feed><title>Liquid site</title><text>@toc</text></feed>\n"
    assert not (output / "feed.html").exists()
    assert source / "_includes" / "value.html" in result.page_dependencies[source / "page.html"]


def test_markdown_and_liquid_only_pages_use_distinct_rendering_paths(tmp_path: Path):
    source = tmp_path / "content"
    output = tmp_path / "public"
    source.mkdir()
    (source / "note.markdown").write_text("# {{ site.title }}\n\n@toc\n")
    (source / "document.html").write_text("# {{ site.title }}\n@toc\n")
    settings = Settings(
        input=source, output=output, project_root=source, recursive=True,
        site_data={"title": "Rendered"},
    )
    Project(settings).build()
    markdown = (output / "note.html").read_text()
    liquid = (output / "document.html").read_text()
    assert '<h1 id="rendered">Rendered</h1>' in markdown and "table-of-contents" in markdown
    assert "# Rendered\n@toc" in liquid and '<main class="container">' not in liquid

    single = tmp_path / "single.html"
    single.write_text('<img src="image.png">')
    (tmp_path / "image.png").write_bytes(b"image")
    Project(Settings.single(single, tmp_path / "moved/single.html")).build()
    assert 'src="data:image/png;base64,' in (tmp_path / "moved/single.html").read_text()
    assert not (tmp_path / "moved/image.png").exists()


def test_source_liquid_can_be_disabled_without_disabling_layouts(tmp_path: Path):
    source = tmp_path / "site"
    output = tmp_path / "public"
    (source / "_layouts").mkdir(parents=True)
    (source / "_layouts" / "default.html").write_text("<title>{{ page.title }}</title><main>{{ content }}</main>")
    (source / "off.html").write_text(
        "---\nlayout: default\ntitle: Page title\nrender_with_liquid: false\n---\n{{ page.title }}",
    )
    (source / "global.md").write_text("---\ntitle: Global\nrender_with_liquid: true\n---\n# {{ page.title }}\n")
    settings = Settings(
        input=source, output=output, output_mode="site", project_root=source,
        recursive=True,
    )
    Project(settings).build()
    html = (output / "off.html").read_text()
    assert "<title>Page title</title>" in html and "<main>{{ page.title }}</main>" in html
    assert '<h1 id="global">Global</h1>' in (output / "global.html").read_text()
    Project(settings.with_cli(output=tmp_path / "without-liquid", parse_liquid=False)).build()
    markdown = (tmp_path / "without-liquid/global.html").read_text()
    assert "<h1 id=\"pagetitle\">{{ page.title }}</h1>" in markdown


def test_source_output_collision_warns_and_other_pages_continue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.chdir(tmp_path)
    Path("page.html").write_text("{{ site.title }}")
    Path("feed.xml").write_text("<feed/>")
    Path("note.md").write_text("# Note\n")
    planned = settings_list_from_args(parser().parse_args(["page.html", "feed.xml", "note.md", "-o", "public"]))
    assert [item.output for item in planned] == [Path("public/page.html"), Path("public/feed.xml"), Path("public/note.html")]
    collision = Project(Settings.single(Path("page.html"))).build()
    assert not collision.written and not collision.page_dependencies
    assert any("source and output are the same file" in warning for warning in collision.warnings)
    assert main(["page.html", "note.md"]) == 0
    assert Path("page.html").read_text() == "{{ site.title }}"
    assert Path("html/note.html").is_file()
    assert not capsys.readouterr().err


def test_native_site_deduplicates_mathjax_styles(tmp_path: Path):
    source, output = site_fixture(tmp_path)
    settings = site_settings(source, output, math=MathSettings("mathjax-chtml"))
    Project(settings).build()
    post = (output / "2026/05/18/gaussianintegral.html").read_text()
    stylesheet = output / "assets/md2html/mathjax-chtml.css"
    css = stylesheet.read_text()
    assert stylesheet.is_file() and "@font-face" in css
    assert ".math-copy-source" in css and ".math-rendered" in css
    assert "mjx-c.mjx-c" in css
    assert "cdn.jsdelivr.net" not in css
    assert 'url("mathjax/woff2/mjx-tex-n.woff2")' in css
    assert (output / "assets/md2html/mathjax/woff2/mjx-tex-n.woff2").is_file()
    assert (output / "assets/md2html/mathjax/woff2/mjx-tex-zero.woff2").is_file()
    assert '<link rel="stylesheet" href="/assets/md2html/mathjax-chtml.css">' in post
    assert 'rel="preload" href="/assets/md2html/mathjax/woff2/mjx-tex-n.woff2"' in post
    assert post.index("data-hash-pending") < post.index("mathjax-chtml.css") < post.index('src="/site.js"')
    assert "<mjx-container" in post
    assert "data-md2html-math-copy" in post
    assert "MJX-CHTML-styles" not in post


@pytest.mark.parametrize("mode, marker", [("remote", "cdn.jsdelivr.net"), ("inline", "data:font/woff2;base64,"), ("none", None)])
def test_native_site_chtml_font_modes(tmp_path: Path, mode: str, marker: str | None):
    source, output = site_fixture(tmp_path)
    settings = site_settings(source, output, math=MathSettings("mathjax-chtml", mode))
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
    settings = site_settings(source, output, math=MathSettings("mathjax-chtml", "all"))
    Project(settings).build()
    fonts = list((output / "assets/md2html/mathjax/woff2").glob("*.woff2"))
    post = (output / "2026/05/18/gaussianintegral.html").read_text()
    assert len(fonts) == 22
    assert post.count('rel="preload"') < len(fonts)


def test_config_paths_are_relative_to_config(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "content").mkdir()
    config = root / "md2html.json"
    config.write_text('{"input":"content","output":"public","output_mode":"pages","math":{"backend":"mathml","chtml_fonts":"inline"}}')
    settings = load_settings(config)
    assert settings.input == root / "content"
    assert settings.output == root / "public"
    assert settings.math.backend == "mathml"
    assert settings.math.chtml_fonts == "inline"
    assert settings.asset_mode == "shared"
    config.write_text('{"input":"content","output_mode":"jekyll-markdown","frontmatter":{"layout":"post"}}')
    settings = load_settings(config)
    assert settings.output == root / "markdown" and settings.recursive
    assert settings.frontmatter == {"layout": "post"}


def test_only_md2html_json_is_discovered_and_configuration_is_json(tmp_path: Path):
    (tmp_path / "md2html.config").write_text("input: content\n")
    (tmp_path / "md2html.yml").write_text("input: content\n")
    assert find_config(tmp_path) is None
    with pytest.raises(ValueError, match="must be a JSON file"):
        load_settings(tmp_path / "md2html.yml")
    config = tmp_path / "md2html.json"
    config.write_text('{"input":"content","timeout":3.5,"feature_css":false,"minify_css":false,"parse_liquid":false,"highlight_style":"friendly","images":{"class":"centered","width":"50%"}}')
    assert find_config(tmp_path) == config
    settings = load_settings(config)
    assert settings.timeout == 3.5
    assert not settings.feature_css
    assert not settings.minify_css
    assert not settings.parse_liquid
    assert settings.highlight_style == "friendly"
    assert settings.images == ImageSettings("centered", "50%")
    config.write_text("input: content\n")
    with pytest.raises(ValueError, match="could not read configuration"):
        load_settings(config)


def test_relative_config_keeps_relative_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    Path("md2html.json").write_text('{"input":"content","output":"public","templates":"templates"}')
    settings = load_settings(Path("md2html.json"))
    assert settings.project_root == Path(".")
    assert settings.input == Path("content")
    assert settings.output == Path("public")
    assert settings.templates == (Path("templates"),)


def test_template_directories_are_ordered_and_repeatable(tmp_path: Path):
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "page.html").write_text("first {{ content }}")
    (second / "page.html").write_text("second {{ content }}")
    config = tmp_path / "md2html.json"
    config.write_text('{"input":"article.md","templates":["first","second"]}')
    assert load_settings(config).templates == (first, second)
    output = build_one(tmp_path, "# Ordered\n", templates=(first, second))
    assert output.startswith("first ") and "second " not in output
    args = parser().parse_args(["article.md", "--templates", "first", "--templates", "second"])
    assert settings_from_args(args).templates == (Path("first"), Path("second"))


def test_template_directory_and_companion_css_take_priority(tmp_path: Path):
    bundled = tmp_path / "_templates"
    bundled.mkdir()
    (bundled / "page.html").write_text("wrong project template")
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "page.html").write_text("<title>{{ page.title }}</title><style>{{ md2html.css }}</style>{{ content }}")
    (templates / "page.css").write_text("body{color:rebeccapurple}")
    output = build_one(tmp_path, "# Custom\n", templates=(templates,))
    assert "rebeccapurple" in output
    assert ".code-box" not in output
    assert "reader-controls" not in output


def test_source_block_does_not_consume_the_following_heading(tmp_path: Path):
    (tmp_path / "example.py").write_text("print('example')\n")
    output = build_one(tmp_path, "@src(example.py)\n## Next section\n")
    assert '<h2 id="next-section">Next section</h2>' in output


def test_custom_template_can_omit_math_renderer_assets(tmp_path: Path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "page.html").write_text("<style>{{ md2html.css }}</style>{{ content }}")
    output = build_one(tmp_path, "$x^2$\n", templates=(templates,))
    assert "<mjx-container" in output
    assert "@font-face" not in output
    assert "data-md2html-math-copy" not in output

    (templates / "page.html").write_text(
        "<style>{{ md2html.css }}</style><style>{{ md2html.math_css }}</style>{{ content }}"
    )
    output = build_one(tmp_path, "$x^2$\n", templates=(templates,))
    assert "@font-face" in output


def test_project_root_fallback_and_project_template_directory(tmp_path: Path):
    nested = tmp_path / "chapters"
    templates = tmp_path / "_templates"
    nested.mkdir()
    templates.mkdir()
    (tmp_path / "shared.md").write_text("Included from root.\n")
    (tmp_path / "program.py").write_text("print('root source')\n")
    (templates / "page.html").write_text("<main data-project-template>{{ content }}</main>")
    source = nested / "one.md"
    source.write_text("@include(shared.md)\n\n@src(program.py)\n")
    settings = Settings.single(source).with_cli(project_root=tmp_path)
    output = Project(settings).build().written[0].read_text()
    assert "data-project-template" in output
    assert "Included from root" in output and "root source" in output


def test_standalone_template_fallback_does_not_search_site_layouts(tmp_path: Path):
    layouts = tmp_path / "_layouts"
    layouts.mkdir()
    (layouts / "page.html").write_text("site layout should not become a page template")
    output = build_one(tmp_path, "# Bundled template\n")
    assert '<main class="container">' in output
    assert "site layout should not become" not in output


def test_page_frontmatter_selects_template_css_and_stylesheets(tmp_path: Path):
    templates = tmp_path / "_templates"
    templates.mkdir()
    (templates / "card.html").write_text(
        "{% for href in md2html.stylesheets %}<link rel=stylesheet href=\"{{ href }}\">{% endfor %}"
        "<style>{{ md2html.css }}</style><main>{{ content }}</main>"
    )
    (tmp_path / "custom.css").write_text("body{color:rebeccapurple}")
    (tmp_path / "print.css").write_text("@media print{}")
    output = build_one(
        tmp_path,
        "---\ntemplate: card\ncss: custom.css\nstylesheets: [print.css]\n---\n```python\nprint(1)\n```\n",
    )
    assert "rebeccapurple" in output
    assert ".code-box" in output and ".codehilite .k" in output
    assert "@media print{}" in output and "<link rel=stylesheet" not in output


def test_authored_stylesheet_follows_default_and_math_css(tmp_path: Path):
    (tmp_path / "override.css").write_text("body{color:purple}")
    output = build_one(tmp_path, "$x^2$\n", stylesheets=("override.css",))
    assert output.index("mjx-container") < output.index("body{color:purple}")


def test_directory_pages_can_choose_different_templates_and_css(tmp_path: Path):
    source = tmp_path / "content"
    templates = tmp_path / "_templates"
    output = tmp_path / "public"
    source.mkdir()
    templates.mkdir()
    (templates / "special.html").write_text("<style>{{ md2html.css }}</style><aside>{{ content }}</aside>")
    (tmp_path / "special.css").write_text("aside{color:purple}")
    (source / "one.md").write_text("---\ntemplate: special\ncss: special.css\n---\n# One\n")
    (source / "two.md").write_text("# Two\n")
    Project(Settings(input=source, output=output, project_root=tmp_path)).build()
    assert "<aside>" in (output / "one.html").read_text() and "color:purple" in (output / "one.html").read_text()
    assert '<main class="container">' in (output / "two.html").read_text()


def test_custom_css_keeps_feature_css_and_highlight_styles_are_cli_names(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    Path("base.css").write_text("body{color:navy}")
    Path("code.md").write_text("```python\nif True: print(1)\n```\n")
    assert main(["code.md", "--css", "base.css", "--highlight-style", "monokai"]) == 0
    output = Path("code.html").read_text()
    assert "color:navy" in output and ".codehilite" in output
    assert "#272822" in output
    settings = settings_from_args(parser().parse_args(["code.md", "--highlight-dark-style", "friendly"]))
    assert settings.highlight_dark_style == "friendly"
    assert main(["code.md", "--css", "base.css", "--no-feature-css"]) == 0
    output = Path("code.html").read_text()
    assert "color:navy" in output and ".codehilite .k {" not in output
    Path("code.md").write_text("---\ncss: []\n---\n```python\nif True: print(1)\n```\n")
    assert main(["code.md", "--css", "base.css"]) == 0
    output = Path("code.html").read_text()
    assert "color:navy" not in output and ".codehilite .k{" in output
    with pytest.raises(SystemExit):
        parser().parse_args(["code.md", "--highlight-style", "not-a-pygments-style"])


def test_css_is_minified_by_default_and_can_remain_readable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    Path("article.md").write_text("# CSS\n")
    Path("custom.css").write_text('body { color: red; } p::before { content: "a : b"; }')
    assert main(["article.md", "--css", "custom.css"]) == 0
    compact = Path("article.html").read_text()
    assert 'body{color:red}p::before{content:"a : b"}' in compact
    assert main(["article.md", "--css", "custom.css", "--no-minify-css"]) == 0
    readable = Path("article.html").read_text()
    assert 'body { color: red; }' in readable and len(readable) > len(compact)


def test_template_feature_introspection_uses_flat_booleans(tmp_path: Path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "page.html").write_text(
        "{{ md2html.has_code }}|{{ md2html.has_toc }}|{{ md2html.has_images }}|"
        "{{ md2html.has_warnings }}|{{ md2html.uses_svg_math }}|{{ md2html.uses_mathjax }}"
        "|{{ md2html.jekyll_compatibility }}"
    )
    output = build_one(
        tmp_path, "# Features\n\n@toc\n\n```py\npass\n```\n\n$x$\n",
        templates=(templates,), math=MathSettings("svg"),
    )
    assert output.strip() == "true|true|false|false|true|false|false"


def test_port_has_a_short_alias():
    assert parser().parse_args(["-p", "4321"]).port == 4321


def test_execution_timeout_is_configurable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "example.demo").write_text("source\n")
    seen: list[float] = []

    def run(*args, **kwargs):
        seen.append(kwargs["timeout"])
        return subprocess.CompletedProcess(args[0], 0, "output\n", "")

    monkeypatch.setattr("md2html2.render.subprocess.run", run)
    build_one(tmp_path, "@src(example.demo)\n", execute=True, timeout=2.5, commands={"demo": "demo {source}"})
    assert seen == [2.5]
    assert settings_from_args(parser().parse_args([str(tmp_path / "article.md"), "--timeout", "7.5"])).timeout == 7.5


def test_single_page_copies_referenced_assets_when_output_moves(tmp_path: Path):
    source = tmp_path / "article.md"
    image = tmp_path / "figure.png"
    code = tmp_path / "example.py"
    source.write_text("![[figure.png|320]]\n\n@src(example.py)\n")
    image.write_bytes(b"image")
    code.write_text("print('copied')\n")
    output = tmp_path / "public" / "article.html"
    result = Project(Settings.single(source, output)).build()
    assert (output.parent / "figure.png").read_bytes() == b"image"
    assert (output.parent / "example.py").read_text() == "print('copied')\n"
    assert result.asset_dependencies[image] == output.parent / "figure.png"


def test_cli_short_flags_and_scaffolds(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    source = Path("one.md")
    source.write_text("# One\n")
    args = parser().parse_args(["-erf", str(source)])
    settings = settings_from_args(args)
    assert settings.execute and settings.recursive and settings.force
    assert settings.input == source and settings.output == Path("one.html")
    assert not settings_from_args(parser().parse_args([str(source), "--no-liquid"])).parse_liquid
    assert main(["--example-config"]) == 0
    assert (tmp_path / "md2html.json").is_file()
    assert main(["--example-config"]) == 2
    assert main(["--example-config", "--force"]) == 0
    assert '"parse_liquid": true' in (tmp_path / "md2html.json").read_text()
    assert main(["--example-template", "-"]) == 0
    assert "<!doctype html>" in capsys.readouterr().out.lower()
    assert main(["--example-template"]) == 0
    assert main(["--example-css"]) == 0
    example_css = (tmp_path / "templates/page.css").read_text()
    assert ".reader-widget form" in example_css
    assert ".table-of-contents" in example_css
    assert ".code-box .codehilite" in example_css
    assert ".code-output pre" in example_css
    assert ".codehilite .kc { color: #008000; font-weight: bold }" in example_css
    assert main([str(source), "--templates", "templates"]) == 0
    generated = source.with_suffix(".html").read_text()
    assert '<main class="container">' in generated and "--reader-text-size" in generated
    assert generated.count(".code-box .codehilite{") == 1


def test_cli_selects_jekyll_modes_and_safe_defaults(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    site = Path("site")
    site.mkdir()
    (site / "index.md").write_text("# Page\n")

    jekyll = settings_from_args(parser().parse_args(["--jekyll", str(site)]))
    markdown = settings_from_args(parser().parse_args(["--jekyll-markdown", str(site)]))
    assert jekyll.output_mode == "jekyll" and jekyll.output == Path("_site") and jekyll.recursive
    assert markdown.output_mode == "jekyll-markdown" and markdown.output == Path("markdown") and markdown.recursive
    assert main(["--jekyll-markdown", str(site), "--serve"]) == 2
    assert "--serve requires HTML output" in capsys.readouterr().err

    calls = []
    monkeypatch.setattr("md2html2.cli.watch", lambda settings, **options: calls.append((settings[0].output_mode, options)) or 0)
    assert main(["--jekyll", str(site), "--serve"]) == 0
    assert main(["--jekyll-markdown", str(site), "--watch"]) == 0
    assert calls == [("jekyll", {"serve": True, "port": 8000}), ("jekyll-markdown", {"serve": False, "port": 8000})]


def test_help_and_readme_explain_watch_serve_and_examples(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit):
        parser().parse_args(["--help"])
    help_text = capsys.readouterr().out
    assert "rebuild when source files change" in help_text
    assert "md2html -erf notes -o html" in help_text
    assert "--assets" in help_text and "--standalone" in help_text and "--timeout" in help_text
    assert main(["--readme"]) == 0
    readme = capsys.readouterr().out
    assert readme == (Path(__file__).parents[1] / "readme.md").read_text()
    assert "@src-begin" in readme
    assert "2026/05/18/gaussianintegral.html" in readme
    assert '"assets": "shared"' in readme and "md2html.json" in readme
    for action in parser()._actions:
        for option in (name for name in action.option_strings if name.startswith("--")):
            assert option in readme


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


def test_multiple_files_build_beside_sources_or_under_output_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    Path("folder").mkdir()
    for name in ("one.md", "two.md", "folder/three.md"):
        Path(name).write_text(f"# {name}\n")
    assert main(["one.md", "two.md", "folder/three.md"]) == 0
    assert Path("html/one.html").is_file() and Path("html/two.html").is_file() and Path("html/folder/three.html").is_file()
    assert Path("html/assets/md2html/page.css").is_file()
    settings = settings_list_from_args(parser().parse_args(["one.md", "two.md", "folder/three.md", "-o", "public"]))
    assert [item.output for item in settings] == [Path("public/one.html"), Path("public/two.html"), Path("public/folder/three.html")]
    assert main(["one.md", "two.md", "folder/three.md", "-o", "public"]) == 0
    assert all(item.output.is_file() for item in settings)


def test_multiple_directories_preserve_their_names_under_one_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    for directory in (Path("book"), Path("notes")):
        directory.mkdir()
        (directory / "index.md").write_text(f"# {directory.name}\n")
    assert main(["-r", "book", "notes", "-o", "public"]) == 0
    assert Path("public/book/index.html").is_file()
    assert Path("public/notes/index.html").is_file()
    for directory in ("book", "notes"):
        css = Path(f"public/{directory}/assets/md2html/page.css")
        page = Path(f"public/{directory}/index.html").read_text()
        assert css.is_file() and ".code-box" in css.read_text()
        assert 'href="assets/md2html/page.css"' in page


def test_shared_asset_mode_collects_files_and_externalizes_common_css(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    Path("one.md").write_text("# One\n")
    Path("two.md").write_text("# Two\n")
    settings = settings_list_from_args(parser().parse_args(["one.md", "two.md", "--assets", "shared"]))
    assert [item.output for item in settings] == [Path("html/one.html"), Path("html/two.html")]
    assert all(item.asset_mode == "shared" for item in settings)
    assert main(["one.md", "two.md", "--assets", "shared"]) == 0
    assert Path("html/assets/md2html/page.css").is_file()
    assert 'href="assets/md2html/page.css"' in Path("html/one.html").read_text()


def test_shared_directory_uses_external_static_math_css_and_fonts(tmp_path: Path):
    source = tmp_path / "content"
    output = tmp_path / "public"
    source.mkdir()
    (source / "index.md").write_text("# Math\n\n$x^2$\n")
    settings = Settings(
        input=source, output=output, project_root=source, assets="shared",
        math=MathSettings("mathjax-chtml", "auto"),
    )
    Project(settings).build()
    page = (output / "index.html").read_text()
    assert 'href="assets/md2html/page.css"' in page
    assert 'href="assets/md2html/mathjax-chtml.css"' in page
    assert "@font-face" not in page
    assert (output / "assets/md2html/mathjax-chtml.css").is_file()
    assert len(list((output / "assets/md2html/mathjax/woff2").glob("*.woff2"))) >= 20
    stylesheet = output / "assets/md2html/mathjax-chtml.css"
    before = stylesheet.read_text()
    skipped = Project(settings).build(skip_unchanged=True)
    assert skipped.skipped == [output / "index.html"]
    assert stylesheet.read_text() == before


def test_single_page_can_use_shared_chtml_without_duplicate_css(tmp_path: Path):
    source, output = tmp_path / "note.md", tmp_path / "note.html"
    source.write_text("$x^2$\n")
    Project(Settings.single(source, output).with_cli(assets="shared")).build()
    page = output.read_text()
    assert 'href="assets/md2html/mathjax-chtml.css"' in page
    assert "data:font/woff2;base64," not in page and CHTML_CDN not in page
    assert (tmp_path / "assets/md2html/mathjax-chtml.css").is_file()


def test_asset_defaults_and_standalone_alias(tmp_path: Path):
    source = tmp_path / "note.md"
    source.write_text("# Note\n")
    assert Settings.single(source).asset_mode == "standalone"
    assert Settings(input=tmp_path, output=tmp_path / "public").asset_mode == "shared"
    assert settings_from_args(parser().parse_args([str(source), "--standalone"])).asset_mode == "standalone"
    assert settings_from_args(parser().parse_args([str(source), "--math-fonts", "local"])).math.chtml_fonts == "local"


@pytest.mark.parametrize("assets, marker", [
    ("standalone", "https://cdn.jsdelivr.net/npm/mathjax@4.1.3/tex-mml-chtml.js"),
    ("shared", 'src="assets/md2html/mathjax.js"'),
    ("cdn", "https://cdn.jsdelivr.net/npm/mathjax@4.1.3/tex-mml-chtml.js"),
])
def test_browser_mathjax_asset_modes(tmp_path: Path, assets: str, marker: str):
    source = tmp_path / "note.md"
    source.write_text("# Math\n\n$x+1$\n")
    output = tmp_path / f"{assets}.html"
    result = Project(Settings.single(source, output).with_cli(assets=assets, math=MathSettings("mathjax"))).build()
    page = output.read_text()
    assert marker in page and "<mjx-container" not in page
    if assets == "standalone":
        assert not (tmp_path / "assets").exists()
        assert any("standalone browser MathJax assets are not implemented" in warning for warning in result.warnings)
    elif assets == "shared":
        assert (tmp_path / "assets/md2html/mathjax.js").is_file()
        assert (tmp_path / "assets/md2html/mathjax-newcm-font/chtml/woff2/mjx-ncm-n.woff2").is_file()
        assert (tmp_path / "assets/md2html/sre/speech-worker.js").is_file()
        assert result.copied


@pytest.mark.parametrize("assets, fonts, marker", [
    ("standalone", "auto", "data:font/woff2;base64,"),
    ("standalone", "remote", CHTML_CDN),
    ("cdn", "auto", CHTML_CDN),
    ("cdn", "local", "data:font/woff2;base64,"),
])
def test_standalone_chtml_font_asset_matrix(tmp_path: Path, assets: str, fonts: str, marker: str):
    source = tmp_path / "note.md"
    source.write_text("$x+1$\n")
    output = tmp_path / f"{assets}-{fonts}.html"
    Project(Settings.single(source, output).with_cli(assets=assets, math=MathSettings("mathjax-chtml", fonts))).build()
    assert marker in output.read_text()


@pytest.mark.parametrize("backend, marker", [
    ("svg", "md2html-math-svg-image"),
    ("mathml", "md2html-mathml"),
    ("raw", "$x+1$"),
])
@pytest.mark.parametrize("assets", ["standalone", "shared", "cdn"])
def test_dependency_free_math_asset_modes(tmp_path: Path, backend: str, marker: str, assets: str):
    source = tmp_path / "note.md"
    source.write_text("$x+1$\n")
    output = tmp_path / f"{backend}-{assets}.html"
    Project(Settings.single(source, output).with_cli(assets=assets, math=MathSettings(backend))).build()
    assert marker in output.read_text()
    assert (tmp_path / "assets/md2html/page.css").is_file() == (assets == "shared")


def test_standalone_directory_embeds_renderer_and_authored_assets_per_page(tmp_path: Path):
    source, output = tmp_path / "content", tmp_path / "public"
    source.mkdir()
    (source / "style.css").write_text("body { background: url(pixel.png); }")
    (source / "pixel.png").write_bytes(b"image")
    (source / "site.js").write_text("window.assetLoaded = true;")
    body = '<link rel="stylesheet" href="style.css"><script src="site.js"></script><img src="pixel.png">\n\n$x$\n'
    (source / "one.md").write_text(body)
    (source / "two.md").write_text(body)
    Project(Settings(input=source, output=output, project_root=source, assets="standalone", recursive=True)).build()
    for name in ("one.html", "two.html"):
        page = (output / name).read_text()
        assert '<link rel="stylesheet"' not in page
        assert "window.assetLoaded = true" in page
        assert page.count("data:image/png;base64,") == 2
        assert "data:font/woff2;base64," in page


def test_asset_mode_changes_prune_obsolete_renderer_files(tmp_path: Path):
    source, output = tmp_path / "content", tmp_path / "public"
    source.mkdir()
    (source / "index.md").write_text("$x$\n")
    Project(Settings(input=source, output=output, project_root=source, assets="shared")).build()
    assert (output / "assets/md2html/page.css").is_file()
    assert (output / "assets/md2html/mathjax-chtml.css").is_file()
    settings = Settings(
        input=source, output=output, project_root=source, assets="standalone",
        math=MathSettings("mathjax"),
    )
    Project(settings).build()
    assert not (output / "assets/md2html/page.css").exists()
    assert not (output / "assets/md2html/mathjax-chtml.css").exists()
    assert not (output / "assets/md2html/mathjax.js").exists()


def test_multiple_input_server_exposes_only_planned_files(tmp_path: Path):
    public = tmp_path / "public"
    public.mkdir()
    page = public / "one.html"
    secret = public / "secret.txt"
    page.write_text("page")
    secret.write_text("secret")
    routes = {"one.html": page}
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    server, _ = _server(public, port, routes)
    try:
        assert urlopen(f"http://127.0.0.1:{port}/one.html").read() == b"page"
        with pytest.raises(OSError):
            urlopen(f"http://127.0.0.1:{port}/secret.txt")
    finally:
        server.shutdown()
        server.server_close()


def test_multiple_file_serve_builds_watches_and_links_every_page_without_exposing_the_source_directory(tmp_path: Path):
    (tmp_path / "folder").mkdir()
    for name in ("one.md", "two.md", "folder/three.md"):
        (tmp_path / name).write_text(f"# {name}\n")
    (tmp_path / "private.txt").write_text("not served")
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "md2html2", "one.md", "two.md", "folder/three.md", "--serve", "--port", str(port)],
        cwd=tmp_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        one = two = three = b""
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                one = urlopen(f"http://127.0.0.1:{port}/one.html", timeout=.2).read()
                two = urlopen(f"http://127.0.0.1:{port}/two.html", timeout=.2).read()
                three = urlopen(f"http://127.0.0.1:{port}/folder/three.html", timeout=.2).read()
                if b"one.md" in one and b"two.md" in two and b"three.md" in three:
                    break
            except OSError:
                time.sleep(.05)
        assert b"one.md" in one and b"two.md" in two and b"three.md" in three
        with pytest.raises(OSError):
            urlopen(f"http://127.0.0.1:{port}/private.txt")
        (tmp_path / "folder/three.md").write_text("# Watched third page\n")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            three = urlopen(f"http://127.0.0.1:{port}/folder/three.html", timeout=.2).read()
            if b"Watched third page" in three:
                break
            time.sleep(.05)
        assert b"Watched third page" in three
    finally:
        process.terminate()
        log, _ = process.communicate(timeout=3)
    assert "preview: http://127.0.0.1:%d/one.html" % port in log
    assert "preview: http://127.0.0.1:%d/two.html" % port in log
    assert "preview: http://127.0.0.1:%d/folder/three.html" % port in log


def test_initial_watch_build_skips_newer_page(tmp_path: Path):
    source = tmp_path / "article.md"
    source.write_text("# Original\n")
    settings = Settings.single(source)
    Project(settings).build()
    output = source.with_suffix(".html")
    stamp = source.stat().st_mtime_ns + 1_000_000_000
    os.utime(output, ns=(stamp, stamp))
    source_text = output.read_text()
    result = Project(settings).build(skip_unchanged=True)
    assert result.written == [] and result.skipped == [output]
    assert output.read_text() == source_text
    assert result.page_dependencies == {source: {source}}
    forced = Project(settings.with_cli(force=True)).build(skip_unchanged=True)
    assert forced.written == [output] and not forced.skipped


def test_directory_assets_have_copy_links_and_update_under_watch(tmp_path: Path):
    source = tmp_path / "source"
    output = source / "html"
    (source / "assets").mkdir(parents=True)
    (source / "index.md").write_text("# Page\n")
    asset = source / "assets/data.txt"
    asset.write_text("before")
    (source / ".private.txt").write_text("hidden")
    (source / "_private.txt").write_text("hidden")
    (source / "md2html.json").write_text("{}")
    result = Project(Settings(input=source, output=output, project_root=source, recursive=True)).build()
    assert result.asset_dependencies[asset] == output / "assets/data.txt"
    assert (output / "assets/data.txt").read_text() == "before"
    assert not (output / ".private.txt").exists() and not (output / "_private.txt").exists()
    assert not (output / "md2html.json").exists()
    assert Project(Settings(input=source, output=output, project_root=source, recursive=True)).build().copied == []
    page_mtime = (output / "index.html").stat().st_mtime_ns

    process = subprocess.Popen(
        [sys.executable, "-m", "md2html2", "-r", str(source), "-o", str(output), "--watch"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        asset.write_text("after")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and (output / "assets/data.txt").read_text() != "after":
            time.sleep(.05)
        assert (output / "assets/data.txt").read_text() == "after"
        assert (output / "index.html").stat().st_mtime_ns == page_mtime
        assert not (output / "html").exists()
        assert process.poll() is None
    finally:
        process.terminate()
        process.wait(timeout=3)


def test_pyinstaller_build_and_install_workflow_is_declared():
    makefile = (Path(__file__).parents[1] / "makefile").read_text()
    project = (Path(__file__).parents[1] / "pyproject.toml").read_text()
    assert "install: pyinstaller" in makefile
    assert "--onefile" in makefile and "--copy-metadata md2html2" in makefile
    assert 'node_modules:node_modules' in makefile and "$(NPM) install" in makefile
    assert 'build = ["pyinstaller>=6"]' in project


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
        initial_mtime = source.with_suffix(".html").stat().st_mtime_ns
        time.sleep(.4)
        assert source.with_suffix(".html").stat().st_mtime_ns == initial_mtime
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
