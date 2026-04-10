.PHONY: install run bot migrate test build up down logs shell celery celery-beat \
        clean project_tree lint format check createsuperuser \
        add_basic_sys_criteria clear_db fakedata setup_tasks

# ── Переменные ────────────────────────────────────────────────────────────────
PYTHON     = poetry run python
MANAGE     = cd backend && $(PYTHON) manage.py
LINT_DIRS  = bot backend tests

# ── Установка ─────────────────────────────────────────────────────────────────
install:
	poetry install

# ── Разработка ────────────────────────────────────────────────────────────────
run:
	$(MANAGE) runserver

bot:
	$(PYTHON) run_bot.py

shell:
	$(MANAGE) shell

createsuperuser:
	$(MANAGE) createsuperuser

# ── База данных ───────────────────────────────────────────────────────────────
migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

add_basic_sys_criteria:
	$(MANAGE) upload_fakedata --users=0 --candidates=0 --events=0

fakedata:
	$(MANAGE) upload_fakedata

clear_db:
	$(MANAGE) clear_fakedata --confirm

setup_tasks:
	$(MANAGE) setup_periodic_tasks

# ── Тесты ─────────────────────────────────────────────────────────────────────
test:
	cd backend && $(PYTHON) -m pytest tests/ -v

test-cov:
	cd backend && $(PYTHON) -m pytest tests/ -v --cov=apps --cov-report=html
	@echo "Coverage report: backend/htmlcov/index.html"

# ── Качество кода ─────────────────────────────────────────────────────────────
format:
	$(PYTHON) -m isort $(LINT_DIRS)
	$(PYTHON) -m black $(LINT_DIRS)

lint:
	$(PYTHON) -m flake8 $(LINT_DIRS)

check:
	$(MANAGE) check
	$(PYTHON) -m flake8 $(LINT_DIRS)
	$(PYTHON) -m isort $(LINT_DIRS) --check-only
	$(PYTHON) -m black $(LINT_DIRS) --check

# ── Celery ────────────────────────────────────────────────────────────────────
celery:
	cd backend && $(PYTHON) -m celery -A backend worker --loglevel=info

celery-beat:
	cd backend && $(PYTHON) -m celery -A backend beat --loglevel=info

# ── Docker ────────────────────────────────────────────────────────────────────
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose down && docker-compose up -d

# ── Утилиты ───────────────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.DS_Store" -delete
	rm -rf .mypy_cache .pytest_cache backend/htmlcov
	@echo "Cleaned up temporary files."

project_tree:
	tree -a -I ".venv|.git|.vscode|.idea|node_modules|migrations|.mypy_cache|__pycache__|htmlcov"
