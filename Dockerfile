FROM ghcr.io/astral-sh/uv:0.12.23 AS uv
FROM python:3.12-slim

COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable \
    && useradd --create-home --uid 10001 agent \
    && mkdir /app/var \
    && chown agent:agent /app/var
ENV PATH="/app/.venv/bin:$PATH"
USER agent
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"
CMD ["uvicorn", "agent_app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
