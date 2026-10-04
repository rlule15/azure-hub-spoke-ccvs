from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.db.schema as schema
from app.core.chess_engine import ChessManager
from app.core.security import verify_session
from app.db.db_config import get_db
from app.models.votes_model import VoteCreate, VoteResponse

router = APIRouter()


@router.post("/vote", response_model=VoteResponse, status_code=201)
def cast_vote(
    vote: VoteCreate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[int, Depends(verify_session)],
):
    # get current game state and user info
    game_state = db.query(schema.GameState).first()
    user = db.query(schema.User).filter(schema.User.id == user_id).first()

    if not game_state:
        raise HTTPException(status_code=500, detail="Game state not initialized")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # check if it's the user's team's turn
    if user.team != game_state.active_team:
        raise HTTPException(
            status_code=403,
            detail=f"It is currently {game_state.active_team}'s turn to vote.",
        )

    # check if user has already voted for this turn
    existing_vote = (
        db.query(schema.Vote)
        .filter_by(user_id=user_id, game_turn=game_state.current_turn)
        .first()
    )
    if existing_vote:
        raise HTTPException(
            status_code=400, detail="User has already voted for this turn"
        )

    # check if move is legal for the current game state
    engine = ChessManager(game_state.board_fen)
    is_valid, error_message = engine.make_move(vote.move)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # 5. SAVE: Include the team in the vote record
    new_vote = schema.Vote(
        user_id=user_id,
        game_turn=game_state.current_turn,
        move=vote.move,
        team=user.team,
    )

    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)

    return new_vote
