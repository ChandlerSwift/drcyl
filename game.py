import types
from CYLGame import GameLanguage
from CYLGame import GridGame
from CYLGame.Player import DefaultGridPlayer
from CYLGame.Game import ConstMapping
import itertools
from collections import deque
from enum import Enum

class Orientation(Enum):
    VERTICAL = 1
    HORIZONTAL = 2

class DrCYLPlayer(DefaultGridPlayer):
    def __init__(self, prog, bot_consts, sensors):
        super(DrCYLPlayer, self).__init__(prog, bot_consts)
        self.sensor_coords = []
        self.NUM_OF_SENSORS = sensors

    def update_state(self, state):
        super(DrCYLPlayer, self).update_state(state)
        self.sensor_coords = []
        for i in range(self.NUM_OF_SENSORS):
            x_name = "s" + str(i + 1) + "x"
            y_name = "s" + str(i + 1) + "y"
            self.sensor_coords.append((state.get(x_name, "0"), state.get(y_name, "0")))

class DrCYL(GridGame):
    MAP_WIDTH = 8
    MAP_HEIGHT = 16
    SCREEN_WIDTH = MAP_WIDTH + 24
    SCREEN_HEIGHT = MAP_HEIGHT + 8
    MSG_START = 3
    MAX_MSG_LEN = SCREEN_WIDTH - MSG_START - 1
    CHAR_WIDTH = 16
    CHAR_HEIGHT = 16
    GAME_TITLE = "Dr. CYL"
    CHAR_SET = "terminal16x16_gs_ro.png"
    NUM_OF_SENSORS = 8 # TODO
    MAX_TURNS = 100

    PLAYER = '@'
    EMPTY = '\0'

    RED_VIRUS    = 'X'
    YELLOW_VIRUS = 'O'
    BLUE_VIRUS   = 'Z'

    RED_PILL     = 'x'
    YELLOW_PILL  = 'o'
    BLUE_PILL    = 'z'

    CAPSULES = ["".join(p) for p in itertools.product(RED_PILL+YELLOW_PILL+BLUE_PILL, repeat=2)]

    RED_PILL_FACING_RIGHT     = 'a'
    YELLOW_PILL_FACING_RIGHT  = 'e'
    BLUE_PILL_FACING_RIGHT    = 'i'

    RED_PILL_FACING_LEFT     = 'b'
    YELLOW_PILL_FACING_LEFT  = 'f'
    BLUE_PILL_FACING_LEFT    = 'j'

    RED_PILL_FACING_UP     = 'c'
    YELLOW_PILL_FACING_UP  = 'g'
    BLUE_PILL_FACING_UP    = 'k'

    RED_PILL_FACING_DOWN     = 'd'
    YELLOW_PILL_FACING_DOWN  = 'h'
    BLUE_PILL_FACING_DOWN    = ''

    def __init__(self, random):
        self.random = random
        self.running = True
        self.score = 0
        self.turns = 0

        # https://tetris.wiki/Dr._Mario#Capsule_Generation
        # Peek to find the upcoming capsule. Once it's been released, place it
        # onto the tail of the queue. That is:
        #     new_pill = self.capsule_queue.popleft()
        #     self.capsule_queue.append(new_pill)
        self.capsule_queue = deque(self.random.choices(self.CAPSULES, k=128))

        self.level = 20

        """
        self.map[x][x] represents an (x,y) coordinate pair, 0-indexed from the
        bottom left. That is, self.map[3][1] represents the following position:
        2 |         |
        1 |---X     |
        0 |   |     |
          +---------+
           012345678
        """
        self.map = [['\0'] * self.MAP_HEIGHT for i in range(self.MAP_WIDTH)]

        self.current_pill = self.capsule_queue.popleft()
        self.capsule_queue.append(self.current_pill)
        self.current_position = (0,3)
        self.current_orientation = Orientation.HORIZONTAL

    def generate_grid(self, level: int):
        self.viruses_left = 4 * (self.level + 1)
        viruses_to_generate = self.viruses_left

        while viruses_to_generate > 0:
            viruses_to_generate = self.place_virus(viruses_to_generate, level)


    def place_virus(self, remaining_viruses: int, level: int):
        # https://tetris.wiki/Dr._Mario#Virus_Generation
        level = min(level, 19)
        max_row = [10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,11,11,12,12,13][level] - 1 # they were 1-indexed
        y = self.random.randint(0,15)
        while y > max_row:
            y = self.random.randint(0,15)
        x = self.random.randint(0,7)
        color_int = remaining_viruses % 4
        if color_int == 0:
            color = self.YELLOW_VIRUS
        elif color_int == 1:
            color = self.RED_VIRUS
        elif color_int == 2:
            color = self.BLUE_VIRUS
        else:
            color_int = self.random.randint(0,15)
            color = [self.YELLOW_VIRUS, self.RED_VIRUS, self.BLUE_VIRUS, self.BLUE_VIRUS,
                self.RED_VIRUS, self.YELLOW_VIRUS, self.YELLOW_VIRUS, self.RED_VIRUS,
                self.BLUE_VIRUS, self.BLUE_VIRUS, self.RED_VIRUS, self.YELLOW_VIRUS,
                self.YELLOW_VIRUS, self.RED_VIRUS, self.BLUE_VIRUS, self.RED_VIRUS][color_int]
        blocked_on_colors = True
        two_away_cells = []
        while self.map[x][y] != '\0' or blocked_on_colors:
            x += 1
            if x == 8:
                x = 0
                y += 1
            if y > max_row:
                return remaining_viruses

            # Check in all four cardinal directions 2 cells away from the candidate virus position the virus contents of the bottle.
            two_away_cells = []
            two_away_cells.append(self.map[x-2][y] if x >= 2 else ' ')
            two_away_cells.append(self.map[x+2][y] if x <  6 else ' ')
            two_away_cells.append(self.map[x][y-2] if y >= 2 else ' ')
            two_away_cells.append(self.map[x][y+2] if y < 14 else ' ')

            blocked_on_colors = self.RED_VIRUS in two_away_cells and self.YELLOW_VIRUS in two_away_cells and self.BLUE_VIRUS in two_away_cells

        while True:
            if color not in two_away_cells:
                self.map[x][y] = color
                return remaining_viruses - 1

            if color == self.YELLOW_VIRUS:
                color = self.BLUE_VIRUS
            elif color == self.RED_VIRUS:
                color = self.YELLOW_VIRUS
            elif color == self.BLUE_VIRUS:
                color = self.RED_VIRUS

    def init_board(self):
        self.generate_grid(self.level)

    def create_new_player(self, prog):
        self.player = DrCYLPlayer(prog, self.get_move_consts(), self.NUM_OF_SENSORS)
        
        self.update_vars_for_player()
        return self.player

    def start_game(self):
        pass

    def do_turn(self):
        self.do_player_move(self.player.move)
        self.update_vars_for_player()

    def do_player_move(self, key):

        ...
        #self.msg_panel.add(str(key))
        

    def is_running(self):
        return self.running

    def get_map_array_tuple(self):
        map_arr = []
        for w in range(0, self.MAP_WIDTH):
            w_arr = []
            for h in range(0, self.MAP_HEIGHT):
                w_arr.append(ord(self.map[w][h]))
            map_arr.append(tuple(w_arr))

        return tuple(map_arr)

    def update_vars_for_player(self):
        bot_vars = {
            "map_width": self.MAP_WIDTH,
            "map_height": self.MAP_HEIGHT,
            "score": self.score,
            "map_array": self.get_map_array_tuple(),
            "pill_value": self.current_pill,
            "pill_position": self.current_position,
            "pill_orientation": self.current_orientation,
            "VERTICAL": Orientation.VERTICAL,
            "HORIZONTAL": Orientation.HORIZONTAL,
            "next_pill": self.capsule_queue[0],
        }

        self.player.bot_vars = bot_vars

    @staticmethod
    def default_prog_for_bot(language):
        if language == GameLanguage.LITTLEPY:
            return open("bot.lp", "r").read()

    @staticmethod
    def get_intro():
        return open("intro.md", "r").read()

    @staticmethod
    def get_move_consts():
        return ConstMapping({"down": ord("s"),
                            "left": ord("a"),
                            "right": ord("d"),
                            "harddrop": ord("w"),
                            "rotate_ccw": ord("q"),
                            "rotate_cw": ord("e"),
                            })

    @staticmethod
    def get_move_names():
        names = Game.get_move_names()
        names.update({ord("s"): "down"})
        names.update({ord("d"): "right"})
        names.update({ord("a"): "left"})
        names.update({ord("w"): "harddrop"})
        names.update({ord("q"): "rotate_ccw"})
        names.update({ord("e"): "rotate_cw"})
        return names

    def get_score(self):
        return self.score

    def draw_screen(self, frame_buffer):

        grid = f"""                                
                                
     \xD5\xCB\xCD\xCD\xCB\xB8                     
      \xBA  \xBA                      
   \xC9\xCD\xCD\xBC  \xC8\xCD\xCD\xBB                   
   \xBA        \xBA      WELCOME      
   \xBA        \xBA        to         
   \xBA        \xBA      DR CYL!      
   \xBA        \xBA                   
   \xBA        \xBA                   
   \xBA        \xBA   next pill: {self.capsule_queue[0]}   
   \xBA        \xBA                   
   \xBA        \xBA   score: {str(self.score).zfill(6)}   
   \xBA        \xBA                   
   \xBA        \xBA  viruses left: {str(self.viruses_left).zfill(2)} 
   \xBA        \xBA                   
   \xBA        \xBA      level: {str(self.level).zfill(2)}    
   \xBA        \xBA                   
   \xBA        \xBA                   
   \xBA        \xBA                   
   \xBA        \xBA                   
   \xC8\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xBC                  
                                
                                """

        for rowi, row in enumerate(grid.split("\n")):
            for coli, col in enumerate(row):
                frame_buffer.set(coli, rowi, col)

        for coli, col in enumerate(self.map):
            for rowi, row in enumerate(col):
                frame_buffer.set(coli+4, self.MAP_HEIGHT - rowi + 4, row)

        # # End of the game
        # if self.turns >= self.MAX_TURNS:
        #     self.msg_panel.add("You are out of moves.")

        # if not self.running:
        #     self.msg_panel.add("GAME 0VER: Score:" + str(self.score))

        # # Update Status
        # self.status_panel["Score"] = self.score
        # self.status_panel["Move"] = str(self.turns) + " of " + str(self.MAX_TURNS)


if __name__ == '__main__':
    from CYLGame import run
    run(DrCYL)