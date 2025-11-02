from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import db as game_db

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / 'data' / 'season_pass_progress.json'

 

@dataclass(frozen=True)
class PassReward:
    level: int
    kind: str  # 'card' | 'coins' | 'xp' | 'unlock'
    # For kind == 'card'
    name: Optional[str] = None
    rarity: Optional[str] = None
    # Visuals
    bg_img: Optional[str] = None
    card_img: Optional[str] = None
    # For kind in {'coins', 'xp'}
    amount: int = 0
    # For kind == 'unlock'
    unlock_pass_id: Optional[str] = None
    unlock_feature: Optional[str] = None  # e.g., 'sbc', 'defi'


# --- Multi-pass support ---
# Configure Season Pass rewards for the Halloween season
HALLOWEEN_REWARDS: Dict[int, PassReward] = {
    1: PassReward(level=1, kind='xp', amount=50),
    2: PassReward(level=2, kind='coins', amount=200),
    3: PassReward(level=3, kind='xp', amount=100),
    4: PassReward(level=4, kind='coins', amount=250),
    5: PassReward(
        level=5,
        kind='card',
        name='Guéla Doué',
        rarity='or rare',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Joueur\\fond ultimate scream.png")),
        card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Joueur\\Guéla Doué.png")),
    ),
    6: PassReward(level=6, kind='xp', amount=150),
    7: PassReward(level=7, kind='coins', amount=300),
    8: PassReward(level=8, kind='xp', amount=150),
    9: PassReward(level=9, kind='coins', amount=400),
    10: PassReward(
        level=10,
        kind='card',
        name='Paul Pogba',
        rarity='or rare',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Joueur\\fond ultimate scream.png")),
        card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Joueur\\Pogba_cam.png")),
    ),
    11: PassReward(level=11, kind='xp', amount=200),
    12: PassReward(level=12, kind='coins', amount=550),
    13: PassReward(level=13, kind='xp', amount=250),
    14: PassReward(level=14, kind='coins', amount=600),
    15: PassReward(
        level=15,
        kind='card',
        name='Peter Crouch',
        rarity='hero',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png")),
        card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Héro\\Crouch.png")),
    ),
    16: PassReward(level=16, kind='coins', amount=650),
    17: PassReward(level=17, kind='xp', amount=350),
    18: PassReward(level=18, kind='coins', amount=700),
    19: PassReward(level=19, kind='xp', amount=400),
    20: PassReward(
        level=20,
        kind='card',
        name='Xabi Alonso',
        rarity='icon',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Icon\\fond icon ultimate scream.png")),
        card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Icon\\Xabi Alonso.png")),
    ),
    21: PassReward(level=21, kind='xp', amount=450),
    22: PassReward(level=22, kind='coins', amount=800),
    23: PassReward(level=23, kind='xp', amount=500),
    24: PassReward(level=24, kind='coins', amount=850),
    25: PassReward(
        level=25,
        kind='card',
        name='Bryan Mbeumo',
        rarity='or rare',
        card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Joueur\\Bryan Mbeumo.png")),
    ),
    26: PassReward(level=26, kind='coins', amount=900),
    27: PassReward(level=27, kind='xp', amount=600),
    28: PassReward(level=28, kind='coins', amount=950),
    29: PassReward(level=29, kind='xp', amount=650),
    30: PassReward(
        level=30,
        kind='card',
        name='Ribéry',
        rarity='icon',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Icon\\fond icon ultimate scream.png")),
        card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Icon\\Ribéry.png")),
    ),
}

# Unlock next season at level 41 in the Season 2 pass
# Now points to Season 3: "Un bon en arrière" (retro)
HALLOWEEN_REWARDS[41] = PassReward(
    level=41,
    kind='unlock',
    unlock_pass_id='retro',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Icon\\fond icon ultimate scream.png")),
)

