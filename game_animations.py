"""
animations.py - Animation system for Ludo game.
Handles particles, dice rolling, lerp movement, glow effects, confetti, floating orbs.
All animations are delta-time based for consistent 60 FPS.
"""

import pygame
import math
import random


# ─── Easing Functions ───────────────────────────────────────────────
def lerp(a, b, t):
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * max(0.0, min(1.0, t))


def lerp_pos(pos_a, pos_b, t):
    """Lerp between two (x, y) positions."""
    return (lerp(pos_a[0], pos_b[0], t), lerp(pos_a[1], pos_b[1], t))


def ease_out_cubic(t):
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_cubic(t):
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def ease_out_bounce(t):
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


# ─── Particle ───────────────────────────────────────────────────────
class Particle:
    """A single particle with position, velocity, color, lifetime, and gravity."""

    def __init__(self, x, y, color, velocity, lifetime, size, gravity=200):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.gravity = gravity

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface):
        alpha = max(0.0, self.lifetime / self.max_lifetime)
        size = max(1, int(self.size * alpha))
        r, g, b = self.color[0], self.color[1], self.color[2]
        a = int(255 * alpha)
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (r, g, b, a), (size, size), size)
        surface.blit(s, (int(self.x - size), int(self.y - size)))


# ─── Particle System ────────────────────────────────────────────────
class ParticleSystem:
    """Manages collections of particles for burst and confetti effects."""

    def __init__(self):
        self.particles = []

    def emit_burst(self, x, y, color, count=30):
        """Burst explosion at (x, y) with given color."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(120, 450)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 150
            lifetime = random.uniform(0.4, 1.2)
            size = random.randint(3, 9)
            self.particles.append(Particle(x, y, color, (vx, vy), lifetime, size))

    def emit_confetti(self, width, height, count=80):
        """Confetti rain from the top of the screen."""
        colors = [
            (255, 71, 87), (46, 213, 115), (55, 66, 250),
            (255, 234, 167), (255, 107, 129), (116, 185, 255),
            (253, 203, 110), (0, 210, 211), (255, 165, 2),
        ]
        for _ in range(count):
            x = random.randint(0, width)
            y = random.randint(-100, -10)
            color = random.choice(colors)
            vx = random.uniform(-40, 40)
            vy = random.uniform(80, 280)
            lifetime = random.uniform(2.5, 5.0)
            size = random.randint(3, 8)
            self.particles.append(Particle(x, y, color, (vx, vy), lifetime, size, gravity=60))

    def emit_golden_glow(self, x, y, count=15):
        """Golden glow pulse effect for home entry."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 120)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.5, 1.0)
            size = random.randint(4, 10)
            gold = (255, 215, 0)
            self.particles.append(Particle(x, y, gold, (vx, vy), lifetime, size, gravity=0))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    @property
    def active(self):
        return len(self.particles) > 0


# ─── Floating Orb (Menu Background) ─────────────────────────────────
class FloatingOrb:
    """Subtle floating colored orb for menu particle background."""

    def __init__(self, x, y, color, speed, radius):
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y
        self.color = color
        self.speed = speed
        self.radius = radius
        self.angle = random.uniform(0, 2 * math.pi)
        self.drift_radius = random.uniform(25, 70)

    def update(self, dt):
        self.angle += self.speed * dt
        self.x = self.base_x + math.cos(self.angle) * self.drift_radius
        self.y = self.base_y + math.sin(self.angle * 0.7) * self.drift_radius

    def draw(self, surface):
        s = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        for r in range(self.radius, 0, -2):
            a = int(35 * (r / self.radius))
            pygame.draw.circle(s, (*self.color, a), (self.radius * 2, self.radius * 2), r)
        surface.blit(s, (int(self.x - self.radius * 2), int(self.y - self.radius * 2)))


