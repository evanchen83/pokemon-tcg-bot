from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "postgresql://testuser:testpwd@postgres:5432/player_db"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=5,
)

Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class PlayerCards(Base):
    __tablename__ = "player_cards"

    discord_id = Column(String, primary_key=True, nullable=False)
    card_name = Column(String, primary_key=True, nullable=False)
    card_image_url = Column(String, nullable=False)
    count = Column(Integer, default=0)
