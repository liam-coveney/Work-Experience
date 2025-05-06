'''
NOTE FROM SAM: OUR gameState class saves entire game state withn no repeated information. 
'''
from board import catanBoard
from player import player

# Parts of gameState which do not change as a game progresses
class staticState():
    def __init__(self, board: catanBoard):
        self.board = board

# Parts of gameState which DO CHANGE as game progresses
class dynamicState():
    def __init__(self, gameOver: bool, players: list, currPlayer: player):
        self.gameOver = gameOver
        self.currPlayer = currPlayer
        self.players = list(players)

# Combination of static and dynamic state
class gameState():
    def __init__(self, catanGame):
        self.lastMove = (None, None)
        self.devCardPlayedThisTurn = False
        self.static = staticState(catanGame.board)
        self.dynamic = dynamicState(catanGame.gameOver, catanGame.playerQueue.queue, catanGame.currPlayer)