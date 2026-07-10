from __future__ import annotations

from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest

from md2html2.cli import _server, main, parser, settings_from_args
from md2html2.project import Project
from md2html2.render import parse_frontmatter
from md2html2.settings import MathSettings, Settings, load_settings


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
    assert "<title>A useful title</title>" in output
    assert "<h1 id=\"a-useful-title\">" in output
    assert "tex-mml-chtml.js" not in output
    assert "Measure" in output and "reader-width" in output and "reader-type" in output


def test_frontmatter_title_and_yaml_types(tmp_path: Path):
    metadata, body = parse_frontmatter("---\ntitle: Named\ntags: [one, two]\n---\nBody\n")
    assert metadata == {"title": "Named", "tags": ["one", "two"]}
    assert body == "Body\n"
    output = build_one(tmp_path, "---\ntitle: Named\n---\n# Different\n")
    assert "<title>Named</title>" in output


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
    assert '<details class="source">' in output


def test_include_cycle_warns_without_aborting(tmp_path: Path):
    (tmp_path / "a.md").write_text("@include(b.md)\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("@include(a.md)\n", encoding="utf-8")
    source = tmp_path / "a.md"
    result = Project(Settings.single(source)).build()
    assert any("include cycle" in warning for warning in result.warnings)
    assert "Include cycle omitted" in result.written[0].read_text(encoding="utf-8")


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
    assert (cached[0] / "execution.json").is_file()
    assert list(cached[0].glob("*.py"))


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
    assert Path((workspace / "workspace.txt").read_text()) == workspace
    assert Path((workspace / "sourcedir.txt").read_text()) == tmp_path
    assert not (tmp_path / "example.out").exists()


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


def test_template_directory_and_companion_css_take_priority(tmp_path: Path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "page.html").write_text("<title>{{ page.title }}</title><style>{{ md2html.css }}</style>{{ content }}")
    (templates / "page.css").write_text("body{color:rebeccapurple}")
    output = build_one(tmp_path, "# Custom\n", templates=templates)
    assert "rebeccapurple" in output
    assert "reader-controls" not in output


def test_cli_short_flags_and_scaffolds(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch):
    source = tmp_path / "one.md"
    source.write_text("# One\n")
    args = parser().parse_args(["-erf", str(source)])
    settings = settings_from_args(args)
    assert settings.execute and settings.recursive and settings.regenerate
    monkeypatch.chdir(tmp_path)
    assert main(["--example-config"]) == 0
    assert (tmp_path / "md2html.config").is_file()
    assert main(["--example-json"]) == 0
    assert (tmp_path / "md2html.json").read_text().startswith("{")
    assert main(["--example-template", "-"]) == 0
    assert "<!doctype html>" in capsys.readouterr().out


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
    source.write_text("# Before\n")
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
        while time.monotonic() < deadline and not page_contains("Before"):
            time.sleep(.05)
        assert page_contains("Before")
        source.write_text("# After\n")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not page_contains("After"):
            time.sleep(.05)
        assert page_contains("After")
    finally:
        process.terminate()
        process.wait(timeout=3)
