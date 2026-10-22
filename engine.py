import chess


class SearchEngine:
    def __init__(self, depth=3):
        self.depth = depth
        self.nodes_visited = 0

    def search(self, board: chess.Board, eval_fn) -> chess.Move:
        self.nodes_visited = 0
        best_move = None

        if board.turn == chess.WHITE:
            best_value = -float("inf")
            alpha = -float("inf")
            beta = float("inf")

            for some_move in self.ordered_moves(board):
                board.push(some_move)
                some_value = self.minimax(board, self.depth - 1, alpha, beta, eval_fn)
                board.pop()

                if some_value > best_value:
                    best_value = some_value
                    best_move = some_move

                alpha = max(alpha, best_value)

        else:
            best_value = float("inf")
            alpha = -float("inf")
            beta = float("inf")

            for some_move in self.ordered_moves(board):
                board.push(some_move)
                some_value = self.minimax(board, self.depth - 1, alpha, beta, eval_fn)
                board.pop()

                if some_value < best_value:
                    best_value = some_value
                    best_move = some_move
                beta = min(beta, best_value)

        return best_move

    def minimax(self, board, depth, alpha, beta, eval_fn):
        self.nodes_visited += 1

        if depth == 0 or board.is_game_over():
            return self.evaluate(board, eval_fn)

        if board.turn == chess.WHITE:
            some_value = -float("inf")
            for move in self.ordered_moves(board):
                board.push(move)
                some_value = max(some_value, self.minimax(board, depth - 1, alpha, beta, eval_fn))
                board.pop()

                alpha = max(alpha, some_value)
                if alpha>=beta:
                    break
            return some_value
        else:
            some_value = float("inf")
            for move in self.ordered_moves(board):
                board.push(move)
                some_value = min(some_value, self.minimax(board, depth - 1, alpha, beta, eval_fn))
                board.pop()

                beta = min(beta, some_value)
                if alpha >= beta:
                    break
            return some_value


    def evaluate(self, board: chess.Board, eval_fn) -> float:
        #evaluation is done from white's perspective
        if board.is_checkmate(): #at check-mate it is the loser's turn
            if board.turn == chess.WHITE:
                return -100000 + self.depth  #bad for white, good for black
            else:
                return 100000 - self.depth #good for white, bad for black

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        return eval_fn(board)

    @staticmethod
    def ordered_moves(board: chess.Board):
        moves = list(board.legal_moves)
        moves.sort(key=lambda m: board.is_capture(m), reverse=True)
        return moves