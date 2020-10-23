import random

import pytest
import sys

from littlepython import Compiler

from CYLGame import GameLanguage, GameRunner
from CYLGame.Player import Room

from game import Ski as Game


def get_fuzzing_seeds(new_seed_count=10):
    previous_bad_seeds = []
    return previous_bad_seeds + [random.randint(0, sys.maxsize) for _ in range(new_seed_count)]


@pytest.mark.parametrize("seed", get_fuzzing_seeds())
def test_run_for_playback(seed):
    # Make default player bot
    compiler = Compiler()
    bot = Game.default_prog_for_bot(GameLanguage.LITTLEPY)
    prog = compiler.compile(bot)
    room = Room([prog], seed=seed)

    runner = GameRunner(Game)
    runner.run(room, playback=True)


@pytest.mark.parametrize("seed", get_fuzzing_seeds())
def test_run_for_score(seed):
    # Make default player bot
    compiler = Compiler()
    bot = Game.default_prog_for_bot(GameLanguage.LITTLEPY)
    prog = compiler.compile(bot)
    room = Room([prog], seed=seed)

    runner = GameRunner(Game)
    runner.run(room, playback=False)

