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
                 destroyed_handler: Callable[[Self], None] = None):
        """
        Initialises a GameObjects properties with the provided arguments. All arguments are optional and
        have a corresponding property. The only point of note is that the active property is set twice to
        force on of the activate() or deactivate() methods and corresponding events handlers to be called.

        """
        self.__name: str | None = name
        self.visible: bool = visible
        self.__children: list[Self] = children.copy() if children else []
        self.draw_handler: Callable[[Self, Any], None] = draw_handler
        self.update_handler: Callable[[Self, float], None] = update_handler
        self.activate_handler: Callable[[Self], None] = activate_handler
        self.deactivate_handler: Callable[[Self], None] = deactivate_handler
        self.destroyed_handler: Callable[[Self], None] = destroyed_handler
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
            if self.activate_handler:
                self.activate_handler(self)
        else:
            self.deactivated()
            if self.deactivate_handler:
                self.deactivate_handler(self)

    @property
    def children(self) -> list[Self]:
        return self.__children.copy()

    def add_child(self, child: Self):
        self.__children.append(child)

    def remove_child(self, child: Self):
        self.__children.remove(child)

    def do_draw(self, surface: Any):
        self.draw(surface)
        if self.draw_handler:
            self.draw_handler(self, surface)

        # Draw all active and visible children
        active_children = [
            game_object for game_object in self.__children
            if game_object.active and game_object.visible
        ]

        for child in active_children:
            child.do_draw(surface)

    def do_update(self, dt: float):
        self.update(dt)
        if self.update_handler:
            self.update_handler(self, dt)

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

        for destroyed_child in children_to_destroy:
            destroyed_child.destroyed()
            if destroyed_child.destroyed_handler:
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