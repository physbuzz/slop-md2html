# md2html 2.0

`md2html` turns Markdown into polished standalone HTML pages and native static
websites. It treats source code, program output, and mathematics as normal parts
of technical writing. The common case needs no project setup:

```console
md2html article.md
```

That command writes `article.html` next to `article.md` and creates nothing
else. The result contains its own responsive CSS. MathJax is added only when the
article uses math, and code styles are useful only when code appears.

## Install

md2html 2.0 requires Python 3.10 or newer.

```console
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
npm install
```

The installed command is named `md2html`. Its Python package is named
`md2html2`, so it can be developed beside the original implementation.

## Everyday commands

Build one self-contained page:

```console
md2html notes.md
md2html notes.md -o public/notes.html
```

Run source examples while building:

```console
md2html -e article.md
```

Build, serve, and rebuild a page whenever its source or an included file
changes:

```console
md2html -es article.md
```

The command prints a clickable loopback URL. Refresh the browser after an edit
to see the new page. Use `--watch` instead of `--serve` to rebuild without an
HTTP server.

Render every Markdown file below a directory while preserving its relative
path:

```console
md2html -r notes -o html
```

The compact development command below executes examples, scans recursively,
and ignores cached execution results:

```console
md2html -erf ~/sicp/src -o ~/sicp/html
```

Build a configured native site:

```console
md2html --config md2html.config
md2html --config md2html.config --serve --port 4000
```

When the current directory contains `md2html.config`, `md2html.yml`,
`md2html.yaml`, or `md2html.json`, the shorter forms work too:

```console
md2html
md2html --serve
```

Run `md2html --help` for the complete option list.

## Writing pages

Standard Markdown headings, links, images, block quotes, tables, task lists,
fenced code, raw HTML, and Jekyll-style YAML front matter are supported.

```markdown
---
title: A Small Example
---

# A Small Example

Some text with `inline code` and $e^{i\pi}+1=0$.
```

If `title` is absent, the first heading becomes the document title. A fenced
code block is protected before template expressions are evaluated, so braces
from Mathematica and other languages remain literal:

````markdown
```wl
Partition[Range[8], 2] /. {{a_, b_} :> a + b}
```
````

Invalid TeX is left visible and reported as a warning; it does not prevent the
rest of the page from building.

## Directives

Directives occupy their own line. Relative paths are resolved from the file
that contains the directive, including nested includes.

### Table of contents

`@toc` creates a linked table of contents from the page headings:

```markdown
# Notes

@toc

## First topic
## Second topic
```

### Include another Markdown file

```markdown
@include(parts/derivation.md)
```

Includes may contain directives of their own. Include cycles and missing files
produce a visible warning instead of aborting the build. Front matter inside an
included fragment is ignored.

### Show a source file

```markdown
@src(code/example.py)
@src(code/long-example.cpp, collapsed)
@src(code/important.rkt, expanded)
```

`collapsed` starts in a closed disclosure box, `expanded` starts in an open
one, and a directive without either flag displays normally.

### Show inline source

```markdown
@src-begin(python, execute, expanded)
print(sum(range(10)))
@src-end
```

Inline source is display-only unless the build also uses `--execute`. The same
is true for the `execute` flag: it documents intent but never causes a program
to run without the command-line or config permission.

## Executable content

`--execute` runs supported `@src` files and inline source blocks, then places
stdout immediately below the source. Python, POSIX shell, JavaScript, Racket,
C, C++, and Wolfram Language have conventional default commands. A missing
runtime, compilation error, nonzero exit, or timeout becomes a warning; the
page still builds.

Native sites cache successful output in `.md2html-cache`. `--regenerate` (or
`-f`) forces programs to run again. Standalone inline examples use temporary
files and do not create a cache directory.

Commands can be added or replaced in configuration. `{source}`, `{output}`,
and `{python}` are available in command strings:

```yaml
commands:
  julia: julia {source}
  txt: my-interpreter {source}
```

Only use executable content from sources you trust.

## Mathematics

Inline `$...$`, display `$$...$$`, and bare `align`, `gather`, `multline`, and
`equation` environments are protected before Markdown and Liquid rendering.
Escaped currency such as `\$5` remains text. Choose a backend on the command
line:

```console
md2html paper.md --math mathjax
md2html paper.md --math mathjax-chtml --math-fonts auto
md2html paper.md --math mathml
md2html paper.md --math svg
md2html paper.md --math raw
```

