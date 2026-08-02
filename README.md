# Python Multi-Platform Game Engine (pmpge)

An easy-to-use Game Engine that works with Pygame Zero on desktop computers and also with
CircuitPython and MicroPython devices. It is designed for use in Coding Clubs.

Please see my website [Code Club Adventures](http://codeclubadventures.com/) for more coding
materials.

## Overview

This project originated from a desire to make it as simple as possible for students at my coding
club to make their own games in Python using Pygame Zero. There were two primary drivers:

1. Remove the need to write the same common code in each game.
2. Avoid the need to modify code from earlier steps, focussing on incremental addition rather than
   modification

So why these aims? Removing the need to write the same common code in each game is boring for the
students and takes up time that is better spent being creative writing new code. The aim is to allow
the students to focus on the game and not the "engine".

Python is a great language for beginnings to start with but even so, writing Python code can be hard
for all newcomers. It is easy to get your indentation wrong or mix parentheses with brackets. It's
even harder to go back and change code you've already written, particularly if you have modified or
extended that code from the original. When students break and then cant fix their previously working
program it leads to frustration and loss of confidence.

It is also difficult to write clear and concise instructions explaining how to modify existing code.
It can very quickly get verbose and hard to follow. I therefore try to avoid this where possible and
focus on incremental addition of new code rather than modification of existing code.

The origins of this project are from the Python Pygame Zero games that I have written for my coding
club. Head over
to [Code Club adventures - games with Pygame Zero](https://codeclubadventures.co.uk/advancing/#games-with-pygame-zero)
to take a look.

A stretch goal for this project is to abstract the underlying host platform (Pygame Zero) so that
support can be added relatively easily for other environments at a later date. The other
environments are primarily CircuitPython and MicroPython which already provide a great hardware
abstraction layer. The driver for this is that writing games for these devices is tricky in a Code
Club other that using the MakeCode platform as the code/test cycle is tiresome and tricky for young
and inexperienced people. This framework aims to make development easy on a desktop which can then
be easily copied across to the device. The main limitation is RAM but with the new Pico 2350 and
ESP32 S3 boards offering 2Mb or more of RAM, it is not the limitation is once was.

## Project structure

The structure of the `pmpge`project is arranged in the following files (listed in order of
importance):

* `controller.py`  - Provides a standard controller abstraction offering different "levels" of
  controller so games can adapt to what the environment offers.
* `environment.py` - Provides information about the environment the engine is operating in such as
  whether it is running on a desktop or microcontroller and which type of Python.
* `game.py`        - Provides the `Game` class which is a helper class used to run the game.
* `game_object.py` - Provides the `GameObject` class which is the basis of `pmpge`.
* `graphics.py`    - Provides a standard graphics abstraction to support different environments.
* `palette.py`     - Provides the `Palette` class for managing colour palettes.
* `sound.py`       - Provides a standard sound abstraction to support different environments.
* `sprite.py`      - Provides the `Sprite` class which is used to represent a GameObject with
  position.
* `utilities.py`   - Provides general utility classes and functions to assist drivers.
* `traits`         - Directory containing a range of traits that can be added to a `GameObject`.

Some sample games written using the `pmpge` framework can be found in `games` and examples
demonstrating how to use the framework can be found in `examples`. There is also the `assets`
directory that contains an inventory of all the assets used in the projects.

## Setting up a Development Environment

The project has been developed using the [PyCharm IDE](https://www.jetbrains.com/pycharm/)
with a VENV for Python (using Python 3.12) with tests written using `pytest` (see
[pytest](https://docs.pytest.org/en/8.2.x/) for more information).

In PyCharm, the following "Project Structure" is used:

![Project Structure](./project_structure.png)

## Supporting Different Execution Environments

In a nutshell, the framework is designed to work as much as possible with vanilla Python with small
modifications to support CircuitPython and MicroPython. Where this gets a little more tricky is with
graphics, sound and controller support. To support these, the framework has been designed to be able
to be extended with new drivers. Some default drivers are provided to cover a broad range of
hardware but it is possible to write your own drivers. For more information on the devices
supported, look at the documentation in the `devices` directory.

So what drivers do you need? You will need drivers to support graphics, sound and controller input.
There is also the option for a device driver too. Using a non-default driver requires setting of the
following configuration properties:

* `DEVICE_DRIVER`
* `CONTROLLER_DRIVER`
* `SOUND_DRIVER`
* `GRAPHICS_DRIVER`

For more information on how to implement a driver, see the documentation in
[drivers](./pmpge/drivers/README.md).

### Note about images

When executing in a CircuitPython environment, transparency can get confusing when loading PNG files
as the function used to load images (`adafruit_imageload.load()`)
does not directly load an alpha channel into the bitmaps. Instead, it loads the image data into a
`Bitmap` and colour indices into a `Palette`. We then pick a specific colour from the Palette to be
transparent; we always pick the first colour and this is often black. If your PNG file has an alpha
channel, `adafruit_imageload.load()`
typically assigns those pixels to the first colour in the palette; this is often Black. Therefore,
if your sprites have transparent bits where you would not expect them to be transparent when
executing in a CircuitPython environment, check the colour palette you have used.

## Roadmap and Changelog

For information on current development priorities, see [roadmap](./roadmap.md). For details of
releases, see [changelog](./changelog.md).

## Alternative projects

This project has specific goals of making it easier to write games in Python both with Pygame Zero
and on microcontroller execution environments. The main audience for this project is Code Clubs. If
this does not meet your needs, there are other projects that may do so. Other projects which I
recommend are listed below.

[picogame](https://picogame.makerclass.cz/) is the most directly comparable project to `pmpge` and
is designed to run on CircuitPython devices as well as in a simulator or in the web editor. It is
designed to run on a [PicoPad](https://picopad.eu/en/) which is a low-cost microcontroller as well
as on custom hardware (a guide is provided). You can find out more on their website or on
[GitHub](https://github.com/MakerClassCZ/picogame).

[MakeCode Arcade](https://arcade.makecode.com/) is a wonderful project that I use extensively in my
Code Clubs. It is developed by Microsoft, runs in a browser for ease of use and supports downloading
to microcontrollers. It is both blocks based as well as supporting TypeScript and Python. This is a
great platform to move to after Scratch. I also provide some materials for it on my
website [here](https://codeclubadventures.co.uk/progressing/#makecode-arcade).

[Pyxel](https://kitao.github.io/pyxel/web/user-guide/) is a retro game engine for Python in the
style of PICO-8. It is suitable for more advanced users. You can see more on
the [GitHub](https://github.com/kitao/pyxel/tree/main) site.

There is also [TIC-80](https://tic80.com/) and [PICO-8](https://www.lexaloffle.com/pico-8.php)
which are virtual consoles that are similar to Pyxel. Pico-8 is programmed in Lua and TIC-80
supports a range of programming languages including Lua, JavaScript and Python
(see [here](https://github.com/nesbox/TIC-80/wiki)).

## License

All materials provided in this project is licensed under the Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International License. To view a copy of this license,
visit
<https://creativecommons.org/licenses/by-nc-sa/4.0/>.

In summary, this means that you are free to:

* **Share** — copy and redistribute the material in any medium or format.
* **Adapt** — remix, transform, and build upon the material.

Provided you follow these terms:

* **Attribution** — You must give appropriate credit , provide a link to the license, and indicate
  if changes were made. You may do so in any reasonable manner, but not in any way that suggests the
  licensor endorses you or your use.
* **NonCommercial** — You may not use the material for commercial purposes.
* **ShareAlike** — If you remix, transform, or build upon the material, you must distribute your
  contributions under the same license as the original.