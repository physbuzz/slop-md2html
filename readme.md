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
`md2html2`.

To build a portable single-file command and install it under
`~/.local/bin/md2html`:

```console
make pyinstaller
# Or build and install in one step:
make install
```

## Everyday commands

Build one self-contained page:

```console
md2html notes.md
md2html notes.md -o public/notes.html
```

Build several independent pages beside their sources, or collect them below
one output directory:

```console
md2html introduction.md chapter1.md appendix/notes.md
md2html introduction.md chapter1.md appendix/notes.md -o public
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
HTTP server. Watch mode uses filesystem notifications and rebuilds only pages
that depend on a changed file. `@src` files are direct dependencies;
`@include`, Liquid includes and layouts, and local CSS imports are followed
recursively. Rebuilding a page replaces its old watch rules, so removed
includes stop triggering it.

The initial watch build skips a page when its existing HTML is newer than its
Markdown source. Static files in directory builds have direct input-to-output
copy links, so changing `assets/image.png` updates the output copy without
rebuilding unrelated pages. Generated HTML, copied output assets,
`.md2html-cache`, and the output tree itself are excluded from observation.
When several scattered pages are served together, the preview server exposes
only their generated pages and copied assets and prints one link per page.

Render every Markdown file below a directory while preserving its relative
path:

```console
md2html -r notes -o html
```

Directory builds place common page CSS in `assets/md2html/page.css`; individual
file builds remain self-contained. Use `--shared-assets` to collect a list of
files under `html/` with the same external CSS behavior. Set
`"shared_assets": false` in a directory project's configuration when every
page should embed its own CSS instead. Build-time CommonHTML in a shared
directory also uses one adaptive stylesheet and local font directory.

The compact development command below executes examples, scans recursively,
and ignores cached execution results:

```console
md2html -erf ~/sicp/src -o ~/sicp/html
```

Build a configured native site:

```console
md2html --config md2html.json
md2html --config md2html.json --serve --port 4000
```

When the current directory or a parent contains `md2html.json`, the shorter
forms work too:

```console
md2html
md2html --serve
```

Run `md2html --help` for the complete option list.

## Writing pages

Standard Markdown headings, links, images, block quotes, tables, task lists,
fenced code, raw HTML, Obsidian `![[image.png]]` embeds, and Jekyll-style YAML
front matter are supported. Images and embedded videos are responsive in the
bundled page template.

```markdown
---
title: A Small Example
---

# A Small Example

