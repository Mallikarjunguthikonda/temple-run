"""
Segment module - represents a single corridor segment with obstacles and coins.
Segments are procedurally generated and recycled as the player runs.
"""
import math
import random

# A segment is 3 units deep along the Z axis
SEGMENT_LENGTH = 3.0

# Corridor dimensions
HALF_WIDTH = 3.0
LANE_WIDTH = 2.0
WALL_HEIGHT = 3.5


class Coin:
    """A collectible coin in the corridor."""

    def __init__(self, lane, z_offset, y=0.6):
        self.lane = lane          # Which lane (0, 1, 2)
        self.z_offset = z_offset  # Z position within the segment
        self.y = y                # Height above the floor
        self.collected = False
        self.anim_offset = random.random() * 2 * math.pi  # Random start phase

    @property
    def world_x(self):
        return -HALF_WIDTH + self.lane * LANE_WIDTH + LANE_WIDTH / 2


class Segment:
    """A section of corridor that can contain obstacles and coins."""

    def __init__(self, z):
        self.z = z                   # World Z position of segment start
        self.obstacle_type = None    # 'wall', 'barrier', 'beam', or None
        self.obstacle_lane = 0       # Which lane the obstacle is in
        self.has_obstacle = False
        self.coins = []              # List of Coin objects
        self.passed = False          # Player has passed this segment
        self.visible = True

    def generate(self, difficulty, prev_segments=None):
        """Randomly generate obstacles and coins for this segment.

        Args:
            difficulty: 0-10 scale, affects obstacle frequency
            prev_segments: List of recent segments (to avoid unfair patterns)
        """
        # -- Obstacle generation --
        # Base chance increases with difficulty
        obs_chance = min(0.35, 0.12 + difficulty * 0.025)

        # Reduce chance if previous segments had obstacles recently
        recent_obstacles = 0
        if prev_segments:
            for s in prev_segments[-3:]:
                if s.has_obstacle:
                    recent_obstacles += 1
        if recent_obstacles >= 2:
            obs_chance *= 0.3
        elif recent_obstacles >= 1:
            obs_chance *= 0.6

        if random.random() < obs_chance:
            self.obstacle_type = random.choice(['wall', 'barrier', 'beam'])

            # Choose a lane, avoiding the same lane as previous obstacles
            blocked_lanes = set()
            if prev_segments:
                for s in reversed(prev_segments[-2:]):
                    if s.has_obstacle:
                        blocked_lanes.add(s.obstacle_lane)

            available = [l for l in range(3) if l not in blocked_lanes]
            # If all lanes blocked (unlikely with 3+ segments), allow any
            if not available:
                available = [0, 1, 2]

            self.obstacle_lane = random.choice(available)
            self.has_obstacle = True

        # -- Coin generation --
        coin_chance = 0.45
        if random.random() < coin_chance:
            lanes = [0, 1, 2]
            # Don't place coins in the obstacle lane
            if self.has_obstacle:
                lanes = [l for l in lanes if l != self.obstacle_lane]

            if lanes:
                count = random.randint(1, min(3, len(lanes)))
                for _ in range(count):
                    lane = random.choice(lanes)
                    lanes.remove(lane)
                    z_off = random.uniform(0.2, SEGMENT_LENGTH - 0.2)
                    self.coins.append(Coin(lane, z_off))

    def obstacle_world_x(self):
        """Get the world X position of the obstacle (center of lane)."""
        return -HALF_WIDTH + self.obstacle_lane * LANE_WIDTH + LANE_WIDTH / 2

    def obstacle_z(self):
        """Z position of the obstacle within the segment."""
        return self.z + SEGMENT_LENGTH * 0.4

    def reset(self, new_z):
        """Reset segment for reuse at a new Z position."""
        self.z = new_z
        self.obstacle_type = None
        self.obstacle_lane = 0
        self.has_obstacle = False
        self.coins = []
        self.passed = False
        self.visible = True
