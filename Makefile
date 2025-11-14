.PHONY: help install dev test lint format clean run docker-up docker-down migrate

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pre-commit install

test: ## Run tests
	pytest -v --cov=app --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	pytest tests/unit -v

test-integration: ## Run integration tests only
	pytest tests/integration -v

lint: ## Run linting checks
	flake8 app/ tests/
	mypy app/

format: ## Format code with black
	black app/ tests/
	isort app/ tests/

clean: ## Clean cache and temporary files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache/

run: ## Run the application locally
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f api

docker-restart: ## Restart Docker containers
	docker-compose restart

init-db: ## Initialize database with sample data
	python scripts/init_db.py

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration
	@read -p "Enter migration name: " name; \
	alembic revision --autogenerate -m "$$name"

migrate-rollback: ## Rollback last migration
	alembic downgrade -1

api-key: ## Generate new API key
	@read -p "Enter name: " name; \
	read -p "Enter email: " email; \
	read -p "Enter tier (free/starter/growth/enterprise): " tier; \
	python scripts/generate_api_key.py --name "$$name" --email "$$email" --tier "$$tier"

shell: ## Open Python shell with app context
	python -i -c "from app.db.base import SessionLocal; from app.models import *; db = SessionLocal()"

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U bridge_user -d bridge_aggregator

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

check: format lint test ## Run all checks (format, lint, test)
