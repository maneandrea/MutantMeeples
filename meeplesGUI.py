from tkinter import *
from tkinter import PhotoImage, filedialog
from PIL import Image, ImageTk
import os
import math
import time
from meeples import *
#For saving stuff in python's format
import pickle
#For executing the solver as a separate thread, so we can kill it
import threading
from multiprocessing import Process

dir_path = os.path.dirname(os.path.realpath(__file__))
icon = dir_path + '/graphics/icon.png'

"""
TODO: Mettere lista di pupini attivi e farli diversi nella GUI
      Implementare i blocchi neri
"""

#Returns a PhotoImage object with the image resized to the desired amount
def resized_img(size, url):
    if isinstance(size, float) or isinstance(size, int):
        size = (size, size)
    img = Image.open(url)
    img = img.resize((int(size[0]),int(size[1])), Image.BILINEAR)
    return ImageTk.PhotoImage(img)

all_colors = ('black','blue','brown','gray','green','red','white','yellow')
other_figures = ('start', 'target', 'blocked', 'atom')

names = {
        'black':'Carbon',
        'blue':'Blue Beamer',
        'brown':'Shortstop',
        'gray':'Ozzy Mosis',
        'green':'Forrest Jump',
        'red':'Sidestep',
        'white':'Skewt',
        'yellow':'MC Edge'
        }

