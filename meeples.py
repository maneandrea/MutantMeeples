import random
import time
import datetime

# TODO add a way to disable meeples
# TODO boardState and move could be integers that are then decoded. Probably much more efficient than creating new objects every time
# TODO parallelize?

heroes_names = ('black','blue','brown','gray','green','red','white','yellow')
heroes       = range(len(heroes_names))

directions     = [[0,1], [-1,0], [0,-1], [1,0]]
directionNames = ("right","down","left","up")

max_total_moves = 24
max_moves       = 10

class Board():
    def __init__(self, canvas=None, size=18):
        '''Initializes the board'''
        self.pieces = {}
        self.starts = {}
        self.size = size
        self.stops = []
        self.canvas = canvas

        squares = random.sample([[a,b] for a in range(size) for b in range(size)]
                                , len(heroes)+1)
        
        self.target = squares[-1]
        self.heroesPositions = squares[:-1]
        for n, c in enumerate(heroes_names):
            self.pieces[c] = Sprite(self, c, *self.heroesPositions[n])
        
        # starting configuration to see if solver works
        self.walls = [(9,1,10,1),(6,1,6,2),(8,7,9,7),(3,9,3,10),(0,2,1,2),(3,5,3,6),
                      (5,4,6,4),(5,3,5,4),(3,1,4,1),(1,8,1,9),(6,6,7,6),(9,4,9,5),
                      (8,9,8,10),(1,4,2,4),(1,4,2,4),(7,6,7,7),(7,3,8,3),(4,8,5,8),
                      (2,0,2,1),(3,2,3,3),(5,5,5,6)]

    def randomBoard(self):
        squares = random.sample([[a,b] for a in range(self.size) for b in range(self.size)]
                                , len(heroes)+1)
        
        self.target = squares[-1]
        self.heroesPositions = squares[:-1]
        for n, c in enumerate(heroes_names):
            self.pieces[c].place(*self.heroesPositions[n])
        self.canvas.redraw_canvas()

    def place_wall(self, pos1, pos2, vorh):
        if vorh == 'vertical':
            r1,c1 = pos1, pos2
            r2 = r1+1
            c2 = c1
            self.walls.append((r1,c1,r2,c2))
            print(f'Vertical wall placed at ({r1},{c1})--({r2},{c2})')
        elif vorh == 'horizontal':
            r1,c1 = pos1, pos2
            r2 = r1
            c2 = c1+1
            self.walls.append((r1,c1,r2,c2))
            print(f'Horizontal wall placed at ({r1},{c1})--({r2},{c2})')
            
        print(self.walls)

    def place_target(self, *pos):
        self.target = list(pos)
        print(f'Target set in position ({pos[0]},{pos[1]})')

    def add_start(self, *pos):
        if len(self.starts) == 0:
            unique = 0
        else:
            unique = max([a for a in self.starts.keys()]) + 1
        self.starts[unique] = pos
        print(f'Added start with id {unique}')
     
    def isWall(self, x, y, v):
        if v == [1,0] and (x+1 >= self.size or (x+1, y, x+1, y+1) in self.walls):
            return True
        elif v == [0,1] and (y+1 >= self.size or (x, y+1, x+1, y+1) in self.walls):
            return True
        elif v == [-1,0] and (x-1 < 0 or (x, y, x, y+1) in self.walls):
            return True
        elif v == [0,-1] and (y-1 < 0 or (x, y, x+1, y) in self.walls):
            return True
        else:
            return False
        
    def precomputeStops(self):
        for i in range(self.size):
            self.stops.append([])
            for j in range(self.size):
                self.stops[i].append([])
                for d in directions:
                    v = [i, j]
                    done = False
                    while not done:
                        if self.isWall(v[0], v[1], d):
                            done = True
                            self.stops[i][j].append(v)
                        else:
                            v = [v[0]+d[0], v[1]+d[1]]

        # TODO precompute powers and add them to powerStops[id]...


                
    def solve(self):
        start_time = time.time()

        numberOfCycles = 0
        movesTested = 0
        
        print("Precomputing stops...")
        self.stops = []
        self.precomputeStops()
        
        # paths contains the list of moves done so far saved in boardState objects
        paths = [boardState(self.heroesPositions.copy(), [] ,[False, False, False])] #do better
        seenPositions = [paths[0].getHash()]
        
        print("--------------- LOOKING FOR SOLUTION ---------------")
        print("target in ", self.target)
        while(len(paths) > 0): 
            path = paths.pop(0)
            numberOfCycles += 1
            if (numberOfCycles % 25000 == 0):
                print("checking ",path.getNumberOfTotalMoves()," moves. Cycle ",numberOfCycles)
                
            successors = self.generateNextStates(path)
            
            for successor in successors:
                movesTested = max(movesTested,successor.getNumberOfTotalMoves())
                if movesTested > max_total_moves:
                    print("More than ", max_total_moves, " are needed")
                    break
                if movesTested < successor.getNumberOfTotalMoves():
                    print("Something went wrong...") # check that number of tested moves is always increasing (I think)
                if successor.getLastPosition() == self.target:
                    print("** FOUND SOLUTION IN ",successor.getNumberOfTotalMoves()," MOVES! **")
                    print("# of cycles = ", numberOfCycles)
                    successor.debugPrint()
                    print(successor.getPositions())
                    elapsed = round(time.time() - start_time,2)
                    print("Solution found in ", str(datetime.timedelta(seconds=elapsed)))
                    print(round(numberOfCycles/elapsed,2)," cycles/second")
                    return
                else:
                    # TODO if I haven't seen this position already... (if !successor.getHash() in seenPositions...)
                    paths.append(successor)
                    seenPositions.append(successor.getHash())
        print("Solution not found")
        return None
    
    # given a boardState, returns all the possible future states. 
    def generateNextStates(self, oldState):
        result = []
        for hero in heroes:
            if oldState.canMove(hero):
                hero_pos = oldState.getPosition(hero)
                dirs = list(range(4))
                lastDir = oldState.getLastDirectionMoved()
                # if I have moved this guy the previous move
                if oldState.getLastHeroMoved() == hero and lastDir >= 0:
                    dirs.remove(lastDir) # removes direction same as last move
                    dirs.remove((lastDir + 2) % 4) #removes direction opposite of last move
                for d in dirs:
                    stop = self.stops[hero_pos[0]][hero_pos[1]][d].copy()
                    if stop == hero_pos:
                        continue
                    for h in heroes:
                        if h == hero:
                            continue
                        hp = oldState.getPosition(h)
                        
                        #print("d = ", d, " hp = ", hp, " stop = ", stop, " hero_pos = ", hero_pos)
                        
                        #check for hero in same coord and in the right direction
                        if hp[0] == stop[0] and d == 0 and hero_pos[1] < hp[1] <= stop[1]:
                            stop[1] = hp[1] - 1                       
                        elif hp[1] == stop[1] and d == 1 and stop[0] <= hp[0] < hero_pos[0]:
                            stop[0] = hp[0] + 1
                        elif hp[0] == stop[0] and d == 2 and stop[1] <= hp[1] < hero_pos[1]:
                            stop[1] = hp[1] + 1
                        elif hp[1] == stop[1] and d == 3 and hero_pos[0] < hp[0] <= stop[0]:
                            stop[0] = hp[0] - 1
                    if stop != hero_pos:
                        positions = oldState.getPositions().copy()
                        positions[hero] = stop
                        result.append(boardState(positions, oldState.getMoves().copy(), oldState.getPowerUsed().copy()))
                        result[-1].addMove(hero, d, hero_pos, stop, -1)
                                                            
                    #if not oldState.powerUsed(hero):
                        # TODO
                        # stop = powerstop[hero][x,y,d]
                        # check that I can do that (different for every power)
                        # 
                        # blue   --- no other hero in final position
                        # brown  --- same as normal move check, but stopping 1 square early
                        # gray   --- no hero inbetween (the wall in the middle is automatically ignored)
                        # green  --- no other hero in final position
                        # red    --- no other hero in final position
                        # white  --- no other hero in final position
                        # yellow --- no hero inbetween (with coordinate looping, maybe check the two region before and after the warp)

        return result

