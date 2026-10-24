from agents import AttackerAgent
from gui import ChessGUI

if __name__ == "__main__":
    agent_a = AttackerAgent(depth=3)
    agent_b = AttackerAgent(depth=3)
    ChessGUI(agent_a, agent_b).run()