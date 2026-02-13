from collections.abc import Callable
from typing import Self, Any


class GameObject:
    """
    GameObject is the base class for all objects in the game. It provides a simple parent/child structure
    for updating and drawing GameObjects as well as a simple way to manage active and visible states.

    A GameObject has the following properties:
        * name: The name of this object. Used when locating an object by name.
        * active: If this is True, the object will be updated and drawn (visible also needs to be
                  True to be drawn).
        * visible: If this is True and active is also True, the object will be drawn.
        * destroy: If this is True, the object will be removed from its parent at the next update.
        * children: A list of child GameObjects. These will be updated and drawn only if this
                    GameObject is active.
        * draw_handler: If specified, this function will be called immediately after drawn() is
                        called and before any children are drawn.
        * update_handler: If specified, this function will be called immediately after updated() is
                          called and before any children are updated.
        * activate_handler = If specified, this function will be called immediately after activated()
                             is called. A GameObject is activated when the active property is set to
                             True.
        * deactivate_handler = If specified, this function will be called immediately after deactivated()
                               is called. A GameObject is deactivated when the active property is set to
                               False.
        * destroyed_handler = If specified, this function will be called immediately after destroyed()
                              is called.

        # TODO: explain handler vs handlers

        # TODO: Note update, draw, activate and deactivate propoagates down the hierarchy
        # TODO: Add a paused property that is like active but does not trigger the activate and deactivate events when changed.
        # TODO: Add a parent property.

        The handlers can be used to provide instance specific behaviour without having to make a subclass
        and override the relevant method.
    """

    def __init__(self,
                 name: str | None = None,
                 active: bool = True,
                 visible: bool = True,
                 children: list[Self] = None,
                 draw_handler: Callable[[Self, Any], None] = None,
                 update_handler: Callable[[Self, float], None] = None,
                 activate_handler: Callable[[Self], None] = None,
                 deactivate_handler: Callable[[Self], None] = None,
                 destroyed_handler: Callable[[Self], None] = None,
                 draw_handlers: list[Callable[[Self, Any], None]] = None,
                 update_handlers: list[Callable[[Self, float], None]] = None,
                 activate_handlers: list[Callable[[Self], None]] = None,
                 deactivate_handlers: list[Callable[[Self], None]] = None,
                 destroyed_handlers: list[Callable[[Self], None]] = None):
        """
        Initialises a GameObjects properties with the provided arguments. All arguments are optional and
        have a corresponding property. The only point of note is that the active property is set twice to
        force on of the activate() or deactivate() methods and corresponding events handlers to be called.

        """
        self.__name: str | None = name
        self.visible: bool = visible
        self.__children: list[Self] = children.copy() if children else []
        self.__draw_handlers: list[
            Callable[[Self, Any], None]] = draw_handlers.copy() if draw_handlers else []
        self.__update_handlers: list[
            Callable[[Self, float], None]] = update_handlers.copy() if update_handlers else []
        self.__activate_handlers: list[
            Callable[[Self], None]] = activate_handlers.copy() if activate_handlers else []
        self.__deactivate_handlers: list[
            Callable[[Self], None]] = deactivate_handlers.copy() if deactivate_handlers else []
        self.__destroyed_handlers: list[
            Callable[[Self], None]] = destroyed_handler.copy() if destroyed_handlers else []
        self.__draw_handlers.append(draw_handler) if draw_handler else None
        self.__update_handlers.append(update_handler) if update_handler else None
        self.__activate_handlers.append(activate_handler) if activate_handler else None
        self.__deactivate_handlers.append(deactivate_handler) if deactivate_handler else None
        self.__destroyed_handlers.append(destroyed_handler) if destroyed_handler else None
        self.destroy: bool = False
        # This forces the active or deactivate events to be called.
        self.__active: bool = not active
        self.active = active

    @property
    def name(self) -> bool | None:
        return self.__name

    @property
    def active(self) -> bool:
        return self.__active

    @active.setter
    def active(self, value):
        if self.__active == value:
            return

        self.__active = value

        if value:
            self.activated()
            for handler in self.__activate_handlers:
                handler(self)
        else:
            self.deactivated()
            for handler in self.__deactivate_handlers:
                handler(self)

        # Propagate the active state to all children.
        for child in self.__children:
            child.active = value

    @property
    def children(self) -> list[Self]:
        return self.__children.copy()

    def add_child(self, child: Self):
        self.__children.append(child)

    def remove_child(self, child: Self):
        self.__children.remove(child)

    def add_draw_handler(self, handler: Callable[[Self, Any], None]):
        self.__draw_handlers.append(handler) if handler else None

    def remove_draw_handler(self, handler: Callable[[Self, Any], None]):
        self.__draw_handlers.remove(handler) if handler else None

    def add_update_handler(self, handler: Callable[[Self, float], None]):
        self.__update_handlers.append(handler) if handler else None

    def remove_update_handler(self, handler: Callable[[Self, float], None]):
        self.__update_handlers.remove(handler) if handler else None

    def add_activate_handler(self, handler: Callable[[Self], None]):
        self.__activate_handlers.append(handler) if handler else None

    def remove_activate_handler(self, handler: Callable[[Self], None]):
        self.__activate_handlers.remove(handler) if handler else None

    def add_deactivate_handler(self, handler: Callable[[Self], None]):
        self.__deactivate_handlers.append(handler) if handler else None

    def remove_deactivate_handler(self, handler: Callable[[Self], None]):
        self.__deactivate_handlers.remove(handler) if handler else None

    def add_destroyed_handler(self, handler: Callable[[Self], None]):
        self.__destroyed_handlers.append(handler) if handler else None

    def remove_destroyed_handler(self, handler: Callable[[Self], None]):
        self.__destroyed_handlers.remove(handler) if handler else None

    def do_draw(self, surface: Any):
        self.draw(surface)
        for handler in self.__draw_handlers:
            handler(self, surface)

        # Draw all active and visible children
        active_children = [
            game_object for game_object in self.__children
            if game_object.active and game_object.visible
        ]

        for child in active_children:
            child.do_draw(surface)

    def do_update(self, dt: float):
        self.update(dt)
        for handler in self.__update_handlers:
            handler(self, dt)

        # Update all active children
        active_children = [
            child for child in self.__children
            if child.active
        ]

        for child in active_children:
            child.do_update(dt)

        # Remove any destroyed children
        children_to_destroy = [
            child for child in self.__children
            if child.destroy
        ]

        self.__children = [
            child for child in self.__children
            if not child.destroy
        ]

        # TODO: Fix destroy handler handling
        for destroyed_child in children_to_destroy:
            destroyed_child.destroyed()
            for handler in destroyed_child.__destroyed_handlers:
                destroyed_child.destroyed_handler(destroyed_child)

    def draw(self, surface: Any):
        pass

    def update(self, dt: float):
        pass

    def activated(self):
        pass

    def deactivated(self):
        pass

    def destroyed(self):
        pass


__root = GameObject()

__background_color: tuple[int, int, int] = (0, 0, 0)


def set_background_colour(colour: tuple[int, int, int]):
    global __background_color
    __background_color = colour


__draw_funcs: list[Callable[[Any], None]] = []


def add_draw_func(func: Callable[[Any], None]):
    __draw_funcs.append(func)


def draw(surface):
    surface.fill(__background_color)
    for draw_func in __draw_funcs:
        draw_func(surface)

    __root.do_draw(surface)


__update_funcs: list[Callable[[float], None]] = []


def add_update_func(func: Callable[[float], None]):
    __update_funcs.append(func)


def update(dt):
    for update_func in __update_funcs:
        update_func(dt)

    __root.do_update(dt)