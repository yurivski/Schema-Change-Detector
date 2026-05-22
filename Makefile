install:
	pip install -e ".[dev]"

test:
	pytest -v

test-cov:
	pytest --cov=schema_change_detector --cov-report=term-missing --cov-report=html

lint:
	ruff check src tests

format:
	ruff format src tests

typecheck:
	mypy src

check:
	lint typecheck test
	ruff check src tests
	mypy src
	pytest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov dist build

.PHONY: install test test-cov lint format typecheck check clean

fix:
	ruff check --fix src tests
	ruff format src tests