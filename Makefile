.PHONY: install dev test lint build migrate train demo

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	docker-compose up

test:
	cd backend && pytest --cov=app

lint:
	cd backend && flake8 app && mypy app && black --check app

build:
	docker-compose build

migrate:
	cd backend && alembic upgrade head

train:
	cd backend && python -m ml_pipeline.train

demo:
	cd backend && python -m scripts.demo
