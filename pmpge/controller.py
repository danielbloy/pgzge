"""
TODO: Replace ABXY with NSEW and provide mappings for ABXY which is device specific.

The controller configuration is based on 12 button SNES controller as follows:

 L Shoulder   R Shoulder

      U           X
    L   R       Y   A
      D           B

    Start       Select

Because the range of devices varies, so does the number of buttons available so all
devices may not support the 12 set of 12 buttons. Common other configurations include:

10 button SNES controller without shoulder buttons:

      U           X
    L   R       Y   A
      D           B

    Start       Select

8 button NES:

      U
    L   R           A
      D           B

    Start       Select

There are lots of other configurations possible too depending on the device.
"""

import pmpge.environment as environment


# FUTURE: Add support for a second players controller
# FUTURE: Add support for a on_repeat event


class Controller:
    """
    The controller has static values that the underlying driver sets.
    This allows multiple instances of controller to share the values.
    There are instance properties that are read only that expose the
    underlying values.
    """
    values: list[bool] = [False for _ in range(12)]  # Current button values
    changed: list[bool] = [False for _ in range(12)]  # Have buttons changed?

    _previous: list[bool] = [False for _ in range(12)]

    # Constants to help access the button values.
    BUTTON_START: int = 0
    BUTTON_SELECT: int = 1
    BUTTON_LEFT: int = 2
    BUTTON_RIGHT: int = 3
    BUTTON_UP: int = 4
    BUTTON_DOWN: int = 5
    BUTTON_A: int = 6
    BUTTON_B: int = 7
    BUTTON_X: int = 8
    BUTTON_Y: int = 9
    BUTTON_LS: int = 10
    BUTTON_RS: int = 11

    @staticmethod
    def reset():
        """
        Reset the controller to its initial state.
        """
        current = Controller.values
        previous = Controller._previous
        changed = Controller.changed
        for i in range(len(Controller.values)):
            current[i] = False
            previous[i] = False
            changed[i] = False

    @staticmethod
    def update(values: list[bool]):
        """
        This updates the button values with a new set. The set of values must be
        exactly 12 booleans long, with each representing a specific button.
        This will set the changed status also.
        """
        current = Controller.values
        previous = Controller._previous
        changed = Controller.changed

        for i in range(12):
            previous[i] = current[i]  # Save old value
            current[i] = values[i]  # Set new value
            changed[i] = current[i] != previous[i]  # Determine if changed

    @staticmethod
    def events() -> list[tuple[int, bool]]:
        """
        Returns a list of the buttons that have changed since the last update.
        and what their status is. The returned list is a list of tuples where
        the first element is the button number and the second element is the
        button status (True for pressed, False for released).
        """
        changed = Controller.changed
        if not any(changed):
            return []
        result = []
        current = Controller.values
        for i in range(12):
            if changed[i]:
                result.append((i, current[i]))

        return result

    @staticmethod
    def is_pressed(button: int) -> bool:
        """
        Returns True if the button is pressed, False otherwise.
        """
        return Controller.values[button]

    @staticmethod
    def is_released(button: int):
        """
        Returns True if the button is released, False otherwise.
        """
        return not Controller.values[button]

    @staticmethod
    def has_changed(button: int):
        """
        Returns True if the button has changed state since the last update.
        """
        return Controller.changed[button]

    @staticmethod
    def has_pressed(button: int):
        """
        Returns True if the button has been pressed since the last update.
        """
        return Controller.values[button] and Controller.changed[button]

    @staticmethod
    def has_released(button: int):
        """
        Returns True if the button has been released since the last update.
        """
        return not Controller.values[button] and Controller.changed[button]

    @property
    def start(self) -> bool:
        return Controller.values[0]

    @property
    def select(self) -> bool:
        return Controller.values[1]

    @property
    def left(self) -> bool:
        return Controller.values[2]

    @property
    def l(self) -> bool:
        return Controller.values[2]

    @property
    def right(self) -> bool:
        return Controller.values[3]

    @property
    def r(self) -> bool:
        return Controller.values[3]

    @property
    def up(self) -> bool:
        return Controller.values[4]

    @property
    def u(self) -> bool:
        return Controller.values[4]

    @property
    def down(self) -> bool:
        return Controller.values[5]

    @property
    def d(self) -> bool:
        return Controller.values[5]

    @property
    def a(self) -> bool:
        return Controller.values[6]

    @property
    def b(self) -> bool:
        return Controller.values[7]

    @property
    def x(self) -> bool:
        return Controller.values[8]

    @property
    def y(self) -> bool:
        return Controller.values[9]

    @property
    def left_shoulder(self) -> bool:
        return Controller.values[10]

    @property
    def ls(self) -> bool:
        return Controller.values[10]

    @property
    def right_shoulder(self) -> bool:
        return Controller.values[11]

    @property
    def rs(self) -> bool:
        return Controller.values[11]


__controller = environment.import_driver('controller')
