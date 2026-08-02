PYTHON ?= python3
VENV ?= .venv
VENV_BIN := $(VENV)/bin

.PHONY: help setup test test-lab lint clean

help:
	@echo "targets:"
	@echo "  setup     create $(VENV) and install the package with dev extras"
	@echo "  test      run every test in labs/"
	@echo "  test-lab  run one lab, for example: make test-lab LAB=labs/00-setup"
	@echo "  lint      run ruff if it is available"
	@echo "  clean     remove caches, build output, and the virtualenv"

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/python -m pip install --upgrade pip
	$(VENV_BIN)/python -m pip install -e ".[dev]"
	@echo "done. activate with: source $(VENV_BIN)/activate"
	@echo "then copy .env.example to .env and add your API key"

test:
	pytest labs -v

test-lab:
	@if [ -z "$(LAB)" ]; then \
		echo "usage: make test-lab LAB=labs/00-setup"; \
		exit 1; \
	fi
	pytest $(LAB)/tests -v

lint:
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check .; \
	else \
		echo "ruff is not installed, skipping lint."; \
		echo "ruff is optional and is not a runtime dependency of this repo."; \
		echo "install it separately with: pip install ruff"; \
	fi

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache build dist $(VENV)
	find labs -name "*.sqlite3" -delete
