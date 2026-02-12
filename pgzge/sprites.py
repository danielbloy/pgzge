class Behaviour:
    def enabled(self, sprite):
        return True

    def execute(self, dt, sprite):
        pass

    def remove(self, sprite):
        return False


# TODO: Move many of the properties to GameObject


class Sprite(GameObject):
    def __init__(self, position, images, *behaviours):
        super().__init__()
        self.lifetime = None
        self.fps = 2
        self.images = images
        self.next_frame = -1
        self.frame = -1
        self.actor = Actor(images[0], position)
        self.behaviours = behaviours

    def activated(self):
        self.next_frame = -1
        self.frame = -1

    def add_behaviour(self, behaviour):
        self.behaviours += behaviour,

    @property
    def pos(self):
        return self.actor.pos

    @pos.setter
    def pos(self, pos):
        self.actor.pos = pos

    def animate(self):
        now = time.time_ns()

        if now > self.next_frame:
            self.frame = (self.frame + 1) % len(self.images)
            self.actor.image = self.images[self.frame]
            self.next_frame = now + (1_000_000_000 / self.fps)

    def draw(self, draw):
        self.actor.draw()

    def update(self, dt):
        if self.lifetime:
            self.lifetime -= dt
            if self.lifetime <= 0:
                self.destroy = True
                return

        self.animate()

        self.behaviours = [
            behaviour for behaviour in self.behaviours
            if not behaviour.remove(self)
        ]
        for behaviour in self.behaviours:
            if behaviour.enabled(self):
                behaviour.execute(dt, self)