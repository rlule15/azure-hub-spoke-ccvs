from pydantic import BaseModel


class GameBase(BaseModel):
    fen: str


class GameResponse(GameBase):
    status: str
    turn: str
    current_turn: int
    last_updated: str | None


class GameMove(BaseModel):
    legal_moves: list[str]
