from gameState import gameState
from board import *
from player import player
from minimaxPlayer import *

# How good is the GAME for the current player?
def gameHeuristic(gameState: gameState):
    board = gameState.static.board
    dynamics = gameState.dynamic
    allPlayers = dynamics.players

    allPlayersValues = []
    # For each player
    for player in allPlayers:
        currentPlayer = player
        # Get each move the player can make
        potentialActions = currentPlayer.getAllPossibleMoves(gameState) #See function for implementation

        # If the game is over, return arbitrary high and low values
        if dynamics.gameOver:
            if(currentPlayer.victoryPoints>=10):
                return 1000 #ARBITRARY MAXIMUM VALUE
            else:
                return -1000 #ARBITRARY MINIMUM VALUE
        
        # Get values for VP, position, development cards, settlements, cities, hand, and roads
        #                                300, -300                                           700, -100                                   600, 0                                            
        game_values = [stateVPValue(currentPlayer, allPlayers, board), statePositionValue(currentPlayer, allPlayers, board), stateDevCardValue(currentPlayer, allPlayers, board), settlementValue(currentPlayer, board), cityValue(currentPlayer,board),handValue(currentPlayer),goodRoadValue(board,currentPlayer)]
        # Assign weights to each element of game_values
        weights =     [                  3,                                             .5,                                                  1,                                              3,                                   3 ,                          .4 ,                         2] 

        # The player's heuristic value is the dot product between their game_values and the given weights.
        allPlayersValues.append(sum(a * b for a, b in zip(game_values, weights)))
    # Return a list with the heuristic value for each player.
    return allPlayersValues

# MAX VALUE: 300
# MIN VALUE: -300
def stateVPValue(player : player, players : list, board : catanBoard):
    returnValue=0
    pVP=player.victoryPoints
    pointsList=[]
    total_knights = sum(person.knightsPlayed for person in players)
    
    # Get list of each player's visible points 
    for i in players:
        pointsList.append(i.visibleVictoryPoints)

    # Get average point value between each player
    avgPoints=sum(pointsList)/len(pointsList)
    # Heuristic higher if above average, lower if below
    if pVP<avgPoints: returnValue-=100
    elif pVP>avgPoints: returnValue+=100

    # Give extra credit for having the most, take away for having the fewest VPs.
    if pVP>=max(pointsList):returnValue+=200
    elif pVP<=min(pointsList):returnValue-=200
    
    return returnValue

# MAX VALUE: ≈ 700
# MIN VALUE: ≈ -100
def statePositionValue(player : player, players : list, board: catanBoard):
    returnValue = 0
    playerResourceDistribution = {
        2 : 0, 3 : 0, 4 : 0, 5 : 0, 6 : 0, 
        8 : 0, 9 : 0, 10 : 0, 11 : 0, 12 : 0
    }

    # For each settlement the player has built,
    for settlementCoord in player.buildGraph['SETTLEMENTS']:
        # For each hex adjacent to the settlement,
        for adjacentHex in board.boardGraph[settlementCoord].adjacentHexList:
            # Get the number on the hex
            resourceNum = board.hexTileDict[adjacentHex].resource.num
            # If not a desert
            if not resourceNum is None:
                # Add to player resource distribution
                playerResourceDistribution[int(resourceNum)] += 1
            if board.hexTileDict[adjacentHex].resource.type in ('WOOD', 'ORE', 'SHEEP', 'WHEAT'):
                # Give bonus for wood, ore, sheep, wheat
                returnValue += 50
    # Same logic, doubled for cities
    for settlementCoord in player.buildGraph['CITIES']:
        for adjacentHex in board.boardGraph[settlementCoord].adjacentHexList:
            resourceNum = board.hexTileDict[adjacentHex].resource.num
            if not resourceNum is None:
                playerResourceDistribution[int(resourceNum)] += 2
            if board.hexTileDict[adjacentHex].resource.type in ('WOOD', 'ORE', 'SHEEP', 'WHEAT'):
                returnValue += 50

    # Give bonus for having a port
    if player.portList:
        returnValue += 100
    
    dice_weights = {
        2: 1, 3: 2, 4: 3, 5: 4, 6: 5,
        8: 5, 9: 4, 10: 3, 11: 2, 12: 1
    }

    # Values how well a players resources are distributed across the board weighted by the likeliness of rolling them
    returnValue += 2*sum(playerResourceDistribution.get(dice, 0) * weight for dice, weight in dice_weights.items())

    tot_cities, tot_settlements = 0, 0
    for person in players:
        tot_settlements += len(person.buildGraph['SETTLEMENTS'])
        tot_cities += len(person.buildGraph['CITIES'])

    # Value above-average number of settlements, cities and devalue below average.
    if len(person.buildGraph['SETTLEMENTS']) > (tot_settlements/len(players)): returnValue += 50
    elif len(person.buildGraph['SETTLEMENTS']) <= (tot_settlements/len(players)): returnValue -= 50
    if len(person.buildGraph['CITIES']) > (tot_settlements/len(players)): returnValue += 50
    elif len(person.buildGraph['CITIES']) <= (tot_settlements/len(players)): returnValue -= 50

    return returnValue

