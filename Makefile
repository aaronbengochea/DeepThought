.PHONY: allLocal database seed downAllLocal

database:
	docker compose up -d dynamodb-local

seed:
	python scripts/seed_data.py

allLocal: database
	@sleep 2
	$(MAKE) seed
	@echo "Starting server in background on port 8080..."
	@uvicorn src.deepthought.api.app:create_app --factory --reload --port 8080 > /dev/null 2>&1 &
	@echo "Server running at http://localhost:8080"
	@echo "API docs at http://localhost:8080/docs"
	@echo "Use 'make downAllLocal' to stop all services"

downAllLocal:
	@echo "Stopping uvicorn server..."
	@pkill -f "uvicorn.*8080" 2>/dev/null || true
	@echo "Stopping Docker containers..."
	docker compose down
	@echo "All services stopped"
