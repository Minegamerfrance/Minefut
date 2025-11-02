from __future__ import annotations

import json
from datetime import timedelta, datetime
from pathlib import Path
from typing import Tuple

from . import timeutil as tz

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / 'data' / 'timers.json'


def _load() -> dict:
    try:
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {"events": {}}


def _save(d: dict) -> None:
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


def _dt_to_iso(dt: datetime) -> str:
    try:
        # serialize aware datetime as ISO
        return dt.isoformat()
    except Exception:
        return tz.now().isoformat()


def _iso_to_dt(s: str) -> datetime:
    try:
        # datetime.fromisoformat preserves tzinfo
        return datetime.fromisoformat(str(s))
    except Exception:
        # fallback: now
        return tz.now()


def ensure_timer(key: str, days: int) -> datetime:
    """Ensure a timer exists for the given key with the specified duration.

    Returns the end datetime for this timer. If the timer already exists, it's
    not modified; if not, it is created with end = now + days.
    """
    d = _load()
    ev = d.setdefault('events', {})
    rec = ev.get(key)
    if not rec:
        end = tz.now() + timedelta(days=max(0, int(days)))
        ev[key] = {"end": _dt_to_iso(end), "days": int(days)}
        _save(d)
        return end
    try:
        return _iso_to_dt(rec.get('end', tz.now().isoformat()))
    except Exception:
        return tz.now()


def remaining_seconds(key: str, days: int) -> int:
    end = ensure_timer(key, days)
    now = tz.now()
    delta = (end - now).total_seconds()
    return int(delta) if delta > 0 else 0


def is_expired(key: str, days: int) -> bool:
    return remaining_seconds(key, days) <= 0


def format_remaining(secs: int) -> str:
    """Format remaining time as a compact French label like '3j 12h 05m' or '02:15:07'."""
    if secs <= 0:
        return 'Expiré'
    d = secs // 86400
    h = (secs % 86400) // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    if d > 0:
        return f"{d}j {h}h {m:02d}m"
    return f"{h:02d}:{m:02d}:{s:02d}"
