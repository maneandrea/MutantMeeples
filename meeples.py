import random

colors = ('black','blue','brown','gray','green','red','white','yellow')

class Board():
    def __init__(self, size=18):
        '''Initializes the board'''
        self.pieces = {}
        self.starts = {}
        self.size = size
        squares = random.sample([(a,b) for a in range(size) for b in range(size)]
                                , len(colors)+1)
        self.target = squares[-1]
        for n, c in enumerate(colors):
            self.pieces[c] = Sprite(self, c, *squares[n])
        self.walls = []

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
        self.target = pos
        print(f'Target set in position ({pos[0]},{pos[1]})')

    def add_start(self, *pos):
        if len(self.starts) == 0:
            unique = 0
        else:
            unique = max([a for a in self.starts.keys()]) + 1
        self.starts[unique] = pos
        print(f'Added start with id {unique}')

class Sprite():
    def __init__(self, master, color, *pos):
        '''Initializes the single piece'''
        self.color = color
        self.master = master
        self.row, self.col = pos

    def admissible(self,vr, vc, start=None):
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
