PYTHON ?= python
APP_NAME ?= md2html
LOCAL_BIN ?= $(HOME)/.local/bin
EXAMPLES_DIR ?= examples

.PHONY: install pyinstaller test examples examples-clean examples_clean clean

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
		--collect-all frontmatter \
		--add-data "md2html/assets:md2html/assets" \
		--add-data "md2html/default_templates:md2html/default_templates" \
		--add-data "readme.md:." \
		md2html/__main__.py

test:
	$(PYTHON) -m pytest -q

# examples:
# 	cd "$(EXAMPLES_DIR)" && $(PYTHON) -m md2html --config md2html.json
# 
# examples-clean examples_clean:
# 	rm -rf "$(EXAMPLES_DIR)/_site"

clean: examples-clean
	rm -rf build dist *.spec *.egg-info .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
