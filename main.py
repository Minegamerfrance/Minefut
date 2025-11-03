import sys
import random
import unicodedata
import unicodedata
import pygame
from game.cards import generate_pack, Card
from game import db as game_db
from game import settings as game_settings
from game import wallet
from pathlib import Path
import os
import json
from typing import Optional
import time

WIDTH, HEIGHT = 1920, 1080
FPS = 60

pygame.init()

# Load settings early to adapt window size to user screen
CURRENT_SETTINGS = game_settings.load_settings()

def _desktop_size(default=(WIDTH, HEIGHT)):
    try:
        ds = pygame.display.get_desktop_sizes()
        if ds and len(ds[0]) == 2:
            return ds[0]
    except Exception:
        pass
    try:
        info = pygame.display.Info()
        w = getattr(info, 'current_w', default[0]) or default[0]
        h = getattr(info, 'current_h', default[1]) or default[1]
        return (w, h)
    except Exception:
        return default

# Compute adaptive WIDTH/HEIGHT (windowed legacy UI)
if CURRENT_SETTINGS.get('fit_screen', True):
    base_w = CURRENT_SETTINGS.get('width', WIDTH)
    base_h = CURRENT_SETTINGS.get('height', HEIGHT)
    desk_w, desk_h = _desktop_size((base_w, base_h))
    margin = 80
    max_w = max(640, desk_w - margin)
    max_h = max(480, desk_h - margin)
    try:
        scale = min(max_w / max(1, base_w), max_h / max(1, base_h), 1.0)
    except Exception:
        scale = 1.0
    WIDTH = max(640, int(base_w * scale))
    HEIGHT = max(480, int(base_h * scale))

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Minefut - Pack Demo")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
large_font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 18)

OPENING = False
cards = []
animation_progress = 0
STATE = 'menu'  # 'menu', 'game', 'collection'
FADE_ALPHA = 0
FADE_SPEED = 600  # alpha per second
ANNOUNCEMENT_OPEN = False
# CURRENT_SETTINGS already loaded above
PACK_ANIM = None  # PackAnimation instance during opening
DRAW_OFFSET = (0, 0)  # global drawing offset (used for camera shake)
SHOP_MSG = ''
SHOP_MSG_T = 0.0

# Announcement image path
ANNOUNCEMENT_PATH = Path(__file__).resolve().parents[0] / 'data' / 'announcement.png'
announcement_img = None
AVATAR_MAP: dict | None = None
AVATARS_DIR = Path(__file__).resolve().parents[0] / 'data' / 'avatars'

def launch_revamp_sbc():
    """Launch the new revamp UI directly into the SBC screen.
    Falls back silently if something goes wrong.
    """
    try:
        from game.app import App, SBC
        print('[Minefut] Launching revamp UI (SBC)…')
        app = App()
        app.push(SBC(app))
        app.run()  # Note: exits process on quit
    except Exception as e:
        print('[Minefut] Failed to launch revamp SBC:', e)

def load_avatar_mapping() -> dict | None:
    try:
        map_path = AVATARS_DIR / 'map.json'
        if map_path.exists():
            with map_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        return None
    return None

def guess_avatar_filename(base_name: str) -> Optional[str]:
    # Try a few filename variants in avatars directory
    if not base_name:
        return None
    base = base_name.strip()
    # sanitize
    base1 = base.replace('.', '').replace("'", '')
    variants = set()
    for b in (base, base1):
        variants.add(b)
        variants.add(b.replace(' ', '_'))
        variants.add(b.replace(' ', ''))
        variants.add(b.lower())
        variants.add(b.lower().replace(' ', '_'))
        variants.add(b.lower().replace(' ', ''))
        variants.add(b.replace('-', '_'))
        variants.add(b.lower().replace('-', '_'))
    exts = ['.png', '.jpg', '.jpeg']
    try:
        for v in variants:
            for ext in exts:
                candidate = AVATARS_DIR / f"{v}{ext}"
                if candidate.exists():
                    return f"data/avatars/{candidate.name}"
    except Exception:
        return None
    return None

def resolve_player_image_by_name(name: str, mapping: Optional[dict]) -> Optional[str]:
    base = name.split('#')[0].strip() if name else ''
    # 1) mapping lookup
    if mapping and base in mapping:
        return f"data/avatars/{mapping[base]}"
    # 2) auto detection
    return guess_avatar_filename(base)

def apply_avatar_mapping_to_db(mapping: Optional[dict]) -> int:
    # Update DB for players without image using mapping or guessed filename
    updated = 0
    try:
        from game import db as _db
        players = _db.load_players()
        changed = False
        for p in players:
            if p.get('image'):
                continue
            img = resolve_player_image_by_name_and_rarity(p.get('name', ''), p.get('rarity', ''), mapping)
            if img:
                p['image'] = img
                updated += 1
                changed = True
        if changed:
            _db.save_players(players)
    except Exception:
        pass
    return updated

if ANNOUNCEMENT_PATH.exists():
    try:
        announcement_img = pygame.image.load(str(ANNOUNCEMENT_PATH)).convert_alpha()
    except Exception:
        announcement_img = None

BUTTON_RECT = pygame.Rect(WIDTH - 300, HEIGHT - 120, 240, 70)
MENU_BUTTONS = []
AVATAR_CACHE = {}
LAST_RELOAD_MSG = ''
LAST_RELOAD_TIME = 0.0

def make_menu_buttons():
    global MENU_BUTTONS
    MENU_BUTTONS = []
    btn_w, btn_h = 360, 72
    start_x = WIDTH//2 - btn_w//2
    start_y = HEIGHT//3
    labels = [
        ('Ouvrir pack', 'game'),
        ('Collection', 'collection'),
        ('SBC', 'sbc'),
        ('Boutique', 'shop'),
        ('Paramètres', 'settings'),
        ('Quitter', 'quit'),
    ]
    for i, (label, action) in enumerate(labels):
        rect = pygame.Rect(start_x, start_y + i * (btn_h + 16), btn_w, btn_h)
        MENU_BUTTONS.append((rect, label, action))


def get_announcement_rect():
    """Return panel rect (left/top) computed from current WIDTH/HEIGHT."""
    panel_w = min(720, int(WIDTH * 0.375))
    panel_h = min(420, int(HEIGHT * 0.39))
    panel_x = 40
    # place below title to avoid overlap
    panel_y = max(40, 80 + large_font.get_height() + 12)
    return pygame.Rect(panel_x, panel_y, panel_w, panel_h)


def scale_preserve_aspect(img, max_w, max_h):
    iw, ih = img.get_size()
    if iw == 0 or ih == 0:
        return img
    scale = min(max_w / iw, max_h / ih)
    new_w = max(1, int(iw * scale))
    new_h = max(1, int(ih * scale))
    return pygame.transform.smoothscale(img, (new_w, new_h))


def _strip_accents(s: str) -> str:
    try:
        return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    except Exception:
        return s


