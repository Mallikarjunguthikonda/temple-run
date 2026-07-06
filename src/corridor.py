"""
Corridor module - manages the ring buffer of segments ahead of the player.
Handles procedural generation, recycling, and collision detection.
"""
from src.segment import Segment, SEGMENT_LENGTH, LANE_WIDTH, HALF_WIDTH

# How many segments to keep ahead of the player
LOOK_AHEAD = 35
# How many segments to keep recycling slack
BUFFER_EXTRA = 5


class Corridor:
    """Manages the procedural endless corridor."""

    def __init__(self):
        # Ring buffer of segments
        self.segments = []
        self.total_segments = LOOK_AHEAD + BUFFER_EXTRA
        self.difficulty = 0.0

        # Initialize ring buffer
        for i in range(self.total_segments):
            z = i * SEGMENT_LENGTH
            seg = Segment(z)
            self.segments.append(seg)

        # Generate obstacles for all segments
        for i, seg in enumerate(self.segments):
            prev = self.segments[:i]
            seg.generate(self.difficulty, prev)

    def update(self, player_z):
        """Update corridor: recycle passed segments, generate new ones ahead.

        Args:
            player_z: Current Z position of the player
        """
        # Update difficulty based on distance traveled
        self.difficulty = min(10.0, player_z / 30.0)

        # Find the furthest segment that has been passed
        # A segment is passed when player_z > segment.z + SEGMENT_LENGTH
        furthest_passed = -1
        for i, seg in enumerate(self.segments):
            if player_z > seg.z + SEGMENT_LENGTH + 1.0:
                furthest_passed = i
            else:
                break

        # Recycle passed segments to the front
        if furthest_passed >= 0:
            for i in range(furthest_passed + 1):
                seg = self.segments[i]
                # Place it after the last segment
                new_z = self.segments[-1].z + SEGMENT_LENGTH
                seg.reset(new_z)

                # Get recent segments for generation context
                recent = self.segments[i+1:i+4]  # segments after this one
                if len(recent) < 3:
                    recent = self.segments[max(0, i-2):i] + recent

                seg.generate(self.difficulty, recent)

            # Reorder the ring buffer: move passed segments to end
            self.segments = self.segments[furthest_passed + 1:] + self.segments[:furthest_passed + 1]

    def get_active_segments(self, player_z, render_distance=65.0):
        """Get segments within render distance of the player.

        Args:
            player_z: Player Z position
            render_distance: How far ahead to render (in world units)

        Returns:
            List of segments within range, sorted near-to-far
        """
        active = []
        for seg in self.segments:
            rel_z = seg.z - player_z
            if -SEGMENT_LENGTH <= rel_z <= render_distance:
                active.append(seg)
        return active

    def check_obstacle_collision(self, player):
        """Check if the player collides with any obstacle.

        Returns:
            True if collision detected (player should die)
        """
        if not player.alive:
            return False

        for seg in self.segments:
            if seg.passed or not seg.has_obstacle:
                continue

            # Check if player is within this segment's Z range
            seg_center_z = seg.z + SEGMENT_LENGTH / 2
            if abs(player.z - seg_center_z) > SEGMENT_LENGTH / 2:
                continue

            # Mark as passed regardless of outcome
            seg.passed = True

            # Check if player is in the obstacle's lane
            player_lane = player.lane
            if player_lane != seg.obstacle_lane:
                continue  # Different lane = safe

            # Check obstacle type
            if seg.obstacle_type == 'wall':
                # Wall blocks the entire lane
                return True
            elif seg.obstacle_type == 'barrier':
                # Barrier: must jump over (y > 0.5)
                if player.y < 0.5:
                    return True
            elif seg.obstacle_type == 'beam':
                # Beam: must slide under
                if not player.sliding:
                    return True

        return False

    def check_coin_collection(self, player):
        """Check if the player collects any coins.

        Returns:
            Number of coins collected this frame
        """
        if not player.alive:
            return 0

        collected = 0
        for seg in self.segments:
            for coin in seg.coins:
                if coin.collected:
                    continue
                # Check proximity to player
                dz = abs(player.z - (seg.z + coin.z_offset))
                if dz < 0.4 and player.lane == coin.lane:
                    coin.collected = True
                    collected += 1

        return collected

    def reset(self):
        """Reset the corridor for a new game."""
        self.segments = []
        self.difficulty = 0.0

        for i in range(self.total_segments):
            z = i * SEGMENT_LENGTH
            seg = Segment(z)
            self.segments.append(seg)

        for i, seg in enumerate(self.segments):
            prev = self.segments[:i]
            seg.generate(self.difficulty, prev)
