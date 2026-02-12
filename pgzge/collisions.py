from core import GameObject


class SpriteCollisions(GameObject):

    def __init__(self):
        super().__init__()
        self.detections = []

    def update(self, dt):
        for sprites1, sprites2, callback in self.detections:

            for sprite1 in sprites1():
                for sprite2 in sprites2():
                    if sprite1.destroy or sprite2.destroy:
                        continue

                    if sprite1.actor.colliderect(sprite2.actor):
                        callback(sprite1, sprite2)

    def add_detection(self, sprites1, sprites2, callback):
        self.detections.append((sprites1, sprites2, callback))