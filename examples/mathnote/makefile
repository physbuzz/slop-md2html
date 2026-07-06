PYTHONPATH = ../..
MD2HTML ?= PYTHONPATH=$(PYTHONPATH) ../../.venv/bin/python -m md2html

.PHONY: all clean

all: raysinglass.html raysinglass-barebones.html raysinglass-super-barebones.html raysinglass-custom.html

raysinglass.html: raysinglass.md
	$(MD2HTML) raysinglass.md

raysinglass-barebones.html: raysinglass.md
	$(MD2HTML) --override-template barebones.html raysinglass.md -o raysinglass-barebones.html

raysinglass-super-barebones.html: raysinglass.md
	$(MD2HTML) --override-template super-barebones.html raysinglass.md -o raysinglass-super-barebones.html

raysinglass-custom.html: raysinglass.md templates/mathnote.html templates/mathnote.css
	$(MD2HTML) --templates templates --override-template mathnote.html raysinglass.md -o raysinglass-custom.html

clean:
	rm -f raysinglass.html raysinglass-barebones.html raysinglass-super-barebones.html raysinglass-custom.html
