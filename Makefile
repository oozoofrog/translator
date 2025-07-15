# 개발 자동화 Makefile

.PHONY: test lint format coverage clean

test:
	pytest tests/unit

lint:
	flake8 epub_extractor

format:
	black epub_extractor tests/unit
	isort epub_extractor tests/unit

coverage:
	pytest --cov=epub_extractor tests/unit --cov-report=term-missing

clean:
	rm -rf .pytest_cache __pycache__ .mypy_cache .coverage 