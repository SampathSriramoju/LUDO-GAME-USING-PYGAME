"""
main.py - Ludo Game Controller with Play vs Bots + Play With Friends modes.
State machine: MENU -> SELECT/FRIENDS_SELECT -> GAME -> WIN_SCREEN
"""
import pygame, sys, random, math
from board import (Board, COLORS, COLOR_ORDER, MAIN_PATH, START_INDICES,
                   SAFE_INDICES, BASE_POSITIONS, get_global_index, CELL_SIZE)
from game_token import Player, Token, draw_token, STATE_BASE, STATE_ACTIVE, STATE_HOME
from game_bot import Bot
from game_animations import AnimationManager
from game_ui import (Button, ColorCard, TextInput, get_font, draw_menu_screen,
                     draw_player_select, draw_friends_select, draw_hud,
                     draw_thinking_indicator, draw_win_screen)

ST_MENU, ST_SELECT, ST_GAME, ST_WIN, ST_FRIENDS = 0, 1, 2, 3, 4
PHASE_ROLL, PHASE_CHOOSE, PHASE_ANIMATE, PHASE_BOT_THINK, PHASE_NEXT_TURN, PHASE_TURN_DELAY = 0,1,2,3,4,5
WIDTH, HEIGHT, FPS = 1100, 750, 60

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("LUDO - The Classic Board Game")
        self.clock = pygame.time.Clock()
        self.board = Board()
        self.anim = AnimationManager()
        self.time_elapsed = 0.0
        self.state = ST_MENU
        self.phase = PHASE_ROLL
        self.friends_mode = False

        # Menu buttons
        cx = WIDTH // 2
        self.bots_btn = Button(cx - 140, 370, 280, 55, "🤖  Play vs Bots", (60, 120, 180))
        self.friends_btn = Button(cx - 140, 445, 280, 55, "👥  Play With Friends", (120, 80, 170))

        # Bot select UI
        self.num_players = 4
        self.selected_color = None
        self.num_btns = []
        self.color_cards = []
        self.start_btn = Button(cx - 100, 550, 200, 50, "START GAME", (42, 157, 143))
        self._init_select_ui()

        # Friends select UI
        self.friends_num_players = 4
        self.friends_num_btns = []
        self.name_inputs = []
        self.friends_start_btn = Button(cx - 100, 590, 200, 50, "▶  START GAME", (42, 157, 143))
        self._init_friends_ui()

        # Game state
        self.players = []
        self.current_idx = 0
        self.dice_value = 0
        self.turn_history = []
        self.roll_btn = Button(800, 400, 250, 45, "🎲  Roll Dice", (70, 110, 160))
        self.can_roll = True
        self.winner = None
        self.turn_delay_timer = 0.0
        self.confetti_timer = 0.0
        self._pending_after_dice = False
        self._pending_capture_check = False
        self._moved_token = None

        # Back button (shared between select screens)
        self.back_btn = Button(20, 15, 100, 40, "← Back", (80, 60, 60))

        # Win screen
        self.play_again_btn = Button(cx - 140, HEIGHT//2 + 80, 130, 50, "Play Again", (42, 157, 143))
        self.menu_btn = Button(cx + 10, HEIGHT//2 + 80, 130, 50, "Main Menu", (100, 80, 150))

    def _init_select_ui(self):
        cx = WIDTH // 2
        for i, n in enumerate([2, 3, 4]):
            self.num_btns.append(Button(cx + (i-1)*70 - 25, 150, 60, 40, str(n), (60, 100, 150)))
        card_w, total_w = 140, 4*140 + 3*15
        sx = cx - total_w // 2
        for i, cn in enumerate(COLOR_ORDER):
            self.color_cards.append(ColorCard(sx + i*(card_w+15), 250, card_w, 80, cn, cn.capitalize()))

    def _init_friends_ui(self):
        cx = WIDTH // 2
        for i, n in enumerate([2, 3, 4]):
            self.friends_num_btns.append(Button(cx + (i-1)*70 - 25, 150, 60, 40, str(n), (60, 100, 150)))
        for i in range(4):
            self.name_inputs.append(TextInput(0, 0, 160, 34, placeholder=f"Player {i+1}"))

    def _setup_bot_game(self):
        self.players = []
        self.friends_mode = False
        for cn in COLOR_ORDER[:self.num_players]:
            if cn == self.selected_color:
                self.players.append(Player(cn, "YOU"))
            else:
                self.players.append(Bot(cn, "BOT 🤖"))
        self._reset_game_state()

    def _setup_friends_game(self):
        self.players = []
        self.friends_mode = True
        for i, cn in enumerate(COLOR_ORDER[:self.friends_num_players]):
            name = self.name_inputs[i].text.strip() if i < len(self.name_inputs) else ""
            if not name:
                name = f"Player {i+1}"
            self.players.append(Player(cn, name))
        self._reset_game_state()

    def _reset_game_state(self):
        self.current_idx = 0
        self.dice_value = 0
        self.phase = PHASE_ROLL
        self.can_roll = True
        self.turn_history = []
        self.winner = None
        self.confetti_timer = 0.0
        self.turn_delay_timer = 0.0
        self._pending_after_dice = False
        self._pending_capture_check = False
        for p in self.players:
            p.reset()
        if self.friends_mode and self.players:
            p = self.players[0]
            self.anim.banner.show(f"🎲 {p.name.upper()}'s TURN!", COLORS[p.color])
            self.anim.banner.duration = 2.5
            self.phase = PHASE_TURN_DELAY
            self.turn_delay_timer = 2.0
            self.can_roll = False

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.time_elapsed += dt
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            events = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_click = True
                events.append(event)
            self.anim.update(dt)

            if self.state == ST_MENU:
                self._update_menu(dt, mouse_pos, mouse_click)
                self._draw_menu()
            elif self.state == ST_SELECT:
                self._update_select(dt, mouse_pos, mouse_click)
                self._draw_select()
            elif self.state == ST_FRIENDS:
                self._update_friends(dt, mouse_pos, mouse_click, events)
                self._draw_friends()
            elif self.state == ST_GAME:
                self._update_game(dt, mouse_pos, mouse_click)
                self._draw_game()
            elif self.state == ST_WIN:
                self._update_win(dt, mouse_pos, mouse_click)
                self._draw_win()

            self.anim.draw_banner(self.screen, get_font(22, bold=True))
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    # ── MENU ──
    def _update_menu(self, dt, mouse_pos, mouse_click):
        if self.bots_btn.update(dt, mouse_pos, mouse_click):
            self.state = ST_SELECT
            self.selected_color = None
        if self.friends_btn.update(dt, mouse_pos, mouse_click):
            self.state = ST_FRIENDS

    def _draw_menu(self):
        draw_menu_screen(self.screen, self.anim, self.bots_btn, self.friends_btn, self.time_elapsed)

    # ── BOT SELECT ──
    def _update_select(self, dt, mouse_pos, mouse_click):
        if self.back_btn.update(dt, mouse_pos, mouse_click):
            self.state = ST_MENU
            return
        for i, btn in enumerate(self.num_btns):
            val = [2,3,4][i]
            btn.color = (42,157,143) if self.num_players == val else (60,100,150)
            if btn.update(dt, mouse_pos, mouse_click):
                self.num_players = val
                if self.selected_color and self.selected_color not in COLOR_ORDER[:val]:
                    self.selected_color = None
        for card in self.color_cards:
            if card.color_name in COLOR_ORDER[:self.num_players]:
                if card.update(mouse_pos, mouse_click):
                    self.selected_color = card.color_name
                    for c2 in self.color_cards:
                        c2.selected = (c2.color_name == self.selected_color)
        if self.selected_color and self.start_btn.update(dt, mouse_pos, mouse_click):
            self._setup_bot_game()
            self.state = ST_GAME

    def _draw_select(self):
        draw_player_select(self.screen, self.anim, self.num_players,
                           self.color_cards, self.start_btn, self.num_btns,
                           self.selected_color, self.time_elapsed)
        self.back_btn.draw(self.screen)

    # ── FRIENDS SELECT ──
    def _update_friends(self, dt, mouse_pos, mouse_click, events):
        if self.back_btn.update(dt, mouse_pos, mouse_click):
            self.state = ST_MENU
            return
        for i, btn in enumerate(self.friends_num_btns):
            val = [2,3,4][i]
            btn.color = (42,157,143) if self.friends_num_players == val else (60,100,150)
            if btn.update(dt, mouse_pos, mouse_click):
                self.friends_num_players = val

        for i in range(self.friends_num_players):
            if i < len(self.name_inputs):
                self.name_inputs[i].update(dt, mouse_pos, mouse_click)

        # Handle keyboard events for text inputs
        for event in events:
            for i in range(self.friends_num_players):
                if i < len(self.name_inputs):
                    tab = self.name_inputs[i].handle_event(event)
                    if tab:
                        self.name_inputs[i].focused = False
                        nxt = (i + 1) % self.friends_num_players
                        self.name_inputs[nxt].focused = True
                        break

        if self.friends_start_btn.update(dt, mouse_pos, mouse_click):
            self._setup_friends_game()
            self.state = ST_GAME

    def _draw_friends(self):
        draw_friends_select(self.screen, self.anim, self.friends_num_players,
                            self.name_inputs[:self.friends_num_players],
                            self.friends_start_btn, self.friends_num_btns, self.time_elapsed)
        self.back_btn.draw(self.screen)

    # ── GAME ──
    def _current_player(self):
        return self.players[self.current_idx]

    def _update_game(self, dt, mouse_pos, mouse_click):
        player = self._current_player()

        if self.phase == PHASE_TURN_DELAY:
            self.turn_delay_timer -= dt
            if self.turn_delay_timer <= 0:
                self.phase = PHASE_ROLL
                self.can_roll = True
            return

        if self.phase == PHASE_ROLL:
            self.can_roll = True
            if player.is_bot:
                self._do_roll()
            else:
                self.roll_btn.update(dt, mouse_pos, False)
                if self.roll_btn.update(dt, mouse_pos, mouse_click):
                    self._do_roll()

        elif self.phase == PHASE_BOT_THINK:
            if player.is_bot and isinstance(player, Bot):
                if player.update_thinking(dt):
                    ti = player.get_pending_move()
                    if ti is not None:
                        self._execute_move(player, ti)
                    else:
                        self._add_history(player, f"No valid move (rolled {self.dice_value})")
                        self.phase = PHASE_NEXT_TURN

        elif self.phase == PHASE_CHOOSE:
            if mouse_click:
                ti = self._pick_token_at(mouse_pos, player)
                if ti is not None and ti in player.get_valid_moves(self.dice_value):
                    self._execute_move(player, ti)

        elif self.phase == PHASE_ANIMATE:
            if not self.anim.any_token_animating():
                self._post_move()

        elif self.phase == PHASE_NEXT_TURN:
            self._advance_turn()

    def _do_roll(self):
        self.dice_value = random.randint(1, 6)
        self.anim.dice.start_roll(self.dice_value)
        self.can_roll = False
        self.phase = PHASE_ANIMATE
        self._pending_after_dice = True

    def _post_dice_roll(self):
        player = self._current_player()
        if self.dice_value == 6:
            player.consecutive_sixes += 1
            if player.consecutive_sixes >= 3:
                if player.last_moved_token is not None:
                    for t in player.tokens:
                        if t.index == player.last_moved_token and t.state == STATE_ACTIVE:
                            self._add_history(player, "3 sixes! Token sent back")
                            t.send_to_base()
                            break
                else:
                    self._add_history(player, "3 sixes! Turn lost")
                player.consecutive_sixes = 0
                self.phase = PHASE_NEXT_TURN
                return
        else:
            player.consecutive_sixes = 0

        valid = player.get_valid_moves(self.dice_value)
        if not valid:
            self._add_history(player, f"Rolled {self.dice_value} — no moves")
            self.phase = PHASE_NEXT_TURN
            return

        if player.is_bot and isinstance(player, Bot):
            player.start_thinking(self.dice_value, self.players)
            self.phase = PHASE_BOT_THINK
        else:
            if len(valid) == 1:
                self._execute_move(player, valid[0])
            else:
                self.phase = PHASE_CHOOSE

    def _execute_move(self, player, token_idx):
        token = player.tokens[token_idx]
        if token.state == STATE_BASE and self.dice_value == 6:
            start_pos = token.get_base_position()
            token.enter_board()
            end_pos = self.board.get_pixel_pos(token.color, token.steps)
            self.anim.start_token_move(token.token_id, start_pos, end_pos, 0.35)
            player.last_moved_token = token_idx
            self._add_history(player, f"Unlocked token {token_idx+1}")
            self.phase = PHASE_ANIMATE
            self._pending_after_dice = False
            self._pending_capture_check = True
            self._moved_token = token
        elif token.state == STATE_ACTIVE:
            start_pos = self.board.get_pixel_pos(token.color, token.steps)
            token.move(self.dice_value)
            end_pos = self.board.get_pixel_pos(token.color, token.steps)
            self.anim.start_token_move(token.token_id, start_pos, end_pos, 0.15*self.dice_value)
            player.last_moved_token = token_idx
            if token.state == STATE_HOME:
                self._add_history(player, f"Token {token_idx+1} reached HOME! 🏠")
                self.anim.particles.emit_golden_glow(end_pos[0], end_pos[1])
            else:
                self._add_history(player, f"Moved token {token_idx+1} ({self.dice_value} steps)")
            self.phase = PHASE_ANIMATE
            self._pending_after_dice = False
            self._pending_capture_check = True
            self._moved_token = token
        else:
            self.phase = PHASE_NEXT_TURN

    def _post_move(self):
        if self._pending_after_dice:
            if self.anim.dice.finished or not self.anim.dice.rolling:
                self._pending_after_dice = False
                self._post_dice_roll()
            return
        if self._pending_capture_check:
            self._pending_capture_check = False
            token = self._moved_token
            if token.state == STATE_ACTIVE:
                self._check_capture(token)
            player = self._current_player()
            if player.has_won:
                self.winner = player
                self.state = ST_WIN
                self.confetti_timer = 0.0
                return
            if self.dice_value == 6:
                self.phase = PHASE_ROLL
                self.can_roll = True
            else:
                self.phase = PHASE_NEXT_TURN
            return
        self.phase = PHASE_NEXT_TURN

    def _check_capture(self, moved_token):
        if moved_token.steps >= 52:
            return
        gi = moved_token.get_global_path_index()
        if gi is None or gi in SAFE_INDICES:
            return
        for player in self.players:
            if player.color == moved_token.color:
                continue
            for t in player.tokens:
                if t.state == STATE_ACTIVE and t.steps < 52:
                    if t.get_global_path_index() == gi:
                        opp_stack = sum(1 for t2 in player.tokens
                                        if t2.state == STATE_ACTIVE and t2.steps < 52
                                        and t2.get_global_path_index() == gi)
                        if opp_stack >= 2:
                            continue
                        pos = self.board.get_pixel_pos(t.color, t.steps)
                        base_pos = t.get_base_position()
                        self.anim.particles.emit_burst(pos[0], pos[1], COLORS[t.color])
                        self.anim.start_token_move(t.token_id, pos, base_pos, 0.4)
                        t.send_to_base()
                        self._add_history(self._current_player(),
                                          f"Captured {player.color.capitalize()}'s token!")

    def _advance_turn(self):
        self.current_idx = (self.current_idx + 1) % len(self.players)
        player = self._current_player()
        player.consecutive_sixes = 0
        player.last_moved_token = None
        c = COLORS[player.color]
        if self.friends_mode:
            self.anim.banner.show(f"🎲 {player.name.upper()}'s TURN!", c)
            self.anim.banner.duration = 2.5
            self.phase = PHASE_TURN_DELAY
            self.turn_delay_timer = 2.0
            self.can_roll = False
        else:
            self.anim.banner.show(f"{player.name}'s Turn ({player.color.capitalize()})", c)
            self.phase = PHASE_ROLL
            self.can_roll = True

    def _pick_token_at(self, mouse_pos, player):
        mx, my = mouse_pos
        for i, token in enumerate(player.tokens):
            if token.state == STATE_BASE:
                tx, ty = token.get_base_position()
            elif token.state == STATE_ACTIVE:
                pos = self.board.get_pixel_pos(token.color, token.steps)
                if pos is None: continue
                tx, ty = pos
            else:
                continue
            if math.sqrt((mx-tx)**2 + (my-ty)**2) <= 22:
                return i
        return None

    def _add_history(self, player, text):
        self.turn_history.append({"color": player.color, "text": text})
        if len(self.turn_history) > 20:
            self.turn_history = self.turn_history[-20:]

    def _draw_game(self):
        self.screen.fill((13, 27, 42))
        self.board.draw(self.screen)
        self._draw_all_tokens()
        show_roll = self.can_roll and self.phase == PHASE_ROLL
        draw_hud(self.screen, self.players, self.current_idx, self.anim.dice,
                 self.turn_history, self.roll_btn, show_roll, self.time_elapsed)

        if self.phase == PHASE_CHOOSE:
            player = self._current_player()
            for ti in player.get_valid_moves(self.dice_value):
                token = player.tokens[ti]
                if token.state == STATE_BASE:
                    tx, ty = token.get_base_position()
                elif token.state == STATE_ACTIVE:
                    pos = self.board.get_pixel_pos(token.color, token.steps)
                    if pos is None: continue
                    tx, ty = pos
                else: continue
                pulse = 0.5 + 0.5 * math.sin(self.time_elapsed * 6)
                r = int(22 + 4 * pulse)
                hs = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
                c = COLORS[player.color]
                pygame.draw.circle(hs, (*c, int(80*pulse)), (r+2, r+2), r, width=3)
                self.screen.blit(hs, (tx-r-2, ty-r-2))
                hf = get_font(11)
                h = hf.render("▲", True, (*c, 200))
                self.screen.blit(h, (tx - h.get_width()//2, ty + 20))

        if self.phase == PHASE_BOT_THINK:
            draw_thinking_indicator(self.screen, 375, 360, self.time_elapsed)

        if self.phase == PHASE_TURN_DELAY and self.friends_mode:
            p = self._current_player()
            f = get_font(24, bold=True)
            txt = f.render(f"Pass device to {p.name}!", True, COLORS[p.color])
            bx = 375 - txt.get_width()//2
            by = 690
            bs = pygame.Surface((txt.get_width()+20, txt.get_height()+10), pygame.SRCALPHA)
            pulse = 0.5 + 0.5 * math.sin(self.time_elapsed * 4)
            pygame.draw.rect(bs, (20,30,50, int(200*pulse)), (0,0,bs.get_width(),bs.get_height()), border_radius=8)
            bs.blit(txt, (10, 5))
            self.screen.blit(bs, (bx-10, by-5))

        self.anim.draw_particles(self.screen)

    def _draw_all_tokens(self):
        cell_tokens = {}
        for player in self.players:
            for token in player.tokens:
                if token.state == STATE_HOME: continue
                anim_pos = self.anim.get_token_anim_pos(token.token_id)
                if anim_pos:
                    tx, ty = int(anim_pos[0]), int(anim_pos[1])
                    bob = 0
                elif token.state == STATE_BASE:
                    tx, ty = token.get_base_position()
                    bob = math.sin(self.time_elapsed*2 + token.index) * 3
                elif token.state == STATE_ACTIVE:
                    pos = self.board.get_pixel_pos(token.color, token.steps)
                    if pos is None: continue
                    tx, ty = pos
                    bob = math.sin(self.time_elapsed*2 + token.index*0.7) * 2.5
                else: continue
                key = (tx//5, ty//5)
                if key not in cell_tokens: cell_tokens[key] = []
                cell_tokens[key].append((tx, ty, token.color, bob, token.token_id))
        for key, tokens in cell_tokens.items():
            color_groups = {}
            for tx, ty, color, bob, tid in tokens:
                if color not in color_groups: color_groups[color] = []
                color_groups[color].append((tx, ty, bob, tid))
            for color, group in color_groups.items():
                tx, ty, bob, tid = group[0]
                draw_token(self.screen, tx, ty, color, bob, len(group))

    # ── WIN SCREEN ──
    def _update_win(self, dt, mouse_pos, mouse_click):
        self.confetti_timer += dt
        if self.confetti_timer > 0.5:
            self.anim.particles.emit_confetti(WIDTH, HEIGHT, 15)
            self.confetti_timer = 0.0
        if self.play_again_btn.update(dt, mouse_pos, mouse_click):
            self.anim.particles.particles.clear()
            if self.friends_mode:
                self.state = ST_FRIENDS
            else:
                self.state = ST_SELECT
                self.selected_color = None
                for card in self.color_cards:
                    card.selected = False
        if self.menu_btn.update(dt, mouse_pos, mouse_click):
            self.anim.particles.particles.clear()
            if self.friends_mode:
                for inp in self.name_inputs:
                    inp.text = ""
            self.state = ST_MENU

    def _draw_win(self):
        self.screen.fill((13, 27, 42))
        self.board.draw(self.screen)
        self._draw_all_tokens()
        draw_win_screen(self.screen, self.winner, self.play_again_btn,
                        self.menu_btn, self.time_elapsed, self.anim.particles)

if __name__ == "__main__":
    Game().run()
