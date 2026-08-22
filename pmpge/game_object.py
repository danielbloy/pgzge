from pmpge.environment import is_running_on_desktop

# These are not available in CircuitPython.
if is_running_on_desktop():
    from collections.abc import Callable
    from typing import Self, Any


class GameObject:
    """
    GameObject is the base class for all objects in the game. It provides a simple parent/child
    structure for updating and drawing GameObjects as well as a simple way to manage active and
    visible states.

    A GameObject has the following built-in properties:
        * name: The name of this object. Used when locating an object by name. Must not contain the
                `/` or `.` characters.
        * active: This has to be True for the GameObject to be updated or drawn (visible and
                  enabled also need to be True). The value of active is propagated to all children.
                  Changing active will also trigger the corresponding handlers.
        * alive: If this is False, the object will be removed from its parent at the next update.
                 Can only be set to False by calling destroy(). When set to False, the corresponding
                 handlers will be triggered and destroy will be propagated to all children.
        * enabled: If this is True and active is also True, the object will be updated. This is not
                   propagated to children. Enabled only ever impacts this GameObject, even during
                   updates (i.e. updates are still propagated to children even if this is False).
        * visible: If this is True and active is also True, the object will be drawn. This is not
                   propagated to children.
        * parent: The parent GameObject. This is None if the GameObject has no parent. A GameObject
                  can only have one parent. It is an error to add a GameObject as a child to
                  multiple parents.
        * children: A list of child GameObjects. These will be updated and drawn only if this
                    GameObject is active.

    A GameObject also provides a set of events that can have handlers attached to them. The handlers
    can be used to provide instance-specific behaviour without having to make a subclass and
    override one of the `draw()`, `update()`, `activate()`, `deactivate()` or destroyed() methods.
    These handlers are also used with Traits (see later).
        * draw_handlers: Draw handlers are called during `draw_hierarchy()` if the GameObject is
          active and visible.
        * update_handlers: Update handlers are called during `update_hierarchy()` if the GameObject
          is active and enabled.
        * activate_handlers = Activate handlers are called when active changes from False to True.
        * deactivate_handlers = Deactivate handlers are called when active changes from True to
          False.
        * destroy_handlers = Destroy handlers are called when `destroy()` is called on the
          GameObject.

    The `update_hierarchy()` and `draw_hierarchy()` functions propagate down the hierarchy if
    active is True and regardless of the visible and active properties (which only apply to this
    GameObject instance). i.e. a child can be enabled or visible even if the parent is not. See
    those functions for more details on how they traverse the hierarchy.

    Destroy, activate and deactivate are propagated to all children irrespective of whether
    active is True or False. All handlers are called before passing to the children except for
    destroy which propagates to the children first.

    The `draw()`, `update()`, `activate()`, `deactivate()` and destroyed() methods are called before
    any handlers.

    GameObjects can also have traits applied to them. Traits are a kind of Mixin and used as a way
    to apply behaviour to a GameObject without subclassing. Traits make use of the handlers. When a
    trait is "applied" to a GameObject, all variables are copied from the trait instance to the
    GameObject and if any of the following methods are present on the trait instance, they are copied
    across to the relevant handler too. This mechanism allows traits to depend on other traits and
    access the same state. Methods that are attached to the GameObjects handlers:
        * draw()
        * update()
        * activated()
        * deactivated()
        * destroyed()

    When a trait is "applied", it will have either the `activated()` or `deactivated()` method called
    based on the state of the GameObject. Finally, if a `merged()` method is present on the trait,
    that will be called.

    Traits are not a complete replacement for subclassing because the entire object is not copied across.
    For example, methods, property getter and setter methods. For an example of a subclass using traits,
    see the Sprite class.
    """
    _parent: Self | None
    _name: str | None
    _active: bool
    visible: bool
    enabled: bool
    _children: list[Self]
    _alive: bool
    _has_dead_child: bool

    _draw_handlers: list[Callable[[Self, Any], None]]
    _update_handlers: list[Callable[[Self, float], None]]
    _activate_handlers: list[Callable[[Self], None]]
    _deactivate_handlers: list[Callable[[Self], None]]
    _destroy_handlers: list[Callable[[Self], None]]

    def __init__(self,
                 *traits,
                 name: str | None = None,
                 active: bool = True,
                 enabled: bool = True,
                 visible: bool = True,
                 parent: Self | None = None,
                 children: list[Self] | None = None,
                 draw_handler: Callable[[Self, Any], None] | None = None,
                 update_handler: Callable[[Self, float], None] | None = None,
                 activate_handler: Callable[[Self], None] | None = None,
                 deactivate_handler: Callable[[Self], None] | None = None,
                 destroy_handler: Callable[[Self], None] | None = None,
                 draw_handlers: list[Callable[[Self, Any], None]] | None = None,
                 update_handlers: list[Callable[[Self, float], None]] | None = None,
                 activate_handlers: list[Callable[[Self], None]] | None = None,
                 deactivate_handlers: list[Callable[[Self], None]] | None = None,
                 destroy_handlers: list[Callable[[Self], None]] | None = None):
        """
        Initialises a GameObjects properties with the provided arguments. All arguments are optional
        and have a corresponding property. The only point of note is that the active property is set
        twice to force on of the activate() or deactivate() methods and corresponding events
        handlers to be called.
        """
        self._parent = None
        self._name = name
        self.visible = visible
        self.enabled = enabled
        self._children = []
        self._alive = True
        self._has_dead_child = False

        # Copy across the handler lists first; this creates empty lists if there are no
        # handler lists specified.
        self._draw_handlers = draw_handlers.copy() if draw_handlers else []
        self._update_handlers = update_handlers.copy() if update_handlers else []
        self._activate_handlers = activate_handlers.copy() if activate_handlers else []
        self._deactivate_handlers = deactivate_handlers.copy() if deactivate_handlers else []
        self._destroy_handlers = destroy_handlers.copy() if destroy_handlers else []

        # Now add the individual handlers.
        self._draw_handlers.append(draw_handler) if draw_handler else None
        self._update_handlers.append(update_handler) if update_handler else None
        self._activate_handlers.append(activate_handler) if activate_handler else None
        self._deactivate_handlers.append(deactivate_handler) if deactivate_handler else None
        self._destroy_handlers.append(destroy_handler) if destroy_handler else None

        # Now add the parent and children before the activate or deactivate events.
        if parent:
            parent.add_child(self)

        if children:
            for child in children:
                self.add_child(child)

        # This forces the active or deactivate events to be called.
        self._active: bool = not active
        self.active = active

        # Add in the traits after triggering the active or deactivate events. This has to be
        # done here as we need the active state to determine which trait methods to call.
        for trait in traits:
            self.apply_trait(trait)

    @property
    def name(self) -> str | None:
        """
        The name of this GameObject or None if the GameObject has no name. It should not contain the
        `/` or `.`` characters. It is used when locating an object by name.

        :return: The name of this GameObject or None if the GameObject has no name.
        """
        return self._name

    @property
    def active(self) -> bool:
        """"
        Returns whether the GameObject is active or not.
        """
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        """
        Setting active to True or False will activate or deactivate the object (only if the new
        active state is different to the current active state). The active value is propagated to
        all children. In the case where this object is `destroyed` then no action is taken.

        A child cannot be activated if its parent is deactivated.
        """
        # Cannot activate a destroyed GameObject.
        if not self._alive:
            return

        if value:
            parent = self._parent
            if parent is not None and not parent._active:
                raise ValueError("Cannot activate a child with deactivated parent")

        do_handlers = self._active != value

        self._active = value

        if do_handlers:
            if value:
                self.activated()
                for handler in self._activate_handlers:
                    handler(self)
            else:
                self.deactivated()
                for handler in self._deactivate_handlers:
                    handler(self)

        # Propagate the active state to all children.
        for child in self._children:
            child.active = value

    def activated(self) -> None:
        """
        This is called when the GameObject is activated. It provides an easy way for subclasses to
        provide activation code without using handlers.
        """
        pass

    def deactivated(self) -> None:
        """
        This is called when the GameObject is deactivated. It provides an easy way for subclasses to
        provide deactivation code without using handlers.
        """
        pass

    def activate(self) -> Self:
        """
        Activates the GameObject. This will trigger the activate handlers and propagate the active
        state to all children. This is a shorthand version of `self.active = True` but also returns
        the GameObject.
        """
        self.active = True
        return self

    def deactivate(self) -> Self:
        """
        Deactivates the GameObject. This will trigger the deactivate handlers and propagate the
        active state to all children. This is a shorthand version of `self.active = False` but also
        returns the GameObject.
        """
        self.active = False
        return self

    def reset(self) -> Self:
        """
        Convenience method to toggle the active state of the GameObject to trigger the corresponding
        handlers. If the GameObject is active, it will be deactivated and then activated again. If
        the GameObject is deactivated, it will be activated and then deactivated again.
        """
        if self.active:
            self.deactivate().activate()
        else:
            self.activate().deactivate()

        return self

    @property
    def disabled(self) -> bool:
        """
        Returns whether this object is disabled or not. This is the opposite of enabled.
        """
        return not self.enabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        """
        Sets whether this object is disabled or not. This is the opposite of enabled.
        """
        self.enabled = not value

    @property
    def alive(self) -> bool:
        """
        Returns whether this object is alive or not. An alive object is not destroyed.
        """
        return self._alive

    # This class variable is used to optimise the automatic pruning of the
    # hierarchy during updates.
    something_destroyed: bool = False

    def destroy(self) -> None:
        """
        Destroys the object, propagating to all children before the handlers for this object are
        triggered. Starting from the leaf nodes, each object will be deactivated and then destroyed
        in turn; the sequence of events is thus:
         * deactivate child
         * destroy child
         * deactivate parent
         * destroy parent
        """

        # Propagate the deactivated state to all children.
        for child in self._children:
            child.destroy()

        if not self._alive:
            return

        GameObject.something_destroyed = True
        self.deactivate()
        self._alive = False

        # Flags the parent to prune its _children list on the next update_hierarchy()
        # pass, instead of every GameObject in the tree rebuilding its _children list
        # whenever anything died anywhere.
        parent = self._parent
        if parent is not None:
            parent._has_dead_child = True

        self.destroyed()
        for handler in self._destroy_handlers:
            handler(self)

    def destroyed(self) -> None:
        """
        This is called when the GameObject is destroyed. It provides an easy way for subclasses to
        provide destruction code without using handlers.
        """
        pass

    @property
    def parent(self) -> Self | None:
        """
        The parent GameObject or None if this GameObject has no parent.
        """
        return self._parent

    @property
    def children(self) -> list[Self]:
        """
        Returns all the children of this GameObject. If there are no children, an empty list
        is returned.
        """
        return self._children

    def add_child(self, child: Self) -> Self:
        """
        Adds a GameObject as a child of this GameObject. If the child object already has a parent an
        error will be raised. This will set the parent of the child to this GameObject.
        """
        if not child:
            return self

        if child._parent:
            if child._parent == self:
                return self

            raise ValueError("child already has a parent")

        child._parent = self
        self._children.append(child)
        return self

    def remove_child(self, child: Self) -> Self:
        """
        Removes a GameObject as a child of this GameObject. If the childs parent is not this
        GameObject then an error will be raised (an exception to this is if the child has no
        parent).
        """
        # If this child does not have a parent, ignore.
        if not child or not child._parent:
            return self

        if child._parent != self:
            raise ValueError("child is not a child of this GameObject")

        child._parent = None
        self._children.remove(child)
        return self

    def _draw(self, surface: Any) -> None:
        """
        This internal method will call all the draw methods irrespective of the GameObject's
        visibility.
        """
        self.draw(surface)
        for handler in self._draw_handlers:
            handler(self, surface)

    def draw(self, surface: Any) -> None:
        """
        This is called when the GameObject is drawn. It provides an easy way for subclasses to
        provide draw code without using handlers and without having to remember to call the
        superclass.
        """
        pass

    def update(self, dt: float) -> None:
        """
        This is called when the GameObject is updated. It provides an easy way for subclasses to
        provide update code without using handlers and without having to remember to call the
        superclass.
        """
        pass

    def add_draw_handler(self, handler: Callable[[Self, Any], None]) -> Self:
        """Adds a `draw` handler."""
        # noinspection PyTypeChecker
        self._draw_handlers.append(handler) if handler else None
        return self

    def remove_draw_handler(self, handler: Callable[[Self, Any], None]) -> Self:
        """Removes a `draw` handler."""
        if handler and handler in self._draw_handlers:
            # noinspection PyTypeChecker
            self._draw_handlers.remove(handler)
        return self

    def add_update_handler(self, handler: Callable[[Self, float], None]) -> Self:
        """Adds a `update` handler."""
        # noinspection PyTypeChecker
        self._update_handlers.append(handler) if handler else None
        return self

    def remove_update_handler(self, handler: Callable[[Self, float], None]) -> Self:
        """Removes a `update` handler."""
        if handler and handler in self._update_handlers:
            # noinspection PyTypeChecker
            self._update_handlers.remove(handler)
        return self

    def add_activate_handler(self, handler: Callable[[Self], None]) -> Self:
        """Adds a `activate` handler."""
        # noinspection PyTypeChecker
        self._activate_handlers.append(handler) if handler else None
        return self

    def remove_activate_handler(self, handler: Callable[[Self], None]) -> Self:
        """Removes a `activate` handler."""
        if handler and handler in self._activate_handlers:
            # noinspection PyTypeChecker
            self._activate_handlers.remove(handler)
        return self

    def add_deactivate_handler(self, handler: Callable[[Self], None]) -> Self:
        """Adds a `deactivate` handler."""
        # noinspection PyTypeChecker
        self._deactivate_handlers.append(handler) if handler else None
        return self

    def remove_deactivate_handler(self, handler: Callable[[Self], None]) -> Self:
        """Removes a `deactivate` handler."""
        if handler and handler in self._deactivate_handlers:
            # noinspection PyTypeChecker
            self._deactivate_handlers.remove(handler)
        return self

    def add_destroy_handler(self, handler: Callable[[Self], None]) -> Self:
        """Adds a `destroy` handler."""
        # noinspection PyTypeChecker
        self._destroy_handlers.append(handler) if handler else None
        return self

    def remove_destroy_handler(self, handler: Callable[[Self], None]) -> Self:
        """Removes a `destroy` handler."""
        if handler and handler in self._destroy_handlers:
            # noinspection PyTypeChecker
            self._destroy_handlers.remove(handler)
        return self

    not_allowed_attributes = frozenset(['draw', 'update', 'activated', 'deactivated', 'destroyed', 'merged'])

    def apply_trait(self, trait: Any) -> Self:
        """
        Merge the properties and handlers of a trait object into this GameObject. It will
        not merge across methods or property getter and setters. For that you will need to
        define a subclass of GameObject.

        When a trait is "applied", it will have either the `activated()` or `deactivated()`
        method called based on the state of the GameObject.

        Finally, if a `merged()` method is present on the trait, that will be called.
        """
        if isinstance(trait, type):
            trait.__init__(self)
            cls = trait
        else:
            # Copy across attributes
            for attribute in dir(trait):
                if attribute.startswith('__') or attribute in GameObject.not_allowed_attributes:
                    continue
                setattr(self, attribute, getattr(trait, attribute))
            cls = trait.__class__

        if hasattr(cls, 'draw'):
            self.add_draw_handler(cls.draw)

        if hasattr(cls, 'update'):
            self.add_update_handler(cls.update)

        if hasattr(cls, 'activated'):
            self.add_activate_handler(cls.activated)

        if hasattr(cls, 'deactivated'):
            self.add_deactivate_handler(cls.deactivated)

        if hasattr(cls, 'destroyed'):
            self.add_destroy_handler(cls.destroyed)

        # Trigger activate and/or deactivate handlers on the combined game_object if they exist.
        if hasattr(cls, 'activated') and self.active:
            cls.activated(self)

        if hasattr(cls, 'deactivated') and not self.active:
            cls.deactivated(self)

        # Finally trigger the merge handler.
        if hasattr(cls, 'merged'):
            cls.merged(self)

        return self


