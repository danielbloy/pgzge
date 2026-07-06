#
# This graphics driver is functional and has reasonable performance on modest
# hardware such as a PyBadge. Presently it provides enough functionality to
# support the desired background colour and the DrawImage trait.
#
# LIMITATION: DISPLAY
#
# Currently, this driver will only work on controllers with built-in displays
# as the board.DISPLAY variable is used.
#
# LIMITATION: HIERARCHY
#
# There is one notable limitation of this driver versus the Pygame zero driver
# that it is important to be aware of and it is related to how the TileGrid
# instances which are used to contain the graphics are constructed. When the
# game is initialise (init() is called) we traverse the entire hierarchy (all
# active AND inactive GameObjects) and generate the TileGrid instances. These
# are all added to the object Group instance. Because we add them in the order
# that we traverse the hierarchy, the implicit draw order is preserved - even
# with the deactivated objects. We also only generate the TileGrid instances
# we need. See the note below about why we don't mimic the hierarchy structure.
#
# However, if the hierarchy later changes, we do not rebuild the order of the
# TileGrid instances. New GameObjects will get added to the end of the list in
# the order they are process. Further, if the parent and child relationships are
# changed for existing objects, the TileGrid order is NOT changed to reflect this.
#
# The way to work around this is straightforward.
#  * Ensure you entire hierarchy is consistent from the start and when adding
#    new branches to the hierarchy, do it in a way that works additively (i.e.
#    add the entire new branch to the Game.root instance).
#  * If you need to rework the hierarchy, call Graphics.game_object_hierarchy_changed()
#    which will force a rebuild of the entire hierarchy. This is expensive so
#    use it sparingly and at points that can accommodate the performance hit.
#
# Destroyed objects always get removed correctly. Deactivated objects get correctly
# hidden.
#
# Why don't we mimic the hierarchy structure?
#
# Some GameObjects can have multiple TileGrid instances and some GameObjects will
# have none. We could in theory place a single Group instance on each GameObject
# in the hierarchy and attach the TileGrids to those and connect up the Groups in
# the hierarchy. Whilst a definite potential improvement, it does come with an
# extra memory requirement and unfortunately, doesn't address all issues. This is
# because under normal operation the draw() function only cycles over enabled
# objects, so if a mix of disabled and enabled objects are added, then the draw
# order won't be correct. therefore, the lower memory cost and faster performance
# option was taken.
#
# REFERENCES
#
# * https://docs.circuitpython.org/en/latest/shared-bindings/displayio/
# * https://learn.adafruit.com/circuitpython-display-support-using-displayio/display-a-bitmap
# * https://learn.adafruit.com/creating-your-first-tilemap-game-with-circuitpython/overview
#
# NOTES
#
# * The display variable is a BusDisplay:
#   See: https://docs.circuitpython.org/en/latest/shared-bindings/busdisplay/index.html#module-busdisplay
#
# * Investigate supporting different bitmap types:
#   See: https://learn.adafruit.com/creating-your-first-tilemap-game-with-circuitpython/indexed-bmp-graphics
#
# * Create a single colour bitmap for the background.
#   See: https://learn.adafruit.com/circuitpython-display-support-using-displayio/draw-pixels

import time

# noinspection PyUnresolvedReferences,PyPackageRequirements
import adafruit_imageload
# noinspection PyUnresolvedReferences,PyPackageRequirements
import board
# noinspection PyUnresolvedReferences,PyPackageRequirements
import terminalio
# noinspection PyUnresolvedReferences,PyPackageRequirements
from adafruit_display_text import label

# noinspection PyUnresolvedReferences,PyPackageRequirements
from displayio import Group, Palette, Bitmap, TileGrid
from pmpge.game import Game
from pmpge.game_object import GameObject, draw_hierarchy, traverse_hierarchy
from pmpge.utilities import calculate_scaling_factor, Borders, CalculateFps

display = board.DISPLAY
display.root_group = None
display.brightness = 0.0  # Turn the display off until the game starts

game: Game | None = None

# Root group to place all items to draw.
root = Group()
background_group: Group = Group()
object_group: Group = Group()
border_group: Group = Group()
overlay_group: Group = Group()

root.append(background_group)
root.append(object_group)
root.append(border_group)
root.append(overlay_group)

background_palette = Palette(1)
background_palette[0] = 0x000000

border_palette = Palette(1)
border_palette[0] = 0x000000

manual_refresh = False
manual_refresh_rate = 0

graphics_stats = False


# The following updates the FPS counter text. This only gets executed if GRAPHICS_STATS
# is present in the config file and set to True
def display_update_fps(fps: int):
    update_fps_text.text = str(fps)


