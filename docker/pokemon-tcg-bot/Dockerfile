FROM python:3.11.1-slim

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock /app/

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy the entire bot folder into the image
COPY bot /app/bot

# Set the command to run the bot
CMD ["python", "-m", "bot.start_bot"]