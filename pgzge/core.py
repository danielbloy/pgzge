from collections.abc import Callable
from typing import Self, Any


class GameObject:
    """
    GameObject is the base class for all objects in the game. It provides a simple parent/child structure
    for updating and drawing GameObjects as well as a simple way to manage active and visible states.

    A GameObject has the following properties:
        * name: The name of this object. Used when locating an object by name. Must not contain the `/`
                or `.` characters.
        * active: This has to be True for the the GameObject to be updated or drawn (visible and
                  enabled also need to be True). The value of active is propagated to all children.
                  Changing active will also trigger the corresponding handlers.
        * destroy: If this is True, the object will be removed from its parent at the next update.
                   When set to True, the corresponding handlers will be triggered and the destroy
                   state will be propagated to all children.
        * enabled: If this is True and active is also True, the object will be updated. This is not
                   propagated to children.
        * visible: If this is True and active is also True, the object will be drawn. This is not
                   propagated to children.
        * parent: The parent GameObject. This is None if the GameObject has no parent. A GameObject
                  can only have one parent and it is an error to add a GameObject as a child to
                  multiple parents.
        * children: A list of child GameObjects. These will be updated and drawn only if this
                    GameObject is active.
        * draw_handlers: Draw handlers are called during `draw()` if the GameObject is active and visible.
        * update_handlers: Update handlers are called during `update()` if the GameObject is active and enabled.
        * activate_handlers = Activate handlers are called when active changes from False to True.
        * deactivate_handlers = Deactivate handlers are called when active changes from True to False.
        * destroy_handlers = Destroy handlers are called when `destroy()` is called on the GameObject.

        The `update()` and `draw()` methods propagate down the hierarchy if active is True and regardless of
        visible and active which only apply to this GameObject instance. i.e. a child can be enabled and
        visible even if the parent is not.

        Destroy, activate and deactivate are propagated to all children irrespective of whether active is
        True or False. All handlers are called before passing to the children except for destroy which
        propagates to the children first. In the case of activate and deactivate, the `activate()` and
        `deactivate()` methods are called before any handlers.

        The handlers can be used to provide instance specific behaviour without having to make a subclass
        and override the relevant method.
    """

    def __init__(self,
                 name: str | None = None,
                 active: bool = True,
                 enabled: bool = True,
                 visible: bool = True,
                 children: list[Self] = None,
                 draw_handler: Callable[[Self, Any], None] = None,
                 update_handler: Callable[[Self, float], None] = None,
                 activate_handler: Callable[[Self], None] = None,
                 deactivate_handler: Callable[[Self], None] = None,
                 destroy_handler: Callable[[Self], None] = None,
                 draw_handlers: list[Callable[[Self, Any], None]] = None,
                 update_handlers: list[Callable[[Self, float], None]] = None,
                 activate_handlers: list[Callable[[Self], None]] = None,
                 deactivate_handlers: list[Callable[[Self], None]] = None,
                 destroy_handlers: list[Callable[[Self], None]] = None):
        """
        Initialises a GameObjects properties with the provided arguments. All arguments are optional and
        have a corresponding property. The only point of note is that the active property is set twice to
        force on of the activate() or deactivate() methods and corresponding events handlers to be called.

        """
        self.__parent: Self | None = None
        self.__name: str | None = name
        self.visible: bool = visible
        self.enabled: bool = enabled
        self.__children: list[Self] = children.copy() if children else []
        self.__draw_handlers: list[
            Callable[[Self, Any], None]] = draw_handlers.copy() if draw_handlers else []
        self.__update_handlers: list[
            Callable[[Self, float], None]] = update_handlers.copy() if update_handlers else []
        self.__activate_handlers: list[
            Callable[[Self], None]] = activate_handlers.copy() if activate_handlers else []
        self.__deactivate_handlers: list[
            Callable[[Self], None]] = deactivate_handlers.copy() if deactivate_handlers else []
        self.__destroy_handlers: list[
            Callable[[Self], None]] = destroy_handlers.copy() if destroy_handlers else []
        self.__draw_handlers.append(draw_handler) if draw_handler else None
        self.__update_handlers.append(update_handler) if update_handler else None
        self.__activate_handlers.append(activate_handler) if activate_handler else None
        self.__deactivate_handlers.append(deactivate_handler) if deactivate_handler else None
        self.__destroy_handlers.append(destroy_handler) if destroy_handler else None
        self.__destroyed: bool = False
        # This forces the active or deactivate events to be called.
        self.__active: bool = not active
        self.active = active

    @property
    def name(self) -> bool | None:
        """
        The name of this GameObject or None if the GameObject has no name. It should not contain the `/` or
        `.`` characters. It is used when locating an object by name.

        :return: The name of this GameObject or None if the GameObject has no name.
        """
        return self.__name

    @property
    def active(self) -> bool:
        """"
        Returns whether the GameObject is active or not.
        """
        return self.__active

    @active.setter
    def active(self, value: bool) -> None:
        """
        Setting active to True or False will activate or deactivate the object (only if the new active state
        is different to the current active state). The active value is propagated to all children. In the
        case where this object is `destroyed` then no action is taken.
        """
        # Cannot activate a destroyed GameObject.
        if self.__destroyed:
            return

        do_handlers = self.__active != value

        self.__active = value

        if do_handlers:
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

    def activated(self) -> Self:
        """
        This is called when the GameObject is activated. It provides an easy way for subclasses to provide
        activation code without using handlers.
        """
        return self

    def deactivated(self) -> Self:
        """
        This is called when the GameObject is deactivated. It provides an easy way for subclasses to provide
        deactivation code without using handlers.
        """
        return self

    def activate(self) -> Self:
        """
        Activates the GameObject. This will trigger the activate handlers and propagate the active state to
        all children. This is a shorthand version of `self.active = True` but also returns the GameObject.
        """
        self.active = True
        return self

    def deactivate(self) -> Self:
        """
        Deactivates the GameObject. This will trigger the deactivate handlers and propagate the active state to
        all children. This is a shorthand version of `self.active = False` but also returns the GameObject.
        """
        self.active = False
        return self

    @property
    def destroyed(self) -> bool:
        """
        Returns whether this object has been destroyed or not.
        """
        return self.__destroyed

    def destroy(self) -> None:
        """
        Destroys the object, propagating to all children before the handlers for this object are triggered.
        This will deactivate the object prior to destruction.
        """

        # Propagate the destroy state to all children.
        for child in self.__children:
            child.destroy()

        if self.__destroyed:
            return

        self.deactivate()
        self.__destroyed = True

        for handler in self.__destroy_handlers:
            handler(self)

    @property
    def parent(self) -> Self | None:
        """
        The parent GameObject or None if this GameObject has no parent.
        """
        return self.__parent

    @property
    def children(self) -> list[Self]:
        """
        Returns all the children of this GameObject. If there are no children, an empty list
        is returned.
        """
        return self.__children.copy()

    def add_child(self, child: Self) -> Self:
        """
        Adds a GameObject as a child of this GameObject. If the child object already has a parent an
        error will be raised. This will set the parent of the child to this GameObject.
        """
        if not child:
            return self

        if child.__parent:
            raise ValueError("child already has a parent")

        child.__parent = self
        self.__children.append(child)
        return self

    def remove_child(self, child: Self) -> Self:
        """
        Removes a GameObject as a child of this GameObject. If the childs parent is not this GameObject
         then an error will be raised (an exception to this is if the child has no parent).
        """
        # If this child does not have a parent, ignore.
        if not child or not child.__parent:
            return self

        if child.__parent != self:
            raise ValueError("child is not a child of this GameObject")

        child.__parent = None
        self.__children.remove(child)
        return self

    def draw(self, surface: Any) -> Self:
        """
        Draws the GameObject (if `active` and `visible`) and propagates to children (if `active`).
        """
        if not self.active:
            return self

        if self.visible:
            for handler in self.__draw_handlers:
                handler(self, surface)

        for child in self.__children:
            child.draw(surface)

        return self

    def update(self, dt: float) -> Self:
        """
        Updates the GameObject (if `active` and `enabled`) and propagates to children (if `active`).
        Also removes any destroyed children.
        """

        # Remove any destroyed children.
        destroyed_children = [
            child for child in self.__children
            if child.destroyed
        ]
        for child in destroyed_children:
            child.__parent = None

        self.__children = [
            child for child in self.__children
            if not child.destroyed
        ]

        if not self.active:
            return self

        if self.enabled:
            for handler in self.__update_handlers:
                handler(self, dt)

        for child in self.__children:
            child.update(dt)

        return self

    def add_draw_handler(self, handler: Callable[[Self, Any], None]) -> Self:
        """Adds a `draw` handler."""
        self.__draw_handlers.append(handler) if handler else None
        return self

    def remove_draw_handler(self, handler: Callable[[Self, Any], None]) -> Self:
        """Removes a `draw` handler."""
        self.__draw_handlers.remove(handler) if handler else None
        return self

    def add_update_handler(self, handler: Callable[[Self, float], None]) -> Self:
        """Adds a `update` handler."""
        self.__update_handlers.append(handler) if handler else None
        return self

    def remove_update_handler(self, handler: Callable[[Self, float], None]) -> Self:
        """Removes a `update` handler."""
        self.__update_handlers.remove(handler) if handler else None
        return self

    def add_activate_handler(self, handler: Callable[[Self], None]) -> Self:
        """Adds a `activate` handler."""
        self.__activate_handlers.append(handler) if handler else None
        return self

    def remove_activate_handler(self, handler: Callable[[Self], None]) -> Self:
        """Removes a `activate` handler."""
        self.__activate_handlers.remove(handler) if handler else None
        return self

    def add_deactivate_handler(self, handler: Callable[[Self], None]) -> Self:
        """Adds a `deactivate` handler."""
        self.__deactivate_handlers.append(handler) if handler else None
        return self

    def remove_deactivate_handler(self, handler: Callable[[Self], None]) -> Self:
        """Removes a `deactivate` handler."""
        self.__deactivate_handlers.remove(handler) if handler else None
        return self

    def add_destroy_handler(self, handler: Callable[[Self], None]) -> Self:
        """Adds a `destroy` handler."""
        self.__destroy_handlers.append(handler) if handler else None
        return self

    def remove_destroy_handler(self, handler: Callable[[Self], None]) -> Self:
        """Removes a `destroy` handler."""
        self.__destroy_handlers.remove(handler) if handler else None
        return self


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

    __root.draw(surface)


__update_funcs: list[Callable[[float], None]] = []


def add_update_func(func: Callable[[float], None]):
    __update_funcs.append(func)


def update(dt):
    for update_func in __update_funcs:
        update_func(dt)

    __root.update(dt)
