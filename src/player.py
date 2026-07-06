"""
Player module - controls the runner character.
The player runs in one of 3 lanes, can jump and slide.
"""
import math


class Player:
    """Endless runner player with lane movement, jumping, and sliding."""

    # Lane geometry
    LANE_WIDTH = 2.0
    LANE_POSITIONS = [-LANE_WIDTH, 0.0, LANE_WIDTH]

    # Movement speeds
    SPEED_INITIAL = 8.0      # Starting speed (units/sec)
    SPEED_MAX = 25.0         # Maximum speed
    SPEED_INCREASE = 0.12    # Speed increase per second

    # Jump physics
    JUMP_VELOCITY = 11.0
    GRAVITY = 35.0

    # Slide
    SLIDE_DURATION = 0.6

    # Collision box
    HEIGHT_STANDING = 1.8
    HEIGHT_SLIDING = 0.5
    WIDTH = 0.7

    def __init__(self):
        # Lane tracking
        self.lane = 1                  # 0=left, 1=center, 2=right
        self.x = 0.0                   # Current X position (smooth)

        # Vertical (jumping)
        self.y = 0.0                   # Height above ground
        self.vy = 0.0                  # Vertical velocity

        # Forward movement
        self.z = 0.0                   # World Z position (distance)
        self.distance = 0.0            # Total distance traveled
        self.speed = self.SPEED_INITIAL

        # Sliding
        self.sliding = False
        self.slide_timer = 0.0

        # State
        self.alive = True

    @property
    def height(self):
        """Current height of the player (reduced when sliding)."""
        return self.HEIGHT_SLIDING if self.sliding else self.HEIGHT_STANDING

    def move_left(self):
        """Move to the left lane."""
        if self.lane > 0 and self.alive:
            self.lane -= 1

    def move_right(self):
        """Move to the right lane."""
        if self.lane < 2 and self.alive:
            self.lane += 1

    def jump(self):
        """Start a jump if on the ground and not sliding."""
        if self.alive and self.y == 0 and not self.sliding:
            self.vy = self.JUMP_VELOCITY

    def slide(self):
        """Start sliding if on the ground and not already sliding."""
        if self.alive and not self.sliding and self.y == 0:
            self.sliding = True
            self.slide_timer = self.SLIDE_DURATION

    def update(self, dt):
        """Update player state for one frame.

        Args:
            dt: Delta time in seconds
        """
        if not self.alive:
            return

        # Smooth lane transition (exponential easing)
        target_x = self.LANE_POSITIONS[self.lane]
        self.x += (target_x - self.x) * min(1.0, 15.0 * dt)

        # Jump physics with gravity
        self.vy -= self.GRAVITY * dt
        self.y += self.vy * dt
        if self.y < 0:
            self.y = 0
            self.vy = 0

        # Slide timer
        if self.sliding:
            self.slide_timer -= dt
            if self.slide_timer <= 0:
                self.sliding = False

        # Forward movement
        self.z += self.speed * dt
        self.distance += self.speed * dt

        # Gradual speed increase
        self.speed = min(self.SPEED_MAX, self.speed + self.SPEED_INCREASE * dt)

    def reset(self):
        """Reset player to initial state."""
        self.lane = 1
        self.x = 0.0
        self.y = 0.0
        self.vy = 0.0
        self.z = 0.0
        self.distance = 0.0
        self.speed = self.SPEED_INITIAL
        self.sliding = False
        self.slide_timer = 0.0
        self.alive = True
