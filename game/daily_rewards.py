from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple, Optional, List

from . import xp as xp_mod
from . import db as game_db
from . import wallet as wallet_mod
from . import timeutil as tz


# Persistence file
_STATE_PATH = Path(__file__).resolve().parents[1] / 'data' / 'daily_rewards.json'


def _today_str() -> str:
    # Use Europe/Paris date
    return tz.today_str()


def _read_state() -> Dict:
    if not _STATE_PATH.exists():
        return {
            'last_claim_date': None,   # YYYY-MM-DD
            'day_index': 0,            # 0 means not started; 1..28 active day
            'cycles_completed': 0,
        }
    try:
        with _STATE_PATH.open('r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError('invalid state')
            # defaults
            data.setdefault('last_claim_date', None)
            data.setdefault('day_index', 0)
            data.setdefault('cycles_completed', 0)
            return data
    except Exception:
        return {
            'last_claim_date': None,
            'day_index': 0,
            'cycles_completed': 0,
        }


def _write_state(data: Dict) -> None:
    try:
        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _STATE_PATH.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# Reward configuration for a 28-day cycle
# Types: {'type': 'xp', 'amount': int} or {'type': 'player', 'name': str, 'rating': int, 'image': str}

def _player_reward(name: str, image_abs_path: str, rating: int = 84) -> Dict:
    return {
        'type': 'player',
        'name': name,
        'rating': rating,
        'image': image_abs_path,  # absolute path to png
        # Rareté spécifique demandée
        'rarity': 'Squad fondation',
        # Fond spécifique pour ces récompenses fondations
        'bg_img': str(Path(r"C:\Users\Utilisateur\Desktop\Minefut\Fond\Sbc\fond fondation.png")),
    }


def _rewards_28() -> List[Dict]:
    # Default for unspecified days: +10 XP
    rewards: List[Dict] = [{'type': 'xp', 'amount': 10} for _ in range(28)]
    # Day 1: +25 XP
    rewards[0] = {'type': 'xp', 'amount': 25}
    # XP days (user-specified)
    for d in (8, 15, 22):
        rewards[d - 1] = {'type': 'xp', 'amount': 25}
    for d in (4, 11, 18, 25):
        rewards[d - 1] = {'type': 'xp', 'amount': 50}
    # Coins days
    for d in (2, 9, 16, 23):
        rewards[d - 1] = {'type': 'coins', 'amount': 250}
    for d in (6, 13, 20, 27):
        rewards[d - 1] = {'type': 'coins', 'amount': 500}
    # Day 7: Teun Koopmeiners (84)
    rewards[6] = _player_reward(
        'Teun Koopmeiners',
        r"C:\Users\Utilisateur\Desktop\Minefut\cards\Squad Fondations\Koopmeiners.png",
        84,
    )
    # Day 14: Matteo Ruggeri (84)
    rewards[13] = _player_reward(
        'Matteo Ruggeri',
        r"C:\Users\Utilisateur\Desktop\Minefut\cards\Squad Fondations\Ruggeri.png",
        84,
    )
    # Day 21: Josip Stanisic (84) — filename with diacritics (Stanišić.png)
    rewards[20] = _player_reward(
        'Josip Stanisic',
        r"C:\Users\Utilisateur\Desktop\Minefut\cards\Squad Fondations\Stanišić.png",
        84,
    )
    # Day 28: Wataru Endo (84)
    rewards[27] = _player_reward(
        'Wataru Endo',
        r"C:\Users\Utilisateur\Desktop\Minefut\cards\Squad Fondations\Endo.png",
        84,
    )
    return rewards


def list_cycle_rewards() -> List[Dict]:
    """Expose the 28-day cycle rewards with day numbers for UI.

    Returns a list of 28 dicts: {'day': i, ...reward...}
    """
    out: List[Dict] = []
    for i, r in enumerate(_rewards_28(), start=1):
        it = dict(r)
        it['day'] = i
        out.append(it)
    return out


def get_daily_only_players() -> List[Dict]:
    """Return daily-only special players so they appear in the catalog if missing."""
    rw = _rewards_28()
    out: List[Dict] = []
    for r in rw:
        if r.get('type') == 'player':
            out.append({
                'name': r['name'],
                'rating': r.get('rating', 84),
                'rarity': r.get('rarity', 'squad fondations'),
                'image': r['image'],  # absolute path acceptable (resolution logic supports absolute)
                'daily_only': True,
                'packable': False,
            })
    return out


def _advance_day(prev_day: int, last_claim_date: Optional[str]) -> int:
    """Return the next day index (1..28) given previous state. Resets on missed day."""
    today = tz.today_date()
    if not last_claim_date:
        return 1
    try:
        last = date.fromisoformat(last_claim_date)
    except Exception:
        return 1
    # If claim already today, do not advance here (caller handles) — but function used only when claiming
    if today == last:
        return max(1, min(28, prev_day))
    # If consecutive day (yesterday), continue streak, else reset
    if today - last == timedelta(days=1):
        nxt = prev_day + 1
        if nxt > 28:
            return 1
        return nxt
    # gap or back-in-time: reset
    return 1


def claim_today() -> Tuple[bool, Optional[Dict]]:
    """Attempt to claim today's daily reward.

    Returns (claimed, reward_info). reward_info contains keys including 'type' and 'day'.
    Claimed is False if already claimed today or on error.
    """
    state = _read_state()
    today = _today_str()
    if state.get('last_claim_date') == today:
        return False, None
    # determine which day to claim
    day_to_claim = _advance_day(int(state.get('day_index', 0)), state.get('last_claim_date'))
    rewards = _rewards_28()
    idx = max(1, min(28, day_to_claim)) - 1
    rew = rewards[idx]
    # apply reward
    try:
        if rew.get('type') == 'xp':
            amt = int(rew.get('amount', 0))
            if amt > 0:
                xp_mod.add_xp(amt)
        elif rew.get('type') == 'coins':
            amt = int(rew.get('amount', 0))
            if amt > 0:
                wallet_mod.add_coins(amt)
        elif rew.get('type') == 'player':
            name = str(rew.get('name', ''))
            if name:
                # add to collection by base name
                game_db.add_to_collection_by_names([name])
        # update state
        new_day_index = day_to_claim
        cycles = int(state.get('cycles_completed', 0))
        if new_day_index >= 28:
            # next time will reset to day 1 and increment cycles
            state['day_index'] = 28
            state['cycles_completed'] = cycles
        else:
            state['day_index'] = new_day_index
        state['last_claim_date'] = today
        _write_state(state)
        info = dict(rew)
        info['day'] = day_to_claim
        return True, info
    except Exception:
        return False, None


def get_status() -> Dict:
    """Return a summary of the daily reward status for UI/debug."""
    s = _read_state()
    return {
        'last_claim_date': s.get('last_claim_date'),
        'day_index': int(s.get('day_index', 0)),
        'cycles_completed': int(s.get('cycles_completed', 0)),
        'today': _today_str(),
    }
