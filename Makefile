.PHONY: help run test clean docs lock down bump-patch bump-minor bump-major

help:
	@echo "Available targets:"
	@echo "  build      - Build Docker image"
	@echo "  run        - Run container locally"
	@echo "  test       - Run tests"
	@echo "  clean      - Remove containers and images"
	@echo "  down       - Stop running containers"
	@echo "  docs       - Serve documentation locally"
	@echo "  lock       - Update uv.lock file"
	@echo "  bump-patch - Bump patch version (0.1.0 -> 0.1.1)"
	@echo "  bump-minor - Bump minor version (0.1.0 -> 0.2.0)"
	@echo "  bump-major - Bump major version (0.1.0 -> 1.0.0)"

lock:
	docker run --rm -v $(PWD):/app -w /app docker.io/astral/uv:python3.13-bookworm-slim uv lock

uv.lock: pyproject.toml
	docker run --rm -v $(PWD):/app -w /app docker.io/astral/uv:python3.13-bookworm-slim uv lock

build: uv.lock
	docker compose build

run:
	docker compose up vertex-block -d

test:
	docker compose run --rm vertex-block pytest

clean:
	docker compose down --rmi local

docs:
	docker compose up docs -d

down:
	docker compose down

bump-patch:
	bump2version patch

bump-minor:
	bump2version minor

bump-major:
	bump2version major
