from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

import app.db.schema as schema
from app.core.chess_engine import ChessManager, generate_board_svg
from app.db.db_config import get_db
from app.models.game_model import GameMove, GameResponse

router = APIRouter()


@router.get("/status", response_model=GameResponse, status_code=200)
def get_game_status(db: Annotated[Session, Depends(get_db)]):
    game_state = db.query(schema.GameState).first()
    if not game_state:
        raise HTTPException(status_code=404, detail="No game in progress")

    # Sync the engine with the database state
    engine = ChessManager(game_state.board_fen)

    return {
        "status": engine.check_game_over(),
        "turn": "white" if engine.board.turn else "black",
        "fen": game_state.board_fen,
        "current_turn": game_state.current_turn,
        "last_updated": game_state.last_updated.isoformat()
        if game_state.last_updated
        else None,
    }


@router.get("/available_moves", response_model=GameMove, status_code=200)
def get_available_moves(db: Annotated[Session, Depends(get_db)]):
    game_state = db.query(schema.GameState).first()
    if not game_state:
        raise HTTPException(status_code=404, detail="No game in progress")

    engine = ChessManager(game_state.board_fen)

    move = engine.get_legal_moves()
    return {"legal_moves": move}


@router.get("/board.svg")
def get_board_svg(db: Annotated[Session, Depends(get_db)]):
    game_state = db.query(schema.GameState).first()
    if not game_state:
        raise HTTPException(status_code=404, detail="No game in progress")

    svg = generate_board_svg(game_state.board_fen, game_state.last_updated)

    return Response(content=svg, media_type="image/svg+xml")
