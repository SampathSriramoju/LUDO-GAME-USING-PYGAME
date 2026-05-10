"""
board.py - Ludo board rendering and coordinate system.
15x15 grid, 750x750 pixel board area. Cell size = 50px.
"""

import pygame
import math

# ─── CONSTANTS ───────────────────────────────────────────────────────
CELL_SIZE = 50
BOARD_PX = 750
GRID = 15

# Color palette
COLORS = {
    "red":    (230, 57, 70),
    "green":  (42, 157, 143),
    "yellow": (233, 196, 106),
    "blue":   (69, 123, 157),
}
COLOR_DARK = {
    "red":    (160, 30, 40),
    "green":  (25, 110, 100),
    "yellow": (180, 150, 60),
    "blue":   (40, 80, 120),
}
COLOR_LIGHT = {
    "red":    (255, 120, 130),
    "green":  (100, 210, 190),
    "yellow": (255, 230, 160),
    "blue":   (130, 175, 210),
}

BG_COLOR = (13, 27, 42)
BOARD_BG = (20, 36, 55)
GRID_LINE = (30, 50, 70)
PATH_COLOR = (40, 60, 85)
CENTER_COLOR = (50, 70, 95)
SAFE_STAR_COLOR = (255, 215, 0)

# ─── 52-cell main path as (row, col) ────────────────────────────────
MAIN_PATH = [
    (6,1),(6,2),(6,3),(6,4),(6,5),           # 0-4   (Red start area)
    (5,6),(4,6),(3,6),(2,6),(1,6),(0,6),      # 5-10  (going up)
    (0,7),(0,8),                               # 11-12 (top edge)
    (1,8),(2,8),(3,8),(4,8),(5,8),            # 13-17 (Green start area, going down)
    (6,9),(6,10),(6,11),(6,12),(6,13),(6,14), # 18-23 (going right)
    (7,14),(8,14),                             # 24-25 (right edge)
    (8,13),(8,12),(8,11),(8,10),(8,9),        # 26-30 (Yellow start area, going left)
    (9,8),(10,8),(11,8),(12,8),(13,8),(14,8), # 31-36 (going down)
    (14,7),(14,6),                             # 37-38 (bottom edge)
    (13,6),(12,6),(11,6),(10,6),(9,6),        # 39-43 (Blue start area, going up)
    (8,5),(8,4),(8,3),(8,2),(8,1),(8,0),      # 44-49 (going left)
    (7,0),(6,0),                               # 50-51 (left edge)
]

# Home columns (6 cells leading to center for each color)
HOME_COLUMNS = {
    "red":    [(7,1),(7,2),(7,3),(7,4),(7,5),(7,6)],
    "green":  [(1,7),(2,7),(3,7),(4,7),(5,7),(6,7)],
    "yellow": [(7,13),(7,12),(7,11),(7,10),(7,9),(7,8)],
    "blue":   [(13,7),(12,7),(11,7),(10,7),(9,7),(8,7)],
}

# Start index on main path for each color
START_INDICES = {"red": 0, "green": 13, "yellow": 26, "blue": 39}

# Safe square indices on main path
SAFE_INDICES = {0, 8, 13, 21, 26, 34, 39, 47}

# Base slot pixel positions (4 per color)
BASE_POSITIONS = {
    "red":    [(100,100),(200,100),(100,200),(200,200)],
    "green":  [(550,100),(650,100),(550,200),(650,200)],
    "yellow": [(550,550),(650,550),(550,650),(650,650)],
    "blue":   [(100,550),(200,550),(100,650),(200,650)],
}

# Base zone rectangles (for drawing colored home areas)
BASE_ZONES = {
    "red":    (0, 0, 6*CELL_SIZE, 6*CELL_SIZE),
    "green":  (9*CELL_SIZE, 0, 6*CELL_SIZE, 6*CELL_SIZE),
    "yellow": (9*CELL_SIZE, 9*CELL_SIZE, 6*CELL_SIZE, 6*CELL_SIZE),
    "blue":   (0, 9*CELL_SIZE, 6*CELL_SIZE, 6*CELL_SIZE),
}

# Order of play
COLOR_ORDER = ["red", "green", "yellow", "blue"]


def cell_to_pixel(row, col):
    """Convert grid (row, col) to pixel center (x, y)."""
    return (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)


def get_path_for_color(color):
    """Return the full path (main + home column) indices list for a color.
    Returns list of (row, col) for positions 0..57.
    Position 0 = entry on main path, 51 = last main cell, 52-57 = home column."""
    start = START_INDICES[color]
    path = []
    for i in range(52):
        idx = (start + i) % 52
        path.append(MAIN_PATH[idx])
    path.extend(HOME_COLUMNS[color])
    return path


def get_global_index(color, steps):
    """Given a color and steps taken, return the global main path index (0-51) or None if in home."""
    if steps < 0 or steps >= 52:
        return None
    start = START_INDICES[color]
    return (start + steps) % 52


def is_safe_square(color, steps):
    """Check if a token at given steps is on a safe square."""
    gi = get_global_index(color, steps)
    if gi is not None and gi in SAFE_INDICES:
        return True
    if steps >= 52:
        return True  # Home column is always safe
    return False


