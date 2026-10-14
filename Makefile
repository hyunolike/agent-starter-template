.PHONY: install dev test lint format eval check

install:
	uv sync --frozen

dev:
	uv run uvicorn agent_app.main:create_app --factory --reload --host 127.0.0.1

test:
	uv run pytest -q

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

eval:
	uv run python evals/evaluate.py

check: lint test eval