def normalize_rarity(r: str) -> str:
    """Map various rarity labels to canonical set: 'or rare', 'or non rare', 'icon', 'hero', 'otw'."""
    if not r:
        return 'or non rare'
    rl = _strip_accents(str(r)).strip().lower()
    # direct canonical
    if rl in ('or rare', 'or_rare', 'gold rare', 'gold_rare', 'rare gold', 'rare_gold'):
        return 'or rare'
    if rl in ('or non rare', 'or_non_rare', 'gold', 'gold common', 'gold_common', 'or commun', 'commun', 'common', 'common_gold'):
        return 'or non rare'
    if rl in ('icon', 'icons', 'legend', 'legendary', 'legendaire', 'legendaire', 'légendaire'):
        return 'icon'
    if rl in ('hero', 'heros', 'epic', 'epique', 'épic'):
        return 'hero'
    if rl in ('otw', 'ones_to_watch'):
        return 'otw'
    # legacy fallbacks
    if rl == 'rare':
        return 'or rare'
    if rl == 'common':
        return 'or non rare'
    return rl


def display_rarity(r: str) -> str:
    return normalize_rarity(r)


def _strip_accents(s: str) -> str:
    try:
        return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    except Exception:
        return s


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
    rl = normalize_rarity(rarity)
    aliases = [rl]
    if rl == 'or rare':
        aliases += ['or_rare', 'or-rare', 'gold rare', 'gold_rare', 'rare gold', 'rare_gold', 'rare', 'gold']
    elif rl == 'or non rare':
        aliases += ['or_non_rare', 'or-non-rare', 'gold common', 'gold_common', 'or commun', 'commun', 'common', 'gold']
    elif rl == 'hero':
        aliases += ['epic', 'epique', 'épic']
    elif rl == 'icon':
        aliases += ['legend', 'legendary', 'legendaire', 'légendaire']
    elif rl == 'otw':
        aliases += ['ones_to_watch']
    # normalize alias variations
    out = []
    for a in aliases:
        for v in (a, a.replace(' ', '_'), a.replace(' ', ''), a.replace('-', '_')):
            vl = v.lower()
            if vl not in out:
                out.append(vl)
    return out


def _find_image_in_rarity_dirs(base_name: str, rarity: str) -> Optional[str]:
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
                    return f"data/avatars/{folder}/{candidate.name}"
    return None


def resolve_card_image_path(card: Card) -> Optional[Path]:
    """Return absolute Path to the player's image for this card if available."""
    # prefer avatar_path from the card
    rel = getattr(card, 'avatar_path', None)
    if rel:
        p = Path(__file__).resolve().parents[0] / rel
        if p.exists():
            return p
    # fallback: try resolve by name using mapping
    # include rarity-aware lookup in subfolders (e.g., "or rare/mbappé.png")
    img_rel = resolve_player_image_by_name_and_rarity(getattr(card, 'name', ''), getattr(card, 'rarity', ''), AVATAR_MAP)
    if img_rel:
        p = Path(__file__).resolve().parents[0] / img_rel
        if p.exists():
            return p
    return None


def resolve_player_image_by_name_and_rarity(name: str, rarity: Optional[str], mapping: Optional[dict]) -> Optional[str]:
    base = name.split('#')[0].strip() if name else ''
    root = Path(__file__).resolve().parents[0]
    avatars_dir = root / 'data' / 'avatars'
    # 1) mapping lookup (robust: exact, then accent-insensitive; support absolute and project-relative values)
    if mapping:
        val = None
        if base in mapping:
            val = mapping[base]
        else:
            nb = _strip_accents(base).lower()
            for k, v in mapping.items():
                try:
                    if _strip_accents(str(k)).lower() == nb:
                        val = v
                        break
                except Exception:
                    continue
        # surname lookup if not found
        if val is None and ' ' in base:
            last = base.split()[-1]
            if last in mapping:
                val = mapping[last]
            else:
                nl = _strip_accents(last).lower()
                for k, v in mapping.items():
                    try:
                        if _strip_accents(str(k)).lower() == nl:
                            val = v
                            break
                    except Exception:
                        continue
        if val:
            v = str(val)
            pv = Path(v)
            # absolute path
            if pv.is_absolute() and pv.exists():
                # return project-relative if inside project
                try:
                    rel = pv.relative_to(root)
                    return str(rel).replace('\\', '/')
                except Exception:
                    return str(pv)
            # try avatars/<v>, project-root/<v>, data/<v>
            candidates = [avatars_dir / v, root / v, root / 'data' / v]
            for p in candidates:
                if p.exists():
                    try:
                        rel = p.relative_to(root)
                        return str(rel).replace('\\', '/')
                    except Exception:
                        return str(p).replace('\\', '/')
    # 2) rarity-based directory search
    rel = _find_image_in_rarity_dirs(base, rarity or '')
    if rel:
        return rel
    # 3) filename auto-detection in root avatars
    rel = guess_avatar_filename(base)
    if rel:
        return rel
    # 4) fuzzy search inside project cards/ assets
    try:
        root_cards = root / 'cards'
        if root_cards.exists():
            def _norm_key(s: str) -> str:
                import unicodedata as _u
                try:
                    s2 = ''.join(c for c in _u.normalize('NFKD', s) if not _u.combining(c))
                except Exception:
                    s2 = s
                s2 = s2.lower()
                for ch in [' ', '_', '-', "'", '.', '’']:
                    s2 = s2.replace(ch, '')
                return s2
            target = _norm_key(base)
            exts = {'.png', '.jpg', '.jpeg'}
            best = None
            for r, _dirs, files in os.walk(root_cards):
                for fn in files:
                    p = Path(r) / fn
                    if p.suffix.lower() not in exts:
                        continue
                    if _norm_key(p.stem) == target:
                        # return project-relative path
                        try:
                            relp = p.relative_to(root)
                            return str(relp).replace('\\', '/')
                        except Exception:
                            best = p
                            break
            if best and best.exists():
                return str(best).replace('\\', '/')
    except Exception:
        pass
    # 5) no match
    return None


def draw_player_png_centered(surf: pygame.Surface, img_path: Path, center: tuple[int, int], max_w: int, max_h: int):
    """Draw the raw PNG centered at position, scaled to fit max_w x max_h, preserving aspect.
    Uses cache for scaled surfaces.
    """
    key = f"raw::{img_path}::{max_w}x{max_h}"
    scaled = AVATAR_CACHE.get(key)
    if scaled is None:
        try:
            raw = pygame.image.load(str(img_path)).convert_alpha()
            scaled = scale_preserve_aspect(raw, max_w, max_h)
            AVATAR_CACHE[key] = scaled
        except Exception:
            return False
    cx, cy = center
    surf.blit(scaled, (cx - scaled.get_width()//2, cy - scaled.get_height()//2))
    return True


def get_rarity_color(rarity: str) -> tuple[int, int, int]:
    # Colors for rarity accents (banner/borders), using canonical labels
    rr = normalize_rarity(rarity)
    mapping = {
        'icon': (245, 245, 235),         # ivory/white-gold
        'hero': (180, 60, 140),          # magenta/purple
        'or rare': (212, 175, 55),       # gold
        'or non rare': (194, 178, 128),  # dull gold/bronze
        'otw': (255, 140, 0),            # orange
    }
    return mapping.get(rr, (180, 180, 180))


def get_effects_quality() -> str:
    q = CURRENT_SETTINGS.get('effects_quality', 'medium')
    return q if q in ('low', 'medium', 'high') else 'medium'


def get_quality_factor() -> float:
    q = get_effects_quality()
    return 0.6 if q == 'low' else 1.5 if q == 'high' else 1.0


def get_beams_count() -> int:
    q = get_effects_quality()
    return 4 if q == 'low' else 10 if q == 'high' else 6


def circle_crop_image(image_surf: pygame.Surface, size: int) -> pygame.Surface:
    """Return a new surface of (size,size) with the image cropped to a circle."""
    # scale image to fit square
    scaled = pygame.transform.smoothscale(image_surf, (size, size))
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2)
    result = scaled.copy()
    # multiply alpha by circular mask
    result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return result


class LightParticle:
    def __init__(self):
        import random as _r
        self.x = _r.uniform(WIDTH * 0.2, WIDTH * 0.8)
        self.y = HEIGHT + _r.uniform(0, HEIGHT * 0.4)
        self.vy = -_r.uniform(200, 480)
        self.size = _r.uniform(2, 5)
        self.alpha = _r.uniform(140, 220)
        self.color = (255, 255, _r.randint(120, 220))

    def update(self, dt: float):
        self.y += self.vy * dt
        self.alpha = max(0, self.alpha - 90 * dt)

    def draw(self, surf: pygame.Surface):
        if self.alpha <= 0:
            return
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (self.color[0], self.color[1], self.color[2], int(self.alpha)), (int(self.size), int(self.size)), int(self.size))
        surf.blit(s, (self.x, self.y), special_flags=pygame.BLEND_PREMULTIPLIED)


