# TODO: Add type annotations

class Root:
    def __init__(self):
        self.draw_funcs = []
        self.update_funcs = []
        self.game_objects = []

    def draw(self, surface):
        surface.fill(BLACK)
        for draw_func in self.draw_funcs:
            draw_func(surface)

        # Draw all active and visible game objects
        active_game_objects = [
            game_object for game_object in self.game_objects
            if game_object.active and game_object.visible
        ]

        for game_object in active_game_objects:
            game_object.draw(surface)

    def update(self, dt):
        for update_func in self.update_funcs:
            update_func(dt)

        # Update all active game objects
        active_game_objects = [
            game_object for game_object in self.game_objects
            if game_object.active
        ]

        for game_object in active_game_objects:
            game_object.update(dt)

        # Remove any destroyed game objects
        game_objects_to_destroy = [
            game_object for game_object in self.game_objects
            if game_object.destroy
        ]

        game_objects = [
            game_object for game_object in self.game_objects
            if not game_object.destroy
        ]

        for destroyed_game_object in game_objects_to_destroy:
            destroyed_game_object.destroyed()

    # TODO: Add draw func
    # TODO: Add update func
    # TODO: Add game object


class GameObject:
    def __init__(self, activate=True):
        # TODO: Add name
        self._active = not activate  # If this is True, the object will be updated and drawn (if visible is also True).
        self.visible = True  # If this is True, the object will be drawn (if active is also True).
        self.destroy = False  # If this is True, the object will be removed from game_objects and destroy() called.
        self.active = activate

    def draw(self, draw):
        pass

    def update(self, dt):
        pass

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        if self._active != value:
            self._active = value
            if value:
                self.activated()
            else:
                self.deactivated()

    def activated(self):
        pass

    def deactivated(self):
        pass

    # Called when the object is removed from game_objects
    def destroyed(self):
        pass