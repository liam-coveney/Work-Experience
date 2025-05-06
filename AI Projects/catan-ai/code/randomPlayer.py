from player import player
from gameState import gameState
import random
import hexLib
from math import floor

class randomPlayer(player):

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
    
    def __init__(self, playerName, playerColor):
        super().__init__(playerName, playerColor, isAI = True)
        self.turnStart = None
        self.random = True
            
    # Core logic to take a turn: runs minimax until turnTimeLimit is reached, then plays bestMove
    def move(self, state : gameState, _):
        currentPlayer = state.dynamic.currPlayer
        randomMove = random.choice(currentPlayer.getAllPossibleMoves(state))
        # print(randomMove[0], randomMove[1])
        self.makeMove(randomMove[0], randomMove[1], state)
        return randomMove
    
    def moveRobber(self, board):
        robberSpots = board.get_robber_spots()
        spotToRobIndex, spotToRobTile = random.choice(list(robberSpots.items()))
        playerToRob = None

        vertexList = hexLib.polygon_corners(board.flat, spotToRobTile.hex)
        for vertex in vertexList:
            playerAtVertex = board.boardGraph[vertex].state['Player']
            if playerAtVertex:
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
    

    def initial_setup(self, board):
        possibleVertices = board.get_setup_settlements(self)

        settlement = random.choice(list(possibleVertices.keys()))

        self.buildSettlement(settlement, board)

        possibleRoads = board.get_setup_roads(self)
        
        road = random.choice([road[1] for road in list(possibleRoads.keys())])

        self.buildRoad(settlement, road, board)