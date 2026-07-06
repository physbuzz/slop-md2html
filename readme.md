# md2html

`md2html` is a small Python page builder for Markdown notes that need protected TeX math, Obsidian image embeds, recursive includes, compact exercise-aware tables of contents, source-code embedding, optional source execution, and static-site output.

The renderer pipeline is:

1. Parse YAML front matter.
2. Expand `@include(path)` recursively with dependency tracking and circular-include detection.
3. Convert Obsidian image embeds such as `![[img/diagram.svg|width=70%|class=center]]`.
4. Scan headings, generate stable slugs, and replace `@toc` with a compact directory.
5. Protect `$...$` and `$$...$$` math so Markdown formatting does not alter TeX.
6. Expand `@src(...)` and `@src-begin(...)` code directives with syntax highlighting and optional execution.
7. Render Markdown.
8. Restore math spans and wrap the output in a template.

## Install And Test

Install for local use:

```bash
python -m pip install .
```

Install for development:

```bash
python -m pip install -e ".[dev]"
```

Run the test suite:

```bash
python -m pytest -q
```

Build a single-file executable and copy it to `~/.local/bin/md2html`:

```bash
make install
```

The executable build bundles the default templates and CSS so output works the same from an installed package or a local source checkout.

## Project Layout

```text
md2html/   importable package and bundled runtime assets
tests/     test suite
examples/  demo Markdown, demo code, and rendered sample output
```

Rendered demos live in `examples/rendered/` so generated HTML does not sit beside package source.

The main package boundaries are:

```text
builder.py      document build orchestration and public result objects
cli.py          argument parsing, source discovery, and job planning
config.py       typed build options and config-file loading
context.py      per-build dependencies, diagnostics, assets, and path lookup
directives.py   shared @include/@src parsing plus include expansion
code.py         source embedding and optional source execution
graph.py        article-level dependency graph for dry-run/watch
rendering.py    Markdown rendering, TOC, slugs, math, images, highlighting, templates
paths.py        shared lenient path resolution and source-output paths
watch.py        rebuild loop and development server
```

## CLI Examples

```bash
md2html note.md
md2html note.md -o index.html
md2html file1.md file2.md -o html/
md2html -r src -o html
md2html -r . -o _site --serve
md2html note.md --dry-run
md2html note.md --format jekyll
md2html note.md --execute
md2html --config path/to/md2html.json
md2html --readme
md2html --example-config
md2html --example-layout
```

`md2html` reads `./md2html.json` automatically when it exists. Use `--config path/to/md2html.json` to pass a different file. Relative `input`, `output`, `project_root`, and template paths inside a config file are resolved from that config file's directory.

## Self-Contained Help

These commands are intended for people and tools that have the executable but not the repository open:

```bash
md2html --readme
md2html --example-config
md2html --example-layout
```

- `--readme` prints this README and exits.
- `--example-config [path]` writes a complete example config. The default path is `md2html.json`.
- `--example-layout [path]` writes a single-file HTML layout with the default stylesheet inlined. The default path is `templates/page.html`.
- Pass `-` as the path to print either example to stdout.
- Existing files are not overwritten unless `--force-rebuild` is also passed.

The generated layout is for md2html HTML output. For Jekyll output, use the `jekyll` config section to set front matter defaults such as `layout`, and customize your Jekyll site's layouts normally.

## HTML Templates

Bundled HTML templates live in `md2html/default_templates/` and are selected with the `template` config key or a page-level `template` front matter key:

- `super-barebones.html`: A near-plain HTML document. Its paired CSS only covers md2html-generated features such as code boxes, `@toc`, warnings, math overflow, and images.
- `barebones.html`: The simple page template with the original centered white reading panel and no reader controls.
- `page.html`: The default template. It includes an `Aa` reader control in the top right for theme, measure, and typeface preferences.

Each bundled template has its own bundled CSS file:

```text
super-barebones.html  ->  super-barebones.css
barebones.html        ->  barebones.css
page.html             ->  page.css
```

When `embed_assets` is true, `embedded_css` contains syntax-highlighting CSS plus the CSS selected for the active template. For a custom template, md2html looks for a same-name companion CSS file in `template_dirs`; for example, `templates/report.html` automatically embeds `templates/report.css` when it exists.

Override embedded CSS from config:

```json
{
  "template": "report.html",
  "template_dirs": ["templates"],
  "css": ["templates/report.css"]
}
```

