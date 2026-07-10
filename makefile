.PHONY: install test clean

install:
	python3 -m venv .venv
	.venv/bin/pip install -e '.[dev]'
	npm install

test:
	.venv/bin/python -m pytest -q

clean:
	rm -rf build dist *.egg-info .pytest_cache
