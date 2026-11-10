import chess
from engine import SearchEngine

"""
    The point is that the different agents' logic gives higher scores for different board states.
    The evaluator of either agent provides the leaf values for the minimax tree which will choose
        which branch/move to make.
    The rank (0-7) of a piece is how far advanced the piece has moved from it's original end of the board
"""

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}  # according to https://www.chess.com/terms/chess-piece-value

#total material value at the start of the game
START_VALUE = 3900 * 2

def evaluate_attacker(board: chess.Board) -> float:
    """
    Attack-oriented logic (aggressive)
    - Material/piece value is still counted but weighted less (85% of actual value)
    - Higher scores for pieces near the enemy king
    - Higher scores for pawns advanced toward the enemy side of the board
    - Lower score for own exposed king
    Returns score from WHITE's perspective.
    """

    # low score if WHITE is under checkmate, high score if BLACK is under checkmate
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000

    score = 0  # this value determines best move

    """
        for each white piece on the board, add their discounted value to the score
        for each black piece on the board, subtract their discounted value from the score
    """
    for square, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.piece_type] * 0.85
        if piece.color == chess.WHITE:
            score += val
        else:
            score -= val

    # Black and White King positions on board
    bk = board.king(chess.BLACK)
    wk = board.king(chess.WHITE)

    # Bonus score for White pieces near Black King
    for sq, piece in board.piece_map().items():
        if piece.piece_type == chess.KING:
            continue
        """
            if a piece is white, find distance between the piece and the black king
            Bonus for each white piece close to the black king

            Find the distance between the piece and the black king and invert it so that
                a closer/smaller distance gives a larger score and scale by six (closing moves probably)
            Use max between the distance and zero, since a piece more than 7 pieces away would give a negative
                far pieces should contribute zero not a negative (penalty)

            Penalize for each black piece close to the white king
                do the same for black pieces close to the white king but subtract from score

        """
        if piece.color == chess.WHITE and bk is not None:
            dist = chess.square_distance(sq, bk)  # Chebyshev Distance (king-move distance)
            score += max(0, (7 - dist)) * 6

        elif piece.color == chess.BLACK and wk is not None:
            dist = chess.square_distance(sq, wk)
            score -= max(0, (7 - dist)) * 6

    """
        Bonus for pawn advancement
        For each square a white pawn is on, add to score the rank of the pawn multiplied by 8
        For each square a black pawn is on, subtract from the score the rank of the pawn
            from the perspective of the black (7-rank) multiplied by 8
    """
    for sq in board.pieces(chess.PAWN, chess.WHITE):
        rank = chess.square_rank(sq)
        score += rank * 8
    for sq in board.pieces(chess.PAWN, chess.BLACK):
        rank = chess.square_rank(sq)
        score -= (7 - rank) * 8

    # Prioritize White King safety, prefer to keep king on a low rank (near the White end)
    if wk is not None and chess.square_rank(wk) > 0:
        score -= 25
    if bk is not None and chess.square_rank(bk) < 7:
        score += 25

    return score

def material_at_risk(board:chess.Board, sq:chess.Square, piece:chess.Piece) -> int:
    attackers = board.attackers(not piece.color, sq)
    if not attackers:
        return 0
    
    val = PIECE_VALUES[piece.piece_type]
    if not board.attackers(piece.color, sq):
        return val
    
    #king can't capture a defended piece, so ignore it as attacker here
    attacker_vals = [PIECE_VALUES[board.piece_type_at(a)] for a in attackers if board.piece_type_at(a) != chess.KING] 
    
    if not attacker_vals:
        return 0
    return max(0, val - min(attacker_vals))

def evaluate_materialist(board: chess.Board) -> float:
    """
        Material-oriented logic (greedy)
        - Material/piece value counted at full weight
        - Bonus if the side to move can win an undefended/underdefended piece
        - Penalty for own pieces left where they can be taken
        - When ahead, bonus for trading down (fewer pieces left = easier win)
        - Ignores piece placement and pawn structure
        Returns score from WHITE's perspective.
    """
    white_mat = 0
    black_mat = 0
    white_risk = 0
    black_risk = 0
    
    for sq, piece in board.piece_map().items():
        if piece.piece_type == chess.KING:
            continue
        val = PIECE_VALUES[piece.piece_type]
        risk = material_at_risk(board, sq, piece)
        if piece.color == chess.WHITE:
            white_mat += val
            white_risk = max(white_risk, risk)
        else:
            black_mat += val
            black_risk = max(black_risk,risk)
    diff = white_mat - black_mat
    score = diff
    
    total = white_mat + black_mat
    score += diff * 0.2 * (1 - total/ START_VALUE)
    
    if board.turn == chess.WHITE:
        score += 0.8 * black_risk -  0.3 * white_risk
    else: 
        score -= 0.8 * white_risk - 0.3 * black_risk
    
    return score


class AttackerAgent:
    name = "Attacker"

    def __init__(self, depth=3):  # depth determines the depth/height/level of the minimax tree searched
        self.engine = SearchEngine(depth)
        self.eval_fn = evaluate_attacker  # store evaluator function as an attribute

    # called in the gui
    def choose_move(self, board: chess.Board):
        return self.engine.search(board, self.eval_fn)
        # board state and evaluator function passed to search engine
        # to determine next move using minimax

class MaterialistAgent:
    name = "Materialist"
    
    def __init__(self, depth=3):
        self.engine = SearchEngine(depth)
        self.eval_fn = evaluate_materialist
    
    def choose_move(self, board: chess.Board):
        return self.engine.search(board, self.eval_fn)