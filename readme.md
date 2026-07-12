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

## Quick Orientation

For Markdown, md2html reads YAML front matter, protects source code and math,
expands directives and Liquid expressions, renders Markdown, and applies the
selected template or layout. For HTML, HTM, and XML, it reads front matter and
renders only Liquid, followed by an explicitly selected site layout. Static-site
builds create the page list first, so layouts can use `site.pages`, `site.posts`,
tags, and categories.

Jekyll compatibility mode uses the same renderer and site model, but reads
`_config.yml`, requires front matter on ordinary Jekyll pages, follows Jekyll's
default exclusions and dated URLs, and writes a complete HTML site. Jekyll
Markdown mode runs md2html directives and executable examples, then writes the
remaining Markdown and Liquid for Jekyll to render.

Print the documentation and starter files from the installed command:

```bash
md2html -h                    # print all CLI options
md2html --readme              # print this README
md2html --example-config -    # print starter JSON to stdout
md2html --example-template -  # print the default page template to stdout
md2html --example-css -       # print editable default CSS to stdout
```

## Install

md2html 2.0 requires Python 3.10 or newer. Create a virtual environment and
install the package for development:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
npm install
```

The npm packages provide MathJax and its CommonHTML fonts. Static
`mathjax-chtml` requires them and a `node` executable at build time. Shared
browser-MathJax assets also come from the npm packages but do not run Node.
CDN browser MathJax does not need the npm packages at build time.

Run the tests:

```bash
python -m pytest -q
```

Build a single-file executable:

```bash
make pyinstaller
```

Build it and copy it to `~/.local/bin/md2html`:

```bash
make install
```

The executable contains md2html's Python packages, templates, CSS, scripts,
and npm MathJax packages. Static CommonHTML still requires `node` on the
machine that builds the page.

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

# Execute @src blocks, force fresh outputs, serve html/, and rebuild on edits.
md2html -erf src -o html --serve

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

# Use settings from another JSON file.
md2html --config path/to/md2html.json
```

With one Markdown file and no `-o`, md2html writes an `.html` file beside the
source. HTML, HTM, and XML preserve their suffixes, so pass `-o` or build them
as part of a directory to keep source and output separate. If an output would
overwrite its source, md2html skips that page, prints a warning, and continues
building other pages. With several inputs and `-o public`, it preserves their
paths relative to their common directory below `public`.

`-o` and `--output` are equivalent. `--output-mode` accepts `pages`, `site`,
`jekyll`, and `jekyll-markdown`. `--jekyll` and `--jekyll-markdown` select the
last two modes directly. The CLI value overrides `output_mode` from JSON. Use
`--version` to print the installed version and `--help` to print all options.

A page directory writes to `html`, a Jekyll site writes to `_site`, and Jekyll
Markdown writes to `markdown` unless `-o` or configuration chooses another
directory. Add `-r` to include nested Markdown in page mode; the other modes
are recursive by default. One input file embeds its assets by default. A
directory or several input files share local assets below `assets/md2html/` by
default. Use `--assets` to select another policy. `--standalone` is an alias
for `--assets standalone`.

`--execute`, `--recursive`, `--force`, and `--serve` have the short forms `-e`,
`-r`, `-f`, and `-s`, so `-erf` combines the first three. `--watch` rebuilds
without starting a server. `--serve` starts a loopback-only server and also
rebuilds. Use `-p` or `--port` to change its port.

`--force` reruns cached executable examples when execution is enabled. It also
allows the starter commands to replace existing files. `--clean` removes a
static site's output directory before building it. It does not apply to
independent page builds. Run `make clean` to remove packaging output, test
output, and `.md2html-cache` from the md2html checkout.

## Configuration

md2html uses one configuration name and format: `md2html.json`. When no input
or `--config` is given, it searches the current directory and its parents for
that file. When one directory is given, it also searches from that directory.
Use `--config path/to/md2html.json` to select a file explicitly.

md2html resolves paths inside the file relative to the file's directory. The
same command therefore works from any current working directory.

The following example shows every build setting. Omit site variables when
building independent pages.

```json
{
  "input": ".",
  "output": "html",
  "output_mode": "pages",
  "recursive": true,
  "clean": false,
  "exclude": ["drafts"],
  "paginate": 10,
  "paginate_path": "/page:num/",
  "frontmatter": {
    "layout": "default"
  },

  "templates": ["templates"],
  "template": "page.html",
  "css": ["styles/base.css"],
  "stylesheets": ["styles/print.css"],
  "feature_css": true,
  "minify_css": true,
  "parse_liquid": true,
  "assets": "shared",
  "highlight_style": "default",
  "highlight_dark_style": "github-dark",

  "math": {
    "backend": "mathjax-chtml",
    "chtml_fonts": "auto"
  },

  "images": {
    "class": null,
    "width": null
  },

  "execute": false,
  "force": false,
  "timeout": 120,
  "commands": {
    "julia": "julia {source}",
    "cpp": "g++ {source} -o {executable} && {executable} > {output}"
  },

  "site": {
    "title": "My technical notes",
    "description": "Notes about mathematics and programs",
    "url": "https://example.com",
    "baseurl": "",
    "permalink": "/:year/:month/:day/:title.html"
  }
}
```

