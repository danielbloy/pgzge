import sys

import pygame
# noinspection PyUnresolvedReferences
from pgzero.loaders import images
# noinspection PyUnresolvedReferences
from pgzero.screen import Screen
from pygame import Surface

from pmpge.game import Game
from pmpge.game_object import draw_hierarchy

game: Game | None = None
scale_surface: Surface | None = None

screen_width: int = 0
screen_height: int = 0

background_colour: tuple[int, int, int] = (0, 0, 0)

mod = sys.modules['__main__']


def init(g: Game, sw: int, sh: int, bgc: tuple[int, int, int]):
    """
    This sets up the game to run at the desired resolution in a python/pygame zero
    environment. If the games specified width or height is smaller than the provided
    screen dimensions, then the image will be scaled. If the games specified width or
    height is larger than the provided screen dimensions, then the game is scaled
    horizontally, vertically or both.

    This function also injects WIDTH, HEIGHT variables into the main application to
    hook into pygame zero. This will overwrite those values if they are set in the
    main Python file.
    """
    global game, screen_width, screen_height, background_colour, scale_surface
    game = g

    width, height = g.width, g.height
    screen_width, screen_height = sw, sh
    background_colour = bgc

    if width > screen_width:
        screen_width = width

    if height > screen_height:
        screen_height = height

    setattr(mod, 'WIDTH', screen_width)
    setattr(mod, 'HEIGHT', screen_height)

    if width < screen_width or height < screen_height:
        scale_surface = pygame.Surface((width, height))


def deinit():
    global game, scale_surface
    game = None
    scale_surface = None


def draw(screen: Screen):
    """
    Performs any scaling that is required.
    """
    screen.fill(background_colour)

    # noinspection PyUnresolvedReferences
    draw_hierarchy(game.root, screen)
    # noinspection PyUnresolvedReferences
    game.draw(screen)

    if scale_surface:
        scale_surface.blit(screen.surface, (0, 0))
        pygame.transform.scale(
            scale_surface,
            (screen_width, screen_height), screen.surface)  # noqa: F821


def game_object_hierarchy_changed():
    """
    Mandatory function that does nothing in the Pygame Zero.
    """
    pass


class DriverImageResource:
    """
    Implementation specific class to load an image resource. The only mandatory
    method is load(). This class is designed to be combined with `ImageResource`.
    """
    surface: Surface

    def __init__(self, hint_requires_transparency: bool):
        pass

    def load(self, image: str) -> tuple[int, int]:
        """
        Loads the named image resource, returning the width and height.
        """
        surface = images.load(image)
        self.surface = surface
        return self.surface.get_width(), self.surface.get_height()


class GraphicsDrawImageTrait:
    """
    This class is designed to be combined with a `DrawImage` trait.
    """
    x: int
    y: int

    image: DriverImageResource

    def draw(self, surface: Surface):
        """
        Draws the image at the specified position, offset from the GameObjects position.
        """
        image = self.image
        # noinspection PyUnresolvedReferences
        surface.blit(image.surface, (self.x - image.offset_x, self.y - image.offset_y))
