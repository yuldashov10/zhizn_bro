.PHONY: install run bot migrate test build up down logs shell celery clean project_tree

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.DS_Store" -delete
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	@echo "Cleaned up temporary files."

project_tree:
	tree -a -I ".venv|.git|.vscode|.idea|node_modules|migrations|.mypy_cache|__pycache__|htmlcov"

install:
	poetry install

run:
	cd backend && poetry run python manage.py runserver

bot:
	poetry run python run_bot.py

migrate:
	cd backend && poetry run python manage.py makemigrations
	cd backend && poetry run python manage.py migrate

test:
	cd backend && poetry run pytest tests/ -v

celery:
	cd backend && poetry run celery -A backend worker --loglevel=info

celery-beat:
	cd backend && poetry run celery -A backend beat --loglevel=info

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	cd backend && poetry run python manage.py shell

createsuperuser:
	cd backend && poetry run python manage.py createsuperuser


add_basic_sys_criteria:
	cd backend && poetry run python manage.py upload_fakedata --users=0 --candidates=0 --events=0
