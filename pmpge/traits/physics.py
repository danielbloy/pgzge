from math import cos, sin


class Velocity:
    """
    Velocity is the rate at which a sprite moves either horizontally, vertically or
    both. It is measured in pixels per second. If a screen is 160 pixels wide and
    a sprite has a velocity of 40 pixels per second then it will take 4 seconds
    to move across the screen.

    The Velocity trait requires a Position trait to be present on the GameObject.
    """

    x: float
    y: float
    vx: int
    vy: int

    def __init__(self, vx, vy: int):
        self.vx: int = vx
        self.vy: int = vy

    def update(self, dt: float):
        self.x += (dt * self.vx)
        self.y += (dt * self.vy)


class BoundVelocity:
    """
    Limits velocity to a range for each of horizontal and vertical velocities.

    The BoundVelocity trait must be combined with a Velocity trait.
    """
    vx: int
    vy: int
    bounds_velocity: tuple[int | None, int | None, int | None, int | None]

    def __init__(self,
                 min_vx: int | None = None, max_vx: int | None = None,
                 min_vy: int | None = None, max_vy: int | None = None):

        if min_vx is not None and max_vx is not None:
            if min_vx > max_vx:
                raise ValueError("min_vx cannot be larger than max_vx")

        if min_vy is not None and max_vy is not None:
            if min_vy > max_vy:
                raise ValueError("min_vy cannot be larger than max_vy")

        self.bounds_velocity = min_vx, min_vy, max_vx, max_vy

    def update(self, dt: float):
        min_vx, min_vy, max_vx, max_vy = self.bounds_velocity

        if min_vx is not None:
            self.vx = max(self.vx, min_vx)

        if max_vx is not None:
            self.vx = min(self.vx, max_vx)

        if min_vy is not None:
            self.vy = max(self.vy, min_vy)

        if max_vy is not None:
            self.vy = min(self.vy, max_vy)


class Acceleration:
    """
    Acceleration is the rate at which a sprite changes its velocity. It is measured in pixels
    per second per second. If a stationary sprite has an acceleration of 40 pixels per second
    per second, then after 1 second it will have a velocity of 40 pixels per second. After 2
    seconds it will have a velocity of 80 pixels per second and so on.

    The Acceleration trait requires a Velocity trait to be present on the GameObject.
    """

    vx: int
    vy: int
    ax: int
    ay: int

    def __init__(self, ax, ay: int):
        self.ax: int = ax
        self.ay: int = ay

    def update(self, dt: float):
        self.vx += dt * self.ax
        self.vy += dt * self.ay


class Friction:
    """
    Friction is an opposing force against the motion of a sprite. If a sprite has a velocity, then
    its friction will slow the sprite down until the velocity becomes zero. This is similar to
    a negative acceleration, but friction stops once the sprite stops.

    The Friction trait requires a Velocity trait to be present on the GameObject.
    """

    vx: int
    vy: int
    fx: int
    fy: int

    def __init__(self, fx, fy: int):
        self.fx: int = fx
        self.fy: int = fy

    def update(self, dt: float):
        if self.vx > 0:
            self.vx -= dt * self.fx

        if self.vy > 0:
            self.vy -= dt * self.fy


class AngularMotion:
    """
    This trait will rotate a sprite around a centre position (cx, cy) with a given radius
    and angular_motion (specified in radians). This will blat any (x, y) coordinate pair
    so will not play nicely with other traits that set position.
    """
    x: float
    y: float
    cx: int
    cy: int
    radius: int
    angular_velocity: float  # This should be in radians
    angle: float

    def __init__(self, cx: int, cy: int, radius: int, angular_velocity: float, start_angle: float = 0.0):
        self.cx: int = cx
        self.cy: int = cy
        self.radius: int = radius
        self.angular_velocity: float = angular_velocity
        self.angle: float = start_angle

    def update(self, dt: float):
        angle = self.angle + (dt * self.angular_velocity)
        self.angle = angle

        radius = self.radius
        self.x = self.cx + (radius * cos(angle))
        self.y = self.cy + (radius * sin(angle))


class HorizontalBounce:
    """
    Simple trait that bounces vertically between two points.
    This trait simply flips velocity when it hits the relevant limit
    which changes direction immediately.
    """
    x: float
    vx: int
    limits_x: tuple[int, int]

    def __init__(self, x_min, x_max: int):
        if x_max < x_min:
            raise ValueError("x_max cannot be smaller than x_min")

        self.limits_x = (x_min, x_max)

    def update(self, dt: float):
        x = self.x
        vx = self.vx
        x_min, x_max = self.limits_x

        if x < x_min and vx < 0:
            self.vx = -vx

        elif x > x_max and vx > 0:
            self.vx = -vx


class VerticalBounce:
    """
    Simple trait that bounces horizontally between two points.
    This trait simply flips velocity when it hits the relevant limit
    which changes direction immediately.
    """
    y: float
    vy: int
    limits_y: tuple[int, int]

    def __init__(self, y_min, y_max: int):
        if y_max < y_min:
            raise ValueError("y_max cannot be smaller than y_min")

        self.limits_y = (y_min, y_max)

    def update(self, dt: float):
        y = self.y
        vy = self.vy
        y_min, y_max = self.limits_y

        if y < y_min and vy < 0:
            self.vy = -vy

        elif y > y_max and vy > 0:
            self.vy = -vy


class HorizontalOscillator:
    """
    Simple trait that oscillates vertically between two points.
    This trait flips acceleration when it hits the relevant limit.
    Therefore, velocity does not instantly change so the GameObject
    will take time to "reverse" direction.
    """
    x: float
    ax: int
    limits_x: tuple[int, int]

    def __init__(self, x_min, x_max: int):
        if x_max < x_min:
            raise ValueError("x_max cannot be smaller than x_min")

        self.limits_x = (x_min, x_max)

    def update(self, dt: float):
        x = self.x
        ax = self.ax
        x_min, x_max = self.limits_x

        if x < x_min and ax < 0:
            self.ax = -ax

        elif x > x_max and ax > 0:
            self.ax = -ax


class VerticalOscillator:
    """
    Simple trait that oscillates horizontally between two points.
    This trait flips acceleration when it hits the relevant limit.
    Therefore, velocity does not instantly change so the GameObject
    will take time to "reverse" direction.
    """
    y: float
    ay: int
    limits_y: tuple[int, int]

    def __init__(self, y_min, y_max: int):
        if y_max < y_min:
            raise ValueError("y_max cannot be smaller than y_min")

        self.limits_y = (y_min, y_max)

    def update(self, dt: float):
        y = self.y
        ay = self.ay
        y_min, y_max = self.limits_y

        if y < y_min and ay < 0:
            self.ay = -ay

        elif y > y_max and ay > 0:
            self.ay = -ay
