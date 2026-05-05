FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.3.3

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi --no-root

COPY backend/ ./backend/
COPY bot/ ./bot/
COPY run_bot.py .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "run_bot.py"]
