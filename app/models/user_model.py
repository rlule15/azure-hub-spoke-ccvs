# TODO Implement user model
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=100)
    username: str = Field(min_length=3, max_length=100)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    team: str


class UserMe(UserResponse):
    participation: float
    vote_alignment: float
