import tkinter as tk
import random
import copy
import time
import math

#----------------------------------------- Game Logic -----------------------------------------#

def sign(x):
    if x==0: return 0
    if x>0: return 1
    if x<0: return -1

'''
Interface:

thinkSetStone(): simulate place a stone, keeping a trail until reset() is called
   -Avoids needing to copy states. ~2x speedup?

setStone(): permanently set a stone

winner(): winner in the current position

'''

#empty should really be a set
class GameState():
    
    posDirs = [(0,1), (1,1), (1,0), (1,-1)]
    
    def __init__(self, rows, cols):

        self.N = 3
        
        self.stones = {}
        self.empty = []
        self.rows = rows
        self.cols = cols
        self.p1Turn = True
        self.saving = False

        self.winner = 0

        #either ball or a stone
        for i in range(0,rows):
            for j in range(0,cols):
                self.stones[(i,j)] = 0
                self.empty.append((i,j))           

    def makeMove(self,move):
        self.setStone(move[0], move[1])

    def curPlayer(self):
        if(self.p1Turn):
            return 1
        else:
            return -1
    
    def setStone(self,r,c):

        if(self.winner != 0):
            print("winner: ", self.winner)
            print("empty: ", self.empty)
            print("stones: ", self.stones)
        assert(self.winner == 0)

        if(self.saving): self.history.append((r,c))

        if(self.p1Turn):
            color = 1
        else:
            color = -1         
        self.stones[(r,c)] = color
        
        self.updateWinner(r,c,color)
            
        self.empty.remove((r,c))                         
        self.p1Turn = not self.p1Turn

    def inBounds(self,coords):
        r,c = coords[0], coords[1]
        return (r>=0 and r<=self.rows-1 and c>=0 and c<=self.cols-1)

    #better way?
    # is there a new winner this turn?
    # also update threat
    def updateWinner(self,r,c,color):
        for pdir in self.posDirs:
            pcount=0
            ncount=0
            for i in range(1,self.N):
                nextSpot = (r+i*pdir[0],c+i*pdir[1])
                if (self.inBounds(nextSpot) and self.stones[nextSpot] == color):
                    pcount = pcount + 1
                else:
                    break
            for i in range(1,self.N):
                nextSpot = (r-i*pdir[0],c-i*pdir[1])
                if (self.inBounds(nextSpot) and self.stones[nextSpot] == color):
                    ncount =ncount + 1
                else:
                    break
            lineLen = ncount+pcount+1
            if(lineLen >= self.N):
               self.winner = color
                

    #save the current state DOES NOT WORK WITH UNDO
    def save(self):
        self.saving = True
        self.history = []
        self.p1TurnSave = self.p1Turn
    
    #restore to the last saved state
    def restore(self):
        self.p1Turn = self.p1TurnSave
        for move in self.history:
            self.stones[move] = 0
            self.empty.append(move)       
        self.saving = False

    #play out the game without changing gamestate
    def playout(self):      
        self.save()
        while(len(self.empty) != 0 and self.winner == 0):

            r = random.randint(0,len(self.empty)-1)
            nextStone = self.empty[r]
            self.makeMove(nextStone)
        ret = self.winner
        self.restore()
        return ret

    def undo(self,move):
        self.stones[move] = 0
        self.empty.append(move)
        self.winner = 0
        self.p1Turn = not self.p1Turn

#--------------------------------- Game Tree ---------------------------------#
class MCGameTreeNode:
    #need to set the player for the root node
    def __init__(self, parent, move):
        self.parent = parent
        self.childMoves = {}

        if(self.parent != None):
           # print("player: ", self.parent.player())
            self.player = -1 * self.parent.player
        
        self.move = move #the move used to get to this node
        self.p1Wins = 0
        self.p2Wins = 0

        self.lastScore = None

    def winUpdate(self,winner):
        if winner == 1:
            self.p1Wins = self.p1Wins + 1
            return
        if winner == -1:
            self.p2Wins = self.p2Wins + 1
            return
        if winner == 0:
            self.p1Wins = self.p1Wins + 0.5
            self.p2Wins = self.p2Wins + 0.5
            return

    def printDescendents(self, depth):
        print(depth * "    ", str(self.move), " :: [", self.p1Wins, " ", self.p2Wins, "]", "  :: ", self.lastScore)
        for m in self.childMoves:
            self.childMoves[m].printDescendents(depth+1)
        

    #matters whose turn it is
    #t is the total simulations involving the parent
    def score(self, t):

        lastPlayer = -1*self.player
        if(lastPlayer == 1): #CHANGED
            wins = self.p1Wins
        else:
            wins = self.p2Wins

        n = self.p1Wins + self.p2Wins
        c = 1.5 #EXPLORATION CONSTANT

        if n == 0:
            print("this probably shouldn't happen...")
            return float("inf")

        s = (wins/n) + c * math.sqrt(math.log(t)/n)

        self.lastScore = s

        return s #the "suggested" function
        
        

