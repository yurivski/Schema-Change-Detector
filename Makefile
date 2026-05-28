UV ?= uv

install:
	$(UV) sync --extra dev --extra postgres

test:
	$(UV) run pytest -v

test-cov:
	$(UV) run pytest --cov=driftbrake --cov-report=term-missing --cov-report=html

lint:
	$(UV) run ruff check src tests

format:
	$(UV) run ruff format src tests

typecheck:
	$(UV) run mypy src

check:
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test

fix:
	$(UV) run ruff check --fix src tests
	$(UV) run ruff format src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov dist build

.PHONY: install test test-cov lint format typecheck check fix clean
