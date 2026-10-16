FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
COPY packages packages
COPY apps/api apps/api
COPY apps/worker/pyproject.toml apps/worker/pyproject.toml
RUN mkdir -p apps/worker/src/dcs_worker && touch apps/worker/src/dcs_worker/__init__.py \
 && uv sync --frozen --no-dev --package dcs-api
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/apps/api
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --retries=20 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status==200 else 1)" || exit 1
CMD ["sh", "-c", "alembic upgrade head && uvicorn dcs_api.main:app_factory --factory --host 0.0.0.0 --port 8000"]
