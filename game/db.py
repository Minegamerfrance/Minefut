import json
from pathlib import Path
from typing import List, Optional, Dict

DATA_FILE = Path(__file__).resolve().parents[1] / 'data' / 'players.json'
COLLECTION_FILE = Path(__file__).resolve().parents[1] / 'data' / 'collection.json'


def load_players() -> List[Dict]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open('r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('players', [])


def save_players(players: List[Dict]):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open('w', encoding='utf-8') as f:
        json.dump({'players': players}, f, indent=2, ensure_ascii=False)


def get_player(player_id: int) -> Optional[Dict]:
    players = load_players()
    for p in players:
        if p.get('id') == player_id:
            return p
    return None


def add_player(name: str, rating: int, rarity: str, image: Optional[str] = None) -> Dict:
    players = load_players()
    next_id = max((p.get('id', 0) for p in players), default=0) + 1
    new: Dict = {'id': next_id, 'name': name, 'rating': rating, 'rarity': rarity}
    if image is not None:
        new['image'] = image
    players.append(new)
    save_players(players)
    return new


def delete_player(player_id: int) -> bool:
    players = load_players()
    new_players = [p for p in players if p.get('id') != player_id]
    if len(new_players) == len(players):
        return False
    save_players(new_players)
    return True


def update_player(player_id: int, **fields) -> Optional[Dict]:
    players = load_players()
    for p in players:
        if p.get('id') == player_id:
            p.update(fields)
            save_players(players)
            return p
    return None


def update_players_images_from_mapping(name_to_file: Dict[str, str]) -> int:
    """Update players missing 'image' using a mapping from base name to filename.

    Base name is the player's name without any trailing ' #number' suffix.
    Returns the number of updated players.
    """
    players = load_players()
    updated = 0
    for p in players:
        if p.get('image'):
            continue
        name = p.get('name', '')
        base = name.split('#')[0].strip()
        filename = name_to_file.get(base)
        if filename:
            p['image'] = f"data/avatars/{filename}"
            updated += 1
    if updated:
        save_players(players)
    return updated


# -------- Collection persistence (Madfut-like, by player base name) -------- #

def _base_name(name: str) -> str:
    return (name or '').split('#')[0].strip()


def load_collection() -> Dict[str, int]:
    """Return a dict mapping base player name -> count owned (>=0)."""
    if not COLLECTION_FILE.exists():
        return {}
    try:
        with COLLECTION_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
        owned = data.get('owned', {})
        # normalize keys to strings
        return {str(k): int(v) for k, v in owned.items() if v is not None}
    except Exception:
        return {}


def save_collection(owned: Dict[str, int]):
    COLLECTION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with COLLECTION_FILE.open('w', encoding='utf-8') as f:
        json.dump({'owned': owned}, f, indent=2, ensure_ascii=False)


def add_to_collection_by_names(names: List[str]) -> Dict[str, int]:
    """Increment ownership counts for provided player names (base names)."""
    owned = load_collection()
    for n in names:
        b = _base_name(n)
        if not b:
            continue
        owned[b] = int(owned.get(b, 0)) + 1
    save_collection(owned)
    return owned


def remove_from_collection_by_names(names: List[str]) -> Dict[str, int]:
    """Decrement ownership counts for provided player base names. Counts won't go below zero."""
    owned = load_collection()
    for n in names:
        b = _base_name(n)
        if not b:
            continue
        current = int(owned.get(b, 0))
        if current > 0:
            owned[b] = current - 1
    save_collection(owned)
    return owned

def get_unique_catalog() -> List[Dict]:
    """Return a unique catalog (by base name) choosing the highest rating entry for display.

    This provides one entry per base name with fields: name, rating, rarity, image(optional)
    """
    players = load_players()
    best: Dict[str, Dict] = {}
    for p in players:
        base = _base_name(p.get('name', ''))
        if not base:
            continue
        cur = best.get(base)
        if cur is None or int(p.get('rating', 0)) > int(cur.get('rating', 0)):
            sel = {
                'name': base,
                'rating': p.get('rating', 0),
                'rarity': p.get('rarity', ''),
            }
            if 'image' in p:
                sel['image'] = p['image']
            best[base] = sel
    # Merge SBC-only special players (not packable) into the catalog, allow variants
    try:
        from . import sbc as _sbc
        for s in _sbc.get_sbc_only_players():
            full = str(s.get('name', '') or '')
            base = _base_name(full)
            key = full or base
            if key and key not in best:
                # keep provided fields; use full name to allow variants (e.g., #sbc)
                entry = {
                    'name': full or base,
                    'rating': s.get('rating', 0),
                    'rarity': s.get('rarity', ''),
                    'sbc_only': True,
                    'packable': False,
                }
                if 'image' in s:
                    entry['image'] = s['image']
                best[key] = entry
    except Exception:
        pass
    # Merge Defi-only special players (not packable) into the catalog; allow variants
    try:
        from . import defi as _defi
        for s in _defi.get_defi_only_players():
            full = str(s.get('name', '') or '')
            base = _base_name(full)
            key = full or base
            if key and key not in best:
                entry = {
                    'name': full or base,
                    'rating': s.get('rating', 0),
                    'rarity': s.get('rarity', ''),
                    'defi_only': True,
                    'packable': False,
                }
                if 'image' in s:
                    entry['image'] = s['image']
                best[key] = entry
    except Exception:
        pass
    # Merge Season Pass-only players (not packable), allow variants
    try:
        from . import season_pass as _sp
        for s in _sp.get_pass_only_players():
            full = str(s.get('name', '') or '')
            base = _base_name(full)
            key = full or base
            if key and key not in best:
                entry = {
                    'name': full or base,
                    'rating': s.get('rating', 0),
                    'rarity': s.get('rarity', ''),
                    'pass_only': True,
                    'packable': False,
                }
                if 'image' in s:
                    entry['image'] = s['image']
                best[key] = entry
    except Exception:
        pass
    # Merge Daily Rewards-only players (not packable)
    try:
        from . import daily_rewards as _daily
        for s in _daily.get_daily_only_players():
            base = _base_name(s.get('name', ''))
            if base and base not in best:
                entry = {
                    'name': base,
                    'rating': s.get('rating', 0),
                    'rarity': s.get('rarity', ''),
                    'daily_only': True,
                    'packable': False,
                }
                if 'image' in s:
                    entry['image'] = s['image']
                best[base] = entry
    except Exception:
        pass
    return sorted(best.values(), key=lambda x: (-int(x.get('rating', 0)), x['name']))
