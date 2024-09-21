from sqlalchemy import Column, Integer, PrimaryKeyConstraint, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from bot import config

DATABASE_URL = f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@postgres:5432/{config.POSTGRES_DB}"

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
Base = declarative_base()


class PlayerCard(Base):
    __tablename__ = "player_cards"

    discord_id = Column(String, nullable=False)
    card_name = Column(String, nullable=False)
    card_image_url = Column(String, nullable=False)
    copies = Column(Integer, default=0)

    __table_args__ = (PrimaryKeyConstraint("discord_id", "card_name"),)


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