# ********************************************************************************
# H I E R A R C H Y    T R A V E R S A L    B A S E D    F U N C T I O N S
# ********************************************************************************
#
# The following functions are used to traverse the hierarchy. There is a general purpose
# traversal function and two specific versions, optimised for either drawing or updating
# the hierarchy. In all cases, the order of visiting each  GameObject in the hierarchy
# is the same and represents the Z-order of the GameObjects (whilst still respecting the
# active, enabled and visible properties as described below).
#
# The order of visiting the GameObjects is by "level" in the hierarchy: root, children,
# grandchildren, great-grandchildren etc. So to explain, the root is visited first. Then
# each of the children of the root in the order they were added to the root. Then each of
# the grandchildren (children of the roots children). The order of visiting is taking
# each child in turn and visiting their children (grandchildren) in the order they were
# added to their parent. This same pattern follows for each subsequent layer. This does
# mean each layer gets progressively larger than that before. It also means that each
# level further from the root is drawn on top of all previous layers.
#
# NOTE: Strictly speaking, Z-order is a little bit more finessed than the order we visit
#       GameObjects in the hierarchy. The finesse is dependent on the graphics driver and
#       how it is implemented. For example, considering a hierarchy that just has images,
#       the Z-order for GameObjects is actually calculated after game initialisation based
#       on the hierarchy at that time. Therefore, significantly changing the hierarchy
#       structure by changing parent can mess up the z-order. This is why there is the
#       game_object_hierarchy_changed() method to recalculate the hierarchy.
#
# A GameObject has the following built-in properties that interact:
#
#   * active: This has to be True for the GameObject to be updated or drawn (visible
#             and enabled also need to be True). The value of a parents active property
#             does affect its children; i.e., if the parent is inactive, the children
#             as also inactive.
#   * enabled: If this is True and active is also True, the object will be updated. This
#              is not cascaded to children.
#   * visible: If this is True and active is also True, the object will be drawn. This is
#              not cascaded to children.
#


