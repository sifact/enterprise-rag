# One container: FastAPI serves the API and the built React app.
# Build prerequisites (local): `make setup` has fetched the corpus and built the search index,
# so data/index, data/cache/models and data/raw/manifest.jsonl exist in the build context.

FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev
COPY configs ./configs
COPY eval/golden ./eval/golden
COPY eval/runs ./eval/runs
COPY eval/fixtures ./eval/fixtures
COPY data/raw/manifest.jsonl ./data/raw/manifest.jsonl
COPY data/index ./data/index
COPY data/cache/models ./data/cache/models
COPY --from=web /web/dist ./web/dist
RUN useradd --create-home app && chown -R app /app
USER app
ENV PATH="/app/.venv/bin:$PATH" PORT=8000 HF_HUB_OFFLINE=1
EXPOSE 8000
# GROQ_API_KEY and SESSION_SECRET come from the host's secret settings at run time.
CMD ["sh", "-c", "enterprise-rag serve --host 0.0.0.0 --port ${PORT}"]
