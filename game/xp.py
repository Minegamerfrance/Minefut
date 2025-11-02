import json
from pathlib import Path
from typing import Dict, Tuple

_PROFILE_PATH = Path(__file__).resolve().parents[1] / 'data' / 'profile.json'
_DEFAULT = {"xp": 0}


def _read() -> Dict:
    if not _PROFILE_PATH.exists():
        return dict(_DEFAULT)
    try:
        with _PROFILE_PATH.open('r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return dict(_DEFAULT)
        if 'xp' not in data or not isinstance(data['xp'], int):
            data['xp'] = _DEFAULT['xp']
        return data
    except Exception:
        return dict(_DEFAULT)


def _write(data: Dict) -> None:
    try:
        _PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _PROFILE_PATH.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_xp() -> int:
    return int(_read().get('xp', _DEFAULT['xp']))


def get_name(default: str = 'Joueur') -> str:
    """Return the profile display name (pseudo)."""
    try:
        data = _read()
        name = str(data.get('name', '') or '').strip()
        return name if name else default
    except Exception:
        return default


def set_name(name: str) -> str:
    """Persist the profile display name and return it. Caps length to 20 chars."""
    try:
        nm = (name or '').strip()
        if len(nm) > 20:
            nm = nm[:20]
        data = _read()
        data['name'] = nm if nm else 'Joueur'
        _write(data)
        return data['name']
    except Exception:
        return 'Joueur'


def add_xp(amount: int) -> int:
    if amount <= 0:
        return get_xp()
    data = _read()
    data['xp'] = int(data.get('xp', 0)) + int(amount)
    _write(data)
    return data['xp']


def _level_from_xp(xp: int) -> int:
    # Simple leveling: each level requires 100 XP
    # Level 1: 0-99, Level 2: 100-199, ...
    return max(1, (xp // 100) + 1)


def get_level() -> int:
    return _level_from_xp(get_xp())


def get_level_progress() -> Tuple[int, int, int]:
    """Return (level, current_in_level, needed_for_next)."""
    xp = get_xp()
    level = _level_from_xp(xp)
    cur = xp % 100
    need = 100
    return level, cur, need
