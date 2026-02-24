FROM python:3.13-slim AS base

COPY --from=docker.io/astral/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

FROM base AS test

RUN uv sync --frozen --extra dev

COPY src/ ./src/
COPY tests/ ./tests/

FROM base AS prod

RUN uv sync --frozen

COPY src/ ./src/

EXPOSE 53/udp
EXPOSE 53/tcp

CMD ["uv", "run", "python", "-m", "vertex_block.main"]
