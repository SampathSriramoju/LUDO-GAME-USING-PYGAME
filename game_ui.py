"""
ui.py - UI components for Ludo game.
Menu, player selection, HUD panel, win screen, buttons, font helpers.
"""

import pygame
import math
from board import COLORS, COLOR_LIGHT, COLOR_DARK, BG_COLOR, COLOR_ORDER


def get_font(size, bold=False):
    """Safe font loader with fallback chain."""
    try:
        f = pygame.font.SysFont("Arial", size, bold=bold)
        if f is not None:
            return f
    except Exception:
        pass
    return pygame.font.Font(None, size)


class Button:
    """Clickable button with hover glow and press animation."""

    def __init__(self, x, y, w, h, text, color=(80, 130, 180), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hovered = False
        self.pressed = False
        self.press_time = 0.0

    def update(self, dt, mouse_pos, mouse_click):
        """Update hover/press state. Returns True if clicked."""
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.press_time > 0:
            self.press_time = max(0, self.press_time - dt)
        if self.hovered and mouse_click:
            self.press_time = 0.15
            self.pressed = True
            return True
        self.pressed = False
        return False

    def draw(self, surface):
        r = self.rect
        # Hover glow
        if self.hovered:
            gs = pygame.Surface((r.w + 12, r.h + 12), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*self.color, 60), (0, 0, r.w + 12, r.h + 12), border_radius=14)
            surface.blit(gs, (r.x - 6, r.y - 6))

        # Press shrink
        shrink = int(3 * (self.press_time / 0.15)) if self.press_time > 0 else 0
        dr = r.inflate(-shrink * 2, -shrink * 2)

        # Shadow
        sr = dr.move(3, 3)
        ss = pygame.Surface((sr.w, sr.h), pygame.SRCALPHA)
        pygame.draw.rect(ss, (0, 0, 0, 50), (0, 0, sr.w, sr.h), border_radius=10)
        surface.blit(ss, sr.topleft)

        # Body (glassmorphism)
        bs = pygame.Surface((dr.w, dr.h), pygame.SRCALPHA)
        bc = (*self.color, 180) if not self.hovered else (*self.color, 220)
        pygame.draw.rect(bs, bc, (0, 0, dr.w, dr.h), border_radius=10)
        # Top highlight
        pygame.draw.line(bs, (*[min(255, c + 60) for c in self.color], 80),
                         (8, 1), (dr.w - 8, 1), 1)
        surface.blit(bs, dr.topleft)

        # Border
        pygame.draw.rect(surface, (*[min(255, c + 30) for c in self.color], 120),
                         dr, width=1, border_radius=10)

        # Text
        font = get_font(max(16, dr.h // 2 - 2), bold=True)
        txt = font.render(self.text, True, self.text_color)
        surface.blit(txt, (dr.centerx - txt.get_width() // 2,
                           dr.centery - txt.get_height() // 2))


class ColorCard:
    """Selectable color card for player selection screen."""

    def __init__(self, x, y, w, h, color_name, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_name = color_name
        self.label = label
        self.selected = False
        self.hovered = False

    def update(self, mouse_pos, mouse_click):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.hovered and mouse_click:
            return True
        return False

    def draw(self, surface, disabled=False):
        c = COLORS[self.color_name]
        r = self.rect

        if disabled:
            # Greyed out
            gs = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(gs, (60, 60, 70, 150), (0, 0, r.w, r.h), border_radius=12)
            surface.blit(gs, r.topleft)
            font = get_font(16)
            txt = font.render(self.label, True, (100, 100, 110))
            surface.blit(txt, (r.centerx - txt.get_width() // 2,
                               r.centery - txt.get_height() // 2))
            return

        # Background
        alpha = 200 if self.selected else (160 if self.hovered else 120)
        gs = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(gs, (*c[:3], alpha), (0, 0, r.w, r.h), border_radius=12)
        surface.blit(gs, r.topleft)

        # Selected border
        if self.selected:
            pygame.draw.rect(surface, (255, 255, 255), r, width=3, border_radius=12)
        elif self.hovered:
            pygame.draw.rect(surface, (*COLOR_LIGHT[self.color_name], 150), r, width=2, border_radius=12)

        # Label
        font = get_font(18, bold=True)
        txt = font.render(self.label, True, (255, 255, 255))
        surface.blit(txt, (r.centerx - txt.get_width() // 2,
                           r.centery - txt.get_height() // 2))


class TextInput:
    """Clickable text input box for name entry. Max 12 chars."""

    def __init__(self, x, y, w, h, default="", placeholder=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = default
        self.placeholder = placeholder
        self.focused = False
        self.max_chars = 12
        self.cursor_blink = 0.0

    def handle_event(self, event):
        """Handle keyboard input when focused. Returns True if TAB pressed."""
        if not self.focused:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return True
            elif event.unicode and len(self.text) < self.max_chars:
                ch = event.unicode
                if ch.isprintable() and ch != '\t':
                    self.text += ch
        return False

    def update(self, dt, mouse_pos, mouse_click):
        """Update focus state on click."""
        self.cursor_blink += dt
        if mouse_click:
            self.focused = self.rect.collidepoint(mouse_pos)
            if self.focused:
                self.cursor_blink = 0.0

    def draw(self, surface, accent_color=(80, 130, 180)):
        r = self.rect
        bg = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (20, 32, 50, 200), (0, 0, r.w, r.h), border_radius=8)
        surface.blit(bg, r.topleft)

        if self.focused:
            pulse = 0.6 + 0.4 * math.sin(self.cursor_blink * 4)
            bc = (*accent_color, int(200 * pulse))
            bs = pygame.Surface((r.w + 4, r.h + 4), pygame.SRCALPHA)
            pygame.draw.rect(bs, bc, (0, 0, r.w + 4, r.h + 4), width=2, border_radius=9)
            surface.blit(bs, (r.x - 2, r.y - 2))
        else:
            pygame.draw.rect(surface, (50, 70, 95), r, width=1, border_radius=8)

        font = get_font(18)
        if self.text:
            txt = font.render(self.text, True, (230, 235, 245))
        else:
            txt = font.render(self.placeholder, True, (90, 105, 120))
        surface.blit(txt, (r.x + 10, r.y + r.h // 2 - txt.get_height() // 2))

        if self.focused and int(self.cursor_blink * 2) % 2 == 0:
            cx = r.x + 12 + font.size(self.text)[0]
            pygame.draw.line(surface, (200, 210, 230),
                             (cx, r.y + 6), (cx, r.y + r.h - 6), 2)


def draw_menu_screen(surface, anim_manager, bots_btn, friends_btn, time_elapsed):
    """Draw the main menu screen with animated neon title and two mode buttons."""
    surface.fill(BG_COLOR)
    anim_manager.draw_menu_bg(surface)

    # Neon glow "LUDO" title
    title_font = get_font(110, bold=True)
    title_text = "L U D O"

    # Glow layers
    glow_colors = [
        ((255, 100, 120), 8), ((100, 200, 255), 5), ((255, 220, 100), 3),
    ]
    cx = surface.get_width() // 2
    cy = 160
    pulse = 0.7 + 0.3 * math.sin(time_elapsed * 2.5)

    for gc, offset in glow_colors:
        gs = pygame.Surface((700, 150), pygame.SRCALPHA)
        gtxt = title_font.render(title_text, True, (*gc, int(50 * pulse)))
        gs.blit(gtxt, (350 - gtxt.get_width() // 2 + offset,
                        75 - gtxt.get_height() // 2 + offset))
        gs.blit(gtxt, (350 - gtxt.get_width() // 2 - offset,
                        75 - gtxt.get_height() // 2 - offset))
        surface.blit(gs, (cx - 350, cy - 75))

    # Main title
    txt = title_font.render(title_text, True, (255, 255, 255))
    surface.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

    # Subtitle
    sub_font = get_font(22)
    sub = sub_font.render("The Classic Board Game", True, (168, 218, 220))
    surface.blit(sub, (cx - sub.get_width() // 2, cy + 65))

    # Draw both mode buttons
    bots_btn.draw(surface)
    friends_btn.draw(surface)


def draw_player_select(surface, anim_manager, num_players, color_cards,
                       start_btn, num_btns, selected_color, time_elapsed):
    """Draw the player selection screen."""
    surface.fill(BG_COLOR)
    anim_manager.draw_menu_bg(surface)
    cx = surface.get_width() // 2

    # Title
    font = get_font(48, bold=True)
    txt = font.render("SELECT PLAYERS", True, (255, 255, 255))
    surface.blit(txt, (cx - txt.get_width() // 2, 40))

    # Subtitle - number of players
    sfont = get_font(22)
    st = sfont.render("Number of Players:", True, (168, 218, 220))
    surface.blit(st, (cx - st.get_width() // 2 - 100, 120))

    # Number buttons
    for btn in num_btns:
        btn.draw(surface)

    # "Choose your color" label
    ct = sfont.render("Choose Your Color:", True, (168, 218, 220))
    surface.blit(ct, (cx - ct.get_width() // 2, 210))

    # Color cards
    active_colors = COLOR_ORDER[:num_players]
    for card in color_cards:
        disabled = card.color_name not in active_colors
        card.draw(surface, disabled=disabled)

    # Show player assignments
    if selected_color:
        ay = 380
        afont = get_font(20)
        for i, cname in enumerate(active_colors):
            label = "YOU" if cname == selected_color else "BOT 🤖"
            c = COLORS[cname]
            # Color swatch
            pygame.draw.circle(surface, c, (cx - 120, ay + i * 40 + 10), 10)
            atxt = afont.render(f"  {cname.capitalize()} — {label}", True, (200, 210, 220))
            surface.blit(atxt, (cx - 100, ay + i * 40))

    # Start button
    if selected_color:
        start_btn.draw(surface)


def draw_friends_select(surface, anim_manager, num_players, name_inputs,
                        start_btn, num_btns, time_elapsed):
    """Draw the Play With Friends setup screen with name entry cards."""
    surface.fill(BG_COLOR)
    anim_manager.draw_menu_bg(surface)
    cx = surface.get_width() // 2

    # Title
    font = get_font(44, bold=True)
    txt = font.render("PLAY WITH FRIENDS", True, (255, 255, 255))
    surface.blit(txt, (cx - txt.get_width() // 2, 30))

    # Subtitle
    sfont = get_font(20)
    st = sfont.render("Everyone takes turns on this device!", True, (168, 218, 220))
    surface.blit(st, (cx - st.get_width() // 2, 80))

    # Number of players label
    nf = get_font(20)
    nt = nf.render("How Many Players?", True, (168, 218, 220))
    surface.blit(nt, (cx - nt.get_width() // 2 - 80, 120))

    # Number buttons
    for btn in num_btns:
        btn.draw(surface)

    # Player cards
    active_colors = COLOR_ORDER[:num_players]
    card_w = 460
    card_h = 85
    card_x = cx - card_w // 2
    card_start_y = 180
    card_gap = 10

    color_emojis = {"red": "🔴", "green": "🟢", "yellow": "🟡", "blue": "🔵"}

    for i, cname in enumerate(active_colors):
        cy_card = card_start_y + i * (card_h + card_gap)
        c = COLORS[cname]

        # Card background (glassmorphism)
        cs = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(cs, (*c[:3], 35), (0, 0, card_w, card_h), border_radius=12)
        surface.blit(cs, (card_x, cy_card))
        pygame.draw.rect(surface, (*c[:3], 80), (card_x, cy_card, card_w, card_h),
                         width=1, border_radius=12)

        # Color swatch + label
        label_font = get_font(20, bold=True)
        emoji = color_emojis.get(cname, "●")
        player_label = f"{emoji}  Player {i + 1}"
        lt = label_font.render(player_label, True, (220, 230, 245))
        surface.blit(lt, (card_x + 18, cy_card + 10))

        # Color indicator (locked)
        color_font = get_font(14)
        ct = color_font.render(f"● {cname.capitalize()} (locked)", True, c)
        surface.blit(ct, (card_x + 18, cy_card + 38))

        # Name label
        name_font = get_font(15)
        name_label = name_font.render("Name:", True, (140, 155, 175))
        surface.blit(name_label, (card_x + 220, cy_card + 14))

        # Name input box
        if i < len(name_inputs):
            inp = name_inputs[i]
            inp.rect.x = card_x + 280
            inp.rect.y = cy_card + 8
            inp.rect.w = 160
            inp.rect.h = 34
            inp.draw(surface, accent_color=c)

    # Greyed-out cards for inactive slots
    for i in range(num_players, 4):
        cy_card = card_start_y + i * (card_h + card_gap)
        cs = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(cs, (40, 45, 55, 100), (0, 0, card_w, card_h), border_radius=12)
        surface.blit(cs, (card_x, cy_card))
        df = get_font(18)
        dt = df.render("—  Empty Slot  —", True, (70, 80, 90))
        surface.blit(dt, (card_x + card_w // 2 - dt.get_width() // 2,
                          cy_card + card_h // 2 - dt.get_height() // 2))

    # Start button
    start_btn.draw(surface)


def draw_hud(surface, players, current_idx, dice_roller, turn_history,
             roll_btn, can_roll, time_elapsed):
    """Draw the HUD panel on the right side (x=750, w=350, h=750)."""
    hud_x = 750
    hud_w = 350
    hud_h = 750

    # HUD background
    panel = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (15, 25, 40, 240), (0, 0, hud_w, hud_h))
    surface.blit(panel, (hud_x, 0))

    # Separator line
    pygame.draw.line(surface, (40, 60, 90), (hud_x, 0), (hud_x, hud_h), 2)

    # Title
    font_title = get_font(26, bold=True)
    title = font_title.render("LUDO", True, (200, 220, 240))
    surface.blit(title, (hud_x + hud_w // 2 - title.get_width() // 2, 15))

    # Player cards
    card_y = 55
    card_h = 65
    font_name = get_font(18, bold=True)
    font_info = get_font(14)

    for i, player in enumerate(players):
        is_active = (i == current_idx)
        cx_card = hud_x + 15
        cy_card = card_y + i * (card_h + 8)
        cw = hud_w - 30
        c = COLORS[player.color]

        # Card background
        cs = pygame.Surface((cw, card_h), pygame.SRCALPHA)
        bg_alpha = 160 if is_active else 80
        pygame.draw.rect(cs, (*c[:3], bg_alpha // 3), (0, 0, cw, card_h), border_radius=10)
        surface.blit(cs, (cx_card, cy_card))

        # Active border pulse
        if is_active:
            pulse = 0.5 + 0.5 * math.sin(time_elapsed * 4)
            border_alpha = int(150 + 105 * pulse)
            bs = pygame.Surface((cw + 4, card_h + 4), pygame.SRCALPHA)
            pygame.draw.rect(bs, (*c, border_alpha), (0, 0, cw + 4, card_h + 4),
                             width=2, border_radius=11)
            surface.blit(bs, (cx_card - 2, cy_card - 2))

        # Color swatch
        pygame.draw.circle(surface, c, (cx_card + 25, cy_card + card_h // 2), 12)
        pygame.draw.circle(surface, (255, 255, 255, 100),
                           (cx_card + 25, cy_card + card_h // 2), 12, width=1)

        # Name
        label = player.name
        ntxt = font_name.render(label, True, (240, 240, 250))
        surface.blit(ntxt, (cx_card + 48, cy_card + 10))

        # Tokens home count
        home_txt = font_info.render(f"Home: {player.tokens_home}/4  Active: {player.tokens_active}",
                                    True, (170, 185, 200))
        surface.blit(home_txt, (cx_card + 48, cy_card + 35))

        # Turn indicator
        if is_active:
            arrow = font_name.render("▶", True, c)
            surface.blit(arrow, (cx_card + cw - 30, cy_card + card_h // 2 - arrow.get_height() // 2))

    # Dice area
    dice_y = card_y + len(players) * (card_h + 8) + 20
    dice_cx = hud_x + hud_w // 2
    dice_roller.draw(surface, dice_cx, dice_y + 50, size=80)

    # Roll button
    roll_btn_y = dice_y + 110
    roll_btn.rect.x = hud_x + 50
    roll_btn.rect.y = roll_btn_y
    roll_btn.rect.w = hud_w - 100
    roll_btn.rect.h = 45
    if can_roll:
        roll_btn.draw(surface)
    else:
        # Greyed out button
        gs = pygame.Surface((roll_btn.rect.w, roll_btn.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(gs, (50, 60, 70, 120), (0, 0, roll_btn.rect.w, roll_btn.rect.h),
                         border_radius=10)
        surface.blit(gs, roll_btn.rect.topleft)
        gf = get_font(18, bold=True)
        gt = gf.render(roll_btn.text, True, (100, 110, 120))
        surface.blit(gt, (roll_btn.rect.centerx - gt.get_width() // 2,
                          roll_btn.rect.centery - gt.get_height() // 2))

    # Turn history
    hist_y = roll_btn_y + 65
    hf = get_font(14)
    ht = get_font(16, bold=True)
    htitle = ht.render("Turn History", True, (150, 170, 190))
    surface.blit(htitle, (hud_x + 20, hist_y))

    pygame.draw.line(surface, (40, 60, 85), (hud_x + 20, hist_y + 22),
                     (hud_x + hud_w - 20, hist_y + 22), 1)

    for j, entry in enumerate(turn_history[-5:]):
        ey = hist_y + 30 + j * 22
        c = COLORS.get(entry.get("color", "red"), (180, 180, 180))
        pygame.draw.circle(surface, c, (hud_x + 30, ey + 8), 5)
        et = hf.render(entry.get("text", ""), True, (160, 175, 190))
        surface.blit(et, (hud_x + 45, ey))


def draw_thinking_indicator(surface, x, y, time_elapsed):
    """Draw animated 'Thinking...' indicator with pulsing dots."""
    font = get_font(20, bold=True)
    base = "Thinking"
    dots_count = int(time_elapsed * 3) % 4
    text = base + "." * dots_count
    txt = font.render(text, True, (200, 200, 220))
    # Pulse alpha
    pulse = 0.5 + 0.5 * math.sin(time_elapsed * 5)
    ts = pygame.Surface((txt.get_width() + 20, txt.get_height() + 10), pygame.SRCALPHA)
    pygame.draw.rect(ts, (30, 40, 60, int(180 * pulse)), (0, 0, ts.get_width(), ts.get_height()),
                     border_radius=8)
    ts.blit(txt, (10, 5))
    surface.blit(ts, (x - ts.get_width() // 2, y))


def draw_win_screen(surface, winner, play_again_btn, menu_btn, time_elapsed, particles):
    """Draw the win/celebration screen."""
    # Dim background
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    cx = surface.get_width() // 2
    cy = surface.get_height() // 2

    # Draw confetti particles
    particles.draw(surface)

    c = COLORS[winner.color]

    # Trophy
    trophy_font = get_font(80)
    trophy = trophy_font.render("🏆", True, (255, 215, 0))
    surface.blit(trophy, (cx - trophy.get_width() // 2, cy - 160))

    # Winner banner
    banner_w = 500
    banner_h = 80
    bs = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
    pygame.draw.rect(bs, (*c, 200), (0, 0, banner_w, banner_h), border_radius=15)
    pygame.draw.rect(bs, (255, 255, 255, 100), (0, 0, banner_w, banner_h),
                     width=2, border_radius=15)
    surface.blit(bs, (cx - banner_w // 2, cy - 60))

    # Winner text
    wf = get_font(36, bold=True)
    wt = wf.render(f"{winner.name} WINS!", True, (255, 255, 255))
    surface.blit(wt, (cx - wt.get_width() // 2, cy - 45))

    # Color label
    sf = get_font(22)
    st = sf.render(f"{winner.color.capitalize()} Team", True, (220, 230, 240))
    surface.blit(st, (cx - st.get_width() // 2, cy + 5))

    # Golden glow pulse
    pulse = 0.5 + 0.5 * math.sin(time_elapsed * 3)
    glow_s = pygame.Surface((banner_w + 40, banner_h + 40), pygame.SRCALPHA)
    pygame.draw.rect(glow_s, (255, 215, 0, int(40 * pulse)),
                     (0, 0, banner_w + 40, banner_h + 40), border_radius=20)
    surface.blit(glow_s, (cx - banner_w // 2 - 20, cy - 80))

    # Buttons
    play_again_btn.draw(surface)
    menu_btn.draw(surface)
