# TODO: Add type annotations

class GameObject:
    # TODO: Add children
    def __init__(self, activate=True, name=None):
        self.__active = not activate  # If this is True, the object will be updated and drawn (if visible is also True).
        self.__name = name  # Name is immutable
        self.visible = True  # If this is True, the object will be drawn (if active is also True).
        self.destroy = False  # If this is True, the object will be removed from game_objects and destroy() called.
        self.active = activate
        self.children = []

    def draw(self, surface):
        # Draw all active and visible children
        active_children = [
            game_object for game_object in self.children
            if game_object.active and game_object.visible
        ]

        for child in active_children:
            child.draw(surface)

    def update(self, dt):
        # Update all active children
        active_children = [
            child for child in self.children
            if child.active
        ]

        for child in active_children:
            child.update(dt)

        # Remove any destroyed children
        children_to_destroy = [
            child for child in self.children
            if child.destroy
        ]

        self.children = [
            child for child in self.children
            if not child.destroy
        ]

        for destroyed_child in children_to_destroy:
            destroyed_child.destroyed()

    @property
    def name(self) -> str:
        return self.__name

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, value):
        if self.__active != value:
            self.__active = value
            if value:
                self.activated()
            else:
                self.deactivated()

    # TODO: Replace with on_activated event
    def activated(self):
        pass

    # TODO: Replace with on_deactivated event
    def deactivated(self):
        pass

    # TODO: Replace with on_destroyed event
    # Called when the object is removed from game_objects
    def destroyed(self):
        pass


__root = GameObject()

__background_color = (0, 0, 0)


def set_background_colour(colour):
    global __background_color
    __background_color = colour


__draw_funcs = []


def add_draw_func(func):
    __draw_funcs.append(func)


def draw(surface):
    surface.fill(__background_color)
    for draw_func in __draw_funcs:
        draw_func(surface)

    __root.draw(surface)


__update_funcs = []


def add_update_func(func):
    __update_funcs.append(func)


def update(dt):
    for update_func in __update_funcs:
        update_func(dt)

    __root.update(dt)