FROM python:3.11.1-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy Poetry configuration files from the project root
COPY pyproject.toml poetry.lock /app/

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi
