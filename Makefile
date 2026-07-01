PYTHON ?= python
APP_NAME ?= md2html
LOCAL_BIN ?= $(HOME)/.local/bin

.PHONY: install pyinstaller test clean

install: pyinstaller
	mkdir -p "$(LOCAL_BIN)"
	install -m 755 "dist/$(APP_NAME)" "$(LOCAL_BIN)/$(APP_NAME)"
	@echo "Installed $(APP_NAME) to $(LOCAL_BIN)/$(APP_NAME)"

pyinstaller:
	$(PYTHON) -m pip install -e ".[build]"
	$(PYTHON) -m PyInstaller \
		--name "$(APP_NAME)" \
		--onefile \
		--clean \
		--collect-all pygments \
		--collect-all mistune \
		--collect-all jinja2 \
		--collect-all watchdog \
		--add-data "md2html/assets:md2html/assets" \
		--add-data "md2html/default_templates:md2html/default_templates" \
		md2html/__main__.py

test:
	$(PYTHON) -m pytest -q

clean:
	rm -rf build dist *.spec .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
