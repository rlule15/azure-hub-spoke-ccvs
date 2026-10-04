from pydantic import BaseModel, Field, ConfigDict


class VoteBase(BaseModel):
    move: str = Field(min_length=2, max_length=10)


class VoteCreate(VoteBase):
    pass


class VoteResponse(VoteBase):
    # Allows pydantic to read data using dot notation
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    game_turn: int
    team: str