### Inputs And Output

| Key | Meaning |
| --- | --- |
| `input` | Markdown file or source directory. The CLI also accepts several inputs. |
| `output` | Output file for one file input, or output directory for a collection. |
| `output_mode` | Select `"pages"`, `"site"`, `"jekyll"`, or `"jekyll-markdown"`. |
| `recursive` | Read supported documents in nested directories. Site and Jekyll modes enable this by default. |
| `parse_liquid` | Render Liquid in source documents. Templates and layouts always use Liquid. The default is `true`. |
| `assets` | Select `shared`, `standalone`, or `cdn` asset placement. One file defaults to `standalone`; collections default to `shared`. |
| `clean` | Remove the output directory before a complete site build. |
| `exclude` | Skip matching source paths. Exact paths, directory prefixes, and path patterns are accepted. |
| `frontmatter` | Add default front matter to Jekyll Markdown output. Source front matter takes precedence. |
| `paginate` | Put this many posts on each paginated `index.html` page in site mode. |
| `paginate_path` | Set the generated page URL. It must contain `:num`; the default is `/page:num/`. |

### Templates And Styles

These keys control independent page output. Static-site mode uses its own
layouts and stylesheet links; generated CommonHTML assets are still added when
needed.

| Key | Meaning |
| --- | --- |
| `templates` | Search this directory or ordered list of directories before `_templates` and the bundled templates. |
| `template` | Select the standalone page template. The default is `page.html`. |
| `css` | Replace the template's base CSS with one path or a list. `null` selects companion or bundled CSS; `[]` selects no base CSS. |
| `stylesheets` | Add one or more stylesheet paths. Standalone output embeds local files; shared and CDN output preserve links. |
| `feature_css` | Add CSS for generated code, output, math, tables of contents, images, and warnings. The default is `true`. |
| `minify_css` | Minify embedded and generated shared CSS. The default is `true`. |
| `highlight_style` | Select a Pygments style name for light syntax highlighting. |
| `highlight_dark_style` | Select a Pygments style name for dark and automatic dark-mode highlighting. |

### Math And Execution

| Key | Meaning |
| --- | --- |
| `math.backend` | Select `mathjax`, `mathjax-chtml`, `svg`, `mathml`, or `raw`. |
| `math.chtml_fonts` | Select `auto`, `all`, `inline`, `local`, `remote`, or `none` for static CommonHTML fonts. |
| `images.class` | Add one or more default classes to Obsidian images. Per-image classes are appended. |
| `images.width` | Set a default Obsidian image width. A per-image width takes precedence. |
| `execute` | Run source directives. Execution is off by default. |
| `force` | Rerun completed source workspaces when execution is enabled. |
| `timeout` | Stop one source command after this many seconds. The default is 120. |
| `commands` | Add or replace execution commands by language name or file extension without the leading dot. |

All other top-level keys become `site` variables. Values in the explicit
`site` object do the same while keeping build settings separate. The built-in
site defaults define `title`, `description`, `url`, and `baseurl`; templates may
use any additional values you provide.

Command-line settings override JSON settings. Boolean CLI options turn their
corresponding behavior on. Use `--no-feature-css` to turn feature CSS off and
`--no-css` to turn both base and feature CSS off for a run.

## Writing Pages

Markdown files use md2html's complete content renderer. It supports headings,
links, images, block quotes, fenced code, inline code, tables, task lists,
strikethrough, automatic URLs, raw HTML, math, and `@` directives. The bundled
CSS makes images, videos, SVG, and embedded YouTube iframes responsive.

HTML, HTM, and XML files use a smaller path: remove optional front matter,
render Liquid, and apply an explicitly selected site layout. md2html does not
interpret Markdown, math delimiters, Obsidian syntax, or `@` directives in
these files. Ordinary pages preserve `.html`, `.htm`, and `.xml` suffixes;
explicit permalinks and dated post routing may choose another path. XML never
acquires `.html` automatically.

Start a page with YAML front matter when it needs metadata or a page-specific
template:

```markdown
---
title: A Small Example
template: page
css:
  - styles/note.css
stylesheets:
  - styles/print.css
feature_css: true
---

# A Small Example

Some text with `inline code` and $e^{i\pi}+1=0$.
```

Without a `title`, the source filename becomes the document title. The default
template also prints the source filename in the upper-left page header.

Front matter controls both independent pages and site pages:

