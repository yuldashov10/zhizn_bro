.PHONY: install run bot migrate test test-cov \
        build up down logs restart shell \
        celery celery-beat \
        lint format check \
        createsuperuser add_basic_sys_criteria \
        fakedata clear_db setup_tasks health \
        clean project_tree \
        deploy deploy-init \
        prod-logs prod-shell prod-migrate prod-createsuperuser

# ── Переменные ────────────────────────────────────────────────────────────────
PYTHON      = poetry run python
MANAGE      = cd backend && $(PYTHON) manage.py
LINT_DIRS   = bot backend tests
DC          = docker compose
DC_WEB      = $(DC) exec -T web python manage.py

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
	$(PYTHON) -m pytest tests/ -v

test-cov:
	$(PYTHON) -m pytest tests/ -v --cov=apps --cov-report=html
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

# ── Docker (локальная разработка) ─────────────────────────────────────────────
build:
	$(DC) build

up:
	$(DC) up -d

down:
	$(DC) down

logs:
	$(DC) logs -f

restart:
	$(DC) down && $(DC) up -d

# ── Продакшн деплой ───────────────────────────────────────────────────────────

## Первый деплой на сервер (запускается один раз вручную)
deploy-init:
	$(DC) build
	$(DC) up -d db redis
	@echo "⏳ Ждём запуска БД..."
	@sleep 10
	$(DC_WEB) migrate
	$(DC_WEB) createsuperuser
	$(DC_WEB) collectstatic --noinput
	$(DC_WEB) upload_fakedata --users=0 --candidates=0 --events=0
	$(DC_WEB) setup_periodic_tasks
	$(DC) up -d
	@echo "✅ Первый деплой завершён!"

## Обновление (запускается через GitHub Actions или вручную)
deploy:
	$(DC) up -d --build
	$(DC_WEB) migrate
	$(DC_WEB) collectstatic --noinput
	$(DC_WEB) upload_fakedata --users=0 --candidates=0 --events=0
	$(DC_WEB) setup_periodic_tasks
	$(DC) image prune -f
	@echo "✅ Деплой завершён!"

# ── Продакшн утилиты ──────────────────────────────────────────────────────────
prod-logs:
	$(DC) logs -f web bot celery

prod-shell:
	$(DC) exec web python manage.py shell

prod-migrate:
	$(DC_WEB) migrate

prod-createsuperuser:
	$(DC) exec web python manage.py createsuperuser

# ── Health check ──────────────────────────────────────────────────────────────
health:
	@echo "Проверка health check..."
	@curl -s --max-time 5 http://localhost:8000/health/ | python -m json.tool \
		&& echo "" \
		|| echo "❌ Сервер недоступен. Запусти: make run"

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
