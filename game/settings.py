import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / 'data' / 'settings.json'

DEFAULTS = {
    'ui_revamp': True,
    'width': 1920,
    'height': 1080,
    'fullscreen': False,
    'volume': 80,
    'effects_quality': 'medium',  # low | medium | high
    'show_fps': False,
    'language': 'fr',
}


def _merge(a: dict, b: dict) -> dict:
    out = dict(a)
    out.update({k: v for k, v in b.items() if v is not None})
    return out


def load_settings() -> dict:
    if not DATA_FILE.exists():
        return dict(DEFAULTS)
    try:
        with DATA_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {}
    # normalize values
    if data.get('effects_quality') not in ('low', 'medium', 'high'):
        data['effects_quality'] = DEFAULTS['effects_quality']
    if not isinstance(data.get('width'), int) or not isinstance(data.get('height'), int):
        data['width'], data['height'] = DEFAULTS['width'], DEFAULTS['height']
    return _merge(DEFAULTS, data)


def save_settings(settings: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = _merge(DEFAULTS, settings or {})
    with DATA_FILE.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
