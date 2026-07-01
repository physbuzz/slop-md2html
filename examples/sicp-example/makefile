MD2HTML ?= $(HOME)/.local/bin/md2html
JEKYLL ?= jekyll

.PHONY: html jekyll

all: html jekyll

html:
	$(MD2HTML) -e -r src -o html

jekyll:
	$(MD2HTML) -e -r src --format jekyll -o jekyll

clean:
	rm -r html
