from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    owner_id: int
    discord_token: str

    model_config = SettingsConfigDict(env_file=".env")


config = Settings()
