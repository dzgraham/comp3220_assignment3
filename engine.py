import chess

class SearchEngine:
    """
        Minimax search optimized with alpha-beta pruning.

        Agent strategy comes from eval_fn passed to search()
        The engine explores the game tree, scores leaves using eval_fn and returns the best move

        Values are always from WHITE's perspective:
            positive  means good for White
            negative  means good for Black
            zero means equal
    """

    def __init__(self, depth=3):
        """
            depth is the number of plies (half-moves) to look ahead
            Greater depth means 'smarter' move but slower (keep around 3)
        """
        self.depth = depth
        self.nodes_visited = 0  #node counter


    def search(self, board: chess.Board, eval_fn) -> chess.Move:
        """
            Checks every legal move at the root and calls minimax for the value
                of the resulting position at specified depth and returns the move with the best value.

            The board is mutated in place using push and pop (not GUI) and is fully
                restored before this method returns.
        """
        self.nodes_visited = 0
        best_move = None

        #White's move (maximize white's score)
        if board.turn == chess.WHITE:
            best_value = -float("inf")     # best score found so far
            alpha = -float("inf")          # maximiser
            beta = float("inf")            # minimiser

            for some_move in self.ordered_moves(board): #list of legal moves sorted
                board.push(some_move)   #descend to the child position (makes move)
                some_value = self.minimax(board, self.depth - 1, alpha, beta, eval_fn)
                board.pop()     # restore board before next move

                # set some_value as the best value and store corresponding best move so far
                # keeps move that maximizes white's score
                if some_value > best_value:
                    best_value = some_value
                    best_move = some_move

                #set alpha as max of itself and best_value
                alpha = max(alpha, best_value)

        # Black's move (minimize white's score)
        else:
            best_value = float("inf")
            alpha = -float("inf")
            beta = float("inf")

            for some_move in self.ordered_moves(board):
                board.push(some_move)
                some_value = self.minimax(board, self.depth - 1, alpha, beta, eval_fn)
                board.pop()

                # set some_value as the best value and store corresponding best move so far
                # keeps move that minimizes white's score
                if some_value < best_value:
                    best_value = some_value
                    best_move = some_move

                beta = min(beta, best_value)

        return best_move # sends best move to gui to move the actual piece on board


    def minimax(self, board, depth, alpha, beta, eval_fn):
        """
            When alpha >= beta, the remaining children cannot change
                the parent's choice, so the loop is cut short/pruned
        """

        self.nodes_visited += 1

        #depth determines when to stop searching and assigns a value
        # base case is leaf or terminal position
        if depth == 0 or board.is_game_over():
            return self.evaluate(board, eval_fn) # return value of leaf

        # white's move, aim is to maximize
        if board.turn == chess.WHITE:
            some_value = -float("inf")
            for move in self.ordered_moves(board):
                board.push(move)
                some_value = max(some_value, self.minimax(board, depth - 1, alpha, beta, eval_fn))
                board.pop()

                # raise the maximiser's floor
                alpha = max(alpha, some_value)

                if alpha >= beta: #prune since the children cannot change the max values
                    break
            return some_value

        # black's move, aim is to minimize
        else:
            some_value = float("inf")
            for move in self.ordered_moves(board):
                board.push(move)
                some_value = min(
                    some_value,
                    self.minimax(board, depth - 1, alpha, beta, eval_fn))
                board.pop()

                # lower the minimiser's ceiling
                beta = min(beta, some_value)

                if alpha >= beta: # prune
                    break
            return some_value


    def evaluate(self, board: chess.Board, eval_fn) -> float:
        """
            uses calling agent's evaluation function (strategy) to assign a value to a leaf node
            if check-mate, assign numerically high value to indicate win or loss
        """

        # At checkmate, the side to move is the loser
        #the depth is added/subtracted to prioritize the checkmate with the fewer moves
        if board.is_checkmate():
            if board.turn == chess.WHITE:
                return -100000 + self.depth   #White is mated, bad for White
            else:
                return 100000 - self.depth    # Black is mated, good for White

        # a draw is worth 0 to both sides
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        #if game continues, evaluate and return leaf node value to be compared with others
        return eval_fn(board)


    @staticmethod
    def ordered_moves(board: chess.Board):
        """
            return legal moves with captures first
            minimax is order-independent
            checking for captures first makes alpha-beta pruning more likely
        """
        moves = list(board.legal_moves)
        moves.sort(key=lambda m: board.is_capture(m), reverse=True)
        return moves