# MAX VALUE: 600 (theoretical, would never happen) + 150 per dev card in hand
# MIN VALUE: 0
def stateDevCardValue(player : player, players : list, board: catanBoard): 
    returnValue = 0

    if player.largestArmyFlag: returnValue += 100
    if player.longestRoadFlag: returnValue += 200
    for person in players: 
        if person is player:
            continue
        # Value larges army
        if person.largestArmyFlag: 
            if (person.knightsPlayed - player.knightsPlayed) < 1: 
                if player.devCards['KNIGHT'] > 0: 
                    returnValue += 100
                else:
                    returnValue += 50
        # Value for longest road commented to reduce funky road building
        # elif person.longestRoadFlag: 
        #     if (person.get_road_length(board) - player.get_road_length(board)) < 1: 
        #         if player.devCards['ROADBUILDER'] > 0 or (player.resources['BRICK'] > 0 and player.resources['WOOD'] > 0):
        #             returnValue += 100
        #         else:
        #             returnValue += 50

    # Value resource-getting cards higher if low on cards.
    if sum(player.resources.values()) < 2:
        for _ in range(player.devCards['YEAROFPLENTY'] + player.devCards['MONOPOLY']):
            returnValue += 100
    else: 
        for _ in range(player.devCards['YEAROFPLENTY'] + player.devCards['MONOPOLY']):
            returnValue += 50

    returnValue += sum(player.devCards.values()) * 150

    return returnValue

# Value for how many settlements a player has
def settlementValue(player, board : catanBoard):
    return 300*(len(player.buildGraph["SETTLEMENTS"])-1)

# Value for how many cities a player has
def cityValue(player:player,board:catanBoard):
    retValue=200*len(player.buildGraph["CITIES"])
    if len(player.buildGraph["SETTLEMENTS"])==5:
        retValue*=2
    return retValue
    
# Value for cards in hand
def handValue (player):
    returnValue = 0
    if sum(player.resources.values()) > 7:
        returnValue -= 50
    if sum(player.resources.values()) > 8:
        returnValue-=80
    if sum(player.resources.values()) > 10:
        returnValue-=80
    
    rec_in_hand = []
    for resource, num_rec in player.resources.items():
        if resource not in rec_in_hand and num_rec > 0:
            returnValue += 20
        rec_in_hand.append(resource)

    return returnValue

# Tries to figure out if road shape is good or bad
def goodRoadValue(board: catanBoard, player : player):
    retVal=0
    roadVertices={}
    for road in player.buildGraph['ROADS']:
        if road[0] in roadVertices:
            roadVertices[road[0]]+=1
        else:
            roadVertices[road[0]]=1
        if road[1] in roadVertices:
            roadVertices[road[1]]+=1
        else:
            roadVertices[road[1]]=1
    # Value connecting to one road, not two
    for vertex,count in roadVertices.items():
        if count==1:
            retVal+=10
        if count==2:
            retVal+=100
        if count==3:
            retVal-=150
    # If the player can settle (roads in good position), increase value
    for settlement in board.get_potential_settlements(player).keys():
        retVal += 20
    
    return retVal
