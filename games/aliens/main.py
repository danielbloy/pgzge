import os

from pgzge.core import draw_game, update_game, add_game_object, GameObject

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
    draw_game(screen)


update_funcs = []


def update(dt):
    update_game(dt)


BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)

STARS_MIN_SPEED = 75
STARS_MAX_SPEED = 150
STARS_TOTAL = 200

from random import randint


def starfield_activate(self):
    self.n = STARS_TOTAL
    self.stars = [
        (
            randint(0, WIDTH),  # x position
            randint(0, HEIGHT),  # y position
            randint(STARS_MIN_SPEED, STARS_MAX_SPEED)  # speed
        )
        for _ in range(STARS_TOTAL)
    ]


def starfield_draw(self, screen: Screen):
    for star in self.stars:
        screen.draw.filled_circle((star[0], star[1]), 1, WHITE)


def starfield_update(self, dt: float):
    # STEP A: Move stars down the screen
    self.stars = [
        (
            star[0],  # x position
            star[1] + (star[2] * dt),  # y position
            star[2]  # speed
        )
        for star in self.stars
    ]

    # STEP B: Remove stars that have moved off the bottom of the screen
    self.stars = [
        (
            star[0],
            star[1],
            star[2]
        )
        for star in self.stars
        if star[1] < HEIGHT
    ]

    # STEP C: Add new stars at the top to maintain the total number of stars
    for _ in range(self.n - len(self.stars)):
        self.stars.append(
            (
                randint(0, WIDTH),  # x position
                0,  # y position - top of screen
                randint(STARS_MIN_SPEED, STARS_MAX_SPEED)  # speed
            )
        )


starfield = GameObject(activate_handler=starfield_activate,
                       draw_handler=starfield_draw,
                       update_handler=starfield_update)
add_game_object(starfield)

pgzrun.go()