class GUI:

    size = 600
    squares = 18
    animation_speed = .005
    #urls of pictures
    black_url   = './graphics/Guy_black.png'
    blue_url    = './graphics/Guy_blue.png'
    brown_url   = './graphics/Guy_brown.png'
    gray_url    = './graphics/Guy_gray.png'
    green_url   = './graphics/Guy_green.png'
    red_url     = './graphics/Guy_red.png'
    white_url   = './graphics/Guy_white.png'
    yellow_url  = './graphics/Guy_yellow.png'
    start_url   = './graphics/start.png'
    target_url  = './graphics/target.png'
    atom_url    = './graphics/atom.png'
    blocked_url = './graphics/blocked.png'
    vertical_url  = './graphics/Vertical.png'
    horizontal_url= './graphics/Horizontal.png'
    eraser_url  = './graphics/eraser.png'
    
    def __init__(self, board, master):
        '''Initializes main windows'''
        self.board = board
        self.board.__init__(self, self.squares)
        self.master = master

        #Selected piece
        self.selected = StringVar()
        self.selected.set('None')
        #Calls a function everytime the value changes
        self.selected.trace('w', self.selected_changed)
        #Is it solving or not
        self.solving = False
        #The moves of the last solution
        self.last_moves = None

        #Window
        master.title('Mutant Meeples')
        master.geometry(f'{self.size+200}x{self.size+300}')
        master.call('wm', 'iconphoto', master._w, PhotoImage(file = icon))

        #Canvas
        self.canvas = Canvas(master, width = self.size, height = self.size)

        #Side frame for tools and other stuff
        self.side = Sidebar(self)

        #Bottom frame for logging and other stuff
        self.bot = Frame(master)

        #Box for logging in bot frame
        self.scrollbar = Scrollbar(self.bot)
        self.textbox = Text(self.bot, relief = SUNKEN, state = DISABLED, yscrollcommand = self.scrollbar.set,
                         borderwidth = 3, font = ('DejaVu Sans Mono', 12))
        self.scrollbar.config(command = self.textbox.yview, width = 12)

        #Creates an invisible widget to collect all events while it's animating
        self.fake = Frame(master, width = 0, height = 0)

        self.menu = Menu(master, font = ('DejaVu Sans', 12))
        self.filemenu = Menu(self.menu, tearoff = 0, font = ('DejaVu Sans', 12))
        self.filemenu.add_command(label = "Save...   Ctrl+N", command = self.save_file)
        self.filemenu.add_command(label = "Open...  Ctrl+O", command = self.open_file)
        self.menu.add_cascade(label = "File", menu = self.filemenu)
        #
        master.config(menu = self.menu)

        #Binding keys
        self.canvas.bind('<Up>', self.pressed_up)
        self.canvas.bind('<Down>', self.pressed_down)
        self.canvas.bind('<Left>', self.pressed_left)
        self.canvas.bind('<Right>', self.pressed_right)
        self.canvas.bind('<w>', self.pressed_up)
        self.canvas.bind('<s>', self.pressed_down)
        self.canvas.bind('<a>', self.pressed_left)
        self.canvas.bind('<d>', self.pressed_right)
        self.master.bind('<1>', self.focus_handle)
        self.canvas.bind('<Tab>', self.select_next)
        self.fake.bind('<Tab>', self.select_next)
        self.canvas.bind('<Shift-Up>', self.select_next)
        self.canvas.bind('<Shift-Down>', self.select_previous)
        self.canvas.bind('<Shift-Left>', self.select_previous)
        self.canvas.bind('<Shift-Right>', self.select_next)
        self.canvas.bind('<space>', self.start_solve)
        self.canvas.bind('<r>', self.random_board)
        master.bind("<Control-s>",lambda x: self.save_file())
        master.bind("<Control-o>",lambda x: self.open_file())
        
        #Draws the pieces
        self.draw_canvas()

        #Configure row and column weights
        master.columnconfigure(0, weight = 0)
        master.rowconfigure(0, weight = 0)
        master.columnconfigure(1, weight = 1)
        master.rowconfigure(1, weight = 1)
        #
        self.bot.columnconfigure(0, weight = 1)
        self.bot.rowconfigure(0, weight = 1)

        #Grid everything in the main window
        self.canvas.grid(row = 0, column = 0, sticky = 'news')
        self.bot.grid(row = 1, column = 0, columnspan = 2, sticky = 'news')
        self.fake.grid(row = 0)
        #Grid everything in the bot frame
        self.textbox.grid(row = 0, column = 0, sticky = 'news')
        self.scrollbar.grid(row = 0, column = 1, sticky = 'nes')

        #For redirecting stdout to the textbox
        class StandardOut():
            def __init__(self, obj, master):
                self.stream = obj
                self.master = master
            def write(self, text):
                bf = False
                #Start a print with \bf to print in boldface
                if len(text) > 3:
                    if text[:3] == r'\bf':
                        btext = text[3:]
                        bf = True
                #This also writes on the terminal
                #sys.__stdout__.write(text)
                self.stream.config(state = NORMAL)
                if bf:
                    self.stream.insert(END, btext, 'boldface')
                    self.stream.tag_config('boldface', font=('DejaVu Sans Mono', 14, 'bold'))
                else:
                    self.stream.insert(END, text)
                self.stream.see(END)
                self.stream.config(state = DISABLED)
                self.master.update()
            def flush(self):
                pass

        sys.stdout = StandardOut(self.textbox, self.master)

        print(r'\bfMutant Meeples')
        print('\n'.join((
              '------',
              'Use Shift+(Up/Right) to go to the next Meeple,',
              'Shift+(Down/Left) to go to the previous one.',
              'Otherwise just click on the Meeple to select or hold to drag it.',
              'Hold the right mouse button on a Meeple to show its available moves',
              'Drag and drop elements from the canvas to place/move them.',
              'Use the eraser to remove walls or starting points.',
              'The objective is to reach the target in the least possible number of moves.',
              '------')))

    def picture(self, color, size):
        '''Returns a resized version of the picture as a PhotoImage object'''
        return {
            'black'  : resized_img(size, self.black_url),
            'blue'   : resized_img(size, self.blue_url),
            'brown'  : resized_img(size, self.brown_url),
            'gray'   : resized_img(size, self.gray_url),
            'green'  : resized_img(size, self.green_url),
            'red'    : resized_img(size, self.red_url),
            'white'  : resized_img(size, self.white_url),
            'yellow' : resized_img(size, self.yellow_url),
            'target' : resized_img(size, self.target_url),
            'start'  : resized_img(size, self.start_url),
            'blocked': resized_img(size, self.blocked_url),
            'atom'   : resized_img(size, self.atom_url),
            'vertical'  : resized_img(size, self.vertical_url),
            'horizontal': resized_img(size, self.horizontal_url),
            'eraser' : resized_img(size, self.eraser_url)
            }[color]

    def walls_target_starts(self):
        '''Draws walls, target and starts'''
        factor = self.size / self.squares
        offset = factor / 2

        #Resets the walls
        for w in self.drawn_walls:
            self.canvas.delete(w[0])
        self.drawn_walls = []
    
        #Draws the walls
        for wall in self.board.walls:
            y1,x1,y2,x2 = [factor*a for a in wall]
            drawn_wall = self.canvas.create_line(x1, self.size - y1, x2, self.size - y2, width=5.)
            self.drawn_walls.append((drawn_wall, wall))

        #Resets the sprites in sprite2
        for spr in self.sprites2:
            self.canvas.delete(spr['img'])
        
        #Draws the starting points, blocked cells and atoms
        for name, collection in [('start', 'starts'), ('atom','atoms'), ('blocked', 'blocked')]:
            for i, start in eval('self.board.'+collection+'.items()'):
                self.canvas.images.append(self.picture(name, factor))
                self.sprites2.append(
                    {'img' : self.canvas.create_image(
                                 (start[1]*factor + offset,
                                  self.size - start[0]*factor - offset),
                                 image = self.canvas.images[-1],
                                 tag = name+str(i)),
                     'obj' : name+str(i)})
        #Draws the target
        self.canvas.images.append(self.picture('target', factor))
        r,c = self.board.target
        self.sprites2.append(
            {'img' : self.canvas.create_image(
                         (c*factor + offset,
                          self.size - r*factor - offset),
                         image = self.canvas.images[-1],
                         tag = 'target'),
             'obj' : 'target'})
        self.canvas.tag_bind(self.sprites2[-1]['img'], '<1>', self.side.on_click('target'))
        self.canvas.tag_bind(self.sprites2[-1]['img'], '<B1-Motion>', self.side.on_drag('target'))
        self.canvas.tag_bind(self.sprites2[-1]['img'], '<ButtonRelease-1>', self.side.on_drop('target'))
        self.canvas.tag_bind(self.sprites2[-1]['img'], '<Enter>', self.change_cursor('enter', True))
        self.canvas.tag_bind(self.sprites2[-1]['img'], '<Leave>', self.change_cursor('exit', True))
        

    def draw_canvas(self):
        '''Draws the canvas for the first time'''
        #Define some factors
        factor = self.size / self.squares
        offset = factor / 2

        #Draw the lines
        for r in range(0,self.squares+1):
            self.canvas.create_line(0,r*factor,self.size,r*factor, width=1., fill = '#646464')
        for c in range(0,self.squares+1):
            self.canvas.create_line(c*factor,0,c*factor,self.size, width=1., fill = '#646464')

        #List of all the pieces as {'img': , 'obj': } dictionary
        self.sprites = []
        #List of starts and the target
        self.sprites2 = []
        #This I need for keeping the reference, otherwise it gets garbage collected
        self.canvas.images = []

        #Initializes the pieces
        for color, p in self.board.pieces.items():
            self.canvas.images.append(self.picture(color, factor))
            self.sprites.append(
                {'img' : self.canvas.create_image(
                             (p.col*factor + offset,
                              self.size - p.row*factor - offset),
                             image = self.canvas.images[-1],
                             tag = color),
                 'obj' : p})
            self.canvas.tag_bind(self.sprites[-1]['img'], '<1>', self.on_piece_click(p))
            self.canvas.tag_bind(self.sprites[-1]['img'], '<3>', self.on_piece_right_down(p))
            self.canvas.tag_bind(self.sprites[-1]['img'], '<ButtonRelease-3>', self.on_piece_right_up)
            self.canvas.tag_bind(self.sprites[-1]['img'], '<B1-Motion>', self.on_piece_drag(p))
            self.canvas.tag_bind(self.sprites[-1]['img'], '<ButtonRelease-1>', self.on_piece_drop(p))
            self.canvas.tag_bind(self.sprites[-1]['img'], '<Enter>', self.change_cursor('enter'))
            self.canvas.tag_bind(self.sprites[-1]['img'], '<Leave>', self.change_cursor('exit'))

        #List of all walls
        self.drawn_walls = []
        #Draw the walls, starts, target, atoms and blocked cells
        self.walls_target_starts()


    def redraw_canvas(self, animation=False):
        '''Redraws the canvas'''
        #Define some factors
        factor = self.size / self.squares
        offset = factor / 2

        if self.selected.get() == 'None':
            #Redraws all the pieces, the walls, starts and target
            for c in all_colors:
                self.canvas.delete(c)

            self.walls_target_starts()
            
            for n, sprite in enumerate(self.sprites):
                p = sprite['obj']
                sprite['img'] = self.canvas.create_image(
                                 (p.col*factor + offset,
                                  self.size - p.row*factor - offset),
                                 image = self.canvas.images[n],
                                 tag = p.color)
                self.canvas.tag_bind(sprite['img'], '<1>', self.on_piece_click(p))
                self.canvas.tag_bind(sprite['img'], '<3>', self.on_piece_right_down(p))
                self.canvas.tag_bind(sprite['img'], '<ButtonRelease-3>', self.on_piece_right_up)
                self.canvas.tag_bind(sprite['img'], '<B1-Motion>', self.on_piece_drag(p))
                self.canvas.tag_bind(sprite['img'], '<ButtonRelease-1>', self.on_piece_drop(p))
                self.canvas.tag_bind(sprite['img'], '<Enter>', self.change_cursor('enter'))
                self.canvas.tag_bind(sprite['img'], '<Leave>', self.change_cursor('exit'))
            
        else:
            #Redraws just the selected piece
            for nn, ssprite in enumerate(self.sprites):
                p = ssprite['obj']
                if p.color == self.selected.get():
                    n = nn
                    sprite = ssprite
                    break
            
            if animation:
                self.animate(sprite,
                             self.canvas.coords(sprite['img']),
                             (p.col*factor + offset,
                              self.size - p.row*factor - offset))
            
            self.canvas.delete(self.selected.get())

            sprite['img'] = self.canvas.create_image(
                             (p.col*factor + offset,
                              self.size - p.row*factor - offset),
                             image = self.canvas.images[n],
                             tag = p.color)
            self.canvas.tag_bind(sprite['img'], '<1>', self.on_piece_click(p))
            self.canvas.tag_bind(sprite['img'], '<3>', self.on_piece_right_down(p))
            self.canvas.tag_bind(sprite['img'], '<ButtonRelease-3>', self.on_piece_right_up)
            self.canvas.tag_bind(sprite['img'], '<B1-Motion>', self.on_piece_drag(p))
            self.canvas.tag_bind(sprite['img'], '<ButtonRelease-1>', self.on_piece_drop(p))
            self.canvas.tag_bind(sprite['img'], '<Enter>', self.change_cursor('enter'))
            self.canvas.tag_bind(sprite['img'], '<Leave>', self.change_cursor('exit'))

    def animate(self, sprite, origin, destination):
        '''Makes a small animation showing the piece moving'''
        #Routes all events to this fake rectangle
        self.fake.grab_set()
        self.fake.focus_set()

        img_object = sprite["img"]

        deltax = destination[0] - origin[0]
        deltay = -destination[1] + origin[1]

        for i in range(50):
            ##self.win.move(img_object, deltax / 50, - deltay / 50)
            #This uses a gaussian to animate, but you can also go back to the linear function
            mu = 20
            twosigmasq = 90
            gauss = lambda x : math.exp(-(x-mu)**2/twosigmasq)/math.sqrt(math.pi * twosigmasq)
            self.canvas.move(img_object, deltax * gauss(i), - deltay * gauss(i))
            self.master.update()
            time.sleep(self.animation_speed)

        #Releases the grab
        self.fake.grab_release()
        self.canvas.focus_set()

    def animate_solution(self):
        if self.last_moves is None:
            print("There is not solution to be animated so far")
        else:
            for move in self.last_moves:
                hero    = all_colors[(move >> 27) & 31]
                starty  = (move >> 20) & 31
                startx  = (move >> 15) & 31
                endy    = (move >> 10) & 31
                endx    = (move >>  5) & 31

                for s in self.sprites:
                    if s['obj'].color == hero:
                        sprite = s
                        break
                factor = self.size / self.squares
                origin = [factor*startx, self.size-factor*starty]
                destination = [factor*endx, self.size-factor*endy]
                true_destination = [endy, endx]

                self.animate(sprite, origin, destination)
                self.board.pieces[hero].place(*true_destination)
                self.canvas.tag_raise(hero)
                
        self.last_moves = None

                
    def change_cursor(self, event, override=False):
        '''Change the cursor to the grabbing hand'''
        def hand(event=None):
            if override or self.side.select_only.get() == 0:
                if not self.side.erasingQ.get():
                    self.master.config(cursor = 'hand2')
        def arrow(event=None):
            if not self.side.erasingQ.get():
                self.master.config(cursor = 'arrow')
        if event == 'enter':
            return hand
        else:
            return arrow

    def focus_handle(self, event=None):
        '''Give or take focus away from the canvas'''
        if event.widget == self.canvas:
            self.canvas.focus_set()
        else:
            self.selected.set('None')
            self.master.focus_set()

    def select_next(self, event=None):
        '''Go to the next piece after tab has been pressed. Or makes it so that the fake widget doesn'r lose focus'''
        if event.widget == self.canvas:
            self.canvas.focus_set()
            try:
                next_piece = all_colors.index(self.selected.get()) + 1
            except:
                next_piece = 0
            if next_piece == len(all_colors):
                next_piece = 0
            self.selected.set(all_colors[next_piece])
            #Returning 'break' overrides event propagation
        return 'break'

    def select_previous(self, event=None):
        '''Go to the next piece after tab has been pressed. Or makes it so that the fake widget doesn't lose focus'''
        if event.widget == self.canvas:
            self.canvas.focus_set()
            try:
                next_piece = all_colors.index(self.selected.get()) - 1
            except:
                next_piece = 0
            if next_piece == -1:
                next_piece = len(all_colors)-1
            self.selected.set(all_colors[next_piece])
            #Returning 'break' overrides event propagation
        return 'break'

    def on_piece_click(self, piece):
        '''A piece on the board has been clicked'''
        def f(event=None):
            if self.side.select_only.get():
                self.selected.set(piece.color)
            else:
                self.side.on_click(piece.color)(event)
            
        return f

    def on_piece_drag(self, piece):
        '''A piece on the board has been dragged'''
        def f(event=None):
            if self.side.select_only.get():
                pass
            else:
                self.side.on_drag(piece.color)(event)
            
        return f

    def on_piece_drop(self, piece):
        '''A piece on the board has been dropped'''
        def f(event=None):
            if self.side.select_only.get():
                pass
            else:
                self.side.on_drop(piece.color)(event)
            
        return f

    def on_piece_right_down(self, piece):
        '''Right click on a piece to show the moves'''
        def f(event=None):
            moves = piece.available_moves()
            factor = self.size / self.squares
            offset = factor/2
            radius = offset/2
            for m in moves:
                self.canvas.create_oval((m[1]*factor + offset - radius,
                                         self.size - m[0]*factor - offset - radius,
                                         m[1]*factor + offset + radius,
                                         self.size - m[0]*factor - offset + radius),
                                        width = 8, outline = '#99bbff', tags = 'showmoves')
            
        return f

    def on_piece_right_up(self, event=None):
        '''Release right click to remove the moves being shown'''
        self.canvas.delete('showmoves')

    def pressed_up(self, event=None):
        sel = self.selected.get()
        if sel != 'None':
            selected = self.board.pieces[sel]
            while selected.admissible(1,0):
                selected.row += 1
            self.redraw_canvas(animation=True)
            self.check_finish(selected)

    def pressed_down(self, event=None):
        sel = self.selected.get()
        if sel != 'None':
            selected = self.board.pieces[sel]
            while selected.admissible(-1,0):
                selected.row -= 1
            self.redraw_canvas(animation=True)
            self.check_finish(selected)

    def pressed_left(self, event=None):
        sel = self.selected.get()
        if sel != 'None':
            selected = self.board.pieces[sel]
            while selected.admissible(0,-1):
                selected.col -= 1
            self.redraw_canvas(animation=True)
            self.check_finish(selected)

    def pressed_right(self, event=None):
        sel = self.selected.get()
        if sel != 'None':
            selected = self.board.pieces[sel]
            while selected.admissible(0,1):
                selected.col += 1
            self.redraw_canvas(animation=True)
            self.check_finish(selected)

    def selected_changed(self, *events):
        '''The selected piece has been changed'''
        sel = self.selected.get()
        if sel != 'None':
            self.side.stringlabel.set('Selected: '+names[sel])
            if sel in ['white', 'yellow']:
                backg = 'gray35'
            elif sel == 'gray':
                sel = 'gray25'
                backg = 'gray94'
            else:
                backg = self.master.cget('bg')
            self.side.label.config(fg=sel, bg=backg)
        else:
            self.side.stringlabel.set('')
            backg = self.master.cget('bg')
            self.side.label.config(fg='black', bg=backg)
            

    def check_finish(self, selected):
        '''Checks if the game has been won'''
        if (selected.row, selected.col) == self.board.target:
            print(r'\bfCongratulations, you reached the target!')
    
    def start_solve(self, event=None):
        '''Starts the solver'''
        if self.solving:
            self.board.sigkill = 1
            self.master.config(cursor = 'arrow')
            self.side.solve_button.config(text = 'Solve')
            self.solving = False
        else:
            self.solving = True
            self.board.sigkill = 0
            self.master.config(cursor = 'watch')
            self.side.solve_button.config(text = 'Abort')
            self.side.solve_button.grab_set()
            solve_thread = threading.Thread(target = self.now_solve)
            # TODO using process might be faster than Thread, but anyways we need to think how to manage the parallelization situation first
            # but process and tkinter don't like working together (at least on windows)
            # solve_thread = Process(target = self.now_solve)
            solve_thread.start()        

    def now_solve(self):
        '''The process that gets called'''
        moves = self.board.solve()
        self.last_moves = moves
        self.side.solve_button.grab_release()
        self.master.config(cursor = 'arrow')
        self.side.solve_button.config(text = 'Solve')
        self.solving = False

    def random_board(self, event=None):
        self.selected.set('None')
        self.board.randomBoard()

    def save_file(self):
        current_folder = os.path.dirname(os.path.realpath(__file__))
        filename = filedialog.asksaveasfilename(initialdir = current_folder, title = "Select file",
                                                filetypes = (("Meeples files", "*.bin"),("All files", "*.*")))
        try:
            with open(filename, "wb") as file:
                dumping = (self.board.starts,
                           self.board.atoms,
                           self.board.blocked,
                           self.board.size,
                           self.board.stops,
                           self.board.heroesPositions,
                           self.board.walls,
                           self.board.target)
                pickle.dump(dumping, file)
        except PermissionError:
            print("Error occurred when saving file.")

    def open_file(self):
        current_folder = os.path.dirname(os.path.realpath(__file__))
        filename = filedialog.askopenfilename(initialdir = current_folder, title = "Select file",
                                                filetypes = (("Meeples files", "*.bin"),("All files", "*.*")))
        try:
            with open(filename, "rb") as file:
                loaded = pickle.load(file)
                self.board.starts  = loaded[0]
                self.board.atoms   = loaded[1]
                self.board.blocked = loaded[2]
                self.board.size    = loaded[3]
                self.board.stops   = loaded[4]
                self.board.heroesPositions = loaded[5]
                self.board.walls   = loaded[6]
                self.board.target  = loaded[7]
                self.board.pieces = {}
                for n, c in enumerate(all_colors):
                    self.board.pieces[c] = Sprite(self.board, c, *self.board.heroesPositions[n])
                self.selected.set('None')
                self.canvas.delete("all")
                self.draw_canvas()
        except (FileNotFoundError, TypeError) as e:
            print("Error occurred when loading file.")

