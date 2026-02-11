import os

os.environ['SDL_VIDEO_WINDOW_POS'] = f'700,100'

import pgzrun
from pgzero.clock import Clock
from pgzero.keyboard import Keyboard
from pgzero.screen import Screen

screen: Screen
keyboard: Keyboard
clock: Clock

WIDTH = 600
HEIGHT = 700


def draw():
    pass


update_funcs = []


def update(dt):
    pass


pgzrun.go()