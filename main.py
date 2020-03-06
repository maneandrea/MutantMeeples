#!/usr/bin/env python3

from meeplesGUI import *
from meeples import *

def main():
    B = Board()
    master = Tk()
    dis = GUI(B, master)

    master.update()
    master.mainloop()

if __name__ == "__main__":
    main()