| Key | Meaning |
| --- | --- |
| `title` | Set `page.title` and the bundled standalone HTML title. The filename is used when this is absent. |
| `template` | Select a standalone page template. |
| `css` | Replace base CSS for this page. Use `[]` to keep only feature CSS. |
| `stylesheets` | Add stylesheet links for this page. |
| `feature_css` | Enable or disable generated feature CSS for this page. |
| `render_with_liquid` | Set to `false` to leave Liquid expressions in this document unchanged. Templates and layouts still render. |
| `layout` | Select a static-site layout from `_layouts`. Layouts may select another layout. |
| `permalink` | Set a static-site URL and output path. A trailing slash writes `index.html`. |
| `date` | Set a post date. ISO dates and YAML date values are accepted. |
| `tags`, `categories` | Add a post to the corresponding `site` groups. Strings and lists are accepted. |
| `published` | Set to `false` to omit a page or post in Jekyll compatibility mode. |

Source pages may use Liquid expressions such as `{{ page.title }}` and
`{{ site.title }}`. Markdown protects raw code, fenced code, inline code, and
math before evaluating Liquid, so braces in Mathematica and other languages
remain literal. Use `{% raw %}...{% endraw %}` to protect a smaller Liquid
region explicitly.

Pass `--no-liquid` or set `"parse_liquid": false` in JSON to leave Liquid
unchanged in every source document. A page may opt out with front matter
`render_with_liquid: false`; a page cannot override a global opt-out. Templates and
layouts continue to render Liquid, so they insert the unparsed document through
`{{ content }}` as-is. Static sites also support Liquid includes, loops,
conditionals, and the `relative_url` and `absolute_url` filters.

Invalid TeX, missing includes, missing source files, Liquid errors, and source
execution failures produce warnings and leave the rest of the page buildable.
Invalid YAML front matter and structurally invalid inline source blocks stop
that page's build.

### Obsidian Images

```markdown
![[img/ex3-10.svg|width=70%|alt=Environment diagram|class=centered]]
![[img/detail.png|480]]
```

Width values ending in `%`, `px`, `em`, or `rem` become CSS widths. md2html
treats plain numeric widths as pixels and uses the first unlabelled non-width
field as alternative text. Use `alt=` and `class=` when explicit names are
clearer. Set `images.class` or `images.width` for project defaults.

## Directives

Put directives on their own lines. md2html resolves relative paths from the
file that contains the directive first, then from the project root. This rule also
applies inside nested Markdown includes.

### `@toc`

`@toc` is replaced with a compact `Directory`. Headings named `Solution` are
skipped. Exercise headings are grouped inside the `Exercises` entry.

```markdown
@toc

## Section 2.5
### Exercises
#### Exercise 2.77
##### Solution
#### Exercise 2.78
```

Heading links use lowercase slugs. Repeated headings receive `-2`, `-3`, and
later suffixes so every link remains distinct.

### `@include(path)`

```markdown
@include(_partials/header.md)
```

Includes may contain directives and further includes. Front matter in an
included file is discarded; only the page's front matter controls the result.
A missing file or include cycle produces a warning in the terminal and a
visible warning in the page.

The watch graph follows includes recursively. After a rebuild, removed
includes no longer trigger that page.

### `@src(path[, flags...])`

Embed a source file with syntax highlighting:

```markdown
@src(code/ex2-77.rkt)
@src(code/ex2-77.rkt, collapsible)
@src(code/ex2-77.rkt, collapsed)
@src(code/ex2-77.rkt, expanded)
@src(code/ex2-77.rkt, noexecute)
```

Without a display flag, md2html shows an ordinary source box.
`collapsible` and `expanded` start with the source open. `collapsed` starts
with it closed. `noexecute` prevents execution and cached-output lookup for
that block. The source file's extension selects the language.

When global execution is enabled, file source directives run unless they use
`noexecute`. Successful output appears below the source. Without global
execution, a matching completed cache is still displayed.

The generated source heading links to the source file. A standalone page whose
output moves to another directory copies the source beside its output so that
link continues to work. Directory builds copy source and other static files
while preserving their paths.

A single-line `@src(` tag with no closing parenthesis becomes a large visible
error on that line and does not stop the page. Missing, nested, or unexpected
`@src-begin` and `@src-end` markers stop the page because the remaining block
boundaries cannot be determined safely.

### `@src-begin(lang[, flags...])`

Embed an inline source block and close it with `@src-end`:

```markdown
@src-begin(cpp, execute, expanded)
#include <iostream>
int main() { std::cout << "Hello, world!\n"; }
@src-end
```

Inline blocks accept the same `collapsed`, `collapsible`, `expanded`, and
`noexecute` flags. The `execute` flag records that the example is intended to
run, but it never enables execution by itself. Pass `--execute` or set
`"execute": true` to allow commands to run. With global execution enabled,
inline blocks run even when the `execute` flag is omitted unless `noexecute`
is present.

## Executable Content

md2html does not execute source by default. Enable it only for files you trust:

```bash
md2html --execute article.md
md2html --execute --force article.md
```

Python, POSIX shell, JavaScript, Racket, Wolfram Language, C, and C++ have
default commands. The corresponding interpreter or compiler must be installed.
A missing program, compile error, nonzero exit status, or timeout produces a
warning. It does not stop other pages or prevent completed cache cleanup.

