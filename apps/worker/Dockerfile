FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
COPY packages/common packages/common
COPY apps/worker apps/worker
COPY apps/api/pyproject.toml apps/api/pyproject.toml
RUN mkdir -p apps/api/src/dcs_api && touch apps/api/src/dcs_api/__init__.py \
 && uv sync --frozen --no-dev --package dcs-worker
ENV PATH="/app/.venv/bin:$PATH"
CMD ["arq", "dcs_worker.settings.WorkerSettings"]
