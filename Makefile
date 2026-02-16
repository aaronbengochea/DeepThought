COMPOSE = docker compose --env-file ./backend/.env --env-file ./frontend/.env

.PHONY: up down build database seed \
        dev dev-backend dev-frontend \
        install install-backend install-frontend \
        test test-backend test-frontend \
        lint

# ---------------------------------------------------------------------------
# Full stack (Docker)
# ---------------------------------------------------------------------------

build:
	$(COMPOSE) build --no-cache

up: build
	$(COMPOSE) up -d
	@echo ""
	@echo "Services running:"
	@echo "  Frontend:     http://localhost:3000"
	@echo "  Backend:      http://localhost:8080"
	@echo "  API docs:     http://localhost:8080/docs"
	@echo "  DynamoDB:     http://localhost:8000"
	@echo "  DynamoDB GUI: http://localhost:8001"

down:
	$(COMPOSE) down

# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

database:
	$(COMPOSE) up -d dynamodb-local dynamodb-admin

seed: database
	@sleep 2
	$(COMPOSE) run --rm seed

# ---------------------------------------------------------------------------
# Dependency installation
# ---------------------------------------------------------------------------

install: install-backend install-frontend

install-backend:
	cd backend && .venv/bin/pip install -e ".[dev]"

install-frontend:
	cd frontend && npm install

# ---------------------------------------------------------------------------
# Local development (without Docker for app servers)
# ---------------------------------------------------------------------------

dev: database seed
	@echo "Starting backend on port 8080..."
	@cd backend && .venv/bin/uvicorn src.deepthought.api.app:create_app --factory --reload --port 8080 &
	@echo "Starting frontend on port 3000..."
	@cd frontend && npm run dev &
	@echo ""
	@echo "Dev servers running:"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8080"

dev-backend: database seed
	cd backend && .venv/bin/uvicorn src.deepthought.api.app:create_app --factory --reload --port 8080

dev-frontend:
	cd frontend && npm run dev

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: test-backend test-frontend

test-backend:
	cd backend && .venv/bin/pytest

test-frontend:
	cd frontend && npm run build

# ---------------------------------------------------------------------------
# Linting & type checking
# ---------------------------------------------------------------------------

lint:
	cd backend && .venv/bin/ruff check src/ && .venv/bin/ruff format --check src/ && .venv/bin/mypy src/