class Sprite():
    def __init__(self, master, color, *pos):
        '''Initializes the single piece'''
        self.color = color
        self.master = master
        self.row, self.col = pos

    def admissible(self, vr, vc, start=None):
        '''Determines whether a move is legal given a unit displacement vector'''
        size = self.master.size
        if start is None:
            row = self.row
            col = self.col
        else:
            row,col = start
        nrow, ncol = (vr + row, vc + col)

        #Out of bounds
        if nrow < 0 or ncol < 0 or nrow >= size or ncol >= size:
            return False
        #Colliding with other pieces
        for other in self.master.pieces.values():
            if not other is self:
                if (nrow, ncol) == (other.row, other.col):
                    return False
        #Colliding with walls
        v = vr,vc
        if v == (1,0) and (nrow,ncol,nrow,ncol+1) in self.master.walls:
            return False
        elif v == (0,1) and (nrow,ncol,nrow+1,ncol) in self.master.walls:
            return False
        elif v == (-1,0) and (nrow+1,ncol,nrow+1,ncol+1) in self.master.walls:
            return False
        elif v == (0,-1) and (nrow,ncol+1,nrow+1,ncol+1) in self.master.walls:
            return False
        
        return True

    def available_moves(self):
        '''Returns a list of the available moves of a given piece'''
        moves = []
        for direction in ((1,0),(0,1),(-1,0),(0,-1)):
            start = self.row, self.col
            move = None
            while self.admissible(*direction,start):
                start = start[0]+direction[0], start[1]+direction[1]
                move = start
            if not move is None:
                moves.append(move)

        return moves
            

    def place(self, *pos):
        for other in self.master.pieces.values():
            if pos == (other.row, other.col):
                return None
        self.row, self.col = pos

