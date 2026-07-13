# md2html 2.0

`md2html` turns Markdown notes into standalone HTML pages, a small static site,
or Markdown for Jekyll to finish. It's aimed at quick math notes, so on my personal computer I can do
`md2html notes.md && upload notes.html` and have a shareable link to a beautiful
standalone webpage ready.

The reason for making Yet Another Static Website Generator is to add some
creature comforts and the ability to execute code snippets (which is handy if,
say, you're solving 200 problems in a textbook and so have 200 short C++ or
Racket files to run) if the `--execute` flag is enabled. There are also the
directives `@toc` for printing a table of contents, `@include` for including
other Markdown, `![[foo.png]]` for Obsidian-style image embeds,
`@src(file.cpp, collapsed)` for a collapsed code snippet box that can show the
`stdout` of `file.cpp`, and `@src-begin(cpp, execute)` for inline runnable
examples.

Basically, if I'm solving problems in SICP or Knuth I do
`md2html -erf knuth -o html --serve` and can see my solutions update in real
time as I write. If I write a math note then (because mathb.in got flooded with
spam) I just do `md2html note.md && upload note.html`.

A note on philosophy: md2html prefers to finish the build. Invalid TeX, a
missing include, a Liquid error, or a failed program run becomes a terminal
warning and a visible note in the page rather than a halt. It also tries not
to do too much: there are no plugins, it never downloads remote resources
during a build, and it never publishes a file you didn't reference.

The command documents itself:

```bash
md2html -h                    # print all CLI options
md2html --readme              # print this README
md2html --example-config -    # print starter JSON to stdout
md2html --example-template -  # print the default page template to stdout
md2html --example-css -       # print editable default CSS to stdout
```

Pass a path instead of `-` to write a file. Existing files are only replaced
when `--force` is present.

## Install

md2html requires Python 3.10 or newer:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install /path/to/md2html
```

Pygments highlighting and the MathML and SVG math backends work out of the
box. Two features need external tools, only when selected:

- Rouge highlighting: install Ruby, then `gem install --user-install rouge`.
- MathJax in a Python-package installation: install Node.js, then in the
  project directory run
  `npm install mathjax@4.1.3 @mathjax/mathjax-tex-font@4.1.3 @mathjax/mathjax-newcm-font@4.1.3`.
  md2html searches the project directory and its parents for `node_modules`,
  so an installed wheel works without a source checkout.

Selecting a backend whose tools are missing stops the build with a clear
error. With no optional tools installed, use `--math mathml`, `--math svg`,
`--math raw`, or `--math mathjax --assets cdn`.

### Development

```bash
python -m pip install -e ".[dev]"   # editable install with test dependencies
python -m pytest -q                 # run the tests
make pyinstaller                    # build a single-file executable
make install                        # build and copy it to ~/.local/bin/md2html
make clean                          # remove packaging and test artifacts
```

The executable installed by `make install` bundles md2html's Python packages,
templates, CSS, scripts, and npm MathJax packages. It can run from any working
directory without a local `node_modules`; static CommonHTML still needs the
`node` executable on the machine that builds pages.

## CLI

```bash
# Generate test.html with the default template and inlined CSS.
md2html test.md

# Generate index.html instead.
md2html test.md -o index.html

# Render Liquid in an HTML file without applying Markdown or a page template.
md2html page.html -o public/page.html

# Generate three independent pages beside their sources.
md2html introduction.md chapter1.md appendix/notes.md

# Preserve those relative paths below public/.
md2html introduction.md chapter1.md appendix/notes.md -o public

# Build every Markdown file under src/ into html/.
md2html -r src -o html

# Rebuild every page, rerun every executable example, serve, and watch.
md2html -erfF src -o html --serve

# Watch and rebuild without starting a local server.
md2html -r src -o html --watch

# Build a configured static site.
md2html --config md2html.json

# Serve that site while rebuilding on change.
md2html --config md2html.json --serve --port 4000

# Build and serve an existing Jekyll source tree without Ruby Jekyll.
md2html --jekyll website -o _site --serve

# Expand md2html syntax, but leave Markdown, Liquid, and layouts for Jekyll.
md2html --jekyll-markdown notes -o website/notes --execute

# In a directory that has md2html.json, build with no arguments.
md2html

# Use a different HTML template for one run.
md2html --template barebones.html test.md -o test-barebones.html

