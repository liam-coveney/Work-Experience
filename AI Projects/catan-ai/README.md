# README for CATAN-AI Project
Team: Liam Coveney, Sam Greenfield, Xander Minch

## Code adapted from other sources
As the base of this project, we cloned the repository at https://github.com/kvombatkere/Catan-AI.git. The license from the original repository is copied into this project to give credit as requested to Karan Vombatkere. This repository is a very basic model of the board game Catan. The intent of the original author was to use machine learning to train an AI player to play Catan. From this code, we took the following files. For each file, the modifications we made to it are listed.
- board.py: Defines catanBoard class, which includes all static information about the game, including the order of resource hexes, order of numbers, game window size, port position, and the stack of development cards (limited numbers of each). On initialization, the board shuffles itself until a valid configuration has been reached. 
    - No major changes
- catanGame.py: Defines catanGame class, which is the entirety of a given game of Catan. The class stores important game variables such as board, gameOver, maxPoints, currPlayer, numPlayers, playerQueue, playerTypes, playerNames, and boardView (see gameView). Its methods also include most of the game logic, including initial settlement and road building, gameState saving and loading, building, robber movement, die rolls, and resource distribution. The main function, however, is in the pygame event loop, which detects clicks on buttons and applies the given command to the game and board.
    - Initialization of game based on player names and types for use in customGame.py
    - Changed player colors and initialization of player objects
    - Fixed bugs and typos which altered game logic from cannon
    - Added dice rolling logic
    - Made fixes to increase pygame refresh rate to keep consistent with actual game state
    - Implemented saving and loading a gameState object (see gameState.py)
    - Fixed game end logic to wait for users to close the window
- gameView.py: Defines catanGameView class, which uses the board and game objects to display the game in a pygame window. This includes drawing the window, board, text, ports, and buttons as well as functions to refresh various parts of the board individually.
    - Changed some of game font to AG_Garamond Bold for visual appeal
    - Implemented visualization of ports to display ports wrapping the vertex they lay on in a directionally relevant way
    - Changed game display size
    - Changed button sizes for visual consistency
    - Added buttons for saving and loading gameStates
    - Fixed logic for human players to build roads, settlements, cities based on display of possibilities
    - Implemented from scratch player info cards on right side of display, which include information about:
        - player name
        - resource and development card inventory
        - visible and total victory points
        - number of knights played
        - largest army and longest road status
- hexLib.py: Library for hexagon math used to display board correctly.
    - No changes
- hexTile.py: Defines the hexTile class, which includes information for each tile about its position, resource, number, neighbors, robber status. Methods allow other parts of the code to get relevant information about the tile.
    - No major changes
- player.py: Defines the player class, which represents a human or AI player in the game, including their attributes, inventories, point totals, played development cards, and graph of built roads, settlements, and cities. Player actions depend on whether the isAI attribute is True or False.
    - Fixed intialization resource counts
    - Implemented getAllPossibleMoves, which returns a list of move tuples describing each action a player might take
    - Commented out print statements for better in-game readability
    - Fixed human trade logic to allow human players to decline trades
    - Implemented AI trading with the bank, via ports, and with other players
    - Implemented AI ability to make moves based on a move tuple
    - Fixed logic of AI players moves to make them consistent with the actual game

Omitted files: 
- AIGame.py: Starts a game between only heuristicAIPlayer players. We built our own logic for AI vs. AI games, and used our own minimaxPlayer.
- heuristicAIPlayer.py: Scaffolding for an AI agent to play a catanGame. Was not feature-complete, so we made our own version which was (minimaxPlayer).
- modelState.py: Beginning of a state object which includes an action list (trace). We implemented our own gameState object using attributes of the game.
- tensorflowTest.py: Basic ML model scaffolding- not of use to use in classical technique-based project.

## Code from scratch
The other files in the project are ones that we created and implemented from scratch. They are listed below.

- customGame.py: Initializes a given number of 3-player games with two randomPlayer players and one minimaxPlayer. The minimaxPlayer is at a random starting position each time to account for differences in starting player. The scores and winner of these games are recorded in a .xlsx spreadsheet called CatanGameSimResluts.xlsx.
- gameState.py: Defines a gameState class, which is made of staticState and dynamicState objects, as described below.
    - class staticState is made of only a catanBoard object
    - class dynamicState comprises a gameOver variable to track whether a player has won yet. It also includes a currentPlayer to track which player's turn it currently is. Finally, it includes a list of all players in the game.
    - class gameState comprises a lastMove tuple to keep track of whether the dice must be rolled for the next step in minimax, a devCardPlayedThisTurn boolean to determine whether a player has already played a card on their turn, and a staticState and dynamicState object.
