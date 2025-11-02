from __future__ import annotations

from datetime import datetime, date, timedelta
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None  # type: ignore

# Fixed game timezone: Europe/Paris
_TZ = None
if ZoneInfo is not None:
    try:
        _TZ = ZoneInfo("Europe/Paris")
    except Exception:
        _TZ = None


def now() -> datetime:
    """Timezone-aware 'now' in Europe/Paris.

    Falls back to naive localtime if ZoneInfo is unavailable.
    """
    if _TZ is not None:
        return datetime.now(_TZ)
    # Fallback: best effort local time
    return datetime.now()


def today_date() -> date:
    """Today's date in Europe/Paris timezone."""
    return now().date()


def today_str() -> str:
    """Today's date ISO string (YYYY-MM-DD) in Europe/Paris timezone."""
    return today_date().isoformat()


def current_cycle_date(reset_hour: int = 19) -> date:
    """Return the date representing the current daily cycle anchored at reset_hour.

    Example: with reset_hour=19 (7pm Paris), any time before 19:00 belongs to
    the previous cycle date; time at/after 19:00 belongs to today.
    """
    n = now()
    try:
        rh = int(reset_hour)
    except Exception:
        rh = 19
    if n.hour < max(0, min(23, rh)):
        return (n.date() - timedelta(days=1))
    return n.date()


def current_cycle_key(reset_hour: int = 19) -> str:
    """String key for the current daily cycle (YYYY-MM-DD) with boundary at reset_hour."""
    return current_cycle_date(reset_hour).isoformat()