# ─── Dice Roller ─────────────────────────────────────────────────────
class DiceRoller:
    """Animated dice with spinning effect and glow highlight."""

    def __init__(self):
        self.rolling = False
        self.roll_time = 0.0
        self.roll_duration = 0.6
        self.current_face = 1
        self.final_face = 1
        self.glow_time = 0.0
        self.glow_duration = 1.0
        self.finished = False

    def start_roll(self, final_value):
        self.rolling = True
        self.roll_time = 0.0
        self.final_face = final_value
        self.glow_time = 0.0
        self.finished = False

    def update(self, dt):
        if self.rolling:
            self.roll_time += dt
            if self.roll_time >= self.roll_duration:
                self.rolling = False
                self.current_face = self.final_face
                self.glow_time = self.glow_duration
                self.finished = True
            else:
                self.current_face = random.randint(1, 6)
        if self.glow_time > 0:
            self.glow_time = max(0, self.glow_time - dt)

    def draw(self, surface, x, y, size=80):
        half = size // 2

        # Glow behind dice
        if self.glow_time > 0:
            glow_alpha = int(80 * (self.glow_time / self.glow_duration))
            gs = pygame.Surface((size + 24, size + 24), pygame.SRCALPHA)
            pygame.draw.rect(gs, (255, 215, 0, glow_alpha), (0, 0, size + 24, size + 24), border_radius=16)
            surface.blit(gs, (x - half - 12, y - half - 12))

        # Rolling scale wobble
        scale = 1.0
        if self.rolling:
            t = self.roll_time / self.roll_duration
            scale = 1.0 + 0.12 * math.sin(t * math.pi * 10)
        actual_size = int(size * scale)
        ah = actual_size // 2

        # Shadow
        shadow_r = pygame.Rect(x - ah + 3, y - ah + 3, actual_size, actual_size)
        ss = pygame.Surface((actual_size, actual_size), pygame.SRCALPHA)
        pygame.draw.rect(ss, (0, 0, 0, 60), (0, 0, actual_size, actual_size), border_radius=12)
        surface.blit(ss, shadow_r.topleft)

        # Dice body
        body_r = pygame.Rect(x - ah, y - ah, actual_size, actual_size)
        pygame.draw.rect(surface, (245, 245, 250), body_r, border_radius=12)
        pygame.draw.rect(surface, (180, 180, 190), body_r, width=2, border_radius=12)

        # Pips
        self._draw_pips(surface, x, y, actual_size, self.current_face)

    def _draw_pips(self, surface, cx, cy, size, value):
        pr = max(3, size // 10)
        off = size // 4
        positions = {
            1: [(0, 0)],
            2: [(-off, -off), (off, off)],
            3: [(-off, -off), (0, 0), (off, off)],
            4: [(-off, -off), (off, -off), (-off, off), (off, off)],
            5: [(-off, -off), (off, -off), (0, 0), (-off, off), (off, off)],
            6: [(-off, -off), (off, -off), (-off, 0), (off, 0), (-off, off), (off, off)],
        }
        pip_color = (40, 40, 50)
        for dx, dy in positions.get(value, [(0, 0)]):
            pygame.draw.circle(surface, pip_color, (cx + dx, cy + dy), pr)


# ─── Turn Banner ─────────────────────────────────────────────────────
class TurnBanner:
    """Color-coded banner that slides in from top on turn change."""

    def __init__(self):
        self.active = False
        self.time = 0.0
        self.duration = 1.5
        self.text = ""
        self.color = (255, 255, 255)
        self.bg_color = (50, 50, 50)

    def show(self, text, color):
        self.active = True
        self.time = 0.0
        self.text = text
        self.color = color
        self.bg_color = tuple(max(0, c // 3) for c in color)

    def update(self, dt):
        if self.active:
            self.time += dt
            if self.time >= self.duration:
                self.active = False

    def draw(self, surface, font):
        if not self.active:
            return
        t = self.time / self.duration
        if t < 0.2:
            slide = ease_out_cubic(t / 0.2)
        elif t < 0.7:
            slide = 1.0
        else:
            slide = 1.0 - ease_out_cubic((t - 0.7) / 0.3)

        banner_h = 50
        y = int(-banner_h + slide * (banner_h + 10))
        w = surface.get_width()

        bs = pygame.Surface((w, banner_h), pygame.SRCALPHA)
        pygame.draw.rect(bs, (*self.bg_color, 200), (0, 0, w, banner_h))
        # Color strip at bottom
        pygame.draw.rect(bs, (*self.color, 220), (0, banner_h - 4, w, 4))

        txt = font.render(self.text, True, self.color)
        bs.blit(txt, (w // 2 - txt.get_width() // 2, banner_h // 2 - txt.get_height() // 2))
        surface.blit(bs, (0, y))


# ─── Animation Manager ──────────────────────────────────────────────
class AnimationManager:
    """Central manager for all animation systems."""

    def __init__(self):
        self.particles = ParticleSystem()
        self.dice = DiceRoller()
        self.banner = TurnBanner()
        self.token_anims = {}
        self.menu_orbs = []
        self._init_menu_orbs()
        self.confetti_timer = 0.0

    def _init_menu_orbs(self):
        colors = [
            (230, 57, 70), (69, 123, 157), (42, 157, 143), (233, 196, 106),
            (255, 107, 129), (116, 185, 255), (253, 203, 110),
        ]
        for _ in range(18):
            x = random.randint(50, 1050)
            y = random.randint(50, 700)
            c = random.choice(colors)
            speed = random.uniform(0.3, 0.9)
            radius = random.randint(20, 55)
            self.menu_orbs.append(FloatingOrb(x, y, c, speed, radius))

    def start_token_move(self, token_id, start_pos, end_pos, duration=0.25):
        """Start a lerp animation for a token."""
        self.token_anims[token_id] = {
            "start": start_pos,
            "end": end_pos,
            "time": 0.0,
            "duration": duration,
        }

    def get_token_anim_pos(self, token_id):
        """Get current animated position for a token, or None if not animating."""
        if token_id not in self.token_anims:
            return None
        anim = self.token_anims[token_id]
        t = min(1.0, anim["time"] / anim["duration"])
        t = ease_out_cubic(t)
        return lerp_pos(anim["start"], anim["end"], t)

    def is_token_animating(self, token_id):
        return token_id in self.token_anims

    def any_token_animating(self):
        return len(self.token_anims) > 0

    def update(self, dt):
        self.particles.update(dt)
        self.dice.update(dt)
        self.banner.update(dt)
        for orb in self.menu_orbs:
            orb.update(dt)

        # Update token animations
        done = []
        for tid, anim in self.token_anims.items():
            anim["time"] += dt
            if anim["time"] >= anim["duration"]:
                done.append(tid)
        for tid in done:
            del self.token_anims[tid]

    def draw_menu_bg(self, surface):
        for orb in self.menu_orbs:
            orb.draw(surface)

    def draw_particles(self, surface):
        self.particles.draw(surface)

    def draw_banner(self, surface, font):
        self.banner.draw(surface, font)