# noinspection PyProtectedMember
def update_hierarchy(root: GameObject, dt: float):
    """
    Updates the GameObject (if `active` and `enabled`) and propagates to children (if `active`).
    Also removes any destroyed children. This doesn't use traverse_hierarchy() as it is slower.
    """
    current = [root]
    children = []
    while current:
        for go in current:

            # Only this GameObject's own dead children trigger a rebuild — avoids
            # reallocating _children for every parent in the tree whenever anything
            # died anywhere (see destroy()'s _has_dead_child flag).
            if go._has_dead_child:
                alive_children = []
                for child in go._children:
                    if child._alive:
                        alive_children.append(child)
                    else:
                        child._parent = None

                # noinspection PyTypeChecker
                go._children = alive_children
                go._has_dead_child = False

            if not go._active:
                continue

            if go.enabled:
                go.update(dt)
                for handler in go._update_handlers:
                    handler(go, dt)

            children.extend(go._children)

        # Now populate the next level
        current.clear()
        current, children = children, current

    GameObject.something_destroyed = False


# noinspection PyProtectedMember
def draw_hierarchy(root: GameObject, surface: Any, draw_only_visible: bool = True):
    """
    Draws the GameObject (if `active` and `visible` - see below) and propagates to children
    (if `active`). The parameter `draw_only_visible` is used to control what gets drawn. By
    default, only `visible` items get drawn but setting draw_only_visible to False will also
    draw items that are invisible (though they still need to be `active`). Why this functionality?
    this is because some drivers don't actually draw anything but rather set properties on
    graphics objects so need to be able to do that with the entire hierarchy.

    The surface is passed down through all objects but does not need to be a Pygame surface.
    This doesn't use traverse_hierarchy() as it is slower.
    """
    draw_everything = not draw_only_visible

    current = [root]
    children = []

    while current:

        # Cycle through this level
        for go in current:
            if not go._active:
                continue

            if draw_everything or go.visible:
                go._draw(surface)

            children.extend(go._children)

        # Now populate the next level
        current.clear()
        current, children = children, current


# noinspection PyProtectedMember
def traverse_hierarchy(
        root: GameObject, func: Callable[[GameObject, Any], tuple[bool, Any]], initial_state: Any = None):
    """
    Provides a way to traverse the entire hierarchy, executing a function on
    each node and passing state. The `func` accepts two parameters:
    * The GameObject instance.
    * Some state (which can be `None`).

    The `func` returns two values:
    * A boolean indicating whether to process nodes children or not.
    * A new value for state to be passed to the children (which can be `None`)

    The GameObject that `traverse_hierarchy` is called on is always processed.
    """

    current = [(root, initial_state)]
    children = []
    while current:

        for go, state in current:
            process_children, new_state = func(go, state)
            if process_children:
                children.extend([(child, new_state) for child in go._children])

        # Now populate the next level
        current.clear()
        current, children = children, current
