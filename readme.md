# md2html

`md2html` turns Markdown notes into standalone HTML pages or Jekyll-ready Markdown. It is aimed at notes that use TeX math, `@toc`, `@include`, Obsidian-style image embeds, and source-code snippets with optional execution.

Each page is built in a fixed order: parse front matter, expand `@include` recursively, convert Obsidian image embeds, replace `@toc` with a heading directory, protect `$...$` and `$$...$$` math so Markdown does not alter TeX, expand `@src` code directives, render Markdown, then restore the math and wrap the result in a template with the CSS and scripts the page needs.

## Quick Orientation

Docs and this readme can be printed to the CLI using the following commands.

```bash
md2html -h                  # all CLI options
md2html --readme            # print this README
md2html --example-config -  # print a complete starter config to stdout
md2html --example-layout -  # print the default single-file HTML layout to stdout
```

## Install

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

## CLI

```bash
# Generate test.html with the default template and inlined CSS.
md2html test.md

# Generate index.html instead.
md2html test.md -o index.html

# Build every Markdown file under src/ into html/.
md2html -r src -o html

# Execute @src blocks, force fresh outputs, watch for edits, and serve html/.
md2html -erf src -o html --watch

# Serve a generated site while rebuilding on change.
md2html -r . -o _site --serve

# Build Jekyll-ready Markdown instead of HTML.
md2html -r src --format jekyll -o jekyll

# Preview the build plan without writing files.
md2html test.md --dry-run

# Use a different HTML template for one run.
md2html --override-template barebones.html test.md -o test-barebones.html

# Use settings from another config file.
md2html --config path/to/md2html.json
```

With one input and no `-o`, output is written beside the source with an `.html` suffix. With one input and `-o page.html`, that file is used. With several inputs, or a directory input and `-o html`, relative source paths are preserved under the output directory.

`--watch` and `--serve` both start a local server and rebuild when watched files change. `-erf` is the short form of `--execute --recursive --force-rebuild`.

## Config

`md2html` reads `./md2html.json` automatically when it exists. Use `--config path/to/md2html.json` to pass a different file. Relative `input`, `output`, `project_root`, and template paths inside a config file are resolved from that config file's directory.

A compact config:

```json
{
  "input": "src",
  "output": "html",
  "recursive": true,
  "copy_assets": true,
  "embed_assets": true,
  "execute": false,
  "images": {
    "class": "note-image",
    "width": "70%"
  },
  "code": {
    "commands": {
      "wl": "wolframscript -file {src}"
    },
    "timeout": 15,
    "output_suffix": ".out"
  },
  "jekyll": {
    "layout": "post",
    "stylesheet": "assets/css/md2html.css"
  }
}
```

Common top-level keys:

- `input`: Markdown file, directory, or list of files/directories to build.
- `output`: Output file for one input, or output directory for multiple inputs/directories.
- `recursive`: Process directory inputs recursively.
- `project_root`: Base directory for includes, source embeds, assets, and relative template directories.
- `output_mode`: `"html"` or `"jekyll"`. The CLI `--format` option overrides this.
- `template_dirs`: Additional template directories.
- `template`: HTML template name for HTML output. Defaults to `page.html`.
- `css`: Local CSS file or list of files to embed when `embed_assets` is true. `null` uses the selected template's default CSS; `[]` disables template CSS.
- `feature_css`: Include automatic CSS for generated features used by the page. Defaults to `true`.
- `stylesheets`: Stylesheet links emitted by templates. Use this when `embed_assets` is false.
- `execute`: Run file-backed `@src(...)` blocks when their output files are missing or stale.
- `embed_assets`: Embed selected CSS in HTML output.
- `copy_assets`: Copy referenced local assets next to generated pages.
- `no_overwrite`: Skip writes when an output file already exists.
- `force_rebuild`: Rebuild even when outputs appear current. When `execute` is enabled, this also refreshes source execution outputs.
- `strict`: Treat missing includes and source embeds as errors.
- `verbose`: Print built/skipped files and diagnostics.

Nested keys:

- `math.backend`: `mathjax` loads browser-side math rendering for pages that contain math. Other values emit math wrappers without loading a renderer.
- `images.class`: Default CSS class added to Obsidian image embeds.
- `images.width`: Default width for Obsidian image embeds.
- `code.commands`: Execution commands by file extension or language. Commands may use `{src}` for the source path and `{stem}` for the source path without its suffix.
- `code.timeout`: Execution timeout in seconds.
- `code.output_suffix`: Sibling output file suffix for source execution and cached output embedding.
- `code.highlight_style`: Pygments style name for light syntax highlighting.
- `code.highlight_dark_style`: Pygments style name for dark syntax highlighting. Use `null` to omit dark token CSS.
- `jekyll.math`: `"passthrough"` keeps `$...$` and `$$...$$` in generated Markdown. `"html"` emits the same math wrappers as HTML output.
- `jekyll.layout`: Default layout for pages without a `layout` front matter key. Use `null` to omit it.
- `jekyll.stylesheet`: Generated stylesheet path relative to the output root. Use `null` to skip writing it.
- `jekyll.highlight_fences`: Convert Markdown fenced code blocks to highlighted HTML before Jekyll processes the page.
- `jekyll.frontmatter`: Front matter defaults merged into every generated page. Per-page front matter wins.

