print("No graphics driver")


def draw(_):
    """
    Mandatory draw method, does nothing.
    """
    pass


def game_object_hierarchy_changed():
    """
    Mandatory function, does nothing.
    """
    pass


class DriverImageResource:
    """
    Mandatory class, does nothing.
    """

    def __init__(self, hint_requires_transparency: bool):
        pass
    
    # noinspection PyMethodMayBeStatic
    def load(self, _: str) -> tuple[int, int]:
        return 0, 0


class GraphicsDrawImageTrait:
    """
    Mandatory class, does nothing.
    """
    pass