`mathjax` is the default and adds the browser renderer only to pages containing
math. `mathjax-chtml` renders static CommonHTML during the build and needs the
Node.js dependency installed above; a site shares one generated stylesheet,
while a standalone page embeds it. `mathml` and `svg` also render during the
build. `raw` preserves delimiters while still shielding them from Markdown.

Static CommonHTML supports five font modes through `--math-fonts` or
`math.chtml_fonts`:

- `auto` is the default. Sites copy and preload only fonts used by each page;
  standalone files use the matching CDN fonts so they remain one file.
- `all` copies every CommonHTML font into a site, while still preloading only
  those needed by a page.
- `inline` embeds used fonts as data URLs in the generated stylesheet.
- `remote` uses CDN fonts for both standalone pages and sites.
- `none` emits no font files or font-face rules.

The generated CommonHTML stylesheet contains only font faces used by the site.
Its glyph metrics are accumulated after typesetting, so static expressions have
the same dimensions as MathJax output rendered in the browser.

## Native sites

A site build discovers all Markdown recursively, evaluates the site model once,
and then renders pages and layouts. Markdown files outside `_posts` keep their
relative path with an `.html` suffix. Posts named
`_posts/YYYY-MM-DD-title.md` use dated URLs:

```text
_posts/2026-05-18-gaussianintegral.md
    -> /2026/05/18/gaussianintegral.html
```

This is the default post permalink and prevents existing Jekyll-style links
from changing. Set `permalink` in `_config.yml` or page front matter to choose a
different path. A permalink ending in `/` writes `index.html` below that path.

Native sites support:

- layouts in `_layouts` and includes in `_includes`;
- recursive layouts through a layout's own front matter;
- `site`, `page`, `content`, and `layout` Liquid variables;
- `site.posts`, `site.pages`, `site.tags`, `site.categories`, and
  `site.tag_list`;
- useful Liquid filters including `relative_url` and `absolute_url`;
- static file copying and a small Atom `feed.xml`;
- `_config.yml` site metadata and exclusion lists.

These familiar names are intentional, but the native site pipeline is not a
promise of complete Jekyll compatibility. Dedicated compatibility stages can
be added later without changing page discovery or content rendering.

## Configuration

JSON and YAML are supported. Paths are resolved relative to the configuration
file, which makes a config runnable from any working directory.

```yaml
input: .
output: _site
output_mode: site
templates: templates
template: page.html
math:
  backend: mathjax-chtml
  chtml_fonts: auto
execute: false
exclude:
  - drafts
site:
  title: My technical notes
  url: https://example.com
```

Top-level values not reserved for build settings also become `site` variables.
This allows an existing `_config.yml` and a small `md2html.config` to work
together cleanly.

## Templates and CSS

Templates are looked up in the configured `templates` directory first and in
the installed defaults second. Native-site layouts and includes are looked up
in `_layouts` and `_includes` before those directories.

The standalone template receives:

- `content`: rendered article HTML;
- `page`: front matter plus `title`, `url`, and `path`;
- `site`: configured site values, often mostly empty for one file;
- `md2html.css`: the CSS selected for the page;
- `md2html.use_mathjax`: whether the page needs browser math rendering.

With the default template, CSS is embedded so a single build remains a single
file. Pass `--css styles.css` more than once to combine custom files, or
`--no-css` for no embedded CSS. A custom `templates/report.html` automatically
uses `templates/report.css` when it exists and no explicit CSS was selected.

The built-in page has a responsive reading measure, horizontal overflow for
wide code and equations, light/dark behavior, accessible reader controls, and
print-friendly semantic markup.

## Print the examples and documentation

The installed command can emit every useful starting point:

```console
md2html --example-config md2html.config
md2html --example-json md2html.json
md2html --example-template templates/page.html
md2html --example-css templates/page.css
md2html --readme
```

Use `-` as an example destination to print it to stdout. Existing files are not
replaced unless `--force` is present.

## Python API

The command line is a thin layer over two public objects:

```python
from pathlib import Path
from md2html2 import Project, Settings

settings = Settings.single(Path("article.md"))
result = Project(settings).build()
print(result.written)
```

`Settings` is immutable. `Project.build()` returns written files, copied files,
warnings, and discovered dependencies, which is enough for other tools to add
their own reporting or watch strategy.

## Design boundaries

The native pipeline deliberately has one representation of a page and one
content renderer. Standalone pages and sites differ in discovery, context, and
final templating—not in how Markdown, directives, math, or code behave. Site
models are complete before Liquid renders any page, so lists and taxonomies do
not depend on build order.

The current release does not provide Jekyll-Markdown output or claim complete
Jekyll compatibility. Those are future adapters around the native page model,
not alternate foundations hidden inside the renderer.
