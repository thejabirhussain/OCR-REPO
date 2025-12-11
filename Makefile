.PHONY: help build up down restart logs test clean init-db migrate

help:
	@echo "Available commands:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - Show logs"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean up volumes and containers"
	@echo "  make init-db    - Initialize database"
	@echo "  make migrate    - Run database migrations"
	@echo "  make download-models - Download ML models"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

test:
	docker-compose exec backend pytest
	docker-compose exec frontend npm test

clean:
	docker-compose down -v
	docker system prune -f

init-db:
	docker-compose exec backend alembic upgrade head

migrate:
	docker-compose exec backend alembic revision --autogenerate -m "$(msg)"
	docker-compose exec backend alembic upgrade head

download-models:
	docker-compose exec backend python scripts/download_models.py




