# md2html and md2html2 feature audit

## Summary

md2html2 covers the core md2html renderer and static-site workflow with about
57% less production Python: approximately 2,362 lines instead of 5,534. Its
architecture is better organized around immutable settings, one project model,
one content renderer, and one execution/cache implementation.

The audit identified the following changes, which are now implemented:

1. Static CommonHTML is again the default, while browser MathJax, SVG, MathML,
   and raw math remain selectable.
2. Embedded and generated shared CSS is minified by default.
3. Global Obsidian image class and width defaults are available.
4. Configured template directories are ordered and repeatable.
5. Templates receive explicit booleans describing the features used by a page.
6. The stale README statement about Jekyll Markdown output was corrected.

Compiler Explorer links, dry-run output, directive key/value arguments, and the
old Python API intentionally remain outside the current design.

The execution cache, Liquid/document ordering, Jekyll compatibility model,
dependency tracking, asset handling, error recovery, and watch/serve behavior
are materially better in md2html2. Restoring every original configuration knob
would add complexity without improving the central architecture.

Both current test suites pass: 149 tests in md2html and 74 tests in md2html2.

## Feature comparison

| Area | Original md2html | md2html2 | Assessment |
| --- | --- | --- | --- |
| Default math | Static MathJax CommonHTML | Static MathJax CommonHTML | Restored. Browser MathJax, SVG, MathML, and raw output remain configurable. |
| Execution workspace | Inline code is copied to a temporary source; file sources execute from their source directory | Inline source is copied into its cache workspace; file-backed `{source}` refers to the original file while commands run in the cache workspace | Intended behavior. Relative imports and includes retain their ordinary meaning while generated products stay in the cache. |
| Directive arguments | Supports `lang=`, `caption=`, `compiler=`, `options=`, and quoted CSV arguments | Intentionally recognizes comma-separated flags only | The smaller flag-only syntax is the intended API. |
| Compiler Explorer | Supports `godbolt`, short links, client-state URLs, and compiler options | Not implemented | A separable missing feature rather than a core rendering problem. |
| Dry run | `--dry-run` emits jobs and the dependency graph as JSON without writing | Not implemented | A useful diagnostic feature that was explicitly deferred. |
| CSS minification | Embedded CSS is minified by default and can be left readable | Embedded and generated shared CSS is minified by default; `--no-minify-css` preserves readable output | Restored without adding a CSS-processing dependency. |
| Default image attributes | Global `images.class` and `images.width` settings | The same defaults are supported, with per-image width taking precedence and classes appended | Restored. |
| Template feature inspection | Exposes generic `features` and `uses` structures | Exposes explicit booleans such as `md2html.has_code`, `has_toc`, and `uses_svg_math` | The newer names are more direct and do not expose renderer-only state. |

The default math difference is defined in `md2html2/settings.py`. Execution is
implemented in `md2html2/render.py`: inline source is written into the
workspace, while file-backed source remains in its article project so relative
imports and includes continue to work.

## Original-only commands and configuration

The following original md2html features are not present in md2html2:

- `--no-overwrite`
- `--verbose`
- `--dry-run`
- `--strict`
- `--site` as a command-line alias
- an explicit `math.backend: none`
- YAML and YML md2html configuration files
- `copy_assets` and `embed_assets` switches
- configurable source-cache enablement
- Jekyll Markdown controls for math passthrough versus pre-rendered HTML
- automatic Jekyll compatibility stylesheet output
- optional Jekyll Markdown fence highlighting
- a separately configured Jekyll Markdown default layout
- the named `super-barebones.html` starter
- the old `MarkdownSiteBuilder` and mutable `BuildOptions` Python API

Most of these are policy options rather than architectural gaps. Strict mode,
execution-cache dependency edges, dry-run behavior, and directive arguments
were explicitly deprioritized. YAML configuration, mutable options, and asset
switches would increase the public surface without strengthening the rendering
model.

The `super-barebones` use case can mostly be expressed with the current
`barebones` template, `--no-css`, and `--no-feature-css`. The `raw` math backend
also covers much of the practical use case of the original `none` backend.

## Behavior changes that are not necessarily regressions

### Inline execution

Original md2html executes an inline block only when it carries the `execute`
flag. md2html2 executes source blocks whenever global execution is enabled,
unless they carry `noexecute`. The current md2html2 behavior was previously
accepted and does not need to change.

### Cache invalidation

The md2html2 execution workspace is selected primarily by source content.
Changing a command requires `--force`. This avoids machine- and checkout-specific
cache invalidation and makes uploaded CI caches portable, at the cost of not
automatically detecting command changes.

### Asset copying

md2html2 copies required assets automatically instead of exposing the original
`copy_assets` policy switch. This removes configuration but also removes a way
to suppress copying.

### Error handling

md2html2 omits the original strict mode. Its normal recovery policy better
matches the intended behavior: report warnings and visible page errors where a
build can continue, and abort a page only when malformed source structure makes
safe continuation or cache cleanup impossible.

## Improvements in md2html2

### Execution and caching

