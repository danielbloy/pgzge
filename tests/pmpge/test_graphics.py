import pytest

from pmpge.graphics import ImageResource
from tests.pmpge.testing_utilities import setup_pgzero


def test_create_image_resource():
    """
    Validates that image resource is created okay in various ways.
    """
    setup_pgzero(__file__)

    # This will error
    with pytest.raises(KeyError):
        image = ImageResource("")

    # As will this
    with pytest.raises(KeyError):
        image = ImageResource("unknown")

    # This will work
    image = ImageResource("earth.png")
    assert image._name == "earth.png"
    assert image.width == 16
    assert image.height == 16

    # As will losing the .png
    image = ImageResource("earth")
    assert image._name == "earth"
    assert image.width == 16
    assert image.height == 16

    # Now try a different size image
    image = ImageResource("moon")
    assert image._name == "moon"
    assert image.width == 8
    assert image.height == 8

    # Now validate we can specify the transparency hint
    image = ImageResource("earth", hint_requires_transparency=True)
    assert image._name == "earth"
    assert image.width == 16
    assert image.height == 16

    image = ImageResource("moon", hint_requires_transparency=False)
    assert image._name == "moon"
    assert image.width == 8
    assert image.height == 8


def test_changing_image_work():
    """
    Validates that when the name is changed, the image resource is changed.
    """
    setup_pgzero(__file__)

    image = ImageResource("earth")
    assert image._name == "earth"
    assert image.width == 16
    assert image.height == 16

    # Change it
    image.name = "moon"
    assert image._name == "moon"
    assert image.width == 8
    assert image.height == 8

    # and change it again
    image.name = "7x3"
    assert image._name == "7x3"
    assert image.width == 7
    assert image.height == 3


def test_callback_works():
    """
    Validates that callback works when the name is changed (and the new image is loaded).
    """
    setup_pgzero(__file__)

    count: int = 0

    def callback():
        nonlocal count
        count += 1

    image = ImageResource("earth", callback)
    assert image._name == "earth"
    assert image.width == 16
    assert image.height == 16
    assert count == 1

    # Change it
    image.name = "moon"
    assert image._name == "moon"
    assert image.width == 8
    assert image.height == 8
    assert count == 2

    # and change it again
    image.name = "7x3"
    assert image._name == "7x3"
    assert image.width == 7
    assert image.height == 3
    assert count == 3
