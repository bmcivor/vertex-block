.PHONY: help run test clean docs lock

help:
	@echo "Available targets:"
	@echo "  build    - Build Docker image"
	@echo "  run      - Run container locally"
	@echo "  test     - Run tests"
	@echo "  clean    - Remove containers and images"
	@echo "  docs     - Serve documentation locally"
	@echo "  lock     - Update uv.lock file"

lock:
	docker run --rm -v $(PWD):/app -w /app docker.io/astral/uv:python3.13-bookworm-slim uv lock

uv.lock: pyproject.toml
	docker run --rm -v $(PWD):/app -w /app docker.io/astral/uv:python3.13-bookworm-slim uv lock

build: uv.lock
	docker compose build

run:
	docker compose up

test:
	docker compose run --rm vertex-block pytest

clean:
	docker compose down --rmi local

docs:
	docker compose run --rm -p 8000:8000 vertex-block mkdocs serve -a 0.0.0.0:8000