The new execution model provides:

- a page-shaped `.md2html-cache/pages/...` hierarchy;
- stable and portable workspaces;
- `{source}`, `{filename}`, `{sourcedir}`, `{builddir}`, `{slug}`,
  `{executable}`, `{output}`, and `{python}` command placeholders;
- containment of compiler products and other generated files;
- cached output when execution is disabled, including in CI;
- completion markers that distinguish valid output from failed execution;
- stale snippet and deleted-page cleanup;
- cleanup after recoverable execution failures; and
- protection against unsafe cleanup after malformed source structures.

This behavior is concentrated in one `Executor` class instead of being divided
among cache, command, graph, and directive modules.

### Rendering pipeline

md2html2 has distinct and consistently ordered document paths:

- `.md` and `.markdown` files receive directives, optional Liquid, Markdown,
  and template or layout processing;
- `.html`, `.htm`, and `.xml` files receive optional Liquid without an added
  Markdown pass;
- front matter is optional in native mode;
- ordinary pages require front matter in Jekyll compatibility mode;
- `render_with_liquid: false` disables Liquid in the current document without
  disabling its layout or template;
- `--no-liquid` disables source Liquid for the whole build;
- fenced code, inline code, comments, raw `pre` blocks, and highlight blocks
  are protected before directives and Liquid;
- adjacent blockquotes are normalized to the expected rendering; and
- malformed single-line `@src(...)` tags produce visible page errors while the
  rest of the page continues.

### Native and Jekyll sites

md2html2 distinguishes four output workflows while sharing the same project
and rendering machinery:

- standalone or directory pages;
- native static sites;
- direct Jekyll-compatible site builds; and
- Markdown prepared for Jekyll to finish.

The shared implementation supports dated posts, compatible URLs, permalinks,
layouts and layout inheritance, includes, tags, categories, tag and category
lists, `site.posts`, `site.pages`, pagination, paginator fields, local
`feed.xml` Liquid rendering, a generated Atom fallback, `_config.yml` includes
and excludes, `published: false`, static files, and common URL filters.

This is a genuine architectural improvement over maintaining a separate large
Jekyll site builder.

### Watch and serve

md2html2 tracks more useful live dependencies:

- recursive Markdown includes;
- Liquid includes and layouts;
- templates and selected CSS;
- local CSS imports;
- direct source dependencies;
- static source-to-output copy links;
- removed copied assets; and
- replacement of stale dependency edges after a rebuild.

An unknown or newly created file causes project discovery to run again. Serving
several scattered pages exposes only their generated pages and copied assets,
not the common source directory. The original dry-run visualization is better,
but md2html2's live incremental behavior is better.

### Assets and generated pages

Other improvements include:

- shared page CSS for directory builds;
- `--assets shared`, `--assets standalone`, and `--assets cdn`;
- automatic relocation of standalone-page assets;
- static CommonHTML font selection and preload pruning;
- a remote CommonHTML font mode;
- site-wide MathJax CSS deduplication;
- pruning of obsolete math assets;
- `--clean`;
- separate example config, template, and CSS commands;
- `--version`;
- output-collision warnings that allow unrelated pages to continue; and
- protection against source-to-output self-overwrites.

## Jekyll limitations

md2html2 remains a compatibility subset rather than an implementation of Ruby
Jekyll. It does not currently implement:

- custom collections;
- `_data`;
- `_config.yml` front-matter defaults;
- themes;
- Sass conversion;
- plugin generators or arbitrary Liquid extensions; or
- drafts and future-post policy beyond `published: false`.

These are not regressions from original md2html, which also did not implement
them.

## Performance comparison

The Gaussian-integral stress page was built from the same source and measured
with maximum gzip compression:

| Renderer | HTML bytes | Gzip bytes |
| --- | ---: | ---: |
| Ruby Jekyll reference | 676,833 | 42,640 |
| Original md2html | 678,056 | 42,796 |
| Old md2html redesign | 677,745 | 42,714 |
| md2html2 | 545,158 | 35,576 |

The md2html2 page uses 34,575 bytes of CommonHTML CSS, 5,958 bytes gzipped,
and a complete 22-file local font set. The page preloads seven font families;
its initial compressed HTML, CSS, and preloaded-font payload is 232,546 bytes.
Browser measurements found the same 17-pixel inline
math height, baseline alignment, display overflow behavior, and zero measured
layout shift as the old redesign. The complete page remains visible with
JavaScript disabled.

## Overall assessment

md2html2 is the stronger architecture. The line reduction comes primarily from
removing parallel implementations and routing standalone pages, native sites,
Jekyll sites, templates, assets, dependencies, and execution through a small
set of shared abstractions. It is not mainly a result of compressed naming or
code golfing.

The audit changes preserve the intentional split between cached inline source
and original file-backed source. Directive key/value arguments, Compiler
Explorer, and dry-run output remain deliberately excluded.

The remaining legacy configuration matrix should not be restored wholesale.
Doing so would add policy branches and public API surface and would be the most
likely route back toward the original codebase size.
