# md2html 2.0

`md2html` turns Markdown notes into standalone HTML pages or a small static
site. It's aimed at quick math notes, so on my personal computer I can do
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

The npm packages provide MathJax and its CommonHTML fonts. They are needed only
for the `mathjax-chtml` backend. That backend also requires a `node` executable
at build time. The browser-side `mathjax` backend does not run Node, but its
generated page loads MathJax from a CDN when opened.

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

# Use settings from another JSON file.
md2html --config path/to/md2html.json
```

With one Markdown file and no `-o`, md2html writes an `.html` file beside the
source. HTML, HTM, and XML preserve their suffixes, so pass `-o` or build them
as part of a directory to keep source and output separate. If an output would
overwrite its source, md2html skips that page, prints a warning, and continues
building other pages. With several inputs and `-o public`, it preserves their
paths relative to their common directory below `public`.

`-o` and `--output` are equivalent. `--output-mode pages` builds independent
pages; `--output-mode site` builds layouts and site data. The CLI value
overrides `output_mode` from JSON. Use `--version` to print the installed
version and `--help` to print all options.

A directory input writes to `html` unless `-o` or configuration chooses another
directory. Add `-r` to include nested Markdown. Directory builds use shared CSS
by default. Several file inputs remain self-contained unless `-o` or
`--shared-assets` collects them below one output directory.
Set `"shared_assets": false` in a directory configuration to embed CSS in each
page instead.

`--execute`, `--recursive`, `--force`, and `--serve` have the short forms `-e`,
`-r`, `-f`, and `-s`, so `-erf` combines the first three. `--watch` rebuilds
without starting a server. `--serve` starts a loopback-only server and also
rebuilds. Use `--port` to change its port.

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

  "templates": "templates",
  "template": "page.html",
  "css": ["styles/base.css"],
  "stylesheets": ["styles/print.css"],
  "feature_css": true,
  "parse_liquid": true,
  "shared_assets": true,
  "highlight_style": "default",
  "highlight_dark_style": "github-dark",

  "math": {
    "backend": "mathjax-chtml",
    "chtml_fonts": "auto"
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
| `output_mode` | `"pages"` for independent templated pages or `"site"` for layouts, posts, and a site model. |
| `recursive` | Read supported documents in nested directories. Site mode enables this by default. |
| `parse_liquid` | Render Liquid in source documents. Templates and layouts always use Liquid. The default is `true`. |
| `shared_assets` | Write common page CSS to `assets/md2html/page.css`. Directory page builds enable this by default. |
| `clean` | Remove the output directory before a complete site build. |
| `exclude` | Skip matching source paths. Exact paths, directory prefixes, and path patterns are accepted. |

### Templates And Styles

These keys control independent page output. Static-site mode uses its own
layouts and stylesheet links; generated CommonHTML assets are still added when
needed.

| Key | Meaning |
| --- | --- |
| `templates` | Search this directory before `_templates` and the bundled templates. |
| `template` | Select the standalone page template. The default is `page.html`. |
| `css` | Replace the template's base CSS with one path or a list. `null` selects companion or bundled CSS; `[]` selects no base CSS. |
| `stylesheets` | Add one or more `<link rel="stylesheet">` entries. Relative local files are watched and copied with moved standalone output. |
| `feature_css` | Add CSS for generated code, output, math, tables of contents, images, and warnings. The default is `true`. |
| `highlight_style` | Select a Pygments style name for light syntax highlighting. |
| `highlight_dark_style` | Select a Pygments style name for dark and automatic dark-mode highlighting. |

### Math And Execution

| Key | Meaning |
| --- | --- |
| `math.backend` | Select `mathjax`, `mathjax-chtml`, `svg`, `mathml`, or `raw`. |
| `math.chtml_fonts` | Select `auto`, `all`, `inline`, `remote`, or `none` for static CommonHTML fonts. |
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
| `parse_liquid` | Set to `false` to leave Liquid expressions in this document unchanged. Templates and layouts still render. |
| `layout` | Select a static-site layout from `_layouts`. Layouts may select another layout. |
| `permalink` | Set a static-site URL and output path. A trailing slash writes `index.html`. |
| `date` | Set a post date. ISO dates and YAML date values are accepted. |
| `tags`, `categories` | Add a post to the corresponding `site` groups. Strings and lists are accepted. |

Source pages may use Liquid expressions such as `{{ page.title }}` and
`{{ site.title }}`. Markdown protects raw code, fenced code, inline code, and
math before evaluating Liquid, so braces in Mathematica and other languages
remain literal. Use `{% raw %}...{% endraw %}` to protect a smaller Liquid
region explicitly.

Pass `--no-liquid` or set `"parse_liquid": false` in JSON to leave Liquid
unchanged in every source document. A page may opt out with front matter
`parse_liquid: false`; a page cannot override a global opt-out. Templates and
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
clearer.

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
.md2html-cache/pages/PAGE_OUTPUT/LANGUAGE-SOURCE_CHECKSUM/
```

For example, executable blocks in `guide/index.html` use
`.md2html-cache/pages/guide/index.html/`. md2html copies inline source into its
workspace. File-backed source is referenced from that workspace. Compilers,
executables, images, and other files made with relative paths remain there and
do not pollute the source directory.

The cache key uses the source text. It does not include checkout paths,
interpreter paths, commands, settings, or md2html metadata. Changing source
text selects a new workspace. Use `--execute --force` after changing a command,
compiler, runtime, or other external input that should refresh existing output.

