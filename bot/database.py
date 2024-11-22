from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://testuser:testpwd@postgres:5432/player_db"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=5,
)

Session = sessionmaker(bind=engine)

metadata = MetaData()

player_cards = Table(
    "player_cards",
    metadata,
    Column("discord_id", String, primary_key=True, nullable=False),
    Column("card_id", String, primary_key=True, nullable=False),
    Column("count", Integer, default=0),
)
