from sprites import Behaviour


class DestroySelf(Behaviour):
    def execute(self, dt, sprite):
        sprite.destroy = True