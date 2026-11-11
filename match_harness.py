"""
match_harness runs N games between the two agents, alternating colours per colour
logs moves and game results then prints a final scoreline.
https://python-chess.readthedocs.io/en/latest/

Usage:
    python match_harness.py     # default: 6 games, depth 3
    python match_harness.py --games 10 --depth 3 --out match_log.txt
"""

import argparse
import chess
import time
from datetime import datetime

from agents import AttackerAgent, MaterialistAgent


def play_one_game(white_agent, black_agent, max_moves=300, verbose=True):
    board = chess.Board()
    moves_san = []

    while not board.is_game_over() and board.fullmove_number <= max_moves:
        agent = white_agent if board.turn == chess.WHITE else black_agent
        move_start = time.time()
        move = agent.choose_move(board.copy())
        move_time = time.time() - move_start

        if move is None or move not in board.legal_moves:
            return "0-1" if board.turn == chess.WHITE else "1-0", \
                   "illegal move", moves_san, board

        san = board.san(move)
        moves_san.append(san)

        # prints every move and its think time
        if verbose:
            move_num = board.fullmove_number
            side = "White" if board.turn == chess.WHITE else "Black"
            print(f"\t{move_num:>3}. {side:<5} {san:<8} ({move_time:.2f}s)")

        board.push(move)

    # determine result and reason
    if board.is_checkmate():
        reason = "checkmate"
    elif board.is_stalemate():
        reason = "stalemate"
    elif board.is_insufficient_material():
        reason = "insufficient material"
    elif board.is_seventyfive_moves():
        reason = "75-move rule"
    elif board.is_fivefold_repetition():
        reason = "fivefold repetition"
    elif board.fullmove_number > max_moves:
        reason = "move limit reached"
    else:
        reason = "unknown"

    return board.result(), reason, moves_san, board


def run_match(agent_a, agent_b, games=6, depth=3, log_path="match_log.txt"):
    agent_a.engine.depth = depth
    agent_b.engine.depth = depth

    score = {"A": 0, "B": 0, "draw": 0}
    game_records = []

    with open(log_path, "w", encoding="utf-8") as f:
        header = (
            f"Agent A: {agent_a.name}\n"
            f"Agent B: {agent_b.name}\n"
            f"Games: {games}\tDepth: {depth}\n"
            + "=" * 35 + "\n"
        )
        f.write(header)
        print(header, end="")

        for i in range(games):
            if i % 2 == 0:
                white_agent, black_agent = agent_a, agent_b
                a_color = "White"
                white_name, black_name = agent_a.name, agent_b.name
            else:
                white_agent, black_agent = agent_b, agent_a
                a_color = "Black"
                white_name, black_name = agent_b.name, agent_a.name

            game_header = (
                f"\n--- Game {i + 1} ---\n"
                f"White: {white_name}\n"
                f"Black: {black_name}\n"
            )
            f.write(game_header)
            print(game_header, end="")

            start = time.time()
            result, reason, moves_san, board = play_one_game(
                white_agent, black_agent
            )
            elapsed = time.time() - start

            if result == "1-0":
                winner = "A" if a_color == "White" else "B"
            elif result == "0-1":
                winner = "A" if a_color == "Black" else "B"
            else:
                winner = "draw"

            if winner == "draw":
                score["draw"] += 1
            else:
                score[winner] += 1

            game_records.append({
                "game": i + 1,
                "a_color": a_color,
                "white_name": white_name,
                "black_name": black_name,
                "result": result,
                "reason": reason,
                "winner": winner,
                "moves": len(moves_san),
                "time": elapsed,
            })

            if winner == "draw":
                winner_text = f"Draw ({reason})"
            else:
                winner_agent = agent_a.name if winner == "A" else agent_b.name
                winner_color = "White" if result == "1-0" else "Black"
                winner_text = f"{winner_color} ({winner_agent})"

            game_footer = (
                f"Winner: {winner_text}\n"
                f"Result: {reason}\n"
                f"Plies: {len(moves_san)}\tTotal Time: {elapsed:.2f}s\n"
            )
            f.write(game_footer)
            print(game_footer, end="")

        # Final summary
        summary = (
            "\n"+"=" * 35 + "\n"
            "FINAL SCORE\n"
            "-----------\n"
            f"Agent A ({agent_a.name}) wins: {score['A']}\n"
            f"Agent B ({agent_b.name}) wins: {score['B']}\n\n"
            f"Total games: {games}\n"
            f"Draws: {score['draw']}\n"
            "\nGame summaries:\n"
        )
        for rec in game_records:
            if rec["winner"] == "draw":
                winner_text = f"Draw ({rec['reason']})"
            else:
                # Map A/B back to the agent name that played that colour
                winner_agent = agent_a.name if rec["winner"] == "A" else agent_b.name
                winner_color = "White" if rec["result"] == "1-0" else "Black"
                winner_text = f"{winner_agent} won as {winner_color} ({rec['reason']})"

            summary += (
                f"\tGame {rec['game']:>2}: {winner_text}\n"
                f"\t\tWhite={rec['white_name']}, Black={rec['black_name']}, "
                f"plies={rec['moves']}, time={rec['time']:.1f}s\n"
            )

        f.write(summary)
        print(summary, end="")

    return score


def main():
    parser = argparse.ArgumentParser(description="Run a match between two chess agents.")
    parser.add_argument("--games", type=int, default=6, help="Number of games (default 6)")
    parser.add_argument("--depth", type=int, default=3, help="Search depth (default 3)")
    parser.add_argument("--out", type=str, default="match_log.txt", help="Log file path")
    args = parser.parse_args()

    agent_a = AttackerAgent(depth=args.depth)
    agent_b = MaterialistAgent(depth=args.depth)
    run_match(agent_a, agent_b, games=args.games, depth=args.depth, log_path=args.out)


if __name__ == "__main__":
    main()