md2html saves successful output as `output.txt` and marks it complete. Later
builds include it even when execution is disabled. A CI job can restore or
check out `.md2html-cache` and build pages without installing compilers or
enabling execution:

```bash
md2html --config md2html.json
```

If an `execute` block has no completed output while execution is disabled,
md2html builds the page and prints a warning explaining how to populate it.
After a successful page render, it removes block workspaces no longer used by
that page. A complete directory build also removes cache directories for pages
that no longer exist. A parse or rendering failure preserves that page's cache.

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

The default `mathjax` backend loads browser-side MathJax only on pages that use
math. Select another backend with `--math` or `math.backend`:

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

### CommonHTML Fonts

Set `--math-fonts MODE` or `math.chtml_fonts` when using `mathjax-chtml`:

| Mode | Behavior |
| --- | --- |
| `auto` | Copy and preload only fonts used by each directory/site page. Standalone pages use the matching CDN fonts and remain one file. |
| `all` | Copy every CommonHTML font for a directory/site build, but preload only fonts used by each page. |
| `inline` | Embed used fonts as data URLs in the generated stylesheet. |
| `remote` | Use CDN fonts for standalone and shared builds. |
| `none` | Omit font files and `@font-face` rules. |

Directory and site builds share `assets/md2html/mathjax-chtml.css` and store
local fonts below `assets/md2html/mathjax/woff2/` when the selected mode uses
local files. The stylesheet contains glyph metrics collected after typesetting
and only the font faces used by the build. Pages preload only their own fonts.

Serve generated HTML and CSS with gzip or Brotli compression. Static
CommonHTML markup compresses well, and shared font files can be cached across
pages and visits.

## Templates And CSS

The bundled templates are:

- `page.html` (default): A centered reading page with reader controls, print
  styles, and a filename header.
- `barebones.html`: A simpler centered reading page without the reader widget.

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
automatically when no explicit `css` setting is present. Use another filename
or directory if you want several designs:

```bash
md2html --example-template templates/report.html
md2html --example-css templates/report.css
md2html --template report --templates templates article.md
```

The example commands do not replace files unless `--force` is present. Pass
`-` as the destination to print an example to standard output.

### Template Lookup

For standalone pages, md2html searches the configured `templates` directory,
then the project `_templates` directory, then the bundled templates. A name
without an extension receives `.html`.

Static-site layouts use the same order and also search the source `_layouts`
directory before the bundled templates. Liquid includes search the configured
template directory, `_templates`, `_includes`, `_layouts`, and the bundled
templates.

### CSS Layers

The default template embeds CSS so one input produces one self-contained HTML
file. Base CSS and generated feature CSS are separate:

```bash
# Replace base CSS but keep CSS for code, math, TOCs, images, and warnings.
md2html --css styles/base.css article.md

# Combine several base files.
md2html --css styles/base.css --css styles/print.css article.md

# Keep base CSS but omit generated feature CSS.
md2html --no-feature-css article.md

# Omit both groups.
md2html --no-css article.md

# Add an external stylesheet link.
md2html --stylesheet styles/site.css article.md
```

Use `"css": ["styles/base.css"]` to replace the selected template's default
CSS. Use `"css": []` to disable template CSS while keeping feature CSS. Set
`"feature_css": false` to disable feature CSS too. The corresponding CLI
options are `--css`, `--no-feature-css`, and `--no-css`. Renderer-required
CommonHTML CSS is still emitted when static math needs it.

Directory builds and `--shared-assets` write common CSS to
`assets/md2html/page.css` and link to it from each ordinary page. A page with
its own `template` or `css` front matter embeds its selected CSS instead.

Local CSS files and their local `@import` dependencies are watched. Local
stylesheet links and referenced page assets are copied when an independent
page's output is moved.

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
code highlighting.

Highlighted fences use a `codehilite` wrapper. Source directives use a
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
| `md2html.css` | CSS selected for this page, or an empty value. |
| `md2html.stylesheets` | Stylesheet hrefs selected for this page. |
| `md2html.use_mathjax` | True when this page needs browser-side MathJax. |

The bundled templates show the required Liquid structure for `<title>`, CSS,
MathJax, the filename header, and rendered content.

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

## Static Site Builds

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
site pattern fields are `:year`, `:month`, `:day`, and `:title`. A permalink
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

`site.pages` contains every discovered page. `site.posts` contains posts in
reverse date order. `site.tags` and `site.categories` map each name to its
posts. `site.tag_list` contains sorted objects with `name`, `slug`, and `posts`
fields. Each page exposes its front matter, URL, source path, filename, excerpt,
tags, and categories through `page`.

`relative_url` adds `site.baseurl` to a path. `absolute_url` adds both
`site.url` and `site.baseurl`. `site.time` contains the build time.

Site mode writes a small `feed.xml` containing the twenty newest posts. Add a
source `feed.xml` to replace it with a custom Liquid feed. md2html renders that
file as XML and does not generate or overwrite it with the fallback feed.

### Static Files And Exclusions

Directory builds copy static files while preserving their relative paths.
They do not copy Markdown sources, `md2html.json`, files or directories whose
names begin with `.` or `_`, or sources under `_layouts`, `_includes`, and
`_posts`. Supported page documents are rendered instead. The configured
`exclude` entries are also skipped.

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
Markdown as a separate output format.

Browser-side MathJax requires network access when the page is opened. Static
CommonHTML requires Node and the installed npm packages while building. SVG
and MathML use Python packages and do not require a TeX installation.