# Replace the base CSS and keep generated feature CSS.
md2html --css styles/base.css test.md

# Choose a math renderer or CommonHTML font mode.
md2html --math mathjax test.md -o test-browser-mathjax.html
md2html --math svg test.md -o test-svg.html
md2html --math mathml test.md -o test-mathml.html
md2html --math mathjax-chtml --math-fonts auto test.md -o test-chtml.html

# Embed every renderer asset in each page, or share local files across a site.
md2html --standalone test.md
md2html --assets shared notes -o html

# Use remote renderer assets explicitly.
md2html --assets cdn --math-fonts remote test.md
```

With one Markdown file and no `-o`, md2html writes an `.html` file beside the
source. HTML, HTM, and XML inputs keep their suffixes, so pass `-o` (or build
a directory) to keep the source and generated file separate; a page whose
destination would overwrite its source is skipped with a warning. Several inputs with `-o
public` preserve their paths relative to their common directory below
`public`. Default output directories per mode: page directories write to
`html`, sites to `_site`, Jekyll Markdown to `markdown`.

When `-o` moves a page away from its source, md2html copies the local images,
media, `@src` sources, and stylesheets the page references below the output
directory, preserving the paths written in the page. Remote URLs, fragment
links, `data:` URLs, and `mailto:` links are left alone.

Options, with their JSON configuration equivalents where one exists:

- `-o, --output PATH`: output file or directory. JSON: `"output"`.
- `-e, --execute`: run executable source and show its standard output.
  JSON: `"execute": true`.
- `-r, --recursive`: include nested documents in page mode. The other modes
  are recursive by default. JSON: `"recursive": true`.
- `-f, --force`: rebuild pages the initial watch timestamp check would skip;
  also lets the `--example-*` commands replace existing files.
  JSON: `"force": true`.
- `-F, --force-execution`: rerun completed execution caches. Requires
  `--execute`; `-eF` reruns everything. JSON: `"force_execution": true`.
- `-s, --serve`: build, rebuild on change, and serve the generated pages on a
  loopback-only (`127.0.0.1`) server.
- `-w, --watch`: rebuild on change without starting a server.
- `-p, --port N`: preview server port. The default is 8000.
- `--config PATH`: select a JSON configuration file explicitly.
- `--output-mode MODE`: `pages`, `site`, `jekyll`, or `jekyll-markdown`.
  `--jekyll` and `--jekyll-markdown` select the last two directly.
  JSON: `"output_mode"`.
- `--templates DIR`: template search directory; repeat to add more.
  JSON: `"templates"`.
- `--template NAME`: standalone page template. The default is `page.html`.
  JSON: `"template"`.
- `--css FILE`: replace the template's base CSS; repeat to combine files.
  JSON: `"css"` (a path or list; `[]` means no base CSS).
- `--stylesheet HREF`: add a stylesheet link; repeat for more.
  JSON: `"stylesheets"`.
- `--assets MODE`: `shared`, `standalone`, or `cdn` renderer-asset placement.
  `--standalone` is an alias for `--assets standalone`. One input file
  defaults to `standalone`; directories and multiple inputs default to
  `shared`. JSON: `"assets"`.
- `--embed-images`: embed local `<img>` sources as data URLs in generated HTML.
  JSON: `"embed_images": true`.
- `--no-css`: omit base and feature CSS. JSON: `"css": []` plus
  `"feature_css": false`.
- `--no-feature-css`: omit generated CSS for code, math, tables of contents,
  images, and warnings. JSON: `"feature_css": false`.
- `--no-minify-css`: leave generated CSS readable. JSON: `"minify_css": false`.
- `--no-liquid`: leave Liquid unchanged in source documents; templates and
  layouts still render. JSON: `"parse_liquid": false`.
- `--highlighter NAME`: `pygments` (default) or `rouge`. JSON: `"highlighter"`.
- `--highlighter-style NAME`, `--highlighter-dark-style NAME`: light and dark
  token styles from the active highlighter. Pygments defaults to `default` and
  `github-dark`; Rouge to `github.light` and `github.dark`.
  JSON: `"highlighter_style"`, `"highlighter_dark_style"`.
- `--math BACKEND`: `mathjax`, `mathjax-chtml` (default), `svg`, `mathml`, or
  `raw`. JSON: `"math": {"backend": ...}`.
- `--math-fonts MODE`: CommonHTML font handling; see
  [CommonHTML Fonts](#commonhtml-fonts). JSON: `"math": {"chtml_fonts": ...}`.
- `--timeout SECONDS`: per-command execution timeout. The default is 120.
  JSON: `"timeout"`.
- `--clean`: remove a site output directory before building. It does not
  apply to independent page builds. JSON: `"clean": true`.
- `--version`, `--help`.

Command-line settings override JSON settings; boolean CLI options only turn
their behavior on.

## Configuration

The configuration file is always named `md2html.json`. When no input or
`--config` is given, md2html searches the current directory and its parents
for it; when one directory is given, it also searches from that directory.
Paths inside the file are resolved relative to the file's directory, so the
same command works from anywhere.

A minimal site configuration:

```json
{
  "input": ".",
  "output": "html",
  "output_mode": "pages",
  "execute": true,
  "assets": "shared",
  "math": { "backend": "mathjax-chtml" }
}
```

`md2html --example-config -` prints a fuller starter. Most keys mirror a CLI
option and are listed with it above. The remaining keys exist only in JSON:

| Key | Meaning |
| --- | --- |
| `input` | Markdown file or source directory. |
| `exclude` | Skip matching source paths. Exact paths, directory prefixes, and patterns are accepted. |
| `frontmatter` | Default front matter for Jekyll Markdown output. Source front matter wins. |
| `paginate` | Site variable giving the posts per paginated `index.html` page. |
| `paginate_path` | Site variable giving the later-page URL; must contain `:num`. Default `/page:num/`. |
| `images.class` | Default class names for Obsidian images. Per-image classes are appended. |
| `images.width` | Default Obsidian image width. A per-image width wins. |
| `commands` | Add or replace execution commands by language name or extension. |
| `site` | Site variables for templates (`title`, `url`, `baseurl`, `permalink`, ...). |

All other top-level keys also become `site` variables. The built-in defaults
define `site.title`, `site.description`, `site.url`, and `site.baseurl`;
templates may use any additional values you provide. `paginate` and
`paginate_path` may equivalently be placed inside the `site` object, matching
their use as Jekyll-style site data.

## Writing Pages

Markdown files use md2html's complete renderer: CommonMark plus tables, task
lists, strikethrough, automatic URLs, raw HTML, math, and the `@` directives.
The bundled CSS makes images, videos, SVG, and embedded YouTube iframes
responsive.

HTML, HTM, and XML files take a smaller path: front matter is read, Liquid is
rendered, and an explicitly selected site layout may wrap the result. No
Markdown, math delimiters, Obsidian syntax, or `@` directives are interpreted
in these files, and XML never acquires an `.html` suffix.

Start a page with YAML front matter when it needs metadata or page-specific
styling:

```markdown
---
title: A Small Example
template: page
css:
  - styles/note.css