# We manually track the time between each display call so we can show the
# game update fps and the screen draw fps separately.
time_func = time.monotonic
last_draw: float = 0.0


def display_draw_fps(fps: int):
    draw_fps_text.text = str(fps)


update_fps: CalculateFps = CalculateFps(callback_interval=0.5, callback=display_update_fps)
draw_fps: CalculateFps = CalculateFps(callback_interval=0.5, callback=display_draw_fps)
# The text labels are anchored in the bottom left and bottom right hand corners of the screen.
# We only use the default font it is exactly 8 pixels high if you ignore the descender part so
# we need to drop it down so to avoid it overlapping the game area with an 8 pixel lower border.
update_fps_text = label.Label(terminalio.FONT, text="00", color=0xFFFFFF)
update_fps_text.anchored_position = (0, display.height + 2)
update_fps_text.anchor_point = (0.0, 1.0)

draw_fps_text = label.Label(terminalio.FONT, text="00", color=0xFFFFFF)
draw_fps_text.anchored_position = (display.width - 1, display.height + 2)
draw_fps_text.anchor_point = (1.0, 1.0)


def init(g: Game, _: int, __: int, bgc: tuple[int, int, int]):
    """
    Initialises the display by creating the desired background, building the entire
    hierarchy of TileGrids and turning on the display.
    """
    global game, last_draw, manual_refresh, manual_refresh_rate, graphics_stats
    game = g

    # Here we build the entire graphics hierarchy in order to place the tileGrid
    # instances in the correct order.
    game_object_hierarchy_changed()

    scaling_factor = calculate_scaling_factor(display.width, display.height, g.width, g.height)
    object_group.scale = scaling_factor

    borders = Borders(display.width, display.height, g.width, g.height, scaling_factor)
    for width, height, x, y in borders.borders:
        border = TileGrid(Bitmap(width, height, 1), pixel_shader=border_palette)
        border.x = x
        border.y = y
        border_group.append(border)

    # Make the game objects relative to the borders
    object_group.x = borders.game_x
    object_group.y = borders.game_y

    # Set the single colour in the palette for our background to the desired background colour
    red = bgc[0] & 255
    green = bgc[1] & 255
    blue = bgc[2] & 255
    background_palette[0] = red << 16 | green << 8 | blue

    # If the background colour is black we can avoid the background object entirely to save RAM.
    # and make it a tiny bit faster.
    if background_palette[0] != 0x000000:
        background = TileGrid(Bitmap(g.width, g.height, 1), pixel_shader=background_palette)
        background_group.scale = scaling_factor
        background_group.append(background)

        # Now adjust the background based on the borders
        background_group.x = borders.game_x
        background_group.y = borders.game_y

    display.root_group = root

    # Determine if we should manually refresh the display.
    from pmpge.environment import config

    if hasattr(config, 'GRAPHICS_MANUAL_REFRESH'):
        manual_refresh = config.GRAPHICS_MANUAL_REFRESH
        # noinspection PyUnresolvedReferences
        manual_refresh_rate = config.GRAPHICS_FRAMERATE  # This property is guaranteed to be set on a microcontroller

    display.auto_refresh = not manual_refresh

    if hasattr(config, 'GRAPHICS_STATS'):
        graphics_stats = config.GRAPHICS_STATS
        overlay_group.append(update_fps_text)
        overlay_group.append(draw_fps_text)

    update_fps.reset()
    draw_fps.reset()
    last_draw = time_func()

    # Finally we turn on the display
    display.brightness = 1


def deinit():
    """
    Removes everything left from the object group.
    """
    global game
    game = None

    display.root_group = None
    display.auto_refresh = True  # Always revert back to auto refresh

    # Remove all the items from the groups (most items from the object group should
    # have been removed via the GameObject.destroy() method.
    for group in [background_group, object_group, border_group]:
        while len(group) > 0:
            obj = group.pop()
            obj.bitmap.deinit()

    # Now treat the overlay group separately.
    while len(overlay_group) > 0:
        overlay_group.pop()

    clear_image_cache()


def update(dt: float):
    """
    Calculates the FPS and displays it on the overlay
    """
    if graphics_stats:
        update_fps.update(dt)


def draw(screen):
    """
    We have to process the entire hierarchy to ensure visbility is set. We also do a
    little bit of maths if we are displaying the graphics stats to calculate the
    framerate (because draw does not get the time delta).
    """
    if graphics_stats:
        global last_draw
        now = time_func()
        draw_fps.update(now - last_draw)
        last_draw = now

    # noinspection PyUnresolvedReferences
    draw_hierarchy(game.root, screen, draw_only_visible=False)
    # noinspection PyUnresolvedReferences
    game.draw(screen)
    if manual_refresh:
        display.refresh(target_frames_per_second=manual_refresh_rate)


