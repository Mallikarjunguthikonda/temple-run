"""
GameWidget - Main Kivy widget that renders the 3D corridor and runs the game loop.
"""
import math
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Color, Mesh, Rectangle, Line
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window

from src.camera import Camera
from src.player import Player
from src.corridor import Corridor
from src.segment import SEGMENT_LENGTH, HALF_WIDTH, LANE_WIDTH, WALL_HEIGHT


# ── Color palette ──────────────────────────────────────────────────
COLOR_BG = (0.06, 0.06, 0.10, 1.0)
COLOR_FLOOR_DARK = (0.18, 0.15, 0.11, 1.0)
COLOR_FLOOR_LIGHT = (0.24, 0.20, 0.15, 1.0)
COLOR_WALL = (0.30, 0.26, 0.22, 1.0)
COLOR_WALL_EDGE = (0.22, 0.19, 0.16, 1.0)
COLOR_OBSTACLE_WALL = (0.55, 0.18, 0.18, 1.0)
COLOR_OBSTACLE_BARRIER = (0.65, 0.30, 0.10, 1.0)
COLOR_OBSTACLE_BEAM = (0.35, 0.25, 0.65, 1.0)
COLOR_COIN = (1.0, 0.85, 0.15, 1.0)
COLOR_PLAYER_BODY = (0.15, 0.50, 0.80, 1.0)
COLOR_PLAYER_HEAD = (0.90, 0.75, 0.55, 1.0)
COLOR_GAMEOVER_BG = (0.0, 0.0, 0.0, 0.7)
COLOR_BUTTON = (0.20, 0.55, 0.85, 1.0)