stylesheets:
  - styles/print.css
---

# A Small Example

Some text with `inline code` and $e^{i\pi}+1=0$.
```

Front matter keys:

| Key | Meaning |
| --- | --- |
| `title` | Page title. The source filename is used when absent. |
| `template` | Standalone page template for this page. |
| `css` | Replace base CSS for this page. `[]` keeps only feature CSS. |
| `stylesheets` | Add stylesheets for this page. |
| `feature_css` | Enable or disable generated feature CSS for this page. |
| `render_with_liquid` | `false` leaves Liquid in this document unchanged. |
| `layout` | Static-site layout from `_layouts`. Layouts may chain. |
| `permalink` | Static-site URL and output path. A trailing slash writes `index.html`. |
| `date` | Post date. ISO strings and YAML dates are accepted. |
| `tags`, `categories` | Post groups. Strings and lists are accepted. |
| `published` | `false` omits the page in Jekyll compatibility mode. |

Pages may use Liquid such as `{{ page.title }}` and `{{ site.title }}`. Code
and math are protected before Liquid runs, so braces in Mathematica and other
languages stay literal; use `{% raw %}...{% endraw %}` to protect anything
else. `--no-liquid` (or `"parse_liquid": false`) turns Liquid off for all
source documents, and a single page can opt out with
`render_with_liquid: false` — either way templates and layouts still render
and insert the document through `{{ content }}` as-is.

Invalid TeX, missing includes, missing source files, Liquid errors, and
execution failures produce warnings and leave the rest of the page buildable.
Invalid YAML front matter and mismatched `@src-begin`/`@src-end` markers stop
the build.

### Obsidian Images

```markdown
![[img/ex3-10.svg|width=70%|alt=Environment diagram|class=centered]]
![[img/detail.png|480]]
```

Widths ending in `%`, `px`, `em`, or `rem` become CSS widths; plain numbers
mean pixels. The first unlabelled non-width field becomes the alt text; use
`alt=` and `class=` when explicit names are clearer. `images.class` and
`images.width` set project defaults.

## Directives

Put directives on their own lines. Relative paths resolve from the file
containing the directive first, then from the project root — including inside
nested includes.

### `@toc`

Replaced with a compact `Directory` of the page's headings. Headings named
`Solution` are skipped, and `Exercise ...` headings are grouped inside the
`Exercises` entry:

```markdown
@toc

