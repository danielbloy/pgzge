from pgzero.keyboard import Keyboard

from sprites import Behaviour

keyboard: Keyboard


class MovePlayer(Behaviour):
    def execute(self, dt, sprite):

        new_pos = sprite.pos
        if keyboard.a or keyboard.left:
            new_pos = (new_pos[0] - (sprite.vx * dt), new_pos[1])
        elif keyboard.d or keyboard.right:
            new_pos = (new_pos[0] + (sprite.vx * dt), new_pos[1])

        if new_pos[0] < sprite.max_left:
            new_pos = (sprite.max_left, new_pos[1])
        elif new_pos[0] > sprite.max_right:
            new_pos = (sprite.max_right, new_pos[1])

        sprite.pos = new_pos


class Move(Behaviour):
    def __init__(self, offset, velocity):
        self.offset_x = offset[0]
        self.offset_y = offset[1]
        self.x_left = abs(self.offset_x)
        self.y_left = abs(self.offset_y)
        self.velocity = velocity

    def execute(self, dt, sprite):
        x = abs(self.velocity[0] * dt)
        y = abs(self.velocity[1] * dt)

        if self.x_left <= 0:
            x = 0
        if self.y_left <= 0:
            y = 0

        if x > self.x_left:
            x = self.x_left

        if y > self.y_left:
            y = self.y_left

        self.x_left -= x
        self.y_left -= y

        if self.offset_x < 0:
            x = -x

        if self.offset_y < 0:
            y = -y

        pos = sprite.pos
        sprite.pos = pos[0] + x, pos[1] + y

    def enabled(self, sprite):
        return self.x_left > 0 or self.y_left > 0


class CalculatedPosition(Behaviour):
    def __init__(self, x_func=None, y_func=None):
        self.x_func = x_func
        self.y_func = y_func
        self.elapsed = 0

    def execute(self, dt, sprite):
        self.elapsed += dt

        new_x, new_y = sprite.pos[0], sprite.pos[1]
        if self.x_func:
            new_x = self.x_func(self.elapsed)

        if self.y_func:
            new_y = self.y_func(self.elapsed)

        sprite.pos = new_x, new_y


class RelativeToNow(Behaviour):
    def __init__(self, behaviour):
        self.start_pos = None
        self.behaviour = behaviour

    def execute(self, dt, sprite):
        if self.start_pos is None:
            self.start_pos = sprite.pos

        self.behaviour.execute(dt, sprite)

        sprite.pos = (
            self.start_pos[0] + sprite.pos[0],
            self.start_pos[1] + sprite.pos[1]
        )

    def enabled(self, sprite):
        return self.behaviour.enabled(sprite)


class RelativeToNowOnlyX(Behaviour):
    def __init__(self, behaviour):
        self.start_pos = None
        self.behaviour = behaviour

    def execute(self, dt, sprite):
        if self.start_pos is None:
            self.start_pos = sprite.pos

        pos = sprite.pos
        self.behaviour.execute(dt, sprite)

        sprite.pos = self.start_pos[0] + sprite.pos[0], pos[1]

    def enabled(self, sprite):
        return self.behaviour.enabled(sprite)


class ReturnToNormalPosition(Behaviour):
    def __init__(self, velocity):
        self.velocity = velocity

    def execute(self, dt, sprite):
        new_x = 0
        new_y = 0
        if sprite.pos[0] > sprite.normal_pos[0]:
            new_x = sprite.pos[0] - (self.velocity[0] * dt)
            if new_x < sprite.normal_pos[0]:
                new_x = sprite.normal_pos[0]

        if sprite.pos[0] < sprite.normal_pos[0]:
            new_x = sprite.pos[0] + (self.velocity[0] * dt)
            if new_x > sprite.normal_pos[0]:
                new_x = sprite.normal_pos[0]

        if sprite.pos[1] > sprite.normal_pos[1]:
            new_y = sprite.pos[1] - (self.velocity[1] * dt)
            if new_y < sprite.normal_pos[1]:
                new_y = sprite.normal_pos[1]

        if sprite.pos[1] < sprite.normal_pos[1]:
            new_y = sprite.pos[1] + (self.velocity[1] * dt)
            if new_y > sprite.normal_pos[1]:
                new_y = sprite.normal_pos[1]

        sprite.pos = new_x, new_y

    def enabled(self, sprite):
        return sprite.normal_pos != sprite.pos


class OverridePosition(Behaviour):
    def __init__(self, behaviour):
        self.pos = None
        self.behaviour = behaviour

    def execute(self, dt, sprite):
        if self.pos is None:
            self.pos = sprite.pos

        sprite.normal_pos = sprite.pos
        sprite.pos = self.pos
        self.behaviour.execute(dt, sprite)
        self.pos = sprite.pos

    def enabled(self, sprite):
        return self.behaviour.enabled(sprite)