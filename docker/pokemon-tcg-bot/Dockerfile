FROM python:3.11.1-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY bot /app/bot
COPY data /app/data

CMD ["python", "-m", "bot.start_bot"]