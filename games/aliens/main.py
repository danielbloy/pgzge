import os
from typing import Any

os.environ['SDL_VIDEO_WINDOW_POS'] = f'700,100'

import pgzrun
from pgzge.core import draw_game, update_game, add_game_object, GameObject
from pgzero.clock import Clock
from pgzero.keyboard import Keyboard
from pgzero.screen import Screen
from random import randint

clock: Clock
screen: Screen
keyboard: Keyboard

WIDTH = 600
HEIGHT = 700

BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)

STARS_MIN_SPEED = 75
STARS_MAX_SPEED = 150
STARS_TOTAL = 200


def create_starfield(n) -> GameObject:
    def starfield_activate(obj):
        obj.n = n
        obj.stars = [
            (
                randint(0, WIDTH),  # x position
                randint(0, HEIGHT),  # y position
                randint(STARS_MIN_SPEED, STARS_MAX_SPEED)  # speed
            )
            for _ in range(obj.n)
        ]

    def starfield_draw(obj, surface: Any):
        for star in obj.stars:
            screen.draw.filled_circle((star[0], star[1]), 1, WHITE)

    def starfield_update(obj, dt: float):
        # STEP A: Move stars down the screen
        obj.stars = [
            (
                star[0],  # x position
                star[1] + (star[2] * dt),  # y position
                star[2]  # speed
            )
            for star in obj.stars
        ]

        # STEP B: Remove stars that have moved off the bottom of the screen
        obj.stars = [
            (
                star[0],
                star[1],
                star[2]
            )
            for star in obj.stars
            if star[1] < HEIGHT
        ]

        # STEP C: Add new stars at the top to maintain the total number of stars
        for _ in range(obj.n - len(obj.stars)):
            obj.stars.append(
                (
                    randint(0, WIDTH),  # x position
                    0,  # y position - top of screen
                    randint(STARS_MIN_SPEED, STARS_MAX_SPEED)  # speed
                )
            )

    game_object = GameObject(
        activate_handler=starfield_activate,
        draw_handler=starfield_draw,
        update_handler=starfield_update)
    add_game_object(game_object)
    return game_object


starfield = create_starfield(STARS_TOTAL)


def draw():
    draw_game(screen.surface)


def update(dt):
    update_game(dt)


pgzrun.go()
