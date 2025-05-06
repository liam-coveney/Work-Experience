from catanGame import catanGame
from openpyxl import load_workbook
import random

file_path = "CatanGameSimResults.xlsx"
wb = load_workbook(file_path)
ws = wb.active
color_order = ["Red", "Blue", "Black"]

numGames = 51

for i in range(1, numGames):
    xcl_push = []
    players = ['random', 'random', 'random']
    ai_index = random.randint(0, len(players) - 1)
    players[ai_index] = 'minimaxAI'
    playerNames = ['random1', 'random2', 'random3']
    playerNames[ai_index] = 'minimaxPlayer'

    customGame = catanGame(players, playerNames)
    customGame.playCatan()

    winner_type = 'minimaxAI' if playerNames.index(customGame.currPlayer.name) == ai_index else 'random'
    xcl_push = [i, winner_type]
    temp_players = []
    while not customGame.playerQueue.empty():
        player = customGame.playerQueue.get()
        temp_players.append(player)

    for player in temp_players:
        capped_score = min(player.victoryPoints, 10)
        if player.randOM:
            xcl_push.append(capped_score)
        else:
            xcl_push.insert(2, capped_score)

    ws.append(xcl_push)
    wb.save(file_path)