Use `"css": null` or omit the key to use the selected template's default CSS. Use `"css": []` to embed only syntax-highlighting CSS. When `embed_assets` is false, `stylesheets` are emitted as `<link>` tags instead.

The default `page.html` template works with JavaScript disabled: it follows the system color scheme, uses normal width and sans-serif text by default, and still renders the page content and code blocks. In browsers with CSS `:has(...)` support, the visible radio controls can change theme, width, and typeface without JavaScript. The small script only persists settings and asks MathJax to re-typeset after a reader setting changes.

## Configuration

A single config file can drive both HTML output and Jekyll Markdown output. Put shared settings at the top level, put Jekyll-only settings under `jekyll`, and use `--format` plus `-o/--output` when you want a different output mode or destination for a particular run:

```bash
md2html --config md2html.json
md2html --config md2html.json --format jekyll -o jekyll
```

If you use the same `output` path for both modes, the generated `.html` and `.md` files will land under the same output root. Use separate output directories when you want to keep the two builds side by side.

A compact `md2html.json`:

```json
{
  "input": "notes",
  "output": "html",
  "recursive": true,
  "copy_assets": true,
  "embed_assets": true,
  "execute": false,
  "images": {
    "class": "note-image",
    "width": "70%"
  },
  "jekyll": {
    "layout": "post",
    "stylesheet": "assets/css/md2html.css"
  }
}
```

For a fuller starting point that includes every major section, run:

```bash
md2html --example-config
```

To customize the default HTML layout and CSS as one file, run:

```bash
md2html --example-layout
```

The generated config points at `templates/page.html`, so those two commands work together as a starting point.

Canonical top-level keys:

- `input`: Markdown file, directory, or list of files/directories to build. Aliases: `inputs`, `files`.
- `output`: Output file for one input, or output directory for multiple inputs/directories.
- `recursive`: Process directory inputs recursively.
- `project_root`: Base directory for includes, source embeds, assets, and relative template directories. Alias: `root`.
- `output_mode`: `"html"` or `"jekyll"`. Alias: `format`. The CLI `--format` option overrides this.
- `template_dirs`: Additional template directories. Alias: `templates`.
- `template`: HTML template name for HTML output. Defaults to `page.html`.
- `css`: Local CSS file or list of files to embed when `embed_assets` is true. `null` uses the selected template's default CSS.
- `stylesheets`: Stylesheet links emitted when `embed_assets` is false.
- `execute`: Run source files for `@src(...)` when their output files are missing or stale.
- `embed_assets`: Embed bundled CSS in HTML output. Alias: `embed_styles`.
- `copy_assets`: Copy referenced local assets next to generated pages.
- `no_overwrite`: Skip writes when an output file already exists.
- `force_rebuild`: Rebuild even when outputs or source execution results appear current.
- `strict`: Treat missing includes and source embeds as errors.
- `verbose`: Print built/skipped files and diagnostics.

Nested keys:

```json
{
  "math": {
    "backend": "mathjax"
  },
  "images": {
    "class": "note-image",
    "width": "70%"
  },
  "code": {
    "commands": {
      "py": "python {src}",
      "rkt": "racket {src}"
    },
    "timeout": 15,
    "output_suffix": ".out"
  },
  "jekyll": {
    "math": "passthrough",
    "layout": "post",
    "stylesheet": "assets/css/md2html.css",
    "highlight_fences": false,
    "frontmatter": {
      "render_with_liquid": false
    }
  }
}
```

- `math.backend`: Math renderer used by HTML output. The bundled template includes browser-side math rendering when this is `"mathjax"` and otherwise emits md2html math wrappers without loading a renderer.
- `images.class`: Default CSS class added to Obsidian image embeds. Alias: `class_name`. The alternate section name `obsidian_images` is also accepted.
- `images.width`: Default width for Obsidian image embeds.
- `code.commands`: Execution commands by file extension or language. Commands may use `{src}` for the source path and `{stem}` for the source path without its suffix.
- `code.timeout`: Execution timeout in seconds. A top-level `timeout` key is also accepted.
- `code.output_suffix`: Sibling output file suffix for source execution and cached output embedding.
- `jekyll.math`: `"passthrough"` keeps `$...$` and `$$...$$` in generated Markdown. `"html"` emits the same math wrappers as HTML output.
- `jekyll.layout`: Default layout for pages without a `layout` front matter key. Use `null` to omit it.
- `jekyll.stylesheet`: Generated stylesheet path relative to the output root. Use `null` to skip writing it.
- `jekyll.highlight_fences`: Convert Markdown fenced code blocks to highlighted HTML before Jekyll processes the page.
- `jekyll.frontmatter`: Front matter defaults merged into every generated page. Per-page front matter wins.

