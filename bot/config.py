from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    owner_id: str
    discord_token: str

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_pool_size: int
    postgres_max_overflow: int

    db_schema_version: str = "1.0.0"

    model_config = SettingsConfigDict(env_file=".env")


config = Settings()
