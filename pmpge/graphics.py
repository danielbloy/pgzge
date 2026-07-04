import pmpge.environment as environment

# These are not available in CircuitPython.
if environment.is_running_on_desktop():
    from typing import Callable

__graphics = environment.import_driver('graphics')
DriverImageResource = __graphics.DriverImageResource
GraphicsDrawImageTrait = __graphics.GraphicsDrawImageTrait
game_object_hierarchy_changed = __graphics.game_object_hierarchy_changed


# FUTURE: Add support for specifying sprites in the same way as they are in MakeCode Arcade
#         so we do not need to ship image assets (and can also make use of the MakeCode
#         Arcade paint tools).

class ImageResource(DriverImageResource):
    """
    Represents an image resource that can be loaded and drawn. The actual image
    loading and drawing is done by the graphics driver via DriverImageResource.

    Setting the name property will trigger a reload of the image and invoke the
    optional callback.

    NOTE: Instances of `DriverImageResource` are not intended to be sharable across
          `GameObject` instances as they may contain `GameObject` specific state
          required by the graphics driver. Therefore, instances of `ImageResource`
          are also NOT sharable.
    """
    width: int
    height: int
    _name: str
    notify: Callable[[], None] | None

    def __init__(self, name: str, notify: Callable[[], None] | None = None):
        DriverImageResource.__init__(self, True)  # TODO: Pass in hint here
        self.width = 0
        self.height = 0
        self.notify = notify
        self.name = name

    @property
    def name(self) -> str:
        """
        Returns the name of the image resource.
        """
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """
        Sets the name of the image resource and fires the notify event.
        """
        self._name = value
        self.width, self.height = self.load(value)

        if self.notify:
            self.notify()
