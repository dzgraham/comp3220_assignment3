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

ATTACKER_MATERIAL_WEIGHT = 0.85   # material counts at 85% of its real value
TROPISM_WEIGHT = {  # closeness to enemy king bonus
    chess.KNIGHT: 4,
    chess.BISHOP: 3,
    chess.ROOK: 3,
    chess.QUEEN: 5,
}
PAWN_ADVANCE_WEIGHT = 5           # per rank advanced beyond rank 1
MISSING_SHIELD_PENALTY = 15       # per missing pawn in front of own king
KING_ZONE_ATTACK_PENALTY = 6      # per enemy attack on the squares around own king
KING_ZONE_ATTACK_CAP = 8          # cap on counted zone attacks so it can't swamp material
CHECK_BONUS = 40

HANGING_OPP_WEIGHT = 0.8          # bonus: side to move can win an enemy piece for free
HANGING_OWN_WEIGHT = 0.6


def king_exposure(board: chess.Board, color: chess.Color) -> float:
    """
    Counts pawns missing from the shield in front of the king, plus enemy
    attacks landing on the king and its neighbouring squares.
    """
    ksq = board.king(color)
    if ksq is None:
        return 0

    kfile, krank = chess.square_file(ksq), chess.square_rank(ksq)
    step = 1 if color == chess.WHITE else -1
    own_pawns = board.pieces(chess.PAWN, color)

    # Missing pawn shield (3 files x 2 ranks directly in front of the king)
    missing = 0
    for f in (kfile - 1, kfile, kfile + 1):
        if not 0 <= f <= 7:
            continue
        shielded = any(
            0 <= r <= 7 and chess.square(f, r) in own_pawns
            for r in (krank + step, krank + 2 * step)
        )
        if not shielded:
            missing += 1

    # Enemy pieces hitting the king zone
    zone = chess.BB_KING_ATTACKS[ksq] | chess.BB_SQUARES[ksq]
    zone_attacks = 0
    for sq, piece in board.piece_map().items():
        if piece.color != color and piece.piece_type not in (chess.PAWN, chess.KING):
            zone_attacks += chess.popcount(board.attacks_mask(sq) & zone)

    return (MISSING_SHIELD_PENALTY * missing
            + KING_ZONE_ATTACK_PENALTY * min(zone_attacks, KING_ZONE_ATTACK_CAP))


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

    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0  # this value determines best move
    white_risk = 0  # biggest White piece that can be captured profitably
    black_risk = 0


    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)

    for sq, piece in board.piece_map().items():
        if piece.piece_type == chess.KING:
            continue

        sign = 1 if piece.color == chess.WHITE else -1

        risk = material_at_risk(board, sq, piece)

        if piece.color == chess.WHITE:
            white_risk = max(white_risk, risk)
        else:
            black_risk = max(black_risk, risk)

        score += sign * ATTACKER_MATERIAL_WEIGHT * PIECE_VALUES[piece.piece_type]

        """
            Bonus for pawn advancement
            For each square a white pawn is on, add to score the rank of the pawn multiplied by 8
            For each square a black pawn is on, subtract from the score the rank of the pawn
                from the perspective of the black (7-rank) multiplied by 8
        """
        if piece.piece_type == chess.PAWN:
            rank = chess.square_rank(sq) if piece.color == chess.WHITE else 7 - chess.square_rank(sq)
            score += sign * PAWN_ADVANCE_WEIGHT * max(0, rank - 1)

        # pieces close to the enemy king
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
        else:
            enemy_king = black_king if piece.color == chess.WHITE else white_king
            if enemy_king is not None:
                closeness = 7 - chess.square_distance(sq, enemy_king)
                score += sign * TROPISM_WEIGHT[piece.piece_type] * closeness

        # Own exposed king is bad
    score -= king_exposure(board, chess.WHITE)
    score += king_exposure(board, chess.BLACK)

    if board.is_check():
        score += CHECK_BONUS if board.turn == chess.BLACK else -CHECK_BONUS

    if board.turn == chess.WHITE:
        score += HANGING_OPP_WEIGHT * black_risk - HANGING_OWN_WEIGHT * white_risk
    else:
        score -= HANGING_OPP_WEIGHT * white_risk - HANGING_OWN_WEIGHT * black_risk

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