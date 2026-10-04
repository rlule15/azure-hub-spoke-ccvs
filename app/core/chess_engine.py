import chess
import chess.svg

import app.db.schema as schema


class ChessManager:
    def __init__(self, fen: str):
        self.board = chess.Board(fen)

    def make_move(self, move: str):
        try:
            try:
                self.board.push_san(move)
            except ValueError:
                self.board.push_uci(move)
            return True, None
        except ValueError:
            return False, "Invalid move format or illegal move."

    def get_board_state(self):
        return self.board.fen()

    def check_game_over(self):
        if self.board.is_checkmate():
            return "checkmate"
        if self.board.is_stalemate():
            return "stalemate"
        if self.board.is_insufficient_material():
            return "insufficient_material"
        if self.board.is_game_over():
            return "draw_or_other"
        return "ongoing"

    def get_winner(self):
        if self.board.is_checkmate():
            # If it's black's turn, white just moved and delivered mate
            return "white" if not self.board.turn else "black"
        return None

    def get_legal_moves(self):
        return [self.board.san(move) for move in self.board.legal_moves]


def start_game(session):
    db = session
    # Check if a game already exists
    existing_game = db.query(schema.GameState).first()
    if existing_game:
        print(f"Game already in progress with FEN: {existing_game.board_fen}")
        return

    # Create the starting state
    new_game = schema.GameState(
        current_turn=1,
        # Default starting position
        board_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        active_team="white",
    )

    db.add(new_game)
    db.commit()
    db.refresh(new_game)

    print(f"New game started with FEN: {new_game.board_fen}")


def generate_board_svg(fen: str, last_updated):
    engine = ChessManager(fen)

    svg = chess.svg.board(
        board=engine.board,
        size=450,
        lastmove=engine.board.peek() if engine.board.move_stack else None,
        check=engine.board.king(engine.board.turn) if engine.board.is_check() else None,
    )

    svg = svg.replace('height="400"', 'height="425"')
    svg = svg.replace('viewBox="0 0 400 400"', 'viewBox="0 0 400 425"')

    if last_updated:
        # Format the timestamp
        time_str = last_updated.strftime("%b %d, %I:%M %p")

        text_element = f'<text x="0" y="400" font-family="sans-serif" font-size="10" fill="white">Last updated: {time_str}</text>'
        svg = svg.replace("</svg>", f"{text_element}</svg>")

    return svg
