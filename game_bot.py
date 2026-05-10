"""
game_bot.py - Bot AI for Ludo game.
Priority-based decision engine with scored moves.
Kill=100, Unlock=75, Advance=50+distance_bonus, Safety=+25 bonus.
"""

import random
from game_token import Player, STATE_BASE, STATE_ACTIVE, STATE_HOME
from board import (MAIN_PATH, START_INDICES, SAFE_INDICES, get_global_index,
                   is_safe_square, COLOR_ORDER)


class Bot(Player):
    """AI-controlled Ludo player with priority-based decision making."""

    def __init__(self, color, name="BOT 🤖"):
        super().__init__(color, name, is_bot=True)
        self.think_delay = random.uniform(0.8, 1.2)
        self.thinking = False
        self.think_timer = 0.0
        self.pending_move = None

    def start_thinking(self, dice_value, all_players):
        """Begin the thinking phase with delay before executing move."""
        self.thinking = True
        self.think_timer = 0.0
        self.think_delay = random.uniform(0.8, 1.2)
        self.pending_move = self._choose_move(dice_value, all_players)

    def update_thinking(self, dt):
        """Update thinking timer. Returns True when done thinking."""
        if not self.thinking:
            return False
        self.think_timer += dt
        if self.think_timer >= self.think_delay:
            self.thinking = False
            return True
        return False

    def get_pending_move(self):
        """Return the chosen token index (or None if no valid move)."""
        move = self.pending_move
        self.pending_move = None
        return move

    def _choose_move(self, dice_value, all_players):
        """Score all valid moves and pick the highest scoring one."""
        valid = self.get_valid_moves(dice_value)
        if not valid:
            return None

        best_score = -1
        best_token = None
        opponents = [p for p in all_players if p.color != self.color]

        for ti in valid:
            score = self._score_move(ti, dice_value, opponents)
            if score > best_score:
                best_score = score
                best_token = ti

        return best_token

    def _score_move(self, token_idx, dice_value, opponents):
        """Score a potential move for the given token."""
        token = self.tokens[token_idx]
        score = 0

        # Case 1: Token is in base (dice must be 6 to unlock)
        if token.state == STATE_BASE:
            score = 75
            start_gi = START_INDICES[self.color]
            if self._opponent_at_global(start_gi, opponents):
                if start_gi not in SAFE_INDICES:
                    score = 100
            return score

        # Case 2: Token is active — simulate the move
        new_steps = token.steps + dice_value

        # Reaching home exactly
        if new_steps == 57:
            return 150

        if new_steps > 57:
            return -1

        # Check for kill opportunity
        if new_steps < 52:
            new_gi = get_global_index(self.color, new_steps)
            if new_gi is not None and new_gi not in SAFE_INDICES:
                if self._opponent_at_global(new_gi, opponents):
                    score = 100
                    return score

        # Advance score: based on how close to home
        score = 50 + (new_steps * 0.5)

        # Safety bonus: moving to a safe square
        if is_safe_square(self.color, new_steps):
            score += 25

        # Penalty: leaving a safe square for an unsafe one
        if token.is_on_safe_square() and not is_safe_square(self.color, new_steps):
            score -= 15

        # Bonus for entering home column
        if new_steps >= 52:
            score += 30

        return score

    def _opponent_at_global(self, global_idx, opponents):
        """Check if any opponent token is at the given global main path index."""
        for opp in opponents:
            for t in opp.tokens:
                if t.state == STATE_ACTIVE and t.steps < 52:
                    opp_gi = get_global_index(opp.color, t.steps)
                    if opp_gi == global_idx:
                        return True
        return False
