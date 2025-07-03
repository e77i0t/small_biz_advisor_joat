import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dev:dev123@localhost:5432/comms_platform"
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ECHO = LOG_LEVEL.upper() == "DEBUG"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=ECHO
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 