Each block runs in a persistent directory below:

```text
SOURCE_DIRECTORY/.md2html-cache/PAGE_NAME/LANGUAGE-SOURCE_CHECKSUM/
```

For example, executable blocks in `guide/index.md` use
`guide/.md2html-cache/index/`. Two pages in one directory receive separate page
directories. A reference to `mysource.rkt` uses a workspace named
`rkt-mysource-CHECKSUM`; inline Racket uses `rkt-inline-CHECKSUM`. md2html copies
inline source into its workspace. File-backed source is referenced from that
workspace, but its cached output belongs to the page containing the directive.
Compilers, executables, images, and other files made with relative paths remain
there and do not pollute the source directory.

The cache key uses the source text. It does not include checkout paths,
interpreter paths, commands, settings, or md2html metadata. Changing source
text selects a new workspace. Use `--execute --force` after changing a command,
compiler, runtime, or other external input that should refresh existing output.

md2html saves successful output as `output.txt` and marks it complete. Later
builds include it even when execution is disabled. A CI job can restore or
check out the source tree's `.md2html-cache` directories and build pages
without installing compilers or enabling execution:

```bash
md2html --config md2html.json
```

If an `execute` block has no completed output while execution is disabled,
md2html builds the page and prints a warning explaining how to populate it.
After a successful page render, it removes block workspaces no longer used by
that page only when execution is enabled. A build with execution disabled never
deletes cached workspaces. Deleting a page leaves its cache in place until the
project's clean command removes `.md2html-cache` directories. A parse or
rendering failure also preserves that page's cache.

### Commands And Output

Add or replace commands in `md2html.json`:

```json
{
  "timeout": 30,
  "commands": {
    "julia": "julia {source}",
    "cpp": "g++ {source} -o {executable} && {executable} > {output}"
  }
}
```

Use a language name for inline blocks or an extension without its dot for file
source. Command strings accept these fields:

| Field | Value |
| --- | --- |
| `{source}` | Source path relative to the workspace. |
| `{filename}` | Alias for `{source}`. |
| `{sourcedir}` | Original source directory relative to the workspace. |
| `{builddir}` | The workspace, written as `.`. |
| `{slug}` | Safe source stem or inline language name. |
| `{executable}` | `./SLUG.md2html-out` inside the workspace. |
| `{output}` | `output.txt` inside the workspace. |
| `{python}` | Python interpreter running md2html. |

The command runs through `sh` with the workspace as its working directory. If
it creates `{output}`, md2html reads that file. Otherwise md2html saves the
command's standard output to `{output}`. Standard error is included in failure
messages but is not added to successful page output.

Set the timeout with `--timeout SECONDS` or the JSON `timeout` key. The default
is 120 seconds per command.

## Math Rendering

md2html recognizes inline `$...$`, display `$$...$$`, and bare `align`,
`gather`, `multline`, and `equation` environments, including starred forms.
It protects math before Markdown and Liquid rendering. Escaped currency such
as `\$5` remains text.

The default `mathjax-chtml` backend renders static CommonHTML during the build.
Select any backend with `--math` or `math.backend`:

```bash
md2html --math mathjax note.md -o note-browser-mathjax.html
md2html --math mathjax-chtml note.md -o note-chtml.html
md2html --math svg note.md -o note-svg.html
md2html --math mathml note.md -o note-mathml.html
md2html --math raw note.md -o note-raw.html
```

`mathjax-chtml` runs MathJax under Node and writes static CommonHTML. `svg`
writes inline SVG. `mathml` writes inline MathML. `raw` preserves the original
delimiters without loading a renderer. If a build-time renderer rejects an
expression, md2html prints a warning and leaves that expression as LaTeX.

Static MathJax CHTML, SVG, and MathML math include a hidden copy source
containing the original LaTeX delimiters. Copying prose that contains equations
should copy the LaTeX source, not the generated CHTML, SVG paths, or MathML
text.

The SVG and MathML backends are built into the Python package dependencies and
do not require a TeX installation. SVG output is inlined by default and uses
`currentColor`, so it follows the default `page.html` light/dark reader theme
and also renders normally in pages with no dark-mode styles. MathML output is
also inline and inherits the page color.

MathML does not support every LaTeX construct. When conversion fails, md2html
emits a warning and falls back to the escaped LaTeX wrapper for that equation.

### Asset Placement

Set `--assets MODE` or the `assets` configuration key:

| Mode | Behavior |
| --- | --- |
| `standalone` | Embed generated CSS, CommonHTML fonts, and local authored stylesheets, scripts, and media in every page. |
| `shared` | Write reusable renderer assets below `assets/md2html/` and link them from each page. Local site media remains in the output tree. |
| `cdn` | Use versioned CDN URLs for browser MathJax and CommonHTML fonts. CSS generated by md2html remains inline. |

