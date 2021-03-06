import types
from CYLGame import GameLanguage
from CYLGame import GridGame
from CYLGame.Player import DefaultGridPlayer
from CYLGame.Game import ConstMapping
import itertools
from collections import deque
from enum import Enum
import time

PERF_DEBUG = False

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

    RED_VIRUS    = '\x01'
    YELLOW_VIRUS = '\x02'
    BLUE_VIRUS   = '\x03'

    RED_PILL     = '\x11'
    YELLOW_PILL  = '\x12'
    BLUE_PILL    = '\x13'

    CAPSULES = ["".join(p) for p in itertools.product(RED_PILL+YELLOW_PILL+BLUE_PILL, repeat=2)]

    RED_PILL_FACING_RIGHT     = '\x04'
    YELLOW_PILL_FACING_RIGHT  = '\x05'
    BLUE_PILL_FACING_RIGHT    = '\x06'

    RED_PILL_FACING_LEFT     = '\x07'
    YELLOW_PILL_FACING_LEFT  = '\x08'
    BLUE_PILL_FACING_LEFT    = '\x09'

    RED_PILL_FACING_UP     = '\x14'
    YELLOW_PILL_FACING_UP  = '\x15'
    BLUE_PILL_FACING_UP    = '\x16'

    RED_PILL_FACING_DOWN     = '\x17'
    YELLOW_PILL_FACING_DOWN  = '\x18'
    BLUE_PILL_FACING_DOWN    = '\x19'

    RED_PLACEHOLDER = '\xF0'
    YELLOW_PLACEHOLDER = '\xF1'
    BLUE_PLACEHOLDER = '\xF2'

    # TODO: this is the dumbest possible way to do this, but I can't think
    # of a better way at the moment, and this seems to work.
    PILLS = {
        "BLUE": {
            "single": BLUE_PILL,
            "up": BLUE_PILL_FACING_UP,
            "down": BLUE_PILL_FACING_DOWN,
            "left": BLUE_PILL_FACING_LEFT,
            "right": BLUE_PILL_FACING_RIGHT,
            "placeholder": BLUE_PLACEHOLDER,
        },
        "YELLOW": {
            "single": YELLOW_PILL,
            "up": YELLOW_PILL_FACING_UP,
            "down": YELLOW_PILL_FACING_DOWN,
            "left": YELLOW_PILL_FACING_LEFT,
            "right": YELLOW_PILL_FACING_RIGHT,
            "placeholder": YELLOW_PLACEHOLDER,
        },
        "RED": {
            "single": RED_PILL,
            "up": RED_PILL_FACING_UP,
            "down": RED_PILL_FACING_DOWN,
            "left": RED_PILL_FACING_LEFT,
            "right": RED_PILL_FACING_RIGHT,
            "placeholder": RED_PLACEHOLDER,
        }
    }

    PLACEHOLDERS = [
        RED_PLACEHOLDER,
        YELLOW_PLACEHOLDER,
        BLUE_PLACEHOLDER,
    ]

    def color(self, s: str):
        if s in [self.RED_VIRUS, self.RED_PILL, self.RED_PILL_FACING_UP, self.RED_PILL_FACING_DOWN, self.RED_PILL_FACING_LEFT, self.RED_PILL_FACING_RIGHT, self.RED_PLACEHOLDER]:
            return "RED"
        if s in [self.YELLOW_VIRUS, self.YELLOW_PILL, self.YELLOW_PILL_FACING_UP, self.YELLOW_PILL_FACING_DOWN, self.YELLOW_PILL_FACING_LEFT, self.YELLOW_PILL_FACING_RIGHT, self.YELLOW_PLACEHOLDER]:
            return "YELLOW"
        if s in [self.BLUE_VIRUS, self.BLUE_PILL, self.BLUE_PILL_FACING_UP, self.BLUE_PILL_FACING_DOWN, self.BLUE_PILL_FACING_LEFT, self.BLUE_PILL_FACING_RIGHT, self.BLUE_PLACEHOLDER]:
            return "BLUE"

    VERTICAL = 0
    HORIZONTAL = 1

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

        self.level = 1

        """
        self.map[x][x] represents an (x,y) coordinate pair, 0-indexed from the
        bottom left. That is, self.map[3][1] represents the following position:
        2 |         |
        1 |---X     |
        0 |   |     |
          +---------+
           012345678
        """
        self.map = [[self.EMPTY] * self.MAP_HEIGHT for i in range(self.MAP_WIDTH)]

        self.current_pill = self.capsule_queue.popleft()
        self.capsule_queue.append(self.current_pill)

        # current_position represents the position of the bottom left square.
        # That is, if the domino is vertical, it's the lower of two positions
        # occupied; if it is horizontal, it's the leftmost of the two positions.
        self.current_position = [3,15]
        self.current_orientation = self.HORIZONTAL
        self.fix_pill()

        self.pills_changed_last_turn = False
        self.can_move = True

        self.viruses_removed_since_last_action = 0

    def fix_pill(self):
        current_pill = self.current_pill
        if self.current_orientation == self.VERTICAL:
            first = self.PILLS[self.color(current_pill[0])]["up"]
            second = self.PILLS[self.color(current_pill[1])]["down"]
        else:
            first = self.PILLS[self.color(current_pill[0])]["right"]
            second = self.PILLS[self.color(current_pill[1])]["left"]
        self.current_pill = first + second

    def generate_grid(self, level: int):
        self.viruses_left = 4 * (min(level, 23) + 1)
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
        while self.map[x][y] != self.EMPTY or blocked_on_colors:
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
        self.turns += 1
        if self.turns > self.MAX_TURNS:
            self.running = False
            return
        if self.viruses_left == 0: # generate new level
            self.level += 1
            self.map = [[self.EMPTY] * self.MAP_HEIGHT for i in range(self.MAP_WIDTH)]
            self.generate_grid(self.level)
        elif self.pills_fall(dry_run=True): # TODO: optimize: only if pills changed last turn
            self.pills_fall()
        elif self.remove_pills(dry_run=True): # TODO: optimize: only if pills changed last turn
            self.remove_pills()
        elif not self.current_pill: # need a new pill
            self.viruses_removed_since_last_action = 0
            if self.map[3][15] == self.EMPTY and self.map[4][15] == self.EMPTY:
                self.current_pill = self.capsule_queue.popleft()
                self.capsule_queue.append(self.current_pill)
                self.current_position = [3,15]
                self.current_orientation = self.HORIZONTAL
                self.fix_pill()
            else:
                self.running = False
                return
        else:
            self.do_player_move(self.player.move)

        self.can_move = not self.pills_fall(dry_run=True) and not self.remove_pills(dry_run=True) # TODO: optimize: only if pills changed last turn

        self.update_vars_for_player()

    def remove_pills(self, dry_run=False) -> bool: # TODO: break pairs
        # In order to enable multiple rows facing different directions, we use
        # a two-pass method. The first pass removes n-in-a-row sequences and
        # replaces them with placeholders that retain the current color, which
        # allows the pills to get caught up in a second sequence later in the
        # first sweep. The second pass removes those placeholders.
        #
        # As an example, consider the following grid. If an O is added in the
        # top left corner, it will complete both the leftmost column and the
        # top row.
        # _ O O O
        # O X X X
        # O X X X
        # O X X X
        # Naïvely, if we remove the column first:
        #   O O O
        #   X X X
        #   X X X
        #   X X X
        # we lose the four-in-a-row that we need to remove the top row. However,
        # if in the first pass we retain color using a placeholder (say, a
        # lowercase value), we can still consider it in other sequences.
        #
        # The final pass simply removes all of the placeholders.
        # O O O O    o O O O    o o o o    _ _ _ _
        # O X X X    o X X X    o X X X    _ X X X
        # O X X X => o X X X => o X X X => _ X X X
        # O X X X    o X X X    o X X X    _ X X X

        facing_up = [self.RED_PILL_FACING_UP, self.YELLOW_PILL_FACING_UP, self.BLUE_PILL_FACING_UP]
        facing_right = [self.RED_PILL_FACING_RIGHT, self.YELLOW_PILL_FACING_RIGHT, self.BLUE_PILL_FACING_RIGHT]
        facing_down = [self.RED_PILL_FACING_DOWN, self.YELLOW_PILL_FACING_DOWN, self.BLUE_PILL_FACING_DOWN]
        facing_left = [self.RED_PILL_FACING_LEFT, self.YELLOW_PILL_FACING_LEFT, self.BLUE_PILL_FACING_LEFT]
        removed_pills = False
        def is_virus(s: str) -> bool:
            return s in [self.RED_VIRUS, self.YELLOW_VIRUS, self.BLUE_VIRUS]
        viruses_removed = 0
        for x in range(self.MAP_WIDTH):
            for y in range(self.MAP_HEIGHT):
                if y < 13 and self.color(self.map[x][y]) == self.color(self.map[x][y+1]) == self.color(self.map[x][y+2]) == self.color(self.map[x][y+3]) != None:
                    # columns
                    removed_pills = True
                    if not dry_run:
                        current_color = self.color(self.map[x][y])
                        current_y = y
                        while current_y < self.MAP_HEIGHT and self.color(self.map[x][current_y]) == current_color:
                            if is_virus(self.map[x][current_y]):
                                viruses_removed += 1
                            if self.map[x][current_y] in facing_left: # attached to left
                                self.map[x - 1][current_y] = self.PILLS[self.color(self.map[x - 1][current_y])]["single"] # break pair
                            elif self.map[x][current_y] in facing_right: # attached to right
                                self.map[x + 1][current_y] = self.PILLS[self.color(self.map[x + 1][current_y])]["single"] # break pair
                            elif self.map[x][current_y] in facing_up: # attached above
                                self.map[x][current_y + 1] = self.PILLS[self.color(self.map[x][current_y + 1])]["single"] # break pair
                            elif self.map[x][current_y] in facing_down: # attached to below
                                self.map[x][current_y - 1] = self.PILLS[self.color(self.map[x][current_y - 1])]["single"] # break pair
                            self.map[x][current_y] = self.PILLS[self.color(self.map[x][current_y])]["placeholder"]
                            current_y += 1
                if x < 5 and self.color(self.map[x][y]) == self.color(self.map[x+1][y]) == self.color(self.map[x+2][y]) == self.color(self.map[x+3][y]) != None:
                    # rows
                    removed_pills = True
                    if not dry_run:
                        current_color = self.color(self.map[x][y])
                        current_x = x
                        while current_x < self.MAP_WIDTH and self.color(self.map[current_x][y]) == current_color:
                            if is_virus(self.map[current_x][y]):
                                viruses_removed += 1
                            if self.map[current_x][y] in facing_left: # attached to left
                                self.map[current_x - 1][y] = self.PILLS[self.color(self.map[current_x - 1][y])]["single"] # break pair
                            elif self.map[current_x][y] in facing_right: # attached to right
                                self.map[current_x + 1][y] = self.PILLS[self.color(self.map[current_x + 1][y])]["single"] # break pair
                            elif self.map[current_x][y] in facing_up: # attached above
                                self.map[current_x][y + 1] = self.PILLS[self.color(self.map[current_x][y + 1])]["single"] # break pair
                            elif self.map[current_x][y] in facing_down: # attached to below
                                self.map[current_x][y - 1] = self.PILLS[self.color(self.map[current_x][y - 1])]["single"] # break pair
                            self.map[current_x][y] = self.PILLS[self.color(self.map[current_x][y])]["placeholder"]
                            current_x += 1

        # Clear placeholders
        for x in range(self.MAP_WIDTH):
            for y in range(self.MAP_HEIGHT):
                if self.map[x][y] in self.PLACEHOLDERS:
                    self.map[x][y] = self.EMPTY

        self.viruses_left -= viruses_removed
        for _ in range(viruses_removed):
            # This is the score that would be used in medium speed in the original
            # game. Low would base off an initial score of 100, and High would
            # scale from 300.
            self.score += 200 * 2 ** min(self.viruses_removed_since_last_action, 5)
            self.viruses_removed_since_last_action += 1
        return removed_pills

    def pills_fall(self, dry_run=False) -> bool:
        pills_fell = False
        single = [self.RED_PILL, self.YELLOW_PILL, self.BLUE_PILL]
        facing_up = [self.RED_PILL_FACING_UP, self.YELLOW_PILL_FACING_UP, self.BLUE_PILL_FACING_UP]
        facing_right = [self.RED_PILL_FACING_RIGHT, self.YELLOW_PILL_FACING_RIGHT, self.BLUE_PILL_FACING_RIGHT]
        for x in range(self.MAP_WIDTH):
            for y in range(1, self.MAP_HEIGHT):
                if self.map[x][y] in single and self.map[x][y-1] == self.EMPTY:
                    if not dry_run:
                        self.map[x][y-1] = self.map[x][y]
                        self.map[x][y] = self.EMPTY
                    pills_fell = True
                if self.map[x][y] in facing_up and self.map[x][y-1] == self.EMPTY:
                    if not dry_run:
                        self.map[x][y-1] = self.map[x][y]
                        self.map[x][y] = self.map[x][y+1]
                        self.map[x][y+1] = self.EMPTY
                    pills_fell = True
                if self.map[x][y] in facing_right and self.map[x][y - 1] == self.EMPTY and self.map[x+1][y-1] == self.EMPTY:
                    if not dry_run:
                        self.map[x][y-1] = self.map[x][y]
                        self.map[x+1][y-1] = self.map[x+1][y]
                        self.map[x][y] = self.map[x+1][y] = self.EMPTY
                    pills_fell = True
        return pills_fell

    def do_player_move(self, key):
        pill_fixed_in_place = False
        if key == "s": # down
            fix_pill_in_place = False
            if self.current_orientation == self.VERTICAL:
                if self.current_position[1] > 0 and self.map[self.current_position[0]][self.current_position[1] - 1] == self.EMPTY: # Free space to move down
                    self.current_position[1] -= 1
                else:
                    if self.current_position[1] < 15: # not on the top row
                        self.map[self.current_position[0]][self.current_position[1] + 1] = self.current_pill[1]
                        self.map[self.current_position[0]][self.current_position[1]] = self.current_pill[0]
                    else:
                        self.map[self.current_position[0]][self.current_position[1]] = self.PILLS[self.color(self.current_pill[0])]["single"]
                    pill_fixed_in_place = True
            else: # horizontal
                if (self.current_position[1] > 0 and
                        self.map[self.current_position[0]][self.current_position[1] - 1] == self.EMPTY and
                        self.map[self.current_position[0] + 1][self.current_position[1] - 1] == self.EMPTY): # Free space to move down
                    self.current_position[1] -= 1
                else:
                    self.map[self.current_position[0]][self.current_position[1]] = self.current_pill[0]
                    self.map[self.current_position[0] + 1][self.current_position[1]] = self.current_pill [1]
                    pill_fixed_in_place = True
        elif key == "d": # right
            if self.current_orientation == self.HORIZONTAL:
                if self.current_position[0] < 6 and self.map[self.current_position[0] + 2][self.current_position[1]] == self.EMPTY: # Free space to move right
                    self.current_position[0] += 1
            else: # vertical
                if (self.current_position[0] < 7 and
                        (self.current_position[1] == 15 or self.map[self.current_position[0] + 1][self.current_position[1] + 1] == self.EMPTY) and # don't check the top if we're above the map
                        self.map[self.current_position[0] + 1][self.current_position[1]] == self.EMPTY): # Free space to move right
                    self.current_position[0] += 1
        elif key == "a": # left
            if self.current_orientation == self.HORIZONTAL:
                if self.current_position[0] > 0 and self.map[self.current_position[0] - 1][self.current_position[1]] == self.EMPTY: # Free space to move left
                    self.current_position[0] -= 1
            else: # vertical
                if (self.current_position[0] > 0 and
                        (self.current_position[1] == 15 or self.map[self.current_position[0] - 1][self.current_position[1] + 1] == self.EMPTY) and
                        self.map[self.current_position[0] - 1][self.current_position[1]] == self.EMPTY): # Free space to move left
                    self.current_position[0] -= 1
        elif key == "w": # harddrop
            # when y increases, we know we've moved on to a new capsule.
            current_y = self.current_position[1]
            self.do_player_move("s") # just use the down move we've already made
            still_dropping = self.running and self.current_position[1] < current_y
            current_y = self.current_position[1]
            while still_dropping:
                self.do_player_move("s") # just use the down move we've already made
                still_dropping = self.running and self.current_position[1] < current_y
                current_y = self.current_position[1]
        # Rotations: taken from https://harddrop.com/wiki/Dr._Mario
        elif key == "q": # rotate_ccw
            if self.current_orientation == self.HORIZONTAL:
                # if we're on the top, we can always rotate counterclockwise; the rightmost simply flips above the leftmost.
                if self.current_position[1] == 15 or self.map[self.current_position[0]][self.current_position[1] + 1] == self.EMPTY:
                    self.current_orientation = self.VERTICAL
            else: # vertical
                if self.current_position[0] < 7 and self.map[self.current_position[0] + 1][self.current_position[1]] == self.EMPTY:
                    self.current_orientation = self.HORIZONTAL
                    self.current_pill = self.current_pill[1] + self.current_pill[0]
                elif self.current_position[0] > 0 and self.map[self.current_position[0] - 1][self.current_position[1]] == self.EMPTY: # can kick left
                    self.current_orientation = self.HORIZONTAL
                    self.current_pill = self.current_pill[1] + self.current_pill[0]
                    self.current_position[0] -= 1
        elif key == "e": # rotate_cw
            if self.current_orientation == self.HORIZONTAL:
                # if we're on the top, we can always rotate counterclockwise; the rightmost simply flips above the leftmost.
                if self.current_position[1] == 15 or self.map[self.current_position[0]][self.current_position[1] + 1] == self.EMPTY:
                    self.current_pill = self.current_pill[1] + self.current_pill[0]
                    self.current_orientation = self.VERTICAL
            else: # vertical
                if self.current_position[0] < 7 and self.map[self.current_position[0] + 1][self.current_position[1]] == self.EMPTY:
                    self.current_orientation = self.HORIZONTAL
                elif self.current_position[0] > 0 and self.map[self.current_position[0] - 1][self.current_position[1]] == self.EMPTY: # can kick left
                    self.current_orientation = self.HORIZONTAL
                    self.current_position[0] -= 1
                    self.current_orientation = self.HORIZONTAL
        else:
            pass
            # raise KeyError

        if self.current_pill is not None:
            self.fix_pill()

        if pill_fixed_in_place:
            self.pills_changed_last_turn = True

            pills_will_be_removed_next_turn = self.remove_pills(dry_run=True)
            if not pills_will_be_removed_next_turn:
                pills_will_fall_next_turn = self.pills_fall(dry_run=True)
            self.can_move = not pills_will_be_removed_next_turn and not pills_will_fall_next_turn

            self.current_pill = None

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
            "vertical": self.VERTICAL,
            "horizontal": self.HORIZONTAL,
            "next_pill": self.capsule_queue[0],
            "can_move": self.can_move
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

        next_pill = self.PILLS[self.color(self.capsule_queue[0][0])]["right"] +  self.PILLS[self.color(self.capsule_queue[0][1])]["left"]

        grid = f"""                                
                                
     \xD5\xCB\xCD\xCD\xCB\xB8                     
      \xBA  \xBA                      
   \xC9\xCD\xCD\xBC  \xC8\xCD\xCD\xBB                   
   \xBA        \xBA      WELCOME      
   \xBA        \xBA        to         
   \xBA        \xBA      DR CYL!      
   \xBA        \xBA                   
   \xBA        \xBA                   
   \xBA        \xBA   next pill: {next_pill}   
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
  {"                           " if self.can_move else "WAITING FOR BOARD TO SETTLE"}   
                                """

        # Draw frame
        for rowi, row in enumerate(grid.split("\n")):
            for coli, col in enumerate(row):
                frame_buffer.set(coli, rowi, col)

        # Draw bottle
        for coli, col in enumerate(self.map):
            for rowi, row in enumerate(col):
                frame_buffer.set(coli+4, self.MAP_HEIGHT - rowi + 4, row)

        # Draw currently falling pill
        if self.current_pill:
            frame_buffer.set(self.current_position[0] + 4, self.MAP_HEIGHT - self.current_position[1] + 4, self.current_pill[0])
            if self.current_orientation == self.HORIZONTAL:
                frame_buffer.set(self.current_position[0] + 1 + 4, self.MAP_HEIGHT - self.current_position[1] + 4, self.current_pill[1])
            else: # self.current_orientation = self.VERTICAL
                frame_buffer.set(self.current_position[0] + 4, self.MAP_HEIGHT - (self.current_position[1] + 1) + 4, self.current_pill[1])

        if not self.running:
            lose_str = f"Good game! Your score: {self.score}"
            left_offset = ((self.SCREEN_WIDTH - len(lose_str)) // 2)
            frame_buffer.set(left_offset - 1, self.SCREEN_HEIGHT // 2 - 1, "\xC9")
            frame_buffer.set(left_offset - 1, self.SCREEN_HEIGHT // 2, "\xBA")
            frame_buffer.set(left_offset - 1, self.SCREEN_HEIGHT // 2 + 1, "\xC8")
            for i, c in enumerate(lose_str):
                frame_buffer.set(left_offset + i, self.SCREEN_HEIGHT // 2 + 1, "\xCD")
                frame_buffer.set(left_offset + i, self.SCREEN_HEIGHT // 2, c)
                frame_buffer.set(left_offset + i, self.SCREEN_HEIGHT // 2 - 1, "\xCD")
            frame_buffer.set(left_offset + len(lose_str), self.SCREEN_HEIGHT // 2 - 1, "\xBB")
            frame_buffer.set(left_offset + len(lose_str), self.SCREEN_HEIGHT // 2, "\xBA")
            frame_buffer.set(left_offset + len(lose_str), self.SCREEN_HEIGHT // 2 + 1, "\xBC")


if __name__ == '__main__':
    from CYLGame import run
    run(DrCYL)
