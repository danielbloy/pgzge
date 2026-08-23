# Changelog

## Unreleased

Fixed sprites that contain black pixels displaying those pixels as transparent with the
displayio graphics driver. Images that supply their own transparency information (indexed
PNG files with a `tRNS` chunk) now keep it instead of having the black/index 0 colour key
applied. Added `tools/convert_images.py` to convert RGBA PNG files into that format and
documented the behaviour in the 'Note about images' section of `README.md`. Images that
do not supply their own transparency information behave exactly as before.

## 0.1.0 - Alpha

Version 0.1.0 provides the basic functionality of the game engine, including support for a
range of traits covering movement, graphics, lifetime and physics. A range of controller
options are supported on both Desktop and CircuitPython platforms. Graphics are supported
on Desktop and CircuitPython platforms that support displayio and have a builtin Display.
All provided functionality works and has comprehensive test coverage.

This version is classed as alpha quality as the graphics functionality is limited, the
sound functionality is non-existent and there is a modest chance that structural changes
will be required to support sound and an extended graphics API. The range of CircuitPython
devices that are supported is limited to those with built-in displays.