# New pass: Lancement (basic starter rewards)
LAUNCH_REWARDS: Dict[int, PassReward] = {
    1: PassReward(level=1, kind='unlock', unlock_feature='defi'),
    2: PassReward(level=2, kind='unlock', unlock_feature='draft'),
    3: PassReward(level=3, kind='unlock', unlock_feature='sbc'),
    4: PassReward(level=4, kind='coins', amount=200),
    5: PassReward(level=5, kind='xp', amount=150),
    6: PassReward(level=6, kind='coins', amount=250),
    7: PassReward(level=7, kind='xp', amount=200),
    8: PassReward(level=8, kind='coins', amount=300),
    9: PassReward(level=9, kind='xp', amount=250),
    10: PassReward(
        level=10,
        kind='card',
        name='Diego Chará',
        rarity='or rare',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond cornestornes.png")),
        card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Cornerstones\\Diego Chará.png")),
    ),
}

# Extend Lancement to 41 levels (11-40 basic rewards, 41 unlocks Halloween)
for lvl in range(11, 41):
    if lvl == 41:
        break
    # alternate xp/coins, gradually increasing
    if lvl % 2 == 1:
        LAUNCH_REWARDS[lvl] = PassReward(level=lvl, kind='xp', amount=200 + (lvl - 11) * 20)
    else:
        LAUNCH_REWARDS[lvl] = PassReward(level=lvl, kind='coins', amount=500 + (lvl - 10) * 50)

# Override specific levels with card rewards as requested
LAUNCH_REWARDS[15] = PassReward(
    level=15,
    kind='card',
    name='Jakub Kamiński',
    rarity='or rare',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\rating reload\\fond rating reload.png")),
    card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ratings Reload\\Jakub Kamiński.png")),
)

LAUNCH_REWARDS[25] = PassReward(
    level=25,
    kind='card',
    name='Ricardo Quaresma',
    rarity='hero',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png")),
    card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Hero\\Ricardo Quaresma.png")),
)

# New unlocks: SBC Hero at 26, Icons at 36
LAUNCH_REWARDS[26] = PassReward(
    level=26,
    kind='unlock',
    unlock_feature='sbc_hero',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\défi\\héro.png")),
)

LAUNCH_REWARDS[30] = PassReward(
    level=30,
    kind='card',
    name='João Neves',
    rarity='or rare',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond cornestornes.png")),
    card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Cornerstones\\João Neves.png")),
)

LAUNCH_REWARDS[35] = PassReward(
    level=35,
    kind='card',
    name='Cha Bum Kun',
    rarity='icon',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon\\fond icone.png")),
    card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Icon\\Cha Bum Kun.png")),
)

LAUNCH_REWARDS[36] = PassReward(
    level=36,
    kind='unlock',
    unlock_feature='sbc_icon',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\défi\\icon.png")),
)

LAUNCH_REWARDS[40] = PassReward(
    level=40,
    kind='card',
    name='Heung Min Son',
    rarity='or rare',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\rating reload\\fond rating reload.png")),
    card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ratings Reload\\Heung Min Son.png")),
)

# Level 41: unlock Halloween season
LAUNCH_REWARDS[41] = PassReward(
    level=41,
    kind='unlock',
    unlock_pass_id='halloween',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Joueur\\fond ultimate scream.png")),
)

# Additional card overrides
LAUNCH_REWARDS[5] = PassReward(
    level=5,
    kind='card',
    name='Carney Chukwuemeka',
    rarity='or rare',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond world tour.png")),
    card_img=str(Path("cards/World Tour/Carney Chukwuemeka.png")),
)

LAUNCH_REWARDS[20] = PassReward(
    level=20,
    kind='card',
    name='James Ward-Prowse',
    rarity='or rare',
    bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond world tour.png")),
    card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\World Tour\\James Ward-Prowse.png")),
)

# Map pass id -> rewards (order doesn't matter for storage; UI sorts by display name)
PASSES: Dict[str, Dict[int, PassReward]] = {
    'launch': LAUNCH_REWARDS,
    'halloween': HALLOWEEN_REWARDS,
    # Season 3: Un bon en arrière (retro theme) — basic progression, unlocks Futmas at 41
    'retro': {
        # simple alternating XP/Coins up to 40
        **{lvl: PassReward(level=lvl, kind=('xp' if lvl % 2 == 1 else 'coins'), amount=(200 + (lvl * 10) if lvl % 2 == 1 else 500 + (lvl * 20))) for lvl in range(1, 41)},
        # Level 41: unlock Futmas (Season 4)
        41: PassReward(level=41, kind='unlock', unlock_pass_id='futmas')
    },
    # Season 4: Futmas (locked until Season 3 level 41)
    'futmas': {},
}

