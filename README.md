Mutant Meeples
---

This is a solver for the Mutant Meeples game with a tkinter GUI.   
It is written in Python 3 (specifically 3.6.8).

Tkinter should be built in, but if it's not there:

- On Linux do

`sudo apt-get install python3-tk`

- On Windows follow the steps in [here](https://tkdocs.com/tutorial/install.html)

It also makes use of the PIL library for dealing with pictures.

For instructions on how to use it read the initial message at startup.

### Done
- Graphical interface that allows the user to place the target, the starting points and the Meeples on the board
- Commands for moving the Meeples
- A function that returns all possible moves of a given Meeples (*not* taking into account the special powers)
- Solving algorithm without Meeple powers
- Animation after a solution
- Used threading to allow the user to stop a solution that takes too long (checks for signals every 25000 moves)
- Used [pickle](https://docs.python.org/2/library/pickle.html) module to save and load the board data as binary files

### To do
- Add the special powers of each single Meeple
- Add a way to disable Meeples
- Maybe change the icons
- A GUI way to change the size and the number of squares on the board (now they are parameters of the GUI class)
- A way to turn on and off the animation (now it's hardcoded)
- Use threading or [multiprocessing](https://docs.python.org/3.6/library/multiprocessing.html) to parallelize stuff?