`--standalone` is an alias for `--assets standalone`. A one-file build uses
`standalone` by default. Directory and multiple-input builds use `shared` by
default. `--assets shared` with one input file writes an `assets/md2html/`
directory beside the output page.

Standalone mode embeds local CSS `@import` files and local `url(...)`
resources recursively. It also embeds local script and image sources. An
explicit remote stylesheet, script, image, video, or iframe remains remote;
md2html does not download arbitrary Internet resources during a build.

Shared browser MathJax copies a minified combined component, its CommonHTML
fonts, dynamically loaded font data, and speech worker. CDN mode loads the
versioned component and fonts from jsDelivr. Standalone browser MathJax is not
implemented; md2html prints a warning and uses the CDN component.

### CommonHTML Fonts

Set `--math-fonts MODE` or `math.chtml_fonts` when using `mathjax-chtml`:

| Mode | Behavior |
| --- | --- |
| `auto` | Follow `assets`: embed used fonts in standalone pages, copy the complete local font set for shared output, or use CDN fonts for CDN output. |
| `local` | Use installed fonts. Embed used fonts unless `assets` is `shared`, in which case copy the complete set. |
| `remote` | Use versioned CDN fonts regardless of the general asset policy. |
| `all` | Use every installed CommonHTML font rather than only the families required by the build. Placement still follows `assets`. |
| `inline` | Embed used fonts as data URLs in the generated stylesheet. |
| `none` | Omit font files and `@font-face` rules. |

Directory and site builds share `assets/md2html/mathjax-chtml.css` and store
local fonts below `assets/md2html/mathjax/woff2/` when the selected mode uses
local files. Shared local output writes the complete 301 KB TeX WOFF2 set so
adding or rebuilding another page cannot invalidate an earlier page's fonts.
Pages preload only the families they use.

`local` and `remote` select ownership rather than layout. Local assets remain
available if a CDN changes or disappears. Remote assets make the generated
files smaller, but the first view requires the network. Browsers can cache CDN
fonts between pages on the same site, but modern partitioned caches generally
do not share that download with unrelated sites and no cache entry is
permanent.

The following sizes were measured from the repository's Gaussian Integral
notes with the default page template and minified CSS. Standalone rows include
the article's local image. CDN rows count only the HTML file, not that image or
the resources downloaded by the browser.

| Math output | Asset policy | HTML | Gzipped HTML |
| --- | --- | ---: | ---: |
| Raw LaTeX | standalone | 709 KB | 410 KB |
| Native MathML | standalone | 860 KB | 419 KB |
| Static CommonHTML | CDN fonts | 593 KB | 44 KB |
| Static CommonHTML | standalone | 1,440 KB | 628 KB |
| Inline SVG | standalone | 3,142 KB | 738 KB |
| Browser MathJax | CDN | 118 KB | 21 KB |
| Browser MathJax | standalone fallback | 711 KB | 410 KB |

MathML is the smallest dependency-free rendered form, but conversion does not
cover every LaTeX construct. Static CommonHTML with embedded fonts is larger
and has broader TeX coverage. Inline SVG has no font or JavaScript dependency,
but repeated path data makes equation-heavy pages much larger. Browser
MathJax CDN output keeps the HTML small at the cost of a runtime dependency.
The standalone browser-MathJax row embeds local article assets but still uses
the CDN renderer because one-file browser MathJax is not implemented.

For a multi-page site, shared local assets normally give the best durability
and total size. For an archival single page, embedded CommonHTML avoids a
third-party dependency while keeping the file substantially smaller than
browser-rendered standalone MathJax.

## Templates And CSS

The bundled templates are:

- `page.html` (default): A centered reading page with reader controls, print
  styles, and a filename header.
- `barebones.html`: A simpler centered reading page without the reader widget.

Both use the internal `math-copy.html` partial when rendered math has a
copyable TeX source. A template may omit that include without changing the
rendered article content.

The page remains readable when JavaScript is disabled. The default reader
controls use standard HTML and CSS; JavaScript saves the selected theme, measure,
typeface, and text size between pages.

### Create Editable Files

Write the default template and a complete editable stylesheet:

```bash
md2html --example-template templates/page.html
md2html --example-css templates/page.css
```

The generated `page.css` contains the base page CSS, feature CSS, and default
light/dark Pygments rules. Edit both files, then build with:

```bash
md2html --templates templates article.md
```

Because `page.css` has the same stem as `page.html`, md2html selects it
automatically when no explicit `css` setting is present. A companion stylesheet
is treated as the complete stylesheet for its template, so md2html does not
append another copy of the bundled feature CSS. Use another filename or
directory if you want several designs:

```bash
md2html --example-template templates/report.html
md2html --example-css templates/report.css
md2html --template report --templates templates article.md
```

The example commands do not replace files unless `--force` is present. Pass
`-` as the destination to print an example to standard output.

### Template Lookup

For standalone pages, md2html searches the configured `templates` directories
in order, then the project `_templates` directory, then the bundled templates.
A name without an extension receives `.html`. Repeat `--templates` to add
directories on the command line.

