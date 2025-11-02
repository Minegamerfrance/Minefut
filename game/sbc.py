from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

from . import db as game_db
from .cards import Card


@dataclass
class SBCRequirement:
    min_count: int
    min_avg_rating: int = 0
    allowed_rarities: Optional[List[str]] = None  # canonical labels: 'or rare', 'or non rare', 'icon', 'hero', 'otw'


@dataclass
class SBCChallenge:
    id: str
    name: str
    description: str
    requirement: SBCRequirement
    reward_pack: Tuple[str, int]  # (pack_name, count)


# Minimal set of SBCs tailored to available data (name, rating, rarity only)
CHALLENGES: List[SBCChallenge] = [
    SBCChallenge(
        id='bronze_basic',
        name='Défi Basique',
        description='Soumets 3 joueurs, note moyenne ≥ 70. Rareté libre.',
        requirement=SBCRequirement(min_count=3, min_avg_rating=70, allowed_rarities=None),
        reward_pack=('Pack Classique', 3),
    ),
    # --- Lancement: World Tour — Dolan (single) ---
    SBCChallenge(
        id='dolan_world_tour_1',
        name='Dolan — World Tour',
        description='11 joueurs, note moyenne ≥ 83. Rareté libre.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=83, allowed_rarities=None),
        reward_pack=('Pack Premium', 3),
    ),
    # --- Spécial Halloween: Paul Pogba — (1 défi) ---
    SBCChallenge(
        id='pogba_halloween_1',
        name='Paul Pogba — Halloween',
        description='11 joueurs, note moyenne ≥ 85. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=85, allowed_rarities=['or rare', 'hero', 'icon', 'otw']),
        reward_pack=('Pack Premium', 4),
    ),
    SBCChallenge(
        id='gold_rare',
        name='Or Rare',
        description='Soumets 5 joueurs or rare, note moyenne ≥ 80.',
        requirement=SBCRequirement(min_count=5, min_avg_rating=80, allowed_rarities=['or rare']),
        reward_pack=('Pack Premium', 5),
    ),
    SBCChallenge(
        id='elite_heroes',
        name='Héros & Icônes',
        description='Soumets 3 joueurs héro/icon, note moyenne ≥ 85.',
        requirement=SBCRequirement(min_count=3, min_avg_rating=85, allowed_rarities=['hero', 'icon']),
        reward_pack=('Pack Icône', 3),
    ),
    # --- Série spéciale: Sergio Busquets — Fin d'une ère (4 défis) ---
    SBCChallenge(
        id='busquets_eoe_1',
        name="Busquets EOE — 1/4",
        description="11 joueurs, note moyenne ≥ 78. Rareté libre.",
        requirement=SBCRequirement(min_count=11, min_avg_rating=78, allowed_rarities=None),
        reward_pack=("Pack Classique", 2),
    ),
    SBCChallenge(
        id='busquets_eoe_2',
        name="Busquets EOE — 2/4",
        description="11 joueurs, note moyenne ≥ 82. Or conseillé.",
        requirement=SBCRequirement(min_count=11, min_avg_rating=82, allowed_rarities=[
            'or non rare', 'or rare', 'hero', 'icon', 'otw'
        ]),
        reward_pack=("Pack Classique", 3),
    ),
    SBCChallenge(
        id='busquets_eoe_3',
        name="Busquets EOE — 3/4",
        description="11 joueurs, note moyenne ≥ 84. Raretés autorisées: Or rare/plus.",
        requirement=SBCRequirement(min_count=11, min_avg_rating=84, allowed_rarities=[
            'or rare', 'hero', 'icon', 'otw'
        ]),
        reward_pack=("Pack Premium", 3),
    ),
    SBCChallenge(
        id='busquets_eoe_4',
        name="Busquets EOE — 4/4",
        description="11 joueurs, note moyenne ≥ 86. Raretés autorisées: Or rare/plus.",
        requirement=SBCRequirement(min_count=11, min_avg_rating=86, allowed_rarities=[
            'or rare', 'hero', 'icon', 'otw'
        ]),
        reward_pack=("Pack Premium", 4),
    ),
    # --- Série spéciale: Jordi Alba — Fin d'une ère (3 défis) ---
    SBCChallenge(
        id='alba_eoe_1',
        name="Jordi Alba EOE — 1/3",
        description="11 joueurs, note moyenne ≥ 80. Rareté libre.",
        requirement=SBCRequirement(min_count=11, min_avg_rating=80, allowed_rarities=None),
        reward_pack=("Pack Classique", 2),
    ),
    SBCChallenge(
        id='alba_eoe_2',
        name="Jordi Alba EOE — 2/3",
        description="11 joueurs, note moyenne ≥ 84. Raretés autorisées: Or rare/plus.",
        requirement=SBCRequirement(min_count=11, min_avg_rating=84, allowed_rarities=[
            'or rare', 'hero', 'icon', 'otw'
        ]),
        reward_pack=("Pack Premium", 3),
    ),
    # --- Série spéciale: Van Buyten — Héro (2 défis) ---
    SBCChallenge(
        id='vanbuyten_hero_1',
        name='Van Buyten Héro — 1/2',
        description='11 joueurs, note moyenne ≥ 83. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=83, allowed_rarities=[
            'or rare', 'hero', 'icon', 'otw'
        ]),
        reward_pack=('Pack Premium', 3),
    ),
    SBCChallenge(
        id='vanbuyten_hero_2',
        name='Van Buyten Héro — 2/2',
        description='11 joueurs, note moyenne ≥ 85. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=85, allowed_rarities=[
            'or rare', 'hero', 'icon', 'otw'
        ]),
        reward_pack=('Pack Premium', 4),
    ),
    SBCChallenge(
        id='alba_eoe_3',
        name="Jordi Alba EOE — 3/3",
        description="11 joueurs, note moyenne ≥ 86. Raretés autorisées: Or rare/plus.",
        requirement=SBCRequirement(min_count=11, min_avg_rating=86, allowed_rarities=[
            'or rare', 'hero', 'icon', 'otw'
        ]),
        reward_pack=("Pack Premium", 4),
    ),
    # --- Série spéciale: Goretzka — Flashback (2 défis) ---
    SBCChallenge(
        id='goretzka_fb_1',
        name='Goretzka Flashback — 1/2',
        description='11 joueurs, note moyenne ≥ 84. Rareté libre.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=84, allowed_rarities=None),
        reward_pack=('Pack Premium', 3),
    ),
    SBCChallenge(
        id='goretzka_fb_2',
        name='Goretzka Flashback — 2/2',
        description='11 joueurs, note moyenne ≥ 86. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=86, allowed_rarities=['or rare', 'hero', 'icon', 'otw']),
        reward_pack=('Pack Premium', 4),
    ),
    # --- Série spéciale: Džeko — Flashback (2 défis) ---
    SBCChallenge(
        id='dzeko_fb_1',
        name='Džeko Flashback — 1/2',
        description='11 joueurs, note moyenne ≥ 82. Rareté libre.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=82, allowed_rarities=None),
        reward_pack=('Pack Classique', 3),
    ),
    SBCChallenge(
        id='dzeko_fb_2',
        name='Džeko Flashback — 2/2',
        description='11 joueurs, note moyenne ≥ 85. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=85, allowed_rarities=['or rare', 'hero', 'icon', 'otw']),
        reward_pack=('Pack Premium', 3),
    ),
    # --- Série spéciale: Xherdan Shaqiri — Flashback (2 défis) ---
    SBCChallenge(
        id='shaqiri_fb_1',
        name='Xherdan Shaqiri — Flashback — 1/2',
        description='11 joueurs, note moyenne ≥ 82. Rareté libre.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=82, allowed_rarities=None),
        reward_pack=('Pack Classique', 3),
    ),
    SBCChallenge(
        id='shaqiri_fb_2',
        name='Xherdan Shaqiri — Flashback — 2/2',
        description='11 joueurs, note moyenne ≥ 85. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=85, allowed_rarities=['or rare', 'hero', 'icon', 'otw']),
        reward_pack=('Pack Premium', 3),
    ),
    # --- Spécial: Dimitri Payet — Héro (1 défi) ---
    SBCChallenge(
        id='payet_hero_1',
        name='Dimitri Payet — Héro',
        description='11 joueurs, note moyenne ≥ 84. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=84, allowed_rarities=['or rare', 'hero', 'icon', 'otw']),
        reward_pack=('Pack Premium', 3),
    ),
    # --- Série spéciale: Zlatan Ibrahimović — Icon début (5 défis) ---
    SBCChallenge(
        id='zlatan_icon_1',
        name='Zlatan Ibrahimović Icon début — 1/5',
        description='11 joueurs, note moyenne ≥ 82. Rareté libre.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=82, allowed_rarities=None),
        reward_pack=('Pack Classique', 3),
    ),
    SBCChallenge(
        id='zlatan_icon_2',
        name='Zlatan Ibrahimović Icon début — 2/5',
        description='11 joueurs, note moyenne ≥ 84. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=84, allowed_rarities=['or rare', 'hero', 'icon', 'otw']),
        reward_pack=('Pack Premium', 3),
    ),
    SBCChallenge(
        id='zlatan_icon_3',
        name='Zlatan Ibrahimović Icon début — 3/5',
        description='11 joueurs, note moyenne ≥ 85. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=85, allowed_rarities=['or rare', 'hero', 'icon', 'otw']),
        reward_pack=('Pack Premium', 3),
    ),
    SBCChallenge(
        id='zlatan_icon_4',
        name='Zlatan Ibrahimović Icon début — 4/5',
        description='11 joueurs, note moyenne ≥ 86. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=86, allowed_rarities=['or rare', 'hero', 'icon', 'otw']),
        reward_pack=('Pack Premium', 4),
    ),
    SBCChallenge(
        id='zlatan_icon_5',
        name='Zlatan Ibrahimović Icon début — 5/5',
        description='11 joueurs, note moyenne ≥ 88. Raretés autorisées: Or rare/plus.',
        requirement=SBCRequirement(min_count=11, min_avg_rating=88, allowed_rarities=['or rare', 'hero', 'icon', 'otw']),
        reward_pack=('Pack Icône', 3),
    ),
]


