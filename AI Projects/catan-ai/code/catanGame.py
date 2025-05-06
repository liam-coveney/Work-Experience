#Settlers of Catan
#Gameplay class with pygame

from board import *
from gameView import *
from player import *
# from heuristicAIPlayer import *
from gameState import *
import dill as pickle
import os
import queue
import numpy as np
import sys, pygame
from minimaxPlayer import minimaxPlayer
import randomPlayer

# Our changes to the borrowed file
# Added dice rolling logic
# Fixed game logic/ game end logic and bugs
# Initializes game based on player names and types
#
# # JUST FOR SAM: puts pygame screen on external monitor
# import subprocess
# subprocess.Popen(["osascript", "/Users/samgreenfield/Library/Mobile Documents/com~apple~ScriptEditor2/Documents/catan_center.scpt"])

#Catan gameplay class definition
class catanGame():
    #Create new gameboard
    def __init__(self, playerTypes : list, playerNames = ['Red', 'Blue', 'Black', 'Yellow']):
        print("Initializing board...")
        self.board = catanBoard()

        #Game State variables
        self.gameOver = False
        self.maxPoints = 10
        self.currPlayer = None
        self.numPlayers = len(playerTypes)
        if self.numPlayers not in [3, 4]:
            raise Exception("Only 3- and 4-player games allowed.")

        self.playerTypes = playerTypes
        self.playerNames = playerNames

        print("Initializing game with {} players...".format(self.numPlayers))
        
        #Initialize blank player queue and initial set up of roads + settlements
        self.playerQueue = queue.Queue(self.numPlayers)
        self.gameSetup = True #Boolean to take care of setup phase

        #Initialize boardview object
        self.boardView = catanGameView(self.board, self)

        #Function to go through initial set up
        self.build_initial_settlements()

        #Display initial board
        self.boardView.displayGameScreen()

    # def __init__(self, gameState: gameState):
    #     self.maxPoints = 10
    #     self.gameSetup = False

    #     self.applyGameState(gameState)

    #     self.boardView = catanGameView(self.board, self)

    #     self.boardView.displayGameScreen()
    
    # Helper function to apply static state to catanGame
    def applyStaticState(self, state: staticState):
        self.board = state.board

    # Helper function to apply dynamic state to catanGame
    def applyDynamicState(self, state: dynamicState):
        self.gameOver = state.gameOver
        self.currPlayer = state.currPlayer
        idx = state.players.index(self.currPlayer)
        state.players = state.players[idx:] + state.players[:idx]
        self.playerQueue = queue.Queue(len(state.players))
        for player in state.players:
            self.playerQueue.put(player)
            
    # Function to apply a gameState object to catanGame
    # importType has three options:
    #       0 - import only static state
    #       1 - import only dynamic state
    #       None: import static and dynamic states
    def applyGameState(self, state: gameState, importType: int = None):
        if importType in [0, None]:
            self.applyStaticState(state.static)
        if importType in [1, None]:
            self.applyDynamicState(state.dynamic)
        self.boardView = catanGameView(self.board, self)
        self.boardView.setup = 1
        self.boardView.displayGameScreen()
    
    def getGameState(self) -> gameState:
        return gameState(self)

    #Function to initialize players + build initial settlements for players
    def build_initial_settlements(self):
        #Initialize new players with names and colors
        playerColors = ['brown3', 'dodgerblue4', 'black', 'gold']
        
        for i in range(self.numPlayers):
            if self.playerTypes[i] == 'human':
                self.playerQueue.put(player(self.playerNames[i], playerColors[i]))
            # elif self.playerTypes[i] == 'originalAI':
            #     aiPlayer = heuristicAIPlayer(self.playerNames[i], playerColors[i], isAI = True)
            #     aiPlayer.updateAI()
            #     self.playerQueue.put(aiPlayer)
            elif self.playerTypes[i] == 'minimaxAI':
                aiPlayer = minimaxPlayer(self.playerNames[i], playerColors[i])
                self.playerQueue.put(aiPlayer)
            elif self.playerTypes[i] == 'random':
                randPlayer = randomPlayer.randomPlayer(self.playerNames[i], playerColors[i])
                self.playerQueue.put(randPlayer)
            else: raise Exception(f"Invalid player type: {self.PlayerTypes[i]}")

        playerList = list(self.playerQueue.queue)

        self.boardView.displayGameScreen() #display the initial gameScreen
        print("Displaying gameScreen.")

        #Build Settlements and roads of each player forwards
        for player_i in playerList: 
            if(player_i.isAI):
                player_i.initial_setup(self.board)
                self.boardView.displayGameScreen()
            
            else:
                self.build(player_i, 'SETTLE')
                self.boardView.displayGameScreen()
                
                self.build(player_i, 'ROAD')
                self.boardView.displayGameScreen()
        
        #Build Settlements and roads of each player reverse
        playerList.reverse()

        for player_i in playerList: 
            if(player_i.isAI):
                player_i.initial_setup(self.board)
                self.boardView.displayGameScreen()

            else:
                self.build(player_i, 'SETTLE')
                self.boardView.displayGameScreen()

                self.build(player_i, 'ROAD')
                self.boardView.displayGameScreen()

            #Initial resource generation
            #check each adjacent hex to latest settlement
            for adjacentHex in self.board.boardGraph[player_i.buildGraph['SETTLEMENTS'][-1]].adjacentHexList:
                resourceGenerated = self.board.hexTileDict[adjacentHex].resource.type
                if(resourceGenerated != 'DESERT'):
                    player_i.resources[resourceGenerated] += 1
                    print("{} collects 1 {} from Settlement".format(player_i.name, resourceGenerated))

        self.gameSetup = False

        return


    #Generic function to handle all building in the game - interface with gameView
    def build(self, player, build_flag):
        if(build_flag == 'ROAD'): #Show screen with potential roads
            if(self.gameSetup):
                potentialRoadDict = self.board.get_setup_roads(player)
            else:
                potentialRoadDict = self.board.get_potential_roads(player)

            roadToBuild = self.boardView.buildRoad_display(player, potentialRoadDict)
            # # Taken care of in buildRoad_display
            # if(roadToBuild != None):
            #     player.build_road(roadToBuild[0], roadToBuild[1], self.board)

            
        if(build_flag == 'SETTLE'): #Show screen with potential settlements
            if(self.gameSetup):
                potentialVertexDict = self.board.get_setup_settlements(player)
            else:
                potentialVertexDict = self.board.get_potential_settlements(player)
            
            vertexSettlement = self.boardView.buildSettlement_display(player, potentialVertexDict)
            # if(vertexSettlement != None):
            #     player.build_settlement(vertexSettlement, self.board) 

        if(build_flag == 'CITY'): 
            potentialCityVertexDict = self.board.get_potential_cities(player)
            vertexCity = self.boardView.buildCity_display(player, potentialCityVertexDict)
            # if(vertexCity != None):
            #     player.build_city(vertexCity, self.board) 


    #Wrapper Function to handle robber functionality
    def robber(self, player):
        potentialRobberDict = self.board.get_robber_spots()
        print("Move Robber!")

        hex_i, playerRobbed = self.boardView.moveRobber_display(player, potentialRobberDict)
        player.move_robber(hex_i, self.board, playerRobbed)


    #Function to roll dice 
    def rollDice(self):
        dice_1 = np.random.randint(1,7)
        dice_2 = np.random.randint(1,7)
        diceRoll = dice_1 + dice_2
        print("Dice Roll = ", diceRoll, "{", dice_1, dice_2, "}")

        self.boardView.displayDiceRoll(diceRoll)
        self.boardView.displayGameScreen()
        return diceRoll

    #Function to update resources for all players
    def update_playerResources(self, diceRoll, currentPlayer):
        if(diceRoll != 7): #Collect resources if not a 7
            #First get the hex or hexes corresponding to diceRoll
            hexResourcesRolled = self.board.getHexResourceRolled(diceRoll)
            #print('Resources rolled this turn:', hexResourcesRolled)

            #Check for each player
            for player_i in list(self.playerQueue.queue):
                #Check each settlement the player has
                for settlementCoord in player_i.buildGraph['SETTLEMENTS']:
                    for adjacentHex in self.board.boardGraph[settlementCoord].adjacentHexList: #check each adjacent hex to a settlement
                        if(adjacentHex in hexResourcesRolled and self.board.hexTileDict[adjacentHex].robber == False): #This player gets a resource if hex is adjacent and no robber
                            resourceGenerated = self.board.hexTileDict[adjacentHex].resource.type
                            player_i.resources[resourceGenerated] += 1
                            print("{} collects 1 {} from Settlement".format(player_i.name, resourceGenerated))
                
                #Check each City the player has
                for cityCoord in player_i.buildGraph['CITIES']:
                    for adjacentHex in self.board.boardGraph[cityCoord].adjacentHexList: #check each adjacent hex to a settlement
                        if(adjacentHex in hexResourcesRolled and self.board.hexTileDict[adjacentHex].robber == False): #This player gets a resource if hex is adjacent and no robber
                            resourceGenerated = self.board.hexTileDict[adjacentHex].resource.type
                            player_i.resources[resourceGenerated] += 2
                            print("{} collects 2 {} from City".format(player_i.name, resourceGenerated))

                print("Player:{}, Resources:{}, Points: {}".format(player_i.name, player_i.resources, player_i.victoryPoints))
                #print('Dev Cards:{}'.format(player_i.devCards))
                #print("RoadsLeft:{}, SettlementsLeft:{}, CitiesLeft:{}".format(player_i.roadsLeft, player_i.settlementsLeft, player_i.citiesLeft))
                print('MaxRoadLength:{}, LongestRoad:{}\n'.format(player_i.maxRoadLength, player_i.longestRoadFlag))
        
        #Logic for a 7 roll
        else:
            #Implement discarding cards
            #Check for each player
            for player_i in list(self.playerQueue.queue):
                player_i.discardResources()

            #Logic for robber
            if(currentPlayer.isAI):
                print("AI using heuristic robber...")
                currentPlayer.moveRobber(self.board)
            else:
                self.robber(currentPlayer)
                self.boardView.displayGameScreen() #Update back to original gamescreen


    #function to check if a player has the longest road - after building latest road
    def check_longest_road(self, player_i):
        if(player_i.maxRoadLength >= 5): #Only eligible if road length is at least 5
            longestRoad = True
            for p in list(self.playerQueue.queue):
                if(p.maxRoadLength >= player_i.maxRoadLength and p != player_i): #Check if any other players have a longer road
                    longestRoad = False
            
            if(longestRoad and player_i.longestRoadFlag == False): #if player_i takes longest road and didn't already have longest road
                #Set previous players flag to false and give player_i the longest road points
                prevPlayer = ''
                for p in list(self.playerQueue.queue):
                    if(p.longestRoadFlag):
                        p.longestRoadFlag = False
                        p.victoryPoints -= 2
                        prevPlayer = 'from Player ' + p.name
    
                player_i.longestRoadFlag = True
                player_i.victoryPoints += 2

                print("Player {} takes Longest Road {}".format(player_i.name, prevPlayer))

    #function to check if a player has the largest army - after playing latest knight
    def check_largest_army(self, player_i):
        if(player_i.knightsPlayed >= 3): #Only eligible if at least 3 knights are player
            largestArmy = True
            for p in list(self.playerQueue.queue):
                if(p.knightsPlayed >= player_i.knightsPlayed and p != player_i): #Check if any other players have more knights played
                    largestArmy = False
            
            if(largestArmy and player_i.largestArmyFlag == False): #if player_i takes largest army and didn't already have it
                #Set previous players flag to false and give player_i the largest points
                prevPlayer = ''
                for p in list(self.playerQueue.queue):
                    if(p.largestArmyFlag):
                        p.largestArmyFlag = False
                        p.victoryPoints -= 2
                        prevPlayer = 'from Player ' + p.name
    
                player_i.largestArmyFlag = True
                player_i.victoryPoints += 2

                print("Player {} takes Largest Army {}".format(player_i.name, prevPlayer))


    #Function that runs the main game loop with all players and pieces
    def playCatan(self):
        #self.board.displayBoard() #Display updated board
        self.boardView.setup = 1
        while (self.gameOver == False):
            #Loop for each player's turn -> iterate through the player queue
            for currPlayer in self.playerQueue.queue:
                if self.gameOver: break
                self.currPlayer = currPlayer
                print("---------------------------------------------------------------------------")
                print("Current Player:", currPlayer.name)

                turnOver = False #boolean to keep track of turn
                diceRolled = False  #Boolean for dice roll status
                
                #Update Player's dev card stack with dev cards drawn in previous turn and reset devCardPlayedThisTurn
                currPlayer.updateDevCards()
                currPlayer.devCardPlayedThisTurn = False

                self.boardView.displayGameScreen()
                pygame.display.update()

                diceNum = None
                tradeMade = False
                
                while(turnOver == False):
                    if(currPlayer.isAI):
                        pygame.event.pump()
                        #Roll Dice
                        if not diceRolled: 
                            diceNum = self.rollDice()
                            self.update_playerResources(diceNum, currPlayer)
                            self.boardView.displayDiceRoll(diceNum)
                            pygame.display.update()
                            diceRolled = True
                        
                        move = currPlayer.move(self.getGameState(), tradeMade)
                        if move[0] == 'proposeTrade': tradeMade = True
                        if move[0] == 'endTurn': turnOver = True
                            
                        #Check if AI player gets longest road/largest army and update Victory points
                        self.check_longest_road(currPlayer)
                        self.check_largest_army(currPlayer)
                        # print("Player:{}, Resources:{}, Points: {}".format(currPlayer.name, currPlayer.resources, currPlayer.victoryPoints))
                        
                        pygame.event.pump()
                        self.boardView.displayGameScreen()
                        pygame.display.update() #Update back to original gamescreen

                    else: #Game loop for human players
                        for e in pygame.event.get(): #Get player actions/in-game events
                            #print(e)
                            if e.type == pygame.QUIT:
                                sys.exit(0)

                            #Check mouse click in rollDice
                            if(e.type == pygame.MOUSEBUTTONDOWN):
                                #Check if player rolled the dice
                                if(self.boardView.rollDice_button.collidepoint(e.pos)):
                                    if(diceRolled == False): #Only roll dice once
                                        diceNum = self.rollDice()
                                        diceRolled = True
                                        
                                        self.boardView.displayDiceRoll(diceNum)
                                        #Code to update player resources with diceNum
                                        self.update_playerResources(diceNum, currPlayer)

                                #Check if player wants to build road
                                if(self.boardView.buildRoad_button.collidepoint(e.pos)):
                                    #Code to check if road is legal and build
                                    if(diceRolled == True): #Can only build after rolling dice
                                        self.build(currPlayer, 'ROAD')
                                        self.boardView.displayGameScreen()#Update back to original gamescreen

                                        #Check if player gets longest road and update Victory points
                                        self.check_longest_road(currPlayer)
                                        #Show updated points and resources  
                                        print("Player:{}, Resources:{}, Points: {}".format(currPlayer.name, currPlayer.resources, currPlayer.victoryPoints))

                                #Check if player wants to build settlement
                                if(self.boardView.buildSettlement_button.collidepoint(e.pos)):
                                    if(diceRolled == True): #Can only build settlement after rolling dice
                                        self.build(currPlayer, 'SETTLE')
                                        self.boardView.displayGameScreen()#Update back to original gamescreen
                                        #Show updated points and resources  
                                        print("Player:{}, Resources:{}, Points: {}".format(currPlayer.name, currPlayer.resources, currPlayer.victoryPoints))

                                #Check if player wants to build city
                                if(self.boardView.buildCity_button.collidepoint(e.pos)):
                                    if(diceRolled == True): #Can only build city after rolling dice
                                        self.build(currPlayer, 'CITY')
                                        self.boardView.displayGameScreen()#Update back to original gamescreen
                                        #Show updated points and resources  
                                        print("Player:{}, Resources:{}, Points: {}".format(currPlayer.name, currPlayer.resources, currPlayer.victoryPoints))

                                #Check if player wants to draw a development card
                                if(self.boardView.devCard_button.collidepoint(e.pos)):
                                    if(diceRolled == True): #Can only draw devCard after rolling dice
                                        currPlayer.draw_devCard(self.board)
                                        #Show updated points and resources  
                                        print("Player:{}, Resources:{}, Points: {}".format(currPlayer.name, currPlayer.resources, currPlayer.victoryPoints))
                                        print('Available Dev Cards:', currPlayer.devCards)
                                        self.boardView.displayGameScreen()

                                #Check if player wants to play a development card - can play devCard whenever after rolling dice
                                if(self.boardView.playDevCard_button.collidepoint(e.pos)):
                                        currPlayer.play_devCard(self)
                                        self.boardView.displayGameScreen()#Update back to original gamescreen
                                        
                                        #Check for Largest Army and longest road
                                        self.check_largest_army(currPlayer)
                                        self.check_longest_road(currPlayer)
                                        #Show updated points and resources  
                                        print("Player:{}, Resources:{}, Points: {}".format(currPlayer.name, currPlayer.resources, currPlayer.victoryPoints))
                                        print('Available Dev Cards:', currPlayer.devCards)

                                #Check if player wants to trade with the bank
                                if(self.boardView.tradeBank_button.collidepoint(e.pos)):
                                        currPlayer.initiate_trade(self, 'BANK')
                                        self.boardView.displayGameScreen()
                                        pygame.display.update()
                                        #Show updated points and resources  
                                        print("Player:{}, Resources:{}, Points: {}".format(currPlayer.name, currPlayer.resources, currPlayer.victoryPoints))
                                
                                #Check if player wants to trade with another player
                                if(self.boardView.tradePlayers_button.collidepoint(e.pos)):
                                        currPlayer.initiate_trade(self, 'PLAYER')
                                        #Show updated points and resources  
                                        print("Player:{}, Resources:{}, Points: {}".format(currPlayer.name, currPlayer.resources, currPlayer.victoryPoints))

                                #Check if player wants to end turn
                                if(self.boardView.endTurn_button.collidepoint(e.pos)):
                                    if(diceRolled == True): #Can only end turn after rolling dice
                                        print("Ending Turn!")
                                        turnOver = True  #Update flag to nextplayer turn
                                        self.boardView.displayGameScreen()

                                if(self.boardView.saveGame_button.collidepoint(e.pos)):
                                    file_path = "saves/slot.ctn"
                                    with open(file_path, "wb") as f:
                                        pickle.dump(self.getGameState(), f)
                                    print("Game saved to Slot")

                                if(self.boardView.loadGame_button.collidepoint(e.pos)):
                                    file_path = "saves/slot.ctn"
                                    if os.path.exists(file_path):
                                        with open(file_path, "rb") as f:
                                            state = pickle.load(f)
                                            self.applyGameState(state)
                                        print("Game loaded from Slot")
                                    else: print("File not found")
                                
                                self.boardView.displayGameScreen()
                                self.boardView.displayDiceRoll(diceNum)
                                pygame.display.update()

                    #Update the display
                    # self.displayGameScreen(None, None)
                    pygame.display.update()
                    
                    #Check if game is over
                    if currPlayer.victoryPoints >= self.maxPoints:
                        self.gameOver = True
                        self.turnOver = True
                        print("====================================================")
                        print("PLAYER {} WINS!".format(currPlayer.name))
                        pygame.event.pump()
                        break
        # while True:
        #     for event in pygame.event.get():
        #         if event.type == pygame.QUIT:
        #             pygame.quit()
        #             sys.exit()
        #     pygame.display.update()

# catanGame(["human", "minimaxAI", "minimaxAI"]).playCatan()