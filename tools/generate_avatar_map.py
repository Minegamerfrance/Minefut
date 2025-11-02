from __future__ import annotations
import json
import re
import unicodedata
from pathlib import Path

# This script scans data/avatars for image files and matches them to player names
# in data/players.json, then writes/merges data/avatars/map.json and updates players
# that don't have an image yet.

IMAGE_EXTS = {'.png', '.jpg', '.jpeg'}


def normalize(s: str) -> str:
    if not s:
        return ''
    # remove accents
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    # lowercase and strip punctuation/whitespace-like separators
    s = s.lower()
    s = s.replace('#', ' ')
    s = re.sub(r"[\s\-_\.\'\"]+", '', s)
    return s


def load_players(players_path: Path) -> list[dict]:
    if not players_path.exists():
        return []
    with players_path.open('r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def save_players(players_path: Path, players: list[dict]) -> None:
    players_path.parent.mkdir(parents=True, exist_ok=True)
    with players_path.open('w', encoding='utf-8') as f:
        json.dump(players, f, ensure_ascii=False, indent=2)


def main() -> int:
    # Resolve project root as parent of this file's directory
    root = Path(__file__).resolve().parents[1]
    data_dir = root / 'data'
    avatars_dir = data_dir / 'avatars'
    players_path = data_dir / 'players.json'
    map_path = avatars_dir / 'map.json'

    avatars_dir.mkdir(parents=True, exist_ok=True)

    # Load players and existing map
    players = load_players(players_path)
    try:
        existing_map: dict[str, str] = {}
        if map_path.exists():
            with map_path.open('r', encoding='utf-8') as f:
                m = json.load(f)
                if isinstance(m, dict):
                    existing_map = {str(k): str(v) for k, v in m.items()}
    except Exception:
        existing_map = {}

    # Index images by normalized filename base
    files = [p for p in avatars_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS and p.name != '_placeholder.png']
    norm_to_filename: dict[str, str] = {}
    for fp in files:
        base = fp.stem
        norm = normalize(base)
        if norm:
            # Prefer png over jpg if duplicates
            if norm in norm_to_filename:
                prev = norm_to_filename[norm]
                # keep png if new is png or if prev isn't png
                if fp.suffix.lower() == '.png' and not prev.lower().endswith('.png'):
                    norm_to_filename[norm] = fp.name
            else:
                norm_to_filename[norm] = fp.name

    # Build new mappings for players without one in existing map
    new_map: dict[str, str] = {}
    assigned = 0
    for p in players:
        base_name = str(p.get('name', '')).split('#')[0].strip()
        if not base_name:
            continue
        if base_name in existing_map:
            # already mapped
            continue
        n = normalize(base_name)
        if not n:
            continue
        fn = norm_to_filename.get(n)
        if fn:
            new_map[base_name] = fn
            assigned += 1

    # Merge maps (existing wins on conflict)
    merged = dict(new_map)
    merged.update(existing_map)

    # Write map
    try:
        with map_path.open('w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to write map.json: {e}")
        return 1

    # Update players without image using merged map
    updated_players = False
    for p in players:
        if p.get('image'):
            continue
        base_name = str(p.get('name', '')).split('#')[0].strip()
        if base_name in merged:
            p['image'] = f"data/avatars/{merged[base_name]}"
            updated_players = True

    if updated_players:
        save_players(players_path, players)

    print(f"Avatar map generated: {len(merged)} entries (new: {len(new_map)}). Players updated: {int(updated_players)}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
