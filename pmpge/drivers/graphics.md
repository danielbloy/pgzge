# Graphics Driver

## Optional methods

### `init(game, screen_width, screen_height, background_colour)`

Called once when the game first runs.

#### Parameters

* `game` - the Game object that is being executed
* `screen_width` - the width of the screen in pixels.
* `screen_height` - the height of the screen in pixels.
* `background_colour` - the default colour of the background in RGB format.

### `update(delta_time: float)`

Called once every update cycle before anything else.

#### Parameters

* `delta_time` - the time since update was last called, in fractions of a second.

### `deinit()`

Called once when the game finishes.

## Mandatory methods

A graphics driver must implement the following mandatory methods:

### `clear(surface)`

Called once per frame. Called before any other display operations.

#### Parameters

* `surface` - an implementation dependent parameter representing the visual
  surface to draw to. For Pygame Zero this will be the `screen` variable. For
  microcontrollers this will be None.

### `draw(surface)`

Called once per frame and passed a surface object that is implementation-dependent.
This function is responsible for drawing the hierarchy of GameObjects (from
`game.root`) and then calling `game.draw` followed by any scaling or other effects.

#### Parameters

* `surface` - an implementation dependent parameter representing the visual
  surface to draw to. For Pgzero this will be the `screen` variable. For
  microcontrollers this will be None.

### `game_object_hierarchy_changed()`

Called to indicate there have been changes to the GameObject hierarchy. This gives
the graphics driver an opportunity to rebuild the graphics objects should it need
to do so. This can be an expensive operation on microcontrollers so use sparingly.

## Mandatory classes

A graphics driver must implement the following mandatory classes:

### `DriverImageResource`

Requires the implementation of a single method:
`def load(self, image: str, hint_requires_transparency: bool) -> tuple[int, int]:`

This performs the driver specific loading of the named image resource. The returned tuple
contains the image width and height. This class is for combining with the `ImageResource`
class in the graphics library.

The `hint_requires_transparency` parameter is used to provide information to the driver
which allows it to potentially perform some optimisation if transparency is not required.
This is particularly important for microcontrollers to save CPU cycles.

NOTE: Instances of `DriverImageResource` are not intended to be sharable across `GameObject`
instances as they may contain `GameObject` specific state.

### `GraphicsDrawImageTrait`

Requires the implementation of the `draw()` method to provide the drawing part of `DrawImage`.
There is no other dependency between the two classes.