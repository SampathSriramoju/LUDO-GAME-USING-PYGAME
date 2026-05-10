"""
token.py - Token and Player classes for Ludo game.
Handles token state, drawing with glow/shadow, stacking badges, and idle bob animation.
"""

import pygame
import math
from board import (COLORS, COLOR_LIGHT, COLOR_DARK, BASE_POSITIONS, START_INDICES,
                   SAFE_INDICES, HOME_COLUMNS, MAIN_PATH, CELL_SIZE, get_global_index)


# Token states
STATE_BASE = 0
STATE_ACTIVE = 1
STATE_HOME = 2

TOKEN_RADIUS = 16
SHADOW_OFFSET = 3


class Token:
    """A single Ludo token/piece."""

    def __init__(self, color, index):
        self.color = color        # "red", "green", "yellow", "blue"
        self.index = index        # 0-3 within the player
        self.state = STATE_BASE
        self.steps = -1           # -1 = in base, 0-51 = main path, 52-57 = home column
        self.token_id = f"{color}_{index}"

    def enter_board(self):
        """Place token at start position (after rolling 6)."""
        self.state = STATE_ACTIVE
        self.steps = 0

    def move(self, dice_value):
        """Move token forward by dice_value steps. Returns new steps value."""
        if self.state != STATE_ACTIVE:
            return self.steps
        self.steps += dice_value
        if self.steps >= 57:
            self.steps = 57
            self.state = STATE_HOME
        return self.steps

    def send_to_base(self):
        """Send token back to base."""
        self.state = STATE_BASE
        self.steps = -1

    def can_move(self, dice_value):
        """Check if this token can legally move with the given dice value."""
        if self.state == STATE_HOME:
            return False
        if self.state == STATE_BASE:
            return dice_value == 6
        # Active token
        new_steps = self.steps + dice_value
        if new_steps > 57:
            return False  # Need exact roll to enter home
        return True

    def get_global_path_index(self):
        """Get the global main path index (0-51) or None if in base/home column."""
        return get_global_index(self.color, self.steps)

    def is_on_safe_square(self):
        """Check if token is on a safe square."""
        if self.state != STATE_ACTIVE:
            return self.state == STATE_HOME
        gi = self.get_global_path_index()
        if gi is not None and gi in SAFE_INDICES:
            return True
        if self.steps >= 52:
            return True  # Home column
        return False

    def get_base_position(self):
        """Get pixel position when in base."""
        return BASE_POSITIONS[self.color][self.index]

    def copy_state(self):
        """Return a dict of the current state for undo purposes."""
        return {"state": self.state, "steps": self.steps}

    def restore_state(self, saved):
        """Restore state from a saved dict."""
        self.state = saved["state"]
        self.steps = saved["steps"]


class Player:
    """A Ludo player (human or bot) with 4 tokens."""

    def __init__(self, color, name, is_bot=False):
        self.color = color
        self.name = name
        self.is_bot = is_bot
        self.tokens = [Token(color, i) for i in range(4)]
        self.consecutive_sixes = 0
        self.last_moved_token = None

    @property
    def tokens_home(self):
        """Count of tokens that have reached home."""
        return sum(1 for t in self.tokens if t.state == STATE_HOME)

    @property
    def tokens_in_base(self):
        """Count of tokens still in base."""
        return sum(1 for t in self.tokens if t.state == STATE_BASE)

    @property
    def tokens_active(self):
        """Count of tokens on the board."""
        return sum(1 for t in self.tokens if t.state == STATE_ACTIVE)

    @property
    def has_won(self):
        """Check if all 4 tokens have reached home."""
        return self.tokens_home == 4

    def get_valid_moves(self, dice_value):
        """Return list of token indices that can move with given dice value."""
        moves = []
        for i, token in enumerate(self.tokens):
            if token.can_move(dice_value):
                moves.append(i)
        return moves

    def reset(self):
        """Reset player state for a new game."""
        self.tokens = [Token(self.color, i) for i in range(4)]
        self.consecutive_sixes = 0
        self.last_moved_token = None


def draw_token(surface, x, y, color_name, bob_offset=0, count=1):
    """Draw a token at pixel position with glow, shadow, and optional stack badge."""
    color = COLORS[color_name]
    light = COLOR_LIGHT[color_name]
    dark = COLOR_DARK[color_name]
    ty = y + int(bob_offset)

    # Drop shadow
    shadow_surf = pygame.Surface((TOKEN_RADIUS * 3, TOKEN_RADIUS * 3), pygame.SRCALPHA)
    pygame.draw.circle(shadow_surf, (0, 0, 0, 50),
                       (TOKEN_RADIUS * 3 // 2, TOKEN_RADIUS * 3 // 2), TOKEN_RADIUS + 2)
    surface.blit(shadow_surf,
                 (x - TOKEN_RADIUS * 3 // 2 + SHADOW_OFFSET,
                  ty - TOKEN_RADIUS * 3 // 2 + SHADOW_OFFSET))

    # Outer glow
    glow_surf = pygame.Surface((TOKEN_RADIUS * 4, TOKEN_RADIUS * 4), pygame.SRCALPHA)
    for r in range(TOKEN_RADIUS + 8, TOKEN_RADIUS, -1):
        alpha = int(30 * ((TOKEN_RADIUS + 8 - r) / 8))
        pygame.draw.circle(glow_surf, (*color, alpha),
                           (TOKEN_RADIUS * 2, TOKEN_RADIUS * 2), r)
    surface.blit(glow_surf, (x - TOKEN_RADIUS * 2, ty - TOKEN_RADIUS * 2))

    # Main body
    pygame.draw.circle(surface, dark, (x, ty), TOKEN_RADIUS)
    pygame.draw.circle(surface, color, (x, ty), TOKEN_RADIUS - 2)

    # Inner glow (highlight)
    inner_surf = pygame.Surface((TOKEN_RADIUS * 2, TOKEN_RADIUS * 2), pygame.SRCALPHA)
    pygame.draw.circle(inner_surf, (*light, 120),
                       (TOKEN_RADIUS, TOKEN_RADIUS - 3), TOKEN_RADIUS // 2)
    surface.blit(inner_surf, (x - TOKEN_RADIUS, ty - TOKEN_RADIUS))

    # Center dot
    pygame.draw.circle(surface, light, (x, ty - 2), 4)

    # Stack badge
    if count > 1:
        badge_r = 10
        bx = x + TOKEN_RADIUS - 4
        by = ty - TOKEN_RADIUS + 4
        pygame.draw.circle(surface, (30, 30, 40), (bx, by), badge_r)
        pygame.draw.circle(surface, color, (bx, by), badge_r, width=2)
        try:
            font = pygame.font.SysFont("Arial", 13, bold=True)
        except Exception:
            font = pygame.font.Font(None, 15)
        txt = font.render(f"×{count}", True, (255, 255, 255))
        surface.blit(txt, (bx - txt.get_width() // 2, by - txt.get_height() // 2))
