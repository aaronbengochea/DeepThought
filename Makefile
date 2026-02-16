COMPOSE = docker compose --env-file ./backend/.env --env-file ./frontend/.env

.PHONY: up down build database seed dev frontend-dev test lint

# Full stack
build:
	$(COMPOSE) build

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

# Individual services
database:
	$(COMPOSE) up -d dynamodb-local

seed: database
	@sleep 2
	$(COMPOSE) run --rm seed

# Local development (without Docker for backend/frontend)
dev: database
	@sleep 2
	$(COMPOSE) run --rm seed
	@echo "Starting backend on port 8080..."
	@cd backend && uvicorn src.deepthought.api.app:create_app --factory --reload --port 8080 &
	@echo "Starting frontend on port 3000..."
	@cd frontend && npm run dev &
	@echo ""
	@echo "Dev servers running:"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8080"

frontend-dev:
	cd frontend && npm run dev

# Quality
test:
	cd backend && pytest

lint:
	cd backend && ruff check src/ && ruff format --check src/ && mypy src/
