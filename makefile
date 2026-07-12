PYTHON ?= .venv/bin/python
NPM ?= npm
APP_NAME ?= md2html
LOCAL_BIN ?= $(HOME)/.local/bin

.PHONY: install pyinstaller test clean

install: pyinstaller
	mkdir -p "$(LOCAL_BIN)"
	install -m 755 "dist/$(APP_NAME)" "$(LOCAL_BIN)/$(APP_NAME)"
	@echo "Installed $(APP_NAME) to $(LOCAL_BIN)/$(APP_NAME)"

pyinstaller:
	$(PYTHON) -m pip install -e '.[build]'
	$(NPM) install
	$(PYTHON) -m PyInstaller --clean md2html.spec

test:
	.venv/bin/python -m pytest -q

clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -type d -name .md2html-cache -prune -exec rm -rf {} +
