MD2HTML ?= $(HOME)/.local/bin/md2html

.PHONY: all html jekyll clean

all: html jekyll

html:
	$(MD2HTML) -e -r src -o html

jekyll:
	$(MD2HTML) -e -r src --format jekyll -o jekyll

clean:
	rm -rf html jekyll
