import json
from pathlib import Path
from typing import Dict

_WALLET_PATH = Path(__file__).resolve().parents[1] / 'data' / 'wallet.json'
_DEFAULT = {"minecoins": 500}


def _read() -> Dict:
    if not _WALLET_PATH.exists():
        return dict(_DEFAULT)
    try:
        with _WALLET_PATH.open('r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return dict(_DEFAULT)
        if 'minecoins' not in data or not isinstance(data['minecoins'], int):
            data['minecoins'] = _DEFAULT['minecoins']
        return data
    except Exception:
        return dict(_DEFAULT)


def _write(data: Dict) -> None:
    try:
        _WALLET_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _WALLET_PATH.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_balance() -> int:
    return int(_read().get('minecoins', _DEFAULT['minecoins']))


def set_balance(amount: int) -> int:
    data = _read()
    data['minecoins'] = max(0, int(amount))
    _write(data)
    return data['minecoins']


def add_coins(amount: int) -> int:
    if amount <= 0:
        return get_balance()
    data = _read()
    data['minecoins'] = int(data.get('minecoins', _DEFAULT['minecoins'])) + int(amount)
    _write(data)
    return data['minecoins']


def spend_coins(amount: int) -> bool:
    """Attempt to spend amount of Minecoins. Returns True if success, False if insufficient."""
    if amount <= 0:
        return True
    data = _read()
    bal = int(data.get('minecoins', _DEFAULT['minecoins']))
    if bal < amount:
        return False
    data['minecoins'] = bal - amount
    _write(data)
    return True