class Board:
    """Renders the Ludo board."""

    def __init__(self):
        self.paths = {c: get_path_for_color(c) for c in COLOR_ORDER}

    def get_pixel_pos(self, color, steps):
        """Get pixel position for a token of given color at given steps."""
        if steps < 0:
            return None
        path = self.paths[color]
        if steps >= len(path):
            return cell_to_pixel(*path[-1])
        return cell_to_pixel(*path[steps])

    def draw(self, surface):
        """Draw the complete board."""
        # Board background
        pygame.draw.rect(surface, BOARD_BG, (0, 0, BOARD_PX, BOARD_PX))

        # Draw colored base zones
        for color_name in COLOR_ORDER:
            zone = BASE_ZONES[color_name]
            c = COLORS[color_name]
            cd = COLOR_DARK[color_name]
            rect = pygame.Rect(zone)
            pygame.draw.rect(surface, cd, rect)
            inner = rect.inflate(-20, -20)
            pygame.draw.rect(surface, c, inner, border_radius=8)
            # Inner white area for base slots
            inner2 = rect.inflate(-50, -50)
            pygame.draw.rect(surface, (30, 45, 65), inner2, border_radius=12)
            pygame.draw.rect(surface, c, inner2, width=2, border_radius=12)

            # Draw base slot circles
            for bx, by in BASE_POSITIONS[color_name]:
                pygame.draw.circle(surface, (40, 55, 75), (bx, by), 18)
                pygame.draw.circle(surface, c, (bx, by), 18, width=2)

        # Draw the cross-shaped path cells
        self._draw_path_cells(surface)

        # Draw center home area
        self._draw_center(surface)

        # Draw home columns with gradient
        self._draw_home_columns(surface)

        # Draw safe square stars
        self._draw_safe_stars(surface)

        # Draw grid glow lines over path
        self._draw_grid_lines(surface)

    def _draw_path_cells(self, surface):
        """Draw all 52 main path cells."""
        for idx, (row, col) in enumerate(MAIN_PATH):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            # Check if this is a colored start position
            color_for_cell = None
            for cname, si in START_INDICES.items():
                if idx == si:
                    color_for_cell = cname
                    break

            if color_for_cell:
                pygame.draw.rect(surface, COLOR_DARK[color_for_cell], rect)
                inner = rect.inflate(-4, -4)
                pygame.draw.rect(surface, COLORS[color_for_cell], inner, border_radius=3)
            else:
                pygame.draw.rect(surface, PATH_COLOR, rect)
                inner = rect.inflate(-2, -2)
                pygame.draw.rect(surface, (50, 75, 100), inner, border_radius=2)

    def _draw_home_columns(self, surface):
        """Draw colored home column cells with gradient toward center."""
        for cname in COLOR_ORDER:
            cells = HOME_COLUMNS[cname]
            n = len(cells)
            for i, (row, col) in enumerate(cells):
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                # Gradient: gets brighter toward center
                t = (i + 1) / n
                base = COLORS[cname]
                bright = COLOR_LIGHT[cname]
                gc = tuple(int(base[j] + (bright[j] - base[j]) * t) for j in range(3))
                pygame.draw.rect(surface, gc, rect, border_radius=2)
                pygame.draw.rect(surface, COLOR_DARK[cname], rect, width=1, border_radius=2)

    def _draw_center(self, surface):
        """Draw the 3x3 center home area with triangles."""
        cx = 7 * CELL_SIZE + CELL_SIZE // 2
        cy = 7 * CELL_SIZE + CELL_SIZE // 2
        center_rect = pygame.Rect(6 * CELL_SIZE, 6 * CELL_SIZE, 3 * CELL_SIZE, 3 * CELL_SIZE)
        pygame.draw.rect(surface, CENTER_COLOR, center_rect)

        half = int(1.5 * CELL_SIZE)
        # Draw triangles pointing to center for each color
        # Top triangle (Green)
        pts = [(cx - half, cy - half), (cx + half, cy - half), (cx, cy)]
        pygame.draw.polygon(surface, COLORS["green"], pts)
        pygame.draw.polygon(surface, COLOR_DARK["green"], pts, width=2)
        # Right triangle (Yellow)
        pts = [(cx + half, cy - half), (cx + half, cy + half), (cx, cy)]
        pygame.draw.polygon(surface, COLORS["yellow"], pts)
        pygame.draw.polygon(surface, COLOR_DARK["yellow"], pts, width=2)
        # Bottom triangle (Blue)
        pts = [(cx + half, cy + half), (cx - half, cy + half), (cx, cy)]
        pygame.draw.polygon(surface, COLORS["blue"], pts)
        pygame.draw.polygon(surface, COLOR_DARK["blue"], pts, width=2)
        # Left triangle (Red)
        pts = [(cx - half, cy + half), (cx - half, cy - half), (cx, cy)]
        pygame.draw.polygon(surface, COLORS["red"], pts)
        pygame.draw.polygon(surface, COLOR_DARK["red"], pts, width=2)

        # Center circle
        pygame.draw.circle(surface, (60, 80, 110), (cx, cy), 18)
        pygame.draw.circle(surface, (200, 200, 220), (cx, cy), 18, width=2)

    def _draw_safe_stars(self, surface):
        """Draw star icons on safe squares."""
        for idx in SAFE_INDICES:
            row, col = MAIN_PATH[idx]
            cx = col * CELL_SIZE + CELL_SIZE // 2
            cy = row * CELL_SIZE + CELL_SIZE // 2
            self._draw_star(surface, cx, cy, 10, 5, SAFE_STAR_COLOR)

    def _draw_star(self, surface, cx, cy, outer_r, inner_r, color):
        """Draw a 5-pointed star."""
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = outer_r if i % 2 == 0 else inner_r
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(surface, color, points)

    def _draw_grid_lines(self, surface):
        """Draw subtle glowing grid lines over the path area."""
        glow_surf = pygame.Surface((BOARD_PX, BOARD_PX), pygame.SRCALPHA)
        for idx, (row, col) in enumerate(MAIN_PATH):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(glow_surf, (80, 120, 160, 20), rect, width=1)
        surface.blit(glow_surf, (0, 0))
