"""
Test script for Temple Run game logic (no GUI needed).
Tests: camera, player, segment generation, corridor, collision, coins.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import math
import random
import traceback

# Mock Kivy's core text Label so gamewidget can import
import types
class MockModule:
    pass

# We need to mock kivy modules before importing gamewidget
import sys
class MockKivy:
    class graphics:
        class Color: pass
        class Mesh: pass
        class Rectangle: pass
        class Line: pass
    class clock:
        class Clock:
            @staticmethod
            def schedule_once(*a, **kw): pass
            @staticmethod
            def schedule_interval(*a, **kw): pass
            @staticmethod
            def get_time(): return 0
    class uix:
        class widget:
            class Widget:
                def __init__(self, **kw): pass
    class core:
        class text:
            class Label:
                def __init__(self, **kw): pass
                def refresh(self): pass
                @property
                def texture(self): return None
        class window:
            class Window:
                width = 400
                height = 720
                @staticmethod
                def bind(**kw): pass
    class utils:
        platform = 'linux'

sys.modules['kivy'] = MockKivy()
sys.modules['kivy.graphics'] = MockKivy.graphics()
sys.modules['kivy.clock'] = MockKivy.clock()
sys.modules['kivy.uix'] = MockKivy.uix()
sys.modules['kivy.uix.widget'] = MockKivy.uix.widget()
sys.modules['kivy.core'] = MockKivy.core()
sys.modules['kivy.core.text'] = MockKivy.core.text()
sys.modules['kivy.core.window'] = MockKivy.core.window()
sys.modules['kivy.utils'] = MockKivy.utils()

# Now import game modules
from src.camera import Camera
from src.player import Player
from src.segment import Segment, SEGMENT_LENGTH, Coin
from src.corridor import Corridor

passed = 0
failed = 0

def test(name, func):
    global passed, failed
    try:
        func()
        passed += 1
        print(f"  ✓ {name}")
    except Exception as e:
        failed += 1
        print(f"  ✗ {name}: {e}")
        traceback.print_exc()

# ── Camera Tests ──────────────────────────────────────────────
def camera_tests():
    cam = Camera(1080, 2400)
    assert cam.screen_width == 1080
    assert cam.screen_height == 2400
    assert cam.focal_length > 0
    assert cam.height == 1.6
    assert cam.distance_behind == 6.0

    # Project a point in front of camera
    result = cam.project(0, 1.6, 10)
    assert result is not None, "Point in front should project"
    sx, sy, scale = result
    assert scale > 0, "Scale should be positive"
    assert sx == cam.center_x, "Center of corridor should map to screen center"

    # Point behind camera
    result = cam.project(0, 0, -1)
    assert result is None, "Point behind camera should be None"

    # Relative Z calculation
    rel = cam.relative_z(10, 5)  # world_z=10, player_z=5
    assert rel == 10 - (5 - 6) == 11, f"Expected 11, got {rel}"

    rel = cam.relative_z(0, 5)
    assert rel == 0 - (5 - 6) == 1, f"Expected 1, got {rel}"

    # project_quad
    corners = [(0, 0, 10), (1, 0, 10), (1, 1, 10), (0, 1, 10)]
    pts = cam.project_quad(corners, 5)
    assert pts is not None, "Quad in front should project"
    assert len(pts) == 4, f"Expected 4 points, got {len(pts)}"

    # Quad behind camera
    corners2 = [(0, 0, -10), (1, 0, -10), (1, 1, -10), (0, 1, -10)]
    pts2 = cam.project_quad(corners2, 20)
    assert pts2 is None, "Quad behind camera should be None"

def player_tests():
    p = Player()
    assert p.lane == 1, "Start in center lane"
    assert p.x == 0.0
    assert p.y == 0.0
    assert p.alive
    assert p.speed == Player.SPEED_INITIAL
    assert p.distance == 0.0
    assert not p.sliding

    # Lane movement
    p.move_left()
    assert p.lane == 0, "Should move to left lane"
    p.update(0.1)
    assert p.x < -1.5, f"Should be moving toward left lane, x={p.x}"

    p2 = Player()
    p2.move_right()
    assert p2.lane == 2, "Should move to right lane"
    p2.update(0.1)
    assert p2.x > 1.5, f"Should be moving toward right lane, x={p2.x}"

    p.move_left()
    assert p.lane == 0, "Should not go past left lane"
    p.move_right()
    assert p.lane == 1, "Should move back to center"
    p.update(0.1)
    assert abs(p.x) < 0.5, f"Should return toward center, x={p.x}"

    # Jump
    p.lane = 1
    p.x = 0
    p.y = 0
    p.vy = 0
    p.jump()
    assert p.vy > 0, "Jump should give upward velocity"
    p.update(0.1)
    assert p.y > 0, "Should be in the air after jump"

    # Gravity should bring player down
    for _ in range(30):
        p.update(0.1)
    assert abs(p.y) < 0.01, f"Should land: y={p.y}"
    assert abs(p.vy) < 0.01, f"Velocity should be 0: vy={p.vy}"

    # Slide
    p.slide()
    assert p.sliding, "Should be sliding"
    assert p.slide_timer > 0
    # Slide for duration
    p.update(p.slide_timer + 0.1)
    assert not p.sliding, "Slide should end"

    # Death
    p.move_left()
    p.alive = False
    old_lane = p.lane
    p.move_right()
    assert p.lane == old_lane, "Dead player shouldn't move"

    # Distance tracking
    p2 = Player()
    p2.update(1.0)
    assert p2.distance > 0, "Player should accumulate distance"
    assert p2.z > 0, "Z should increase"

    # Speed increase
    p3 = Player()
    old_speed = p3.speed
    for _ in range(100):
        p3.update(0.1)
    assert p3.speed > old_speed, "Speed should increase over time"
    assert p3.speed <= Player.SPEED_MAX, f"Speed should not exceed max: {p3.speed}"

    # Reset
    p3.reset()
    assert p3.speed == Player.SPEED_INITIAL
    assert p3.distance == 0
    assert p3.z == 0
    assert p3.alive

    # Height property
    p4 = Player()
    assert p4.height == Player.HEIGHT_STANDING
    p4.sliding = True
    assert p4.height == Player.HEIGHT_SLIDING

def segment_tests():
    # Basic creation
    s = Segment(10.0)
    assert s.z == 10.0
    assert not s.has_obstacle
    assert len(s.coins) == 0
    assert not s.passed

    # Obstacle Z
    expected_z = 10.0 + SEGMENT_LENGTH * 0.4
    assert abs(s.obstacle_z() - expected_z) < 0.001

    # Generate with low difficulty - might or might not have obstacle
    s.generate(0.0, [])
    # At difficulty 0, chance is 12%, so it's random. Just verify no crash.

    # Generate many segments to verify obstacle types
    types_seen = set()
    for _ in range(200):
        s2 = Segment(_ * SEGMENT_LENGTH)
        s2.generate(10.0, [])  # max difficulty
        if s2.has_obstacle:
            types_seen.add(s2.obstacle_type)
            assert s2.obstacle_type in ('wall', 'barrier', 'beam')
    assert len(types_seen) == 3, f"Should see all obstacle types: {types_seen}"

    # Coins
    coin = Coin(0, 1.5, 0.6)
    assert coin.lane == 0
    assert coin.z_offset == 1.5
    assert not coin.collected
    assert coin.anim_offset >= 0

    # World X
    cx = coin.world_x
    expected_lane_center = -3.0 + 0 * 2.0 + 1.0  # -HALF_WIDTH + lane * LANE_WIDTH + LANE_WIDTH/2
    assert abs(cx - expected_lane_center) < 0.001, f"Coin world_x={cx}, expected={expected_lane_center}"

    # Reset
    s3 = Segment(0)
    s3.generate(5.0, [])
    s3.passed = True
    s3.reset(100.0)
    assert s3.z == 100.0
    assert not s3.has_obstacle
    assert len(s3.coins) == 0
    assert not s3.passed

    # Obstacle world x
    s4 = Segment(0)
    s4.obstacle_lane = 1
    owx = s4.obstacle_world_x()
    assert abs(owx) < 0.001, f"Center lane obstacle should be at x=0: {owx}"

    s4.obstacle_lane = 0
    owx = s4.obstacle_world_x()
    assert owx < 0, f"Left lane should be negative: {owx}"

def corridor_tests():
    c = Corridor()
    assert len(c.segments) == Corridor().total_segments

    # All segments should be in order
    for i in range(1, len(c.segments)):
        assert c.segments[i].z > c.segments[i-1].z, "Segments should be ordered"

    # First segment should be at z=0
    assert c.segments[0].z == 0

    # Spacing should be SEGMENT_LENGTH
    assert abs(c.segments[1].z - c.segments[0].z - SEGMENT_LENGTH) < 0.001

    # Update with player movement
    player_z = 0
    c.update(player_z)
    assert len(c.segments) == c.total_segments

    # Player moves forward - segments should recycle
    player_z = 50
    c.update(player_z)

    # After player moves, segments ahead should cover more ground
    max_z = max(s.z for s in c.segments)
    assert max_z > player_z + 20, f"Should have segments ahead: max_z={max_z}"

    # Active segments
    active = c.get_active_segments(player_z)
    assert len(active) > 0
    for seg in active:
        assert seg.z - player_z <= 65, f"Segment too far: {seg.z - player_z}"

    # Collision detection
    p = Player()
    p.z = 10
    c2 = Corridor()

    # Place an obstacle right in front of player
    c2.segments[3].has_obstacle = True
    c2.segments[3].obstacle_type = 'wall'
    c2.segments[3].obstacle_lane = 1  # center lane
    # Player starts in center lane
    p.lane = 1
    p.x = 0
    p.z = c2.segments[3].z + SEGMENT_LENGTH / 2 + 0.1  # just entering segment
    p.y = 0
    p.sliding = False
    p.alive = True

    assert c2.check_obstacle_collision(p), "Wall in center lane should collide"

    # Player in different lane should be safe
    p.reset()
    p.z = c2.segments[3].z + SEGMENT_LENGTH / 2 + 0.1
    p.lane = 0
    assert not c2.check_obstacle_collision(p), "Different lane should be safe"

    # Jump over barrier
    p.reset()
    c2.segments[3].obstacle_type = 'barrier'
    p.z = c2.segments[3].z + SEGMENT_LENGTH / 2 + 0.1
    p.lane = 1
    p.vy = 10
    p.y = 0.8  # in the air
    assert not c2.check_obstacle_collision(p), "Jumping over barrier should be safe"

    # Not jumping = hit
    p.reset()
    p.z = c2.segments[3].z + SEGMENT_LENGTH / 2 + 0.1
    p.lane = 1
    p.y = 0
    # Need a new segment since the old one was marked passed
    c2.segments[4].has_obstacle = True
    c2.segments[4].obstacle_type = 'barrier'
    c2.segments[4].obstacle_lane = 1
    p.z = c2.segments[4].z + SEGMENT_LENGTH / 2 + 0.1
    assert c2.check_obstacle_collision(p), "Not jumping barrier should collide"

    # Slide under beam
    p.reset()
    c2.segments[5].has_obstacle = True
    c2.segments[5].obstacle_type = 'beam'
    c2.segments[5].obstacle_lane = 1
    p.z = c2.segments[5].z + SEGMENT_LENGTH / 2 + 0.1
    p.lane = 1
    p.sliding = True
    assert not c2.check_obstacle_collision(p), "Sliding under beam should be safe"

    # Not sliding = hit
    p.reset()
    c2.segments[6].has_obstacle = True
    c2.segments[6].obstacle_type = 'beam'
    c2.segments[6].obstacle_lane = 1
    p.z = c2.segments[6].z + SEGMENT_LENGTH / 2 + 0.1
    p.lane = 1
    p.sliding = False
    assert c2.check_obstacle_collision(p), "Not sliding under beam should collide"

    # Coin collection
    c3 = Corridor()
    p2 = Player()

    # Place a coin in player's path
    test_seg = c3.segments[3]
    coin = Coin(1, SEGMENT_LENGTH / 2)  # center lane, middle of segment
    test_seg.coins.append(coin)

    p2.z = test_seg.z + SEGMENT_LENGTH / 2
    p2.lane = 1
    coins = c3.check_coin_collection(p2)
    assert coins == 1, f"Should collect 1 coin, got {coins}"
    assert coin.collected, "Coin should be marked collected"

    # Same coin shouldn't be collected twice
    coins = c3.check_coin_collection(p2)
    assert coins == 0, "Already collected coin should not count again"

    # Player in different lane shouldn't collect
    c3.segments[4].coins.append(Coin(0, SEGMENT_LENGTH / 2))
    p2.z = c3.segments[4].z + SEGMENT_LENGTH / 2
    p2.lane = 1
    coins = c3.check_coin_collection(p2)
    assert coins == 0, "Different lane shouldn't collect"

def reset_tests():
    # Test full game reset
    c = Corridor()
    p = Player()

    # Change some state
    p.move_left()
    p.jump()
    p.update(0.5)
    c.update(100)

    # Reset
    p.reset()
    c.reset()

    assert p.lane == 1
    assert p.x == 0
    assert p.y == 0
    assert p.z == 0
    assert p.speed == Player.SPEED_INITIAL
    assert p.alive
    assert c.difficulty == 0
    assert len(c.segments) == c.total_segments
    assert c.segments[0].z == 0

def difficulty_tests():
    # Higher difficulty = more obstacles
    c_easy = Corridor()
    c_hard = Corridor()

    # Force difficulty
    c_easy.difficulty = 0
    c_hard.difficulty = 10

    # Regenerate all segments
    c_easy.segments = []
    c_hard.segments = []
    for i in range(100):
        s_easy = Segment(i * SEGMENT_LENGTH)
        s_hard = Segment(i * SEGMENT_LENGTH)
        s_easy.generate(0, [])
        s_hard.generate(10, [])
        c_easy.segments.append(s_easy)
        c_hard.segments.append(s_hard)

    easy_obs = sum(1 for s in c_easy.segments if s.has_obstacle)
    hard_obs = sum(1 for s in c_hard.segments if s.has_obstacle)

    # Hard should have more obstacles (statistically)
    assert hard_obs > easy_obs, \
        f"Hard difficulty ({hard_obs}) should have more obstacles than easy ({easy_obs})"

# ── Edge Case Tests ──────────────────────────────────────────────
def edge_case_tests():
    # Camera at various screen sizes
    for w, h in [(400, 720), (1080, 2400), (720, 1280)]:
        cam = Camera(w, h)
        assert cam.screen_width == w
        assert cam.screen_height == h

    # Player update with zero dt
    p = Player()
    old_z = p.z
    p.update(0)
    assert p.z == old_z, "Zero dt shouldn't move player"

    # Player update with large dt (lag spike)
    p.update(0.1)  # should be capped at 0.05

    # Jump while already jumping shouldn't work
    p.y = 1.0
    p.jump()
    assert p.vy == 0, "Can't double jump"
    p.y = 0
    p.jump()  # should work

    # Slide while in air shouldn't work
    p.sliding = False
    p.slide_timer = 0
    p.y = 0
    p.vy = 0
    p.jump()  # vy > 0 but y is still 0
    assert p.vy > 0
    p.update(0.05)  # now actually in the air
    assert p.y > 0, f"Should be in air: y={p.y}"
    p.slide()
    assert not p.sliding, "Can't slide while in air"

    # Consecutive obstacles in same lane should be prevented
    segs = []
    for i in range(10):
        s = Segment(i * SEGMENT_LENGTH)
        prev = segs[:i]
        s.generate(10.0, prev)
        segs.append(s)

    # Check no two consecutive obstacles in same lane
    for i in range(1, len(segs)):
        if segs[i].has_obstacle and segs[i-1].has_obstacle:
            assert segs[i].obstacle_lane != segs[i-1].obstacle_lane, \
                f"Consecutive obstacles in same lane at segments {i-1} and {i}"


# ── Run Tests ──────────────────────────────────────────────────
print("═" * 50)
print("Temple Run - Game Logic Tests")
print("═" * 50)

print("\n📐 Camera Tests")
test("Camera creation and projection", camera_tests)

print("\n🏃 Player Tests")
test("Player movement and physics", player_tests)

print("\n🧱 Segment Tests")
test("Segment generation and coins", segment_tests)

print("\n🛤️  Corridor Tests")
test("Corridor management and collision", corridor_tests)

print("\n🔄 Reset Tests")
test("Full game reset", reset_tests)

print("\n📈 Difficulty Tests")
test("Difficulty scaling", difficulty_tests)

print("\n⚡ Edge Case Tests")
test("Edge cases and constraints", edge_case_tests)

print("\n" + "═" * 50)
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")

if failed > 0:
    print("❌ SOME TESTS FAILED")
    sys.exit(1)
else:
    print("✅ ALL TESTS PASSED")