def canonical_rarity(r: str) -> str:
    rl = (r or '').strip().lower()
    if rl in ('or rare', 'or_rare', 'gold rare', 'gold_rare', 'rare', 'rare gold', 'rare_gold'):
        return 'or rare'
    if rl in ('or non rare', 'or_non_rare', 'gold', 'gold common', 'gold_common', 'commun', 'common', 'or commun', 'common_gold'):
        return 'or non rare'
    if rl in ('icon', 'icons', 'legend', 'legendary', 'legendaire', 'légendaire'):
        return 'icon'
    if rl in ('hero', 'heros', 'epic', 'epique', 'épic'):
        return 'hero'
    if rl in ('otw', 'ones_to_watch', 'ones to watch'):
        return 'otw'
    return rl


def get_owned_pool() -> Dict[str, int]:
    """Return owned counts by base name."""
    return game_db.load_collection()


def get_catalog_index() -> Dict[str, Dict]:
    """Map base name -> best player entry (name, rating, rarity, image)."""
    catalog = game_db.get_unique_catalog()
    return {c['name']: c for c in catalog}


def validate_selection(selection: List[str], challenge: SBCChallenge) -> Tuple[bool, str]:
    """Check if selection meets the requirement.
    selection: list of base player names.
    """
    req = challenge.requirement
    if len(selection) < req.min_count:
        return False, f"Sélection incomplète ({len(selection)}/{req.min_count})."

    index = get_catalog_index()
    ratings = []
    rarities = []
    for name in selection:
        item = index.get(name)
        if not item:
            return False, f"Joueur inconnu: {name}"
        ratings.append(int(item.get('rating', 0)))
        rarities.append(canonical_rarity(item.get('rarity', '')))

    avg = int(round(sum(ratings) / max(1, len(ratings))))
    if avg < req.min_avg_rating:
        return False, f"Note moyenne insuffisante ({avg} < {req.min_avg_rating})."

    if req.allowed_rarities:
        for r in rarities:
            if r not in req.allowed_rarities:
                return False, f"Rareté non autorisée: {r}."

    return True, 'OK'


