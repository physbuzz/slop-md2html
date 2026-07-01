MD2HTML ?= $(HOME)/.local/bin/md2html
JEKYLL ?= jekyll

.PHONY: all html jekyll

all: html jekyll

html:
	$(MD2HTML) -e -r src -o html

jekyll:
	$(MD2HTML) -e -r src --format jekyll -o jekyll

clean:
	rm -r html
	find jekyll -mindepth 1 -maxdepth 1 ! -name '_layouts' -exec rm -rf -- {} +
