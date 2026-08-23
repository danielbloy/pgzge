# Roadmap

## Now

* Rework the controller to use NSEW for the right side buttons instead of ABXY. Then use mappings
  which are device controlled to map ABXY to NSEW. Requires updating the examples.
* Modify the validation scripts to continue to reduce memory requirements
* Expand the set of examples to cover all supported traits.
* Implement a small number of simple example games based on MakeCode Arcade examples
* Add support for CircuitPython devices that do not have a builtin display
    * Include support for SPI displays
    * Include support for 8-bit parallel displays (for improved performance)
* Build a custom reference handheld "console" based around a Pico 2 board with a 160x128 display
  with 10 buttons
* Build a custom reference TV "console" based around a Pico 2 board and HDMI output with SNES
  controllers

## Next

* Implement a sound driver support for Pygame Zero and CircuitPython
* Extend the set of built-in traits

## Later

* Extend the graphics driver with additional capabilities
* Extend the sound driver with additional capabilities
* Add multi-microcontroller support with one controller driving the screen and the second
  microcontroller driving the game, connected via SPI
* Add support for left stick and right stick analogue controllers.
* Explore supporting MicroPython

### Functionality gaps against MakeCode Arcade

The following are known functionality gaps between this framework and MakeCode Arcade that will be
closed as development of the multi-platform games continues.

* Lives - Info Trait
* Scores - Info Trait
* Countdown - Info Trait
* Game over - Game Trait
* On Game Update every 500ms - Game Trait
* On Game Update - Game Trait
* Reset game - Game Trait
* Time since start (ms) - Game Trait
* Embedded image assets
* Palette
* Backgrounds
* Animations
* Scrolling/tilemaps
* Collision detection
* Particles
