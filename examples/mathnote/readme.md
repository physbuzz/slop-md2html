# Mathnote example

This example renders one math-heavy Markdown note to standalone HTML using the default reader template, the two simpler bundled templates, and one custom template.

Run the examples from this directory:

```sh
make
```

The makefile keeps the commands deliberately close to what a person would type:

- `$(MD2HTML) raysinglass.md` builds `raysinglass.html` with the default `page.html` reader template.
- `$(MD2HTML) --override-template barebones.html raysinglass.md -o raysinglass-barebones.html` builds the non-reader page.
- `$(MD2HTML) --override-template super-barebones.html raysinglass.md -o raysinglass-super-barebones.html` builds the nearly plain page.
- `$(MD2HTML) --templates templates --override-template mathnote.html raysinglass.md -o raysinglass-custom.html` builds with the local custom template and its same-name companion CSS.

The custom template does not need a config file. `--templates templates` adds a local template directory, and `--override-template mathnote.html` selects `templates/mathnote.html`. md2html automatically embeds `templates/mathnote.css` because it has the same basename.

The source note uses YAML front matter for page metadata and an Obsidian-style image embed for the ray diagram.
