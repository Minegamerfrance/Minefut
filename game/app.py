from __future__ import annotations

import sys
import time
import json
import unicodedata
from pathlib import Path
from typing import Optional, List, Tuple

import pygame
import random
import math

from . import settings as app_settings
from .packs import generate_pack, RARITY_COLORS
from .cards import Card
from . import db as game_db
from . import wallet
from . import xp
from . import sbc as sbc_mod
from . import defi as defi_mod
from . import season_pass as sp_mod
from . import daily_rewards as daily_mod


class Button:
    def __init__(self, rect: pygame.Rect, label: str):
        self.rect = rect
        self.label = label

    def draw(self, surf: pygame.Surface, font: pygame.font.Font, hovered: bool = False, pressed: bool = False):
        bg = (40, 40, 50) if not hovered else (55, 55, 70)
        border = (90, 90, 110)
        if pressed:
            bg = (30, 30, 40)
        pygame.draw.rect(surf, bg, self.rect, border_radius=10)
        pygame.draw.rect(surf, border, self.rect, 2, border_radius=10)
        txt = font.render(self.label, True, (230, 230, 235))
        surf.blit(txt, (self.rect.centerx - txt.get_width() // 2, self.rect.centery - txt.get_height() // 2))


class Screen:
    def __init__(self, app: 'App'):
        self.app = app
    def handle(self, event: pygame.event.Event):
        pass
    def update(self, dt: float):
        pass
    def draw(self, screen: pygame.Surface):
        pass


class MainMenu(Screen):
    def __init__(self, app: 'App'):
        super().__init__(app)
        w, h = app.size
        bx, bw, bh, gap = w // 2 - 140, 280, 56, 16
        self.buttons = [
            Button(pygame.Rect(bx, h // 2 - 2 * (bh + gap), bw, bh), 'Ouvrir des packs'),
            Button(pygame.Rect(bx, h // 2 - 1 * (bh + gap), bw, bh), 'Collection'),
            Button(pygame.Rect(bx, h // 2 + 0 * (bh + gap), bw, bh), 'SBC'),
            Button(pygame.Rect(bx, h // 2 + 1 * (bh + gap), bw, bh), 'Défis'),
            Button(pygame.Rect(bx, h // 2 + 2 * (bh + gap), bw, bh), 'Paramètres'),
            Button(pygame.Rect(bx, h // 2 + 3 * (bh + gap), bw, bh), 'Quitter'),
        ]

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # open Season Pass panel if clicked (top-left), same size as event banner
            sp_rect = self.app._get_season_pass_rect()
            if sp_rect and sp_rect.collidepoint((mx, my)):
                try:
                    self.app.push(SeasonPass(self.app))
                except Exception:
                    pass
                return
            # bottom-left Daily Rewards button
            try:
                daily_rect = self._daily_btn_rect()
                if daily_rect.collidepoint((mx, my)):
                    self.app.push(DailyRewards(self.app))
                    return
            except Exception:
                pass
            for i, b in enumerate(self.buttons):
                if b.rect.collidepoint((mx, my)):
                    if i == 0:
                        self.app.push(Packs(self.app))
                    elif i == 1:
                        self.app.push(Collection(self.app))
                    elif i == 2:
                        # gate SBC until unlocked via Pass level 3
                        try:
                            if sp_mod.is_feature_unlocked('sbc'):
                                self.app.push(SBC(self.app))
                            else:
                                self.app.show_toast('Atteins Niv 3 (Saison 1 : Lancement) pour débloquer SBC', 2.0)
                        except Exception:
                            pass
                    elif i == 3:
                        # gate Defi until unlocked via Pass level 1
                        try:
                            if sp_mod.is_feature_unlocked('defi'):
                                self.app.push(Defi(self.app))
                            else:
                                self.app.show_toast('Atteins Niv 1 (Saison 1 : Lancement) pour débloquer Défis', 2.0)
                        except Exception:
                            pass
                    elif i == 4:
                        self.app.push(Settings(self.app))
                    elif i == 5:
                        self.app.running = False

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((18, 20, 24))
        title = self.app.h1.render('Minefut', True, (235, 235, 245))
        subtitle = self.app.h3.render('Edition 2025 — Menu principal', True, (160, 160, 175))
        screen.blit(title, (w // 2 - title.get_width() // 2, 120))
        screen.blit(subtitle, (w // 2 - subtitle.get_width() // 2, 180))
        mx, my = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()[0]
        for idx, b in enumerate(self.buttons):
            hovered = b.rect.collidepoint((mx, my))
            b.draw(screen, self.app.h3, hovered=hovered, pressed=pressed and hovered)
            # overlay lock state for Défis (idx 3) and SBC (idx 2)
            try:
                if idx == 2 and not sp_mod.is_feature_unlocked('sbc'):
                    # draw lock badge
                    badge = pygame.Surface((b.rect.w, 20), pygame.SRCALPHA)
                    pygame.draw.rect(badge, (100, 40, 40, 220), badge.get_rect(), border_radius=6)
                    txt = self.app.h5.render('Verrouillé — Atteins Niv 3 (Saison 1 : Lancement)', True, (255, 255, 255))
                    badge.blit(txt, (badge.get_width()//2 - txt.get_width()//2, 2))
                    screen.blit(badge, (b.rect.x, b.rect.bottom + 6))
                    # dim button slightly
                    dim = pygame.Surface((b.rect.w, b.rect.h), pygame.SRCALPHA)
                    dim.fill((0, 0, 0, 60))
                    screen.blit(dim, b.rect.topleft)
                if idx == 3 and not sp_mod.is_feature_unlocked('defi'):
                    badge = pygame.Surface((b.rect.w, 20), pygame.SRCALPHA)
                    pygame.draw.rect(badge, (100, 40, 40, 220), badge.get_rect(), border_radius=6)
                    txt = self.app.h5.render('Verrouillé — Atteins Niv 1 (Saison 1 : Lancement)', True, (255, 255, 255))
                    badge.blit(txt, (badge.get_width()//2 - txt.get_width()//2, 2))
                    screen.blit(badge, (b.rect.x, b.rect.bottom + 6))
                    dim = pygame.Surface((b.rect.w, b.rect.h), pygame.SRCALPHA)
                    dim.fill((0, 0, 0, 60))
                    screen.blit(dim, b.rect.topleft)
            except Exception:
                pass
        # Minecoins + XP chips (top-right)
        y = self._draw_wallet_chip(screen)
        self._draw_xp_chip(screen, y + 8)
        # Season Pass panel (top-left), same size as Event banner
        sp = self.app._get_season_pass_rect()
        if sp is not None:
            # background panel
            pygame.draw.rect(screen, (20, 22, 28), pygame.Rect(sp.x - 8, sp.y - 8, sp.w + 16, sp.h + 16), border_radius=12)
            pygame.draw.rect(screen, (70, 72, 90), pygame.Rect(sp.x - 8, sp.y - 8, sp.w + 16, sp.h + 16), 2, border_radius=12)
            # label
            lbl = self.app.h4.render('Pass de saison', True, (235, 235, 245))
            screen.blit(lbl, (sp.x, sp.y - 24))
            # inner decorative panel
            inner = pygame.Rect(sp.x, sp.y, sp.w, sp.h)
            pygame.draw.rect(screen, (32, 36, 46), inner, border_radius=10)
            pygame.draw.rect(screen, (90, 94, 120), inner, 2, border_radius=10)
            # simple progress preview using XP (visual only)
            try:
                lvl, cur, need = xp.get_level_progress()
                bar = pygame.Rect(inner.x + 16, inner.bottom - 28, inner.w - 32, 8)
                pygame.draw.rect(screen, (46, 50, 66), bar, border_radius=6)
                ratio = 0.0 if need <= 0 else min(1.0, cur / max(1, need))
                fill = pygame.Rect(bar.x, bar.y, int(bar.w * ratio), bar.h)
                pygame.draw.rect(screen, (90, 200, 110), fill, border_radius=6)
                txt = self.app.h5.render(f"Niv {lvl}  ·  {cur}/{need} XP", True, (220, 220, 230))
                screen.blit(txt, (inner.centerx - txt.get_width() // 2, bar.y - 22))
            except Exception:
                pass
        # Bottom-left: Daily Rewards button
        try:
            daily_rect = self._daily_btn_rect()
            mx, my = pygame.mouse.get_pos()
            pressed = pygame.mouse.get_pressed()[0]
            btn = Button(daily_rect, 'Récompenses quotidiennes')
            hovered = daily_rect.collidepoint((mx, my))
            btn.draw(screen, self.app.h4, hovered=hovered, pressed=pressed and hovered)
            # small availability badge if claimable today
            import datetime
            st = daily_mod.get_status()
            today = datetime.date.today().isoformat()
            already = (st.get('last_claim_date') == today)
            if not already:
                dot = pygame.Surface((12, 12), pygame.SRCALPHA)
                pygame.draw.circle(dot, (90, 200, 110), (6, 6), 6)
                screen.blit(dot, (daily_rect.right + 8, daily_rect.centery - 6))
        except Exception:
            pass

    def _draw_wallet_chip(self, screen: pygame.Surface):
        w, _ = self.app.size
        bal = wallet.get_balance()
        txt = self.app.h4.render(f"{bal} Minecoins", True, (235, 235, 245))
        pad = 10
        box = pygame.Rect(0, 0, txt.get_width() + pad * 2, txt.get_height() + pad)
        box.topright = (w - 20, 20)
        pygame.draw.rect(screen, (28, 30, 38), box, border_radius=10)
        pygame.draw.rect(screen, (70, 72, 90), box, 2, border_radius=10)
        screen.blit(txt, (box.x + pad, box.y + (box.h - txt.get_height()) // 2))
        return box.bottom

    def _draw_xp_chip(self, screen: pygame.Surface, top: int):
        w, _ = self.app.size
        lvl, cur, need = xp.get_level_progress()
        txt = self.app.h4.render(f"XP {xp.get_xp()}  ·  Lv {lvl}", True, (235, 235, 245))
        pad = 10
        box = pygame.Rect(0, 0, txt.get_width() + pad * 2, txt.get_height() + pad)
        box.topright = (w - 20, top)
        pygame.draw.rect(screen, (28, 30, 38), box, border_radius=10)
        pygame.draw.rect(screen, (70, 72, 90), box, 2, border_radius=10)
        screen.blit(txt, (box.x + pad, box.y + (box.h - txt.get_height()) // 2))

    def _daily_btn_rect(self) -> pygame.Rect:
        # Bottom-left persistent button
        return pygame.Rect(20, self.app.size[1] - 60, 280, 40)


class Packs(Screen):
    PACKS = [
        ('Pack Classique', 5, 100),
        ('Pack Premium', 5, 300),
        ('Pack Icône', 3, 800),
    ]

    def __init__(self, app: 'App'):
        super().__init__(app)
        self.generated: Optional[List[Card]] = None
        self.revealed_index = -1
        self.last_reveal = 0.0
        self.selected_pack = 0
        # track which cards have been recorded into collection during reveal
        self._revealed_recorded: set[int] = set()
        self.message = ''

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # quick access SBC button (top-right)
            sbc_rect = pygame.Rect(self.app.size[0] - 140, 28, 100, 36)
            if sbc_rect.collidepoint((mx, my)):
                # gate SBC behind feature unlock
                try:
                    if sp_mod.is_feature_unlocked('sbc'):
                        self.app.push(SBC(self.app))
                except Exception:
                    pass
                return
            # click on pack to open
            self.open_selected_pack()

    def open_selected_pack(self):
        label, count, price = self.PACKS[self.selected_pack]
        # attempt to spend Minecoins
        if not wallet.spend_coins(price):
            self.message = "Pas assez de Minecoins"
            return
        # log defi event: coins spent
        try:
            defi_mod.add_progress('coins_spent', price)
        except Exception:
            pass
        self.generated = generate_pack(label, count)
        self.revealed_index = -1
        self.last_reveal = 0.0
        # reset reveal recorded set; collection will update on each reveal, Madfut-style
        self._revealed_recorded.clear()
        # award XP for opening a paid pack
        try:
            xp.add_xp(10)
        except Exception:
            pass
        # log defi event: pack opened
        try:
            defi_mod.add_progress('pack_opened', 1)
        except Exception:
            pass

    def update(self, dt: float):
        if self.generated:
            if time.time() - self.last_reveal > 0.45 and self.revealed_index < len(self.generated) - 1:
                self.revealed_index += 1
                self.last_reveal = time.time()
                # record collection increment for the newly revealed card
                if self.revealed_index not in self._revealed_recorded:
                    self._revealed_recorded.add(self.revealed_index)
                    try:
                        game_db.add_to_collection_by_names([self.generated[self.revealed_index].name])
                    except Exception:
                        pass

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((14, 16, 20))
        title = self.app.h2.render('Packs', True, (230, 230, 240))
        screen.blit(title, (40, 32))
        # Minecoins + XP chips
        y = self._draw_wallet_chip(screen)
        self._draw_xp_chip(screen, y + 8)
        # SBC quick button (top-right)
        sbc_rect = pygame.Rect(w - 140, 28, 100, 36)
        mx, my = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()[0]
        sbc_locked = False
        try:
            sbc_locked = not sp_mod.is_feature_unlocked('sbc')
        except Exception:
            pass
        sbc_label = 'SBC 🔒' if sbc_locked else 'SBC'
        Button(sbc_rect, sbc_label).draw(screen, self.app.h4, hovered=sbc_rect.collidepoint((mx, my)), pressed=pressed and sbc_rect.collidepoint((mx, my)))
        # pack tabs
        tab_w, tab_h = 180, 42
        tab_x = 40
        mx, my = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()[0]
        for i, (label, count, price) in enumerate(self.PACKS):
            r = pygame.Rect(tab_x + i * (tab_w + 12), 96, tab_w, tab_h)
            hovered = r.collidepoint((mx, my))
            sel = (i == self.selected_pack)
            bg = (38, 40, 50) if not sel else (58, 60, 90)
            if hovered:
                bg = (48, 50, 65) if not sel else (68, 70, 110)
            pygame.draw.rect(screen, bg, r, border_radius=10)
            pygame.draw.rect(screen, (90, 90, 110), r, 2, border_radius=10)
            txt = self.app.h4.render(f'{label}  x{count}  — {price}', True, (235, 235, 245))
            screen.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))
            if hovered and pressed:
                self.selected_pack = i
                self.generated = None
                self.revealed_index = -1

        # open button
        open_rect = pygame.Rect(40, 170, 260, 48)
        # display price on button
        _, _, price = self.PACKS[self.selected_pack]
        open_btn = Button(open_rect, f'Ouvrir le pack ({price})')
        open_btn.draw(screen, self.app.h3, hovered=open_rect.collidepoint((mx, my)), pressed=pressed and open_rect.collidepoint((mx, my)))
        if pressed and open_rect.collidepoint((mx, my)):
            self.open_selected_pack()

        # reveal area
        reveal_area = pygame.Rect(40, 240, w - 80, h - 300)
        pygame.draw.rect(screen, (25, 27, 33), reveal_area, border_radius=16)
        pygame.draw.rect(screen, (70, 72, 90), reveal_area, 2, border_radius=16)

        if self.generated:
            cols = min(5, max(1, len(self.generated)))
            gap = 18
            card_w = min(220, (reveal_area.w - (cols + 1) * gap) // cols)
            card_h = int(card_w * 1.35)
            for i, card in enumerate(self.generated[: self.revealed_index + 1]):
                row = i // cols
                col = i % cols
                x = reveal_area.x + gap + col * (card_w + gap)
                y = reveal_area.y + gap + row * (card_h + gap)
                self._draw_card(screen, pygame.Rect(x, y, card_w, card_h), card)

        # back hint
        hint = self.app.h4.render('[Esc] Retour', True, (150, 150, 160))
        screen.blit(hint, (w - hint.get_width() - 32, 32))
        if self.message:
            msg = self.app.h4.render(self.message, True, (220, 120, 120))
            screen.blit(msg, (40, 136))

    def _draw_wallet_chip(self, screen: pygame.Surface) -> int:
        # reuse the same chip rendering as MainMenu
        w, _ = self.app.size
        bal = wallet.get_balance()
        txt = self.app.h4.render(f"{bal} Minecoins", True, (235, 235, 245))
        pad = 10
        box = pygame.Rect(0, 0, txt.get_width() + pad * 2, txt.get_height() + pad)
        box.topright = (w - 20, 20)
        pygame.draw.rect(screen, (28, 30, 38), box, border_radius=10)
        pygame.draw.rect(screen, (70, 72, 90), box, 2, border_radius=10)
        screen.blit(txt, (box.x + pad, box.y + (box.h - txt.get_height()) // 2))
        return box.bottom

    def _draw_xp_chip(self, screen: pygame.Surface, top: int):
        w, _ = self.app.size
        lvl, cur, need = xp.get_level_progress()
        txt = self.app.h4.render(f"XP {xp.get_xp()}  ·  Lv {lvl}", True, (235, 235, 245))
        pad = 10
        box = pygame.Rect(0, 0, txt.get_width() + pad * 2, txt.get_height() + pad)
        box.topright = (w - 20, top)
        pygame.draw.rect(screen, (28, 30, 38), box, border_radius=10)
        pygame.draw.rect(screen, (70, 72, 90), box, 2, border_radius=10)
        screen.blit(txt, (box.x + pad, box.y + (box.h - txt.get_height()) // 2))

    def _draw_card(self, screen: pygame.Surface, rect: pygame.Rect, card: Card):
        color = RARITY_COLORS.get(card.rarity, (160, 160, 160))
        # raw PNG full-bleed with a thin rarity border
        bg = (24, 26, 32)
        pygame.draw.rect(screen, bg, rect, border_radius=14)
        # draw PNG centered, with small padding
        pad = 6
        inner = pygame.Rect(rect.x + pad, rect.y + pad, rect.w - 2 * pad, rect.h - 2 * pad)
        img_path = resolve_player_image_by_name_and_rarity(card.name, card.rarity)
        if img_path is not None:
            ok = draw_player_png_centered(screen, img_path, (inner.centerx, inner.centery), inner.w, inner.h)
            if not ok:
                pygame.draw.rect(screen, (45, 47, 58), inner, border_radius=12)
        else:
            pygame.draw.rect(screen, (45, 47, 58), inner, border_radius=12)
        # rarity outline
        pygame.draw.rect(screen, color, rect, 3, border_radius=14)


class Settings(Screen):
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.dragging_vol = False

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            vs = self._vol_slider_rect()
            if vs.collidepoint((mx, my)):
                self.dragging_vol = True
                self._update_volume(mx)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_vol = False
        if event.type == pygame.MOUSEMOTION and self.dragging_vol:
            self._update_volume(event.pos[0])

    def _vol_slider_rect(self) -> pygame.Rect:
        return pygame.Rect(320, 200, 400, 24)

    def _update_volume(self, mouse_x: int):
        vs = self._vol_slider_rect()
        rel = max(0, min(vs.w, mouse_x - vs.x))
        vol = int((rel / vs.w) * 100)
        self.app.settings['volume'] = vol
        app_settings.save_settings(self.app.settings)

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((16, 18, 22))
        title = self.app.h2.render('Paramètres', True, (230, 230, 240))
        screen.blit(title, (40, 32))

        # effects quality cycle
        q = self.app.settings.get('effects_quality', 'medium')
        lbl = 'Qualité effets: ' + ('Bas' if q == 'low' else 'Moyen' if q == 'medium' else 'Élevé')
        qrect = pygame.Rect(40, 100, 300, 42)
        btn = Button(qrect, lbl)
        mx, my = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()[0]
        btn.draw(screen, self.app.h4, hovered=qrect.collidepoint((mx, my)), pressed=pressed and qrect.collidepoint((mx, my)))
        if pressed and qrect.collidepoint((mx, my)):
            new_q = {'low': 'medium', 'medium': 'high', 'high': 'low'}[q]
            self.app.settings['effects_quality'] = new_q
            app_settings.save_settings(self.app.settings)

        # show fps toggle
        srect = pygame.Rect(40, 160, 220, 42)
        sbtn = Button(srect, f"Afficher FPS: {'Oui' if self.app.settings.get('show_fps') else 'Non'}")
        sbtn.draw(screen, self.app.h4, hovered=srect.collidepoint((mx, my)), pressed=pressed and srect.collidepoint((mx, my)))
        if pressed and srect.collidepoint((mx, my)):
            self.app.settings['show_fps'] = not self.app.settings.get('show_fps', False)
            app_settings.save_settings(self.app.settings)

        # volume slider
        vs = self._vol_slider_rect()
        pygame.draw.rect(screen, (42, 44, 54), vs, border_radius=8)
        vol = self.app.settings.get('volume', 80)
        filled = pygame.Rect(vs.x, vs.y, int(vs.w * (vol / 100.0)), vs.h)
        pygame.draw.rect(screen, (62, 140, 255), filled, border_radius=8)
        vtxt = self.app.h4.render(f'Volume: {vol}%', True, (210, 210, 220))
        screen.blit(vtxt, (vs.x, vs.y - 32))

        hint = self.app.h5.render('[Esc] Retour', True, (150, 150, 160))
        screen.blit(hint, (w - hint.get_width() - 32, 32))


class SeasonPass(Screen):
    """Simple Season Pass screen (placeholder): shows current XP/level and a few tiers."""
    def __init__(self, app: 'App'):
        super().__init__(app)
        # horizontal scroll like SBC/Défis
        self.tile_scroll_x = 0
        self._tiles = []  # list of (rect, level)
        # optional background image for the Season Pass screen
        try:
            # Use project-relative background for Android compatibility
            p = Path("Fond/Sbc/Ultimate Scream/Joueur/fond ultimate scream.png")
            self._pass_bg_path = (_ROOT / p) if (_ROOT / p).exists() else None
        except Exception:
            self._pass_bg_path = None
        # pass selector tabs cache (id, name)
        try:
            # (id, name, unlocked)
            self.pass_tabs = sp_mod.list_all_passes()
        except Exception:
            self.pass_tabs = [('halloween', 'Saison 2 : Ultimate Scream', False)]

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
        elif event.type == pygame.MOUSEWHEEL:
            # horizontal scroll via mouse wheel
            self.tile_scroll_x = max(0, self.tile_scroll_x - event.y * 60)
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            # scroll by one tile step (based on 3 columns layout)
            w, h = self.app.size
            area = pygame.Rect(40, 150, w - 80, h - 220)
            gap = 20
            cols = 3
            tile_h = max(220, area.h - 24)
            tile_w = max(180, (area.w - (cols - 1) * gap - 8) // cols)
            step = tile_w + gap
            dx = -step if event.key == pygame.K_LEFT else step
            self.tile_scroll_x = max(0, self.tile_scroll_x + dx)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # pass selector tabs click
            try:
                tabs = sp_mod.list_all_passes()
            except Exception:
                tabs = [('halloween', 'Saison 2 : Ultimate Scream', False)]
            tx, ty = 40, 60
            # dynamic tab widths based on label size to avoid clipping
            spacing = 12
            x = tx
            for i, (pid, pname, unlocked) in enumerate(tabs):
                label_txt = pname + ('  🔒' if not unlocked else '')
                try:
                    lbl = self.app.h4.render(label_txt, True, (0, 0, 0))
                    tab_w = max(140, lbl.get_width() + 28)
                except Exception:
                    tab_w = 200
                r = pygame.Rect(x, ty, tab_w, 36)
                if r.collidepoint((mx, my)):
                    try:
                        if unlocked and sp_mod.set_active_pass(pid):
                            self.tile_scroll_x = 0
                    except Exception:
                        pass
                    return
                x += tab_w + spacing
            # check claim buttons by recomputing positions
            lvl, cur, need = xp.get_level_progress()
            current_level = lvl
            # Recompute current tile layout
            w, h = self.app.size
            area = pygame.Rect(40, 150, w - 80, h - 220)
            gap = 20
            cols = 3
            tile_h = max(220, area.h - 24)
            tile_w = max(180, (area.w - (cols - 1) * gap - 8) // cols)
            rewards = sp_mod.list_rewards()
            # Overflow arrows clickable like SBC/Collection
            content_w = max(0, len(rewards) * (tile_w + gap) - gap)
            overflow = content_w > area.w
            if overflow:
                left_arrow = pygame.Rect(area.x + 6, area.centery - 24, 32, 48)
                right_arrow = pygame.Rect(area.right - 38, area.centery - 24, 32, 48)
                if left_arrow.collidepoint((mx, my)):
                    self.tile_scroll_x = max(0, self.tile_scroll_x - (tile_w + gap))
                    return
                if right_arrow.collidepoint((mx, my)):
                    self.tile_scroll_x = max(0, self.tile_scroll_x + (tile_w + gap))
                    return
            # single row scroller (3 tiles per view)
            start_x = area.x + 4 - self.tile_scroll_x
            y = area.y + 12
            for i, rw in enumerate(rewards):
                r = pygame.Rect(start_x + i * (tile_w + gap), y, tile_w, tile_h)
                if not area.collidepoint((mx, my)) or not r.collidepoint((mx, my)):
                    continue
                claim = pygame.Rect(r.centerx - 60, r.bottom - 44, 120, 32)
                if claim.collidepoint((mx, my)):
                    if sp_mod.can_claim(rw.level, current_level):
                        sp_mod.claim(rw.level)
                    break

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((16, 18, 22))
        # background cover image (per-pass)
        try:
            active_pid = sp_mod.get_active_pass_id()
        except Exception:
            active_pid = 'launch'
        try:
            if active_pid == 'halloween':
                bg_rel = Path("Fond/Sbc/Ultimate Scream/Joueur/fond ultimate scream.png")
            else:
                # default background for launch or others
                bg_rel = Path("Fond/fond de football pass saison.png")
            bg_path = _ROOT / bg_rel
            if bg_path.exists():
                draw_bg_cover(screen, bg_path, pygame.Rect(0, 0, w, h))
                dim = pygame.Surface((w, h), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 120))
                screen.blit(dim, (0, 0))
        except Exception:
            pass
        try:
            pass_name = sp_mod.get_active_pass_name()
        except Exception:
            pass_name = 'Saison 2 : Ultimate Scream'
        # title removed (avoid white text behind season tabs)
        # pass selector tabs
        try:
            tabs = sp_mod.list_all_passes()
        except Exception:
            tabs = [('halloween', 'Saison 2 : Ultimate Scream', False)]
        active_id = None
        try:
            active_id = sp_mod.get_active_pass_id()
        except Exception:
            active_id = 'halloween'
        tx, ty = 40, 60
        mx, my = pygame.mouse.get_pos()
        # Tabs backdrop to improve readability over bright backgrounds
        rects = []
        try:
            spacing = 12
            # compute dynamic widths from labels
            x = tx
            total_w = 0
            for (pid, pname, unlocked) in tabs:
                label_txt = pname + ('  🔒' if not unlocked else '')
                try:
                    lbl = self.app.h4.render(label_txt, True, (0, 0, 0))
                    tab_w = max(140, lbl.get_width() + 28)
                except Exception:
                    tab_w = 200
                rects.append((pid, pygame.Rect(x, ty, tab_w, 36), pname, unlocked))
                x += tab_w + spacing
                total_w += (tab_w + spacing)
            if rects:
                total_w = total_w - spacing  # remove last spacing
            back = pygame.Rect(tx - 12, ty - 8, max(0, total_w) + 24, 52)
            back_surf = pygame.Surface((back.w, back.h), pygame.SRCALPHA)
            back_surf.fill((10, 12, 16, 200))
            pygame.draw.rect(back_surf, (90, 94, 120, 220), back_surf.get_rect(), 2, border_radius=12)
            screen.blit(back_surf, back.topleft)
        except Exception:
            # fallback to fixed layout if something goes wrong
            rects = [(pid, pygame.Rect(tx + i * (240 + 12), ty, 240, 36), pname, unlocked) for i, (pid, pname, unlocked) in enumerate(tabs)]
        for (pid, r, pname, unlocked) in rects:
            sel = (pid == active_id)
            hovered = r.collidepoint((mx, my))
            # locked style: darker, no hover brighten
            if not unlocked:
                bg = (32, 34, 44)
            else:
                bg = (38, 40, 50) if not sel else (58, 60, 90)
            if hovered:
                if unlocked:
                    bg = (48, 50, 65) if not sel else (68, 70, 110)
            pygame.draw.rect(screen, bg, r, border_radius=10)
            pygame.draw.rect(screen, (90, 90, 110), r, 2, border_radius=10)
            label_txt = pname + ('  🔒' if not unlocked else '')
            # keep legible but compact font
            lbl = self.app.h4.render(label_txt, True, (235, 235, 245))
            screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))
        # If hovering a locked tab, show small hint under tabs
        try:
            for (pid, r, pname, unlocked) in rects:
                if not unlocked and r.collidepoint((mx, my)):
                    hint = sp_mod.get_unlock_hint(pid)
                    ht = self.app.h5.render(hint, True, (180, 180, 190))
                    screen.blit(ht, (tx, ty + 32))
                    break
        except Exception:
            pass
        # XP chip
        lvl, cur, need = xp.get_level_progress()
        # XP chip — slightly larger to stand out
        chip = pygame.Rect(40, 92, 380, 56)
        pygame.draw.rect(screen, (28, 30, 38), chip, border_radius=12)
        pygame.draw.rect(screen, (70, 72, 90), chip, 3, border_radius=12)
        txt = self.app.h4.render(f"Niveau {lvl}  ·  {cur}/{need} XP", True, (235, 235, 245))
        screen.blit(txt, (chip.centerx - txt.get_width() // 2, chip.centery - txt.get_height() // 2))
        # area for tiles and scrolled content (slightly taller for top progress bar clearance)
        area = pygame.Rect(40, 162, w - 80, h - 216)
        pygame.draw.rect(screen, (20, 22, 28), area, border_radius=12)
        pygame.draw.rect(screen, (60, 62, 78), area, 2, border_radius=12)
        # Season Pass tiles area — show 3 tiles per view, scroll with wheel/arrow keys
        pygame.draw.rect(screen, (18, 20, 26), area, border_radius=12)
        pygame.draw.rect(screen, (60, 62, 78), area, 2, border_radius=12)
        rewards = sp_mod.list_rewards()
        gap = 20
        cols = 3
        pad_top = 28  # extra top padding to avoid overlap with the progress bar
        tile_h = max(220, area.h - 24 - pad_top)
        tile_w = max(180, (area.w - (cols - 1) * gap - 8) // cols)
        start_x = area.x + 4 - self.tile_scroll_x
        y = area.y + pad_top
        # overflow arrows
        content_w = max(0, len(rewards) * (tile_w + gap) - gap)
        overflow = content_w > area.w
        if overflow:
            la = pygame.Rect(area.x + 6, area.centery - 24, 32, 48)
            ra = pygame.Rect(area.right - 38, area.centery - 24, 32, 48)
            pygame.draw.rect(screen, (28, 30, 38), la, border_radius=8)
            pygame.draw.rect(screen, (28, 30, 38), ra, border_radius=8)
            pygame.draw.polygon(screen, (200, 200, 210), [(la.right - 8, la.y + 8), (la.x + 10, la.centery), (la.right - 8, la.bottom - 8)])
            pygame.draw.polygon(screen, (200, 200, 210), [(ra.x + 8, ra.y + 8), (ra.right - 10, ra.centery), (ra.x + 8, ra.bottom - 8)])
        # clip to area
        prev_clip = screen.get_clip()
        screen.set_clip(area.inflate(-2, -2))
        self._tiles.clear()
        mx, my = pygame.mouse.get_pos()
        for i, rw in enumerate(rewards):
            r = pygame.Rect(start_x + i * (tile_w + gap), y, tile_w, tile_h)
            if r.right < area.x or r.x > area.right:
                continue
            self._tiles.append((r, rw.level))
            # base card with hover effect to match SBC/Collection
            hovered = (area.collidepoint((mx, my)) and r.collidepoint((mx, my)))
            base_col = (32, 36, 46)
            if hovered:
                base_col = (38, 42, 56)
            pygame.draw.rect(screen, base_col, r, border_radius=14)
            pygame.draw.rect(screen, (90, 94, 120), r, 2, border_radius=14)
            # title
            t = self.app.h4.render(f'Niveau {rw.level}', True, (235, 235, 245))
            screen.blit(t, (r.centerx - t.get_width() // 2, r.y + 10))
            # background image (cover)
            if getattr(rw, 'bg_img', None):
                try:
                    p = Path(str(rw.bg_img))
                    if (p.is_absolute() and p.exists()) or (_ROOT / str(rw.bg_img)).exists():
                        use_p = p if p.exists() else (_ROOT / str(rw.bg_img))
                        inner_bg = r.inflate(-8, -8)
                        panel = pygame.Surface((inner_bg.w, inner_bg.h), pygame.SRCALPHA)
                        draw_bg_cover(panel, use_p, panel.get_rect())
                        mask = pygame.Surface((inner_bg.w, inner_bg.h), pygame.SRCALPHA)
                        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
                        panel.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        screen.blit(panel, inner_bg.topleft)
                except Exception:
                    pass
            # card image (if card reward)
            if rw.kind == 'card' and getattr(rw, 'card_img', None):
                try:
                    p = Path(str(rw.card_img))
                    if not p.is_absolute():
                        p = _ROOT / str(rw.card_img)
                    if p.exists():
                        draw_player_png_centered(screen, p, r.center, int(r.w * 0.7), int(r.h * 0.7))
                except Exception:
                    pass
            # (badge for unlock rewards removed by request)
            # non-card reward chip (coins/XP/unlock), centered like Defi reward chip
            if rw.kind in ('coins', 'xp', 'unlock'):
                chip = pygame.Surface((int(r.w * 0.7), 32), pygame.SRCALPHA)
                pygame.draw.rect(chip, (60, 62, 78, 210), chip.get_rect(), border_radius=10)
                if rw.kind == 'coins':
                    label = f"+{rw.amount} Coins"
                elif rw.kind == 'xp':
                    label = f"+{rw.amount} XP"
                else:
                    # unlock
                    target_pass = getattr(rw, 'unlock_pass_id', None)
                    feat = getattr(rw, 'unlock_feature', None)
                    if feat == 'sbc':
                        label = 'Débloque SBC'
                    elif feat == 'draft':
                        label = 'Débloque Draft'
                    elif feat == 'defi':
                        label = 'Débloque Défis'
                    elif target_pass == 'halloween':
                        label = 'Débloque Saison 2 : Ultimate Scream'
                    elif target_pass == 'futmas':
                        label = 'Débloque Saison 3 : Futmas'
                    else:
                        label = 'Débloque du contenu'
                ct = self.app.h4.render(label, True, (235, 235, 245))
                chip.blit(ct, (chip.get_width() // 2 - ct.get_width() // 2, chip.get_height() // 2 - ct.get_height() // 2))
                screen.blit(chip, (r.centerx - chip.get_width() // 2, r.centery - chip.get_height() // 2))
            # state + claim button
            current_level = lvl
            claimed = sp_mod.is_claimed(rw.level)
            eligible = sp_mod.can_claim(rw.level, current_level)
            status = 'Réclamé' if claimed else ('Disponible' if eligible else 'Verrouillé')
            st = self.app.h5.render(status, True, (230, 230, 240))
            screen.blit(st, (r.centerx - st.get_width() // 2, r.bottom - 76))
            claim = pygame.Rect(r.centerx - 60, r.bottom - 44, 120, 32)
            pygame.draw.rect(screen, (40, 140, 240) if eligible else (60, 62, 78), claim, border_radius=8)
            ct = self.app.h4.render('Récupérer' if eligible else ('Réclamé' if claimed else 'Bloqué'), True, (255, 255, 255))
            screen.blit(ct, (claim.centerx - ct.get_width() // 2, claim.centery - ct.get_height() // 2))
        # XP progress bar that follows the mouse wheel (overall: Niveau 1 -> Niveau max)
        try:
            max_level = max((rw.level for rw in rewards), default=1)
        except Exception:
            max_level = 1
        # overall ratio includes previous levels + fraction of current
        frac_in_level = 0.0 if need <= 0 else min(1.0, cur / max(1, need))
        denom = max(1, max_level - 1)
        ratio = max(0.0, min(1.0, ((max(lvl, 1) - 1) + frac_in_level) / denom))
        # make the track span the entire scroll content width so it truly goes to the max level
        track_w = content_w if content_w > 0 else int(area.w * 0.9)
        prog_w = max(300, track_w)
        # position the bar at the top of the scroll area
        bar_area = pygame.Rect(start_x + 8, area.y + 6, prog_w, 16)
        # background and border for visibility
        pygame.draw.rect(screen, (50, 54, 70), bar_area, border_radius=8)
        pygame.draw.rect(screen, (90, 94, 120), bar_area, 2, border_radius=8)
        # fill
        fill = pygame.Rect(bar_area.x, bar_area.y, int(bar_area.w * ratio), bar_area.h)
        pygame.draw.rect(screen, (80, 210, 120), fill, border_radius=8)
        # end cap marker for clarity
        head_x = fill.right
        if head_x > bar_area.x:
            pygame.draw.circle(screen, (120, 255, 160), (head_x, bar_area.centery), 5)
        # optional ticks every 5 levels for readability
        step = 5 if max_level > 10 else 1
        denom = max(1, max_level - 1)
        for t in range(0, max_level + 1, step):
            tx = bar_area.x + int(bar_area.w * (t / denom))
            pygame.draw.line(screen, (100, 104, 130), (tx, bar_area.y), (tx, bar_area.bottom), 1)
        # no start/end level labels requested
        # restore clip
        screen.set_clip(prev_clip)
        # bottom hint like SBC/Défis
        hint_txt = 'Molette ou ← → pour défiler · Clique Récupérer quand un palier est atteint'
        hint = self.app.h5.render(hint_txt, True, (160, 160, 170))
        screen.blit(hint, (area.x + 12, area.bottom + 8))
        esc = self.app.h5.render('[Esc] Retour', True, (150, 150, 160))
        screen.blit(esc, (w - esc.get_width() - 32, 32))


class DailyRewards(Screen):
    """Calendar view for the 28-day daily rewards with manual claim option."""
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.message = ''

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # claim button
            w, h = self.app.size
            claim_rect = pygame.Rect(w - 220, 96, 180, 40)
            if claim_rect.collidepoint((mx, my)):
                # try claim
                try:
                    claimed, info = daily_mod.claim_today()
                    if claimed and info:
                        if info.get('type') == 'xp':
                            self.app.show_toast(f"+{int(info.get('amount', 0))} XP obtenu", 2.0)
                        elif info.get('type') == 'coins':
                            self.app.show_toast(f"+{int(info.get('amount', 0))} Minecoins", 2.0)
                        elif info.get('type') == 'player':
                            nm = str(info.get('name', ''))
                            try:
                                from .cards import Card
                                card = Card(name=nm, rarity='squad fondations', bg_color=(90, 110, 150), rating=int(info.get('rating', 84)))
                                self.app.push(SpecialRewardScreen(self.app, card))
                            except Exception:
                                self.app.show_toast(nm, 2.0)
                    else:
                        self.app.show_toast('Déjà réclamé aujourd\'hui', 2.0)
                except Exception:
                    self.app.show_toast('Erreur de réclamation', 2.0)

    def _compute_today_day(self) -> tuple[int, bool]:
        """Return (day_number, already_claimed_today)."""
        import datetime
        st = daily_mod.get_status()
        day_idx = int(st.get('day_index', 0))
        last = st.get('last_claim_date')
        today = datetime.date.today()
        if last == today.isoformat():
            return (max(1, min(28, day_idx or 1)), True)
        # not claimed today → compute next day by consecutive rule
        if not last:
            return (1, False)
        try:
            last_d = datetime.datetime.strptime(last, '%Y-%m-%d').date()
        except Exception:
            return (1, False)
        if today - last_d == datetime.timedelta(days=1):
            nxt = (day_idx or 0) + 1
            return ((1 if nxt > 28 else nxt), False)
        return (1, False)

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((16, 18, 22))
        title = self.app.h2.render('Récompenses quotidiennes', True, (235, 235, 245))
        screen.blit(title, (40, 32))
        # status chip
        try:
            (day_t, claimed_today) = self._compute_today_day()
            st = daily_mod.get_status()
            lbl = f"Jour {day_t}/28  ·  {'Réclamé aujourd\'hui' if claimed_today else 'Disponible'}"
        except Exception:
            lbl = 'Statut indisponible'
        chip = pygame.Rect(40, 80, 420, 44)
        pygame.draw.rect(screen, (28, 30, 38), chip, border_radius=10)
        pygame.draw.rect(screen, (70, 72, 90), chip, 2, border_radius=10)
        t = self.app.h4.render(lbl, True, (235, 235, 245))
        screen.blit(t, (chip.centerx - t.get_width() // 2, chip.centery - t.get_height() // 2))
        # claim button (top-right)
        claim_rect = pygame.Rect(w - 220, 96, 180, 40)
        can_claim = ("Disponible" in lbl)
        pygame.draw.rect(screen, (40, 140, 240) if can_claim else (60, 62, 78), claim_rect, border_radius=10)
        ct = self.app.h4.render('Récupérer', True, (255, 255, 255))
        screen.blit(ct, (claim_rect.centerx - ct.get_width() // 2, claim_rect.centery - ct.get_height() // 2))
        # grid panel
        area = pygame.Rect(40, 140, w - 80, h - 200)
        pygame.draw.rect(screen, (20, 22, 28), area, border_radius=12)
        pygame.draw.rect(screen, (60, 62, 78), area, 2, border_radius=12)
        # layout 7 columns x 4 rows
        cols, rows = 7, 4
        gap = 12
        cell_w = (area.w - (cols + 1) * gap) // cols
        cell_h = (area.h - (rows + 1) * gap) // rows
        # get rewards
        try:
            rewards = daily_mod.list_cycle_rewards()
        except Exception:
            rewards = []
        # determine claimed up to day_index (inclusive if claimed today)
        st = daily_mod.get_status()
        last = st.get('last_claim_date')
        day_idx = int(st.get('day_index', 0))
        import datetime
        already = (last == datetime.date.today().isoformat())
        claimed_upto = day_idx if already else max(0, day_idx)
        # draw tiles
        for i, rw in enumerate(rewards[:28]):
            d = i + 1
            row = i // cols
            col = i % cols
            x = area.x + gap + col * (cell_w + gap)
            y = area.y + gap + row * (cell_h + gap)
            r = pygame.Rect(x, y, cell_w, cell_h)
            # state coloring
            if d <= claimed_upto:
                bg = (28, 40, 30)
                border = (90, 140, 100)
            elif d == day_t and not already:
                bg = (34, 36, 50)
                border = (90, 120, 220)
            else:
                bg = (32, 34, 44)
                border = (90, 90, 110)
            pygame.draw.rect(screen, bg, r, border_radius=10)
            pygame.draw.rect(screen, border, r, 2, border_radius=10)
            # Day label
            dtxt = self.app.h5.render(f'Jour {d}', True, (230, 230, 240))
            screen.blit(dtxt, (r.centerx - dtxt.get_width() // 2, r.y + 6))
            # Content
            if rw.get('type') == 'xp':
                chip = pygame.Surface((int(r.w * 0.7), 26), pygame.SRCALPHA)
                pygame.draw.rect(chip, (60, 62, 78, 210), chip.get_rect(), border_radius=8)
                amt = int(rw.get('amount', 0))
                ct = self.app.h4.render(f"+{amt} XP", True, (235, 235, 245))
                chip.blit(ct, (chip.get_width() // 2 - ct.get_width() // 2, chip.get_height() // 2 - ct.get_height() // 2))
                screen.blit(chip, (r.centerx - chip.get_width() // 2, r.centery - chip.get_height() // 2))
            elif rw.get('type') == 'coins':
                chip = pygame.Surface((int(r.w * 0.8), 26), pygame.SRCALPHA)
                pygame.draw.rect(chip, (60, 62, 78, 210), chip.get_rect(), border_radius=8)
                amt = int(rw.get('amount', 0))
                ct = self.app.h4.render(f"+{amt} Coins", True, (235, 235, 245))
                chip.blit(ct, (chip.get_width() // 2 - ct.get_width() // 2, chip.get_height() // 2 - ct.get_height() // 2))
                screen.blit(chip, (r.centerx - chip.get_width() // 2, r.centery - chip.get_height() // 2))
            elif rw.get('type') == 'player':
                name = str(rw.get('name', ''))
                # try to draw card image
                p = resolve_player_image_by_name_and_rarity(name, None)
                if p is not None:
                    draw_player_png_centered(screen, p, r.center, int(r.w * 0.7), int(r.h * 0.7))
                # name label
                nt = self.app.h5.render(name, True, (220, 220, 230))
                screen.blit(nt, (r.centerx - nt.get_width() // 2, r.bottom - 24))
        # bottom hint
        hint = self.app.h5.render('[Esc] Retour', True, (150, 150, 160))
        screen.blit(hint, (w - hint.get_width() - 32, 32))


class Collection(Screen):
    FILTERS = ['Tous', 'or non rare', 'or rare', 'hero', 'icon', 'otw', 'flashback', "fin d'une ère"]

    def __init__(self, app: 'App'):
        super().__init__(app)
        self.filter_idx = 0
        self.scroll = 0
        self.catalog = game_db.get_unique_catalog()
        self.owned = game_db.load_collection()
        self.owned_only = False
        self.search_text = ''
        self._search_active = False
        self._cell_cache: dict[Tuple[str, int], pygame.Surface] = {}

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # quick SBC access button (top-right)
            sbc_rect = pygame.Rect(self.app.size[0] - 140, 28, 100, 36)
            if sbc_rect.collidepoint((mx, my)):
                try:
                    if sp_mod.is_feature_unlocked('sbc'):
                        self.app.push(SBC(self.app))
                except Exception:
                    pass
                return
            # filter tabs
            tabs_y = 92
            x = 40
            for i, f in enumerate(self.FILTERS):
                r = pygame.Rect(x + i * (150 + 10), tabs_y, 150, 36)
                if r.collidepoint((mx, my)):
                    self.filter_idx = i
                    break
            # owned-only toggle
            own_rect = pygame.Rect(self.app.size[0] - 220, 60, 180, 28)
            if own_rect.collidepoint((mx, my)):
                self.owned_only = not self.owned_only
            # search box
            srect = pygame.Rect(self.app.size[0] - 420, 60, 180, 28)
            self._search_active = srect.collidepoint((mx, my))
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y * 40)
        elif event.type == pygame.KEYDOWN and self._search_active:
            if event.key == pygame.K_BACKSPACE:
                self.search_text = self.search_text[:-1]
            elif event.key == pygame.K_RETURN:
                self._search_active = False
            else:
                ch = event.unicode
                if ch and ch.isprintable():
                    self.search_text += ch

    def _filtered_catalog(self):
        # always reload owned so UI reflects latest pack reveals
        self.owned = game_db.load_collection()
        items = self.catalog
        if self.filter_idx != 0:
            rar = self.FILTERS[self.filter_idx]
            items = [c for c in items if str(c.get('rarity', '')).strip().lower() == rar]
        # search
        if self.search_text:
            needle = _normalize_text(self.search_text)
            items = [c for c in items if needle in _normalize_text(c['name'])]
        # owned only
        if self.owned_only:
            # Use base name (before any '#variant') so variants share ownership visibility
            def _owned(c: dict) -> bool:
                nm = str(c.get('name', '') or '')
                base = nm.split('#')[0].strip()
                return int(self.owned.get(base, 0)) > 0
            items = [c for c in items if _owned(c)]
        return items

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((18, 20, 24))
        title = self.app.h2.render('Collection', True, (230, 230, 240))
        screen.blit(title, (40, 32))
        # SBC quick button
        sbc_rect = pygame.Rect(w - 140, 28, 100, 36)
        mx, my = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()[0]
        sbc_locked = False
        try:
            sbc_locked = not sp_mod.is_feature_unlocked('sbc')
        except Exception:
            pass
        Button(sbc_rect, ('SBC 🔒' if sbc_locked else 'SBC')).draw(screen, self.app.h4, hovered=sbc_rect.collidepoint((mx, my)), pressed=pressed and sbc_rect.collidepoint((mx, my)))

        # progress
        owned_names = {k for k, v in self.owned.items() if v > 0}
        total = len({c['name'] for c in self.catalog})
        pct = int((len(owned_names) / total) * 100) if total else 0
        progress = self.app.h4.render(f"{len(owned_names)}/{total}  ({pct}%)", True, (200, 200, 210))
        screen.blit(progress, (40, 64))

        # owned-only toggle and search box
        own_rect = pygame.Rect(w - 220, 60, 180, 28)
        pygame.draw.rect(screen, (38, 40, 50), own_rect, border_radius=8)
        pygame.draw.rect(screen, (90, 90, 110), own_rect, 2, border_radius=8)
        own_txt = self.app.h5.render(f"Possédés uniquement: {'Oui' if self.owned_only else 'Non'}", True, (235, 235, 245))
        screen.blit(own_txt, (own_rect.x + 8, own_rect.y + 5))

        srect = pygame.Rect(w - 420, 60, 180, 28)
        pygame.draw.rect(screen, (38, 40, 50), srect, border_radius=8)
        pygame.draw.rect(screen, (90, 90, 110), srect, 2, border_radius=8)
        stxt = self.app.h5.render(self.search_text or 'Recherche…', True, (200, 200, 210) if self.search_text else (140, 140, 150))
        screen.blit(stxt, (srect.x + 8, srect.y + 5))

        # filter tabs
        tabs_y = 92
        mx, my = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()[0]
        for i, f in enumerate(self.FILTERS):
            r = pygame.Rect(40 + i * (150 + 10), tabs_y, 150, 36)
            sel = i == self.filter_idx
            hovered = r.collidepoint((mx, my))
            bg = (38, 40, 50) if not sel else (58, 60, 90)
            if hovered:
                bg = (48, 50, 65) if not sel else (68, 70, 110)
            pygame.draw.rect(screen, bg, r, border_radius=10)
            pygame.draw.rect(screen, (90, 90, 110), r, 2, border_radius=10)
            txt = self.app.h5.render(f, True, (235, 235, 245))
            screen.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))

        # grid area
        area = pygame.Rect(40, tabs_y + 52, w - 80, h - (tabs_y + 52) - 40)
        pygame.draw.rect(screen, (25, 27, 33), area, border_radius=16)
        pygame.draw.rect(screen, (70, 72, 90), area, 2, border_radius=16)

        # layout
        items = self._filtered_catalog()
        cols = max(1, area.w // 180)
        gap = 16
        cell_w = (area.w - (cols + 1) * gap) // cols
        cell_h = int(cell_w * 1.3)
        y_off = self.scroll
        start_row = max(0, (y_off // (cell_h + gap)))
        max_rows = max(1, area.h // (cell_h + gap) + 2)
        start_idx = start_row * cols
        end_idx = min(len(items), start_idx + max_rows * cols)
        # Clip drawing to the panel so images never draw outside when scrolling
        prev_clip = screen.get_clip()
        screen.set_clip(area.inflate(-2, -2))
        for idx in range(start_idx, end_idx):
            c = items[idx]
            row = (idx // cols)
            col = (idx % cols)
            x = area.x + gap + col * (cell_w + gap)
            y = area.y + gap + row * (cell_h + gap) - y_off
            r = pygame.Rect(x, y, cell_w, cell_h)
            # skip if completely outside vertically (small optimization)
            if r.bottom < area.y or r.y > area.bottom:
                continue
            self._draw_collection_cell(screen, r, c)
        screen.set_clip(prev_clip)

        hint = self.app.h5.render('[Molette] Scroll   [Esc] Retour', True, (150, 150, 160))
        screen.blit(hint, (w - hint.get_width() - 32, 32))

    def _draw_collection_cell(self, screen: pygame.Surface, rect: pygame.Rect, item: dict):
        name = item['name']
        # Count ownership by base name so variants (e.g., #pass/#sbc) share counts
        base_name = (name or '').split('#')[0].strip()
        owned_count = int(self.owned.get(base_name, 0))
        # Only draw the PNG image (no framed background behind)
        pad = 0
        inner = pygame.Rect(rect.x + pad, rect.y + pad, rect.w - 2 * pad, rect.h - 2 * pad)
        # player image (PNG-first), fill most of the cell
        img = resolve_player_image_by_name_and_rarity(name, item.get('rarity', ''))
        if img is not None:
            draw_player_png_centered(screen, img, inner.center, inner.w, inner.h)
        else:
            # subtle placeholder only if image not found
            pygame.draw.rect(screen, (40, 42, 52), inner, border_radius=10)
        # Note: remove name and rarity text to keep only images as requested
        # exclusivity badges: SBC-only, Défi-only, or Pass-only
        if item.get('sbc_only') or item.get('defi_only') or item.get('pass_only'):
            if item.get('sbc_only'):
                label = 'SBC seulement'
            elif item.get('defi_only'):
                label = 'Défi seulement'
            else:
                label = 'Pass seulement'
            badge = pygame.Surface((120, 20), pygame.SRCALPHA)
            pygame.draw.rect(badge, (200, 120, 40), badge.get_rect(), border_radius=8)
            bt = self.app.h5.render(label, True, (255, 255, 255))
            badge.blit(bt, (badge.get_width() // 2 - bt.get_width() // 2, badge.get_height() // 2 - bt.get_height() // 2))
            screen.blit(badge, (rect.x + 8, rect.y + 8))
        # owned count badge (top-right)
        if owned_count > 1:
            b = pygame.Surface((34, 22), pygame.SRCALPHA)
            pygame.draw.rect(b, (40, 140, 240), b.get_rect(), border_radius=8)
            t = self.app.h5.render(f"x{owned_count}", True, (255, 255, 255))
            b.blit(t, (b.get_width() // 2 - t.get_width() // 2, b.get_height() // 2 - t.get_height() // 2))
            screen.blit(b, (rect.right - b.get_width() - 8, rect.y + 8))
        # lock overlay if not owned
        if owned_count <= 0:
            lock = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
            lock.fill((0, 0, 0, 120))
            screen.blit(lock, inner.topleft)
            # simple lock icon
            bx = inner.centerx - 12
            by = inner.centery - 8
            pygame.draw.rect(screen, (235, 235, 245), pygame.Rect(bx, by, 24, 16), 2, border_radius=4)
            pygame.draw.arc(screen, (235, 235, 245), pygame.Rect(bx + 6, by - 14, 12, 14), 3.14, 0, 2)


class SpecialRewardScreen(Screen):
    """Overlay screen showing an animated special card reward (zoom-in + confetti)."""
    def __init__(self, app: 'App', card: Card):
        super().__init__(app)
        self.card = card
        self.t0 = time.time()
        self._confetti = []  # list of (x, y, vx, vy, col, r)
        w, h = self.app.size
        cols = [(240, 90, 90), (90, 200, 120), (90, 160, 240), (240, 200, 90), (200, 90, 220)]
        for _ in range(140):
            x = random.randint(0, w)
            y = random.randint(-h // 2, 0)
            vx = random.uniform(-40, 40)
            vy = random.uniform(120, 240)
            col = random.choice(cols)
            r = random.randint(2, 4)
            self._confetti.append([x, y, vx, vy, col, r])

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            self.app.pop()

    def update(self, dt: float):
        w, h = self.app.size
        for i in range(len(self._confetti)):
            x, y, vx, vy, col, r = self._confetti[i]
            y += vy * dt
            x += vx * dt
            if y > h + 10:
                y = random.randint(-h // 2, -10)
                x = random.randint(0, w)
            self._confetti[i][0] = x
            self._confetti[i][1] = y

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        # dim the background
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        # confetti
        now = time.time()
        for x, y, vx, vy, col, r in self._confetti:
            pygame.draw.circle(screen, col, (int(x), int(y)), r)
        # center panel
        panel = pygame.Rect(w // 2 - 360, h // 2 - 220, 720, 440)
        pygame.draw.rect(screen, (24, 26, 34), panel, border_radius=16)
        pygame.draw.rect(screen, (90, 90, 110), panel, 2, border_radius=16)
        # title
        title = self.app.h3.render('Carte spéciale obtenue !', True, (235, 235, 245))
        screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 20))
        # zoom animation
        t = min(1.0, (now - self.t0) / 1.0)
        # ease out cubic
        s = 1 - pow(1 - t, 3)
        max_w = int(panel.w * 0.42)
        max_h = int(panel.h * 0.58)
        img = resolve_player_image_by_name_and_rarity(self.card.name, self.card.rarity)
        if img is not None:
            draw_player_png_centered(screen, img, (panel.centerx, panel.centery + 10), int(max_w * s), int(max_h * s))
        # name + rarity
        nm = self.app.h3.render(self.card.name, True, (230, 230, 240))
        screen.blit(nm, (panel.centerx - nm.get_width() // 2, panel.bottom - 96))
        rar = self.app.h5.render(str(self.card.rarity).upper(), True, (200, 200, 210))
        screen.blit(rar, (panel.centerx - rar.get_width() // 2, panel.bottom - 68))
        hint = self.app.h5.render('Cliquer ou Entrée pour continuer', True, (170, 170, 180))
        screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 36))


class SBC(Screen):
    def __init__(self, app: 'App'):
        super().__init__(app)
        # FIFA-like SBC hub (tile menu like the screenshot)
        self.message = ''
        self.groups = self._build_groups()
        self.tile_scroll_x = 0
        self.hover_tile = -1
        # Tabs: 'Tous', 'Ultimate Scream' and 'Premium'
        self.tabs = ['Tous', 'Ultimate Scream', 'Premium']
        self.active_tab = 0

    def _challenges(self):
        return sbc_mod.CHALLENGES

    def _owned(self):
        return game_db.load_collection()

    def _catalog(self):
        return sbc_mod.get_catalog_index()

    # --- New: group tiles (like FIFA) ---
    def _build_groups(self):
        # Group busquets series together; others are standalone
        groups = []
        busq_ids = [ch.id for ch in self._challenges() if ch.id.startswith('busquets_eoe_')]
        if busq_ids:
            groups.append({
                'title': "Sergio Busquets — Fin d'une ère",
                'challenge_ids': busq_ids,
                'days': 15,
                'image_key': 'Sergio Busquets',
                'bg': (92, 82, 54),
                'bg_img': str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Fin d'une ère\\fond fin d'une  ère.png")),
                'type': 'premium',
            })
        alba_ids = [ch.id for ch in self._challenges() if ch.id.startswith('alba_eoe_')]
        if alba_ids:
            groups.append({
                'title': "Jordi Alba — Fin d'une ère",
                'challenge_ids': alba_ids,
                'days': 12,
                'image_key': 'Jordi Alba',
                'bg': (92, 82, 54),
                'bg_img': str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Fin d'une ère\\fond fin d'une  ère.png")),
                'type': 'premium',
            })
        gori_ids = [ch.id for ch in self._challenges() if ch.id.startswith('goretzka_fb_')]
        # fallback by name contains 'flashback' + 'goretzka' if prefix not found
        if not gori_ids:
            gori_ids = [ch.id for ch in self._challenges() if ('flashback' in _normalize_text(ch.name) and 'goretzka' in _normalize_text(ch.name))]
        if gori_ids:
            groups.append({
                'title': 'Goretzka — Flashback',
                'challenge_ids': gori_ids,
                'days': 10,
                'image_key': 'Goretzka',
                'bg': (46, 76, 112),
                'bg_img': str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Flashback\\fond flashback.png")),
            })
        dzeko_ids = [ch.id for ch in self._challenges() if ch.id.startswith('dzeko_fb_')]
        if not dzeko_ids:
            dzeko_ids = [ch.id for ch in self._challenges() if ('flashback' in _normalize_text(ch.name) and ('dzeko' in _normalize_text(ch.name) or 'džeko' in _normalize_text(ch.name)))]
        if dzeko_ids:
            groups.append({
                'title': 'Džeko — Flashback',
                'challenge_ids': dzeko_ids,
                'days': 10,
                'image_key': 'Džeko',
                'bg': (46, 76, 112),
                'bg_img': str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Flashback\\fond flashback.png")),
            })
        # Flashback: Xherdan Shaqiri
        shaq_ids = [ch.id for ch in self._challenges() if ch.id.startswith('shaqiri_fb_')]
        if not shaq_ids:
            shaq_ids = [ch.id for ch in self._challenges() if ('flashback' in _normalize_text(ch.name) and 'shaqiri' in _normalize_text(ch.name))]
        if shaq_ids:
            groups.append({
                'title': 'Xherdan Shaqiri — Flashback',
                'challenge_ids': shaq_ids,
                'days': 10,
                'image_key': 'Xherdan Shaqiri',
                'bg': (46, 76, 112),
                'bg_img': str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Flashback\\fond flashback.png")),
                'type': 'halloween',
            })
        # Hero: Van Buyten
        van_ids = [ch.id for ch in self._challenges() if ch.id.startswith('vanbuyten_hero_')]
        if not van_ids:
            van_ids = [ch.id for ch in self._challenges() if ('hero' in _normalize_text(ch.name) and 'van buyten' in _normalize_text(ch.name))]
        if van_ids:
            groups.append({
                'title': 'Van Buyten — Héro',
                'challenge_ids': van_ids,
                'days': 9,
                'image_key': 'Van Buyten',
                'bg': (84, 58, 110),
                'bg_img': str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png")),
            })
        # Icon début: Zlatan Ibrahimović (5 steps)
        zlatan_ids = [ch.id for ch in self._challenges() if ch.id.startswith('zlatan_icon_')]
        if not zlatan_ids:
            zlatan_ids = [ch.id for ch in self._challenges() if ('icon' in _normalize_text(ch.name) and ('zlatan' in _normalize_text(ch.name) or 'ibrahimovic' in _normalize_text(ch.name)))]
        if zlatan_ids:
            groups.append({
                'title': 'Zlatan Ibrahimović — Icon début',
                'challenge_ids': zlatan_ids,
                'days': 20,
                'image_key': 'Ibrahimović',
                'bg': (90, 90, 110),
                'bg_img': str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon debut champion\\fond icon debut champion .png")),
            })
        # Hero: Dimitri Payet (single)
        payet_ids = [ch.id for ch in self._challenges() if ch.id.startswith('payet_hero_')]
        if not payet_ids:
            payet_ids = [ch.id for ch in self._challenges() if ('hero' in _normalize_text(ch.name) and 'payet' in _normalize_text(ch.name))]
        if payet_ids:
            groups.append({
                'title': 'Dimitri Payet — Héro',
                'challenge_ids': payet_ids,
                'days': 9,
                'image_key': 'Payet',
                'bg': (84, 58, 110),
                'bg_img': str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png")),
            })
        # Ultimate Scream: Paul Pogba (single)
        pogba_ids = [ch.id for ch in self._challenges() if ch.id.startswith('pogba_halloween_')]
        if pogba_ids:
            groups.append({
                'title': 'Paul Pogba — Ultimate Scream',
                'challenge_ids': pogba_ids,
                'days': 14,
                'image_key': 'Paul Pogba#sbc',
                'bg_img': str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Joueur\\fond ultimate scream.png")),
                'bg': (96, 72, 20),  # orange-ish
                'type': 'halloween',
            })
        # other singles
        for ch in self._challenges():
            name_norm = _normalize_text(ch.name)
            is_flashback_name = ('flashback' in name_norm and ('goretzka' in name_norm or 'dzeko' in name_norm or 'džeko' in name_norm))
            if ch.id.startswith('busquets_eoe_') or ch.id.startswith('alba_eoe_') or ch.id.startswith('goretzka_fb_') or ch.id.startswith('dzeko_fb_') or is_flashback_name:
                continue
            groups.append({
                'title': ch.name,
                'challenge_ids': [ch.id],
                'days': 5,
                'image_key': None,
                'bg': (58, 62, 78),
            })
        return groups

    def _visible_groups(self):
        if self.active_tab == 0:
            return self.groups
        if self.active_tab == 1:
            # Ultimate Scream tab
            return [g for g in self.groups if str(g.get('type', '')).lower() == 'halloween']
        # Premium tab
        return [g for g in self.groups if str(g.get('type', '')).lower() == 'premium']

    def _group_progress(self, challenge_ids: List[str]) -> tuple[int, int]:
        done = sum(1 for cid in challenge_ids if sbc_mod.is_completed(cid))
        return done, len(challenge_ids)

    def _next_incomplete_index(self, challenge_ids: List[str]) -> Optional[int]:
        id_to_index = {ch.id: i for i, ch in enumerate(self._challenges())}
        for cid in challenge_ids:
            if not sbc_mod.is_completed(cid):
                return id_to_index.get(cid)
        # all complete; return the last one's index
        if challenge_ids:
            return id_to_index.get(challenge_ids[-1])
        return None

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
            return
        if event.type == pygame.MOUSEWHEEL:
            # horizontal scroll with wheel
            self.tile_scroll_x = max(0, self.tile_scroll_x - event.y * 60)
            return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            # Dynamic step = one tile width + gap based on current window height
            win_w, win_h = self.app.size
            area_h = win_h - 220
            tile_h = max(220, area_h - 24)
            tile_w = int(tile_h * 0.78)
            gap = 20
            step = tile_w + gap
            dx = -step if event.key == pygame.K_LEFT else step
            self.tile_scroll_x = max(0, self.tile_scroll_x + dx)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # tabs (placeholder)
            tx = 40
            ty = 88
            for i, t in enumerate(self.tabs):
                r = pygame.Rect(tx + i * (120 + 8), ty, 120, 36)
                if r.collidepoint((mx, my)):
                    self.active_tab = i
                    return
            # tiles area
            area = pygame.Rect(40, 140, self.app.size[0] - 80, self.app.size[1] - 220)
            # Make tile height fill the vertical area with a 12px padding top/bottom
            tile_h = max(220, area.h - 24)
            tile_w = int(tile_h * 0.78)
            gap = 20
            start_x = area.x + 4 - self.tile_scroll_x
            y = area.y
            # arrows (if overflow) handled below
            vis_groups = self._visible_groups()
            content_w = max(0, len(vis_groups) * (tile_w + gap) - gap)
            overflow = content_w > area.w
            left_arrow = right_arrow = None
            if overflow:
                left_arrow = pygame.Rect(area.x + 6, area.centery - 24, 32, 48)
                right_arrow = pygame.Rect(area.right - 38, area.centery - 24, 32, 48)
                if left_arrow.collidepoint((mx, my)):
                    self.tile_scroll_x = max(0, self.tile_scroll_x - (tile_w + gap))
                    return
                if right_arrow.collidepoint((mx, my)):
                    self.tile_scroll_x = max(0, self.tile_scroll_x + (tile_w + gap))
                    return
            for idx, g in enumerate(vis_groups):
                r = pygame.Rect(start_x + idx * (tile_w + gap), y, tile_w, tile_h)
                # Only allow clicks inside the panel area
                if area.collidepoint((mx, my)) and r.collidepoint((mx, my)):
                    # open group detail if multiple steps, else go straight to the single challenge
                    if len(g['challenge_ids']) > 1:
                        try:
                            self.app.push(SBCGroupDetail(self.app, g['title'], g['challenge_ids']))
                        except Exception:
                            pass
                    else:
                        next_idx = self._next_incomplete_index(g['challenge_ids'])
                        if next_idx is not None:
                            try:
                                self.app.push(SBCSquad(self.app, next_idx))
                            except Exception:
                                pass
                    return

    def _filtered_owned_names(self) -> List[str]:
        # Not used in hub view anymore; keep as safe stub
        return []

    def _toggle_select(self, name: str):
        # Not used in hub view
        return

    def _submit(self):
        # Not used in hub view
        return

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((12, 14, 18))
        # title
        title = self.app.h2.render('SBC', True, (235, 235, 245))
        screen.blit(title, (40, 32))
        # tabs (placeholder)
        tx = 40
        ty = 88
        for i, t in enumerate(self.tabs):
            r = pygame.Rect(tx + i * (120 + 8), ty, 120, 36)
            sel = i == self.active_tab
            pygame.draw.rect(screen, (38, 40, 50) if not sel else (58, 60, 90), r, border_radius=10)
            pygame.draw.rect(screen, (90, 90, 110), r, 2, border_radius=10)
            lbl = self.app.h4.render(t, True, (235, 235, 245))
            screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))

    # tiles area
        area = pygame.Rect(40, 140, w - 80, h - 220)
        pygame.draw.rect(screen, (18, 20, 26), area, border_radius=12)
        pygame.draw.rect(screen, (60, 62, 78), area, 2, border_radius=12)
        # Dynamic tile size: fill vertical space with margins
        tile_h = max(220, area.h - 24)
        tile_w = int(tile_h * 0.78)
        gap = 20
        start_x = area.x + 4 - self.tile_scroll_x
        y = area.y + 12
        mx, my = pygame.mouse.get_pos()
        self.hover_tile = -1
        # overflow arrows
        vis_groups = self._visible_groups()
        content_w = max(0, len(vis_groups) * (tile_w + gap) - gap)
        overflow = content_w > area.w
        if overflow:
            # left arrow
            la = pygame.Rect(area.x + 6, area.centery - 24, 32, 48)
            ra = pygame.Rect(area.right - 38, area.centery - 24, 32, 48)
            pygame.draw.rect(screen, (28, 30, 38), la, border_radius=8)
            pygame.draw.rect(screen, (28, 30, 38), ra, border_radius=8)
            pygame.draw.polygon(screen, (200, 200, 210), [(la.right - 8, la.y + 8), (la.x + 10, la.centery), (la.right - 8, la.bottom - 8)])
            pygame.draw.polygon(screen, (200, 200, 210), [(ra.x + 8, ra.y + 8), (ra.right - 10, ra.centery), (ra.x + 8, ra.bottom - 8)])
        # Clip drawing to the panel so tiles never paint outside the frame
        prev_clip = screen.get_clip()
        screen.set_clip(area.inflate(-2, -2))
        for idx, g in enumerate(vis_groups):
            r = pygame.Rect(start_x + idx * (tile_w + gap), y, tile_w, tile_h)
            if r.right < area.x or r.x > area.right:
                continue
            hovered = (area.collidepoint((mx, my)) and r.collidepoint((mx, my)))
            if hovered:
                self.hover_tile = idx
            # card background (use group bg on the frame itself)
            tile_bg = g.get('bg') or (30, 32, 42)
            if hovered:
                tile_bg = tuple(min(255, c + 12) for c in tile_bg)
            pygame.draw.rect(screen, tile_bg, r, border_radius=14)
            # background image inside the card (cover) with rounded-corner mask so it never escapes the frame
            bg_img = g.get('bg_img')
            if bg_img:
                try:
                    p = Path(str(bg_img))
                    if (p.is_absolute() and p.exists()) or (_ROOT / str(bg_img)).exists():
                        use_p = p if p.exists() else (_ROOT / str(bg_img))
                        inner = r.inflate(-8, -8)
                        # render onto a temporary surface
                        panel = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
                        draw_bg_cover(panel, use_p, panel.get_rect())
                        # rounded mask
                        mask = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
                        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
                        panel.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        screen.blit(panel, inner.topleft)
                except Exception:
                    pass
            pygame.draw.rect(screen, (90, 90, 110), r, 2, border_radius=14)
            # corner ribbon like FIFA
            rib = pygame.Rect(r.right - 36, r.y + 8, 28, 28)
            pygame.draw.polygon(screen, (80, 180, 220), [(rib.x, rib.y), (rib.right, rib.y), (rib.right, rib.bottom)])
            # title
            ttl = self.app.h4.render(g['title'], True, (235, 235, 245))
            screen.blit(ttl, (r.x + 12, r.y + 12))
            # emblem area (image) - scaled with tile size
            shield_h = max(120, int(r.h * 0.44))
            shield_w = int(shield_h * 0.8)
            shield_y = r.y + max(70, int(r.h * 0.2))
            # ensure bottom spacing stays within the card
            if shield_y + shield_h > r.bottom - 96:
                shield_y = r.bottom - 96 - shield_h
            shield = pygame.Rect(r.centerx - shield_w // 2, shield_y, shield_w, shield_h)
            # neutral shield background and frame (image sits on top)
            pygame.draw.rect(screen, (60, 64, 80), shield, border_radius=16)
            pygame.draw.rect(screen, (120, 124, 140), shield, 2, border_radius=16)
            # try to draw group image if available
            gkey = g.get('image_key')
            if gkey:
                p = resolve_player_image_by_name_and_rarity(gkey, None)
                if p is not None:
                    # draw centered inside shield with small padding
                    draw_player_png_centered(screen, p, (shield.centerx, shield.centery), shield.w - 12, shield.h - 12)
            # stars (progress style)
            done, total = self._group_progress(g['challenge_ids'])
            for s in range(3):
                cx = r.centerx - 34 + s * 34
                cy = min(r.bottom - 60, shield.bottom + max(18, int(r.h * 0.05)))
                col = (200, 200, 210) if s < min(3, done) else (100, 100, 120)
                pygame.draw.circle(screen, col, (cx, cy), 9)
            # remaining days
            rem = self.app.h5.render(f"{g['days']} Days Remaining", True, (180, 180, 190))
            rem_y = min(r.bottom - 42, cy + max(12, int(r.h * 0.05)))
            screen.blit(rem, (r.centerx - rem.get_width() // 2, rem_y))
            # completed text
            comp = self.app.h5.render(f"{done}/{total} COMPLETED", True, (210, 210, 220))
            screen.blit(comp, (r.centerx - comp.get_width() // 2, r.bottom - 34))
        # restore clipping
        screen.set_clip(prev_clip)

        # hint
        hint_txt = 'Molette ou ← → pour défiler · Clique une tuile pour ouvrir'
        hint = self.app.h5.render(hint_txt, True, (160, 160, 170))
        screen.blit(hint, (area.x + 12, area.bottom + 8))
        esc = self.app.h5.render('[Esc] Retour', True, (150, 150, 160))
        screen.blit(esc, (w - esc.get_width() - 32, 32))

class Defi(Screen):
    def __init__(self, app: 'App'):
        super().__init__(app)
        self.active_group_idx = 0
        self.groups = defi_mod.groups() or ['Tous']
        if 'Tous' not in self.groups:
            self.groups = ['Tous'] + self.groups
        self.message = ''
        self.tile_scroll_x = 0
        self.hover_tile = -1

    def _boateng_ids(self) -> List[str]:
        try:
            tasks = defi_mod.list_defis(None if self.groups[self.active_group_idx] == 'Tous' else self.groups[self.active_group_idx])
        except Exception:
            tasks = defi_mod.list_defis(None)
        return [d.id for d in tasks if str(getattr(d, 'id', '')).startswith('boateng_eoe_')]

    def _build_items(self):
        """Return a list of tiles to render: either ('group', dict) or ('defi', Defi).
        Groups supported: Boateng (6), Juninho (6), Lacazette (4), Iniesta (8), Pogba (3).
        """
        gname = self.groups[self.active_group_idx]
        tasks = defi_mod.list_defis(None if gname == 'Tous' else gname)
        # series definitions: prefix -> (title, bg_img, image_key)
        series = [
            ('boateng_eoe_', "Jérôme Boateng — Fin d'une ère", str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Fin d'une ère\\fond fin d'une  ère.png")), "Jérôme Boateng"),
            ('juninho_hero_', 'Juninho — Héro', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png")), 'Juninho'),
            ('lacazette_flashback_', 'Lacazette — Flashback', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Flashback\\fond flashback.png")), 'Lacazette'),
            ('iniesta_icon_debut_', 'Iniesta — Icon début', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon debut champion\\fond icon debut champion .png")), 'Iniesta'),
            ('pogba_halloween_defi_', 'Paul Pogba — Ultimate Scream', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Joueur\\fond ultimate scream.png")), 'Paul Pogba#sbc'),
            ('forsberg_flashback_', 'Emil Forsberg — Flashback', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Flashback\\fond flashback.png")), 'Emil Forsberg'),
        ]
        used_ids = set()
        items = []
        for pref, title, bgimg, image_key in series:
            lst = [d for d in tasks if d.id.startswith(pref)]
            if lst:
                lst = sorted(lst, key=lambda d: d.id)
                items.append(('group', {
                    'title': title,
                    'ids': [d.id for d in lst],
                    'bg_img': bgimg,
                    'image_key': image_key,
                    'steps': len(lst),
                }))
                used_ids.update(d.id for d in lst)
        # append remaining individual defis
        for d in tasks:
            if d.id not in used_ids:
                items.append(('defi', d))
        return items

    def _tasks(self):
        g = self.groups[self.active_group_idx]
        return defi_mod.list_defis(None if g == 'Tous' else g)

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
            return
        if event.type == pygame.MOUSEWHEEL:
            # horizontal scroll via mouse wheel
            self.tile_scroll_x = max(0, self.tile_scroll_x - event.y * 60)
            return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            # scroll by one tile step
            win_w, win_h = self.app.size
            area_h = win_h - 220
            tile_h = max(220, area_h - 24)
            tile_w = int(tile_h * 0.78)
            gap = 20
            step = tile_w + gap
            dx = -step if event.key == pygame.K_LEFT else step
            self.tile_scroll_x = max(0, self.tile_scroll_x + dx)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # tabs
            tx, ty = 40, 96
            for i, g in enumerate(self.groups):
                r = pygame.Rect(tx + i * (140 + 8), ty, 140, 34)
                if r.collidepoint((mx, my)):
                    self.active_group_idx = i
                    return
            # tiles area + claim buttons inside tile
            area = pygame.Rect(40, 140, self.app.size[0] - 80, self.app.size[1] - 220)
            tile_h = max(220, area.h - 24)
            tile_w = int(tile_h * 0.78)
            gap = 20
            start_x = area.x + 4 - self.tile_scroll_x
            y = area.y + 12
            items = self._build_items()
            for idx, itm in enumerate(items):
                r = pygame.Rect(start_x + idx * (tile_w + gap), y, tile_w, tile_h)
                if not area.collidepoint((mx, my)) or not r.collidepoint((mx, my)):
                    continue
                kind = itm[0]
                if kind == 'group':
                    data = itm[1]
                    # open group detail for Boateng steps
                    try:
                        self.app.push(DefiGroupDetail(self.app, data['title'], data['ids']))
                    except Exception:
                        pass
                    return
                else:
                    d = itm[1]
                    # claim button rectangle within the tile
                    claim = pygame.Rect(r.centerx - 60, r.bottom - 56, 120, 36)
                    if claim.collidepoint((mx, my)):
                        if defi_mod.can_claim(d):
                            ok = defi_mod.claim(d)
                            self.message = 'Récompense récupérée' if ok else 'Non disponible'
                        else:
                            self.message = 'Incomplet ou déjà réclamé'
                        return

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((12, 14, 18))
        title = self.app.h2.render('Défis', True, (235, 235, 245))
        screen.blit(title, (40, 32))
        # tabs
        tx, ty = 40, 96
        mx, my = pygame.mouse.get_pos()
        for i, g in enumerate(self.groups):
            r = pygame.Rect(tx + i * (140 + 8), ty, 140, 34)
            sel = (i == self.active_group_idx)
            pygame.draw.rect(screen, (38, 40, 50) if not sel else (58, 60, 90), r, border_radius=10)
            pygame.draw.rect(screen, (90, 90, 110), r, 2, border_radius=10)
            lbl = self.app.h4.render(g, True, (235, 235, 245))
            screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))

        # tiles panel (same style as SBC hub)
        area = pygame.Rect(40, 140, w - 80, h - 220)
        pygame.draw.rect(screen, (18, 20, 26), area, border_radius=12)
        pygame.draw.rect(screen, (60, 62, 78), area, 2, border_radius=12)
        tile_h = max(220, area.h - 24)
        tile_w = int(tile_h * 0.78)
        gap = 20
        start_x = area.x + 4 - self.tile_scroll_x
        y = area.y + 12
        # overflow arrows
        items = self._build_items()
        content_w = max(0, len(items) * (tile_w + gap) - gap)
        overflow = content_w > area.w
        if overflow:
            la = pygame.Rect(area.x + 6, area.centery - 24, 32, 48)
            ra = pygame.Rect(area.right - 38, area.centery - 24, 32, 48)
            pygame.draw.rect(screen, (28, 30, 38), la, border_radius=8)
            pygame.draw.rect(screen, (28, 30, 38), ra, border_radius=8)
            pygame.draw.polygon(screen, (200, 200, 210), [(la.right - 8, la.y + 8), (la.x + 10, la.centery), (la.right - 8, la.bottom - 8)])
            pygame.draw.polygon(screen, (200, 200, 210), [(ra.x + 8, ra.y + 8), (ra.right - 10, ra.centery), (ra.x + 8, ra.bottom - 8)])

        prev_clip = screen.get_clip()
        screen.set_clip(area.inflate(-2, -2))
        self.hover_tile = -1
        for idx, itm in enumerate(items):
            r = pygame.Rect(start_x + idx * (tile_w + gap), y, tile_w, tile_h)
            if r.right < area.x or r.x > area.right:
                continue
            hovered = (area.collidepoint((mx, my)) and r.collidepoint((mx, my)))
            if hovered:
                self.hover_tile = idx
            # base tile
            bg = (32, 34, 44)
            if hovered:
                bg = (40, 42, 54)
            pygame.draw.rect(screen, bg, r, border_radius=14)
            pygame.draw.rect(screen, (90, 90, 110), r, 2, border_radius=14)
            if itm[0] == 'group':
                data = itm[1]
                # background image like SBC tiles with mask
                try:
                    p = Path(str(data.get('bg_img', '')))
                    if p and ((p.is_absolute() and p.exists()) or (_ROOT / str(p)).exists()):
                        use_p = p if p.exists() else (_ROOT / str(p))
                        inner = r.inflate(-8, -8)
                        panel = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
                        draw_bg_cover(panel, use_p, panel.get_rect())
                        mask = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
                        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
                        panel.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        screen.blit(panel, inner.topleft)
                except Exception:
                    pass
                # title
                ttl = self.app.h4.render(data['title'], True, (235, 235, 245))
                screen.blit(ttl, (r.x + 12, r.y + 12))
                # emblem (Boateng image)
                shield_h = max(120, int(r.h * 0.44))
                shield_w = int(shield_h * 0.8)
                shield = pygame.Rect(r.centerx - shield_w // 2, r.y + int(r.h * 0.22), shield_w, shield_h)
                pygame.draw.rect(screen, (60, 64, 80), shield, border_radius=16)
                pygame.draw.rect(screen, (120, 124, 140), shield, 2, border_radius=16)
                # emblem image based on the group's configured image_key
                try:
                    key_name = str(data.get('image_key') or '')
                    pimg = resolve_player_image_by_name_and_rarity(key_name, None)
                    if pimg is not None:
                        draw_player_png_centered(screen, pimg, shield.center, shield.w - 12, shield.h - 12)
                except Exception:
                    pass
                # steps chip
                chip = pygame.Surface((140, 24), pygame.SRCALPHA)
                pygame.draw.rect(chip, (60, 62, 78, 200), chip.get_rect(), border_radius=8)
                ct = self.app.h5.render(f"{data['steps']} ÉTAPES", True, (230, 230, 240))
                chip.blit(ct, (chip.get_width() // 2 - ct.get_width() // 2, chip.get_height() // 2 - ct.get_height() // 2))
                screen.blit(chip, (r.x + 12, r.bottom - 48))
                # Open hint
                bt = self.app.h4.render('Ouvrir', True, (255, 255, 255))
                open_btn = pygame.Rect(r.centerx - 60, r.bottom - 56, 120, 36)
                pygame.draw.rect(screen, (40, 140, 240), open_btn, border_radius=10)
                screen.blit(bt, (open_btn.centerx - bt.get_width() // 2, open_btn.centery - bt.get_height() // 2))
            else:
                d = itm[1]
                # optional background image
                if getattr(d, 'bg_img', None):
                    try:
                        p = Path(str(d.bg_img))
                        if (p.is_absolute() and p.exists()) or (_ROOT / str(d.bg_img)).exists():
                            use_p = p if p.exists() else (_ROOT / str(d.bg_img))
                            inner = r.inflate(-8, -8)
                            panel = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
                            draw_bg_cover(panel, use_p, panel.get_rect())
                            mask = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
                            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
                            panel.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                            screen.blit(panel, inner.topleft)
                    except Exception:
                        pass
                # title & desc
                ttl = self.app.h4.render(d.name, True, (235, 235, 245))
                screen.blit(ttl, (r.x + 12, r.y + 12))
                dsc = self.app.h5.render(d.description, True, (200, 200, 210))
                screen.blit(dsc, (r.x + 12, r.y + 44))
                # card image if present
                if getattr(d, 'card_img', None):
                    try:
                        p = Path(str(d.card_img))
                        if not p.is_absolute():
                            p = _ROOT / str(d.card_img)
                        if p.exists():
                            shield_h = max(120, int(r.h * 0.44))
                            shield_w = int(shield_h * 0.8)
                            shield = pygame.Rect(r.centerx - shield_w // 2, r.y + int(r.h * 0.22), shield_w, shield_h)
                            draw_player_png_centered(screen, p, shield.center, shield.w - 8, shield.h - 8)
                    except Exception:
                        pass
                # progress bar
                cur = defi_mod.get_progress(d.event_key)
                tgt = max(1, d.target)
                prog = min(cur / tgt, 1.0)
                bar = pygame.Rect(r.x + 12, min(r.bottom - 64, r.y + int(r.h * 0.7)), r.w - 24, 8)
                pygame.draw.rect(screen, (46, 48, 60), bar, border_radius=6)
                fill = pygame.Rect(bar.x, bar.y, int(bar.w * prog), bar.h)
                pygame.draw.rect(screen, (90, 200, 110), fill, border_radius=6)
                pr = self.app.h5.render(f"{min(cur, tgt)}/{tgt}", True, (210, 210, 220))
                screen.blit(pr, (bar.centerx - pr.get_width() // 2, bar.y - 18))
                # reward chip
                typ, amt = d.reward
                chip = pygame.Surface((130, 22), pygame.SRCALPHA)
                pygame.draw.rect(chip, (60, 62, 78, 200), chip.get_rect(), border_radius=8)
                text = f"+{amt} {'XP' if typ=='xp' else 'Coins'}"
                ct = self.app.h5.render(text, True, (230, 230, 240))
                chip.blit(ct, (chip.get_width() // 2 - ct.get_width() // 2, chip.get_height() // 2 - ct.get_height() // 2))
                screen.blit(chip, (r.x + 12, r.bottom - 48))
                # claim button
                can = defi_mod.can_claim(d)
                claim = pygame.Rect(r.centerx - 60, r.bottom - 56, 120, 36)
                pygame.draw.rect(screen, (40, 140, 240) if can else (60, 62, 78), claim, border_radius=10)
                bt = self.app.h4.render('Récupérer' if can else 'Bloqué', True, (255, 255, 255))
                screen.blit(bt, (claim.centerx - bt.get_width() // 2, claim.centery - bt.get_height() // 2))
        screen.set_clip(prev_clip)

        # hint
        hint_txt = 'Molette ou ← → pour défiler · Clique Récupérer quand un défi est terminé'
        hint = self.app.h5.render(hint_txt, True, (160, 160, 170))
        screen.blit(hint, (area.x + 12, area.bottom + 8))
        esc = self.app.h5.render('[Esc] Retour', True, (150, 150, 160))
        screen.blit(esc, (w - esc.get_width() - 32, 32))


class DefiGroupDetail(Screen):
    """Detail view for a group of Défis (multi-step) with SBC-like layout and sizing."""
    def __init__(self, app: 'App', title: str, defi_ids: List[str]):
        super().__init__(app)
        self.title = title
        self.defi_ids = defi_ids
        # build id->defi mapping once
        self.id_map = {d.id: d for d in defi_mod.list_defis(None)}
        # select first non-claimed, else last
        self.selected_id = None
        for cid in self.defi_ids:
            try:
                if not defi_mod.is_claimed(cid):
                    self.selected_id = cid
                    break
            except Exception:
                pass
        if self.selected_id is None and self.defi_ids:
            self.selected_id = self.defi_ids[-1]

    def _selected_defi(self):
        if not self.selected_id:
            return None
        return self.id_map.get(self.selected_id)

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            d = self._selected_defi()
            if d is not None and defi_mod.can_claim(d):
                defi_mod.claim(d)
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            w, h = self.app.size
            area = pygame.Rect(40, 140, w - 80 - 360, h - 220)
            padding, gap = 12, 12
            rows = 2
            n = len(self.defi_ids)
            inner = pygame.Rect(area.x + padding, area.y + padding, area.w - 2 * padding, area.h - 2 * padding)
            if n == 2:
                cols = 2
                col_w = (inner.w - (cols - 1) * gap) // cols
                row0_h = (inner.h - gap) // 2
                x_left = inner.x
                x_right = inner.x + col_w + gap
                y_top = inner.y
                for i, cid in enumerate(self.defi_ids):
                    if i == 0:
                        r = pygame.Rect(x_left, y_top, col_w, row0_h)
                    else:
                        r = pygame.Rect(x_right, y_top, col_w, row0_h)
                    if r.collidepoint((mx, my)):
                        self.selected_id = cid
                        return
            else:
                cols = max(2, (n + rows - 1) // rows)
                step_w = (inner.w - (cols - 1) * gap) / max(1, cols)
                step_h = (inner.h - (rows - 1) * gap) / max(1, rows)
                for i, cid in enumerate(self.defi_ids):
                    col = i % cols
                    row = i // cols
                    x = int(round(inner.x + col * (step_w + gap)))
                    y = int(round(inner.y + row * (step_h + gap)))
                    w_rect = inner.right - x if col == cols - 1 else int(round(step_w))
                    h_rect = inner.bottom - y if row == rows - 1 else int(round(step_h))
                    r = pygame.Rect(x, y, w_rect, h_rect)
                    if r.collidepoint((mx, my)):
                        self.selected_id = cid
                        return
            # right panel claim button
            right = pygame.Rect(area.right + 24, area.y, 336, area.h)
            claim_rect = pygame.Rect(right.x + 20, right.bottom - 64, right.w - 40, 44)
            if claim_rect.collidepoint((mx, my)):
                d = self._selected_defi()
                if d is not None and defi_mod.can_claim(d):
                    defi_mod.claim(d)

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((10, 12, 16))
        hdr = self.app.h2.render(self.title, True, (235, 235, 245))
        screen.blit(hdr, (40, 32))
        area = pygame.Rect(40, 140, w - 80 - 360, h - 220)
        right = pygame.Rect(area.right + 24, area.y, 336, area.h)
        pygame.draw.rect(screen, (18, 20, 26), area, border_radius=12)
        pygame.draw.rect(screen, (60, 62, 78), area, 2, border_radius=12)
        pygame.draw.rect(screen, (18, 20, 26), right, border_radius=12)
        pygame.draw.rect(screen, (60, 62, 78), right, 2, border_radius=12)

        padding, gap = 12, 12
        rows = 2
        n = len(self.defi_ids)
        inner = pygame.Rect(area.x + padding, area.y + padding, area.w - 2 * padding, area.h - 2 * padding)
        mx, my = pygame.mouse.get_pos()
        if n == 2:
            cols = 2
            col_w = (inner.w - (cols - 1) * gap) // cols
            row0_h = (inner.h - gap) // 2
            x_left = inner.x
            x_right = inner.x + col_w + gap
            y_top = inner.y
            for i, cid in enumerate(self.defi_ids):
                d = self.id_map.get(cid)
                if i == 0:
                    r = pygame.Rect(x_left, y_top, col_w, row0_h)
                else:
                    r = pygame.Rect(x_right, y_top, col_w, row0_h)
                claimed = defi_mod.is_claimed(cid)
                selected = (cid == self.selected_id)
                hovered = r.collidepoint((mx, my))
                bg = (32, 34, 44)
                if selected:
                    bg = (190, 220, 60)
                elif hovered:
                    bg = (40, 42, 54)
                pygame.draw.rect(screen, bg, r, border_radius=12)
                pygame.draw.rect(screen, (90, 92, 110), r, 2, border_radius=12)
                ttl = self.app.h4.render(d.name, True, (20, 22, 26) if selected else (235, 235, 245))
                screen.blit(ttl, (r.x + 16, r.y + 12))
                dsc = self.app.h5.render(d.description, True, (30, 32, 36) if selected else (200, 200, 210))
                screen.blit(dsc, (r.x + 16, r.y + 46))
                if claimed:
                    badge = self.app.h5.render('COMPLETED', True, (20, 22, 26) if selected else (180, 240, 120))
                    screen.blit(badge, (r.x + 16, r.bottom - 28))
        else:
            cols = max(2, (n + rows - 1) // rows)
            step_w = (inner.w - (cols - 1) * gap) / max(1, cols)
            step_h = (inner.h - (rows - 1) * gap) / max(1, rows)
            for i, cid in enumerate(self.defi_ids):
                d = self.id_map.get(cid)
                col = i % cols
                row = i // cols
                x = int(round(inner.x + col * (step_w + gap)))
                y = int(round(inner.y + row * (step_h + gap)))
                w_rect = inner.right - x if col == cols - 1 else int(round(step_w))
                h_rect = inner.bottom - y if row == rows - 1 else int(round(step_h))
                r = pygame.Rect(x, y, w_rect, h_rect)
                claimed = defi_mod.is_claimed(cid)
                selected = (cid == self.selected_id)
                hovered = r.collidepoint((mx, my))
                bg = (32, 34, 44)
                if selected:
                    bg = (190, 220, 60)
                elif hovered:
                    bg = (40, 42, 54)
                pygame.draw.rect(screen, bg, r, border_radius=12)
                pygame.draw.rect(screen, (90, 92, 110), r, 2, border_radius=12)
                ttl = self.app.h4.render(d.name, True, (20, 22, 26) if selected else (235, 235, 245))
                screen.blit(ttl, (r.x + 16, r.y + 12))
                dsc = self.app.h5.render(d.description, True, (30, 32, 36) if selected else (200, 200, 210))
                screen.blit(dsc, (r.x + 16, r.y + 46))
                if claimed:
                    badge = self.app.h5.render('COMPLETED', True, (20, 22, 26) if selected else (180, 240, 120))
                    screen.blit(badge, (r.x + 16, r.bottom - 28))

        # right panel: selected details + claim
        d = self._selected_defi()
        if d is not None:
            hdr2 = self.app.h4.render(d.name, True, (235, 235, 245))
            screen.blit(hdr2, (right.x + 16, right.y + 16))
            sub = self.app.h5.render('OBJECTIF', True, (180, 180, 190))
            screen.blit(sub, (right.x + 16, right.y + 54))
            y0 = right.y + 80
            # show target and current progress
            try:
                cur = defi_mod.get_progress(d.event_key)
                tgt = max(1, d.target)
                lines = [
                    f"Compléter {tgt} SBC au total",
                    f"Progression: {min(cur, tgt)}/{tgt}",
                ]
            except Exception:
                lines = []
            for b in lines:
                dot = self.app.h4.render('•', True, (210, 210, 220))
                txt = self.app.h5.render(b, True, (210, 210, 220))
                screen.blit(dot, (right.x + 18, y0))
                screen.blit(txt, (right.x + 36, y0 + 4))
                y0 += 28
            # reward label
            rw = self.app.h5.render('RÉCOMPENSE', True, (180, 180, 190))
            screen.blit(rw, (right.x + 16, right.bottom - 108))
            # claim button
            can = defi_mod.can_claim(d)
            claim_rect = pygame.Rect(right.x + 20, right.bottom - 64, right.w - 40, 44)
            pygame.draw.rect(screen, (40, 140, 240) if can else (60, 62, 78), claim_rect, border_radius=10)
            lbl = self.app.h4.render('Récupérer' if can else ('Réclamé' if defi_mod.is_claimed(d.id) else 'Bloqué'), True, (255, 255, 255))
            screen.blit(lbl, (claim_rect.centerx - lbl.get_width() // 2, claim_rect.centery - lbl.get_height() // 2))

        hint = self.app.h5.render('[Esc] Retour', True, (150, 150, 160))
        screen.blit(hint, (w - hint.get_width() - 32, 32))


class SBCSquad(Screen):
    """Dedicated squad page for a specific SBC challenge. Only duplicates are usable."""
    def __init__(self, app: 'App', challenge_index: int):
        super().__init__(app)
        self.challenge_index = challenge_index
        # fixed 11 slots (4-3-3) — None when empty, otherwise player name
        self.slots = [None] * 11
        self.message = ''
        self.reward_cards = None
        self.search = ''
        self._search_active = False
        self.pool_scroll = 0
        self.FILTERS = ['Tous', 'or non rare', 'or rare', 'hero', 'icon', 'otw']
        self.filter_idx = 0
        # background pitch image for the squad placement area
        try:
            root = Path(__file__).resolve().parents[1]
            p = root / 'Fond' / 'terrain de foot vertical.png'
            self._pitch_img_path = p if p.exists() else None
        except Exception:
            self._pitch_img_path = None
        # drag & drop state
        self._drag_name = None
        self._drag_pos = (0, 0)
        self._drag_from = None  # 'pool' or 'slot'

    def _ch(self):
        return sbc_mod.CHALLENGES[self.challenge_index]

    def _owned(self):
        return game_db.load_collection()

    def _catalog(self):
        return sbc_mod.get_catalog_index()

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # rarity filter tabs
            fbase = pygame.Rect(40, 108, 560, 32)
            for i, f in enumerate(self.FILTERS):
                r = pygame.Rect(fbase.x + i * (100 + 8), fbase.y, 100, fbase.h)
                if r.collidepoint((mx, my)):
                    self.filter_idx = i
                    self.pool_scroll = 0
                    return
            # search
            srect = pygame.Rect(self.app.size[0] - 420, 108, 220, 28)
            self._search_active = srect.collidepoint((mx, my))
            # buttons
            submit_rect = pygame.Rect(self.app.size[0] - 220, self.app.size[1] - 80, 160, 42)
            clear_rect = pygame.Rect(self.app.size[0] - 400, self.app.size[1] - 80, 160, 42)
            if submit_rect.collidepoint((mx, my)):
                self._submit()
                return
            if clear_rect.collidepoint((mx, my)):
                self.slots = [None] * 11
                self.message = ''
                self.reward_cards = None
                return
            # right slots (formation) : click to remove
            w, h = self.app.size
            right = pygame.Rect(w // 2 + 20, 156, w - (w // 2 + 20) - 40, h - 240)
            # fixed 4-3-3 with exactly 11 slots
            target_n = 11
            for i, r in enumerate(self._formation_433_positions(right, target_n)):
                if r.collidepoint((mx, my)) and self.slots[i] is not None:
                    # simple remove on click (drag from slot not implemented yet)
                    self.slots[i] = None
                    return
            # start drag from pool card
            left = pygame.Rect(40, 156, w // 2 - 60, h - 240)
            pool = self._filtered_owned_names()
            gap = 12
            cols = max(1, (left.w - gap) // 160)
            card_w = (left.w - (cols + 1) * gap) // cols
            card_h = int(card_w * 1.35)
            cell_h = card_h + 16
            y_off = self.pool_scroll
            start_row = max(0, y_off // (cell_h + gap))
            max_rows = max(1, left.h // (cell_h + gap) + 2)
            start_idx = start_row * cols
            end_idx = min(len(pool), start_idx + max_rows * cols)
            for idx in range(start_idx, end_idx):
                name = pool[idx]
                row = (idx // cols)
                col = (idx % cols)
                x = left.x + gap + col * (card_w + gap)
                y = left.y + gap + (row * (cell_h + gap)) - y_off
                r = pygame.Rect(x, y, card_w, card_h)
                if r.collidepoint((mx, my)):
                    self._drag_name = name
                    self._drag_from = 'pool'
                    self._drag_pos = (mx, my)
                    return
        elif event.type == pygame.MOUSEMOTION:
            self._drag_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._drag_name:
                mx, my = event.pos
                w, h = self.app.size
                right = pygame.Rect(w // 2 + 20, 156, w - (w // 2 + 20) - 40, h - 240)
                slots = self._formation_433_positions(right, 11)
                for i, r in enumerate(slots):
                    if r.collidepoint((mx, my)):
                        name = self._drag_name
                        owned_cnt = self._owned().get(name, 0)
                        cur = sum(1 for x in self.slots if x == name)
                        if self.slots[i] is None and cur < max(0, owned_cnt - 1):
                            self.slots[i] = name
                        else:
                            self.message = "Emplacement indisponible ou pas assez de doublons"
                        break
                self._drag_name = None
                self._drag_from = None
        elif event.type == pygame.KEYDOWN and self._search_active:
            if event.key == pygame.K_BACKSPACE:
                self.search = self.search[:-1]
            elif event.key == pygame.K_RETURN:
                self._search_active = False
            else:
                ch = event.unicode
                if ch and ch.isprintable():
                    self.search += ch
        elif event.type == pygame.MOUSEWHEEL:
            w, h = self.app.size
            left = pygame.Rect(40, 156, w // 2 - 60, h - 240)
            if left.collidepoint(pygame.mouse.get_pos()):
                self.pool_scroll = max(0, self.pool_scroll - event.y * 40)

    def _filtered_owned_names(self) -> List[str]:
        owned = self._owned()
        index = self._catalog()
        # duplicates only: count >= 2
        names = [n for n, c in owned.items() if c >= 2 and n in index]
        if self.filter_idx != 0:
            rar = self.FILTERS[self.filter_idx]
            names = [n for n in names if _normalize_text(index[n].get('rarity', '')) == _normalize_text(rar)]
        if self.search:
            needle = _normalize_text(self.search)
            names = [n for n in names if needle in _normalize_text(n)]
        names.sort(key=lambda n: (-int(index[n].get('rating', 0)), n))
        return names

    def _toggle_select(self, name: str):
        # Add to first empty slot if allowed; otherwise remove one occurrence
        owned_cnt = self._owned().get(name, 0)
        cur = sum(1 for x in self.slots if x == name)
        max_allowed = max(0, owned_cnt - 1)
        if cur < max_allowed and any(s is None for s in self.slots):
            for i in range(len(self.slots)):
                if self.slots[i] is None:
                    self.slots[i] = name
                    return
        else:
            for i, x in enumerate(self.slots):
                if x == name:
                    self.slots[i] = None
                    return

    def _submit(self):
        ch_obj = self._ch()
        # must be exactly 11 players selected (no None)
        if any(s is None for s in self.slots):
            cur = sum(1 for s in self.slots if s is not None)
            self.message = f"Sélection incomplète (" + str(cur) + "/11)."
            return
        # quick duplicates guard: ensure we keep at least one of each selected name
        owned = self._owned()
        need: dict[str, int] = {}
        sel_list = [s for s in self.slots if s is not None]
        for n in sel_list:
            need[n] = need.get(n, 0) + 1
        for n, cnt in need.items():
            if owned.get(n, 0) - cnt < 1:
                self.message = f"Utilise uniquement tes doublons (pas assez de {n})."
                return
        ok, msg = sbc_mod.validate_selection(sel_list, ch_obj)
        if not ok:
            self.message = msg
            return
        # also check normal consume guard (owned >= need)
        ok2, msg2 = sbc_mod.can_consume(sel_list)
        if not ok2:
            self.message = msg2
            return
        sbc_mod.consume(sel_list)
        self.slots = [None] * 11
        self.message = 'Défi validé ! Récompense en cours…'
        pack_name, count = ch_obj.reward_pack
        self.reward_cards = generate_pack(pack_name, count)
        game_db.add_to_collection_by_names([c.name for c in self.reward_cards])
        # log defi event: sbc completed
        try:
            defi_mod.add_progress('sbc_completed', 1)
        except Exception:
            pass
        # mark completion and check special Busquets reward
        try:
            sbc_mod.mark_completed(ch_obj.id)
            extras_to_show: List[Card] = []
            extra = sbc_mod.check_and_grant_busquets_bundle()
            if extra is not None:
                self.message = "Défi validé ! Récompense en cours… + Busquets obtenu !"
                self.reward_cards.append(extra)
                extras_to_show.append(extra)
            # check Alba as well
            extra2 = sbc_mod.check_and_grant_alba_bundle()
            if extra2 is not None:
                self.message = "Défi validé ! Récompense en cours… + Alba obtenu !"
                self.reward_cards.append(extra2)
                extras_to_show.append(extra2)
            # check Flashbacks: Goretzka & Džeko
            extra3 = sbc_mod.check_and_grant_goretzka_bundle()
            if extra3 is not None:
                self.message = "Défi validé ! Récompense en cours… + Goretzka obtenu !"
                self.reward_cards.append(extra3)
                extras_to_show.append(extra3)
            extra4 = sbc_mod.check_and_grant_dzeko_bundle()
            if extra4 is not None:
                self.message = "Défi validé ! Récompense en cours… + Džeko obtenu !"
                self.reward_cards.append(extra4)
                extras_to_show.append(extra4)
            # check Flashback: Xherdan Shaqiri
            extra_sh = sbc_mod.check_and_grant_shaqiri_bundle()
            if extra_sh is not None:
                self.message = "Défi validé ! Récompense en cours… + Shaqiri obtenu !"
                self.reward_cards.append(extra_sh)
                extras_to_show.append(extra_sh)
            # check Hero: Van Buyten
            extra5 = sbc_mod.check_and_grant_vanbuyten_bundle()
            if extra5 is not None:
                self.message = "Défi validé ! Récompense en cours… + Van Buyten obtenu !"
                self.reward_cards.append(extra5)
                extras_to_show.append(extra5)
            # check Hero: Dimitri Payet
            extra6 = sbc_mod.check_and_grant_payet_bundle()
            if extra6 is not None:
                self.message = "Défi validé ! Récompense en cours… + Payet obtenu !"
                self.reward_cards.append(extra6)
                extras_to_show.append(extra6)
            # check Icon début: Zlatan Ibrahimović
            extra7 = sbc_mod.check_and_grant_zlatan_bundle()
            if extra7 is not None:
                self.message = "Défi validé ! Récompense en cours… + Ibrahimović obtenu !"
                self.reward_cards.append(extra7)
                extras_to_show.append(extra7)
            # check Halloween: Paul Pogba
            extra8 = sbc_mod.check_and_grant_pogba_bundle()
            if extra8 is not None:
                self.message = "Défi validé ! Récompense en cours… + Pogba obtenu !"
                self.reward_cards.append(extra8)
                extras_to_show.append(extra8)
            # push special reward screens (stacked)
            for c in reversed(extras_to_show):
                self.app.push(SpecialRewardScreen(self.app, c))
        except Exception:
            pass

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((14, 16, 20))
        title = self.app.h2.render('SQUAD — Défi SBC', True, (230, 230, 240))
        screen.blit(title, (40, 32))
        # challenge name
        ch_obj = self._ch()
        cname = self.app.h4.render(ch_obj.name, True, (210, 210, 220))
        screen.blit(cname, (40, 68))
        # search box
        srect = pygame.Rect(w - 420, 108, 220, 28)
        pygame.draw.rect(screen, (38, 40, 50), srect, border_radius=8)
        pygame.draw.rect(screen, (90, 90, 110), srect, 2, border_radius=8)
        stxt = self.app.h5.render(self.search or 'Recherche…', True, (200, 200, 210) if self.search else (140, 140, 150))
        screen.blit(stxt, (srect.x + 8, srect.y + 5))
        # rarity filter tabs
        fbase = pygame.Rect(40, 108, 560, 32)
        for i, f in enumerate(self.FILTERS):
            r = pygame.Rect(fbase.x + i * (100 + 8), fbase.y, 100, fbase.h)
            sel = i == self.filter_idx
            bg = (38, 40, 50) if not sel else (58, 60, 90)
            pygame.draw.rect(screen, bg, r, border_radius=8)
            pygame.draw.rect(screen, (90, 90, 110), r, 1, border_radius=8)
            txt = self.app.h5.render(f, True, (235, 235, 245))
            screen.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - txt.get_height() // 2))

        # left pool (duplicates only) — show card images (thumbnails) instead of name rows
        left = pygame.Rect(40, 156, w // 2 - 60, h - 240)
        pygame.draw.rect(screen, (25, 27, 33), left, border_radius=12)
        pygame.draw.rect(screen, (70, 72, 90), left, 2, border_radius=12)
        pool = self._filtered_owned_names()
        # grid layout
        gap = 12
        cols = max(1, (left.w - gap) // 160)  # aim ~150-160px cards
        card_w = (left.w - (cols + 1) * gap) // cols
        card_h = int(card_w * 1.35)
        cell_h = card_h + 16
        y_off = self.pool_scroll
        start_row = max(0, y_off // (cell_h + gap))
        max_rows = max(1, left.h // (cell_h + gap) + 2)
        start_idx = start_row * cols
        end_idx = min(len(pool), start_idx + max_rows * cols)
        mx, my = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()[0]
        for idx in range(start_idx, end_idx):
            name = pool[idx]
            row = (idx // cols)
            col = (idx % cols)
            x = left.x + gap + col * (card_w + gap)
            y = left.y + gap + (row * (cell_h + gap)) - y_off
            # card rect
            r = pygame.Rect(x, y, card_w, card_h)
            item = self._catalog()[name]
            color = RARITY_COLORS.get(item.get('rarity', ''), (120, 120, 130))
            # card background and border
            pygame.draw.rect(screen, (30, 32, 40), r, border_radius=12)
            pygame.draw.rect(screen, color, r, 2, border_radius=12)
            # image inside with small padding
            img = resolve_player_image_by_name_and_rarity(name, item.get('rarity', ''))
            pad = 6
            inner = pygame.Rect(r.x + pad, r.y + pad, r.w - 2 * pad, r.h - 2 * pad)
            if img is not None:
                draw_player_png_centered(screen, img, inner.center, inner.w, inner.h)
            else:
                pygame.draw.rect(screen, (45, 47, 58), inner, border_radius=10)
            # duplicates badge (owned-1)
            owned_cnt = max(0, self._owned().get(name, 0) - 1)
            badge = pygame.Rect(r.right - 38, r.y + 8, 30, 20)
            pygame.draw.rect(screen, (28, 30, 38), badge, border_radius=6)
            pygame.draw.rect(screen, (90, 92, 110), badge, 1, border_radius=6)
            btxt = self.app.h5.render(f"x{owned_cnt}", True, (235, 235, 245))
            screen.blit(btxt, (badge.centerx - btxt.get_width() // 2, badge.centery - btxt.get_height() // 2))
            # plus button overlay
            plus = pygame.Rect(r.right - 28, r.bottom - 28, 24, 24)
            hovered = plus.collidepoint((mx, my))
            pygame.draw.rect(screen, (80, 180, 90) if not hovered else (90, 200, 100), plus, border_radius=6)
            ptxt = self.app.h5.render('+', True, (255, 255, 255))
            screen.blit(ptxt, (plus.centerx - ptxt.get_width() // 2, plus.centery - ptxt.get_height() // 2 - 1))
            if hovered and pressed:
                self._toggle_select(name)

        # right formation (4-3-3) with pitch background
        right = pygame.Rect(w // 2 + 20, 156, w - (w // 2 + 20) - 40, h - 240)
        # draw background image (cover) clipped to rounded rect; fallback to green pitch lines
        if self._pitch_img_path is not None:
            panel = pygame.Surface((right.w, right.h), pygame.SRCALPHA)
            ok = draw_bg_cover(panel, self._pitch_img_path, panel.get_rect())
            # rounded mask so it doesn't escape the area
            mask = pygame.Surface((right.w, right.h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
            panel.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(panel, right.topleft)
            if not ok:
                # fallback if draw failed
                pitch = pygame.Surface((right.w, right.h))
                pitch.fill((24, 66, 40))
                pygame.draw.rect(pitch, (220, 220, 220), pitch.get_rect(), 2, border_radius=12)
                mid_y = right.h // 2
                pygame.draw.line(pitch, (220, 220, 220), (10, mid_y), (right.w - 10, mid_y), 1)
                screen.blit(pitch, right.topleft)
        else:
            pitch = pygame.Surface((right.w, right.h))
            pitch.fill((24, 66, 40))
            pygame.draw.rect(pitch, (220, 220, 220), pitch.get_rect(), 2, border_radius=12)
            mid_y = right.h // 2
            pygame.draw.line(pitch, (220, 220, 220), (10, mid_y), (right.w - 10, mid_y), 1)
            screen.blit(pitch, right.topleft)

        # render exactly 11 slots for 4-3-3
        slots = self._formation_433_positions(right, 11)
        for i, r in enumerate(slots):
            pygame.draw.rect(screen, (32, 34, 42), r, border_radius=10)
            pygame.draw.rect(screen, (70, 72, 90), r, 2, border_radius=10)
            num = self.app.h5.render(str(i + 1), True, (160, 160, 170))
            screen.blit(num, (r.x + 8, r.y + 6))
            if self.slots[i] is not None:
                name = self.slots[i]
                item = self._catalog()[name]
                img = resolve_player_image_by_name_and_rarity(name, item.get('rarity', ''))
                pad = 6
                inner = pygame.Rect(r.x + pad, r.y + pad, r.w - 2 * pad, r.h - 2 * pad)
                if img is not None:
                    draw_player_png_centered(screen, img, inner.center, inner.w, inner.h)
                else:
                    pygame.draw.rect(screen, (40, 42, 52), inner, border_radius=8)
                ntxt = self.app.h5.render(name, True, (235, 235, 245))
                screen.blit(ntxt, (r.centerx - ntxt.get_width() // 2, r.bottom - ntxt.get_height() - 4))
            else:
                hint = self.app.h5.render('Ajouter', True, (120, 120, 130))
                screen.blit(hint, (r.centerx - hint.get_width() // 2, r.centery - hint.get_height() // 2))

        # highlight slot under cursor while dragging
        if self._drag_name:
            mx, my = pygame.mouse.get_pos()
            for r in slots:
                if r.collidepoint((mx, my)):
                    pygame.draw.rect(screen, (90, 200, 110), r, 3, border_radius=10)
                    break

        # bottom controls and info
        submit_rect = pygame.Rect(w - 220, h - 80, 160, 42)
        clear_rect = pygame.Rect(w - 400, h - 80, 160, 42)
        pygame.draw.rect(screen, (40, 140, 240), submit_rect, border_radius=10)
        pygame.draw.rect(screen, (120, 120, 140), clear_rect, border_radius=10)
        screen.blit(self.app.h4.render('Valider', True, (255, 255, 255)), (submit_rect.x + 24, submit_rect.y + 8))
        screen.blit(self.app.h4.render('Effacer', True, (255, 255, 255)), (clear_rect.x + 24, clear_rect.y + 8))

        pack_name, count = self._ch().reward_pack
        preview = self.app.h4.render(f"Récompense: {pack_name} x{count}", True, (210, 210, 220))
        screen.blit(preview, (40, h - 118))
        if self.message:
            m = self.app.h4.render(self.message, True, (220, 220, 230))
            screen.blit(m, (40, h - 78))
        if self.reward_cards:
            strip = pygame.Rect(40, h - 220, w - 320, 120)
            pygame.draw.rect(screen, (20, 22, 28), strip, border_radius=10)
            x = strip.x + 10
            for c in self.reward_cards:
                img = resolve_player_image_by_name_and_rarity(c.name, c.rarity)
                if img is not None:
                    draw_player_png_centered(screen, img, (x + 50, strip.centery), 100, 110)
                x += 110
        hint = self.app.h5.render('[Esc] Retour', True, (150, 150, 160))
        screen.blit(hint, (w - hint.get_width() - 32, 32))
        # draw floating dragged card
        if self._drag_name:
            name = self._drag_name
            item = self._catalog().get(name)
            if item:
                color = RARITY_COLORS.get(item.get('rarity', ''), (120, 120, 130))
                mx, my = self._drag_pos
                fw, fh = 140, int(140 * 1.35)
                r = pygame.Rect(mx - fw // 2, my - fh // 2, fw, fh)
                pygame.draw.rect(screen, (30, 32, 40, 220), r, border_radius=12)
                pygame.draw.rect(screen, color, r, 2, border_radius=12)
                img = resolve_player_image_by_name_and_rarity(name, item.get('rarity', ''))
                pad = 6
                inner = pygame.Rect(r.x + pad, r.y + pad, r.w - 2 * pad, r.h - 2 * pad)
                if img is not None:
                    draw_player_png_centered(screen, img, inner.center, inner.w, inner.h)
                ntxt = self.app.h5.render(name, True, (235, 235, 245))
                screen.blit(ntxt, (r.centerx - ntxt.get_width() // 2, r.bottom - ntxt.get_height() - 4))

    def _formation_433_positions(self, area: pygame.Rect, count: int) -> List[pygame.Rect]:
        # center coordinates normalized for 4-3-3: forwards (top), mids, defs, GK (bottom)
        W, H = area.w, area.h
        cx = lambda f: area.x + int(W * f)
        cy = lambda f: area.y + int(H * f)
        centers = []
        # Forwards (LW, ST, RW)
        centers += [(cx(0.2), cy(0.18)), (cx(0.5), cy(0.18)), (cx(0.8), cy(0.18))]
        # Midfield (LCM, CM, RCM)
        centers += [(cx(0.25), cy(0.40)), (cx(0.5), cy(0.40)), (cx(0.75), cy(0.40))]
        # Defense (LB, LCB, RCB, RB)
        centers += [(cx(0.15), cy(0.65)), (cx(0.38), cy(0.65)), (cx(0.62), cy(0.65)), (cx(0.85), cy(0.65))]
        # GK
        centers += [(cx(0.5), cy(0.85))]
        # determine slot size
        s = max(64, min(W // 5, H // 6))
        rects: List[pygame.Rect] = []
        for (x, y) in centers[:count]:
            r = pygame.Rect(0, 0, int(s * 0.9), int(s * 1.1))
            r.center = (x, y)
            rects.append(r)
        return rects


class SBCGroupDetail(Screen):
    """Detail view for a group of SBCs (multi-step). Shows step tiles and a requirements panel."""
    def __init__(self, app: 'App', title: str, challenge_ids: List[str]):
        super().__init__(app)
        self.title = title
        self.challenge_ids = challenge_ids
        # map ids to indices in global list
        self.id_to_index = {ch.id: i for i, ch in enumerate(sbc_mod.CHALLENGES)}
        # default select next incomplete
        self.selected_id = None
        for cid in self.challenge_ids:
            if not sbc_mod.is_completed(cid):
                self.selected_id = cid
                break
        if self.selected_id is None and self.challenge_ids:
            self.selected_id = self.challenge_ids[-1]

    def _selected_challenge(self):
        if not self.selected_id:
            return None
        idx = self.id_to_index.get(self.selected_id)
        if idx is None:
            return None
        return sbc_mod.CHALLENGES[idx]

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            ch = self._selected_challenge()
            if ch is not None:
                idx = self.id_to_index.get(ch.id)
                if idx is not None:
                    self.app.push(SBCSquad(self.app, idx))
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # step tiles area (left)
            w, h = self.app.size
            area = pygame.Rect(40, 140, w - 80 - 360, h - 220)
            # 2 rows per column layout
            padding, gap = 12, 12
            rows = 2
            n = len(self.challenge_ids)
            inner = pygame.Rect(40 + padding, 140 + padding, (w - 80 - 360) - 2 * padding, (h - 220) - 2 * padding)
            if n == 2:
                # Place both steps on the TOP ROW: left and right columns, using 2x2 grid sizes.
                cols = 2
                col_w = (inner.w - (cols - 1) * gap) // cols
                row0_h = (inner.h - gap) // 2
                x_left = inner.x
                x_right = inner.x + col_w + gap
                y_top = inner.y
                for i, cid in enumerate(self.challenge_ids):
                    if i == 0:
                        r = pygame.Rect(x_left, y_top, col_w, row0_h)
                    else:
                        r = pygame.Rect(x_right, y_top, col_w, row0_h)
                    if r.collidepoint((mx, my)):
                        self.selected_id = cid
                        return
            else:
                # Fill entire panel: distribute width and height across cols x rows
                cols = max(2, (n + rows - 1) // rows)
                step_w = (inner.w - (cols - 1) * gap) / max(1, cols)
                step_h = (inner.h - (rows - 1) * gap) / max(1, rows)
                for i, cid in enumerate(self.challenge_ids):
                    col = i % cols
                    row = i // cols
                    x = int(round(inner.x + col * (step_w + gap)))
                    y = int(round(inner.y + row * (step_h + gap)))
                    # last col/row absorb leftover pixels
                    w_rect = inner.right - x if col == cols - 1 else int(round(step_w))
                    h_rect = inner.bottom - y if row == rows - 1 else int(round(step_h))
                    r = pygame.Rect(x, y, w_rect, h_rect)
                    if r.collidepoint((mx, my)):
                        self.selected_id = cid
                        return
            # start button in right panel
            right = pygame.Rect(area.right + 24, area.y, 336, area.h)
            start_rect = pygame.Rect(right.x + 20, right.bottom - 64, right.w - 40, 44)
            if start_rect.collidepoint((mx, my)):
                ch = self._selected_challenge()
                if ch is not None:
                    idx = self.id_to_index.get(ch.id)
                    if idx is not None:
                        self.app.push(SBCSquad(self.app, idx))

    def draw(self, screen: pygame.Surface):
        w, h = self.app.size
        screen.fill((10, 12, 16))
        # header / breadcrumb-like
        hdr = self.app.h2.render(self.title, True, (235, 235, 245))
        screen.blit(hdr, (40, 32))
        # areas
        area = pygame.Rect(40, 140, w - 80 - 360, h - 220)
        right = pygame.Rect(area.right + 24, area.y, 336, area.h)
        pygame.draw.rect(screen, (18, 20, 26), area, border_radius=12)
        pygame.draw.rect(screen, (60, 62, 78), area, 2, border_radius=12)
        pygame.draw.rect(screen, (18, 20, 26), right, border_radius=12)
        pygame.draw.rect(screen, (60, 62, 78), right, 2, border_radius=12)

        # step tiles in a grid: fill panel except when exactly 2 challenges (don't stretch)
        padding, gap = 12, 12
        rows = 2
        n = len(self.challenge_ids)
        inner = pygame.Rect(area.x + padding, area.y + padding, area.w - 2 * padding, area.h - 2 * padding)
        mx, my = pygame.mouse.get_pos()
        if n == 2:
            # Draw both steps on the top row, left and right columns, with 2x2 grid sizing
            cols = 2
            col_w = (inner.w - (cols - 1) * gap) // cols
            row0_h = (inner.h - gap) // 2
            x_left = inner.x
            x_right = inner.x + col_w + gap
            y_top = inner.y
            for i, cid in enumerate(self.challenge_ids):
                ch = sbc_mod.CHALLENGES[self.id_to_index[cid]]
                if i == 0:
                    r = pygame.Rect(x_left, y_top, col_w, row0_h)
                else:
                    r = pygame.Rect(x_right, y_top, col_w, row0_h)
                completed = sbc_mod.is_completed(cid)
                selected = (cid == self.selected_id)
                hovered = r.collidepoint((mx, my))
                bg = (32, 34, 44)
                if selected:
                    bg = (190, 220, 60)
                elif hovered:
                    bg = (40, 42, 54)
                pygame.draw.rect(screen, bg, r, border_radius=12)
                pygame.draw.rect(screen, (90, 92, 110), r, 2, border_radius=12)
                ttl = self.app.h4.render(ch.name, True, (20, 22, 26) if selected else (235, 235, 245))
                screen.blit(ttl, (r.x + 16, r.y + 12))
                dsc = self.app.h5.render(ch.description, True, (30, 32, 36) if selected else (200, 200, 210))
                screen.blit(dsc, (r.x + 16, r.y + 46))
                emblem = pygame.Rect(r.right - 110, r.y + 40, 76, 76)
                pygame.draw.rect(screen, (70, 72, 90), emblem, border_radius=14)
                pygame.draw.rect(screen, (120, 124, 140), emblem, 2, border_radius=14)
                if completed:
                    badge = self.app.h5.render('COMPLETED', True, (20, 22, 26) if selected else (180, 240, 120))
                    screen.blit(badge, (r.x + 16, r.bottom - 28))
        else:
            cols = max(2, (n + rows - 1) // rows)
            step_w = (inner.w - (cols - 1) * gap) / max(1, cols)
            step_h = (inner.h - (rows - 1) * gap) / max(1, rows)
            for i, cid in enumerate(self.challenge_ids):
                ch = sbc_mod.CHALLENGES[self.id_to_index[cid]]
                col = i % cols
                row = i // cols
                x = int(round(inner.x + col * (step_w + gap)))
                y = int(round(inner.y + row * (step_h + gap)))
                w_rect = inner.right - x if col == cols - 1 else int(round(step_w))
                h_rect = inner.bottom - y if row == rows - 1 else int(round(step_h))
                r = pygame.Rect(x, y, w_rect, h_rect)
                completed = sbc_mod.is_completed(cid)
                selected = (cid == self.selected_id)
                hovered = r.collidepoint((mx, my))
                bg = (32, 34, 44)
                if selected:
                    bg = (190, 220, 60)
                elif hovered:
                    bg = (40, 42, 54)
                pygame.draw.rect(screen, bg, r, border_radius=12)
                pygame.draw.rect(screen, (90, 92, 110), r, 2, border_radius=12)
                ttl = self.app.h4.render(ch.name, True, (20, 22, 26) if selected else (235, 235, 245))
                screen.blit(ttl, (r.x + 16, r.y + 12))
                dsc = self.app.h5.render(ch.description, True, (30, 32, 36) if selected else (200, 200, 210))
                screen.blit(dsc, (r.x + 16, r.y + 46))
                emblem = pygame.Rect(r.right - 110, r.y + 40, 76, 76)
                pygame.draw.rect(screen, (70, 72, 90), emblem, border_radius=14)
                pygame.draw.rect(screen, (120, 124, 140), emblem, 2, border_radius=14)
                if completed:
                    badge = self.app.h5.render('COMPLETED', True, (20, 22, 26) if selected else (180, 240, 120))
                    screen.blit(badge, (r.x + 16, r.bottom - 28))

        # right panel: requirements
        ch = self._selected_challenge()
        if ch is not None:
            hdr2 = self.app.h4.render(ch.name, True, (235, 235, 245))
            screen.blit(hdr2, (right.x + 16, right.y + 16))
            sub = self.app.h5.render('REQUIREMENTS', True, (180, 180, 190))
            screen.blit(sub, (right.x + 16, right.y + 54))
            y0 = right.y + 80
            # bullets from our requirement model
            bullets = [
                f"Joueurs requis: {ch.requirement.min_count}",
            ]
            if ch.requirement.min_avg_rating:
                bullets.append(f"Note moyenne min: {ch.requirement.min_avg_rating}")
            if ch.requirement.allowed_rarities:
                bullets.append("Raretés: " + ', '.join(ch.requirement.allowed_rarities))
            for b in bullets:
                dot = self.app.h4.render('•', True, (210, 210, 220))
                txt = self.app.h5.render(b, True, (210, 210, 220))
                screen.blit(dot, (right.x + 18, y0))
                screen.blit(txt, (right.x + 36, y0 + 4))
                y0 += 28
            # view rewards label
            vr = self.app.h5.render('VIEW REWARDS', True, (180, 180, 190))
            screen.blit(vr, (right.x + 16, right.bottom - 108))
            # start button
            start_rect = pygame.Rect(right.x + 20, right.bottom - 64, right.w - 40, 44)
            pygame.draw.rect(screen, (40, 140, 240), start_rect, border_radius=10)
            lbl = self.app.h4.render('Commencer', True, (255, 255, 255))
            screen.blit(lbl, (start_rect.centerx - lbl.get_width() // 2, start_rect.centery - lbl.get_height() // 2))
        # back hint
        hint = self.app.h5.render('[Esc] Retour', True, (150, 150, 160))
        screen.blit(hint, (w - hint.get_width() - 32, 32))


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Minefut — Revamp 2025')
        self.settings = app_settings.load_settings()
        flags = pygame.SCALED
        if self.settings.get('fullscreen'):
            flags |= pygame.FULLSCREEN
        self.size = (self.settings.get('width', 1920), self.settings.get('height', 1080))
        # robust display creation with fallbacks (fixes "failed to create renderer" on some setups)
        try:
            self.screen = pygame.display.set_mode(self.size, flags)
        except Exception as e:
            print('[Minefut] set_mode failed with SCALED/fullscreen flags, retrying windowed RESIZABLE…', e)
            try:
                self.screen = pygame.display.set_mode(self.size, pygame.RESIZABLE)
            except Exception as e2:
                print('[Minefut] set_mode RESIZABLE failed, retrying 1280x720 windowed…', e2)
                self.size = (1280, 720)
                self.screen = pygame.display.set_mode(self.size)
        self.clock = pygame.time.Clock()
        # fonts
        self.h1 = pygame.font.SysFont('arial', 72)
        self.h2 = pygame.font.SysFont('arial', 40)
        self.h3 = pygame.font.SysFont('arial', 28)
        self.h4 = pygame.font.SysFont('arial', 22)
        self.h5 = pygame.font.SysFont('arial', 18)
        # event banner (top-right)
        self.event_img_orig: Optional[pygame.Surface] = None
        self.event_img_small: Optional[pygame.Surface] = None
        self.event_modal_open: bool = False
        try:
            root = Path(__file__).resolve().parents[1]
            p = root / 'data' / 'announcement.png'
            if p.exists():
                raw = pygame.image.load(str(p)).convert_alpha()
                self.event_img_orig = raw
                # slightly larger small banner
                self.event_img_small = self._scale_keep_aspect(raw, 320, 160)
        except Exception as e:
            print('[Minefut] Failed to load event image:', e)
        # stack of screens
        self.stack: List[Screen] = [MainMenu(self)]
        self.running = True
        # toast system
        self.toast_message = None
        self.toast_until = 0.0
        # daily reward check (guard to run once)
        self._daily_checked = False

    def push(self, s: Screen):
        self.stack.append(s)

    def pop(self):
        if len(self.stack) > 1:
            self.stack.pop()

    def current(self) -> Screen:
        return self.stack[-1]

    def _scale_keep_aspect(self, surf: pygame.Surface, max_w: int, max_h: int) -> pygame.Surface:
        w, h = surf.get_width(), surf.get_height()
        if w == 0 or h == 0:
            return surf
        r = min(max_w / w, max_h / h)
        nw, nh = max(1, int(w * r)), max(1, int(h * r))
        return pygame.transform.smoothscale(surf, (nw, nh))

    def _get_event_banner_rect(self) -> Optional[pygame.Rect]:
        if self.event_img_small is None:
            return None
        iw, ih = self.event_img_small.get_width(), self.event_img_small.get_height()
        x = self.size[0] - iw - 20
        y = 20
        return pygame.Rect(x, y, iw, ih)

    def _get_season_pass_rect(self) -> Optional[pygame.Rect]:
        # Same size as event banner (fallback to 320x160 if event not available)
        if self.event_img_small is not None:
            iw, ih = self.event_img_small.get_width(), self.event_img_small.get_height()
        else:
            iw, ih = 320, 160
        x = 20
        y = 20
        return pygame.Rect(x, y, iw, ih)

    def _get_event_modal_layout(self):
        # returns (panel_rect, image_surface, image_rect, close_rect)
        if self.event_img_orig is None:
            return None
        max_w = int(self.size[0] * 0.7)
        max_h = int(self.size[1] * 0.7)
        img = self._scale_keep_aspect(self.event_img_orig, max_w, max_h)
        iw, ih = img.get_width(), img.get_height()
        panel = pygame.Rect(0, 0, iw + 40, ih + 40)
        panel.center = (self.size[0] // 2, self.size[1] // 2)
        img_rect = pygame.Rect(0, 0, iw, ih)
        img_rect.center = panel.center
        # close button in panel's top-right corner
        close_rect = pygame.Rect(panel.right - 36, panel.top + 8, 28, 28)
        return panel, img, img_rect, close_rect

    def show_toast(self, message: str, duration: float = 2.0):
        try:
            self.toast_message = str(message)
            self.toast_until = time.time() + max(0.5, float(duration))
        except Exception:
            # fail-safe: set for 2s
            self.toast_message = str(message)
            self.toast_until = time.time() + 2.0

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            # Daily rewards are now manual (via the DailyRewards screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    # event banner interactions (only on MainMenu)
                    handled = False
                    on_main = isinstance(self.current(), MainMenu)
                    if on_main and self.event_img_small is not None:
                        # modal close handlers
                        if self.event_modal_open:
                            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                                self.event_modal_open = False
                                handled = True
                            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                layout = self._get_event_modal_layout()
                                if layout is not None:
                                    panel, _img, _irec, close_rect = layout
                                    mx, my = event.pos
                                    if close_rect.collidepoint((mx, my)):
                                        self.event_modal_open = False
                                        handled = True
                                    elif not panel.collidepoint((mx, my)):
                                        # click outside closes as well
                                        self.event_modal_open = False
                                        handled = True
                        else:
                            # banner open handler
                            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                                br = self._get_event_banner_rect()
                                if br and br.collidepoint(event.pos):
                                    self.event_modal_open = True
                                    handled = True
                    elif not on_main and self.event_modal_open:
                        # ensure modal is closed when leaving main menu
                        self.event_modal_open = False
                    if not handled:
                        self.current().handle(event)
            self.current().update(dt)
            self.current().draw(self.screen)
            # draw event banner overlay (only on MainMenu)
            if isinstance(self.current(), MainMenu) and self.event_img_small is not None:
                br = self._get_event_banner_rect()
                if br is not None:
                    iw, ih = br.w, br.h
                    # background panel
                    panel = pygame.Rect(br.x - 8, br.y - 8, iw + 16, ih + 16)
                    pygame.draw.rect(self.screen, (20, 22, 28), panel, border_radius=12)
                    pygame.draw.rect(self.screen, (70, 72, 90), panel, 2, border_radius=12)
                    # label
                    lbl = self.h4.render('Événement', True, (235, 235, 245))
                    self.screen.blit(lbl, (br.x + iw - lbl.get_width(), br.y - 24))
                    # image
                    self.screen.blit(self.event_img_small, br.topleft)
            # draw modal if open (only on MainMenu)
            if isinstance(self.current(), MainMenu) and self.event_modal_open and self.event_img_orig is not None:
                # dim background
                overlay = pygame.Surface(self.size, pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 140))
                self.screen.blit(overlay, (0, 0))
                layout = self._get_event_modal_layout()
                if layout is not None:
                    panel, img, img_rect, close_rect = layout
                    # panel
                    pygame.draw.rect(self.screen, (22, 24, 30), panel, border_radius=16)
                    pygame.draw.rect(self.screen, (80, 82, 100), panel, 2, border_radius=16)
                    # title
                    ttl = self.h3.render('Événement', True, (235, 235, 245))
                    self.screen.blit(ttl, (panel.x + 16, panel.y + 8))
                    # close button (X)
                    pygame.draw.rect(self.screen, (120, 60, 60), close_rect, border_radius=6)
                    x_txt = self.h4.render('X', True, (255, 255, 255))
                    self.screen.blit(x_txt, (close_rect.centerx - x_txt.get_width() // 2, close_rect.centery - x_txt.get_height() // 2))
                    # image
                    self.screen.blit(img, img_rect.topleft)
            # toast overlay (global)
            if self.toast_message:
                now = time.time()
                if now < self.toast_until:
                    # draw bottom-center toast panel
                    pad_x, pad_y = 16, 10
                    txt = self.h4.render(self.toast_message, True, (255, 255, 255))
                    w = txt.get_width() + pad_x * 2
                    h = txt.get_height() + pad_y * 2
                    rect = pygame.Rect(0, 0, w, h)
                    rect.centerx = self.size[0] // 2
                    rect.bottom = self.size[1] - 24
                    # background with translucency
                    panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    pygame.draw.rect(panel, (20, 20, 26, 220), panel.get_rect(), border_radius=12)
                    # subtle border
                    pygame.draw.rect(panel, (90, 90, 110, 240), panel.get_rect(), 2, border_radius=12)
                    self.screen.blit(panel, rect.topleft)
                    self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
                else:
                    # expire
                    self.toast_message = None
                    self.toast_until = 0.0
            if self.settings.get('show_fps'):
                fps = self.h5.render(f"{self.clock.get_fps():.0f} FPS", True, (200, 200, 210))
                self.screen.blit(fps, (10, 10))
            pygame.display.flip()
        pygame.quit()
        sys.exit(0)


def run_app():
    App().run()


# -------- PNG resolve/draw helpers (local, minimal, rarity-aware) -------- #

AVATAR_CACHE: dict[str, pygame.Surface] = {}
BG_CACHE: dict[str, pygame.Surface] = {}
_ROOT = Path(__file__).resolve().parents[1]
AVATARS_DIR = _ROOT / 'data' / 'avatars'

try:
    with (AVATARS_DIR / 'map.json').open('r', encoding='utf-8') as f:
        AVATAR_MAP = json.load(f)
except Exception:
    AVATAR_MAP = {}

# ensure special mapping for Busquets Fin d'une ère image
try:
    AVATAR_MAP.setdefault('Sergio Busquets', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Fin d'une ère\\Sergio Busquets.png")))
except Exception:
    pass
# ensure special mapping for Jordi Alba Fin d'une ère image (project-relative path)
try:
    AVATAR_MAP.setdefault('Jordi Alba', "cards/Fin d'une ère/Jordi Alba.png")
except Exception:
    pass
# Flashback mappings (absolute paths provided)
try:
    AVATAR_MAP.setdefault('Goretzka', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Flashback\\Goretzka.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Džeko', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Flashback\\Džeko.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Xherdan Shaqiri', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Flashback\\Shaqiri.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Van Buyten', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Hero\\Van Buyten.png")))
except Exception:
    pass
# Defi-only special mappings
try:
    AVATAR_MAP.setdefault("Jérôme Boateng", str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Fin d'une ère\\Jerome Boateng.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Juninho', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Hero\\Juninho.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Lacazette', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Flashback\\Lacazette.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Iniesta', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Icon\\Icon début\\Iniesta.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Payet', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Hero\\Payet.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Emil Forsberg', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Flashback\\Emil Forsberg.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Quaresma', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Hero\\Quaresma.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Ibrahimović', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Icon\\Icon début\\Ibrahimović.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Xabi Alonso', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Icon\\Xabi Alonso.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Ribéry', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Icon\\Ribéry.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Peter Crouch', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Héro\\Crouch.png")))
except Exception:
    pass
try:
    # Use SBC version (CDM) for global Pogba mapping; Season Pass tile uses its own CAM image via card_img
    AVATAR_MAP['Paul Pogba'] = str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Joueur\\Pogba_cdm.png"))
except Exception:
    pass
try:
    # Variant-specific mappings so Collection can show both Pogba versions distinctly
    AVATAR_MAP['Paul Pogba#sbc'] = str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Joueur\\Pogba_cdm.png"))
    AVATAR_MAP['Paul Pogba#pass'] = str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Joueur\\Pogba_cam.png"))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Guéla Doué', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Joueur\\Guéla Doué.png")))
except Exception:
    pass
try:
    AVATAR_MAP.setdefault('Bryan Mbeumo', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Joueur\\Bryan Mbeumo.png")))
except Exception:
    pass
try:
    # Daily Rewards — Squad Fondations
    AVATAR_MAP.setdefault('Teun Koopmeiners', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Squad Fondations\\Koopmeiners.png")))
    AVATAR_MAP.setdefault('Matteo Ruggeri', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Squad Fondations\\Ruggeri.png")))
    # Handle both ascii and diacritics for Stanisic
    AVATAR_MAP.setdefault('Josip Stanisic', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Squad Fondations\\Stanišić.png")))
    AVATAR_MAP.setdefault('Josip Stanišić', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Squad Fondations\\Stanišić.png")))
    AVATAR_MAP.setdefault('Wataru Endo', str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Squad Fondations\\Endo.png")))
except Exception:
    pass


def _strip_accents(s: str) -> str:
    try:
        return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    except Exception:
        return s

def _normalize_text(s: str) -> str:
    try:
        return _strip_accents((s or '').lower())
    except Exception:
        return (s or '').lower()

def _name_variants(base_name: str) -> list[str]:
    base = base_name or ''
    cand = set()
    for b in (base, base.replace('.', ''), base.replace("'", '')):
        for v in (b, _strip_accents(b)):
            v = v.strip()
            if not v:
                continue
            vl = v.lower()
            cand.add(vl)
            cand.add(vl.replace(' ', '_'))
            cand.add(vl.replace(' ', ''))
            cand.add(vl.replace('-', '_'))
            cand.add(vl.replace('-', ''))
    return list(cand)


def _rarity_folder_aliases(rarity: str) -> list[str]:
    rl = (rarity or '').strip().lower()
    if rl in ('or_rare', 'gold rare', 'gold_rare', 'rare'):
        rl = 'or rare'
    if rl in ('or_non_rare', 'gold', 'gold common', 'gold_common', 'commun', 'common'):
        rl = 'or non rare'
    aliases = [rl]
    if rl == 'or rare':
        aliases += ['or_rare', 'or-rare', 'gold rare', 'gold_rare', 'rare']
    elif rl == 'or non rare':
        aliases += ['or_non_rare', 'or-non-rare', 'gold', 'gold common', 'gold_common', 'commun', 'common']
    elif rl == 'hero':
        aliases += ['epic', 'epique', 'épic']
    elif rl == 'icon':
        aliases += ['legend', 'legendary', 'legendaire', 'légendaire']
    elif rl == 'otw':
        aliases += ['ones_to_watch']
    out = []
    for a in aliases:
        for v in (a, a.replace(' ', '_'), a.replace(' ', ''), a.replace('-', '_')):
            vl = v.lower()
            if vl and vl not in out:
                out.append(vl)
    return out


def _find_image_in_rarity_dirs(base_name: str, rarity: str) -> Optional[Path]:
    if not base_name:
        return None
    name_vars = _name_variants(base_name)
    folders = _rarity_folder_aliases(rarity)
    exts = ['.png', '.jpg', '.jpeg']
    for folder in folders:
        for nv in name_vars:
            for ext in exts:
                candidate = AVATARS_DIR / folder / f"{nv}{ext}"
                if candidate.exists():
                    return candidate
    return None


def resolve_player_image_by_name_and_rarity(name: str, rarity: Optional[str]) -> Optional[Path]:
    # Try exact name mapping first (to support variants like "#pass" / "#sbc"), then fallback to base name
    full = (name or '').strip()
    base = full.split('#')[0].strip()
    if AVATAR_MAP:
        val = None
        # exact match (case/diacritics-insensitive)
        if full in AVATAR_MAP:
            val = AVATAR_MAP[full]
        else:
            nf = _normalize_text(full)
            for k, v in AVATAR_MAP.items():
                if _normalize_text(str(k)) == nf:
                    val = v
                    break
        # fallback to base
        if val is None and base:
            if base in AVATAR_MAP:
                val = AVATAR_MAP[base]
            else:
                nb = _normalize_text(base)
                for k, v in AVATAR_MAP.items():
                    if _normalize_text(str(k)) == nb:
                        val = v
                        break
        if val:
            try:
                cand = []
                v = str(val)
                pv = Path(v)
                if pv.is_absolute() and pv.exists():
                    return pv
                cand.append(AVATARS_DIR / v)
                cand.append(_ROOT / v)
                cand.append(_ROOT / 'data' / v)
                for p in cand:
                    if p.exists():
                        return p
            except Exception:
                pass
    # 2) rarity-based directory search
    p = _find_image_in_rarity_dirs(base, rarity or '')
    if p is not None:
        return p
    # 3) root lookup
    for nv in _name_variants(base):
        for ext in ('.png', '.jpg', '.jpeg'):
            p = AVATARS_DIR / f"{nv}{ext}"
            if p.exists():
                return p
    # 4) placeholder if available
    ph = AVATARS_DIR / '_placeholder.png'
    return ph if ph.exists() else None


def draw_player_png_centered(surf: pygame.Surface, img_path: Path, center: tuple[int, int], max_w: int, max_h: int) -> bool:
    key = f"raw::{img_path}::{max_w}x{max_h}"
    scaled = AVATAR_CACHE.get(key)
    if scaled is None:
        try:
            raw = pygame.image.load(str(img_path)).convert_alpha()
            iw, ih = raw.get_size()
            if iw <= 0 or ih <= 0:
                return False
            scale = min(max_w / iw, max_h / ih)
            new_w = max(1, int(iw * scale))
            new_h = max(1, int(ih * scale))
            scaled = pygame.transform.smoothscale(raw, (new_w, new_h))
            AVATAR_CACHE[key] = scaled
        except Exception:
            return False
    cx, cy = center
    surf.blit(scaled, (cx - scaled.get_width() // 2, cy - scaled.get_height() // 2))
    return True


def draw_bg_cover(surf: pygame.Surface, img_path: Path, rect: pygame.Rect) -> bool:
    """Draw a background image covering rect (like CSS background-size: cover)."""
    key = f"bg::{img_path}::{rect.w}x{rect.h}"
    scaled = BG_CACHE.get(key)
    if scaled is None:
        try:
            raw = pygame.image.load(str(img_path)).convert_alpha()
            iw, ih = raw.get_size()
            if iw <= 0 or ih <= 0:
                return False
            scale = max(rect.w / iw, rect.h / ih)
            new_w = max(1, int(iw * scale))
            new_h = max(1, int(ih * scale))
            scaled = pygame.transform.smoothscale(raw, (new_w, new_h))
            BG_CACHE[key] = scaled
        except Exception:
            return False
    # center within rect
    x = rect.x + (rect.w - scaled.get_width()) // 2
    y = rect.y + (rect.h - scaled.get_height()) // 2
    surf.blit(scaled, (x, y))
    return True
