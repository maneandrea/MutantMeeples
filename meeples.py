import random
import time
import datetime
from collections import deque

# TODO add a way to disable meeples and disable black power if hero is disabled
# TODO boardState and move could be integers that are then decoded. Probably much more efficient than creating new objects every time
# TODO boardState could be a dictionary of positions, moves and powers. Mothods would then become static. Probably faster
# TODO boardState needs 8 x 2 x 5 bits for heroes positions, moves list, 3 bit for powers.
# TODO powers are memorized both in moves and boardState, maybe redundand
# TODO parallelize?
# TODO check compatibility between this and the GUI script
# TODO powerId in move could be replaced by True/False. Start and end of them move contain all the informatioms
# TODO use ordered list. more efficient lookup for hashes
# TODO @manenti way to undo animation

heroes_names    = ['black','blue','brown','gray','green','red','white','yellow']
heroes          = range(len(heroes_names))

directions      = [[0,1], [-1,0], [0,-1], [1,0]]
directionNames  = ["right","down","left","up"]

max_total_moves = 24
max_moves       = 10

class Board():
    def __init__(self, canvas=None, size=18):
        '''Initializes the board'''
        self.pieces = {}
        self.starts = {}
        self.atoms = {}
        self.blocked = {}
        self.size = size
        self.stops = []
        self.canvas = canvas
        #This can be set to 1 to stop the execution
        self.sigkill = 0

        squares = random.sample([[a,b] for a in range(size) for b in range(size)]
                                , len(heroes)+1)
        
        self.target = squares[-1]
        self.heroesPositions = squares[:-1]
        for n, c in enumerate(heroes_names):
            self.pieces[c] = Sprite(self, c, *self.heroesPositions[n])
        
        self.walls = []
        # starting configuration to see if solver works
        #self.walls = [(9,1,10,1),(6,1,6,2),(8,7,9,7),(3,9,3,10),(0,2,1,2),(3,5,3,6),
        #              (5,4,6,4),(5,3,5,4),(3,1,4,1),(1,8,1,9),(6,6,7,6),(9,4,9,5),
        #              (8,9,8,10),(1,4,2,4),(1,4,2,4),(7,6,7,7),(7,3,8,3),(4,8,5,8),
        #              (2,0,2,1),(3,2,3,3),(5,5,5,6)]
        # TODO self.atoms   = {0:(3, 14), 1:(7, 10), 2:(10, 7), 3:(14, 3)}

        self.walls = [(0, 2, 1, 2), (2, 1, 3, 1), (3, 1, 3, 2), (4, 0, 4, 1), 
                      (4, 4, 4, 5), (4, 5, 5, 5), (6, 3, 6, 4), (7, 1, 7, 2), 
                      (6, 2, 7, 2), (8, 2, 8, 3), (10, 0, 10, 1), (9, 3, 10, 3), 
                      (11, 2, 11, 3), (11, 2, 12, 2), (10, 4, 11, 4), (10, 4, 10, 5), 
                      (13, 1, 14, 1), (15, 2, 16, 2), (16, 3, 17, 3), (16, 3, 16, 4), 
                      (17, 5, 18, 5), (15, 5, 15, 6), (12, 5, 13, 5), (13, 7, 14, 7), 
                      (14, 6, 14, 7), (14, 8, 14, 9), (15, 8, 16, 8), (16, 10, 17, 10), 
                      (17, 9, 17, 10), (17, 13, 18, 13), (16, 15, 16, 16), (15, 11, 15, 12), 
                      (14, 11, 15, 11), (12, 10, 12, 11), (14, 13, 14, 14), (14, 15, 15, 15), 
                      (15, 17, 15, 18), (12, 17, 13, 17), (12, 16, 12, 17), (11, 7, 11, 8), 
                      (11, 12, 12, 12), (10, 11, 11, 11), (10, 10, 10, 11), (11, 14, 11, 15), 
                      (9, 14, 10, 14), (9, 12, 9, 13), (8, 6, 9, 6), (8, 6, 8, 7), 
                      (7, 7, 8, 7), (6, 7, 7, 7), (6, 7, 6, 8), (4, 7, 5, 7), 
                      (2, 8, 3, 8), (2, 8, 2, 9), (1, 5, 2, 5), (1, 5, 1, 6), 
                      (0, 8, 1, 8), (0, 12, 1, 12), (1, 14, 2, 14), (1, 15, 1, 16), 
                      (3, 10, 4, 10), (5, 9, 6, 9), (8, 9, 8, 10), (7, 11, 7, 12), 
                      (8, 16, 9, 16), (7, 15, 8, 15), (6, 17, 6, 18), (5, 16, 6, 16), 
                      (3, 16, 3, 17), (3, 17, 4, 17), (5, 13, 5, 14), (4, 14, 4, 15), 
                      (3, 12, 3, 13)]
        self.atoms   = {0:(3, 14), 1:(7, 10), 2:(10, 7), 3:(14, 3)}

        self.blocked = {0:(self.size-1, 0), 1:(0, self.size-1)}

    def randomBoard(self):
        squares = random.sample([[a,b] for a in range(self.size) for b in range(self.size)]
                                , len(heroes)+1)
        
        self.target = squares[-1]
        self.heroesPositions = squares[:-1]
        for n, c in enumerate(heroes_names):
            self.pieces[c].row = self.heroesPositions[n][0]
            self.pieces[c].col = self.heroesPositions[n][1]
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

    def add_blocked(self, *pos):
        if len(self.blocked) == 0:
            unique = 0
        else:
            unique = max([a for a in self.blocked.keys()]) + 1
        self.blocked[unique] = pos
        print(f'Added blocked cell with id {unique}')
        print(self.blocked)

    def add_atom(self, *pos):
        if len(self.atoms) == 0:
            unique = 0
        else:
            unique = max([a for a in self.atoms.keys()]) + 1
        self.atoms[unique] = pos
        print(f'Added atom with id {unique}')
    
    def cantMove(self, x, y, v):
        return self.isWall(x, y, v) or self.isEndOfMap(x, y, v)

    def isWall(self, x, y, v):
        if   v == [1,0]  and (x+1, y, x+1, y+1) in self.walls:
            return True
        elif v == [0,1]  and (x, y+1, x+1, y+1) in self.walls:
            return True
        elif v == [-1,0] and (x, y, x, y+1)     in self.walls:
            return True
        elif v == [0,-1] and (x, y, x+1, y)     in self.walls:
            return True
        else:
            return False

    def isEndOfMap(self, x, y, v):
        if   v == [1,0]  and (x+1 >= self.size or (x+1,y) in self.blocked.values()):
            return True
        elif v == [0,1]  and (y+1 >= self.size or (x,y+1) in self.blocked.values()):
            return True
        elif v == [-1,0] and (x-1 < 0          or (x-1,y) in self.blocked.values()):
            return True
        elif v == [0,-1] and (y-1 < 0          or (x,y-1) in self.blocked.values()):
            return True
        else:
            return False
        
    def precomputeStops(self):
        stops = []
        powerStops = []

        powerFcns = {
            'black':  self.blackStops,
            'blue':   self.blueStops,
            'brown':  self.brownStops,
            'gray':   self.grayStops,
            'green':  self.greenStops,
            'red':    self.redStops,
            'white':  self.whiteStops,
            'yellow': self.yellowStops        
        }

        for i in range(self.size):
            stops.append([])
            for j in range(self.size):
                stops[i].append([])
                for d in directions:
                    v = [i, j]
                    done = False
                    while not done:
                        if self.cantMove(v[0], v[1], d):
                            done = True
                            stops[i][j].append(v)
                        else:
                            v = [v[0]+d[0], v[1]+d[1]]

        for heroid, heroname in enumerate(heroes_names):
            powerStops.append([])
            for i in range(self.size):
                powerStops[heroid].append([])
                for j in range(self.size):
                    ps = powerFcns[heroname](i,j)
                    powerStops[heroid][i].append(ps)

        return stops, powerStops

    def redStops(self, i, j):
        res = []
        if not self.cantMove(i, j,  [0,1]):
            res.append([i, j+1])
        if not self.cantMove(i, j, [-1,0]):
            res.append([i-1, j])
        if not self.cantMove(i, j, [0,-1]):
            res.append([i, j-1])
        if not self.cantMove(i, j,  [1,0]):
            res.append([i+1, j])
        return res

    # a white movement is forbidden if there is a corner or two walls in a row
    # TODO check the 2-wall code
    def whiteStops(self, i, j):
        res = []
        if i+1 < self.size and j+1 < self.size and not ((self.cantMove(i, j, [1,0])  and self.cantMove(i, j, [0,1]))  or (self.cantMove(i, j, [1,0])   and self.cantMove(i, j+1, [1,0])) or (self.cantMove(i, j, [0,1])   and self.cantMove(i+1, j, [0,1]))):
            res.append([i+1, j+1])
        if i+1 < self.size and j>0             and not ((self.cantMove(i, j, [1,0])  and self.cantMove(i, j, [0,-1])) or (self.cantMove(i, j, [1,0])   and self.cantMove(i, j-1, [1,0])) or (self.cantMove(i, j, [0,-1])  and self.cantMove(i+1, j, [0,-1]))):
            res.append([i+1, j-1])
        if i>0             and j+1 < self.size and not ((self.cantMove(i, j, [-1,0]) and self.cantMove(i, j, [0,1]))  or (self.cantMove(i, j, [-1,0])  and self.cantMove(i, j+1, [1,0])) or (self.cantMove(i, j, [0,1])   and self.cantMove(i-1, j, [0,1]))):
            res.append([i-1, j+1])
        if i>0             and j>0             and not ((self.cantMove(i, j, [-1,0]) and self.cantMove(i, j, [0,-1])) or (self.cantMove(i, j, [-1,0])  and self.cantMove(i, j-1, [1,0])) or (self.cantMove(i, j, [0,-1])  and self.cantMove(i-1, j, [0,-1]))):
            res.append([i-1, j-1])
        return res

    def greenStops(self, i, j):
        res = []
        if j+3 < self.size:
            res.append([i, j+3])
        if i > 2:
            res.append([i-3, j])
        if j > 2:
            res.append([i, j-3])
        if i+3 < self.size:
            res.append([i+3, j])
        return res

    # as a normal move, but the first wall sets a boolean to True and the move
    # is valid only if it stops somewhere else and this boolean is True
    def grayStops(self, i, j):
        res = []
        for d in directions:
            v = [i, j]
            done = False
            wentThrough = False
            while not done:
                if self.cantMove(v[0], v[1], d):
                    if not wentThrough and self.isWall(v[0], v[1], d):
                        wentThrough = True
                        v = [v[0]+d[0], v[1]+d[1]]
                        continue
                    done = True
                    if wentThrough:
                        res.append(v)
                    else:
                        # I append a non-move if in that direction the power is not usable
                        # so that when I cycle over the stops the index and the direction coincide
                        res.append([i,j])
                else:
                    v = [v[0]+d[0], v[1]+d[1]]
        return res

    def blueStops(self, i, j):
        return list(self.atoms.values())

    # TODO doesn't work if blocked cells are not on the border of the map...
    # same as gray power. The edge of the map makes it wrap around.
    # the move is considered only if I wrapped once.
    # the edge of the map is defined in a non-general way
    def yellowStops(self, i, j):
        res = []
        for d in directions:
            v = [i, j]
            done = False
            wentThrough = False
            while not done:
                if self.cantMove(v[0], v[1], d):
                    if not wentThrough and self.isEndOfMap(v[0], v[1], d):
                        wentThrough = True
                        if d == [1,0]:
                            if [0, v[1]] in self.blocked.values():
                                v = [1, v[1]]
                            else:
                                v = [0, v[1]]
                        elif d == [0,1]:
                            if [v[0], 0] in self.blocked.values():
                                v = [v[0], 1]
                            else:
                                v = [v[0], 0]
                        elif d == [-1,0]:
                            if [self.size-1, v[1]] in self.blocked.values():
                                v = [self.size-2, v[1]]
                            else:
                                v = [self.size-1, v[1]]
                        elif d == [0,-1]:
                            if [v[0], self.size-1] in self.blocked.values():
                                v = [v[0], self.size-2]
                            else:
                                v = [v[0], self.size-1]
                        continue
                    done = True
                    if wentThrough:
                        res.append(v)
                    else:
                        # see comment on grey power
                        res.append([i,j])
                else:
                    v = [v[0]+d[0], v[1]+d[1]]
        return res

    def brownStops(self, i, j):
        res = []
        for d in directions:
            v = [i, j]
            done = False
            while not done:
                if self.cantMove(v[0], v[1], d):
                    done = True
                    if v != [i, j]:
                        v = [v[0]-d[0], v[1]-d[1]]
                        res.append(v)
                else:
                    v = [v[0]+d[0], v[1]+d[1]]
        return res

    def blackStops(self, i, j):
        # special case, probably handled later
        return []


                
    def solve(self):
        start_time = time.time()

        numberOfCycles = 0
        movesTested = 0
        
        print("Precomputing stops...")
        stops, powerStops = self.precomputeStops()
        
        # paths contains the list of moves done so far saved in boardState objects
        paths = deque([boardState(self.heroesPositions.copy(), [] ,[False,False,False,False,False,False,False,False])])

        # seenPositions = [paths[0].getHash()]
        
        print("--------------- LOOKING FOR SOLUTION ---------------")
        print("target in ", self.target)
        while(len(paths) > 0): 
            path = paths.popleft()
            numberOfCycles += 1
            if (numberOfCycles % 25000 == 0):
                print("Checking solutions with ",path.getNumberOfTotalMoves()," moves. States checked: ",numberOfCycles)
                if self.sigkill:
                    print("Ok, ok, I'll stop... jeez!")
                    return []
                
            successors = self.generateNextStates(path, stops, powerStops)
            
            for successor in successors:
                movesTested = max(movesTested,successor.getNumberOfTotalMoves())
                if movesTested < successor.getNumberOfTotalMoves():
                    print("Something went wrong...") # check that number of tested moves is always increasing (I think)
                    break
                if successor.getLastPosition() == self.target:
                    print("** FOUND SOLUTION IN ",successor.getNumberOfTotalMoves()," MOVES! **")
                    print("# of cycles = ", numberOfCycles)
                    successor.debugPrint()
                    print(successor.getPositions())
                    elapsed = round(time.time() - start_time,2)
                    print("Solution found in ", str(datetime.timedelta(seconds=elapsed)))
                    print(round(numberOfCycles/elapsed,2)," cycles/second")
                    return successor.moves
                else:
                    # TODO if I haven't seen this position already... (if !successor.getHash() in seenPositions...)
                    paths.append(successor)
                    # seenPositions.append(successor.getHash())
        print("Solution not found")
        return []
    
    # given a boardState, returns all the possible future states. 
    def generateNextStates(self, oldState, stops, powerStops):
        result = []
        for hero in heroes:
            if oldState.cantMove(hero):
                hero_pos = oldState.getPosition(hero)
                dirs = list(range(4))
                lastDir = oldState.getLastDirectionMoved()
                # if I have moved this guy the previous move with a normal move
                if oldState.getLastHeroMoved() == hero and not oldState.lastMoveWasPower() and  lastDir >= 0:
                    dirs.remove(lastDir) # removes direction same as last move
                    dirs.remove((lastDir + 2) % 4) # removes direction opposite of last move
                for d in dirs:
                    stop = stops[hero_pos[0]][hero_pos[1]][d].copy()
                    if stop == hero_pos:
                        continue
                    for h in heroes:
                        if h == hero:
                            continue
                        hp = oldState.getPosition(h)
                        
                        # check for hero in same coord and in the right direction
                        if   d == 0 and hp[0] == stop[0] and hero_pos[1] < hp[1] <= stop[1]:
                            stop[1] = hp[1] - 1                       
                        elif d == 1 and hp[1] == stop[1] and stop[0] <= hp[0] < hero_pos[0]:
                            stop[0] = hp[0] + 1
                        elif d == 2 and hp[0] == stop[0] and stop[1] <= hp[1] < hero_pos[1]:
                            stop[1] = hp[1] + 1
                        elif d == 3 and hp[1] == stop[1] and hero_pos[0] < hp[0] <= stop[0]:
                            stop[0] = hp[0] - 1
                    if stop != hero_pos:
                        positions = oldState.getPositions().copy()
                        positions[hero] = stop
                        result.append(boardState(positions, oldState.getMoves().copy(), oldState.getPowerUsed().copy()))
                        result[-1].addMove(hero, d, hero_pos, stop, -1)
                                                            
                if not oldState.powerUsed(hero):
                    if hero == 0:
                        # black... do nothing for now
                        continue
                    else:
                        pStops = powerStops[hero][hero_pos[0]][hero_pos[1]].copy()
                        for d, pstop in enumerate(pStops):
                            if pstop == hero_pos:
                                continue
                            if heroes_names[hero] in ['red','white','green','blue']: # TODO is this slow? is it creating a new list obj everytime?
                                # for these heroes the move is impossible only if there is somebody
                                # in the end cell
                                for h in heroes:
                                    if h == hero or pstop == oldState.getPosition(h):
                                        continue                                    
                                if pstop != hero_pos:
                                    positions = oldState.getPositions().copy()
                                    positions[hero] = pstop
                                    result.append(boardState(positions, oldState.getMoves().copy(), oldState.getPowerUsed().copy()))
                                    result[-1].addMove(hero, 0, hero_pos, pstop, hero)
                                    result[-1].setPowerUsed(hero, True)
                            if heroes_names[hero] == 'brown':
                                # same as in the normal move. Stop 1 cell before other guys
                                # exception if there is a guy in the cell right adjacent where the move doesn't happen at all
                                for h in heroes:
                                    if h == hero:
                                        continue
                                    hp = oldState.getPosition(h)

                                    if   d == 0 and hp[0] == pstop[0] and hero_pos[1] < hp[1] <= pstop[1]:
                                        if hp[1] == hero_pos[1] + 1:
                                            pstop = hero_pos
                                            break
                                        else:
                                            pstop[1] = hp[1] - 2
                                    elif d == 1 and hp[1] == pstop[1] and pstop[0] <= hp[0] < hero_pos[0]:
                                        if hp[0] == hero_pos[0] - 1:
                                            pstop = hero_pos
                                            break
                                        else:
                                            pstop[0] = hp[0] + 2
                                    elif d == 2 and hp[0] == pstop[0] and pstop[1] <= hp[1] < hero_pos[1]:
                                        if hp[1] == hero_pos[1] - 1:
                                            pstop = hero_pos
                                            break
                                        else:
                                            pstop[1] = hp[1] + 2
                                    elif d == 3 and hp[1] == pstop[1] and hero_pos[0] < hp[0] <= pstop[0]:
                                        if hp[0] == hero_pos[0] + 1:
                                            pstop = hero_pos
                                            break
                                        else:
                                            pstop[0] = hp[0] - 2
                                if pstop != hero_pos:
                                    positions = oldState.getPositions().copy()
                                    positions[hero] = pstop
                                    result.append(boardState(positions, oldState.getMoves().copy(), oldState.getPowerUsed().copy()))
                                    result[-1].addMove(hero, d, hero_pos, pstop, hero)
                                    result[-1].setPowerUsed(hero, True)
                            if heroes_names[hero] == 'yellow':
                                # similar to the normal move, but there are three cases:
                                # case 1: the other guy is before the edge of the map (coincides with stop) -> move doesn't happen since it doesn't use the power
                                # case 2: the other guy is right after the edge, move doesn't happen
                                # case 3: the other guy is on the other side -> I stop one cell before him
                                stop = stops[hero_pos[0]][hero_pos[1]][d].copy()
                                for h in heroes:
                                    if h == hero:
                                        continue
                                    hp = oldState.getPosition(h)
                                    if   d == 0 and hp[0] == pstop[0]:
                                        if hero_pos[1] < hp[1] <= stop[1] or hp[1] == 0:
                                            pstop = hero_pos
                                            break
                                        elif 0 < hp[1] <= pstop[1]:
                                            pstop[1] = hp[1] - 1
                                    elif d == 1 and hp[1] == pstop[1]:
                                        if hero_pos[0] > hp[0] >= stop[0] or hp[0] == self.size - 1:
                                            pstop = hero_pos
                                            break
                                        elif self.size > hp[0] >= pstop[0]:
                                            pstop[0] = hp[0] + 1
                                    elif d == 2 and hp[0] == pstop[0]:
                                        if hero_pos[1] > hp[1] >= stop[1] or hp[1] == self.size - 1:
                                            pstop = hero_pos
                                            break
                                        elif self.size > hp[1] >= pstop[1]:
                                            pstop[1] = hp[1] + 1
                                    elif d == 3 and hp[1] == pstop[1]:
                                        if hero_pos[0] < hp[0] <= stop[0] or hp[0] == 0:
                                            pstop = hero_pos
                                            break
                                        elif 0 < hp[0] <= pstop[0]:
                                            pstop[0] = hp[0] - 1

                                if pstop != hero_pos and pstop != stop:
                                    positions = oldState.getPositions().copy()
                                    positions[hero] = pstop
                                    result.append(boardState(positions, oldState.getMoves().copy(), oldState.getPowerUsed().copy()))
                                    result[-1].addMove(hero, d, hero_pos, pstop, hero)
                                    result[-1].setPowerUsed(hero, True)
                            if heroes_names[hero] == 'gray':
                                # as for the yellow, I can only bump after the first wall (i. e. stop)
                                # otherwise it would be a normal move
                                stop = stops[hero_pos[0]][hero_pos[1]][d].copy()
                                for h in heroes:
                                    if h == hero:
                                        continue
                                    hp = oldState.getPosition(h)

                                    if   d == 0 and hp[0] == pstop[0] and hero_pos[1] < hp[1] <= pstop[1]:
                                        if hp[1] > stop[1]:
                                            pstop[1] = hp[1] - 1          
                                        else:
                                            pstop = hero_pos
                                            break
                                    elif d == 1 and hp[1] == pstop[1] and pstop[0] <= hp[0] < hero_pos[0]:
                                        if hp[0] < stop[0]:
                                            pstop[0] = hp[0] + 1
                                        else:
                                            pstop = hero_pos
                                            break
                                    elif d == 2 and hp[0] == pstop[0] and pstop[1] <= hp[1] < hero_pos[1]:
                                        if hp[1] < stop[1]:
                                            pstop[1] = hp[1] + 1
                                        else:
                                            pstop = hero_pos
                                            break
                                    elif d == 3 and hp[1] == pstop[1] and hero_pos[0] < hp[0] <= pstop[0]:
                                        if hp[0] > stop[0]:
                                            pstop[0] = hp[0] - 1
                                        else:
                                            pstop = hero_pos
                                            break
                                if pstop != hero_pos and pstop != stop:
                                    positions = oldState.getPositions().copy()
                                    positions[hero] = pstop
                                    result.append(boardState(positions, oldState.getMoves().copy(), oldState.getPowerUsed().copy()))
                                    result[-1].addMove(hero, d, hero_pos, pstop, hero)
                                    result[-1].setPowerUsed(hero, True)

        return result

