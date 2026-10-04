# TODO Implement votes processing logic
import csv
import os
from datetime import datetime, timezone

import git
from sqlalchemy import desc, func
from sqlalchemy.sql.functions import count

from app.core.chess_engine import ChessManager

# import backend.app.db.schema as schema
from app.db import schema
from app.db.db_config import get_session

# Tip: CVS is a pharmacy, CSV is a file format! ;)
CURRENT_WD = os.getcwd()
CSV_FILE = os.path.join(CURRENT_WD, "app", "data", "game_history.csv")


def process_daily_votes():
    db = get_session()
    # Check existence here or inside the "if success" block
    file_exists = os.path.isfile(CSV_FILE)

    try:
        game_state = db.query(schema.GameState).first()
        if not game_state:
            print("No active game.")
            return

        # 1. Query for the winning move and its count
        winning_move_query = (
            db.query(
                schema.Vote.move,
                count(schema.Vote.id).label("vote_count"),
                func.max(schema.Vote.id).label("representative_vote_id"),
            )
            .filter(
                schema.Vote.game_turn == game_state.current_turn,
                schema.Vote.team == game_state.active_team,
            )
            .group_by(schema.Vote.move)
            .order_by(desc("vote_count"), schema.Vote.move.asc())
            .first()
        )

        if not winning_move_query:
            print(
                f"No votes for {game_state.active_team} on turn {game_state.current_turn}."
            )
            return

        # 2. Extract both values from the query result
        winning_move, vote_count, winning_id = winning_move_query

        # Capture current turn/team before incrementing for the log
        logged_turn = game_state.current_turn
        logged_team = game_state.active_team

        # 3. Apply move via Engine
        engine = ChessManager(game_state.board_fen)
        success, error = engine.make_move(winning_move)

        if success:
            # Update Database state
            game_state.board_fen = engine.board.fen()
            game_state.current_turn += 1
            game_state.active_team = "white" if engine.board.turn else "black"
            game_state.last_updated = datetime.now(timezone.utc)
            game_state.winning_vote_id = winning_id

            # 4. Write to CSV with the vote count
            with open(CSV_FILE, mode="a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                if not file_exists:
                    writer.writerow(
                        [
                            "timestamp",
                            "turn_number",
                            "team",
                            "move",
                            "vote_count",
                            "new_fen",
                        ]
                    )

                writer.writerow(
                    [
                        datetime.now(timezone.utc).isoformat(),
                        logged_turn,
                        logged_team,
                        winning_move,
                        vote_count,  # Added the count here
                        game_state.board_fen,
                    ]
                )

            db.commit()
            print(f"Move {winning_move} ({vote_count} votes) executed.")

            push_votes_to_git()

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


def push_votes_to_git():
    try:
        repo = git.Repo(os.path.dirname(CURRENT_WD))
        repo.git.add(CSV_FILE)
        repo.index.commit(f"Update game history with latest votes - {datetime.now()}")
        origin = repo.remote(name="origin")
        origin.push()
        print("Votes pushed to Git repository.")
    except Exception as e:
        print(f"Git push failed: {e}")


if __name__ == "__main__":
    process_daily_votes()