class Sidebar:
    '''The sidebar that allows us to choose the pieces and the walls to put on the board'''

    
    def __init__(self, parent):
        '''Initializes the sidebar'''
        frame = self.frame = Frame(parent.master)
        self.parent = parent

        #Size of pictures
        size = min(parent.size / parent.squares, 60)

        #Select pieces or drag pieces when clicking on them
        self.select_only = IntVar()

        #For scheduling the eraser cancellations with after
        self.schedule = None
        
        #Define the buttons
        self.buttons = {}
        frame.columnconfigure(1, weight = 1, minsize = 10)
        for c in range(2):
            frame.columnconfigure(2*c, weight = 1, minsize = size)
            for i, typ in enumerate(other_figures[c::2]):
                pic = parent.picture(typ, size)
                self.buttons[typ] = Button(frame, image = pic)
                self.buttons[typ].img = pic
                self.buttons[typ].bind('<Button-1>', self.on_click(typ))
                self.buttons[typ].bind('<B1-Motion>', self.on_drag(typ))
                self.buttons[typ].bind('<ButtonRelease-1>', self.on_drop(typ))
                #
                frame.rowconfigure(i, weight = 1)
                self.buttons[typ].grid(row = i, column = 2*c, sticky = 'w' if c else 'e')
            #Now the walls
            vh = ('vertical','horizontal')[c]
            wallpic = self.parent.picture(vh, size)
            self.buttons[vh] = Button(frame, image = wallpic)
            self.buttons[vh].img = wallpic
            self.buttons[vh].bind('<Button-1>', self.on_click(vh))
            self.buttons[vh].bind('<B1-Motion>', self.on_drag(vh))
            self.buttons[vh].bind('<ButtonRelease-1>', self.on_drop(vh))
            #
            frame.rowconfigure(i+1, weight = 1)
            self.buttons[vh].grid(row = i+1, column = 2*c, sticky = 'w' if c else 'e')

        self.clear_walls = Button(frame, text = 'Clear all', command = self.clear, font = ('DejaVu Sans', 14))
        self.toggle_button = Checkbutton(frame, text = 'Dragging', variable = self.select_only,
                                         command = self.toggle_drag_select, font = ('DejaVu Sans', 14), indicatoron = 0)
        self.random_button = Button(frame, text = 'Randomize', command = self.parent.random_board, font = ('DejaVu Sans', 14))
        self.solve_button = Button(frame, text = 'Solve', command = self.parent.start_solve, font = ('DejaVu Sans', 14))
        self.animate_button = Button(frame, text = 'Animate', command = self.parent.animate_solution, font = ('DejaVu Sans', 14))
        eraser_pic = self.parent.picture('eraser', size)
        self.erasingQ = IntVar()
        self.erasingQ.set(0)
        self.eraser = Checkbutton(frame, image = eraser_pic, command = self.erase, variable = self.erasingQ, indicatoron=0)
        self.eraser.img = eraser_pic

        #Define a canvas for dragging the images (it belongs to the parent widget! Otherwise we cannot drag it outside of this Frame)
        self.floating = Canvas(parent.master, width = size - 4, height = size - 4, relief = RAISED, bd = 1)
        
        #Configure columns
        frame.columnconfigure(0, weight = 1)
        frame.rowconfigure(0, weight = 1)
        frame.rowconfigure(6, weight = 1)
        frame.rowconfigure(7, weight = 1)
        frame.rowconfigure(8, weight = 1)
        frame.rowconfigure(9, weight = 1)
        frame.rowconfigure(10, weight = 1)
        frame.rowconfigure(11, weight = 1)
        frame.rowconfigure(12, weight = 1)

        #Grid everything
        frame.grid(row = 0, column = 1, sticky = 'news')
        self.eraser.grid(row = 6, column = 0, columnspan = 3)
        self.clear_walls.grid(row = 7, column = 0, columnspan = 3, padx=20, pady=10, sticky = 'nswe')
        self.toggle_button.grid(row = 8, column = 0, columnspan = 3, padx=20, pady=10, sticky = 'nswe')
        self.random_button.grid(row = 9, column = 0, columnspan = 3, padx=20, pady=10, sticky = 'nswe')
        self.solve_button.grid(row = 10, column = 0, columnspan = 3, padx=20, pady=10, sticky = 'nswe')
        self.animate_button.grid(row = 11, column = 0, columnspan = 3, padx=20, pady=10, sticky = 'nswe')

        #Label
        self.stringlabel = StringVar()
        self.label = Label(frame, textvariable = self.stringlabel, font = ('DejaVu Sans', 12))
        frame.rowconfigure(8, weight = 1)
        self.label.grid(row = 12, column = 0, columnspan = 3)

    def toggle_drag_select(self):
        '''Toggles between selecting or dragging pieces'''
        if self.select_only.get():
            self.toggle_button.config(text = 'Selecting')
        else:
            self.toggle_button.config(text = 'Dragging')


    def on_click(self, colororwall):
        '''Places canvas on the spot'''
        def f(event):
            (vx, vy) = (event.x_root - self.parent.master.winfo_x(), event.y_root - self.parent.master.winfo_y())
            if colororwall in other_figures:
                self.floating.remember_image = self.buttons[colororwall].img
            else:
                size = min(self.parent.size / self.parent.squares, 60)
                self.floating.remember_image = self.parent.picture(colororwall, size)
            self.floating.image = self.floating.create_image((0,0), image = self.floating.remember_image, anchor = NW)
            self.floating.place(x = vx, y = vy, anchor = CENTER)
            
        return f


    def on_drag(self, colororwall):
        '''Drags the canvas along with the mouse'''
        def f(event):
            if self.erasingQ.get():
                self.erasingQ.set(0)
                self.parent.canvas.unbind('<B1-Motion>', self.canvasbinding)
            (vx, vy) = (event.x_root - self.parent.master.winfo_rootx(), event.y_root - self.parent.master.winfo_rooty())
            self.floating.place(x = vx, y = vy, anchor = CENTER)
            self.frame.update()

            #This is temporary
            piece_or_wall = 'color' if colororwall in all_colors else colororwall
            row,col = self.get_pos(vx,vy, piece_or_wall)
            self.parent.master.config(cursor = 'hand2')

        return f


    def get_pos(self, x, y, piece_or_wall):
        '''When given a position on the screen x,y returns a row, column on the canvas'''
        where = self.parent.master.grid_location(x,y)
        if where == (0,0):
            #We are on the canvas
            s = self.parent.size
            r = self.parent.size / self.parent.squares
            n = self.parent.squares
            if piece_or_wall in ['color', 'target', 'start', 'blocked', 'atom']:
                col = math.floor(x/r)
                row = n - math.floor(y/r) - 1
                if 0 <= row < n and 0 <= col < n:
                    return (row, col)
            elif piece_or_wall == 'vertical':
                #For vertical walls I take the bottom vertex as row,col
                col = math.floor(x/r+1/2)
                row = n - math.floor(y/r) - 1
                if 0 <= row <= n and 0 <= col <= n:
                    return (row, col)
            elif piece_or_wall == 'horizontal':
                #For horizontal walls I take the left vertex
                col = math.floor(x/r)
                row = n - math.floor(y/r+1/2)
                if 0 <= row <= n and 0 <= col <= n:
                    return (row, col)

        return None,None
        

    def on_drop(self, colororwall):
        '''Drops the canvas'''
        def f(event):
            (vx, vy) = (event.x_root - self.parent.master.winfo_rootx(), event.y_root - self.parent.master.winfo_rooty())
            piece_or_wall = 'color' if colororwall in all_colors else colororwall
            getpos = self.get_pos(vx, vy, piece_or_wall)
            self.floating.place_forget()
            self.floating.delete(self.floating.image)
            self.parent.master.config(cursor = 'arrow')

            if getpos == (None, None):
                return None
            else:
                if piece_or_wall == 'color':
                    #It's a piece
                    self.parent.board.pieces[colororwall].place(*getpos)
                elif piece_or_wall in ['vertical', 'horizontal']:
                    #It's a wall
                    self.parent.board.place_wall(*getpos, colororwall)
                elif piece_or_wall == 'target':
                    self.parent.board.place_target(*getpos)
                elif piece_or_wall == 'atom':
                    self.parent.board.add_atom(*getpos)
                elif piece_or_wall == 'blocked':
                    self.parent.board.add_blocked(*getpos)
                elif piece_or_wall == 'start':
                    self.parent.board.add_start(*getpos)
                self.parent.selected.set('None')
                self.parent.redraw_canvas()

        return f

    def clear(self):
        '''Clears the walls'''
        self.parent.board.walls = []
        self.parent.board.starts = {}
        self.parent.board.atoms = {}
        self.parent.board.blocked = {}
        self.parent.selected.set('None')
        self.parent.redraw_canvas()

    def erase(self):
        '''Erases walls by dragging the mouse on them or by clicking'''
        erasing = self.erasingQ.get()
        self.parent.master.config(cursor = 'X_cursor' if erasing else '')
        #Binds an event to the canvas that keeps track of mouse movement with button pressed
        if erasing:
            self.canvasbinding = self.parent.canvas.bind('<B1-Motion>', self.move_eraser_around)
        else:
            self.parent.canvas.unbind('<B1-Motion>', self.canvasbinding)

    def move_eraser_around(self, event):
        '''A general event for the canvas that makes it possible to bind a <Enter> event to the walls with the mouse down'''
        s = self.parent.size / self.parent.squares
        
        def funct():
            can = self.parent.canvas
            widgets = can.find_overlapping(event.x-s/4,
                                           event.y-s/4,
                                           event.x+s/4,
                                           event.y+s/4)
            for w in widgets:
                for a in self.parent.drawn_walls:
                    if a[0] == w:
                        can.delete(a[0])
                        self.parent.board.walls.remove(a[1])
                        self.parent.selected.set('None')
                        self.parent.redraw_canvas()
                        print('The wall has been erased')
                        break
                for a in self.parent.sprites2:
                    if a['img'] == w and a['obj'] != 'target':
                        can.delete(a['img'])
                        if a['obj'][:4] == 'atom':
                            i = int(a['obj'][4:])
                            del self.parent.board.atoms[i]
                        elif a['obj'][:5] == 'start':
                            i = int(a['obj'][5:])
                            del self.parent.board.starts[i]
                        elif a['obj'][:7] == 'blocked':
                            i = int(a['obj'][7:])
                            del self.parent.board.blocked[i]
                        self.parent.selected.set('None')
                        self.parent.redraw_canvas()
                        print(f"The starting point with id {i} has been erased")
                        break

        if not self.schedule is None:
            self.parent.master.after_cancel(self.schedule)
        self.schedule = self.parent.master.after(1, funct)
