from sprites import Behaviour


class Sequence(Behaviour):
    def __init__(self, *behaviours):
        self.behaviours = behaviours
        self.index = 0

    def execute(self, dt, sprite):
        self.behaviours[self.index].execute(dt, sprite)

    def enabled(self, sprite):
        if not self.behaviours[self.index].enabled(sprite) and self.index < len(self.behaviours) - 1:
            self.index += 1
            return self.enabled(sprite)

        return self.behaviours[self.index].enabled(sprite)


class RemoveWhenFinished(Behaviour):
    def __init__(self, behaviour):
        self.behaviour = behaviour

    def execute(self, dt, sprite):
        self.behaviour.execute(dt, sprite)

    def enabled(self, sprite):
        return self.behaviour.enabled(sprite)

    def remove(self, sprite):
        return not self.behaviour.enabled(sprite)


class Whilst(Behaviour):
    def __init__(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary

    def execute(self, dt, sprite):
        self.primary.execute(dt, sprite)
        self.secondary.execute(dt, sprite)

    def enabled(self, sprite):
        return self.primary.enabled(sprite)


class Exactly(Behaviour):
    def __init__(self, count, behaviour):
        self.count = count
        self.behaviour = behaviour

    def execute(self, dt, sprite):
        self.count -= 1

        self.behaviour.execute(dt, sprite)

    def enabled(self, sprite):
        return self.count > 0


class Callback(Behaviour):
    def __init__(self, func):
        self.func = func

    def execute(self, dt, sprite):
        self.func(dt, sprite)