Static-site layouts use the same order and also search the source `_layouts`
directory before the bundled templates. Liquid includes search the configured
template directories, `_templates`, `_includes`, `_layouts`, and the bundled
templates.

### CSS Layers

The default template embeds CSS so one input produces one self-contained HTML
file. Base CSS and generated feature CSS are separate. Explicit `--css` files
replace the base layer and keep the feature layer:

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

Use `"css": ["styles/base.css"]` to replace the selected template's default
CSS. It does not append the bundled page design. Use `"css": []` to disable
template CSS while keeping feature CSS. Set `"feature_css": false` to disable
feature CSS too. The corresponding CLI options are `--css`,
`--no-feature-css`, and `--no-css`.

Math renderer CSS is a separate template layer. The bundled templates include
it after ordinary CSS. A custom template may omit `md2html.math_css`,
`md2html.math_stylesheets`, and `md2html.font_preloads` when it will supply its
own CommonHTML, MathML, or SVG rules. Generated math markup will then remain in
the document without md2html's renderer CSS.

Embedded and generated shared CSS is minified by default. This happens after
feature selection, so a standalone page first omits unused feature styles and
then minifies the CSS it retains. Set `"minify_css": false` or pass
`--no-minify-css` when inspecting generated styles.

`--assets shared` writes common CSS to `assets/md2html/page.css` and links to
it from each ordinary page. A page with its own `template` or `css` front
matter embeds its selected CSS instead.

Local CSS files and their local `@import` dependencies are watched.
Standalone mode embeds local stylesheet links, imports, CSS resources,
scripts, and media. Shared output keeps reusable files in the output tree.

### Syntax Highlighting

Fenced code and source directives use Pygments. Select styles by name:

```bash
md2html --highlight-style friendly \
  --highlight-dark-style github-dark article.md
```

Set `highlight_style` and `highlight_dark_style` in JSON for project defaults.
Run `pygmentize -L styles` to list names provided by the installed Pygments
version. md2html rejects an unknown CLI style name. It generates token CSS from
the selected styles and adds it only when the page or shared stylesheet needs
code highlighting. Native layouts receive the selected token rules through
`md2html.css`; place that value after the site's structural code-block CSS.

Highlighted fences use a `codehilite fenced-code` wrapper. A fence with an info
string also receives a small `code-language` label. Source directives use a
`code-box` containing `code-header`, `codehilite`, and, when available,
`code-output`. Collapsible source uses `collapsible-code` inside the same
`code-box`. Use these class names from custom CSS.

### Template Variables

Standalone templates receive:

| Variable | Value |
| --- | --- |
| `content` | Rendered page body HTML. |
| `page` | Front matter plus `title`, `name`, `url`, `path`, tags, categories, and excerpt. |
| `site` | Configured site values and defaults. |
| `md2html.page_stylesheets` | Generated shared page stylesheet hrefs. |
| `md2html.css` | Selected embedded base and feature CSS, or an empty value. |
| `md2html.math_css` | Generated math renderer CSS, or an empty value. |
| `md2html.math_stylesheets` | Generated math renderer stylesheet hrefs. |
| `md2html.font_preloads` | Font hrefs to preload for this page. |
| `md2html.stylesheets` | Authored stylesheet hrefs, emitted last so they can override the preceding layers. |
| `md2html.mathjax_config` | Browser MathJax configuration JavaScript, or an empty value. |
| `md2html.mathjax_src` | Browser MathJax script href, or an empty value. |
| `md2html.jekyll_compatibility` | True only while md2html is directly building a Jekyll source tree. |
| `md2html.uses_mathjax` | True when this page needs browser-side MathJax. |
| `md2html.uses_mathjax_chtml` | True when this page contains static CommonHTML math. |
| `md2html.uses_svg_math` | True when this page contains generated SVG math. |
| `md2html.uses_mathml` | True when this page contains generated MathML. |
| `md2html.has_code` | True when this page contains highlighted code or a source box. |
| `md2html.has_toc` | True when this page contains a generated table of contents. |
| `md2html.has_images` | True when rendered page content contains an image. |
| `md2html.has_warnings` | True when rendered page content contains a generated warning. |
| `md2html.has_math_copy` | True when rendered math has a hidden copyable TeX source. |

The bundled templates show the Liquid structure for `<title>`, authored
stylesheets, selected CSS, math assets, browser MathJax, the filename header,
and rendered content. Native site layouts receive the same `md2html` values.
They decide where renderer assets belong; md2html does not search completed
HTML to insert renderer assets.

The complete removable math block is:

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

## Asset Copying

When a single output stays beside its source, local links already point to the
source files and md2html does not duplicate them. When `-o` moves that page,
md2html copies local Obsidian images, Markdown images, HTML image/video sources,
source files shown by `@src`, and local stylesheet hrefs below the output
directory. It preserves the path written in the page. Remote URLs, fragment
links, data URLs, and `mailto:` links are not copied.

