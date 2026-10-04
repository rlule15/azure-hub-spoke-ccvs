# TODO Implement user routes
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.db.schema as schema
from app.core.security import (
    authenticate_user,
    hash_password,
    verify_session,
)
from app.db.db_config import get_db
from app.models.user_model import UserCreate, UserMe, UserResponse

router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=201)
def sign_up(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    exisitng_user = db.execute(
        select(schema.User).where(schema.User.username == user.username)
    ).scalar_one_or_none()
    if exisitng_user:
        raise HTTPException(status_code=400, detail="Username not available")

    count_white = db.query(schema.User).filter(schema.User.team == "white").count()
    count_black = db.query(schema.User).filter(schema.User.team == "black").count()

    if count_white > count_black:
        assigned_team = "black"
    else:
        assigned_team = "white"

    new_user = schema.User(
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        password=hash_password(user.password),
        team=assigned_team,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/signin", response_model=UserResponse, status_code=201)
def sign_in(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    request.session["user_id"] = user.id
    request.session["username"] = user.username

    return user


@router.post("/signout")
def sign_out(request: Request):
    request.session.clear()
    return "Successfully signed out"


@router.get("/me", response_model=UserMe, status_code=201)
def get_me(
    user_id: Annotated[int, Depends(verify_session)],
    db: Annotated[Session, Depends(get_db)],
):
    user = db.execute(
        select(schema.User).where(schema.User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    participation_ratio, vote_alignment = get_stats(user, db)

    user.participation = participation_ratio  # type: ignore
    user.vote_alignment = vote_alignment  # type: ignore
    return user


def get_stats(user: schema.User, db: Session):
    user_vote_count = (
        db.query(schema.Vote).filter(schema.Vote.user_id == user.id).count()
    )
    team_vote_count = (
        db.query(schema.Vote).filter(schema.Vote.team == user.team).count()
    )

    if team_vote_count > 0:
        participation_ratio = user_vote_count / team_vote_count
    else:
        participation_ratio = 0.0

    winning_moves_subquery = (
        db.query(schema.Vote.move, schema.Vote.game_turn, schema.Vote.team)
        .join(schema.GameState, schema.GameState.winning_vote_id == schema.Vote.id)
        .subquery()
    )

    alignment_count = (
        db.query(func.count(schema.Vote.id))
        .join(
            winning_moves_subquery,
            (schema.Vote.game_turn == winning_moves_subquery.c.game_turn)
            & (schema.Vote.team == winning_moves_subquery.c.team)
            & (schema.Vote.move == winning_moves_subquery.c.move),
        )
        .filter(schema.Vote.user_id == user.id)
        .scalar()
        or 0
    )

    if user_vote_count > 0:
        alignment_ratio = alignment_count / user_vote_count
    else:
        alignment_ratio = 0.0

    return participation_ratio, alignment_ratio
