from __future__ import annotations

from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'


RESET_FILES: List[str] = [
    'collection.json',
    'profile.json',
    'wallet.json',
    'sbc_progress.json',
    'defi_progress.json',
    'season_pass_progress.json',
    'daily_rewards.json',
]


def reset_all_progress() -> Dict[str, bool]:
    """Delete all progress/save files so the game restarts from a fresh state.

    We intentionally do not touch static content like players.json, players images,
    or settings.json. Modules will recreate missing files with their defaults.

    Returns a dict mapping filename -> success flag for deletion.
    """
    results: Dict[str, bool] = {}
    for name in RESET_FILES:
        try:
            p = DATA_DIR / name
            if p.exists():
                p.unlink()
            results[name] = True
        except Exception:
            results[name] = False
    return results
