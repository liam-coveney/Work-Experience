# Minimax Catan Player implementation
from player import player
import copy
import time
from gameState import gameState
import random
import hexLib, hexTile
import minimax_heuristics as heuristics
from math import floor

dice_probabilities = {
    2: 1/36,
    3: 2/36,
    4: 3/36,
    5: 4/36,
    6: 5/36,
    7: 6/36,
    8: 5/36,
    9: 4/36,
    10: 3/36,
    11: 2/36,
    12: 1/36
}

class minimaxPlayer(player):
    def __init__(self, playerName, playerColor, turnTimeLimit = .2):
        super().__init__(playerName, playerColor, isAI = True)
        self.turnTimeLimit = turnTimeLimit
        self.turnStart = None
        self.random = False
        # Arbitrary win/lose scores
        self.WIN_SCORE = 1000
        self.LOSE_SCORE = -1000

    
    # Core minimax algorithm
    def minimax(self, state: gameState, depth, tradeMade: bool):
        # Check if time limit reached
        if time.time() - self.turnStart > self.turnTimeLimit:
            return None, heuristics.gameHeuristic(state)
        # if False: pass
        else:
            # Depth = 0 returns no move, just heuristic
            if depth == 0: 
                return None, heuristics.gameHeuristic(state)
            # If state is gameOver return score based on if currPlayer won
            elif state.dynamic.gameOver:
                if self.victoryPoints >= 10:
                    return None, self.WIN_SCORE
                else:
                    return None, self.LOSE_SCORE
            else:
                currPlayer = state.dynamic.currPlayer
                currIndex = state.dynamic.players.index(currPlayer)
                bestScore = [self.WIN_SCORE] * len(state.dynamic.players)
                bestScore[currIndex] = self.LOSE_SCORE
                bestMove = ("endTurn", None)

                # minimax after dice roll
                if state.lastMove[0] == "endTurn":
                    state.lastMove[0] == "DICE_ROLLED"
                    expected_score = [0 for _ in state.dynamic.players]
                    for dice, prob in dice_probabilities.items():
                        rolledState = self.simulateDiceRoll(state, dice)
                        _, scoreVector = self.minimax(rolledState, depth - 1, tradeMade)
                        for i in range(len(scoreVector)):
                            expected_score[i] += prob * scoreVector[i]
                    return None, expected_score

                # For each possible move,
                for move in currPlayer.getAllPossibleMoves(state):
                    if tradeMade and move[0] == 'proposeTrade':
                        continue
                    # Simulate state with move played
                    newState = self.simulate(state, move)
                    # Recursively get a heuristic at that state
                    _, curr_heur = self.minimax(newState, depth - 1, tradeMade or (move[0] == 'proposeTrade'))
                    # Check if best move
                    bestDifferential = bestScore[currIndex] - ((sum(bestScore) - bestScore[currIndex]) / (len(bestScore) - 1))
                    currDifferential = curr_heur[currIndex] - ((sum(curr_heur) - curr_heur[currIndex]) / (len(curr_heur) - 1))
                    if currDifferential > bestDifferential:
                        bestScore = curr_heur
                        bestMove = move
                # Return best move
                return bestMove, bestScore
            
    # Core logic to take a turn: runs minimax until turnTimeLimit is reached, then plays bestMove
    def move(self, state, tradeMade):
        # Default to ending turn (if no better move exists)
        bestMove = ("endTurn", None)
        # Initialize minimax depth to 0
        depth = 2
        # Get turn start time
        self.turnStart = time.time()
        # print(currPlayer.getAllPossibleMoves(state.static.board))

        # While time limit hasn't been reached,
        while time.time() - self.turnStart < self.turnTimeLimit:
            # Call minimax to get a move
            minimaxMove, heuristic = self.minimax(state, depth, tradeMade)
            # If minimax runs all the way through (time limit is not reached), set best move equal to the move minimax gives
            if minimaxMove is not None: 
                bestMove = (minimaxMove, heuristic)
                if minimaxMove[0] == 'proposeTrade':
                    tradeMade = True
            # Increment depth
            depth += 1
        # minimaxPlayer plays the best move at the end of turn
        self.makeMove(bestMove[0][0], bestMove[0][1], state)
        state.lastMove = bestMove[0]
        print(f"FLAG {self.name} MAKING move: {bestMove} based on depth {depth}.")
        return bestMove[0]
    
    def simulate(self, state: gameState, move):
        copiedState = copy.deepcopy(state)
        playerCopy = copiedState.dynamic.currPlayer
        playerCopy.makeMove(move[0], move[1], copiedState)
        copiedState.lastMove = move
        return copiedState
    
    def moveRobber(self, board):
        robberSpots = board.get_robber_spots()
        playerToRob = None

        while playerToRob is None:
            spotToRobIndex, spotToRobTile = random.choice(list(robberSpots.items()))
            vertexList = hexLib.polygon_corners(board.flat, spotToRobTile.hex)
            for vertex in vertexList:
                playerAtVertex = board.boardGraph[vertex].state['Player']
                if playerAtVertex and not playerAtVertex == self:
                    playerToRob = playerAtVertex
                    break

        self.move_robber(spotToRobIndex, board, playerToRob)

    def discardResources(self):
        numCards = sum(self.resources.values())
        if numCards > 7: 
            numToDiscard = floor(numCards / 2.0)
            for _ in range(numToDiscard):
                resourceToDiscard = max(self.resources, key = self.resources.get)
                self.resources[resourceToDiscard] -= 1
    
    def simulateDiceRoll(self, state: gameState, dice: int):
        copiedState = copy.deepcopy(state)
        board = copiedState.static.board
        players = copiedState.dynamic.players
        currPlayer = copiedState.dynamic.currPlayer

        if(dice != 7):
            hexResourcesRolled = board.getHexResourceRolled(dice)
            for player_i in players:
                for settlementCoord in player_i.buildGraph['SETTLEMENTS']:
                    for adjacentHex in board.boardGraph[settlementCoord].adjacentHexList: 
                        if(adjacentHex in hexResourcesRolled and board.hexTileDict[adjacentHex].robber == False): 
                            resourceGenerated = board.hexTileDict[adjacentHex].resource.type
                            player_i.resources[resourceGenerated] += 1
                            # print("{} collects 1 {} from Settlement".format(player_i.name, resourceGenerated))
                for cityCoord in player_i.buildGraph['CITIES']:
                    for adjacentHex in board.boardGraph[cityCoord].adjacentHexList: 
                        if(adjacentHex in hexResourcesRolled and board.hexTileDict[adjacentHex].robber == False):
                            resourceGenerated = board.hexTileDict[adjacentHex].resource.type
                            player_i.resources[resourceGenerated] += 2
                            # print("{} collects 2 {} from City".format(player_i.name, resourceGenerated))
        
        else:
            for player_i in players:
                minimaxPlayer.discardResources(player_i)
            minimaxPlayer.moveRobber(currPlayer, board)
        
        copiedState.lastMove = (None, None)
        return copiedState

    def initial_setup(self, board):
        possibleVertices = board.get_setup_settlements(self)

        valueDict = {}

        for vertex in possibleVertices.keys():
            value = 0
            for hexID in board.boardGraph[vertex].adjacentHexList:
                hexTile = board.hexTileDict[hexID]
                if not hexTile.resource.num is None:
                    prob = dice_probabilities.get(int(hexTile.resource.num))
                    value += prob
            valueDict[vertex] = value

        settlement = max(valueDict, key = valueDict.get)
        
        # settlement = random.choice(list(possibleVertices.keys()))

        self.buildSettlement(settlement, board)

        possibleRoads = board.get_setup_roads(self)
        
        road = random.choice([road[1] for road in list(possibleRoads.keys())])

        self.buildRoad(settlement, road, board)