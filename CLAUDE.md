# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`pmpge` (Python Multi-Platform Game Engine) is a game engine for Coding Clubs that runs
unmodified on desktop (via Pygame Zero) and on microcontrollers (CircuitPython/MicroPython).
Two design goals shape almost every decision in this codebase:

1. Avoid students needing to write the same boilerplate in every game.
2. Favour incremental addition of code over modification of existing code, since beginners
   find editing previously-working code error-prone and demoralising.

A stretch goal is abstracting the host platform so the same game code can run on desktop for
fast iteration and then be copied to a microcontroller with no changes. See `README.md` for
the full rationale and `devices/README.md` for the microcontroller performance targets
(30 fps @ 160x120, 20-50 GameObjects, 8x8/16x16 sprites).

## Commands

```bash
# Install dependencies (editable install required for tests/examples to import pmpge)
pip install -r requirements.txt
pip install -e .

# Run the full unit test suite
pytest tests/

# Run a single test file / test
pytest tests/pmpge/test_game.py
pytest tests/pmpge/test_game.py::test_name -v

# Run all example scripts as a smoke test (each example must execute without error)
pytest examples/

# Lint (matches CI: first command fails the build, second is warning-only)
flake8 pmpge --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 pmpge --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run device/driver validation scripts (not part of pytest; exercises real drivers)
PYTHONPATH=. python validate/validate_all.py
```

CI (`.github/workflows/python-app.yml`) runs on Python 3.12 and 3.13 and executes, in order:
flake8, `pip install -e .`, `pytest tests/`, `pytest examples/`, then `validate/validate_all.py`.
Reproduce all four before considering a change done.

## Architecture

### Environment/driver abstraction (the core of the multi-platform design)

`pmpge/environment.py` is the platform boundary. It detects at import time whether the code is
running on desktop, CircuitPython, or MicroPython (via `sys.implementation.name`) and **must
not import any other file in the framework except drivers** — everything else depends on it,
so it cannot depend back.

Four pluggable driver categories exist: `DEVICE_DRIVER`, `CONTROLLER_DRIVER`, `SOUND_DRIVER`,
`GRAPHICS_DRIVER`. Each has a `pgzero` implementation for desktop and a `none`/microcontroller-specific
implementation under `pmpge/drivers/{controller,device,graphics,sound}/`. The active driver is
resolved per-category in `environment.py` (`get_*_driver()`), defaulting by platform unless overridden
by a `config.py` in the game's working directory (e.g. `GRAPHICS_DRIVER = "pmpge.drivers.graphics.displayio"`).
Drivers are loaded dynamically via `import_driver()`, which uses `importlib` on desktop and a manual
`__import__` fallback on microcontrollers (no `importlib` there). A driver optionally implements
`init()`, `update(delta_time)`, and `deinit()` hooks; see `pmpge/drivers/README.md` and the per-driver
docs (`controller.md`, `device.md`, `graphics.md`, `sound.md`) for the mandatory interface of each kind.

`environment.execute(game, background_colour)` is the actual game loop entry point: on desktop it
injects `draw()`/`update()` into `__main__` for Pygame Zero to call; on a microcontroller it runs its
own loop using the `RateLimiter` class (also defined in `environment.py`) to independently throttle
`update()` and `draw()` to `UPDATE_FRAMERATE`/`GRAPHICS_FRAMERATE`.

When changing platform-sensitive code, remember CircuitPython/MicroPython lack parts of the standard
library (e.g. `typing`, `collections.abc.Callable`, `importlib`) — existing code guards these imports
behind `is_running_on_desktop()` checks; follow that pattern rather than importing unconditionally.

### GameObject / trait system

`pmpge/game_object.py` defines `GameObject`, the base of nearly everything in the engine (see the
class docstring there for the full contract — it's the best single source of truth). Key points:

- Parent/child hierarchy with `update_hierarchy()`/`draw_hierarchy()` traversal, gated by
  `active`/`enabled`/`visible`/`alive` flags with specific propagation rules (e.g. `active` propagates
  to children, `enabled`/`visible` do not; `destroy()`/`activate()`/`deactivate()` always propagate
  regardless of `active`).
- A handler-list system (`draw_handlers`, `update_handlers`, `activate_handlers`,
  `deactivate_handlers`, `destroy_handlers`) that lets behaviour be attached without subclassing.
- **Traits** (`pmpge/traits/`) are mixins applied via `GameObject(*traits)`: applying a trait copies
  its instance variables onto the GameObject and registers any of its `draw()`/`update()`/`activated()`/
  `deactivated()`/`destroyed()` methods into the corresponding handler list, plus calls `merged()` if
  present. Traits commonly depend on other traits being present (e.g. `Acceleration` requires
  `Velocity`, `Velocity` requires `Position`) — this is documented per-trait, not enforced by the type
  system, so check the trait's docstring before combining them.
- `Sprite` (`pmpge/sprite.py`) is the canonical example of subclassing `GameObject` plus traits
  together, for cases where traits alone aren't sufficient (e.g. property getters/setters).

Trait categories live under `pmpge/traits/`: `physics.py` (velocity, acceleration, friction, bounce,
oscillator, angular motion), `position.py`, `controller.py`, `graphics.py`, `lifetime.py`.

### Testing

- `tests/pmpge/` mirrors the `pmpge` package structure; `tests/drivers/` contains dummy driver
  implementations used to exercise the engine without real Pygame Zero/hardware dependencies.
- `examples/` doubles as both learning material (numbered `1 - Game` through `5 - Controller`) and a
  test suite — `examples/test_examples.py` executes every `.py` file in every example subfolder as a
  subprocess and fails if any exits non-zero. When adding a new example, make sure it runs cleanly to
  completion (it will be picked up automatically; no registration needed).
- `validate/` is not run by pytest — it targets real CircuitPython/MicroPython hardware and includes
  interactive/human-judged checks (see `validate/validation.md` for the device setup procedure) and
  performance baselines. `validate/validate_all.py` runs the non-interactive subset and is what CI
  invokes on desktop as a smoke test of the drivers.

### Games vs examples vs devices

- `examples/` — minimal, numbered, incremental lessons teaching the API.
- `games/pgzero/` — complete desktop-only games. `games/multi-platform/` — games designed to also run
  on the Adafruit EdgeBadge reference hardware.
- `devices/` — reference `config.py` files for specific supported hardware boards.
