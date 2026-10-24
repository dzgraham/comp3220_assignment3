import threading
import tkinter as tk
from tkinter import ttk, messagebox
import chess

"""
AvA means Agent vs Agent

In chess, ranks and files are the grid lines that make up the 8x8 chessboard,
    creating the coordinate system used to identify every square and record moves
    https://www.chess.com/terms/chessboard
"""

UNICODE_PIECES = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}

#board colours
LIGHT = "#eeeed2"
DARK = "#769656"
HIGHLIGHT = "#0b54db"


class ChessGUI:
    def __init__(self, agent_a, agent_b):
        self.board = chess.Board()
        self.agents = {"Defensive": agent_a, "Attacker": agent_b}

        # Default Colour in Agent vs Agent mode
        self.AvA_white = "Defensive"
        self.AvA_black = "Attacker"

        self.selected_square = None   # square selected on the first human click
        self.agent_thinking = False   # True while a search thread is running
        self.paused = False           # True between Stop and Resume
        self.AvA_after_id = None      # pending Tk `after` id for the AvA loop
        self.AvA_started = False      # has Start been clicked for the current game?
        self.generation = 0           # bumped on every reset; stale-result guard

        # ----- Root window -----
        self.root = tk.Tk()
        self.root.title("Minimax Chess")
        self.build_widgets()
        self.draw_board()


    def build_widgets(self):
        # top toolbar
        top = ttk.Frame(self.root, padding=6)
        top.grid(row=0, column=0, columnspan=8, sticky="ew")

        # mode selector
        ttk.Label(top, text="Mode:").pack(side="left")
        self.mode = tk.StringVar(value="Human vs Agent")
        self.mode_menu = ttk.Combobox(
            top,
            textvariable=self.mode,
            state="readonly",
            values=["Human vs Agent", "Agent vs Agent"],
            width=15,
        )
        self.mode_menu.pack(side="left", padx=6)

        # mode change resets the game
        self.mode_menu.bind("<<ComboboxSelected>>", self.reset_game)

        #human colour selector
        ttk.Label(top, text="Human plays:").pack(side="left")
        self.human_side = tk.StringVar(value="White")
        self.human_side_menu = ttk.Combobox(
            top,
            textvariable=self.human_side,
            state="readonly",
            values=["White", "Black"],
            width=7,
        )
        self.human_side_menu.pack(side="left", padx=6)

        # colour change resets the game
        self.human_side_menu.bind("<<ComboboxSelected>>", self.reset_game)

        # agent opponent selector
        ttk.Label(top, text="Human vs:").pack(side="left")
        self.human_opponent = tk.StringVar(value="Defensive")
        ttk.Combobox(
            top,
            textvariable=self.human_opponent,
            state="readonly",
            values=["Defensive", "Attacker"],
            width=11,
        ).pack(side="left", padx=6)

        # search depth spinbox 1-5
        ttk.Label(top, text="Depth:").pack(side="left")
        self.depth_var = tk.IntVar(value=3)
        ttk.Spinbox(
            top,
            from_=1, to=5,
            textvariable=self.depth_var,
            width=3,
        ).pack(side="left", padx=6)

        # control buttons
        self.new_btn = ttk.Button(top, text="New Game", command=self.reset_game)
        self.new_btn.pack(side="left", padx=6)

        # start button enabled only in Agent vs Agent mode before game begins
        self.start_btn = ttk.Button(
            top, text="Start", command=self.start_agent_vs_agent, state="disabled"
        )
        self.start_btn.pack(side="left", padx=4)

        # Stop and Resume buttons freeze and unfreeze the AvA loop
        self.stop_btn = ttk.Button(top, text="Stop", command=self.stop_game, state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        self.resume_btn = ttk.Button(top, text="Resume", command=self.resume_game, state="disabled")
        self.resume_btn.pack(side="left", padx=4)

        # Swap Agents flips the ganet colours in Agent vs Agent mode
        self.swap_btn = ttk.Button(top, text="Swap Agents", command=self.swap_agents, state="disabled")
        self.swap_btn.pack(side="left", padx=4)

        # Game status line [turn / result / paused]
        self.status = ttk.Label(
            self.root,
            padding=(6, 10),
            anchor="center",
            font=("Arial", 16, "bold"),
        )
        self.status.grid(row=9, column=0, columnspan=8, sticky="ew")

        # AvA colour assignment line
        self.assignment_label = ttk.Label(
            self.root,
            padding=(6, 4, 6, 10),
            anchor="center",
            foreground="#444444",
            font=("Arial", 11),
        )
        self.assignment_label.grid(row=10, column=0, columnspan=8, sticky="ew")

        # Board canvas
        self.square_size = 60
        self.offset = 20    # margin around the board for rank and file labels
        canvas_px = self.square_size * 8 + self.offset * 2

        # frame holds the canvas and centres it
        self.board_frame = ttk.Frame(self.root)
        self.board_frame.grid(row=1, column=0, columnspan=8, pady=6)

        # board cell stretch so the canvas can be centred
        for col in range(8):
            self.root.grid_columnconfigure(col, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.canvas = tk.Canvas(
            self.board_frame,
            width=canvas_px,
            height=canvas_px,
            highlightthickness=0,
            bg="#ffffff",
        )
        self.canvas.pack(expand=True)
        self.canvas.bind("<Button-1>", self.on_click)

        self.fit_window_to_screen()
        self.reset_game()

    # Window Sizing
    def fit_window_to_screen(self):
        # maximise screen on launch
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()

        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.attributes("-zoomed", True)

        if self.root.winfo_width() < sw // 2:
            self.root.geometry(f"{sw}x{sh}+0+0")

        # compute the largest square size that fits the visible area with
        max_side = min(sh - 220, sw - 60)
        self.square_size = max(30, (max_side - self.offset * 2) // 8)
        canvas_px = self.square_size * 8 + self.offset * 2
        self.canvas.config(width=canvas_px, height=canvas_px)
        self.root.update_idletasks()

    # Board Drawing
    def draw_board(self):
        # redraw every frame
        self.canvas.delete("all")

        # if the human plays Black in Human vs Agent, flip so their pieces are at bottom
        flipped = (self.human_side.get() == "Black") and (self.mode.get() == "Human vs Agent")
        ss, off = self.square_size, self.offset

        for r in range(8):
            for c in range(8):
                # squares
                x1, y1 = off + c * ss, off + r * ss
                color = LIGHT if (r + c) % 2 == 0 else DARK
                self.canvas.create_rectangle(x1, y1, x1 + ss, y1 + ss, fill=color)

                file = c if not flipped else 7 - c
                rank = 7 - r if not flipped else r
                sq = chess.square(file, rank)

                # highlight the selected square
                if sq == self.selected_square:
                    self.canvas.create_rectangle(
                        x1, y1, x1 + ss, y1 + ss,
                        outline=HIGHLIGHT, width=4,
                    )

                # Draw the piece glyph
                piece = self.board.piece_at(sq)
                if piece:
                    self.canvas.create_text(
                        x1 + ss / 2, y1 + ss / 2,
                        text=UNICODE_PIECES[piece.symbol()],
                        font=("Arial", max(20, int(ss * 0.6))),  # scale with square
                    )

        # rank and file labels in the margin
        for i in range(8):
            # rank (row) labels starting from white side 1 to 8
            rank_num = 8 - i if not flipped else i + 1

            # file (column) labels starting from a to h
            file_char = "abcdefgh"[i if not flipped else 7 - i]

            # Left margin has rank numbers
            self.canvas.create_text(
                off / 2, off + i * ss + ss / 2,
                text=str(rank_num),
                font=("Arial", 11, "bold"),
                fill="#333333",
            )
            # Bottom margin has file letters
            self.canvas.create_text(
                off + i * ss + ss / 2, off + 8 * ss + off / 2,
                text=file_char,
                font=("Arial", 11, "bold"),
                fill="#333333",
            )

        self.update_status()

    def update_status(self):
        # create the status text: result at game over, paused or whose turn
        if self.board.is_game_over():
            res = self.board.result()
            if res == "1-0":
                text = "White wins"
            elif res == "0-1":
                text = "Black wins"
            else:
                # Pick the first matching draw reason.
                reason = next((r for r, cond in [
                    ("Stalemate", self.board.is_stalemate()),
                    ("Insufficient material", self.board.is_insufficient_material()),
                    ("75-move rule", self.board.is_seventyfive_moves()),
                    ("Fivefold repetition", self.board.is_fivefold_repetition()),
                ] if cond), "Draw")
                text = f"Draw — {reason}"
            self.status.config(text=text)
        elif self.paused:
            self.status.config(text="Paused")
        else:
            self.status.config(
                text=f"{'White' if self.board.turn == chess.WHITE else 'Black'} to move"
            )

    def refresh_ui_state(self):
        # Single source of truth for every button's enabled/disabled state.

        is_ava = self.mode.get() == "Agent vs Agent"
        game_over = self.board.is_game_over()

        # swap only available in AvA mode and before/after game
        self.swap_btn.config(
            state="normal" if is_ava and not self.AvA_started else "disabled"
        )

        # show agent colour assignment only in AvA mode
        self.assignment_label.config(
            text=f"White: {self.AvA_white}    |    Black: {self.AvA_black}"
            if is_ava else ""
        )

        if is_ava:
            # start button enabled in AvA mode and game not started
            self.start_btn.config(
                state="normal" if not self.AvA_started and not game_over else "disabled"
            )
            # new game button enabled once a game has begun or after it ends
            self.new_btn.config(
                state="normal" if self.AvA_started or game_over else "disabled"
            )
            # stop button enabled only while running
            self.stop_btn.config(
                state="normal"
                if self.AvA_started and not self.paused and not game_over
                else "disabled"
            )

            # resume button enabled only while paused
            self.resume_btn.config(
                state="normal" if self.paused and not game_over else "disabled"
            )
        else:
            # in Human vs Agent mode only New Game button is enabled
            self.new_btn.config(state="normal")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.resume_btn.config(state="disabled")


    # Game Actions
    def reset_game(self, event=None):
        #used for new game, mode change and side change
        self.cancel_pending_AvA()
        self.generation += 1
        self.board = chess.Board()
        self.selected_square = None
        self.agent_thinking = False
        self.paused = False
        self.AvA_started = False

        self.draw_board()
        self.refresh_ui_state()

        # if human plays Black the white agent moves first automatically
        if self.mode.get() == "Human vs Agent" and self.human_side.get() == "Black":
            self.root.after(150, self.agent_move)

    def cancel_pending_AvA(self):
        # cancel a scheduled AvA step
        if self.AvA_after_id is not None:
            self.root.after_cancel(self.AvA_after_id)
            self.AvA_after_id = None

    # Click Handling
    def on_click(self, event):
        # ignore clicks while game paused or game over
        if (self.mode.get() != "Human vs Agent"
                or self.agent_thinking
                or self.paused
                or self.board.is_game_over()):
            return

        flipped = self.human_side.get() == "Black"
        c = (event.x - self.offset) // self.square_size
        r = (event.y - self.offset) // self.square_size
        if not (0 <= c < 8 and 0 <= r < 8):
            return   # ignore click if click in the margin

        sq = chess.square(c if not flipped else 7 - c, 7 - r if not flipped else r)
        human_color = chess.WHITE if self.human_side.get() == "White" else chess.BLACK
        if self.board.turn != human_color:
            return   # ignore click if not the human's turn

        if self.selected_square is None:
            # first click selects a piece of the human's colour
            piece = self.board.piece_at(sq)
            if piece and piece.color == human_color:
                self.selected_square = sq
        else:
            # second click attempts the move.
            move = chess.Move(self.selected_square, sq)
            piece = self.board.piece_at(self.selected_square)

            # auto-promote pawn to queen on the last rank
            if piece and piece.piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7):
                move = chess.Move(self.selected_square, sq, promotion=chess.QUEEN)

            if move in self.board.legal_moves:
                self.board.push(move)
                self.selected_square = None
                self.draw_board()
                self.root.after(50, self.agent_move)
            else:
                self.selected_square = None
        self.draw_board()

    # Agent's Turn
    def agent_move(self):
        # only run in Human vs Agent mode and the agent is to move
        if self.mode.get() != "Human vs Agent" or self.board.is_game_over():
            return
        human_color = chess.WHITE if self.human_side.get() == "White" else chess.BLACK
        if self.board.turn == human_color:
            return

        self._launch_agent_thread(self.agents[self.human_opponent.get()])

    def start_agent_vs_agent(self):
        # starts the AvA loop.
        self.AvA_started = True
        self.refresh_ui_state()
        self.kick_AvA_loop()

    def kick_AvA_loop(self):
        # schedule the first move of the AvA loop with short delay for smooth UI
        self.cancel_pending_AvA()
        self.AvA_after_id = self.root.after(150, self.agent_move_AvA)

    def agent_move_AvA(self):
        # step function for the AvA loop
        self.AvA_after_id = None
        if self.paused or self.mode.get() != "Agent vs Agent" or self.board.is_game_over():
            return

        # pick the agent whose colour matches the side to move
        key = self.AvA_white if self.board.turn == chess.WHITE else self.AvA_black
        self._launch_agent_thread(self.agents[key])

    def _launch_agent_thread(self, agent):
        """
            worker launcher for Human vs Agent and AvA turns
            Snapshots (fen, turn, generation) travel with the result so that
                apply_agent_move can discard stale moves safely
        """
        self.agent_thinking = True
        agent.engine.depth = self.depth_var.get()   # GUI can override engine depth

        snapshot_fen = self.board.fen()
        side_to_move = self.board.turn
        gen = self.generation

        def worker():
            # board.copy() isolates the search from the GUI's live board
            move = agent.choose_move(self.board.copy())
            # root.after posts back to the main thread
            self.root.after(0, lambda: self.apply_agent_move(move, snapshot_fen, side_to_move, gen))

        threading.Thread(target=worker, daemon=True).start()

    def apply_agent_move(self, move, expected_fen, expected_turn, gen):
        # runs on the main thread and reject results that arrived too late
        if gen != self.generation or self.paused:
            return

        self.agent_thinking = False
        # move must be legal for the current board and side to move
        if (move is None
                or self.board.fen() != expected_fen
                or self.board.turn != expected_turn
                or move not in self.board.legal_moves):
            return

        self.selected_square = None
        self.board.push(move)
        self.draw_board()

        # on game over stop the AvA loop and refresh UI states
        if self.board.is_game_over():
            self.AvA_started = False
            self.refresh_ui_state()
            return

        # continue the AvA loop with a short delay
        if self.mode.get() == "Agent vs Agent":
            self.AvA_after_id = self.root.after(50, self.agent_move_AvA)


    # Game Controls
    def stop_game(self):
        # freeze the AvA loop
        self.paused = True
        self.cancel_pending_AvA()
        self.refresh_ui_state()
        self.update_status()

    def resume_game(self):
        # resume after stop
        if not self.paused:
            return
        self.paused = False
        self.refresh_ui_state()
        self.update_status()
        if self.mode.get() == "Agent vs Agent" and not self.board.is_game_over():
            self.AvA_after_id = self.root.after(100, self.agent_move_AvA)

    def swap_agents(self):
        # switches agent colours
        if self.AvA_started and not self.board.is_game_over():
            messagebox.showinfo(
                "Swap Agents",
                "Stop or finish the current game before swapping agents.",
            )
            return
        self.AvA_white, self.AvA_black = self.AvA_black, self.AvA_white
        self.refresh_ui_state()

    def run(self):
        self.root.mainloop()