For a complete starter config:

```bash
md2html --example-config
```

## Built-In Starters

```bash
# Print this README from the installed command.
md2html --readme

# Write a starter config to md2html.json.
md2html --example-config

# Write an editable single-file HTML layout to templates/page.html.
md2html --example-layout
```

Pass a path to `--example-config` or `--example-layout` to choose another destination. Pass `-` as the path to print the generated file to stdout. Existing files are not overwritten unless `--force-rebuild` is also passed.

## Templates And CSS

HTML output uses `page.html` by default. The built-in templates are:

- `super-barebones.html`: A near-plain HTML document. Pages still get CSS for generated features they use.
- `barebones.html`: A simple centered reading page without reader controls.
- `page.html`: The default reading page with title, theme, width, and typeface controls.

Use `--override-template barebones.html` for one run, set `"template"` in config, or set `template` in page front matter. Use `--templates templates` to add a custom template directory; for example, `templates/report.html` can have a same-name `templates/report.css` companion file.

When `embed_assets` is true, CSS is inlined in the generated HTML. Template CSS is included by default, and generated feature CSS is included only for features the page uses. The feature names, as they appear in the `features` and `uses` template variables, are: `inline_code`, `code_highlight`, `code_box`, `collapsible_code`, `code_output`, `toc`, `math`, `image`, `obsidian_image`, and `warning`.

Use `"css": ["templates/report.css"]` to replace the selected template's default CSS. Use `"css": []` to disable template CSS while keeping feature CSS. Set `"feature_css": false` to disable feature CSS too. When `embed_assets` is false, `embedded_css` is empty; add stylesheet links with `stylesheets`.

Custom templates can use these variables:

- `content`: Rendered page body HTML.
- `title`: Front matter title, first `#` heading, or source filename.
- `metadata` and `frontmatter`: Page front matter.
- `embedded_css`: Inline CSS selected for this page.
- `stylesheets`: Stylesheet hrefs to emit as `<link>` tags.
- `features`: Sorted list of active feature names.
- `uses`: Feature flags such as `uses.math` or `uses.code_box`.
- `use_mathjax`: True only when the page contains math and `math.backend` is `mathjax`.
- `header_title`: Front matter title when present, otherwise the source filename.
- `source_name`: Source filename.
- `lang`: Page language, defaulting to `en`.
- `layout`: Page layout metadata, defaulting to `post`.

To customize the default layout and CSS as one file:

```bash
md2html --example-layout
```

## Directives

Put directives on their own lines.

### `@toc`

`@toc` is replaced with a compact `Directory`. Headings named `Solution` are skipped. Exercise headings are grouped inside the `Exercises` entry.

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

Embeds a source file with syntax highlighting. Without execution, an existing sibling output file is embedded when present; otherwise only the source appears. With `--execute` or `"execute": true`, md2html runs the source when the sibling output file is missing, older than the source, or `--force-rebuild` is used.

```md
@src(code/ex2-77.rkt)              # expanded, not collapsible
@src(code/ex2-77.rkt, collapsible) # expanded, collapsible
@src(code/ex2-77.rkt, collapsed)   # collapsed, collapsible
@src(example.py, lang=python, caption="Runnable example")
```

Default execution support covers Python, shell scripts, JavaScript, Racket/Scheme, C, and C++ when the needed tools are installed. Add or override commands in `md2html.json`:

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

### `@src-begin(lang[, flags...])`

Embeds an inline source block. Close it with `@src-end`. Inline source blocks are display-only: they are highlighted but are not executed, do not read cached output, and do not use `code.commands`.

```md
@src-begin(cpp, godbolt)
#include <iostream>
int main(){ std::cout << "Hello, world!\n"; }
@src-end
```

The `godbolt` flag adds a link to Compiler Explorer.

### Obsidian Images

```md
![[img/ex3-10.svg|width=70%|alt=Environment diagram|class=centered]]
```

Width values ending in `%`, `px`, `em`, or `rem` become CSS widths. Plain numeric widths are treated as pixels. Local image assets are copied next to generated pages when `copy_assets` is true.

## Jekyll Output

`--format jekyll` writes Markdown files with YAML front matter so Jekyll can run its normal Markdown, layout, and styling pipeline.

- Each page keeps its own front matter. A configured default `layout` is added only when the page has none.
- One stylesheet covering md2html's generated markup is written under the output root unless `jekyll.stylesheet` is `null`.
- Files or directories whose names start with `_` are skipped as render sources. They are still copied as static files when `copy_assets` is enabled.

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

## Python API

```python
from pathlib import Path
from md2html import MarkdownSiteBuilder, BuildOptions

builder = MarkdownSiteBuilder(BuildOptions(project_root=Path.cwd()))
result = builder.build_file(Path("note.md"), Path("note.html"))
print(result.as_dict())
```

## Behavior And Limits

The dependency graph models Markdown `@include` relationships and direct article dependencies from `@src(...)` source/output files. It is an article rebuild graph, not a general language build graph.

Source execution runs local commands on the current machine. Keep `execute` disabled for untrusted notes or source files.