- minimax_heuristics.py: Combines various values to give a list of heuristic values for each player, which minimaxPlayer uses to decide the best move to make.
    - gameHeuristic loops over each player. For each player, it calls the other functions below and finds the weighted sum of the values based on the values and weights defined. It returns a list of this weighted value for each player's position.
    - stateVPValue: Computes a value which represents the number of victory points a player has and their relation to other players (i.e. if a player has the maximum number of points, they get a bonus, etc.).
    - statePositionValue: Computes a value which representes their dominance in resource production. Takes into account probability of resources being rolled, distribution of resources, dominance compared to other players.
    - stateDevCardValue: Gives points for having development cards, largest army. Situationally aware (if a player has few resources, dev cards which supply the player with resources are better).
    - settlementValue: Values number of settlements a player has.
    - cityValue: Values number of cities a player has.
    - handValue: Values having a lot of cards, but not too many (averse to risk of discarding on a 7 roll).
    - goodRoadValue: Values having good road structure (instead of building useless roads).
- minimaxPlayer.py: Defines minimaxPlayer class, which inherits from player. Uses n-max (an extension of minimax for more than two players) to determine the best move in a given turnTimeLimit. Utilizes an iterative deepening approach to look as many layers deep as it can.
    - minimax function:
        - Returns None moves if the time limit has been reached, depth is zero, or game is over (with gameOver values).
        - Otherwise, begin by defining base move as "endTurn" with LOSE_SCORE value to force it to look at all other moves.
        - If the last move of the gameState is an endTurn, loop through each dice roll possibility, call minimax recursively, and weigh the future scores by the probability of the dice roll.
        - If the last move was not endTurn (or the dice were just rolled), loop through each move in the player's getAllPossibleMoves function (inherited from player). For each move,
            - Simulate a new gameState with the move made (see simulate below).
            - Compute heuristic values for each player based on the simulated state by recursively calling minimax.
            - Get the differential between the current player's heuristic and the average of the other two players' heuristic values.
            - Keep the move with the best differential for the player.
        - Return the best move and it's heuristic list with a score for each player.
    - move function: Uses minimax to make a move, as described below:
        - Initialize turn start time and depth = 2
        - While not out of time, 
            - Call minimax with current depth.
            - Increment depth, keeping track of whether a trade has been proposed by the minimaxPlayer (disallow a player from repeatedly asking for trades).
        - Call makeMove (inherited from player) with the best move found by minimax to make the move in the real game layer (not simulated minimax layers).
        - Print a flag to show a viewer which move was made at which depth.
    - simulate function: Takes a gameState, deep copies it, applies a move to the state, and returns the new state.
    - moveRobber function: Moves robber to a random spot with a non-self player, and robs from that player.
    - discardResources function: Discards it's most plentiful resource for each resource required to discard.
    - simulateDiceRoll function: Deep copies the gameState, distributes resources based on the dice roll, includes logic for 7-rolls (discard and move robber).
    - initial_setup function: Places a settlement at a maximum-production node and a random valid road connected to the settlement.
- randomPlayer.py: Defines randomPlayer class, which inherits from player. It is essentially minimaxPlayer without smart logic. It's move function lists all possible moves and chooses a random move. Its moveRobber function chooses a random hex, and its initial_setup function chooses random valid settlements and roads.

## Run our code
If you want to try out our game (and you should), you have two main options we've implemented. They are as follows:
- If you want to play against a couple of our minimax agents, as a human, uncomment lines 471-478 of catanGame.py and run the full python script. You'll begin by placing settlements by clicking on the circle marker you desire. From there, you'll see the minimaxPlayers make their moves quickly. Make your second move, and click Roll Dice to get started. (NOTE: For some aspects of the game when playing as a human, you will have to answer questions in the terminal having to do with trading and discarding. If the game looks like it is stuck, this is likely because you need to answer a question in the terminal.)
- To watch our minimaxPlayer try to beat two random players, run customGame.py as-is. This will loop through the defined numGames number of games with a minimax player playing against two random players. (NOTE: If likes 471-476 of catanGame are uncommented, customGame will not work properly, as the games will not close after finishing.) After the games have finished, you can look at the CatanGameSimResults.xlsx spreadsheet to view game statistics for that run.
- Dependencies: The following are all required to run this project:
    - dill (for saving and loading states)
    - os
    - queue
    - numpy
    - sys
    - pygame
    - string
    - openpyxl (for saving game data in customGame.py)
    - random
    - math
    - collections
    - copy
    - time
    