#creates the abstraction of a full game tree stored in memory which can be accessed
class MCGameTree:
    posDirs = [(0,1), (1,1), (1,0), (1,-1)]
    
    #gamestate gets update as we move up and down the tree
    def __init__(self, gamestate):
        self.gamestate = gamestate
        self.root = MCGameTreeNode(None, None)
        self.root.player = 1 #set!
        self.curNode = self.root

    def up(self):
#        print("Going up")
        self.gamestate.undo(self.curNode.move)
        self.curNode = self.curNode.parent
        if(self.curNode == None):
            print("tried to access parent of root") #TESTING CODE

    def down(self,move):
        if(move in self.curNode.childMoves):
            self.curNode = self.curNode.childMoves[move]
        else:
            newNode = MCGameTreeNode(self.curNode,move)
            self.curNode.childMoves[move] = newNode
            self.curNode = newNode
        self.gamestate.makeMove(move)

    #go down the tree until finding unexplored moves
    def newMCSelectNode(self):
        while(True):
            curPlayer = self.gamestate.curPlayer()
            bestScore = -float("inf")
            bestMove = None
            children = self.curNode.childMoves
            if(len(children) != len(self.gamestate.empty) ): #there are unexplored children
 #               print("no children")
                return
            
            for move in self.curNode.childMoves:
                childNode = self.curNode.childMoves[move]
                childScore = childNode.score(self.curNode.p1Wins + self.curNode.p2Wins)
 #               print("childScore: ", childScore)
                if childScore > bestScore:
                    bestScore = childScore
                    bestMove = move
            if(bestMove != None):
 #               print("best: ", bestMove)
                self.down(bestMove)
            else:
 #               print("end of game?")
                return
        
        
    
    #explores a totally random child node
    def MCRandomExplore(self):
        numMoves = len(self.gamestate.empty)
        
        if self.gamestate.winner != 0: return #don't try to explore for a winning position       
        if numMoves == 0: return #other things we could do...
        
        #Might want to make sure that this function does choose something that's already in the tree

        randMove = None
        while((randMove==None) or (randMove in self.curNode.childMoves)): #Really stupid!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            randMove = self.gamestate.empty[random.randint(0,numMoves - 1)] #just use random choice
        self.down(randMove)
        

    #assumes that self.curNode is the state that winner corresponds to
    def backProp(self, winner):
        while(True):
            if(winner == 1): self.curNode.p1Wins = self.curNode.p1Wins + 1
            if(winner == -1): self.curNode.p2Wins = self.curNode.p2Wins + 1
            if(winner == 0):
                self.curNode.p1Wins = self.curNode.p1Wins + 0.5
                self.curNode.p2Wins = self.curNode.p2Wins + 0.5
            #do something for a tie...
                
            if(self.curNode.parent != None):
                self.up()
            else:
                return
    
    def MCiteration(self):
        self.newMCSelectNode()
 #       print("selected: ", self.curNode.move)
 #       self.root.printDescendents(0)
        self.MCRandomExplore()
#        print("random child: ", self.curNode.move)
        winner = self.gamestate.playout()
#        print("playout winner: ", winner)
        self.backProp(winner)
#        print(" ")
#        print(" ")
           

#FAILS TO MAKE WINNING MOVES IN TIC TAC TOE... WHY???
    def getAIMove(self):
        for i in range(0,10000): #VERY SMALL NUMBER OF ITERATIONS!!!!!
            self.MCiteration()
 #       self.root.printDescendents(0)

        curBestMove = None
        curMax = 0
        for m in self.root.childMoves:
            node = self.root.childMoves[m]
            numVisited = node.p1Wins + node.p2Wins
            if(numVisited > curMax):
                curMax = numVisited
                curBestMove = m
        return curBestMove


    def makeMove(self,move):
 #       self.gamestate.makeMove(move)
        self.root = MCGameTreeNode(None, None)
        self.root.player = self.gamestate.curPlayer() #set!
        self.curNode = self.root
        
