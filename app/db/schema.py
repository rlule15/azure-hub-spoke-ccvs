# TODO Implement schema for database
from datetime import datetime, timezone

from app.db.db_config import Base

# from app.db.db_config import Base
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(150), nullable=False)
    team: Mapped[str] = mapped_column(String(10), nullable=False)


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    move: Mapped[str] = mapped_column(String(10), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    game_turn: Mapped[int] = mapped_column(Integer, nullable=False)
    team: Mapped[str] = mapped_column(String(10), nullable=False)


class GameState(Base):
    __tablename__ = "game_state"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    current_turn: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    board_fen: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    )
    active_team: Mapped[str] = mapped_column(String(10), nullable=False)
    winning_vote_id: Mapped[int] = mapped_column(ForeignKey("votes.id"), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