class GameWidget(Widget):
    """Main game widget - handles rendering, game state, and input."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialized = False
        Clock.schedule_once(self._init_game, 0)

    def _init_game(self, dt):
        """Initialize game after widget has dimensions."""
        self.camera = Camera(Window.width if Window.width else 1080,
                              Window.height if Window.height else 1920)
        self.player = Player()
        self.corridor = Corridor()
        self.state = 'menu'       # 'menu', 'playing', 'game_over'
        self.score = 0
        self.coins_collected = 0
        self.game_time = 0.0
        self.high_score = 0

        # Touch tracking for swipe detection
        self._touch_start = None
        self._touch_time = 0.0

        # Pre-rendered text textures (cache for performance)
        self._text_cache = {}

        # Bind touch events
        Window.bind(on_touch_down=self._on_touch_down)
        Window.bind(on_touch_up=self._on_touch_up)

        # Start game loop
        Clock.schedule_interval(self.update, 1.0 / 60.0)
        self._initialized = True

    # ── Text Rendering (uses Kivy's core text, looks clean) ────────
    def _render_text(self, text, font_size=24, color=(1, 1, 1, 1), bold=False):
        """Render text to a texture and return it."""
        cache_key = (text, font_size, color, bold)
        if cache_key in self._text_cache:
            return self._text_cache[cache_key]

        label = CoreLabel(
            text=text,
            font_size=font_size,
            color=color,
            bold=bold,
        )
        label.refresh()
        self._text_cache[cache_key] = label
        return label

    def _draw_text(self, text, x, y, font_size=24, color=(1, 1, 1, 1),
                   bold=False, anchor='center', valign='middle'):
        """Draw text at the given screen position."""
        label = self._render_text(text, font_size, color, bold)
        texture = label.texture
        if texture is None:
            return

        tex_w, tex_h = texture.size
        if anchor == 'center':
            px = x - tex_w / 2
        elif anchor == 'left':
            px = x
        elif anchor == 'right':
            px = x - tex_w

        if valign == 'middle':
            py = y - tex_h / 2
        elif valign == 'top':
            py = y - tex_h
        elif valign == 'bottom':
            py = y

        Color(1, 1, 1, 1)
        Rectangle(pos=(px, py), size=(tex_w, tex_h), texture=texture)

    # ── Input Handling ──────────────────────────────────────────────
    def _on_touch_down(self, window, touch):
        if self.state == 'game_over':
            self._start_game()
            return
        if self.state == 'menu':
            self._start_game()
            return
        self._touch_start = (touch.x, touch.y)
        self._touch_time = Clock.get_time()

    def _on_touch_up(self, window, touch):
        if self.state != 'playing':
            return
        if self._touch_start is None:
            return

        dx = touch.x - self._touch_start[0]
        dy = touch.y - self._touch_start[1]

        min_swipe = 40

        if abs(dx) > min_swipe or abs(dy) > min_swipe:
            if abs(dx) > abs(dy):
                if dx > 0:
                    self.player.move_right()
                else:
                    self.player.move_left()
            else:
                if dy > 0:
                    self.player.slide()
                else:
                    self.player.jump()

        self._touch_start = None

    # ── Game State ─────────────────────────────────────────────────
    def _start_game(self):
        self.player.reset()
        self.corridor.reset()
        self.state = 'playing'
        self.score = 0
        self.coins_collected = 0
        self.game_time = 0.0

    # ── Update Loop ────────────────────────────────────────────────
    def update(self, dt):
        """Called every frame (60 FPS)."""
        dt = min(dt, 0.05)

        if self.state == 'playing':
            self.game_time += dt
            self.player.update(dt)
            self.corridor.update(self.player.z)
            self.score = int(self.player.distance)

            # Obstacle collision
            if self.corridor.check_obstacle_collision(self.player):
                self.player.alive = False
                self.state = 'game_over'
                if self.score > self.high_score:
                    self.high_score = self.score

            # Coin collection
            coins = self.corridor.check_coin_collection(self.player)
            if coins > 0:
                self.coins_collected += coins
                self.score += coins * 10

        self.redraw()

    # ── Rendering ──────────────────────────────────────────────────
    def redraw(self):
        """Clear and redraw the entire scene."""
        self.canvas.clear()
        with self.canvas:
            Color(*COLOR_BG)
            Rectangle(pos=(0, 0), size=self.size)

            if self.state == 'menu':
                self._draw_menu()
                return

            self._draw_corridor()
            self._draw_hud()

            if self.state == 'game_over':
                self._draw_game_over()

    # ── 3D Corridor Rendering ──────────────────────────────────────
    def _draw_corridor(self):
        """Draw the 3D corridor with all game elements."""
        player_z = self.player.z
        active = self.corridor.get_active_segments(player_z)

        # Sort far-to-near for painter's algorithm
        active.sort(key=lambda s: s.z, reverse=True)

        for seg in active:
            self._draw_segment(seg, player_z)

        # Draw player on top
        self._draw_player(player_z)

    def _draw_segment(self, seg, player_z):
        """Draw a single corridor segment."""
        zf = self.camera.relative_z(seg.z, player_z)
        zb = self.camera.relative_z(seg.z + SEGMENT_LENGTH, player_z)

        if zb <= 0 and zf <= 0:
            return

        if zf <= 0:
            zf = 0.1

        # Floor tiles
        tile_index = int(seg.z / SEGMENT_LENGTH)
        for lane in range(3):
            left = -HALF_WIDTH + lane * LANE_WIDTH
            right = left + LANE_WIDTH
            is_dark = (lane + tile_index) % 2 == 0
            color = COLOR_FLOOR_DARK if is_dark else COLOR_FLOOR_LIGHT
            self._draw_quad([
                (left, 0, zf), (right, 0, zf),
                (right, 0, zb), (left, 0, zb)
            ], color, player_z)

        # Left wall
        self._draw_quad([
            (-HALF_WIDTH, 0, zf), (-HALF_WIDTH, WALL_HEIGHT, zf),
            (-HALF_WIDTH, WALL_HEIGHT, zb), (-HALF_WIDTH, 0, zb)
        ], COLOR_WALL, player_z)
        self._draw_quad([
            (-HALF_WIDTH, WALL_HEIGHT, zf), (-HALF_WIDTH + 0.15, WALL_HEIGHT, zf),
            (-HALF_WIDTH + 0.15, WALL_HEIGHT, zb), (-HALF_WIDTH, WALL_HEIGHT, zb)
        ], COLOR_WALL_EDGE, player_z)

        # Right wall
        self._draw_quad([
            (HALF_WIDTH, 0, zf), (HALF_WIDTH, WALL_HEIGHT, zf),
            (HALF_WIDTH, WALL_HEIGHT, zb), (HALF_WIDTH, 0, zb)
        ], COLOR_WALL, player_z)
        self._draw_quad([
            (HALF_WIDTH - 0.15, WALL_HEIGHT, zf), (HALF_WIDTH, WALL_HEIGHT, zf),
            (HALF_WIDTH, WALL_HEIGHT, zb), (HALF_WIDTH - 0.15, WALL_HEIGHT, zb)
        ], COLOR_WALL_EDGE, player_z)

        # Obstacle
        if seg.has_obstacle:
            self._draw_obstacle(seg, player_z)

        # Coins
        for coin in seg.coins:
            if not coin.collected:
                self._draw_coin(coin, seg.z, player_z)

    def _draw_obstacle(self, seg, player_z):
        """Draw an obstacle (wall, barrier, or beam) with 3D depth."""
        z_obs = self.camera.relative_z(seg.obstacle_z(), player_z)
        if z_obs <= 0:
            return

        lane = seg.obstacle_lane
        left = -HALF_WIDTH + lane * LANE_WIDTH
        right = left + LANE_WIDTH

        if seg.obstacle_type == 'wall':
            self._draw_obstacle_box(left, right, 0, WALL_HEIGHT, z_obs,
                                     COLOR_OBSTACLE_WALL, 0.3, player_z)

        elif seg.obstacle_type == 'barrier':
            self._draw_obstacle_box(left, right, 0, 0.8, z_obs,
                                     COLOR_OBSTACLE_BARRIER, 0.25, player_z)

        elif seg.obstacle_type == 'beam':
            self._draw_obstacle_box(-HALF_WIDTH, HALF_WIDTH, 1.5, 1.8, z_obs,
                                     COLOR_OBSTACLE_BEAM, 0.25, player_z)

    def _draw_obstacle_box(self, left, right, y_bot, y_top, z_obs, color, depth, player_z):
        """Draw a 3D box obstacle (front, top, side faces)."""
        # Front face
        self._draw_quad([
            (left, y_bot, z_obs), (right, y_bot, z_obs),
            (right, y_top, z_obs), (left, y_top, z_obs)
        ], color, player_z)
        # Top face
        self._draw_quad([
            (left, y_top, z_obs), (right, y_top, z_obs),
            (right, y_top, z_obs - depth), (left, y_top, z_obs - depth)
        ], (color[0] * 0.7, color[1] * 0.7, color[2] * 0.7, 1.0), player_z)
        # Side face
        self._draw_quad([
            (right, y_bot, z_obs), (right, y_top, z_obs),
            (right, y_top, z_obs - depth), (right, y_bot, z_obs - depth)
        ], (color[0] * 0.5, color[1] * 0.5, color[2] * 0.5, 1.0), player_z)

    def _draw_coin(self, coin, seg_z, player_z):
        """Draw a spinning coin."""
        z_coin = self.camera.relative_z(seg_z + coin.z_offset, player_z)
        if z_coin <= 0:
            return

        cx = coin.world_x
        spin = math.cos(self.game_time * 4.0 + coin.anim_offset)
        visible_w = abs(spin)

        if visible_w < 0.05:
            return

        half_w = 0.3 * visible_w
        half_h = 0.3
        brightness = 0.6 + 0.4 * abs(spin)

        self._draw_quad([
            (cx - half_w, coin.y - half_h, z_coin),
            (cx + half_w, coin.y - half_h, z_coin),
            (cx + half_w, coin.y + half_h, z_coin),
            (cx - half_w, coin.y + half_h, z_coin)
        ], (COLOR_COIN[0] * brightness, COLOR_COIN[1] * brightness,
            COLOR_COIN[2] * brightness, 1.0), player_z)

    def _draw_player(self, player_z):
        """Draw the player character."""
        p = self.player
        pz = self.camera.relative_z(p.z, player_z)
        if pz <= 0:
            return

        hw = p.WIDTH / 2
        body_h = p.height
        y_bot = p.y
        d = 0.25  # depth for 3D effect

        # Body front
        self._draw_quad([
            (p.x - hw, y_bot, pz), (p.x + hw, y_bot, pz),
            (p.x + hw, y_bot + body_h, pz), (p.x - hw, y_bot + body_h, pz)
        ], COLOR_PLAYER_BODY, player_z)

        # Body side (depth)
        self._draw_quad([
            (p.x + hw, y_bot, pz), (p.x + hw, y_bot + body_h, pz),
            (p.x + hw, y_bot + body_h, pz - d), (p.x + hw, y_bot, pz - d)
        ], (COLOR_PLAYER_BODY[0] * 0.6, COLOR_PLAYER_BODY[1] * 0.6,
            COLOR_PLAYER_BODY[2] * 0.6, 1.0), player_z)

        if not p.sliding:
            # Head
            head_y = y_bot + body_h
            self._draw_quad([
                (p.x - 0.2, head_y, pz), (p.x + 0.2, head_y, pz),
                (p.x + 0.2, head_y + 0.25, pz), (p.x - 0.2, head_y + 0.25, pz)
            ], COLOR_PLAYER_HEAD, player_z)

    # ── 3D Drawing Primitive ──────────────────────────────────────────
    def _draw_quad(self, corners, color, player_z):
        """Draw a filled quad. corners contain (x, y, rel_z) where rel_z is
        distance from camera (positive = in front)."""
        pts = []
        for wx, wy, rel_z in corners:
            p = self.camera.project(wx, wy, rel_z)
            if p is None:
                return
            pts.append((p[0], p[1]))

        Color(*color)
        vertices = []
        for sx, sy in pts:
            vertices.extend([sx, sy, 0.0, 0.0])
        Mesh(vertices=vertices, indices=[0, 1, 2, 0, 2, 3],
             mode='triangles')

    # ── UI Screens ────────────────────────────────────────────────────
    def _draw_menu(self):
        """Draw the start screen."""
        cx = self.width / 2
        cy = self.height / 2

        # Title
        self._draw_text("TEMPLE RUN", cx, cy + 120, font_size=48,
                         color=(0.95, 0.75, 0.15, 1.0), bold=True)

        # Instructions
        self._draw_text("Swipe to dodge • Jump • Slide", cx, cy + 50,
                         font_size=18, color=(0.8, 0.8, 0.8, 1.0))
        self._draw_text("Collect coins for bonus points", cx, cy + 20,
                         font_size=16, color=(0.6, 0.6, 0.6, 1.0))

        # Start button area
        self._draw_text("TAP TO START", cx, cy - 60,
                         font_size=22, color=COLOR_BUTTON, bold=True)

        # Controls hint at bottom
        self._draw_text("← →  Move   |   ↑ Jump   |   ↓ Slide",
                         cx, 40, font_size=14, color=(0.5, 0.5, 0.5, 1.0))

        if self.high_score > 0:
            self._draw_text(f"High Score: {self.high_score}", cx, cy - 120,
                             font_size=18, color=(0.8, 0.8, 0.8, 1.0))

    def _draw_hud(self):
        """Draw heads-up display during gameplay."""
        if self.state not in ('playing', 'game_over'):
            return

        # Score (top center)
        self._draw_text(f"{self.score}", self.width / 2, self.height - 50,
                         font_size=36, color=(1, 1, 1, 1), bold=True)

        # Coin count (top left)
        self._draw_text(f"○ {self.coins_collected}", 60, self.height - 50,
                         font_size=20, color=(1.0, 0.85, 0.15, 1.0))

        # Speed (top right)
        speed_pct = int((self.player.speed / Player.SPEED_MAX) * 100)
        self._draw_text(f"{speed_pct}%", self.width - 50, self.height - 50,
                         font_size=18, color=(0.6, 0.6, 0.6, 1.0), anchor='right')

    def _draw_game_over(self):
        """Draw the game over overlay."""
        # Dim background
        Color(*COLOR_GAMEOVER_BG)
        Rectangle(pos=(0, 0), size=self.size)

        cx = self.width / 2
        cy = self.height / 2

        # Game Over title
        self._draw_text("GAME OVER", cx, cy + 100,
                         font_size=42, color=(0.9, 0.2, 0.2, 1.0), bold=True)

        # Stats
        self._draw_text(f"Score: {self.score}", cx, cy + 30,
                         font_size=26, color=(1, 1, 1, 1))
        self._draw_text(f"Coins: {self.coins_collected}", cx, cy - 10,
                         font_size=20, color=(1.0, 0.85, 0.15, 1.0))

        if self.score >= self.high_score and self.score > 0:
            self._draw_text("NEW HIGH SCORE!", cx, cy - 50,
                             font_size=18, color=(1.0, 0.85, 0.15, 1.0), bold=True)

        # Retry
        self._draw_text("TAP TO RETRY", cx, cy - 110,
                         font_size=22, color=COLOR_BUTTON, bold=True)

    def on_size(self, *args):
        """Handle widget resize."""
        if hasattr(self, 'camera') and self.width > 0 and self.height > 0:
            self.camera = Camera(self.width, self.height)
