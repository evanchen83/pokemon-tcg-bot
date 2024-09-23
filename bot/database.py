from sqlalchemy import Column, Integer, PrimaryKeyConstraint, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from bot import config

DATABASE_URL = f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@postgres:5432/{config.POSTGRES_DB}"

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
Base = declarative_base()


class PlayerCards(Base):
    __tablename__ = "player_cards"

    discord_id = Column(String, nullable=False)
    card_name = Column(String, nullable=False)
    card_image_url = Column(String, nullable=False)
    count = Column(Integer, default=0)

    __table_args__ = (PrimaryKeyConstraint("discord_id", "card_name"),)


class SchemaVersion(Base):
    __tablename__ = "schema_version"

    version = Column(String(10), nullable=False, primary_key=True)


Session = sessionmaker(bind=engine)


def _ensure_schema_version_compatibility():
    with Session() as session, session.begin():
        actual_schema_version = session.query(SchemaVersion).first().version
        if actual_schema_version != config.DB_SCHEMA_VERSION:
            raise Exception(
                f"Expected schema version {config.DB_SCHEMA_VERSION}, but got {actual_schema_version}."
            )


_ensure_schema_version_compatibility()
