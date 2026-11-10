import chess

"""
    Negamax is a variant of the minimax algorithm used in two-player, zero-sum games.
    It simplifies implementation by relying on the mathematical property that maximizing
        a player's score is equivalent to minimizing the negated score of the opponent:
        max(a, b) = -min(-a, -b)
    https://chessprogramming.org/Negamax
"""

class SearchEngine:
    """
        Minimax (Negamax) search optimized with alpha-beta pruning

        Agent strategy comes from eval_fn passed to search()
        The engine explores the game tree, scores leaves using eval_fn and returns the best move
    """

    def __init__(self, depth=3):
        """
            depth is the number of plies (half-moves) to look ahead
            higher depth means 'smarter' move but slower
        """
        self.depth = depth
        self.nodes_visited = 0  #node counter


    def search(self, board: chess.Board, eval_fn) -> chess.Move:
        """
            Checks every legal move at the root and calls minimax for the value
                of the resulting position at specified depth and returns the move with the best value.

            The board is mutated in place using push and pop and is fully
                restored before this method returns.
        """

        self.nodes_visited = 0
        best_move = None
        best_value = -float("inf")
        alpha, beta = -float("inf"), float("inf")

        for move in self.ordered_moves(board):
            board.push(move) #descend to the child position (makes move)
            # negate the child's return - swap and negate the window
            # original: value = -self.minimax(board, self.depth - 1, -beta, -alpha, eval_fn)
            value = -self.minimax(board, self.depth - 1, -beta, -alpha, eval_fn, ply=1)            
            board.pop() # restore board before next move

            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, best_value)

        return best_move

    def minimax(self, board, depth, alpha, beta, eval_fn, ply=0): #added ply=0
        self.nodes_visited += 1
        
        #treat any repeat inside the search as a draw to avoid shuffling
        if ply > 0 and board.is_repetition(2):
            return 0

        if depth == 0 or board.is_game_over():
            return self.evaluate(board, eval_fn, ply)  # added ply

        value = -float("inf")
        for move in self.ordered_moves(board):
            board.push(move)
            value = max(value, -self.minimax(board, depth - 1, -beta, -alpha, eval_fn, ply+1)) #added ply+1
            board.pop()
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value


    def evaluate(self, board: chess.Board, eval_fn, ply=0) -> float: #ply
        """
            uses calling agent's evaluation function (strategy) to assign a value to a leaf node
            if check-mate, assign numerically high value to indicate win or loss
        """

        # At checkmate the side to move is the loser
        # the depth is added/subtracted to prioritize the checkmate with the fewer moves
        # if board.is_checkmate():
        #     if board.turn == chess.WHITE:
        #         return -100000 + self.depth   #White is mated, bad for White
        #     else:
        #         return 100000 - self.depth    # Black is mated, good for White
        # # a draw is worth 0 to both sides
        # if board.is_stalemate() or board.is_insufficient_material():
        #     return 0
        
        if board.is_checkmate():
            return -100000 + ply
        if board.is_game_over():
            return 0

        #if game continues, evaluate and return leaf node value to be compared with others
        score = eval_fn(board)
        return score if board.turn == chess.WHITE else -score
        

    @staticmethod
    def ordered_moves(board: chess.Board):
        """
            return legal moves with captures first
            minimax is order independent
            checking for captures first makes alpha-beta pruning more likely
        """
        moves = list(board.legal_moves)
        moves.sort(key=lambda m: board.is_capture(m), reverse=True)
        return moves