Directory builds copy static files from the input tree while preserving their
relative paths. Markdown sources become HTML instead. Private source paths,
project files, and configured exclusions follow the rules under
[Static Files And Exclusions](#static-files-and-exclusions).

The build result records every direct source-to-output asset link. Watch mode
uses those links to copy changes without rerendering a page. Files made by an
executable example remain in that example's `.md2html-cache` workspace; md2html
does not publish them automatically.

## Jekyll Markdown Output

Use `--jekyll-markdown` or set `output_mode` to `"jekyll-markdown"` to prepare
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

This mode expands `@include`, `@toc`, `@src`, inline source blocks, and
Obsidian images. Generated tables of contents and source directives become HTML
that is valid inside Markdown, and cached or newly executed output is included
below the source. Ordinary fenced code, inline code, math, raw HTML, links, and
Liquid remain for Jekyll. Directives written inside fenced or inline code remain
literal.

The output keeps each `.md` or `.markdown` path. Source front matter overrides
the configured `frontmatter` defaults. Pages without a title use their source
filename. md2html writes the resulting YAML and Markdown; Jekyll performs the
Liquid, Markdown, permalink, and layout stages.

Directory builds copy the remaining source tree, including Jekyll layouts,
includes, configuration, source files, and static assets. They omit md2html's
configuration, cache, output, version-control data, and Python cache files.
`--watch` updates this tree as inputs change. Use Jekyll or Jekyll compatibility
mode to serve it; `--serve` is reserved for HTML output.

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

A typical source tree is:

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

Site mode discovers Markdown, HTML, HTM, and XML recursively. Front matter is
optional for every type. Markdown uses the complete md2html renderer and changes
its suffix to `.html`. HTML, HTM, and XML render only Liquid. Ordinary files
preserve their suffixes before permalink and dated-post rules are applied.

Markdown, HTML, and HTM posts named `_posts/YYYY-MM-DD-title.EXT` use dated
URLs. XML keeps its source path and suffix:

```text
_posts/2026-05-18-gaussianintegral.md
    -> /2026/05/18/gaussianintegral.html
```

Set `site.permalink` or page `permalink` to change that path. The supported
site pattern fields are `:year`, `:month`, `:day`, `:title`, `:slug`, and
`:categories`. A permalink
ending in `/` writes `index.html` inside that directory.

### Layouts And Includes

Set `layout` in page front matter to wrap a page:

```markdown
---
layout: post
title: Gaussian integral
---
```

Layouts receive `site`, `page`, `content`, and `layout`. A layout may select
another layout in its own front matter. Layout cycles and missing layouts
produce warnings. A site page with no layout writes its rendered body without
an outer document. Use `layout` when Markdown output needs a complete HTML page
or when a Liquid-only document needs an explicit wrapper.

Use `{% include 'navigation.html' %}` or the unquoted
`{% include navigation.html %}` form to load `_includes/navigation.html`.
Liquid dependencies are watched recursively.

### Site Data

`site.pages` contains every discovered page in native site mode; Jekyll mode
keeps posts in `site.posts` instead. Posts are in reverse date order.
`site.tags` and `site.categories` map each name to its posts. `site.tag_list`
and `site.category_list` contain sorted objects with `name`, `slug`, `posts`,
and `size` fields. Each page exposes its front matter, URL, source path,
filename, excerpt, tags, and categories through `page`.

`relative_url` adds `site.baseurl` to a path. `absolute_url` adds both
`site.url` and `site.baseurl`. `site.time` contains the build time.

### Pagination

Set `paginate` to the number of posts on each page. Set `paginate_path` to the
URL for pages after the first:

```json
{
  "output_mode": "site",
  "paginate": 5,
  "paginate_path": "/blog/page:num/"
}
```

Pagination applies to HTML files named `index.html`. The first page keeps the
index page's URL and output path. Later pages replace `:num` with page numbers
beginning at 2. Markdown index files are not pagination templates.

The index page and its layouts receive `paginator`. Use `paginator.posts` for
the posts on the current page. The other fields are `page`, `per_page`,
`total_posts`, `total_pages`, `previous_page`, `previous_page_path`,
`next_page`, and `next_page_path`. A missing previous or next page has a Liquid
`nil` value. Posts with `hidden: true` do not appear in `paginator.posts`.

HTML site modes write a small `feed.xml` containing the twenty newest posts. Add a
source `feed.xml` to replace it with a custom Liquid feed. md2html renders that
file as XML and does not generate or overwrite it with the fallback feed.

## Jekyll Compatibility Mode

Use `--jekyll` or set `output_mode` to `"jekyll"` to build a Jekyll source tree
directly:

```bash
md2html --jekyll website -o _site
md2html --jekyll website -o _site --serve
```

This mode reads `_config.yml` and uses the existing site discovery, content
renderer, layouts, includes, Liquid environment, pagination, feed, execution
cache, dependency graph, watcher, and server. Markdown pages still support all
md2html directives and executable source examples. HTML and HTM pages use
Liquid without an added Markdown pass.

Ordinary Jekyll pages require YAML front matter; supported files without it are
copied unchanged. Dated files in `_posts` become posts. The default post URL is
`/:categories/:year/:month/:day/:title.html`, while `_config.yml` or page
permalinks may replace it. Tags and categories are normalized to lists.
`site.posts`, `site.pages`, `site.tags`, `site.categories`, pagination fields,
and common URL filters are available to Liquid.

Jekyll's standard cache, package, `_site`, and vendored dependency paths are
excluded. `_config.yml` `include` and `exclude` entries are honored. Local
`_layouts` and `_includes` are used; Ruby plugins and theme-provided templates
or assets are not executed. A local `feed.xml` is rendered when present;
otherwise md2html writes its small Atom feed.

The compatibility subset does not implement custom collections, `_data`,
front-matter defaults, Sass conversion, or plugin generators.

### Adapting A Jekyll Layout

Compatibility mode is intended to provide most of a useful preview without
reimplementing a Jekyll theme, its Sass pipeline, or its plugins. Existing
layouts remain responsible for their own stylesheets and scripts. md2html does
not discover, replace, suppress, or inject layout assets in this mode.

If a layout already loads browser MathJax, select `math.backend: "mathjax"` so
the layout renders the preserved TeX source. Static CommonHTML, SVG, and MathML
remain available for sites whose layouts are written to use those forms. The
feature booleans listed above are available to layouts that deliberately want
different behavior under md2html, but no compatibility condition is required.

## Static Files And Exclusions

Directory builds copy static files while preserving their relative paths.
HTML builds render discovered page sources and do not copy `md2html.json`,
private paths, layouts, includes, or post sources. In native site mode every
supported document is a page. In Jekyll mode ordinary supported documents
without front matter remain static files and are copied unchanged. Configured
exclusions are also skipped.

An output directory below the source tree is excluded from discovery and
copying, so `md2html -r . -o html` does not read `html` again. The build rejects
an output directory equal to the input. It also rejects `--clean` when the
input is inside the directory that would be removed.

## Watch And Serve

`--watch` performs an initial build, then watches source and dependency
directories. `--serve` does the same and starts an HTTP server on `127.0.0.1`.
Both commands keep running until interrupted.

The initial watch build skips a page when its output is at least as new as its
source. `--force` disables that skip. No execution cache is needed for this
decision.

The page dependency graph follows Markdown includes, source directives, Liquid
includes and layouts, templates, selected CSS, and local CSS imports. Rebuilding
a page replaces its dependency edges. A newly created or otherwise unknown
file causes a complete project build so new pages and assets are discovered.

Static files use direct source-to-output copy links. Changing an image or other
static asset updates its output without rerendering unrelated pages. Deleting
such an asset removes its output copy. Generated page output, copied assets,
`.md2html-cache`, `node_modules`, Git data, Python bytecode, and the complete
output tree are ignored by the watcher.

When several scattered pages are served together, md2html exposes only their
generated pages and copied assets. It does not serve the whole common source
directory. It prints one preview URL for each generated HTML page.

## Built-In Starters

```bash
# Print this README from the installed command.
md2html --readme

# Write a starter config to md2html.json.
md2html --example-config

# Write an editable single-file HTML template to templates/page.html.
md2html --example-template

# Write complete editable CSS to templates/page.css.
md2html --example-css
```

Pass a path to any example command to choose another destination. Pass `-` to
print it to standard output. Existing files are not overwritten unless
`--force` is present.

## Python API

```python
from pathlib import Path
from md2html2 import Project, Settings

settings = Settings.single(Path("article.md"))
result = Project(settings).build()
print(result.written)
```

`Settings` is immutable. Use `Settings.single()` for one page, construct
`Settings` for a directory, or use `load_settings()` from `md2html2.settings`
to read `md2html.json`.

`Project.build()` returns a `BuildResult` containing written files, copied
files, skipped pages, warnings, dependencies grouped by source page, and direct
source-to-output asset copy links. Pass a set of source paths as `only` to
rebuild selected pages. Pass `skip_unchanged=True` for the initial watch-style
timestamp check.

## Behavior And Limits

Source execution runs local commands through `sh`. Keep execution disabled for
untrusted Markdown and source files. md2html HTML-escapes cached output before
adding it to a page.

The static-site mode implements pages, dated posts, layouts, includes,
permalinks, common Liquid expressions and filters, tags, categories, static
files, and a small Atom feed. It does not run Ruby Jekyll, themes, plugins,
collections, Sass, or arbitrary Liquid extensions. It does not emit Jekyll
Markdown in static-site mode; use the separate `jekyll-markdown` output mode
when Jekyll should perform the later rendering stages.

Browser-side MathJax requires network access when the page is opened. Static
CommonHTML requires Node and the installed npm packages while building. SVG
and MathML use Python packages and do not require a TeX installation.