#---------------------------------------------- GUI ---------------------------------------------#
class Board(tk.Frame):

    cursorRow=-1
    cursorCol=-1
    cursorStoneId = -1

    #get nearest grid point (in L_1 norm) to given coordinates
    def row_col(self,x,y):
        r = (y-self.vborder + 0.5*self.squaresize)//self.squaresize
        c = (x-self.hborder+ 0.5*self.squaresize)//self.squaresize
        return (r,c)

    #use the game state to update the baord GUI
    def updateStones(self):
        for point in self.gamestate.stones:
            r,c = point[0],point[1]
            if((r,c) in self.stoneIDs):
                self.board.delete(self.stoneIDs[(r,c)])
            if (self.gamestate.stones[point] == 1):
                self.stoneIDs[(r,c)] = self.drawStone(r,c,"red")
            elif (self.gamestate.stones[point] == -1):
                self.stoneIDs[(r,c)] = self.drawStone(r,c,"blue")

        

    #called on a click
    def onClick(self,event):
        r,c = self.row_col(event.x,event.y)
        success = self.tryPlace(r,c)
        if(success):
#            nextMove = self.AI.getAIMove()
#            self.AI.makeMove(nextMove[0], nextMove[1])
#            self.gamestate.setStone(nextMove[0],nextMove[1])
             nextMove = self.AI.getAIMove()
             self.gamestate.makeMove(nextMove)
             self.AI.makeMove(nextMove)


             self.updateStones()


    #try to place a stone
    #fails if spot is taken or if it's out of bounds
    def tryPlace(self,r,c):
        if r<0 or r>self.rows-1 or c<0 or c>self.cols-1:
            return False
        if self.gamestate.stones[(r,c)] != 0:
            return False
        self.gamestate.setStone(r,c)
        self.AI.makeMove((r,c))
        self.updateStones()
        return True
        
    #called when the cursor moves
    def onMove(self,event):
        r,c = self.row_col(event.x,event.y)
        if r<0 or r>self.rows-1 or c<0 or c>self.cols-1:
            if(self.cursorStoneId != -1): #copy pasta
                self.board.delete(self.cursorStoneId)
                self.cursorStoneId = -1
            return
        if(r != self.cursorRow or c != self.cursorCol):
            if(self.cursorStoneId != -1):
                self.board.delete(self.cursorStoneId)
            if(self.gamestate.stones[(r,c)] == 0): #empty square
                if(self.gamestate.p1Turn):
                    color = "#FFCCCC"
                else:
                    color = "#CCFFFF"
                self.cursorStoneId = self.drawStone(r,c,color)
                self.cursorRow, self.cursorCol = r,c
            else:
                self.cursorRow, self.cursorCol = -1,-1
        
    #create stone, return ID
    def drawStone(self,r,c,color):
        center = (self.hborder + c*self.squaresize, self.vborder + r*self.squaresize)
        rad = self.stonerad
        return self.board.create_oval(center[0]-rad, center[1]-rad,center[0]+rad,center[1]+rad, fill=color)  


    def __init__(self, parent, gamestate):
        
        tk.Frame.__init__(self,parent)
        self.gamestate = gamestate
        self.rows = self.gamestate.rows #number of horizontal lines
        self.cols = self.gamestate.cols #number of vertical lines
        self.hborder = 50 #left-right border
        self.vborder = 50 #top-bottom border
        self.squaresize = 40
        self.stonerad = 0.3*self.squaresize
        self.stoneIDs = {} #keep track of stone id's

        w = (self.cols-1)*self.squaresize + 2*self.hborder
        h = (self.rows-1)*self.squaresize + 2*self.vborder
        self.board = tk.Canvas(parent, width=w, height=h) #why does this need to be parent rather than self?
        self.board.pack() #necessary?

        ##### AI #####
        self.AI = MCGameTree(self.gamestate)
        ##############

        for i in range(0,self.cols):
            x = self.hborder+i*self.squaresize
            self.board.create_line(x,self.vborder,x,self.vborder+self.squaresize*(self.rows-1))
    
        for i in range(0,self.rows):
            y = self.vborder+i*self.squaresize
            self.board.create_line(self.hborder,y,self.hborder+self.squaresize*(self.cols-1),y)
        
        self.board.bind("<Button-1>", self.onClick)
        self.board.bind("<Motion>", self.onMove)
    

top = tk.Tk()
gamestate = GameState(4,4)
gameboard = Board(top,gamestate)
top.mainloop()