class Sprite():
    '''This class is a bit superfluous, I could just access to heroesPosition from
       the GUI. It's true though that it's useful for showing the available moves.'''
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

        # Out of bounds
        if nrow < 0 or ncol < 0 or nrow >= size or ncol >= size:
            return False
        # Colliding with other pieces
        for other in self.master.pieces.values():
            if not other is self:
                if (nrow, ncol) == (other.row, other.col):
                    return False
        # Colliding with walls
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
        #This re-creates the entire list. We have to do it only after drag and drops
        temp = []
        for c in heroes_names:
            temp.append([self.master.pieces[c].row,self.master.pieces[c].col])
        self.master.heroesPositions = temp

class boardState:
    
    def __init__(self, positions, mov, pows):
        self.meeplePositions = positions
        self.moves = mov
        self.usedPower = pows # needed?
    
    # returns number of total moves done until now
    def getNumberOfTotalMoves(self):
        return len(self.moves)
    
    # returns whether this hero can move or not
    # Total moves less than MAX_TOTAL_MOVES
    # less than three heroes moved
    # last move + less than MAX_MOVES
    # has never moved
    def cantMove(self, hero):
        if len(self.moves)==0:
            # if this is the first move of the state I can always move
            return True
        if (len(self.moves) > max_total_moves):
            return False
        if self.getHero(self.moves[-1]) == hero:
            # if the last move was done by hero, make sure that I haven'd done more than max_moves (10 in the actual game)
            c = 0 # counts the number of moves I have done
            for m in self.moves:
                if self.getHero(m) == hero:
                    c += 1
            return c < max_moves
        else:
            # if the previous move was not me, make sure that I have never moved and I haven't already moved 3 different heroes before
            c = 0 # counts the number of different heroes that have moved
            last = -1 # hero thad did the last move checked
            for m in self.moves:
                if last != self.getHero(m): # if I have never seen the last hero, increment c
                    c += 1
                    last = self.getHero(m)
                if self.getHero(m) == hero: # if I find hero, I have already moved
                    return False
            if c > 2:
                return False
        return True
    
    # returns whether that hero has used its power
    def powerUsed(self, hero):
        return self.usedPower[hero]
    
    # returns power used list
    def getPowerUsed(self):
        return self.usedPower
        
    # sets power used
    def setPowerUsed(self, hero, value):
        self.usedPower[hero] = value
    
    # returns last move done in this state
    def getLastDirectionMoved(self):
        if len(self.moves)==0:
            return -1
        return (self.moves[-1] >> 25) & 3
        
    # returns last hero moved
    def getLastHeroMoved(self):
        if len(self.moves)==0:
            return -1
        return (self.moves[-1] >> 27) & 31
    
    # returns all positions array
    def getPositions(self):
        return self.meeplePositions
    
    # returns position of given hero
    def getPosition(self, hero):
        return self.meeplePositions[hero]
    
    # used to determine wether last move was the winning one
    def getLastPosition(self):
        return self.meeplePositions[self.getLastHeroMoved()]
    
    def lastMoveWasPower(self):
        return self.moves[-1] & 31 < 31
    
    # return moves array
    def getMoves(self):
        return self.moves
    
    # helper function. Given a move returns the hero Id
    def getHero(self, m):
        return (m >> 27) & 31

    # adds new move to the state
    # a move is 5 bits hero ID, 2 bits direction, 10 bits start, 10 bit end , 5 bits power ID
    def addMove(self, hero, direction, start, end, powerId):
        move = hero << 2
        move = (move | direction) << 5
        move = (move | start[0]) << 5
        move = (move | start[1]) << 5
        move = (move | end[0]) << 5
        move = (move | end[1]) << 5
        move =  move | (powerId & 31)
        self.moves.append(move)
    
    # TODO
    # returns unique state identifier as a int or something.
    def getHash(self):
        return 0
    
    # prints moves done for debug purposes
    def debugPrint(self):
        for m in self.moves:
            self.printMove(m)
        print(self.usedPower)
        print("end moves")
    
    # move = hhhhhddsssssssssseeeeeeeeeeppppp
    def printMove(self, move):
        hero    = (move >> 27) & 31
        d       = (move >> 25) &  3
        starty  = (move >> 20) & 31
        startx  = (move >> 15) & 31
        endy    = (move >> 10) & 31
        endx    = (move >>  5) & 31
        powerId =  move        & 31
        
        # powerId 31 == -1
        if powerId < 31:
            print("hero ", heroes_names[hero], " uses power of ", heroes_names[powerId], " - [", starty, ",", startx, "] -> [", endy, ",", endx, "]")
        else:
            print("hero ", heroes_names[hero], " - direction ", directionNames[d], " - [", starty, ",", startx, "] -> [", endy, ",", endx, "]")
