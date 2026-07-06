"""
Camera module - handles 3D to 2D perspective projection.
The camera sits behind and above the player, looking down the corridor.
"""
import math


class Camera:
    """Perspective camera that projects 3D world points to 2D screen coordinates."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.center_x = screen_width / 2
        self.center_y = screen_height / 2
        # Focal length determines field of view (~75 deg horizontal at 1080px)
        self.focal_length = max(screen_width, screen_height) * 0.55
        # Camera height above the floor (eye level)
        self.height = 1.6
        # How far behind the player the camera sits
        self.distance_behind = 6.0

    def relative_z(self, world_z, player_z):
        """Convert world Z to Z relative to camera.
        Positive means in front of camera, negative means behind."""
        return world_z - (player_z - self.distance_behind)

    def project(self, world_x, world_y, world_z):
        """Project a 3D world point to 2D screen coordinates.

        Args:
            world_x: Left-right position (-3 to 3 is corridor width)
            world_y: Up-down position (0 = floor)
            world_z: Forward distance from camera (must be > 0)

        Returns:
            (screen_x, screen_y, scale) or None if behind camera
        """
        if world_z <= 0.05:
            return None
        scale = self.focal_length / world_z
        sx = self.center_x + world_x * scale
        sy = self.center_y - (world_y - self.height) * scale
        return sx, sy, scale

    def project_quad(self, corners, player_z):
        """Project 4 world-space corners to screen coordinates.

        corners: [(x, y, z_world), (x, y, z_world), (x, y, z_world), (x, y, z_world)]
        Returns list of (sx, sy) or None if any corner is behind camera.
        """
        projected = []
        for wx, wy, wz in corners:
            rel_z = self.relative_z(wz, player_z)
            p = self.project(wx, wy, rel_z)
            if p is None:
                return None
            projected.append((p[0], p[1]))
        return projected