## Section 2.5
### Exercises
#### Exercise 2.77
##### Solution
#### Exercise 2.78
```

Links use lowercase slugs; repeated headings get `-2`, `-3`, ... suffixes.

### `@include(path)`

```markdown
@include(_partials/header.md)
```

Includes may contain directives and further includes. Front matter in an
included file is discarded; only the page's own front matter applies. Missing
files and include cycles produce a warning in the terminal and in the page.
Watch mode follows includes recursively.

### `@src(path[, flags...])`

Embed a source file with syntax highlighting:

```markdown
@src(code/ex2-77.rkt)
@src(code/ex2-77.rkt, collapsed)
```

Flags: `collapsible` and `expanded` show a collapsible box that starts open,
`collapsed` starts closed, and `noexecute` prevents execution and cached
program output lookup for the block. The file extension selects the language.
With execution enabled, the block runs and its standard output appears below
the source; without it, a completed cache is still displayed.

The generated heading links to the source file, and builds copy the source
next to the generated page so the link keeps working. A single-line `@src(` with no
closing parenthesis becomes a large visible error without stopping the page.

### `@src-begin(lang[, flags...])`

Embed an inline source block, closed by `@src-end`:

```markdown
@src-begin(cpp, execute, expanded)
#include <iostream>
int main() { std::cout << "Hello, world!\n"; }
@src-end
```

Inline blocks accept the same display flags. The `execute` flag only records
that the example is meant to run — nothing executes without `--execute`. With
execution enabled, inline blocks run unless `noexecute` is present.

## Executable Content

md2html never executes source by default. Enable it only for files you trust:

```bash
md2html --execute article.md
```

Python, shell (bash), JavaScript, Racket, Wolfram Language, C, and C++ have
default commands; the corresponding interpreter or compiler must be on
`PATH`. A missing program, compile error, nonzero exit, or timeout produces a
warning and the build continues.

Each block runs in a persistent workspace below
`SOURCE_DIRECTORY/.md2html-cache/PAGE_NAME/LANGUAGE-NAME-CHECKSUM/`, where the
checksum is of the source text alone. Inline source is copied into its
workspace; file-backed source stays where it is, with its executable and
cached program output owned by the page containing the directive. The working
directory is the page's directory, so programs can read local data files.

Because the cache key is only the source text, changing a command, compiler,
or data file does not invalidate it — use `-eF` (`--execute
--force-execution`) to rerun everything after such a change.

Successful standard output is saved as `output.txt` and included in later
builds even when execution is disabled, so a CI job can restore
`.md2html-cache` and build pages without compilers. Builds with execution
disabled never delete cached workspaces; with execution enabled, workspaces a
page no longer uses are removed after a successful render.

### Commands And Program Output

Add or replace commands in `md2html.json`, keyed by language name (for inline
blocks) or file extension without the dot (for file source):

```json
{
  "timeout": 30,
  "commands": {
    "julia": "julia {source}",
    "cpp": "g++ {source} -o {executable} && {executable} > {output}"
  }
}
```

Command strings accept:

| Field | Value |
| --- | --- |
| `{source}`, `{filename}` | Source path relative to the page directory. |
| `{sourcedir}` | Original source directory. |
| `{builddir}` | Page-owned workspace. |
| `{slug}` | Safe source stem or inline language name. |
| `{executable}` | `SLUG.md2html-out` inside the workspace. |
| `{output}` | `output.txt` inside the workspace. |
| `{python}` | The Python interpreter running md2html. |

The command runs through `sh` with the page directory as its working
directory. If it creates `{output}`, that file is used; otherwise standard
output is saved there. Standard error appears in failure messages only.

## Math Rendering

md2html recognizes inline `$...$`, display `$$...$$`, and bare `align`,
`gather`, `multline`, and `equation` environments (including starred forms),
protecting them before Markdown and Liquid run. Escaped currency like `\$5`
stays text.

```bash
md2html --math mathjax-chtml note.md   # the default: static CommonHTML
md2html --math mathjax note.md         # browser-side MathJax
md2html --math svg note.md             # inline SVG
md2html --math mathml note.md          # inline MathML
md2html --math raw note.md             # keep the TeX delimiters as-is
```

`mathjax-chtml` runs MathJax under Node at build time and writes static
CommonHTML. It is the default rather than MathML because, although native
MathML is compact and dependency-free, browser MathML typesetting is simply
too ugly — CommonHTML looks like TeX everywhere. MathML also covers less
LaTeX; when conversion fails, md2html warns and leaves that equation as TeX.
SVG output is self-contained, uses `currentColor` so it follows light/dark
themes, and needs no fonts or JavaScript, but repeated path data makes
equation-heavy pages much larger. If any build-time renderer rejects an
expression, it is left as LaTeX with a warning.

Static CHTML, SVG, and MathML output each include a hidden copy of the
original LaTeX, so copying prose that contains equations copies the TeX
source rather than generated markup.

### Asset Placement

Set `--assets MODE` or the `assets` key:

| Mode | Behavior |
| --- | --- |
| `standalone` | Embed generated CSS, CommonHTML fonts, and configured local stylesheets in every page. |
| `shared` | Write reusable renderer assets below `assets/md2html/` and link them from each page. |
| `cdn` | Use versioned jsDelivr URLs for browser MathJax and CommonHTML fonts. Generated CSS stays inline. |

One input file defaults to `standalone`; directories and multiple inputs
default to `shared`. Standalone pages embed local stylesheets (with their
`@import` chains and `url(...)` resources), but authored images remain normal
file references. Pass `--embed-images` to embed local `<img>` sources as data
URLs. Raw HTML `<link>` and `<script>` elements and remote resources are left
untouched. Standalone browser MathJax is not implemented — md2html warns and
uses the CDN component instead. A CDN page needs network access when opened.

### CommonHTML Fonts

Set `--math-fonts MODE` or `math.chtml_fonts` when using `mathjax-chtml`:

| Mode | Behavior |
| --- | --- |
| `auto` | Follow `assets`: embed used fonts in standalone pages, copy the local font set in shared mode, use CDN fonts in CDN mode. |
| `local` | Use installed fonts. Embedded in standalone pages, copied in shared mode. |
| `remote` | Use versioned CDN fonts regardless of the asset policy. |
| `all` | Include every installed font, not just the families the build uses. |
| `inline` | Embed used fonts as data URLs in the generated stylesheet. |
| `none` | Omit font files and `@font-face` rules. |

Shared builds write `assets/md2html/mathjax-chtml.css` and, for local modes,
the complete 301 KB TeX WOFF2 set below `assets/md2html/mathjax/woff2/`, so
rebuilding one page can't invalidate another's fonts; each page preloads only
the families it uses. Local fonts survive a CDN disappearing; remote fonts
make the generated files smaller but need the network on first view, and
modern partitioned browser caches don't share that download across sites.

### Page Sizes

Measured from the repository's Gaussian Integral notes with the default
template and minified CSS. Authored images remain external; renderer markup
and fonts are included according to the selected asset policy.

| Math output | Asset policy | HTML | Gzipped HTML |
| --- | --- | ---: | ---: |
| Browser MathJax | CDN | 118 KB | 21 KB |
| Static CommonHTML | standalone | 848 KB | 238 KB |
| Native MathML | standalone | 267 KB | 29 KB |
| Inline SVG | standalone | 2,549 KB | 346 KB |

For a multi-page site, shared local assets give the best durability and total
size. For an archival single page, embedded CommonHTML avoids third-party
dependencies while remaining much smaller than inline SVG on math-heavy pages.

## Templates And CSS

The bundled templates are `page.html` (default: a centered reading page with
reader controls, print styles, and a filename header) and `barebones.html`
(the same without the reader widget). Pages stay readable with JavaScript
disabled; JavaScript only saves the reader's theme, measure, typeface, and
text size between pages.

### Create Editable Files

```bash
md2html --example-template templates/page.html
md2html --example-css templates/page.css
md2html --templates templates article.md
```

The generated `page.css` contains the base page CSS, feature CSS, and the
selected highlighter's light/dark rules. Because it shares a stem with
`page.html`, md2html selects it automatically as that template's complete
stylesheet (no extra feature CSS is appended). Use other filenames for
several designs:

```bash
md2html --example-template templates/report.html
md2html --example-css templates/report.css
md2html --template report --templates templates article.md
```

### Template Lookup

Standalone pages search the configured `templates` directories in order, then
the project `_templates` directory, then the bundled templates; a name
without an extension gets `.html`. Static-site layouts also search the source
`_layouts` directory before the bundled templates. Liquid includes search the
configured template directories, `_templates`, `_includes`, `_layouts`, and
the bundled templates.

### CSS Layers

The default template embeds CSS so one input produces one self-contained
file. Base CSS and generated feature CSS are separate layers:

```bash
# Replace base CSS but keep CSS for code, math, TOCs, images, and warnings.
md2html --css styles/base.css article.md

# Combine several base files.
md2html --css styles/base.css --css styles/print.css article.md

# Keep base CSS but omit generated feature CSS.
md2html --no-feature-css article.md

# Omit both groups.
md2html --no-css article.md

# Leave generated CSS readable instead of minifying it.
md2html --no-minify-css article.md

# Add an external stylesheet link.
md2html --stylesheet styles/site.css article.md

# Use only your stylesheet and the HTML template's structure.
md2html --no-css --stylesheet styles/site.css article.md
```

Minification happens after feature selection, so a standalone page first
drops unused feature styles and then minifies what remains. `--assets shared`
writes common CSS to `assets/md2html/page.css` and links it from each page; a
page with its own `template` or `css` front matter embeds its selection
instead. Configured local CSS files and their `@import` chains are watched.

Math renderer CSS is a separate template layer. A custom template may omit
`md2html.math_css`, `md2html.math_stylesheets`, and `md2html.font_preloads`
to supply its own math rules; the generated markup then remains unstyled by
md2html.

### Syntax Highlighting

```bash
md2html --highlighter pygments --highlighter-style friendly \
  --highlighter-dark-style github-dark article.md
md2html --highlighter rouge --highlighter-style github.light \
  --highlighter-dark-style github.dark article.md
```

Run `pygmentize -L styles` to list Pygments styles or `rougify help style`
for Rouge's. A style not provided by the selected highlighter is rejected.
Token CSS is generated from the selected styles and added only when the page
needs it.

For custom CSS: highlighted fences use a `codehilite fenced-code` wrapper
(plus a `code-language` label when the fence has an info string), and source
directives use a `code-box` containing `code-header`, `codehilite`, and
`code-output`; collapsible source adds `collapsible-code`.

### Template Variables

Standalone templates receive:

| Variable | Value |
| --- | --- |
| `content` | Rendered page body HTML. |
| `page` | Front matter plus `title`, `name`, `url`, `path`, tags, categories, and excerpt. |
| `site` | Configured site values and defaults. |
| `md2html.page_stylesheets` | Generated shared page stylesheet hrefs. |
| `md2html.css` | Selected embedded base and feature CSS, or empty. |
| `md2html.math_css` | Generated math renderer CSS, or empty. |
| `md2html.math_stylesheets` | Generated math renderer stylesheet hrefs. |
| `md2html.font_preloads` | Font hrefs to preload for this page. |
| `md2html.inline_stylesheets` | Authored local stylesheet text for `<style>` elements. |
| `md2html.stylesheets` | Authored stylesheet hrefs, emitted last so they can override earlier layers. |
| `md2html.mathjax_config` | Browser MathJax configuration JavaScript, or empty. |
| `md2html.mathjax_src` | Browser MathJax script href, or empty. |
| `md2html.jekyll_compatibility` | True while building a Jekyll source tree directly. |
| `md2html.uses_mathjax` | True when the page needs browser-side MathJax. |
| `md2html.uses_mathjax_chtml` | True when the page contains static CommonHTML math. |
| `md2html.uses_svg_math` | True when the page contains generated SVG math. |
| `md2html.uses_mathml` | True when the page contains generated MathML. |
| `md2html.has_code` | True when the page contains highlighted code. |
| `md2html.has_toc` | True when the page contains a generated table of contents. |
| `md2html.has_images` | True when rendered content contains an image. |
| `md2html.has_warnings` | True when rendered content contains a generated warning. |
| `md2html.has_math_copy` | True when rendered math has a hidden copyable TeX source. |

Native site layouts receive the same `md2html` values and decide where the
assets belong. Emit configured stylesheets like this:

```liquid
{% for stylesheet in md2html.inline_stylesheets %}
<style>{{ stylesheet }}</style>
{% endfor %}
{% for stylesheet in md2html.stylesheets %}
<link rel="stylesheet" href="{{ stylesheet }}">
{% endfor %}
```

And the complete (removable) math block:

```liquid
{% for font in md2html.font_preloads %}
<link rel="preload" href="{{ font }}" as="font" type="font/woff2" crossorigin>
{% endfor %}
{% for stylesheet in md2html.math_stylesheets %}
<link rel="stylesheet" href="{{ stylesheet }}">
{% endfor %}
{% if md2html.math_css %}<style>{{ md2html.math_css }}</style>{% endif %}
{% if md2html.mathjax_src %}
<script>{{ md2html.mathjax_config }}</script>
<script defer src="{{ md2html.mathjax_src }}"></script>
{% endif %}
```

Both bundled templates use the internal `math-copy.html` partial when
rendered math has a copyable TeX source; a template may omit it without
changing the article content.

## Native Static Site Builds

Set `output_mode` to `"site"` in `md2html.json`:

```json
{
  "input": ".",
  "output": "_site",
  "output_mode": "site",
  "site": {
    "title": "My notes",
    "url": "https://example.com"
  }
}
```

A typical source tree:

```text
md2html.json
index.md
about.md
_posts/
  2026-05-18-gaussianintegral.md
_layouts/
  default.html
  post.html
_includes/
  navigation.html
assets/
  site.css
  figure.png
```

Site mode discovers Markdown, HTML, HTM, and XML recursively; front matter is
optional everywhere. Markdown becomes `.html`; HTML, HTM, and XML render only
Liquid and keep their suffixes. Static files are copied with their relative
paths preserved, skipping `md2html.json`, dot- and underscore-prefixed paths,
and configured exclusions. An output directory below the source is excluded
from discovery, output paths must stay below the output directory with one
owner each, and `--clean` refuses to remove a directory containing the input.

Posts named `_posts/YYYY-MM-DD-title.EXT` get dated URLs
(`/2026/05/18/gaussianintegral.html`). Set `site.permalink` or page
`permalink` to change the pattern; the fields are `:year`, `:month`, `:day`,
`:title`, `:slug`, and `:categories`, and a pattern ending in `/` writes
`index.html` inside that directory.

### Layouts And Includes

Set `layout` in front matter to wrap a page. Layouts receive `site`, `page`,
`content`, and `layout`, and may select another layout in their own front
matter; cycles and missing layouts produce warnings. A page with no layout
writes its rendered body without an outer document.

`{% include navigation.html %}` (quoted or unquoted) loads
`_includes/navigation.html`. Liquid dependencies are watched recursively.

### Site Data

`site.pages` contains every discovered page; posts are in `site.posts` in
reverse date order. `site.tags` and `site.categories` map names to posts, and
`site.tag_list` and `site.category_list` contain sorted objects with `name`,
`slug`, `posts`, and `size`. Each page exposes its front matter, URL, source
path, filename, excerpt, tags, and categories through `page`. `relative_url`
prepends `site.baseurl`; `absolute_url` prepends `site.url` too. `site.time`
is the build time.

### Pagination

```json
{
  "output_mode": "site",
  "paginate": 5,
  "paginate_path": "/blog/page:num/"
}
```

Pagination applies to HTML files named `index.html` (Markdown index files are
not pagination templates). The first page keeps the index URL; later pages
replace `:num` starting at 2. The index page and its layouts receive
`paginator` with `posts`, `page`, `per_page`, `total_posts`, `total_pages`,
`previous_page`, `previous_page_path`, `next_page`, and `next_page_path`;
missing neighbors are `nil`, and posts with `hidden: true` are excluded.

### Feed

HTML site modes write a minimal Atom `feed.xml` with the twenty newest posts.
`site.author` may be a string or an object with `name`, `email`, and `uri`;
the site title is used when it is absent. Add your own source `feed.xml` to
replace the generated one.

## Jekyll Compatibility Mode

Use `--jekyll` (or `output_mode: "jekyll"`) to build an existing Jekyll
source tree directly:

```bash
md2html --jekyll website -o _site --serve
```

This reads `_config.yml` and uses the same renderer, layouts, includes,
Liquid environment, pagination, feed, execution cache, and watcher as site
mode. Markdown pages still support all md2html directives and executable
examples. Following Jekyll's rules: ordinary pages require front matter
(supported files without it are copied unchanged), dated `_posts` files
become posts with the default URL
`/:categories/:year/:month/:day/:title.html`, and `_config.yml` `include`,
`exclude`, and permalink settings are honored, along with Jekyll's standard
cache and vendor exclusions.

The compatibility subset does not run Ruby: plugins, themes, custom
collections, `_data`, front-matter defaults, and Sass are not implemented.
Existing layouts remain responsible for their own stylesheets and scripts —
md2html does not inject assets into them. If a layout already loads browser
MathJax, select `math.backend: "mathjax"` so it renders the preserved TeX;
the static backends (`mathjax-chtml`, `svg`, `mathml`) are unavailable in
this mode and warn while leaving the TeX in place.

## Jekyll Markdown Output

Use `--jekyll-markdown` (or `output_mode: "jekyll-markdown"`) to prepare
Markdown for a later Jekyll build:

```json
{
  "input": "notes",
  "output": "website/notes",
  "output_mode": "jekyll-markdown",
  "execute": true,
  "frontmatter": {
    "layout": "notes",
    "render_with_liquid": false
  }
}
```

This expands `@include`, `@toc`, `@src`, inline source blocks, and Obsidian
images into HTML that is valid inside Markdown, including cached or newly
executed program output. Ordinary fenced code, inline code, math, raw HTML, links,
and Liquid remain for Jekyll, and directives inside code stay literal. Each
`.md` path is kept; the configured `frontmatter` defaults are merged under
the source's own front matter.

Directory builds copy the rest of the source tree (layouts, includes,
configuration, static assets), omitting md2html's configuration, caches, and
version-control data. `--watch` keeps the tree updated; `--serve` is for
generated HTML, so let Jekyll or Jekyll compatibility mode serve the result.

## Watch And Serve

`--watch` performs an initial build, then rebuilds as sources change.
`--serve` does the same and serves the generated pages on `127.0.0.1`. Both run until
interrupted.

The initial build skips a page whose generated file is at least as new as its source;
`--force` disables the skip, and `--force-execution` additionally pushes
pages through the renderer so executable directives rerun. The dependency
graph follows Markdown includes, source directives, Liquid includes and
layouts, templates, and CSS imports, so an edit rebuilds exactly the affected
pages; a new or unknown file triggers a full build so it can be discovered.
Changed static assets are copied directly without rerendering pages. When
several scattered pages are served together, only their generated pages and
copied assets are exposed, with one preview URL printed per page.

## Python API

```python
from pathlib import Path
from md2html import Project, Settings

settings = Settings.single(Path("article.md"))
result = Project(settings).build()
print(result.written)
```

`Settings` is immutable: use `Settings.single()` for one page, construct
`Settings` for a directory, or `load_settings()` from `md2html.settings` to
read `md2html.json`. `Project.build()` returns a `BuildResult` with written
files, copied files, skipped pages, warnings, and dependency maps. Pass
`only` (a set of source paths) to rebuild selected pages, or
`skip_unchanged=True` for the watch-style timestamp check.

## Behavior And Limits

Source execution runs local commands through `sh` and targets Unix-like
systems; Windows needs an environment providing those conventions. Keep
execution disabled for untrusted files. Cached program output is HTML-escaped before
it is added to a page.

The static-site support is deliberately a subset: pages, dated posts,
layouts, includes, permalinks, common Liquid, tags, categories, static files,
pagination, and a small Atom feed — not Ruby Jekyll, themes, plugins,
collections, Sass, or arbitrary Liquid extensions. When you need the rest of
Jekyll, use `jekyll-markdown` mode and let Jekyll finish the job.