class PackAnimation:
    """FIFA20-like cinematic pack opening with lights, doors, and walkout."""
    def __init__(self, cards_list: list[Card]):
        self.cards = cards_list
        self.elapsed = 0.0
        self.finished = False
        self.stage = 'intro'  # intro -> tunnel -> doors -> walkout/reveal -> fanout -> done
        self.particles: list[LightParticle] = []
        self.flash_alpha = 0
        self.door_progress = 0.0  # 0 closed, 1 open
        self.last_door_progress = 0.0
        self.impact_flash = 0  # flash on doors open
        self.shake_time = 0.0
        self.shake_amp = 0.0
        self.revealed = False
        self.fanout_progress = 0.0
        # pick top card for potential walkout
        self.top_card = max(self.cards, key=lambda c: getattr(c, 'rating', 0)) if self.cards else None
        self.walkout = False
        if self.top_card:
            r = getattr(self.top_card, 'rating', 0)
            rarity = getattr(self.top_card, 'rarity', 'or non rare')
            rr = normalize_rarity(rarity)
            self.walkout = (r >= 86) or (rr in ('icon', 'otw'))
        # precompute positions
        spread = 200
        total_width = (len(self.cards)-1) * spread
        start_x = WIDTH//2 - total_width//2
        target_y = HEIGHT//2 + 120
        for i, c in enumerate(self.cards):
            c.x = WIDTH//2
            c.y = HEIGHT + 400
            c.target_y = target_y
            c.offset_x = 0
            c.fx = start_x + i * spread
        # rarity palette for effects
        top_rarity = getattr(self.top_card, 'rarity', 'Common') if self.top_card else 'Common'
        self.palette = get_rarity_color(top_rarity)
        self.confetti = []
        self._confetti_spawned = False
        # quality settings
        self.q_factor = get_quality_factor()
        self.beams = get_beams_count()
        self.particle_rate = min(0.45, 0.18 * self.q_factor)

    def skip(self):
        # jump to end
        self.stage = 'done'
        self.finished = True

    def update(self, dt: float):
        if self.finished:
            return
        self.elapsed += dt
        # spawn particles during intro/tunnel/doors
        if self.stage in ('intro', 'tunnel', 'doors'):
            from random import random
            if random() < self.particle_rate:
                self.particles.append(LightParticle())
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alpha > 1 and p.y > -40]

        if self.stage == 'intro':
            # quick flash-in
            self.flash_alpha = max(0, 220 - int(self.elapsed * 400))
            if self.elapsed > 0.6:
                self.stage = 'tunnel'
                self.elapsed = 0.0
        elif self.stage == 'tunnel':
            if self.elapsed > 1.2:
                self.stage = 'doors'
                self.elapsed = 0.0
        elif self.stage == 'doors':
            self.door_progress = min(1.0, self.elapsed / 1.2)
            # detect open transition for impact flash + shake
            if self.door_progress >= 1.0 and self.last_door_progress < 1.0:
                rarity = getattr(self.top_card, 'rarity', 'or non rare') if self.top_card else 'or non rare'
                rr = normalize_rarity(rarity)
                if rr == 'icon':
                    self.impact_flash = 200
                    self.shake_time, self.shake_amp = 0.6, 16
                elif rr == 'otw':
                    self.impact_flash = 170
                    self.shake_time, self.shake_amp = 0.55, 14
                elif rr == 'hero':
                    self.impact_flash = 150
                    self.shake_time, self.shake_amp = 0.5, 12
                elif rr == 'or rare':
                    self.impact_flash = 120
                    self.shake_time, self.shake_amp = 0.45, 9
                else:
                    self.impact_flash = 90
                    self.shake_time, self.shake_amp = 0.4, 6
            if self.door_progress >= 1.0:
                self.stage = 'walkout' if self.walkout else 'reveal'
                self.elapsed = 0.0
            self.last_door_progress = self.door_progress
        elif self.stage == 'walkout':
            if self.elapsed > 1.3:
                self.stage = 'reveal'
                self.elapsed = 0.0
        elif self.stage == 'reveal':
            self.reveal_t = min(1.0, self.elapsed / 1.0)
            # spawn confetti once on reveal depending on rarity
            if not self._confetti_spawned:
                self.spawn_confetti_for_rarity()
                self._confetti_spawned = True
            if self.elapsed > 1.0:
                self.stage = 'fanout'
                self.elapsed = 0.0
        elif self.stage == 'fanout':
            self.fanout_progress = min(1.0, self.elapsed / 1.2)
            for i, c in enumerate(self.cards):
                t = self.fanout_progress
                c.x = WIDTH//2 + int((c.fx - WIDTH//2) * (1 - (1 - t)**3))
                c.y = int((HEIGHT//2 + 40) + (c.target_y - (HEIGHT//2 + 40)) * (1 - (1 - t)**3))
            if self.fanout_progress >= 1.0:
                self.stage = 'done'
        elif self.stage == 'done':
            self.finished = True
        # update confetti
        for c in self.confetti:
            c.update(dt)
        self.confetti = [c for c in self.confetti if c.alpha > 5 and c.y < HEIGHT + 60]
        # decay impact flash and shake
        if self.impact_flash > 0:
            self.impact_flash = max(0, self.impact_flash - int(300 * dt))
        if self.shake_time > 0:
            self.shake_time = max(0.0, self.shake_time - dt)

    def spawn_confetti_for_rarity(self):
        rarity = getattr(self.top_card, 'rarity', 'or non rare') if self.top_card else 'or non rare'
        rr = normalize_rarity(rarity)
        base = 40
        if rr == 'icon':
            count = 180
        elif rr == 'hero':
            count = 120
        elif rr == 'otw':
            count = 140
        elif rr == 'or rare':
            count = 80
        else:
            count = base
        count = max(10, int(count * self.q_factor))
        for _ in range(count):
            self.confetti.append(Confetti(self.palette))

    def draw_background(self, surf: pygame.Surface):
        # gradient background
        grad = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            a = int(40 + 60 * (y / HEIGHT))
            color = (10, 10, 20 + a//2)
            pygame.draw.line(grad, color, (0, y), (WIDTH, y))
        surf.blit(grad, (0, 0))
        # moving light beams in tunnel stage
        if self.stage in ('tunnel', 'doors'):
            t = pygame.time.get_ticks() / 1000.0
            for i in range(self.beams):
                phase = (t * 0.8 + i * 0.3) % 1.0
                x = int(WIDTH * (0.1 + 0.8 * phase))
                beam = pygame.Surface((16, HEIGHT), pygame.SRCALPHA)
                beam_col = (*self.palette, 50)
                pygame.draw.rect(beam, beam_col, (0, 0, 16, HEIGHT))
                surf.blit(beam, (x, 0))
        # particles
        for p in self.particles:
            p.draw(surf)
        # doors (two dark panels opening)
        if self.stage in ('doors', 'walkout', 'reveal', 'fanout', 'done'):
            prog = self.door_progress
            door_w = int(WIDTH * 0.28)
            gap = int((WIDTH * 0.1) * prog)
            left_rect = pygame.Rect(WIDTH//2 - gap - door_w, HEIGHT//2 - 220, door_w, 440)
            right_rect = pygame.Rect(WIDTH//2 + gap, HEIGHT//2 - 220, door_w, 440)
            pygame.draw.rect(surf, (15, 15, 18), left_rect, border_radius=8)
            pygame.draw.rect(surf, (15, 15, 18), right_rect, border_radius=8)
            # door rim glow
            glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            rim_col = (*self.palette, 64)
            pygame.draw.rect(glow, rim_col, (WIDTH//2 - gap - 8, HEIGHT//2 - 220, 8, 440))
            pygame.draw.rect(glow, rim_col, (WIDTH//2 + gap, HEIGHT//2 - 220, 8, 440))
            surf.blit(glow, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)

        # radial center glow tinted by rarity during reveal/fanout
        if self.stage in ('walkout', 'reveal', 'fanout') and self.top_card:
            cx, cy = WIDTH//2, HEIGHT//2 + 40
            for r in range(240, 20, -40):
                g = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                alpha = int(18 * (r / 240))
                pygame.draw.circle(g, (*self.palette, alpha), (r, r), r)
                surf.blit(g, (cx - r, cy - r), special_flags=pygame.BLEND_PREMULTIPLIED)

        # intro white flash fade
        if self.stage == 'intro' and self.flash_alpha > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, int(self.flash_alpha)))
            surf.blit(overlay, (0, 0))
        # impact flash tinted by rarity
        if self.impact_flash > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((*self.palette, int(self.impact_flash)))
            surf.blit(overlay, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)

    def draw(self, surf: pygame.Surface):
        # compute camera shake offset
        dx = dy = 0
        if self.shake_time > 0:
            import math, time as _time
            t = _time.time()
            k = max(0.0, min(1.0, self.shake_time / 0.6))
            amp = self.shake_amp * k
            dx = int(math.sin(t * 40.0) * amp)
            dy = int(math.cos(t * 42.0) * amp)
        # draw background onto temp surface, then blit with offset
        bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.draw_background(bg)
        surf.blit(bg, (dx, dy))
        # Walkout silhouette
        if self.stage == 'walkout' and self.top_card:
            t = min(1.0, self.elapsed / 1.0)
            center = (WIDTH//2, HEIGHT//2 + 40)
            radius = int(40 + 80 * t)
            pygame.draw.circle(surf, (240, 240, 255), (center[0] + dx, center[1] + dy), radius, 2)
            s = pygame.Surface((180, 260), pygame.SRCALPHA)
            pygame.draw.rect(s, (230, 230, 255, int(40 + 100 * (1 - t))), (0, 0, 180, 260), border_radius=12)
            surf.blit(s, (WIDTH//2 - 90 + dx, HEIGHT//2 - 130 + dy))
        # Reveal top card big
        if self.stage in ('reveal',) and self.top_card:
            t = getattr(self, 'reveal_t', 0.0)
            scale = 0.75 + 0.35 * (1 - (1 - t)**3)
            # try to draw raw PNG directly
            img_path = resolve_card_image_path(self.top_card)
            if img_path is not None:
                base_w, base_h = 300, 420
                max_w, max_h = int(base_w * scale), int(base_h * scale)
                center = (WIDTH//2 + dx, HEIGHT//2 + dy)
                ok = draw_player_png_centered(surf, img_path, center, max_w, max_h)
                if not ok:
                    # fallback to UI card
                    tmp_w, tmp_h = 260, 360
                    card_surf = pygame.Surface((tmp_w, tmp_h), pygame.SRCALPHA)
                    saved_x, saved_y = self.top_card.x, self.top_card.y
                    self.top_card.x, self.top_card.y = 0, 0
                    draw_card_scaled(self.top_card, card_surf, (tmp_w, tmp_h))
                    self.top_card.x, self.top_card.y = saved_x, saved_y
                    scaled_surf = pygame.transform.smoothscale(card_surf, (int(tmp_w*scale), int(tmp_h*scale)))
                    surf.blit(scaled_surf, (WIDTH//2 - scaled_surf.get_width()//2 + dx, HEIGHT//2 - scaled_surf.get_height()//2 + dy))
            else:
                # fallback if no image path found
                tmp_w, tmp_h = 260, 360
                card_surf = pygame.Surface((tmp_w, tmp_h), pygame.SRCALPHA)
                saved_x, saved_y = self.top_card.x, self.top_card.y
                self.top_card.x, self.top_card.y = 0, 0
                draw_card_scaled(self.top_card, card_surf, (tmp_w, tmp_h))
                self.top_card.x, self.top_card.y = saved_x, saved_y
                scaled_surf = pygame.transform.smoothscale(card_surf, (int(tmp_w*scale), int(tmp_h*scale)))
                surf.blit(scaled_surf, (WIDTH//2 - scaled_surf.get_width()//2 + dx, HEIGHT//2 - scaled_surf.get_height()//2 + dy))
        # Fanout: draw all cards in their positions
        if self.stage in ('fanout', 'done'):
            # draw each pulled player's PNG directly; fallback to card UI if not available
            item_w, item_h = 160, 220
            for c in self.cards:
                img_path = resolve_card_image_path(c)
                cx = int(c.x + item_w//2 + dx)
                cy = int(c.y + item_h//2 + dy)
                if img_path is not None:
                    ok = draw_player_png_centered(surf, img_path, (cx, cy), item_w, item_h)
                    if not ok:
                        # fallback
                        global DRAW_OFFSET
                        prev_off = DRAW_OFFSET
                        DRAW_OFFSET = (dx, dy)
                        draw_card(c)
                        DRAW_OFFSET = prev_off
                else:
                    prev_off = DRAW_OFFSET
                    DRAW_OFFSET = (dx, dy)
                    draw_card(c)
                    DRAW_OFFSET = prev_off
        # draw confetti on a temp surface then blit with offset
        conf_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for cf in self.confetti:
            cf.draw(conf_layer)
        surf.blit(conf_layer, (dx, dy), special_flags=pygame.BLEND_PREMULTIPLIED)
        hint = small_font.render('[Echap] pour passer', True, (200, 200, 200))
        surf.blit(hint, (20, HEIGHT - 40))


class Confetti:
    def __init__(self, base_color: tuple[int, int, int]):
        import random as _r
        self.x = _r.uniform(WIDTH * 0.2, WIDTH * 0.8)
        self.y = HEIGHT//2 - 60
        self.vx = _r.uniform(-120, 120)
        self.vy = _r.uniform(-50, -200)
        self.size = _r.uniform(4, 8)
        # color variations around base
        jitter = lambda v: max(0, min(255, int(v + _r.uniform(-40, 40))))
        self.color = (jitter(base_color[0]), jitter(base_color[1]), jitter(base_color[2]))
        self.alpha = 200
        self.spin = _r.uniform(-360, 360)
        self.angle = _r.uniform(0, 360)

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 300 * dt  # gravity
        self.angle += self.spin * dt
        self.alpha = max(0, self.alpha - 60 * dt)

    def draw(self, surf: pygame.Surface):
        s = pygame.Surface((self.size, self.size*2), pygame.SRCALPHA)
        s.fill((*self.color, int(self.alpha)))
        rs = pygame.transform.rotate(s, self.angle)
        surf.blit(rs, (self.x, self.y), special_flags=pygame.BLEND_PREMULTIPLIED)


def draw_card_scaled(card: Card, target_surf: pygame.Surface, size: tuple[int, int]):
    """Draw a card into target_surf with given size (w,h) at top-left."""
    w, h = size
    pygame.draw.rect(target_surf, card.bg_color, (0, 0, w, h), border_radius=16)
    pygame.draw.rect(target_surf, (0, 0, 0), (0, 0, w, h), 2, border_radius=16)
    rarity_color = get_rarity_color(card.rarity)
    pygame.draw.rect(target_surf, rarity_color, (0, 0, w, 32), border_radius=16)
    rarity_txt = small_font.render(card.rarity, True, (255, 255, 255))
    target_surf.blit(rarity_txt, (10, 6))
    avatar_rect = pygame.Rect(w//2 - 56, 44, 112, 112)
    surf = None
    if getattr(card, 'avatar_path', None):
        img_path = Path(__file__).resolve().parents[0] / card.avatar_path
        if img_path.exists():
            key = f"scaled::{img_path}::{avatar_rect.w}x{avatar_rect.h}"
            surf = AVATAR_CACHE.get(key)
            if surf is None:
                try:
                    raw = pygame.image.load(str(img_path)).convert_alpha()
                    surf = scale_preserve_aspect(raw, avatar_rect.w, avatar_rect.h)
                    AVATAR_CACHE[key] = surf
                except Exception:
                    surf = None
    if surf is not None:
        circ = circle_crop_image(surf, min(avatar_rect.w, avatar_rect.h))
        target_surf.blit(circ, avatar_rect.topleft)
        pygame.draw.circle(target_surf, (255, 255, 255), (avatar_rect.x + avatar_rect.w//2, avatar_rect.y + avatar_rect.h//2), avatar_rect.w//2 + 2, 0)
        pygame.draw.circle(target_surf, rarity_color, (avatar_rect.x + avatar_rect.w//2, avatar_rect.y + avatar_rect.h//2), avatar_rect.w//2 + 2, 3)
    name_surf = font.render(card.name, True, (10, 10, 10))
    rating_surf = small_font.render(f"Rating: {getattr(card, 'rating', '??')}", True, (10, 10, 10))
    target_surf.blit(name_surf, (12, avatar_rect.bottom + 16))
    target_surf.blit(rating_surf, (12, avatar_rect.bottom + 42))


def draw_button_state(rect, label, hovered: bool, pressed: bool):
    # scale when hovered
    scale = 1.06 if hovered else 1.0
    w, h = rect.w, rect.h
    sw, sh = int(w * scale), int(h * scale)
    sx = rect.x - (sw - w) // 2
    sy = rect.y - (sh - h) // 2
    r = pygame.Rect(sx, sy, sw, sh)
    if pressed:
        color = (20, 110, 200)
    elif hovered:
        color = (50, 170, 255)
    else:
        color = (30, 144, 255)
    pygame.draw.rect(screen, color, r, border_radius=10)
    txt = large_font.render(label, True, (255, 255, 255))
    screen.blit(txt, (r.x + r.w//2 - txt.get_width()//2, r.y + r.h//2 - txt.get_height()//2))



def draw_button():
    pygame.draw.rect(screen, (30, 144, 255), BUTTON_RECT, border_radius=8)
    txt = large_font.render("Ouvrir pack", True, (255, 255, 255))
    screen.blit(txt, (BUTTON_RECT.x + 12, BUTTON_RECT.y + 8))


def draw_wallet_chip():
    bal = wallet.get_balance()
    txt = large_font.render(f"{bal} Minecoins", True, (235, 235, 245))
    pad_x, pad_y = 14, 8
    box = pygame.Rect(0, 0, txt.get_width() + pad_x * 2, txt.get_height() + pad_y)
    box.topright = (WIDTH - 20, 20)
    pygame.draw.rect(screen, (28, 30, 38), box, border_radius=10)
    pygame.draw.rect(screen, (70, 72, 90), box, 2, border_radius=10)
    screen.blit(txt, (box.x + pad_x, box.y + (box.h - txt.get_height()) // 2))


def get_continue_button_rect() -> pygame.Rect:
    w, h = 260, 64
    return pygame.Rect(WIDTH//2 - w//2, HEIGHT - 140, w, h)


def reload_avatar_mapping(clear_cache: bool = True) -> int:
    """Load avatar map and update DB for players without image. Optionally clear image cache."""
    global AVATAR_MAP, LAST_RELOAD_MSG, LAST_RELOAD_TIME
    AVATAR_MAP = load_avatar_mapping() or {}
    if clear_cache:
        AVATAR_CACHE.clear()
    count = apply_avatar_mapping_to_db(AVATAR_MAP)
    LAST_RELOAD_MSG = f"Images mises à jour: {count}"
    LAST_RELOAD_TIME = time.time()
    return count


def start_opening():
    global OPENING, cards, animation_progress, PACK_ANIM
    if OPENING:
        return
    cards = generate_pack(5)
    animation_progress = 0
    OPENING = True
    # save opened cards to collection
    for c in cards:
        try:
            image = getattr(c, 'avatar_path', None)
            game_db.add_player(c.name, c.rating, c.rarity, image=image)
        except Exception:
            pass
    # create cinematic animation controller
    PACK_ANIM = PackAnimation(cards)


def update_animation(dt):
    global OPENING, PACK_ANIM
    if not OPENING:
        return
    if PACK_ANIM is not None:
        PACK_ANIM.update(dt)
        if PACK_ANIM.finished:
            OPENING = False


def draw_card(card: Card):
    # card size for landscape
    w, h = 160, 220
    x = int(card.x + card.offset_x)
    y = int(card.y)
    rect = pygame.Rect(x, y, w, h)

    # shadow
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 60), shadow.get_rect(), border_radius=10)
    ox, oy = DRAW_OFFSET
    screen.blit(shadow, (x + 4 + ox, y + 6 + oy))

    # card background
    card_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, card.bg_color, card_surf.get_rect(), border_radius=10)
    pygame.draw.rect(card_surf, (0, 0, 0), card_surf.get_rect(), 2, border_radius=10)

    rarity_color = get_rarity_color(card.rarity)

    # avatar/card image: prefer full card art if image seems portrait; otherwise circular avatar with rarity ring
    avatar_rect = pygame.Rect(w//2 - 38, 36, 76, 76)
    drew_full_card_image = False
    if getattr(card, 'avatar_path', None):
        img_path = Path(__file__).resolve().parents[0] / card.avatar_path
        raw = None
        if img_path.exists():
            try:
                raw = pygame.image.load(str(img_path)).convert_alpha()
            except Exception:
                raw = None
        if raw is None:
            ph_path = Path(__file__).resolve().parents[0] / 'data' / 'avatars' / '_placeholder.png'
            if ph_path.exists():
                try:
                    raw = pygame.image.load(str(ph_path)).convert_alpha()
                except Exception:
                    raw = None
        if raw is not None:
            iw, ih = raw.get_size()
            is_card_img = ih / max(1, iw) >= 1.2
            if is_card_img:
                inner = pygame.Rect(4, 4, w - 8, h - 8)
                scaled = scale_preserve_aspect(raw, inner.w, inner.h)
                pygame.draw.rect(card_surf, rarity_color, card_surf.get_rect(), 3, border_radius=10)
                card_surf.blit(scaled, (inner.x + (inner.w - scaled.get_width()) // 2, inner.y + (inner.h - scaled.get_height()) // 2))
                drew_full_card_image = True
            else:
                surf = scale_preserve_aspect(raw, avatar_rect.w, avatar_rect.h)
                circle_img = circle_crop_image(surf, min(avatar_rect.w, avatar_rect.h))
                card_surf.blit(circle_img, avatar_rect.topleft)
                pygame.draw.circle(card_surf, (255, 255, 255), (avatar_rect.x + avatar_rect.w//2, avatar_rect.y + avatar_rect.h//2), avatar_rect.w//2 + 2, 0)
                pygame.draw.circle(card_surf, rarity_color, (avatar_rect.x + avatar_rect.w//2, avatar_rect.y + avatar_rect.h//2), avatar_rect.w//2 + 2, 3)
        else:
            # fallback circle
            fallback = pygame.Surface((76, 76), pygame.SRCALPHA)
            pygame.draw.circle(fallback, (240, 240, 240), (38, 38), 38)
            pygame.draw.circle(fallback, (200, 200, 200), (38, 38), 36)
            card_surf.blit(fallback, avatar_rect.topleft)
    else:
        # legacy: no avatar path provided
        fallback = pygame.Surface((76, 76), pygame.SRCALPHA)
        pygame.draw.circle(fallback, (240, 240, 240), (38, 38), 38)
        pygame.draw.circle(fallback, (200, 200, 200), (38, 38), 36)
        card_surf.blit(fallback, avatar_rect.topleft)

    # rarity banner (only if we didn't fill with a full card image)
    if not drew_full_card_image:
        pygame.draw.rect(card_surf, rarity_color, (0, 0, w, 28), border_radius=10)
    rarity_txt = small_font.render(display_rarity(card.rarity), True, (255, 255, 255))
    card_surf.blit(rarity_txt, (8, 4))

    # name and rating
    name_surf = font.render(card.name, True, (10, 10, 10))
    rating_surf = small_font.render(f"Rating: {getattr(card, 'rating', '??')}", True, (10, 10, 10))
    card_surf.blit(name_surf, (8, 108))
    card_surf.blit(rating_surf, (8, 132))

    screen.blit(card_surf, (rect.x + ox, rect.y + oy))


def main():
    global OPENING, FADE_ALPHA, ANNOUNCEMENT_OPEN
    # one-time migration/update
    reload_avatar_mapping(clear_cache=False)
    make_menu_buttons()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # behavior depends on state
                    if ANNOUNCEMENT_OPEN:
                        ANNOUNCEMENT_OPEN = False
                        continue
                    if STATE in ('collection', 'shop', 'settings'):
                        change_state('menu')
                        continue
                    if STATE == 'game':
                        # skip current pack animation if running
                        if 'PACK_ANIM' in globals() and PACK_ANIM is not None and not getattr(PACK_ANIM, 'finished', True):
                            PACK_ANIM.skip()
                            continue
                        else:
                            change_state('menu')
                            continue
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # if announcement modal is open, check close button first
                if ANNOUNCEMENT_OPEN:
                    box_w = int(WIDTH * 0.75)
                    box_h = int(HEIGHT * 0.75)
                    box_x = WIDTH//2 - box_w//2
                    box_y = HEIGHT//2 - box_h//2
                    close_rect = pygame.Rect(box_x + box_w - 48, box_y + 12, 36, 36)
                    if close_rect.collidepoint(event.pos):
                        ANNOUNCEMENT_OPEN = False
                        continue
                # menu handling
                if STATE == 'menu':
                    clicked_menu = False
                    for rect, label, action in MENU_BUTTONS:
                        if rect.collidepoint(event.pos):
                            clicked_menu = True
                            if action == 'game':
                                start_opening()
                                change_state('game')
                            elif action == 'collection':
                                change_state('collection')
                            elif action == 'sbc':
                                # Launch the revamp SBC screen directly
                                launch_revamp_sbc()
                                running = False
                            elif action == 'shop':
                                change_state('shop')
                            elif action == 'settings':
                                change_state('settings')
                            elif action == 'quit':
                                running = False
                    # if not clicking a menu button, check announcement panel click
                    if not clicked_menu:
                        ann_rect = get_announcement_rect()
                        if ann_rect.collidepoint(event.pos):
                            ANNOUNCEMENT_OPEN = True
                elif STATE == 'shop':
                    # buy button click: only act on actual MOUSEBUTTONDOWN
                    buy_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 30, 200, 60)
                    if buy_rect.collidepoint(event.pos):
                        price = 100
                        if wallet.spend_coins(price):
                            start_opening()
                            change_state('game')
                        else:
                            global SHOP_MSG, SHOP_MSG_T
                            SHOP_MSG = "Pas assez de Minecoins"
                            SHOP_MSG_T = time.time()
                elif STATE == 'settings':
                    reload_rect = pygame.Rect(220, 200, 240, 48)
                    if reload_rect.collidepoint(event.pos):
                        reload_avatar_mapping(clear_cache=True)
                    # effects quality button
                    quality_rect = pygame.Rect(220, 260, 240, 48)
                    if quality_rect.collidepoint(event.pos):
                        q = get_effects_quality()
                        nxt = 'medium' if q == 'low' else 'high' if q == 'medium' else 'low'
                        CURRENT_SETTINGS['effects_quality'] = nxt
                        game_settings.save_settings(CURRENT_SETTINGS)
                else:
                    # handle click on Continue button when animation finished
                    if STATE == 'game' and 'PACK_ANIM' in globals() and PACK_ANIM is not None and getattr(PACK_ANIM, 'finished', False):
                        cont_rect = get_continue_button_rect()
                        if cont_rect.collidepoint(event.pos):
                            change_state('collection')
                            continue
                    # allow clicking to skip while animation is running
                    if STATE == 'game' and 'PACK_ANIM' in globals() and PACK_ANIM is not None and not getattr(PACK_ANIM, 'finished', True):
                        PACK_ANIM.skip()
                        continue
                    if BUTTON_RECT.collidepoint(event.pos):
                        start_opening()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    start_opening()
                if event.key == pygame.K_ESCAPE:
                    # close announcement modal if open
                    if ANNOUNCEMENT_OPEN:
                        ANNOUNCEMENT_OPEN = False
                    # skip animation if running
                    if STATE == 'game' and 'PACK_ANIM' in globals() and PACK_ANIM is not None and not getattr(PACK_ANIM, 'finished', True):
                        PACK_ANIM.skip()

        # update fade alpha for simple transition effect
        # (we'll just fade in when entering a non-menu screen)
        if STATE != 'menu' and FADE_ALPHA < 180:
            FADE_ALPHA = min(180, FADE_ALPHA + FADE_SPEED * dt)
        elif STATE == 'menu' and FADE_ALPHA > 0:
            FADE_ALPHA = max(0, FADE_ALPHA - FADE_SPEED * dt)

        update_animation(dt)

        screen.fill((200, 200, 200))
        if STATE == 'menu':
            title = large_font.render("Minefut", True, (20, 20, 20))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))
            # Announcement panel (computed)
            panel_rect = get_announcement_rect()
            panel_x, panel_y, panel_w, panel_h = panel_rect.x, panel_rect.y, panel_rect.w, panel_rect.h
            pygame.draw.rect(screen, (245, 245, 245), panel_rect, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2, border_radius=10)
            ann_title = font.render('Annonce', True, (20, 20, 20))
            screen.blit(ann_title, (panel_x + 12, panel_y + 8))
            # draw image if available
            if announcement_img:
                # fit image inside a box and preserve aspect
                img_box = pygame.Rect(panel_x + 12, panel_y + 48, panel_w - 24, panel_h - 96)
                img_scaled = scale_preserve_aspect(announcement_img, img_box.w, img_box.h)
                ix = img_box.x + (img_box.w - img_scaled.get_width()) // 2
                iy = img_box.y + (img_box.h - img_scaled.get_height()) // 2
                screen.blit(img_scaled, (ix, iy))
            else:
                # placeholder
                ph = pygame.Rect(panel_x + 12, panel_y + 48, panel_w - 24, panel_h - 96)
                pygame.draw.rect(screen, (220, 220, 220), ph, border_radius=8)
                ph_txt = font.render('Image annonce manquante', True, (120, 120, 120))
                screen.blit(ph_txt, (ph.x + 8, ph.y + ph.h//2 - ph_txt.get_height()//2))
            # short description
            desc = small_font.render('Découvre les nouveautés et événements !', True, (60, 60, 60))
            screen.blit(desc, (panel_x + 12, panel_y + panel_h - 40))
            # indicate clickable
            click_hint = small_font.render('[Cliquer pour voir]', True, (90, 90, 200))
            screen.blit(click_hint, (panel_x + panel_w - click_hint.get_width() - 12, panel_y + panel_h - 40))
            # draw buttons with hover/pressed state
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()[0]
            for rect, label, action in MENU_BUTTONS:
                hovered = rect.collidepoint(mouse_pos)
                pressed = hovered and mouse_pressed
                draw_button_state(rect, label, hovered, pressed)
            draw_wallet_chip()
        elif STATE == 'collection':
            title = large_font.render("Collection", True, (20, 20, 20))
            screen.blit(title, (20, 20))
            # list players from DB
            from game import db
            players = db.load_players()
            for i, p in enumerate(players):
                y = 80 + i * 56
                # draw avatar/card thumb
                thumb_x, thumb_y = 24, y - 8
                thumb_w, thumb_h = 40, 40
                thumb_rect = pygame.Rect(thumb_x, thumb_y, thumb_w, thumb_h)
                img_path = p.get('image')
                if not img_path:
                    img_path = resolve_player_image_by_name_and_rarity(p.get('name', ''), p.get('rarity', ''), AVATAR_MAP)
                raw = None
                if img_path:
                    resolved = Path(__file__).resolve().parents[0] / img_path
                    if resolved.exists():
                        try:
                            raw = pygame.image.load(str(resolved)).convert_alpha()
                        except Exception:
                            raw = None
                if raw is None:
                    # placeholder
                    ph_path = Path(__file__).resolve().parents[0] / 'data' / 'avatars' / '_placeholder.png'
                    if ph_path.exists():
                        try:
                            raw = pygame.image.load(str(ph_path)).convert_alpha()
                        except Exception:
                            raw = None
                ring_color = get_rarity_color(p.get('rarity', 'Common'))
                if raw is not None:
                    iw, ih = raw.get_size()
                    is_card_img = ih / max(1, iw) >= 1.2
                    if is_card_img:
                        # rect thumb with small padding and rarity strip
                        pad = 2
                        rect_area = pygame.Rect(thumb_rect.x + pad, thumb_rect.y + pad, thumb_w - 2*pad, thumb_h - 2*pad)
                        scaled = scale_preserve_aspect(raw, rect_area.w, rect_area.h)
                        pygame.draw.rect(screen, (230, 230, 230), thumb_rect, border_radius=6)
                        pygame.draw.rect(screen, (180, 180, 180), thumb_rect, 1, border_radius=6)
                        screen.blit(scaled, (rect_area.x + (rect_area.w - scaled.get_width()) // 2, rect_area.y + (rect_area.h - scaled.get_height()) // 2))
                        pygame.draw.rect(screen, ring_color, (thumb_rect.x - 4, thumb_rect.y, 4, thumb_rect.h))
                    else:
                        # circular avatar with ring
                        pygame.draw.circle(screen, (240, 240, 240), (thumb_rect.x + thumb_w//2, thumb_rect.y + thumb_h//2), thumb_w//2)
                        surf = scale_preserve_aspect(raw, thumb_w, thumb_h)
                        circ = circle_crop_image(surf, min(thumb_w, thumb_h))
                        screen.blit(circ, thumb_rect.topleft)
                        pygame.draw.circle(screen, ring_color, (thumb_rect.x + thumb_w//2, thumb_rect.y + thumb_h//2), thumb_w//2 + 2, 3)
                else:
                    # placeholder circle
                    pygame.draw.circle(screen, (240, 240, 240), (thumb_rect.x + thumb_w//2, thumb_rect.y + thumb_h//2), thumb_w//2)
                    pygame.draw.circle(screen, (200, 200, 200), (thumb_rect.x + thumb_w//2, thumb_rect.y + thumb_h//2), thumb_w//2 - 2, 2)
                # text next to thumb
                txt = font.render(f"{p['id']}. {p['name']}  ({p['rarity']}) - {p['rating']}", True, (30, 30, 30))
                screen.blit(txt, (thumb_rect.right + 12, y))
            # back hint
            hint = small_font.render("[Esc] pour retourner au menu", True, (80, 80, 80))
            screen.blit(hint, (20, HEIGHT - 40))
            draw_wallet_chip()
        else:
            # Pack opening cinematic (STATE == 'game')
            if PACK_ANIM is not None and OPENING:
                PACK_ANIM.draw(screen)
                if PACK_ANIM.finished:
                    # draw clickable Continue button + Enter hint
                    cont_rect = get_continue_button_rect()
                    mouse_pos = pygame.mouse.get_pos()
                    hovered = cont_rect.collidepoint(mouse_pos)
                    pressed = hovered and pygame.mouse.get_pressed()[0]
                    draw_button_state(cont_rect, 'Continuer', hovered, pressed)
                    hint = small_font.render('(Entrée)', True, (230, 230, 230))
                    screen.blit(hint, (cont_rect.centerx - hint.get_width()//2, cont_rect.bottom + 6))
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_RETURN]:
                        change_state('collection')
            else:
                title = large_font.render("Minefut - Démo d'ouverture de pack", True, (20, 20, 20))
                screen.blit(title, (20, 20))
                instruction = font.render("Cliquez sur 'Ouvrir pack' ou appuyez sur [Espace]", True, (50, 50, 50))
                screen.blit(instruction, (20, 70))
                draw_button()
                draw_wallet_chip()
                # Show last received cards as PNGs instead of framed UI
                item_w, item_h = 160, 220
                for c in cards:
                    img_path = resolve_card_image_path(c)
                    cx = int(c.x + item_w//2)
                    cy = int(c.y + item_h//2)
                    if img_path is not None:
                        ok = draw_player_png_centered(screen, img_path, (cx, cy), item_w, item_h)
                        if not ok:
                            draw_card(c)
                    else:
                        draw_card(c)
        # shop screen
        if STATE == 'shop':
            title = large_font.render('Boutique', True, (20, 20, 20))
            screen.blit(title, (20, 20))
            # buy pack button
            buy_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 30, 200, 60)
            mouse_pos = pygame.mouse.get_pos()
            hovered = buy_rect.collidepoint(mouse_pos)
            pressed = hovered and pygame.mouse.get_pressed()[0]
            draw_button_state(buy_rect, 'Acheter pack (100)', hovered, pressed)
            hint = small_font.render("[Esc] pour revenir", True, (80, 80, 80))
            screen.blit(hint, (20, HEIGHT - 40))
            # transient message if any
            if SHOP_MSG and time.time() - SHOP_MSG_T < 2.5:
                msg = large_font.render(SHOP_MSG, True, (200, 80, 80))
                screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 + 44))
            draw_wallet_chip()

        # settings screen
        if STATE == 'settings':
            title = large_font.render('Paramètres', True, (20, 20, 20))
            screen.blit(title, (20, 20))
            # volume slider
            vs_rect = pygame.Rect(220, 140, 360, 28)
            pygame.draw.rect(screen, (220, 220, 220), vs_rect, border_radius=6)
            vol = CURRENT_SETTINGS.get('volume', 80)
            filled_w = int((vol / 100.0) * vs_rect.w)
            pygame.draw.rect(screen, (30, 144, 255), (vs_rect.x, vs_rect.y, filled_w, vs_rect.h), border_radius=6)
            vol_txt = font.render(f'Volume: {vol}%', True, (30, 30, 30))
            screen.blit(vol_txt, (vs_rect.x, vs_rect.y - 28))
            hint = small_font.render("Clique et glisse pour changer. [Esc] pour revenir", True, (80, 80, 80))
            screen.blit(hint, (20, HEIGHT - 40))
            # handle mouse drag for slider
            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                if vs_rect.collidepoint((mx, my)):
                    rel = mx - vs_rect.x
                    vol = max(0, min(100, int((rel / vs_rect.w) * 100)))
                    CURRENT_SETTINGS['volume'] = vol
                    game_settings.save_settings(CURRENT_SETTINGS)
            # reload mapping button
            reload_rect = pygame.Rect(220, 200, 240, 48)
            mouse_pos = pygame.mouse.get_pos()
            hovered = reload_rect.collidepoint(mouse_pos)
            pressed = hovered and pygame.mouse.get_pressed()[0]
            draw_button_state(reload_rect, 'Recharger images', hovered, pressed)
            if LAST_RELOAD_MSG and time.time() - LAST_RELOAD_TIME < 3.0:
                msg = small_font.render(LAST_RELOAD_MSG, True, (60, 120, 60))
                screen.blit(msg, (reload_rect.right + 16, reload_rect.y + 12))
            # effects quality button
            quality_rect = pygame.Rect(220, 260, 240, 48)
            mouse_pos = pygame.mouse.get_pos()
            hovered = quality_rect.collidepoint(mouse_pos)
            pressed = hovered and pygame.mouse.get_pressed()[0]
            q = get_effects_quality()
            label = 'Qualité effets: ' + ('Bas' if q == 'low' else 'Élevé' if q == 'high' else 'Moyen')
            draw_button_state(quality_rect, label, hovered, pressed)
            draw_wallet_chip()

        # apply fade overlay if any
        if FADE_ALPHA > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(FADE_ALPHA)))
            screen.blit(overlay, (0, 0))

        # announcement full-screen modal
        if ANNOUNCEMENT_OPEN:
            modal = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            modal.fill((0, 0, 0, 220))
            screen.blit(modal, (0, 0))
            # draw centered image box
            box_w = int(WIDTH * 0.75)
            box_h = int(HEIGHT * 0.75)
            box_x = WIDTH//2 - box_w//2
            box_y = HEIGHT//2 - box_h//2
            box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
            pygame.draw.rect(screen, (245, 245, 245), box_rect, border_radius=12)
            pygame.draw.rect(screen, (200, 200, 200), box_rect, 3, border_radius=12)
            if announcement_img:
                img_scaled = scale_preserve_aspect(announcement_img, box_w - 40, box_h - 120)
                ix = box_x + 20 + (box_w - 40 - img_scaled.get_width()) // 2
                iy = box_y + 20 + (box_h - 120 - img_scaled.get_height()) // 2
                screen.blit(img_scaled, (ix, iy))
            else:
                no_txt = font.render('Aucune image', True, (120, 120, 120))
                screen.blit(no_txt, (box_x + 20, box_y + 20))
            # close hint
            close_txt = font.render('[Echap] Fermer', True, (80, 80, 80))
            screen.blit(close_txt, (box_x + 20, box_y + box_h - 40))
            # draw clickable X button (top-right of box)
            close_rect = pygame.Rect(box_x + box_w - 48, box_y + 12, 36, 36)
            pygame.draw.rect(screen, (220, 80, 80), close_rect, border_radius=6)
            x_txt = font.render('X', True, (255, 255, 255))
            screen.blit(x_txt, (close_rect.x + close_rect.w//2 - x_txt.get_width()//2, close_rect.y + close_rect.h//2 - x_txt.get_height()//2))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def change_state(new_state: str):
    global STATE
    STATE = new_state


if __name__ == '__main__':
    # Prefer the new revamped app if enabled; print which path is used for clarity.
    from game.settings import load_settings
    s = load_settings()
    if s.get('ui_revamp', True):
        try:
            from game.app import run_app
            print('[Minefut] Launching revamp UI…')
            run_app()
            sys.exit(0)
        except Exception as e:
            print('[Minefut] Failed to launch revamp UI, falling back to legacy:', e)
    else:
        print('[Minefut] ui_revamp=false → using legacy UI')
    print('[Minefut] Launching legacy UI…')
    main()