Some text with `inline code` and $e^{i\pi}+1=0$.
```

If `title` is absent, the source filename becomes the document title. A fenced
code block is protected before template expressions are evaluated, so braces
from Mathematica and other languages remain literal:

````markdown
```wl
Partition[Range[8], 2] /. {{a_, b_} :> a + b}
```
````

Invalid TeX is left visible and reported as a warning; it does not prevent the
rest of the page from building.

Obsidian image embeds accept width, alternative text, and CSS classes. A plain
number is interpreted as pixels:

```markdown
![[figures/orbit.png|width=70%|alt=Orbital diagram|class=centered]]
![[figures/detail.png|480]]
```

## Directives

Directives occupy their own line. Relative paths are resolved from the file
that contains the directive, including nested includes, and then from the
project root when no local file exists.

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
one, and a directive without either flag displays normally. A single-line
`@src(` tag missing its closing parenthesis becomes a visible page error.

### Show inline source

```markdown
@src-begin(python, execute, expanded)
print(sum(range(10)))
@src-end
```

Inline source is display-only when it has neither cached output nor
`--execute`. The `execute` flag documents intent but never causes a program to
run without command-line or config permission.

## Executable content

`--execute` runs supported `@src` files and inline source blocks, then places
stdout immediately below the source. Python, POSIX shell, JavaScript, Racket,
C, C++, and Wolfram Language have conventional default commands. A missing
runtime, compilation error, nonzero exit, or timeout becomes a warning; the
page still builds.

Executable content gets an isolated, persistent workspace under a cache tree
that follows the website's output paths. For example, executable blocks in
`guide/index.html` use `.md2html-cache/pages/guide/index.html/`. Each block has
a source-content checksum subdirectory. The command runs there, so compiled
programs and files created with relative paths do not pollute the source tree.
Successful output is marked complete and cached; `--force` (or `-f`) reruns it
when execution is enabled.

Valid cached output is always included in the page, even without `--execute`.
The checksum depends only on the displayed source—not checkout paths, Python
or compiler locations, commands, settings, or cache format fields. This makes
`.md2html-cache` suitable for committing to a repository or restoring in
GitHub Actions. A cache-only build needs no language runtimes: install
md2html and its MathJax packages, restore or check out the cache, and build
normally without `--execute`.

```console
# Run from the website repository, where the cache is not ignored.
git add .md2html-cache
md2html --config md2html.json
```

Changing the source text selects a new cache entry. Changing checkout paths,
commands, runtimes, settings, or md2html metadata does not; use
`--execute --force` when one of those changes should refresh output. If
an `execute` block has no matching cache and execution is disabled, the page
still builds and reports how to populate it.

Commands can be added or replaced in configuration. `{source}`, `{output}`,
`{sourcedir}`, `{builddir}`, `{slug}`, `{executable}`, and `{python}` are
available in command strings. `{filename}` is an alias for `{source}`. For
`@src`, the source is relative to the workspace; inline source is staged there.
`{sourcedir}` is also relative, `{builddir}` is `.`, `{executable}` is a
`slug.md2html-out` path, and `{output}` is `output.txt`:

```json
{
  "timeout": 30,
  "commands": {
    "julia": "julia {source}",
    "cpp": "g++ {source} -o {executable} && {executable} > {output}"
  }
}
```

If a command creates `{output}`, its contents appear below the source.
Otherwise md2html uses stdout and saves it to `{output}`. Other generated files
remain in the workspace for inspection but are not copied into the website.
After a page is written, workspaces for blocks no longer on that page are
removed. A completed project build also removes cache trees for deleted pages.
Failed executable examples remain available for inspection and do not prevent
this cleanup; a page parse or rendering failure preserves its previous cache.

Only use executable content from sources you trust.
The execution timeout defaults to 120 seconds and can be changed with
`--timeout SECONDS` or the JSON `timeout` setting.

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
Build-time CommonHTML, MathML, and SVG keep a hidden copy of the original
delimited LaTeX beside the visual rendering. Selecting prose that contains
static math therefore copies `$...$` or `$$...$$` instead of presentation
glyphs.

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
from changing. Set `site.permalink` in `md2html.json` or `permalink` in page
front matter to choose a different path. A permalink ending in `/` writes
`index.html` below that path.

Native sites support:

- layouts in `_layouts` and includes in `_includes`;
- recursive layouts through a layout's own front matter;
- `site`, `page`, `content`, and `layout` Liquid variables;
- `site.posts`, `site.pages`, `site.tags`, `site.categories`, and
  `site.tag_list`;
- useful Liquid filters including `relative_url` and `absolute_url`;
- static file copying and a small Atom `feed.xml`;
- site metadata and exclusion lists from `md2html.json`.

These familiar names are intentional, but the native site pipeline does not
attempt to reproduce every Jekyll behavior.

## Configuration

Configuration uses one file name and one format: `md2html.json`. Paths are
resolved relative to that file, which makes a project runnable from any working
directory.

```json
{
  "input": ".",
  "output": "_site",
  "output_mode": "site",
  "templates": "templates",
  "template": "page.html",
  "css": ["styles/base.css"],
  "feature_css": true,
  "shared_assets": true,
  "highlight_style": "default",
  "highlight_dark_style": "github-dark",
  "timeout": 120,
  "math": {
    "backend": "mathjax-chtml",
    "chtml_fonts": "auto"
  },
  "execute": false,
  "exclude": ["drafts"],
  "site": {
    "title": "My technical notes",
    "url": "https://example.com"
  }
}
```

Top-level values not reserved for build settings also become `site` variables.
Use the explicit `site` object when keeping build and template settings visually
separate is helpful.

## Templates and CSS

Templates are looked up in the configured `templates` directory first, then in
the project's `_templates` directory, and finally in the installed defaults.
Native-site `_layouts` remain available after `_templates`; Liquid includes
also search `_includes`.

The standalone template receives:

- `content`: rendered article HTML;
- `page`: front matter plus `title`, `name`, `url`, and `path`;
- `site`: configured site values, often mostly empty for one file;
- `md2html.css`: the CSS selected for the page;
- `md2html.stylesheets`: external stylesheet URLs selected for the page;
- `md2html.use_mathjax`: whether the page needs browser math rendering.

With the default template, CSS is embedded so a single build remains a single
file. Pass `--css styles.css` more than once to replace and combine base CSS
files. Generated feature CSS for code, math, TOCs, images, and warnings is
still added; use `--no-feature-css` or `"feature_css": false` to omit it.
`--no-css` omits both groups. A custom `templates/report.html` automatically
uses `templates/report.css` when it exists and no explicit base CSS was
selected. `--stylesheet URL` adds an external stylesheet link.

Page front matter can override the project template and CSS without creating a
separate build:

```markdown
---
template: report
css:
  - styles/report.css
stylesheets:
  - styles/print.css
feature_css: true
---
```

The template is found using the same configured-directory, `_templates`, and
bundled lookup order. An empty `css: []` removes base CSS while retaining
feature CSS. A page with its own `template` or `css` embeds its selected styles
even when the rest of a directory uses shared assets.

The built-in page has a responsive reading measure, horizontal overflow for
wide code and equations, light/dark behavior, text-size and typeface controls,
and print-friendly semantic markup. The native controls and their eight
ID-specific CSS selectors work without JavaScript; JavaScript only remembers
their selections between pages.

Highlighted fences use a `codehilite` wrapper. Source directives use a
`code-box` containing `code-header`, `codehilite`, and, when execution produced
text, `code-output`. Explicitly collapsible source uses `collapsible-code`
inside that same outer box. The default page includes a light Pygments palette
and a dark counterpart. Choose them by Pygments style name with
`--highlight-style NAME` and `--highlight-dark-style NAME`, or the corresponding
JSON settings. These class names are stable hooks for custom CSS.

## Print the examples and documentation

The installed command can emit every useful starting point:

```console
md2html --example-config md2html.json
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
skipped pages, warnings, dependencies grouped by source page, and direct
source-to-output asset copy links.
Markdown and Liquid include cycles produce warnings and visible error markup
while the remaining website continues building.

## Design boundaries

The native pipeline deliberately has one representation of a page and one
content renderer. Standalone pages and sites differ in discovery, context, and
final templating—not in how Markdown, directives, math, or code behave. Site
models are complete before Liquid renders any page, so lists and taxonomies do
not depend on build order.

The package emits standalone HTML pages and native static sites. It does not
emit Jekyll Markdown or reproduce Jekyll as a separate rendering mode.