def can_consume(selection: List[str]) -> Tuple[bool, str]:
    """Check owned counts are enough to consume this selection."""
    owned = get_owned_pool()
    need: Dict[str, int] = {}
    for n in selection:
        need[n] = need.get(n, 0) + 1
    for n, cnt in need.items():
        if owned.get(n, 0) < cnt:
            return False, f"Pas assez de {n} (possédé: {owned.get(n, 0)}, requis: {cnt})."
    return True, 'OK'


def consume(selection: List[str]) -> Dict[str, int]:
    """Decrement owned counts for the selection."""
    return game_db.remove_from_collection_by_names(selection)


# ----------------- Progress & Special Reward (Busquets EOE) ----------------- #

_PROGRESS_PATH = Path(__file__).resolve().parents[1] / 'data' / 'sbc_progress.json'
_BUSQUETS_IDS = ['busquets_eoe_1', 'busquets_eoe_2', 'busquets_eoe_3', 'busquets_eoe_4']
_BUSQUETS_NAME = 'Sergio Busquets'
_BUSQUETS_RARITY = "fin d'une ère"
_BUSQUETS_RATING = 91

# Jordi Alba constants
_ALBA_IDS = ['alba_eoe_1', 'alba_eoe_2', 'alba_eoe_3']
_ALBA_NAME = 'Jordi Alba'
_ALBA_RARITY = "fin d'une ère"
_ALBA_RATING = 90