class boardState:
    
    def __init__(self, positions, mov, pows):
        self.meeplePositions = positions
        self.moves = mov
        self.usedPower = pows
    
    #returns number of total moves done until now
    def getNumberOfTotalMoves(self):
        return len(self.moves)
    
    # TODO check if this is all implemented
    # return whether this hero can move or not
    # less than three heroes moved
    # last move + less than MAX_MOVES
    # has never moved
    def canMove(self, hero):
        if len(self.moves)==0:
            # if this is the first move of the state I can always move
            return True
        if self.moves[-1].getHero() == hero:
            # if the last move was done by hero, make sure that I haven'd done more than max_moves (10 in the actual game)
            c = 0 # counts the number of moves I have done
            for m in self.moves:
                if m.getHero() == hero:
                    c += 1
            return c < max_moves
        else:
            # if the previous move was not me, make sure that I have never moved and I haven't already moved 3 different heroes before
            c = 0 # counts the number of different heroes that have moved
            last = -1 # hero thad did the last move checked
            for m in self.moves:
                if last != m.getHero(): # if I have never seen the last hero, increment c
                    c += 1
                    last = m.getHero()
                if m.getHero() == hero: # if I find hero, I have already moved
                    return False
            if c > 2:
                return False
        return True
    
    #return whether that hero has used its power
    def powerUsed(self, hero):
        return self.usedPower[hero]
    
    #return power used list
    def getPowerUsed(self):
        return self.usedPower
        
    #sets power used
    def setPowerUsed(self, hero,value):
        self.usedPower[hero] = value
    
    #return last move done in this state
    def getLastDirectionMoved(self):
        if len(self.moves)==0:
            return -1
        return self.moves[-1].getDirection()
        
    #return last hero moved
    def getLastHeroMoved(self):
        if len(self.moves)==0:
            return -1
        return self.moves[-1].getHero()
    
    #return all positions array
    def getPositions(self):
        return self.meeplePositions
    
    #returns position of given hero
    def getPosition(self, hero):
        return self.meeplePositions[hero]
    
    #used to determine wether last move was the winning one
    def getLastPosition(self):
        return self.meeplePositions[self.moves[-1].getHero()]
    
    #return moves array
    def getMoves(self):
        return self.moves
    
    #add new move to the state
    def addMove(self, hero, direction, start, end, power):
        self.moves.append(move(hero, direction, start, end, power))
    
    # TODO
    # returns unique state identifier as a int or something.
    def getHash(self):
        return 0
    
    #print moves done for debug purposes
    def debugPrint(self):
        for m in self.moves:
            m.printMove()
        print(self.usedPower)
        print("end move")
    
class move:
        
    # powerId is the which hero's power is used. -1 = no power.
    def __init__(self, hero, direction, start, end, powerId):
        self.hero = hero
        self.direction = direction
        self.powerId = powerId
        # TODO remove start and end, only for debug
        self.start = start 
        self.end = end
        
    #return whether this is a normal move or a power
    def isPower(self):
        return self.powerId >= 0
            
    def getDirection(self):
        return self.direction
            
    def getHero(self):
        return self.hero
            
    def printMove(self):
        if self.isPower():
            print("hero ", heroes_names[self.hero], " uses power id ", self.powerId, " - direction ", self.direction, " ", self.start, " -> ", self.end)
        else:
            print("hero ", heroes_names[self.hero], " - direction ", directionNames[self.direction], " ", self.start, " -> ", self.end)