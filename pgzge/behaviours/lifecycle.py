class DestroySelf(Behaviour):
    def execute(self, dt, sprite):
        sprite.destroy = True