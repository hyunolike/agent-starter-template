# Contributing

Start with the [English README](README.md) or [한국어 README](docs/README.ko.md).

## Local workflow

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv run python evals/evaluate.py
```

Create a branch from the repository's current default branch (`develop`). Keep each change focused and explain the behavior it changes in the pull request.

## Project conventions

- Keep tool adapters thin and business logic independently testable.
- Use async I/O in tools and return bounded, JSON-serializable dictionaries.
- Add meaningful regression cases when fixing runtime behavior.
- Keep paid API calls out of default tests and CI.
- Update English and Korean README when setup, configuration, or scope changes.
- Update `uv.lock` with `uv lock` when dependencies change.
- Do not commit keys, real customer data, checkpoint databases, or `.env` files.

For new infrastructure or a framework change, explain the concrete requirement before adding another dependency. Optional extensions should preserve the small local quick start.
