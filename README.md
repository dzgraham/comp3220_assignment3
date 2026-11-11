# Implementing a Chess-Playing Agent Using Minimax and Alpha-Beta Pruning
## COMP3220 Assignment 3
    Alexia Barrows - 620161540
    Daniel Graham - 620171166

## Agents - agents.py
### Alexia Barrows (620161540) - The Materialist
        The Materialist agent has more of a greedy approach. It scores a position almost entirely by piece count, using full piece values. 
        -	It rewards winning an enemy piece the side to move can capture for free and penalises leaving its own pieces where they can be taken.
        -	The material lead gets a bonus that grows as pieces leave the board, so it simplifies toward an easy win.
        -	It ignores where pieces stand, pawn structure and king safety. It plays safe, practical chess and rarely gives anything away.

### Daniel Graham (620171166) - The Attacker
        The Attacker agent has an aggressive approach. It values material at only 85%, so it is willing to give up pieces for a higher position. Most of its score comes from pressure on the enemy king.
        -	Knights, bishops, rooks and queens get a bonus for being close to the enemy king.
        -	Pawns get a bonus for marching up the board.
        -	It is penalised for a broken pawn shield or enemy closeness to its own king.
        -	Moves that result in a check earns a bonus.

## Instructions
    First, ensure that the python chess library is installed in the environment.
        pip install -r requirements.txt

    To run the graphical chess application, run the command 'python main.py'
    Within the application, there are controls to change the mode ('Human vs Agent' or 'Agent vs Agent').
    The user may switch between playing as White or Black. They may also switch between playing against the Materialist or the Attacker agent.
    The agent depth can also be changed within the application. A higher depth takes exponentially longer but makes "smarter" decisions.
    
    In Human vs Agent mode, when clicking on your own piece, the GUI will highlight all legal moves for that piece.

    To run the match harness, run the command 'python match_harness.py'.
    The agents play each other and alternate between black and white.
    By default, 6 games are played at a depth of 3 and the results are output to match_log.txt.
    
    By using the flags, the number of games, the depth and the output file can be modified to custom values.
        Run the command, 'python match_harness.py 
                                --games <number of games>
                                --depth <desired depth
                                --out <custom file>'
        e.g. python match_harness.py --games 12 --depth 5 --out results.txt
        This command runs the match harness which will play 12 games at a depth of 5 and log the results in results.txt

 
