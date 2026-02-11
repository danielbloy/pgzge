GRAVITY = 60

PARTICLE_EXPLOSION_MIN_VX = -90
PARTICLE_EXPLOSION_MAX_VX = 90
PARTICLE_EXPLOSION_MIN_VY = -90
PARTICLE_EXPLOSION_MAX_VY = 90


class ParticleExplosion(GameObject):

    def __init__(self, pos, lifetime, colour, count):
        super().__init__()
        self.left = lifetime
        self.colour = colour
        self.particles = [(pos[0], pos[1],
                           randint(PARTICLE_EXPLOSION_MIN_VX,
                                   PARTICLE_EXPLOSION_MAX_VX),
                           randint(PARTICLE_EXPLOSION_MIN_VY,
                                   PARTICLE_EXPLOSION_MAX_VY))
                          for _ in range(count)]

    def draw(self, draw):
        for particle in self.particles:
            draw.filled_circle((particle[0], particle[1]), 1, self.colour)

    def update(self, dt):
        self.left -= dt
        self.destroy = self.left < 0

        self.particles = [(particle[0] + (particle[2] * dt),
                           particle[1] + (particle[3] * dt), particle[2],
                           particle[3] + (GRAVITY * dt))
                          for particle in self.particles]


PARTICLE_SCORE_MIN_VX = -60
PARTICLE_SCORE_MAX_VX = 60
PARTICLE_SCORE_MIN_VY = -30
PARTICLE_SCORE_MAX_VY = 60


class ParticleScore(GameObject):

    def __init__(self, pos, lifetime, value):
        super().__init__()
        self.position = pos
        self.left = lifetime
        self.value = value
        self.vx = randint(PARTICLE_SCORE_MIN_VX, PARTICLE_SCORE_MAX_VX)
        self.vy = randint(PARTICLE_SCORE_MIN_VY, PARTICLE_SCORE_MAX_VY)

    @property
    def position(self):
        return self.x, self.y

    @position.setter
    def position(self, pos):
        self.x = pos[0]
        self.y = pos[1]

    def draw(self, draw):
        draw.text(f"{self.value}",
                  center=self.position,
                  color=YELLOW,
                  fontsize=24)

    def update(self, dt):
        self.left -= dt
        self.destroy = self.left < 0
        self.vy += (GRAVITY * dt)
        self.x += self.vx * dt
        self.y += self.vy * dt