#!/usr/bin/env python3

import itertools
import random

board = """                                
      ====                      
      |  |                      
   +--+  +--+                   
   |        |      WELCOME      
   |        |        to         
   |        |      DR CYL!      
   |        |                   
   |        |                   
   |        |   next pill: --   
   |        |                   
   |        |   score: ------   
   |        |                   
   |        |  viruses left: -- 
   |        |                   
   |        |      level: --    
   |        |                   
   |        |                   
   |        |                   
   |        |                   
   +--------+                   
"""

RED_VIRUS    = 'X'
YELLOW_VIRUS = 'O'
BLUE_VIRUS   = 'Z'

RED_PILL     = 'x'
YELLOW_PILL  = 'o'
BLUE_PILL    = 'z'

CAPSULES = list(itertools.product('xoz', repeat=2))

def setchar(x, y, char):
    global board
    before = 33*y + x
    board = board[:before] + char + board[before+1:]

def getchar(x,y):
    return board[33*y + x]

row = [' '] * 8
game_grid = []
for i in range(16):
    game_grid.append(row.copy())

def generate_grid(level: int):
    level = min(level, 20)
    level = max(level, 1)
    remaining_viruses = 4 * (level + 1)

    setchar(29,13,str(remaining_viruses).zfill(2)[0])
    setchar(30,13,str(remaining_viruses).zfill(2)[1])
    while remaining_viruses > 0:
        remaining_viruses = place_virus(remaining_viruses, level, game_grid)

    for rowi, row in enumerate(game_grid):
        for coli, col in enumerate(row):
            setchar(coli + 4, (15 - rowi) + 4, col)


def place_virus(remaining_viruses, level, game_grid):
    # https://tetris.wiki/Dr._Mario#Virus_Generation
    level = min(level, 19)
    max_row = [10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,11,11,12,12,13][level] - 1
    y = random.randint(0,15)
    while y > max_row:
        y = random.randint(0,15)
    x = random.randint(0,7)
    color_int = remaining_viruses % 4
    if color_int == 0:
        color = YELLOW_VIRUS
    elif color_int == 1:
        color = RED_VIRUS
    elif color_int == 3:
        color = BLUE_VIRUS
    else:
        color_int = random.randint(0,15)
        color = [YELLOW_VIRUS, RED_VIRUS, BLUE_VIRUS, BLUE_VIRUS,
            RED_VIRUS, YELLOW_VIRUS, YELLOW_VIRUS, RED_VIRUS,
            BLUE_VIRUS, BLUE_VIRUS, RED_VIRUS, YELLOW_VIRUS,
            YELLOW_VIRUS, RED_VIRUS, BLUE_VIRUS, RED_VIRUS][color_int]
    blocked_on_colors = True
    two_away_cells = []
    while game_grid[y][x] != ' ' or blocked_on_colors:
        x += 1
        if x == 8:
            x = 0
            y += 1
        if y == 16:
            return remaining_viruses

        # Check in all four cardinal directions 2 cells away from the candidate virus position the virus contents of the bottle.
        two_away_cells = []
        two_away_cells.append(game_grid[y][x-2] if x >= 2 else ' ')
        two_away_cells.append(game_grid[y][x+2] if x <  6 else ' ')
        two_away_cells.append(game_grid[y-2][x] if y >= 2 else ' ')
        two_away_cells.append(game_grid[y+2][x] if y < 14 else ' ')

        blocked_on_colors = RED_VIRUS in two_away_cells and YELLOW_VIRUS in two_away_cells and BLUE_VIRUS in two_away_cells

    while True:
        if color not in two_away_cells:
            game_grid[y][x] = color
            return remaining_viruses - 1

        if color == YELLOW_VIRUS:
            color = BLUE_VIRUS
        elif color == RED_VIRUS:
            color = YELLOW_VIRUS
        elif color == BLUE_VIRUS:
            color = RED_VIRUS

level = input("level: ").zfill(2)
generate_grid(int(level))
height = 15
while getchar(7,20-height) == ' ' and getchar(8,20 - height) == ' ':
    height -= 1

setchar(26,15,level[0])
setchar(27,15,level[1])

while True:
    # clear screen
    print(chr(27) + "[2J")

    pill = random.choice(CAPSULES)
    setchar(27,9,pill[0])
    setchar(28,9,pill[1])

    print(board)
    
    move = input("> ")
    if move != "":
        eval(move)

    setchar(7,19-height, pill[0])
    setchar(8,19-height, pill[1])
    height += 1

    if height > 16:
        print("you lose!")
        break
