# md2html

`md2html` is a small Python page-builder for Markdown notes that need a little more than ordinary Markdown: protected TeX math, Obsidian image embeds, recursive includes, compact exercise-aware tables of contents, source-code embedding, optional source execution, and a simple static-site CLI.

The implementation is intentionally organized as a package rather than a single script. The renderer pipeline is:

1. Parse YAML frontmatter.
2. Expand `@include(path)` recursively with dependency tracking and circular-include detection.
3. Convert Obsidian image embeds such as `![[img/diagram.svg|width=70%|class=center]]`.
4. Scan headings, generate stable slugs, and replace `@toc` with a compact HTML directory.
5. Protect `$...$` and `$$...$$` math so Markdown does not parse underscores or emphasis inside TeX.
6. Expand `@src(...)` and `@src-begin(...)` code directives with Pygments highlighting and optional execution.
7. Render Markdown with Mistune.
8. Restore math spans and wrap the output in a template.

## Install locally

This project uses `pyproject.toml` for packaging and dependency metadata. That is why
there is no hand-maintained dependency list in the old style; the runtime
requirements are declared under `[project].dependencies`.

For normal local use:

```bash
python -m pip install .
```

For development, install the package in editable mode with the `dev` extra:

```bash
python -m pip install -e ".[dev]"
```

To build a single-file executable and copy it to `~/.local/bin/md2html`:

```bash
make install
```

The PyInstaller build bundles the default templates and CSS. Resource lookup uses `package_resource_path(...)`, so template/assets paths work both from source and from the frozen executable.

## Project layout

The top-level directories are intentionally separated:

```text
md2html/   importable package and bundled runtime assets
tests/     pytest test suite
examples/  demo Markdown, demo code, and rendered sample output
```

Rendered demos live in `examples/rendered/` so generated HTML does not sit beside
the package source.

The example build configuration lives at `examples/md2html.json`. To render the
examples into `examples/_site/`:

```bash
make examples
```

To remove that generated example site:

```bash
make examples-clean
```

Inside `md2html/`, the main boundaries are:

```text
builder.py      document build orchestration and public result objects
cli.py          argument parsing, source discovery, and job planning
config.py       typed build options and config-file loading
context.py      per-build dependencies, diagnostics, assets, and path lookup
directives.py   shared @include/@src parsing plus include expansion
code.py         source embedding and optional source execution
graph.py        article-level dependency graph for dry-run/watch
rendering.py    Mistune rendering, TOC, slugs, math, images, highlighting, templates
paths.py        shared lenient path resolution and source-output paths
watch.py        watchdog rebuild loop and development server
```

## CLI examples

```bash
md2html note.md
md2html note.md -o index.html
md2html file1.md file2.md -o html/
md2html -r src -o html
md2html -r . -o _site --serve
md2html note.md --dry-run
md2html note.md --format jekyll
md2html note.md --execute
```

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

Includes are resolved relative to the current Markdown file first, then the project root. Include cycles raise an error.

```md
@include(_partials/header.md)
```

### `@src(path[, flags...])`

Embeds a source file. If `--execute` is enabled, the source is run when the sibling `.out` file is missing or older than the source; otherwise the existing `.out` file is reused. If execution is disabled but the `.out` file exists, the output is embedded.

The display policy is intentionally simple:

```md
@src(code/ex2-77.rkt)              # expanded, not collapsible
@src(code/ex2-77.rkt, collapsible) # expanded, collapsible
@src(code/ex2-77.rkt, collapsed)   # collapsed, collapsible
@src(example.py, lang=python, caption="Runnable example")
```

Default execution commands are provided for Python, shell, Node, Racket, C, and C++. The watch graph records direct article edges like `main.cpp -> page.md` and, when present, `main.out -> page.md`; it does not scan inside `main.cpp` for C/C++ header dependencies. You can override or add commands in `md2html.json`:

```json
{
  "code": {
    "commands": {
      "rkt": "racket {src}",
      "py": "python {src}"
    },
    "timeout": 10
  }
}
```

### `@src-begin(lang, godbolt)`

Embeds an inline code block. Close with `@src-end`.

```md
@src-begin(cpp, godbolt)
#include <iostream>
int main(){ std::cout << "Hello, world!\n"; }
@src-end
```

### Obsidian images

```md
![[img/ex3-10.svg|width=70%|alt=Environment diagram|class=centered]]
```

## Configuration

A minimal `md2html.json` can look like this:

```json
{
  "input": "notes",
  "output": "_site",
  "recursive": true,
  "embed_assets": true,
  "execute": false,
  "images": {
    "class": "note-image",
    "width": "70%"
  }
}
```

## Python API

```python
from pathlib import Path
from md2html import MarkdownSiteBuilder, BuildOptions

builder = MarkdownSiteBuilder(BuildOptions(project_root=Path.cwd()))
result = builder.build_file(Path("note.md"), Path("note.html"))
print(result.as_dict())
```

## Implemented now versus extension points

Implemented now: MathJax output, math shielding, `@toc`, recursive `@include`, circular include errors, Obsidian image embeds, Pygments highlighting, plain/collapsible/collapsed source blocks, optional source execution, `.out` embedding, a small article-level dependency graph, Jekyll-style output, default templates, dry-run JSON, watchdog-powered watch mode, output-directory exclusions for site builds, a development server, and `make install` for a PyInstaller executable.

Designed as extension points: MathML/SVG math backends, richer Godbolt URL state generation, stronger sandboxing for executed code, and production-grade live browser reload. The dependency graph is intentionally not a general build-system DAG. It models Markdown `@include` relationships and direct article dependencies like `@src(main.cpp) -> page.md`; it does not inspect language-level dependencies such as C/C++ headers or Racket imports.
