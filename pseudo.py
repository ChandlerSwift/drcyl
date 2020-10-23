class Pill:
    base_value = "a" # bottom left corner
    right_value = "a" # right of the base
    top_value = None # above the base

class GameBoard:
    falling_pill = None
    def get_next_pill(self):
        ...

# State must be one of
#  * waiting for board to settle (falling pills after combo)
#  * Player dropping pill
#  * Board waiting to insert new pill
#  * Player lost

gb = GameBoard()
max_moves = 1000
for move in range(max_moves):
    if gb.falling_pill == None:
        gb.falling_pill = 
