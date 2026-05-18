# Makefile
# BetBot AI - Docker Management Makefile

.PHONY: up down build logs migrate seed test shell-backend shell-db restart clean \
        ps pull lint format check-env setup

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN  := \033[36m
GREEN := \033[32m
RESET := \033[0m

## help: Show this help message
help:
	@echo "$(CYAN)BetBot AI - Available Commands$(RESET)"
	@echo "================================="
	@grep -E '^##' $(MAKEFILE_LIST) | sed 's/## //' | column -t -s ':'

# ============================================================
# Core Docker Commands
# ============================================================

## up: Start all services in detached mode
up: check-env
	@echo "$(GREEN)Starting BetBot AI services...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)Services started. Backend: http://localhost:8000  Frontend: http://localhost:3000$(RESET)"

## down: Stop all services
down:
	@echo "$(CYAN)Stopping BetBot AI services...$(RESET)"
	docker-compose down

## build: Build all Docker images
build:
	@echo "$(CYAN)Building Docker images...$(RESET)"
	docker-compose build --no-cache

## logs: Follow logs from all services
logs:
	docker-compose logs -f

## logs-backend: Follow backend logs only
logs-backend:
	docker-compose logs -f backend

## logs-worker: Follow celery worker logs only
logs-worker:
	docker-compose logs -f celery_worker

## ps: Show running containers
ps:
	docker-compose ps

## pull: Pull latest base images
pull:
	docker-compose pull

# ============================================================
# Database Commands
# ============================================================

## migrate: Run Alembic database migrations
migrate:
	@echo "$(CYAN)Running database migrations...$(RESET)"
	docker-compose exec backend alembic upgrade head
	@echo "$(GREEN)Migrations complete.$(RESET)"

## migrate-down: Rollback last migration
migrate-down:
	docker-compose exec backend alembic downgrade -1

## migrate-history: Show migration history
migrate-history:
	docker-compose exec backend alembic history --verbose

## seed: Seed the database with sample data
seed:
	@echo "$(CYAN)Seeding database with sample data...$(RESET)"
	docker-compose exec backend python /app/scripts/seed_db.py
	@echo "$(GREEN)Database seeded successfully.$(RESET)"

## shell-db: Open a psql shell in the postgres container
shell-db:
	docker-compose exec postgres psql -U $${POSTGRES_USER:-betbot} -d $${POSTGRES_DB:-betbot}

# ============================================================
# Application Shells
# ============================================================

## shell-backend: Open a bash shell in the backend container
shell-backend:
	docker-compose exec backend bash

## shell-frontend: Open a sh shell in the frontend container
shell-frontend:
	docker-compose exec frontend sh

## shell-redis: Open a redis-cli session
shell-redis:
	docker-compose exec redis redis-cli

# ============================================================
# Testing
# ============================================================

## test: Run backend test suite
test:
	@echo "$(CYAN)Running backend tests...$(RESET)"
	docker-compose exec backend pytest backend/tests/ -v --tb=short

## test-coverage: Run tests with coverage report
test-coverage:
	docker-compose exec backend pytest backend/tests/ -v --cov=app --cov-report=html --cov-report=term-missing

## test-unit: Run unit tests only
test-unit:
	docker-compose exec backend pytest backend/tests/ -v -m "unit"

## test-integration: Run integration tests only
test-integration:
	docker-compose exec backend pytest backend/tests/ -v -m "integration"

# ============================================================
# Code Quality
# ============================================================

## lint: Run linting checks
lint:
	docker-compose exec backend flake8 app/ --max-line-length=100
	docker-compose exec backend mypy app/ --ignore-missing-imports

## format: Auto-format code with black and isort
format:
	docker-compose exec backend black app/ backend/tests/
	docker-compose exec backend isort app/ backend/tests/

# ============================================================
# Lifecycle
# ============================================================

## restart: Restart all services (down then up)
restart: down up

## restart-backend: Restart only the backend service
restart-backend:
	docker-compose restart backend celery_worker celery_beat

## clean: Stop services and remove all volumes (DESTRUCTIVE)
clean:
	@echo "$(CYAN)WARNING: This will delete all data including the database.$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose down -v --remove-orphans
	@echo "$(GREEN)All containers and volumes removed.$(RESET)"

## clean-force: Stop services and remove all volumes without confirmation
clean-force:
	docker-compose down -v --remove-orphans

# ============================================================
# Setup
# ============================================================

## setup: First-time project setup (copy .env, build, up, migrate, seed)
setup:
	@echo "$(CYAN)Setting up BetBot AI for the first time...$(RESET)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN).env file created from .env.example — please edit it with your secrets.$(RESET)"; \
	else \
		echo ".env already exists, skipping copy."; \
	fi
	$(MAKE) build
	$(MAKE) up
	@echo "$(CYAN)Waiting for services to be healthy...$(RESET)"
	@sleep 10
	$(MAKE) migrate
	$(MAKE) seed
	@echo "$(GREEN)Setup complete!$(RESET)"
	@echo "  Backend API:  http://localhost:8000/docs"
	@echo "  Frontend:     http://localhost:3000"

## check-env: Ensure .env file exists
check-env:
	@if [ ! -f .env ]; then \
		echo "$(CYAN).env not found. Copying from .env.example...$(RESET)"; \
		cp .env.example .env; \
		echo "$(GREEN).env created. Edit it with your real credentials before proceeding.$(RESET)"; \
	fi