# Display names for passes
PASS_NAMES: Dict[str, str] = {
    'launch': 'Saison 1 : Lancement',
    'halloween': 'Saison 2 : Ultimate Scream',
    'retro': 'Saison 3 : Un bon en arrière',
    'futmas': 'Saison 4 : Futmas',
}


def _ensure_file():
    if not DATA_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(
            json.dumps({'active': 'launch', 'claimed': {}, 'unlocked': ['launch'], 'features': {'sbc': False, 'defi': False, 'draft': False, 'sbc_hero': False, 'sbc_icon': False}, 'start_xp': {}, 'frozen_xp': {}}, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )


def _load() -> Dict:
    _ensure_file()
    try:
        with DATA_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
            # Back-compat: if claimed is a list, wrap it under 'halloween'
            if isinstance(data.get('claimed'), list):
                data = {
                    'active': data.get('active', 'launch'),
                    'claimed': {'halloween': list(data.get('claimed', []))},
                }
            if 'active' not in data:
                data['active'] = 'launch'
            if 'claimed' not in data or not isinstance(data['claimed'], dict):
                data['claimed'] = {}
            # Introduce unlocked pass list
            if 'unlocked' not in data or not isinstance(data['unlocked'], list):
                data['unlocked'] = ['launch']
            # Introduce features dictionary
            if 'features' not in data or not isinstance(data['features'], dict):
                data['features'] = {'sbc': False, 'defi': False, 'draft': False, 'sbc_hero': False, 'sbc_icon': False}
            else:
                data['features'].setdefault('sbc', False)
                data['features'].setdefault('defi', False)
                data['features'].setdefault('draft', False)
                data['features'].setdefault('sbc_hero', False)
                data['features'].setdefault('sbc_icon', False)
            # Per-pass XP baseline so levels reset when switching seasons
            if 'start_xp' not in data or not isinstance(data['start_xp'], dict):
                data['start_xp'] = {}
            # Frozen per-pass XP deltas for inactive passes (so progress doesn't move when inactive)
            if 'frozen_xp' not in data or not isinstance(data['frozen_xp'], dict):
                data['frozen_xp'] = {}
            # Guard: ensure active is an unlocked pass
            if data.get('active') not in data['unlocked']:
                data['active'] = 'launch'
            return data
    except Exception:
        return {'active': 'launch', 'claimed': {}, 'unlocked': ['launch'], 'features': {'sbc': False, 'defi': False}, 'start_xp': {}}


def _save(d: Dict):
    try:
        DATA_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


def get_active_pass_id() -> str:
    d = _load()
    aid = d.get('active') or 'launch'
    if aid not in PASSES or aid not in set(d.get('unlocked', [])):
        aid = 'launch'
    return aid


def get_active_pass_name() -> str:
    pid = get_active_pass_id()
    return PASS_NAMES.get(pid, pid)


def list_passes() -> List[Tuple[str, str]]:
    """Return list of available passes as (id, displayName)."""
    out: List[Tuple[str, str]] = []
    d = _load()
    unlocked = set(d.get('unlocked', []))
    for pid, name in PASS_NAMES.items():
        if pid in unlocked:
            out.append((pid, name))
    # stable order: by display name then id
    out.sort(key=lambda x: (str(x[1]).lower(), str(x[0]).lower()))
    return out


def set_active_pass(pass_id: str) -> bool:
    """Set the active pass if it exists. Returns True if changed/applied."""
    d = _load()
    if pass_id not in PASSES or pass_id not in set(d.get('unlocked', [])):
        return False
    if d.get('active') == pass_id:
        return True
    # Freeze outgoing pass progress so it doesn't keep moving when inactive
    try:
        from . import xp as _xp
        gxp = int(_xp.get_xp())
    except Exception:
        gxp = 0
    baselines = d.get('start_xp') if isinstance(d.get('start_xp'), dict) else {}
    frozen = d.get('frozen_xp') if isinstance(d.get('frozen_xp'), dict) else {}
    old = d.get('active')
    if old and old in PASSES:
        base_old = int(baselines.get(old, gxp))
        delta_old = max(0, gxp - base_old)
        frozen[old] = int(delta_old)
    # Switch active
    d['active'] = pass_id
    # Initialize or realign baseline for the new active pass to preserve its stored delta
    if pass_id not in baselines:
        baselines[pass_id] = gxp
    # If there is a frozen delta for the new pass, realign baseline so live delta matches it
    if pass_id in frozen:
        baselines[pass_id] = max(0, gxp - int(frozen[pass_id]))
        # unfreeze when it becomes active
        try:
            del frozen[pass_id]
        except Exception:
            pass
    d['start_xp'] = baselines
    d['frozen_xp'] = frozen
    _save(d)
    return True


def list_rewards(pass_id: Optional[str] = None) -> List[PassReward]:
    pid = pass_id or get_active_pass_id()
    rewards = PASSES.get(pid, {})
    return [rewards[k] for k in sorted(rewards.keys())]


def get_relative_level_progress(pass_id: Optional[str] = None) -> Tuple[int, int, int]:
    """Return (level, current_in_level, needed_for_next) relative to the active pass baseline.

    Each time a pass becomes active, we snapshot the current global XP as the start_xp
    for that pass. The displayed level is then computed from (global_xp - start_xp),
    effectively resetting the level to 1 when switching seasons.
    Inactive passes use a frozen delta captured when they were deactivated, so their
    progress does not move while inactive.
    """
    # read data and ensure baseline for the pass
    d = _load()
    pid = pass_id or (d.get('active') or 'launch')
    active = d.get('active') or 'launch'
    try:
        from . import xp as _xp
        gxp = int(_xp.get_xp())
    except Exception:
        gxp = 0
    baselines = d.get('start_xp') if isinstance(d.get('start_xp'), dict) else {}
    frozen = d.get('frozen_xp') if isinstance(d.get('frozen_xp'), dict) else {}
    # Active pass: live progress from baseline, initializing baseline if needed
    if pid == active:
        if pid not in baselines:
            baselines[pid] = gxp
            d['start_xp'] = baselines
            _save(d)
        delta = max(0, gxp - int(baselines.get(pid, 0)))
    else:
        # Inactive: use frozen snapshot; if missing, default to 0 (not started)
        delta = max(0, int(frozen.get(pid, 0)))
    # same leveling curve as xp.py: 100 XP per level
    level = max(1, (delta // 100) + 1)
    cur = delta % 100
    need = 100
    return level, cur, need


def is_claimed(level: int, pass_id: Optional[str] = None) -> bool:
    d = _load()
    pid = pass_id or get_active_pass_id()
    cl = set(int(x) for x in d.get('claimed', {}).get(pid, []))
    return int(level) in cl


def can_claim(level: int, current_level: int, pass_id: Optional[str] = None) -> bool:
    pid = pass_id or get_active_pass_id()
    rewards = PASSES.get(pid, {})
    return (level <= current_level) and (not is_claimed(level, pid)) and (level in rewards)


def claim(level: int, pass_id: Optional[str] = None) -> bool:
    pid = pass_id or get_active_pass_id()
    rewards = PASSES.get(pid, {})
    if level not in rewards:
        return False
    d = _load()
    already = set(int(x) for x in d.get('claimed', {}).get(pid, []))
    if int(level) in already:
        return False
    reward = rewards[level]
    if reward.kind == 'card' and reward.name:
        try:
            game_db.add_to_collection_by_names([reward.name])
        except Exception:
            pass
    elif reward.kind == 'coins':
        try:
            from . import wallet
            wallet.add_coins(max(0, reward.amount))
        except Exception:
            pass
    elif reward.kind == 'xp':
        try:
            from . import xp
            xp.add_xp(max(0, reward.amount))
        except Exception:
            pass
    elif reward.kind == 'unlock':
        # Unlock a pass
        if reward.unlock_pass_id:
            target = reward.unlock_pass_id
            if target in PASSES:
                unlocked = set(d.get('unlocked', []))
                unlocked.add(target)
                d['unlocked'] = sorted(unlocked)
        # Unlock a feature
        if reward.unlock_feature:
            feats = d.get('features') if isinstance(d.get('features'), dict) else {}
            feats[reward.unlock_feature] = True
            d['features'] = feats
    # mark claimed
    cl = set(int(x) for x in d.get('claimed', {}).get(pid, []))
    cl.add(int(level))
    if 'claimed' not in d or not isinstance(d['claimed'], dict):
        d['claimed'] = {}
    d['claimed'][pid] = sorted(list(cl))
    _save(d)
    return True


def get_pass_only_players() -> List[Dict]:
    """Players that are obtainable only via Season Pass (not packable)."""
    out: List[Dict] = []
    # Provide catalog entries for card rewards across all passes
    for rewards in PASSES.values():
        for r in rewards.values():
            if r.kind == 'card' and r.name and r.rarity:
                nl = r.name.lower()
                if nl == 'xabi alonso':
                    rating = 88
                elif nl in ('ribéry', 'ribery'):
                    rating = 89
                elif nl == 'paul pogba':
                    rating = 86
                elif nl == 'peter crouch':
                    rating = 87
                elif nl == 'bryan mbeumo':
                    rating = 87
                elif nl in ('diego chará', 'diego chara'):
                    rating = 83
                elif nl in ('heung min son',):
                    rating = 88
                elif nl in ('joão neves', 'joao neves'):
                    rating = 86
                elif nl in ('jakub kamiński', 'jakub kaminski'):
                    rating = 83
                elif nl in ('cha bum kun', 'cha-bum kun', 'cha bum-keun'):
                    rating = 86
                elif nl in ('guéla doué', 'guela doue'):
                    rating = 84
                elif nl in ('quaresma', 'ricardo quaresma'):
                    rating = 85
                elif nl in ('carney chukwuemeka', 'chukwuemeka'):
                    rating = 84
                elif nl in ('james ward-prowse', 'ward-prowse', 'james ward prowse'):
                    rating = 84
                else:
                    rating = 90
                # For Pogba, expose a distinct variant name so Collection lists CAM separately
                disp_name = r.name
                if r.name and r.name.lower() == 'paul pogba':
                    disp_name = 'Paul Pogba#pass'
                entry = {
                    'name': disp_name,
                    'rating': rating,
                    'rarity': r.rarity,
                }
                # include image if provided on the reward to help catalog visuals
                if r.card_img:
                    entry['image'] = str(r.card_img)
                out.append(entry)
    return out


# ---- Feature flags API ----
def is_feature_unlocked(feature: str) -> bool:
    try:
        d = _load()
        feats = d.get('features') if isinstance(d.get('features'), dict) else {}
        return bool(feats.get(feature, False))
    except Exception:
        return False


# ---- Pass listing including locked ----
def list_all_passes() -> List[Tuple[str, str, bool]]:
    """Return list of all passes as (id, displayName, unlocked_flag)."""
    d = _load()
    unlocked = set(d.get('unlocked', []))
    out: List[Tuple[str, str, bool]] = []
    for pid, name in PASS_NAMES.items():
        out.append((pid, name, pid in unlocked))
    # stable order by display name, then id
    out.sort(key=lambda x: (str(x[1]).lower(), str(x[0]).lower()))
    return out


def get_unlock_hint(pass_id: str) -> str:
    """If a pass is locked, return a short hint on how to unlock it.

    Searches all PASSES for an unlock reward pointing to pass_id and reports the source.
    """
    try:
        for src_id, rewards in PASSES.items():
            for lvl, r in rewards.items():
                if r.kind == 'unlock' and r.unlock_pass_id == pass_id:
                    src_name = PASS_NAMES.get(src_id, src_id)
                    return f"Débloqué au Niv {lvl} — {src_name}"
        return 'Débloqué via Pass'
    except Exception:
        return 'Débloqué via Pass'
