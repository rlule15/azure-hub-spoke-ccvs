# TODO Implement database configuration and connection setup
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DEFAULT_DB_PATH = Path("/app/data/ccvs.db")
DB_PATH = Path(os.environ.get("DB_PATH", DEFAULT_DB_PATH))

DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.resolve()}")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db


def get_session():
    return SessionLocal()