# Flashback bundles
_GORETZKA_IDS = ['goretzka_fb_1', 'goretzka_fb_2']
_GORETZKA_NAME = 'Goretzka'
_GORETZKA_RARITY = 'flashback'
_GORETZKA_RATING = 90

_DZEKO_IDS = ['dzeko_fb_1', 'dzeko_fb_2']
_DZEKO_NAME = 'Džeko'
_DZEKO_RARITY = 'flashback'
_DZEKO_RATING = 88

# Flashback bundle: Xherdan Shaqiri
_SHAQIRI_IDS = ['shaqiri_fb_1', 'shaqiri_fb_2']
_SHAQIRI_NAME = 'Xherdan Shaqiri'
_SHAQIRI_RARITY = 'flashback'
_SHAQIRI_RATING = 82

# Hero bundle: Van Buyten
_VANBUYTEN_IDS = ['vanbuyten_hero_1', 'vanbuyten_hero_2']
_VANBUYTEN_NAME = 'Van Buyten'
_VANBUYTEN_RARITY = 'hero'
_VANBUYTEN_RATING = 89

# Hero single: Dimitri Payet
_PAYET_IDS = ['payet_hero_1']
_PAYET_NAME = 'Payet'
_PAYET_RARITY = 'hero'
_PAYET_RATING = 85

# Icon début series: Zlatan Ibrahimović (grant after all 5)
_ZLATAN_IDS = ['zlatan_icon_1', 'zlatan_icon_2', 'zlatan_icon_3', 'zlatan_icon_4', 'zlatan_icon_5']
_ZLATAN_NAME = 'Ibrahimović'
_ZLATAN_RARITY = 'icon'
_ZLATAN_RATING = 86

# Halloween single: Paul Pogba
_POGBA_IDS = ['pogba_halloween_1']
_POGBA_NAME = 'Paul Pogba#sbc'
_POGBA_RARITY = 'or rare'
_POGBA_RATING = 86

# Launch single: Dolan — World Tour
_DOLAN_IDS = ['dolan_world_tour_1']
_DOLAN_NAME = 'Dolan'
_DOLAN_RARITY = 'world tour'
_DOLAN_RATING = 84


