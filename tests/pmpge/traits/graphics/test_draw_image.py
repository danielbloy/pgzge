from pygments.lexers import go

import pmpge.environment as environment
from pmpge.game import Game
from pmpge.game_object import GameObject, update_hierarchy
from pmpge.traits.graphics import DrawImage
from pmpge.traits.position import Position
from tests.pmpge.testing_utilities import setup_pgzero


# noinspection PyUnresolvedReferences
def test_constructor():
    """
    Simple test to ensure that DrawImage works.
    """
    setup_pgzero(__file__)
    trait = DrawImage("7x3.png")
    assert trait.image.surface is not None
    assert trait.image.offset_x == 3
    assert trait.image.offset_y == 1
    assert trait.image.name == "7x3.png"

    trait = DrawImage("7x7.png")
    assert trait.image.surface is not None
    assert trait.image.offset_x == 3
    assert trait.image.offset_y == 3
    assert trait.image.name == "7x7.png"

    trait = DrawImage("8x8.png")
    assert trait.image.surface is not None
    assert trait.image.offset_x == 4
    assert trait.image.offset_y == 4
    assert trait.image.name == "8x8.png"

    trait = DrawImage("7x7.png", centered=False)
    assert trait.image.surface is not None
    assert trait.image.offset_x == 0
    assert trait.image.offset_y == 0
    assert trait.image.name == "7x7.png"

    trait = DrawImage("8x8.png", centered=False)
    assert trait.image.surface is not None
    assert trait.image.offset_x == 0
    assert trait.image.offset_y == 0
    assert trait.image.name == "8x8.png"

    # Validate that we can pass in the transparency hint.
    trait = DrawImage("7x7.png", hint_requires_transparency=True)
    assert trait.image.surface is not None
    assert trait.image.offset_x == 3
    assert trait.image.offset_y == 3
    assert trait.image.name == "7x7.png"

    trait = DrawImage("8x8.png", hint_requires_transparency=False)
    assert trait.image.surface is not None
    assert trait.image.offset_x == 4
    assert trait.image.offset_y == 4
    assert trait.image.name == "8x8.png"

    trait = DrawImage("7x7.png", centered=False, hint_requires_transparency=True)
    assert trait.image.surface is not None
    assert trait.image.offset_x == 0
    assert trait.image.offset_y == 0
    assert trait.image.name == "7x7.png"

    trait = DrawImage("8x8.png", centered=False, hint_requires_transparency=False)
    assert trait.image.surface is not None
    assert trait.image.offset_x == 0
    assert trait.image.offset_y == 0
    assert trait.image.name == "8x8.png"


# noinspection PyUnresolvedReferences
def test_changing_image():
    """
    Validates that the image can be changed.
    """
    setup_pgzero(__file__)
    go = GameObject(DrawImage("8x8.png"))
    assert go.image.surface is not None
    assert go.image.offset_x == 4
    assert go.image.offset_y == 4
    assert go.image.name == "8x8.png"

    update_hierarchy(go, 0)
    assert go.image.surface is not None
    assert go.image.offset_x == 4
    assert go.image.offset_y == 4
    assert go.image.name == "8x8.png"

    go.image.name = "7x3.png"
    assert go.image.surface is not None
    assert go.image.offset_x == 3
    assert go.image.offset_y == 1
    assert go.image.name == "7x3.png"

    update_hierarchy(go, 0)
    assert go.image.surface is not None
    assert go.image.offset_x == 3
    assert go.image.offset_y == 1
    assert go.image.name == "7x3.png"

    # Now try it using non-centered images
    go = GameObject(DrawImage("8x8.png", centered=False))
    assert go.image.surface is not None
    assert go.image.offset_x == 0
    assert go.image.offset_y == 0
    assert go.image.name == "8x8.png"

    update_hierarchy(go, 0)
    assert go.image.surface is not None
    assert go.image.offset_x == 0
    assert go.image.offset_y == 0
    assert go.image.name == "8x8.png"

    go.image.name = "7x3.png"
    assert go.image.surface is not None
    assert go.image.offset_x == 0
    assert go.image.offset_y == 0
    assert go.image.name == "7x3.png"

    update_hierarchy(go, 0)
    assert go.image.surface is not None
    assert go.image.offset_x == 0
    assert go.image.offset_y == 0
    assert go.image.name == "7x3.png"


# noinspection PyUnresolvedReferences
def test_using_with_game_object():
    """
    Validates it can be used as a GameObject trait.
    """
    setup_pgzero(__file__)
    go = GameObject(DrawImage("8x8.png"))
    assert go.image.surface is not None
    assert go.image.offset_x == 4
    assert go.image.offset_y == 4
    assert go.image.name == "8x8.png"
    update_hierarchy(go, 0)

    go = GameObject(Position(10, 20), DrawImage("7x3.png"))
    assert go.image.surface is not None
    assert go.image.offset_x == 3
    assert go.image.offset_y == 1
    assert go.image.name == "7x3.png"
    update_hierarchy(go, 0)


def test_draws_when_combined_with_game_object():
    """
    Validates that DrawImage draws without throwing an exception when combined with GameObject.
    """
    setup_pgzero(__file__)
    update_counter = 2

    def draw(surface):
        nonlocal update_counter
        update_counter -= 1
        if update_counter <= 0:
            environment.terminate()

    game = Game(320, 200)
    game.add_draw_func(draw)

    setup_pgzero(__file__)
    go = GameObject(Position(10, 20), DrawImage("7x3.png"))
    game.add_child(go)
    game.run()
