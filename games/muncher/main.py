import os

os.environ['SDL_VIDEO_WINDOW_POS'] = f'700,100'

import pgzrun
from pgzge.core import draw_game, update_game
from pgzero.clock import Clock
from pgzero.keyboard import Keyboard
from pgzero.screen import Screen

screen: Screen
keyboard: Keyboard
clock: Clock

WIDTH = 600
HEIGHT = 700


def draw():
    draw_game(screen.surface)


def update(dt):
    update_game(dt)


pgzrun.go()