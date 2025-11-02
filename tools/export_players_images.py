import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYERS_FILE = ROOT / 'data' / 'players.json'
AVATARS_DIR = ROOT / 'data' / 'avatars'
MAP_FILE = AVATARS_DIR / 'map.json'
OUTPUT_FILE = ROOT / 'data' / 'players_images.json'


def strip_accents(s: str) -> str:
    try:
        return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    except Exception:
        return s


def name_variants(base_name: str) -> list[str]:
    base = base_name or ''
    cand = set()
    for b in (base, base.replace('.', ''), base.replace("'", '')):
        for v in (b, strip_accents(b)):
            v = v.strip()
            if not v:
                continue
            vl = v.lower()
            cand.add(vl)
            cand.add(vl.replace(' ', '_'))
            cand.add(vl.replace(' ', ''))
            cand.add(vl.replace('-', '_'))
            cand.add(vl.replace('-', ''))
    return list(cand)


def rarity_folder_aliases(rarity: str) -> list[str]:
    rl = (rarity or '').lower()
    aliases = [rl]
    if rl == 'rare':
        aliases += ['or rare', 'or_rare', 'or-rare', 'gold rare', 'gold_rare', 'rare gold', 'rare_gold']
    elif rl == 'common':
        aliases += ['common_gold', 'gold common', 'or commun', 'commun', 'gold', 'or']
    elif rl == 'epic':
        aliases += ['epique', 'épic']
    elif rl == 'legendary':
        aliases += ['legendaire', 'légendaire', 'legend']
    elif rl == 'otw':
        aliases += ['ones_to_watch', 'otw']
    # normalize alias variations
    out = []
    for a in aliases:
        for v in (a, a.replace(' ', '_'), a.replace(' ', ''), a.replace('-', '_')):
            vl = v.lower()
            if vl and vl not in out:
                out.append(vl)
    return out


def find_png_in_rarity_dirs(base_name: str, rarity: str) -> str | None:
    if not base_name:
        return None
    name_vars = name_variants(base_name)
    folders = rarity_folder_aliases(rarity)
    for folder in folders:
        for nv in name_vars:
            candidate = AVATARS_DIR / folder / f"{nv}.png"
            if candidate.exists():
                return f"data/avatars/{folder}/{candidate.name}"
    return None


def guess_png_in_root(base_name: str) -> str | None:
    if not base_name:
        return None
    for nv in name_variants(base_name):
        candidate = AVATARS_DIR / f"{nv}.png"
        if candidate.exists():
            return f"data/avatars/{candidate.name}"
    return None


def resolve_png(name: str, rarity: str, mapping: dict | None) -> str | None:
    base = (name or '').split('#')[0].strip()
    # 1) mapping lookup limited to PNG
    if mapping and base in mapping:
        rel = mapping[base]
        if rel.lower().endswith('.png'):
            p = AVATARS_DIR / rel
            if p.exists():
                return f"data/avatars/{rel}"
        else:
            # try png variant for same base name
            png_guess = (AVATARS_DIR / (Path(rel).stem + '.png'))
            if png_guess.exists():
                return f"data/avatars/{png_guess.name}"
    # 2) rarity subfolders
    rel = find_png_in_rarity_dirs(base, rarity or '')
    if rel:
        return rel
    # 3) root avatars
    return guess_png_in_root(base)


def main():
    players_data = []
    if PLAYERS_FILE.exists():
        with PLAYERS_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
            players_data = data.get('players', [])
    mapping = None
    if MAP_FILE.exists():
        try:
            with MAP_FILE.open('r', encoding='utf-8') as f:
                data = json.load(f)
                mapping = data if isinstance(data, dict) else None
        except Exception:
            mapping = None

    out = []
    for p in players_data:
        pid = p.get('id')
        name = p.get('name', '')
        rating = p.get('rating', 0)
        rarity = p.get('rarity', 'Common')
        # prefer existing image if it ends with .png and exists
        image = p.get('image')
        resolved_png = None
        if image and image.lower().endswith('.png'):
            ap = ROOT / image
            if ap.exists():
                resolved_png = image
        if not resolved_png:
            resolved_png = resolve_png(name, rarity, mapping)
        out.append({
            'id': pid,
            'name': name,
            'rating': rating,
            'rarity': rarity,
            'image_png': resolved_png
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open('w', encoding='utf-8') as f:
        json.dump({'players': out}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUTPUT_FILE} with {len(out)} entries.")


if __name__ == '__main__':
    main()
