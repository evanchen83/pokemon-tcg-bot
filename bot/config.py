import os

from dotenv import load_dotenv

load_dotenv()

OWNER_ID = os.environ["OWNER_ID"]
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

DB_SCHEMA_VERSION = "1.0.0"
