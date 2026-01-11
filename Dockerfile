FROM python:3.13-slim

COPY --from=docker.io/astral/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY src/ ./src/

EXPOSE 53/udp
EXPOSE 53/tcp

CMD ["uv", "run", "python", "-m", "vertex_block.main"]