## Jekyll Output

`--format jekyll` writes Markdown files with YAML front matter so Jekyll can run its normal Markdown, layout, and styling pipeline.

- Each page keeps its own front matter. A configured default `layout` is added only when the page has none.
- One stylesheet covering md2html's generated markup is written under the output root unless `jekyll.stylesheet` is `null`.
- Files or directories whose names start with `_` are skipped as render sources. They are still copied as static files when `copy_assets` is enabled, matching Jekyll's private-path conventions.

With the default `jekyll.math: "passthrough"`, disable kramdown's math engine if your MathJax setup expects dollar delimiters:

```yaml
kramdown:
  math_engine: ~
```

Then configure MathJax for dollar delimiters:

```html
<script>
  window.MathJax = {
    tex: {
      inlineMath: [['$', '$']],
      displayMath: [['$$', '$$']],
      processEscapes: true
    }
  };
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
```

`examples/sicp-example/jekyll/` contains a working `_config.yml` and `_layouts/post.html` demonstrating this setup.

## Directives

### `@toc`

Place `@toc` on its own line. The builder scans Markdown headings and creates a `Directory`. Headings named `Solution` are skipped. Exercise headings are shown compactly inside the `Exercises` entry:

```md
@toc

## Section 2.5
### Exercises
#### Exercise 2.77
##### Solution
#### Exercise 2.78
```

### `@include(path)`

Includes are resolved relative to the current Markdown file first, then the project root. Included files may contain front matter; only the including page's front matter is used for the rendered page. Include cycles raise an error.

```md
@include(_partials/header.md)
```

### `@src(path[, flags...])`

Embeds a source file. If `--execute` is enabled, the source is run when the sibling output file is missing or older than the source. Otherwise, an existing sibling output file is reused. If execution is disabled and no output file exists, only the source is embedded.

```md
@src(code/ex2-77.rkt)              # expanded, not collapsible
@src(code/ex2-77.rkt, collapsible) # expanded, collapsible
@src(code/ex2-77.rkt, collapsed)   # collapsed, collapsible
@src(example.py, lang=python, caption="Runnable example")
```

Default execution commands are provided for Python, shell, Node, Racket, C, and C++. You can override or add commands in `md2html.json`; this is also how to run file types that md2html does not know about directly:

```json
{
  "code": {
    "commands": {
      "rkt": "racket {src}",
      "py": "python {src}",
      "wl": "wolframscript -file {src}"
    },
    "timeout": 10,
    "output_suffix": ".out"
  }
}
```

The watch graph records article-level edges such as `main.cpp -> page.md` and, when present, `main.out -> page.md`. It does not inspect language-level dependencies such as C/C++ headers or Racket imports.

### `@src-begin(lang, godbolt)`

Embeds an inline code block. Close with `@src-end`. Inline source blocks are display-only: they are highlighted but are not executed and do not use `code.commands`.

```md
@src-begin(cpp, godbolt)
#include <iostream>
int main(){ std::cout << "Hello, world!\n"; }
@src-end
```

### Obsidian Images

```md
![[img/ex3-10.svg|width=70%|alt=Environment diagram|class=centered]]
```

Width values ending in `%`, `px`, `em`, or `rem` become CSS widths. Plain numeric widths become HTML `width` attributes.

## Python API

```python
from pathlib import Path
from md2html import MarkdownSiteBuilder, BuildOptions

builder = MarkdownSiteBuilder(BuildOptions(project_root=Path.cwd()))
result = builder.build_file(Path("note.md"), Path("note.html"))
print(result.as_dict())
```

## Behavior And Limits

The dependency graph models Markdown `@include` relationships and direct article dependencies from `@src(...)` source/output files. It is intentionally an article rebuild graph, not a general language build graph.

Source execution runs local commands on the current machine. Keep `execute` disabled for untrusted notes or source files.

TODOs:

- Inline `@src-begin(...)` execution is not implemented. Use file-backed `@src(path)` blocks when output capture or custom commands are needed.
- Non-MathJax math output needs a renderer extension point before `math.backend` can produce SVG or MathML directly.
