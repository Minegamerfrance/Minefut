from __future__ import annotations

import random
from typing import List, Tuple

from .cards import Card


# Canonical rarity colors aligned with UI theme
RARITY_COLORS = {
    'icon': (245, 245, 235),
    'hero': (180, 60, 140),
    'or rare': (212, 175, 55),
    'or non rare': (194, 178, 128),
    'otw': (255, 140, 0),
    'world tour': (60, 200, 220),
}


def _color_for_rarity(rarity: str) -> Tuple[int, int, int]:
    return RARITY_COLORS.get(rarity, (180, 180, 180))


PACK_DEFS = {
    # name: list of (rarity, weight)
    'Pack Classique': [
        ('otw', 1),
        ('icon', 2),
        ('hero', 8),
        ('or rare', 28),
        ('or non rare', 61),
    ],
    'Pack Premium': [
        ('otw', 2),
        ('icon', 4),
        ('hero', 14),
        ('or rare', 40),
        ('or non rare', 40),
    ],
    'Pack Icône': [
        ('icon', 60),
        ('hero', 25),
        ('or rare', 10),
        ('otw', 3),
        ('or non rare', 2),
    ],
}


def _weighted_pick(weights):
    total = sum(w for _, w in weights)
    r = random.uniform(0, total)
    upto = 0
    for name, w in weights:
        if upto + w >= r:
            return name
        upto += w
    return weights[-1][0]


def generate_pack(pack_name: str, count: int = 5) -> List[Card]:
    """Generate a pack of cards according to the selected pack definition.
    Ratings are roughly 65–97, with small boosts for higher rarities and OTW.
    """
    weights = PACK_DEFS.get(pack_name) or PACK_DEFS['Pack Classique']
    from .cards import PLAYER_CATALOG  # local import to avoid cyclic on module import time

    out: List[Card] = []
    for _ in range(count):
        rarity = _weighted_pick(weights)
        name_entry = random.choice(PLAYER_CATALOG)
        name = name_entry['name']
        base = random.randint(65, 92)
        # Soft boosts by rarity
        if rarity in ('or rare', 'hero', 'icon', 'otw'):
            base = max(base, random.randint(80, 90))
        if rarity in ('hero', 'icon'):
            base = max(base, random.randint(86, 94))
        if rarity == 'icon':
            base = max(base, 90)
        if rarity == 'otw':
            base = max(base, random.randint(88, 96))
        rating = min(base, 97)
        color = _color_for_rarity(rarity)
        avatar_rel = f"data/avatars/{name_entry.get('avatar', '')}" if name_entry.get('avatar') else None
        out.append(Card(name=name, rarity=rarity, bg_color=color, rating=rating, otw=(rarity == 'otw'), avatar_path=avatar_rel))
    return out