# This global setting is used to force all GameObjects to re-add their displayio
# objects back to the object Group. This is used when rebuilding the hierarchy.
force_add_tile_grids = False


def game_object_hierarchy_changed():
    """
    This notifies us that the game has made changes to the GameObject hierarchy. We don't
    know what those changes are so we forcibly remove and re-add all displayio objects
    to the object Group. This ensures that the draw order of the objects is correct.

    This is an expensive operation so use sparingly.
    """
    global force_add_tile_grids
    force_add_tile_grids = True

    while len(object_group) > 0:
        object_group.pop()

    def forced_draw(go: GameObject, _):
        # noinspection PyProtectedMember
        go._draw(None)
        return True, None

    # noinspection PyUnresolvedReferences
    traverse_hierarchy(game.root, forced_draw)
    force_add_tile_grids = False


# FUTURE: Do something better for caching. We could also extract out the code in deinit().
image_cache: dict[str, tuple[Bitmap, Palette]] = {}


def clear_image_cache():
    """
    Erases all cached images.
    """
    for bitmap, _ in image_cache.values():
        bitmap.deinit()
    image_cache.clear()


# This extraction has a massive positive impact on draw speed
def load_image(image: str, requires_transparency: bool) -> tuple[Bitmap, Palette]:
    """
    This will populate the image_cache with the specified image resource if it
    does not already exist in the cache. It will then return the cached image.

    NOTE: Because we cache images to save RAM, the `requires_transparency` parameter on
          the first time the image is loaded applies. If the image is later loaded but
          has a different `requires_transparency` value, it is ignored.
    """
    if image in image_cache:
        image = image_cache[image]
        return image[0], image[1]

    bitmap, palette = adafruit_imageload.load(f"/images/{image}", bitmap=Bitmap, palette=Palette)
    image_cache[image] = bitmap, palette

    # PERFORMANCE: Transparency has a pretty harsh impact on fps so only use it when necessary.
    if requires_transparency:
        palette.make_transparent(0)

    return bitmap, palette


class DriverImageResource:
    """
    Implementation specific class to load an image resource. The only mandatory
    method is load(). This class is designed to be combined with `ImageResource`.

    NOTE: Instances of `DriverImageResource` are not intended to be sharable across
          `GameObject` instances as they may contain `GameObject` specific state
          required by the graphics driver.
    """
    tile_grid: TileGrid
    tile_grid_index: int  # Holds the index that the image was added to the object_group
    new_image_loaded: bool  # Set to True when load is called.
    requires_transparency: bool  # Used to optimise the drawing of images

    def __init__(self, hint_requires_transparency: bool):
        # Indicate that this is the first time the image has been added but using -1
        self.tile_grid_index = -1
        self.requires_transparency = hint_requires_transparency

    def load(self, image: str) -> tuple[int, int]:
        """
        Loads the named image resource, returning the width and height.
        """
        bitmap, palette = load_image(image, self.requires_transparency)

        # Create a TileGrid to hold the bitmap
        tile_grid = TileGrid(bitmap, pixel_shader=palette)
        tile_grid.hidden = True
        self.new_image_loaded = True

        # Now set the properties on the containing object
        self.tile_grid = tile_grid
        return bitmap.width, bitmap.height


class GraphicsDrawImageTrait:
    """
    This class is designed to be combined with a `DrawImage` trait.
    """
    x: int
    y: int
    _active: bool  # From GameObject
    visible: bool  # From GameObject

    image: DriverImageResource

    def __init__(self):
        pass

    def draw(self, _):
        """
        Draws the image at the specified position, offset from the GameObjects position.
        """
        image = self.image

        # Either add a new image to the object_group or replace the existing one.
        index = image.tile_grid_index
        if force_add_tile_grids or index < 0:  # Add image
            image.tile_grid_index = len(object_group)
            object_group.append(image.tile_grid)

        elif image.new_image_loaded:  # Replace existing image
            object_group[index] = image.tile_grid

        image.new_image_loaded = False

        tile_grid = image.tile_grid
        tile_grid.hidden = not (self._active and self.visible)
        # noinspection PyUnresolvedReferences
        tile_grid.x = int(self.x - image.offset_x)
        # noinspection PyUnresolvedReferences
        tile_grid.y = int(self.y - image.offset_y)

    def deactivated(self):
        """
        We just set `hidden` on the TileGrid to stop it being displayed.
        """
        self.image.tile_grid.hidden = True

    def destroyed(self):
        """
        We hide the TileGrid but do not remove it from the object group to avoid invalidating
        all the other index values. To free up memory of destroyed objects, call the function
        game_object_hierarchy_changed().
        """
        self.image.tile_grid.hidden = True