def _load_progress() -> Dict:
    try:
        if _PROGRESS_PATH.exists():
            with _PROGRESS_PATH.open('r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {"completed": []}


def _save_progress(data: Dict) -> None:
    try:
        _PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _PROGRESS_PATH.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def mark_completed(ch_id: str) -> None:
    data = _load_progress()
    comp = set(data.get('completed', []))
    if ch_id not in comp:
        comp.add(ch_id)
        data['completed'] = sorted(list(comp))
        _save_progress(data)


def is_completed(ch_id: str) -> bool:
    data = _load_progress()
    return ch_id in set(data.get('completed', []))


def busquets_all_completed() -> bool:
    comp = set(_load_progress().get('completed', []))
    return all(cid in comp for cid in _BUSQUETS_IDS)


def check_and_grant_busquets_bundle() -> Optional[Card]:
    """If all four Busquets EOE parts are completed, grant the special Busquets card once.
    Returns the granted Card for preview, or None if not eligible/already granted.
    """
    data = _load_progress()
    # use a flag to avoid double grant
    if not busquets_all_completed():
        return None
    if data.get('busquets_eoe_granted'):
        return None
    # grant now
    data['busquets_eoe_granted'] = True
    _save_progress(data)
    # add to collection
    game_db.add_to_collection_by_names([_BUSQUETS_NAME])
    # Return a Card for preview (avatar path mapping handled elsewhere)
    return Card(name=_BUSQUETS_NAME, rarity=_BUSQUETS_RARITY, bg_color=(210, 180, 60), rating=_BUSQUETS_RATING)


def check_and_grant_alba_bundle() -> Optional[Card]:
    """If all three Jordi Alba EOE parts are completed, grant the special Alba card once."""
    data = _load_progress()
    comp = set(data.get('completed', []))
    if not all(cid in comp for cid in _ALBA_IDS):
        return None
    if data.get('alba_eoe_granted'):
        return None
    data['alba_eoe_granted'] = True
    _save_progress(data)
    game_db.add_to_collection_by_names([_ALBA_NAME])
    return Card(name=_ALBA_NAME, rarity=_ALBA_RARITY, bg_color=(210, 180, 60), rating=_ALBA_RATING)


def check_and_grant_goretzka_bundle() -> Optional[Card]:
    data = _load_progress()
    comp = set(data.get('completed', []))
    if not all(cid in comp for cid in _GORETZKA_IDS):
        return None
    if data.get('goretzka_fb_granted'):
        return None
    data['goretzka_fb_granted'] = True
    _save_progress(data)
    game_db.add_to_collection_by_names([_GORETZKA_NAME])
    return Card(name=_GORETZKA_NAME, rarity=_GORETZKA_RARITY, bg_color=(100, 180, 240), rating=_GORETZKA_RATING)


def check_and_grant_dzeko_bundle() -> Optional[Card]:
    data = _load_progress()
    comp = set(data.get('completed', []))
    if not all(cid in comp for cid in _DZEKO_IDS):
        return None
    if data.get('dzeko_fb_granted'):
        return None
    data['dzeko_fb_granted'] = True
    _save_progress(data)
    game_db.add_to_collection_by_names([_DZEKO_NAME])
    return Card(name=_DZEKO_NAME, rarity=_DZEKO_RARITY, bg_color=(100, 180, 240), rating=_DZEKO_RATING)


def check_and_grant_shaqiri_bundle() -> Optional[Card]:
    data = _load_progress()
    comp = set(data.get('completed', []))
    if not all(cid in comp for cid in _SHAQIRI_IDS):
        return None
    if data.get('shaqiri_fb_granted'):
        return None
    data['shaqiri_fb_granted'] = True
    _save_progress(data)
    game_db.add_to_collection_by_names([_SHAQIRI_NAME])
    return Card(name=_SHAQIRI_NAME, rarity=_SHAQIRI_RARITY, bg_color=(100, 180, 240), rating=_SHAQIRI_RATING)


def check_and_grant_vanbuyten_bundle() -> Optional[Card]:
    data = _load_progress()
    comp = set(data.get('completed', []))
    if not all(cid in comp for cid in _VANBUYTEN_IDS):
        return None
    if data.get('vanbuyten_hero_granted'):
        return None
    data['vanbuyten_hero_granted'] = True
    _save_progress(data)
    game_db.add_to_collection_by_names([_VANBUYTEN_NAME])
    return Card(name=_VANBUYTEN_NAME, rarity=_VANBUYTEN_RARITY, bg_color=(140, 90, 180), rating=_VANBUYTEN_RATING)


def check_and_grant_payet_bundle() -> Optional[Card]:
    """If the Payet hero challenge is completed, grant the special Payet card once."""
    data = _load_progress()
    comp = set(data.get('completed', []))
    if not all(cid in comp for cid in _PAYET_IDS):
        return None
    if data.get('payet_hero_granted'):
        return None
    data['payet_hero_granted'] = True
    _save_progress(data)
    game_db.add_to_collection_by_names([_PAYET_NAME])
    return Card(name=_PAYET_NAME, rarity=_PAYET_RARITY, bg_color=(140, 90, 180), rating=_PAYET_RATING)


def check_and_grant_zlatan_bundle() -> Optional[Card]:
    """If all five Zlatan Icon début parts are completed, grant the special Zlatan card once."""
    data = _load_progress()
    comp = set(data.get('completed', []))
    if not all(cid in comp for cid in _ZLATAN_IDS):
        return None
    if data.get('zlatan_icon_granted'):
        return None
    data['zlatan_icon_granted'] = True
    _save_progress(data)
    game_db.add_to_collection_by_names([_ZLATAN_NAME])
    return Card(name=_ZLATAN_NAME, rarity=_ZLATAN_RARITY, bg_color=(210, 210, 210), rating=_ZLATAN_RATING)


def check_and_grant_pogba_bundle() -> Optional[Card]:
    """If the Pogba Halloween challenge is completed, grant the special Pogba card once."""
    data = _load_progress()
    comp = set(data.get('completed', []))
    if not all(cid in comp for cid in _POGBA_IDS):
        return None
    if data.get('pogba_halloween_granted'):
        return None
    data['pogba_halloween_granted'] = True
    _save_progress(data)
    game_db.add_to_collection_by_names([_POGBA_NAME])
    return Card(name=_POGBA_NAME, rarity=_POGBA_RARITY, bg_color=(240, 160, 60), rating=_POGBA_RATING)


def check_and_grant_dolan_bundle() -> Optional[Card]:
    """If the Dolan World Tour challenge is completed, grant the special Dolan card once."""
    data = _load_progress()
    comp = set(data.get('completed', []))
    if not all(cid in comp for cid in _DOLAN_IDS):
        return None
    if data.get('dolan_world_tour_granted'):
        return None
    data['dolan_world_tour_granted'] = True
    _save_progress(data)
    game_db.add_to_collection_by_names([_DOLAN_NAME])
    return Card(name=_DOLAN_NAME, rarity=_DOLAN_RARITY, bg_color=(60, 200, 220), rating=_DOLAN_RATING)


# ----------------- Catalog helpers: SBC-only special players ----------------- #

def get_sbc_only_players() -> List[Dict]:
    """Return a list of special players that are only unlockable via SBCs (not packable).

    Each item contains at least: name, rating, rarity, and flags sbc_only=True, packable=False.
    Images are resolved at render-time via avatar mapping; we do not set image paths here.
    """
    specials = [
        {"name": _BUSQUETS_NAME, "rating": _BUSQUETS_RATING, "rarity": _BUSQUETS_RARITY},
        {"name": _ALBA_NAME, "rating": _ALBA_RATING, "rarity": _ALBA_RARITY},
        {"name": _GORETZKA_NAME, "rating": _GORETZKA_RATING, "rarity": _GORETZKA_RARITY},
        {"name": _DZEKO_NAME, "rating": _DZEKO_RATING, "rarity": _DZEKO_RARITY},
        {"name": _SHAQIRI_NAME, "rating": _SHAQIRI_RATING, "rarity": _SHAQIRI_RARITY},
        {"name": _VANBUYTEN_NAME, "rating": _VANBUYTEN_RATING, "rarity": _VANBUYTEN_RARITY},
        {"name": _PAYET_NAME, "rating": _PAYET_RATING, "rarity": _PAYET_RARITY},
        {"name": _ZLATAN_NAME, "rating": _ZLATAN_RATING, "rarity": _ZLATAN_RARITY},
        {"name": _POGBA_NAME, "rating": _POGBA_RATING, "rarity": _POGBA_RARITY},
        {"name": _DOLAN_NAME, "rating": _DOLAN_RATING, "rarity": _DOLAN_RARITY},
    ]
    for s in specials:
        s["sbc_only"] = True
        s["packable"] = False
    return specials
