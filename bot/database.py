from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from bot.config import config

DATABASE_URL = f"postgresql://{config.postgres_user}:{config.postgres_password}@postgres:5432/{config.postgres_db}"

engine = create_engine(
    DATABASE_URL,
    pool_size=config.postgres_pool_size,
    max_overflow=config.postgres_max_overflow,
)


class Base(DeclarativeBase):
    pass


class PlayerCards(Base):
    __tablename__ = "player_cards"

    discord_id = Column(String, primary_key=True, nullable=False)
    card_name = Column(String, primary_key=True, nullable=False)
    card_image_url = Column(String, nullable=False)
    count = Column(Integer, default=0)


class SchemaVersion(Base):
    __tablename__ = "schema_version"

    version = Column(String(10), primary_key=True, nullable=False)


Session = sessionmaker(bind=engine)


def _ensure_schema_version_compatibility():
    with Session() as session, session.begin():
        actual_schema_version = session.query(SchemaVersion).first().version
        if actual_schema_version != config.db_schema_version:
            raise Exception(
                f"Expected schema version {config.db_schema_version}, but got {actual_schema_version}."
            )


_ensure_schema_version_compatibility()
