# 🕶 Жизнь БРО — Без Розовых Очков

> Система рационального принятия решений в сложных жизненных ситуациях.
> Без эмоций. Без иллюзий. Только факты.

[![CI](https://github.com/yuldashov10/zhizn_bro/actions/workflows/ci.yml/badge.svg)](https://github.com/yuldashov10/zhizn_bro/actions/workflows/ci.yml)
[![CD](https://github.com/yuldashov10/zhizn_bro/actions/workflows/cd.yml/badge.svg)](https://github.com/yuldashov10/zhizn_bro/actions/workflows/cd.yml)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.x-green?logo=django)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📖 О проекте

**Жизнь БРО** — Telegram-бот и веб-платформа для рационального принятия решений.

Проект помогает анализировать сложные жизненные ситуации без когнитивных искажений: в отношениях, карьере, финансах и
других сферах.

### Как это работает

1. **Описываете событие** своими словами в Telegram-боте
2. **AI анализирует** событие по критериям и выявляет когнитивные искажения
3. **Вы подтверждаете** или корректируете оценку
4. **Система накапливает** данные и строит объективную картину

### Текущие модули

| Модуль       | Статус          | Описание                              |
|--------------|-----------------|---------------------------------------|
| ❤️ Отношения | ✅ Доступен      | Анализ партнёров, Hard Stops, скоринг |
| 💼 Карьера   | 🔄 В разработке | Анализ офферов и работодателей        |
| 💰 Финансы   | 🔄 В разработке | Рациональный анализ крупных решений   |
| 🌍 Переезд   | 🔄 В разработке | Сравнение городов и стран             |

---

## 🚀 Быстрый старт

### Попробовать бота

Просто откройте [@zhizn_bro_bot](https://t.me/zhizn_bro_bot) в Telegram.

### Запустить локально

**Требования:** Python 3.11+, Poetry 2.x, Docker, Redis

```bash
# Клонируем репозиторий
git clone https://github.com/yuldashov10/zhizn_bro.git
cd zhizn_bro

# Устанавливаем зависимости
poetry install

# Настраиваем окружение
cp .env.example .env
# Заполни .env своими значениями

# Применяем миграции
make migrate

# Заполняем системные данные
make add_basic_sys_criteria

# Запускаем Django
make run

# В отдельном терминале — бот
make bot

# В отдельном терминале — Celery
make celery
```

---

## 🛠 Технологии

### Backend

| Технология            | Версия | Назначение             |
|-----------------------|--------|------------------------|
| Python                | 3.11   | Основной язык          |
| Django                | 5.x    | Web framework          |
| Django REST Framework | 3.x    | REST API               |
| PostgreSQL            | 16     | База данных            |
| Redis                 | 7      | Кэш и брокер сообщений |
| Celery                | 5.x    | Асинхронные задачи     |
| django-constance      | —      | Настройки через Admin  |
| django-celery-beat    | —      | Расписание задач       |

### AI

| Технология           | Назначение           |
|----------------------|----------------------|
| Groq (llama-3.3-70b) | Анализ событий       |
| Pydantic             | Валидация ответов AI |

### Telegram Bot

| Технология  | Назначение             |
|-------------|------------------------|
| aiogram 3.x | Telegram Bot framework |
| httpx       | HTTP клиент для API    |

### Отчёты

| Технология | Назначение      |
|------------|-----------------|
| ReportLab  | Генерация PDF   |
| openpyxl   | Генерация Excel |
| Pillow     | Генерация PNG   |

### DevOps

| Технология     | Назначение        |
|----------------|-------------------|
| Docker         | Контейнеризация   |
| nginx          | Reverse proxy     |
| Let's Encrypt  | SSL сертификаты   |
| GitHub Actions | CI/CD             |
| Sentry         | Мониторинг ошибок |

---

## 📁 Структура проекта

```
zhizn_bro/
├── backend/                 # Django проект
│   ├── ai/                  # AI провайдеры (Groq, Claude, Gemini)
│   │   ├── provider/        # Адаптеры провайдеров
│   │   ├── prompts/         # Промпты
│   │   ├── schemas/         # Pydantic схемы
│   │   └── services/        # Сервис анализа
│   ├── api/v1/              # REST API эндпоинты
│   │   ├── assessments/     # Тесты привязанности
│   │   ├── candidates/      # Кандидаты
│   │   ├── criteria/        # Критерии и Hard Stops
│   │   ├── events/          # События
│   │   ├── reports/         # Отчёты
│   │   └── users/           # Пользователи
│   ├── apps/                # Django приложения
│   │   ├── assessments/     # Тесты привязанности
│   │   ├── candidates/      # Кандидаты
│   │   ├── criteria/        # Критерии и Hard Stops
│   │   ├── events/          # События и скоринг
│   │   ├── reports/         # Отчёты
│   │   └── users/           # Пользователи
│   ├── core/                # Утилиты, исключения, пагинация
│   └── backend/             # Настройки Django
├── bot/                     # Telegram бот (aiogram)
│   ├── client/              # HTTP клиент для API
│   ├── handlers/            # Обработчики сообщений
│   ├── keyboards/           # Клавиатуры
│   ├── middlewares/         # Middleware авторизации
│   └── states/              # FSM состояния
├── tests/                   # Тесты
│   ├── unit/                # Unit тесты
│   └── integration/         # Integration тесты
├── nginx/                   # Конфигурация nginx
├── .github/workflows/       # GitHub Actions CI/CD
├── docker-compose.yml       # Продакшн
├── docker-compose.dev.yml   # Разработка
└── Makefile                 # Команды разработки
```

---

## 🔌 API

Базовый URL: `https://zhizn-bro.ru/api/v1/`

Полная документация эндпоинтов: [docs/ENDPOINTS.md](docs/ENDPOINTS.md)

### Аутентификация

```bash
POST /api/v1/auth/telegram/
{
    "telegram_id": 123456789,
    "username": "username"
}
```

Ответ:

```json
{
  "token": "your-auth-token",
  "created": true
}
```

Все последующие запросы: `Authorization: Token your-auth-token`

---

## ⚙️ Конфигурация

Все переменные окружения описаны в [.env.example](.env.example).

Ключевые переменные:

```bash
# Django
SECRET_KEY=                  # Секретный ключ Django
DEBUG=False                  # Режим отладки
ALLOWED_HOSTS=               # Разрешённые хосты

# База данных
DB_ENGINE=django.db.backends.postgresql
DB_NAME=zhizn_bro
DB_USER=zhizn_bro_user
DB_PASSWORD=
DB_HOST=db
DB_PORT=5432

# AI провайдер
AI_PROVIDER=groq
GROQ_API_KEY=

# Telegram
BOT_TOKEN=
ADMIN_TELEGRAM_ID=

# Мониторинг
SENTRY_DSN=
```

Настройки которые можно менять через Django Admin (django-constance):

| Настройка                   | По умолчанию   | Описание                     |
|-----------------------------|----------------|------------------------------|
| `REPORT_RETENTION_DAYS`     | 30             | Хранить файлы отчётов N дней |
| `WEEKLY_REPORTS_ENABLED`    | True           | Еженедельные автоотчёты      |
| `AI_DAILY_TOKEN_LIMIT_FREE` | 10000          | Дневной лимит токенов        |
| `BOT_USERNAME`              | @zhizn_bro_bot | Username бота                |

---

## 🧪 Тесты

```bash
# Все тесты
make test

# С покрытием
make test-cov

# Только unit тесты
poetry run pytest tests/unit/ -v

# Только integration тесты
poetry run pytest tests/integration/ -v
```

---

## 🐳 Docker

```bash
# Собрать образы
docker compose build

# Запустить все сервисы
docker compose up -d

# Посмотреть статус
docker compose ps

# Логи
docker compose logs -f web bot

# Остановить
docker compose down
```

### Сервисы

| Сервис        | Описание            |
|---------------|---------------------|
| `web`         | Django + Gunicorn   |
| `bot`         | Telegram бот        |
| `celery`      | Celery worker       |
| `celery-beat` | Планировщик задач   |
| `db`          | PostgreSQL 16       |
| `redis`       | Redis 7             |
| `nginx`       | Reverse proxy + SSL |
| `certbot`     | Автообновление SSL  |

---

## 📦 Makefile команды

```bash
make install          # Установить зависимости
make run              # Запустить Django
make bot              # Запустить бота
make migrate          # Создать и применить миграции
make test             # Запустить тесты
make test-cov         # Тесты с покрытием
make format           # Форматирование кода (isort + black)
make lint             # Проверка кода (flake8)
make check            # Полная проверка (Django + lint)
make celery           # Запустить Celery worker
make celery-beat      # Запустить Celery Beat
make add_basic_sys_criteria  # Загрузить системные данные
make setup_tasks      # Настроить периодические задачи
make clean            # Очистить временные файлы
make project_tree     # Показать структуру проекта
```

---

## 🚀 Деплой

### Первый деплой

```bash
# На сервере
git clone https://github.com/yuldashov10/zhizn_bro.git /opt/zhizn_bro
cd /opt/zhizn_bro
cp .env.example .env
nano .env  # Заполни переменные

# Собираем и запускаем
docker compose build
docker compose up -d db redis
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py createsuperuser
docker compose run --rm web python manage.py collectstatic --noinput
docker compose run --rm web python manage.py upload_fakedata --users=0 --candidates=0 --events=0
docker compose run --rm web python manage.py setup_periodic_tasks
docker compose up -d
```

### SSL сертификат

```bash
# Получить сертификат
docker run --rm -p 80:80 \
  -v zhizn_bro_certbot_certs:/etc/letsencrypt \
  -v zhizn_bro_certbot_data:/var/www/certbot \
  certbot/certbot certonly --standalone \
  --email YOUR@email.com --agree-tos --no-eff-email \
  -d YOUR_DOMAIN -d www.YOUR_DOMAIN
```

### CI/CD

Автоматический деплой настроен через GitHub Actions:

```
push в dev → CI (lint + tests) → auto merge в main → CD (деплой на сервер)
```

Необходимые GitHub Secrets:

| Secret              | Описание                     |
|---------------------|------------------------------|
| `SECRET_KEY`        | Django секретный ключ        |
| `BOT_TOKEN`         | Токен Telegram бота          |
| `ADMIN_TELEGRAM_ID` | Telegram ID администратора   |
| `GROQ_API_KEY`      | Ключ Groq API                |
| `SERVER_HOST`       | IP адрес сервера             |
| `SERVER_USER`       | Пользователь сервера         |
| `SERVER_SSH_KEY`    | Приватный SSH ключ           |
| `PAT_TOKEN`         | GitHub Personal Access Token |

---

## 🤝 Contributing

1. Fork репозитория
2. Создай ветку: `git checkout -b feature/my-feature`
3. Сделай изменения и тесты
4. Проверь код: `make check`
5. Запусти тесты: `make test`
6. Создай Pull Request в ветку `dev`

---

## 📄 Лицензия

MIT License — подробности в [LICENSE](LICENSE).

---

## 👨‍💻 Автор

**Шохрух Юлдашов** — [Github](https://github.com/yuldashov10) | [Telegram](t.me/shyuldashov)

> *"Лучшие решения принимаются не на основе чувств, а на основе фактов."*
