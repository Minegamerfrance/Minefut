from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import wallet
from . import xp
from . import db as game_db
from . import season_pass as sp_mod
from . import timeutil as tz

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / 'data' / 'defi_progress.json'


@dataclass(frozen=True)
class Defi:
    id: str
    name: str
    description: str
    event_key: str
    target: int
    reward: Tuple[str, int]  # ('coins'|'xp', amount)
    group: str = 'Quotidien'
    bg_img: Optional[str] = None  # optional background image path
    card_img: Optional[str] = None  # optional card image path
    # optionally grant a special card directly to the collection when claimed
    grant_card_name: Optional[str] = None
    grant_card_rarity: Optional[str] = None


# Static catalog of challenges
DEFI_LIST: List[Defi] = [
    # Quotidien (reset chaque jour à 19h heure de Paris)
    Defi('daily_spend_1500', 'Dépenser 1500 Minecoins', 'Dépense 1500 Minecoins aujourd\'hui.', 'daily:coins_spent', 1500, ('xp', 10), 'Quotidien'),
    Defi('daily_complete_1_sbc', 'Compléter 1 SBC', 'Valide 1 SBC aujourd\'hui.', 'daily:sbc_completed', 1, ('xp', 10), 'Quotidien'),
    Defi('daily_open_5_packs', 'Ouvrir 5 packs', 'Ouvre 5 packs aujourd\'hui.', 'daily:pack_opened', 5, ('coins', 150), 'Quotidien'),
    # Hebdo (existant)
    Defi('weekly_complete_1_sbc', 'Compléter 1 SBC', 'Valide un défi SBC.', 'sbc_completed', 1, ('coins', 300), 'Hebdo'),
    # Special event: Jérôme Boateng Fin d'une ère — 6 étapes
    Defi(
        'boateng_eoe_1',
        "Jérôme Boateng — Fin d'une ère — 1/6",
        'Complète 1 SBC.',
        'sbc_completed',
        1,
        ('xp', 100),
        'Événement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Fin d'une ère\\fond fin d'une  ère.png")),
    ),
    Defi(
        'boateng_eoe_2',
        "Jérôme Boateng — Fin d'une ère — 2/6",
        'Complète 2 SBC.',
        'sbc_completed',
        2,
        ('coins', 200),
        'Événement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Fin d'une ère\\fond fin d'une  ère.png")),
    ),
    Defi(
        'boateng_eoe_3',
        "Jérôme Boateng — Fin d'une ère — 3/6",
        'Complète 3 SBC.',
        'sbc_completed',
        3,
        ('xp', 150),
        'Événement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Fin d'une ère\\fond fin d'une  ère.png")),
    ),
    Defi(
        'boateng_eoe_4',
        "Jérôme Boateng — Fin d'une ère — 4/6",
        'Complète 4 SBC.',
        'sbc_completed',
        4,
        ('coins', 300),
        'Événement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Fin d'une ère\\fond fin d'une  ère.png")),
    ),
    Defi(
        'boateng_eoe_5',
        "Jérôme Boateng — Fin d'une ère — 5/6",
        'Complète 5 SBC.',
        'sbc_completed',
        5,
        ('xp', 200),
        'Événement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Fin d'une ère\\fond fin d'une  ère.png")),
    ),
    Defi(
        'boateng_eoe_6',
        "Jérôme Boateng — Fin d'une ère — 6/6",
        'Complète 6 SBC pour obtenir la carte spéciale.',
        'sbc_completed',
        6,
        ('coins', 400),
        'Événement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Fin d'une ère\\fond fin d'une  ère.png")),
        card_img="cards/Fin d'une ère/Jerome Boateng.png",
        grant_card_name='Jérôme Boateng',
        grant_card_rarity="fin d'une ère",
    ),
    # Juninho — Héro (6 étapes)
    Defi('juninho_hero_1', 'Juninho — Héro — 1/6', 'Complète 1 SBC.', 'sbc_completed', 1, ('xp', 100), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png"))),
    Defi('juninho_hero_2', 'Juninho — Héro — 2/6', 'Complète 2 SBC.', 'sbc_completed', 2, ('coins', 200), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png"))),
    Defi('juninho_hero_3', 'Juninho — Héro — 3/6', 'Complète 3 SBC.', 'sbc_completed', 3, ('xp', 150), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png"))),
    Defi('juninho_hero_4', 'Juninho — Héro — 4/6', 'Complète 4 SBC.', 'sbc_completed', 4, ('coins', 300), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png"))),
    Defi('juninho_hero_5', 'Juninho — Héro — 5/6', 'Complète 5 SBC.', 'sbc_completed', 5, ('xp', 200), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png"))),
    Defi('juninho_hero_6', 'Juninho — Héro — 6/6', 'Complète 6 SBC pour obtenir la carte.', 'sbc_completed', 6, ('coins', 400), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Héro\\fond héro.png")), card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Hero\\Juninho.png")), grant_card_name='Juninho', grant_card_rarity='hero'),
    # Flashback: Lacazette (Defi-only special)
    # Lacazette — Flashback (4 étapes)
    Defi('lacazette_flashback_1', 'Lacazette — Flashback — 1/4', 'Complète 1 SBC.', 'sbc_completed', 1, ('xp', 100), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Flashback\\fond flashback.png"))),
    Defi('lacazette_flashback_2', 'Lacazette — Flashback — 2/4', 'Complète 2 SBC.', 'sbc_completed', 2, ('coins', 200), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Flashback\\fond flashback.png"))),
    Defi('lacazette_flashback_3', 'Lacazette — Flashback — 3/4', 'Complète 3 SBC.', 'sbc_completed', 3, ('xp', 150), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Flashback\\fond flashback.png"))),
    Defi('lacazette_flashback_4', 'Lacazette — Flashback — 4/4', 'Complète 4 SBC pour obtenir la carte.', 'sbc_completed', 4, ('coins', 300), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Flashback\\fond flashback.png")), card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Flashback\\Lacazette.png")), grant_card_name='Lacazette', grant_card_rarity='flashback'),
    # Iniesta — Icon début (8 étapes)
    Defi('iniesta_icon_debut_1', 'Iniesta — Icon début — 1/8', 'Complète 1 SBC.', 'sbc_completed', 1, ('xp', 100), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon debut champion\\fond icon debut champion .png"))),
    Defi('iniesta_icon_debut_2', 'Iniesta — Icon début — 2/8', 'Complète 2 SBC.', 'sbc_completed', 2, ('coins', 200), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon debut champion\\fond icon debut champion .png"))),
    Defi('iniesta_icon_debut_3', 'Iniesta — Icon début — 3/8', 'Complète 3 SBC.', 'sbc_completed', 3, ('xp', 150), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon debut champion\\fond icon debut champion .png"))),
    Defi('iniesta_icon_debut_4', 'Iniesta — Icon début — 4/8', 'Complète 4 SBC.', 'sbc_completed', 4, ('coins', 300), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon debut champion\\fond icon debut champion .png"))),
    Defi('iniesta_icon_debut_5', 'Iniesta — Icon début — 5/8', 'Complète 5 SBC.', 'sbc_completed', 5, ('xp', 200), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon debut champion\\fond icon debut champion .png"))),
    Defi('iniesta_icon_debut_6', 'Iniesta — Icon début — 6/8', 'Complète 6 SBC.', 'sbc_completed', 6, ('coins', 400), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon debut champion\\fond icon debut champion .png"))),
    Defi('iniesta_icon_debut_7', 'Iniesta — Icon début — 7/8', 'Complète 7 SBC.', 'sbc_completed', 7, ('xp', 250), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon debut champion\\fond icon debut champion .png"))),
    Defi('iniesta_icon_debut_8', 'Iniesta — Icon début — 8/8', 'Complète 8 SBC pour obtenir la carte.', 'sbc_completed', 8, ('coins', 500), 'Événement', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Icon debut champion\\fond icon debut champion .png")), card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Icon\\Icon début\\Iniesta.png")), grant_card_name='Iniesta', grant_card_rarity='icon'),
    # Pogba — Ultimate Scream (3 étapes)
    Defi('pogba_halloween_defi_1', 'Paul Pogba — Ultimate Scream — 1/3', 'Complète entièrement le SBC de Pogba.', 'pogba_sbc_completed', 1, ('xp', 120), 'Ultimate Scream', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Joueur\\fond ultimate scream.png"))),
    Defi('pogba_halloween_defi_2', 'Paul Pogba — Ultimate Scream — 2/3', 'Avoir au moins 1× Paul Pogba (79) dans ta collection.', 'pogba79_owned', 1, ('coins', 250), 'Ultimate Scream', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Joueur\\fond ultimate scream.png"))),
    Defi('pogba_halloween_defi_3', 'Paul Pogba — Ultimate Scream — 3/3', 'Complète 3 SBC pour obtenir la carte.', 'sbc_completed', 3, ('coins', 350), 'Ultimate Scream', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Joueur\\fond ultimate scream.png")), card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ultimate Scream\\Joueur\\Pogba_cdm.png")), grant_card_name='Paul Pogba', grant_card_rarity='or rare'),
    # Emil Forsberg — Flashback (2 étapes) — regrouppé sous Ultimate Scream (événement saison 2)
    Defi('forsberg_flashback_1', 'Emil Forsberg — Flashback — 1/2', 'Complète 1 SBC.', 'sbc_completed', 1, ('xp', 120), 'Ultimate Scream', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Joueur\\fond ultimate scream.png"))),
    Defi('forsberg_flashback_2', 'Emil Forsberg — Flashback — 2/2', 'Complète 2 SBC pour obtenir la carte.', 'sbc_completed', 2, ('coins', 300), 'Ultimate Scream', bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\Ultimate Scream\\Joueur\\fond ultimate scream.png")), card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Flashback\\Emil Forsberg.png")), grant_card_name='Emil Forsberg', grant_card_rarity='flashback'),
    # Ousman Dembélé — Ballon d'or (événement solo)
    Defi(
        'dembele_ballon_dor_1',
        "Ousman Dembélé — Ballon d'or",
        'Complète 1 SBC pour obtenir la carte Ballon d\'or.',
        'sbc_completed',
        1,
        ('xp', 150),
        'Événement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond ballon dor.png")),
        card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Ballon d'or\\Dembélé.png")),
        grant_card_name='Ousman Dembele',
        grant_card_rarity="Ballon d'or",
    ),
    # Lancement — World Tour: Tomori (2 étapes basées sur le Pass Lancement)
    Defi(
        'tomori_world_tour_1',
        'Tomori — World Tour — 1/2',
        'Atteins le niveau 5 du Pass Lancement.',
        'pass_level:launch',
        5,
        ('xp', 100),
        'Lancement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond world tour.png")),
    ),
    Defi(
        'tomori_world_tour_2',
        'Tomori — World Tour — 2/4',
        'Atteins le niveau 20 du Pass Lancement.',
        'pass_level:launch',
        20,
        ('xp', 150),
        'Lancement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond world tour.png")),
    ),
    # Étape 3: Compléter le SBC de Dolan
    Defi(
        'tomori_world_tour_3',
        'Tomori — World Tour — 3/4',
        'Complète le SBC de Dolan.',
        'dolan_sbc_completed',
        1,
        ('xp', 150),
        'Lancement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond world tour.png")),
    ),
    # Étape 4: Posséder Tomori (81, Or rare) au moins 1x dans la collection
    Defi(
        'tomori_world_tour_4',
        'Tomori — World Tour — 4/4',
        "Avoir au moins 1× Tomori (81, Or rare) dans ta collection et valider pour obtenir la carte 86 (World Tour).",
        'tomori81_gold_owned',
        1,
        ('coins', 200),
        'Lancement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond world tour.png")),
        card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\World Tour\\Tomori.png")),
        grant_card_name='Tomori',
        grant_card_rarity='world tour',
    ),
    # Lancement — Fondations: Garcia (4 étapes, vérifie possession de cartes fondation)
    Defi(
        'garcia_foundations_1',
        'Garcia — Fondations — 1/4',
        'Récupère Teun Koopmeiners (Fondation).',
        'owned_foundation:Teun Koopmeiners',
        1,
        ('xp', 120),
        'Lancement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond fondation.png")),
    ),
    Defi(
        'garcia_foundations_2',
        'Garcia — Fondations — 2/4',
        'Récupère Matteo Ruggeri (Fondation).',
        'owned_foundation:Matteo Ruggeri',
        1,
        ('coins', 201),
        'Lancement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond fondation.png")),
    ),
    Defi(
        'garcia_foundations_3',
        'Garcia — Fondations — 3/4',
        'Récupère Josip Stanišić (Fondation).',
        'owned_foundation:Josip Stanišić',
        1,
        ('xp', 150),
        'Lancement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond fondation.png")),
    ),
    Defi(
        'garcia_foundations_4',
        'Garcia — Fondations — 4/4',
        'Récupère Wataru Endo (Fondation) et valide pour obtenir Garcia (84, Squad fondation).',
        'owned_foundation:Wataru Endo',
        1,
        ('coins', 300),
        'Lancement',
        bg_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\Fond\\Sbc\\fond fondation.png")),
        card_img=str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Squad Fondations\\Garcia.png")),
        grant_card_name='Garcia',
        grant_card_rarity='Squad fondation',
    ),
]


def _ensure_file():
    if not DATA_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps({'events': {}, 'claimed': {}, 'daily': {}}, ensure_ascii=False, indent=2), encoding='utf-8')


def _load() -> Dict:
    _ensure_file()
    try:
        with DATA_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'events': {}, 'claimed': {}, 'daily': {}}


def _save(d: Dict):
    try:
        DATA_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


# --- Daily cycle helpers (reset 19:00 Europe/Paris) ---
def _ensure_daily_cycle(d: Dict):
    try:
        cur_key = tz.current_cycle_key(19)
    except Exception:
        # fallback to plain today
        cur_key = tz.today_str()
    daily = d.setdefault('daily', {})
    if daily.get('cycle_key') != cur_key:
        # reset daily state for new cycle
        daily['cycle_key'] = cur_key
        daily['baseline'] = {}
        daily['claimed_ids'] = {}
        _save(d)


def _is_daily_event_key(event_key: str) -> bool:
    try:
        return str(event_key).startswith('daily:')
    except Exception:
        return False


def _base_event_key(event_key: str) -> str:
    if _is_daily_event_key(event_key):
        return str(event_key).split(':', 1)[1]
    return str(event_key)


def _get_daily_progress_for(base_key: str) -> int:
    """Return daily progress for a base event key using baseline snapshots."""
    d = _load()
    _ensure_daily_cycle(d)
    ev = d.setdefault('events', {})
    cur = int(ev.get(base_key, 0))
    daily = d.setdefault('daily', {})
    bl = daily.setdefault('baseline', {})
    if base_key not in bl:
        # snapshot current as starting point for this cycle
        bl[base_key] = cur
        _save(d)
    base = int(bl.get(base_key, 0))
    return max(0, cur - base)


def _is_daily_claimed(defi_id: str) -> bool:
    d = _load()
    _ensure_daily_cycle(d)
    daily = d.setdefault('daily', {})
    claimed = daily.setdefault('claimed_ids', {})
    return bool(claimed.get(defi_id))


def _mark_daily_claimed(defi_id: str):
    d = _load()
    _ensure_daily_cycle(d)
    daily = d.setdefault('daily', {})
    claimed = daily.setdefault('claimed_ids', {})
    claimed[defi_id] = True
    _save(d)


def get_progress(event_key: str) -> int:
    d = _load()
    # Dynamic events resolved on the fly
    if event_key == 'pogba79_owned':
        try:
            owned = game_db.load_collection()
            return 1 if int(owned.get('Paul Pogba', 0)) >= 1 else 0
        except Exception:
            return 0
    if event_key == 'tomori81_gold_owned':
        try:
            owned = game_db.load_collection()
            has = int(owned.get('Tomori', 0)) >= 1
            if not has:
                return 0
            # verify there exists a Tomori entry with or rare and rating >=81 in players data
            players = game_db.load_players()
            def _norm(s: str) -> str:
                try:
                    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower().strip()
                except Exception:
                    return (s or '').lower().strip()
            ok = any((_norm(p.get('name','')) == _norm('Tomori') and str(p.get('rarity','')).strip().lower() in ('or rare', 'or_rare', 'gold rare', 'rare') and int(p.get('rating',0)) >= 81) for p in players)
            return 1 if ok else 0
        except Exception:
            return 0
    # Dynamic: foundation ownership checks for Garcia series
    try:
        if str(event_key).startswith('owned_foundation:'):
            target = str(event_key).split(':', 1)[1]
            def _norm(s: str) -> str:
                try:
                    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower().strip()
                except Exception:
                    return (s or '').lower().strip()
            owned = game_db.load_collection()
            base_names = set(owned.keys())
            # accept both with/without diacritics variants
            n_target = _norm(target)
            for nm in base_names:
                if _norm(nm) == n_target and int(owned.get(nm, 0)) >= 1:
                    return 1
            return 0
    except Exception:
        return 0
    # Dynamic: pass level progress for a specific pass id, returns current level
    try:
        if str(event_key).startswith('pass_level:'):
            parts = str(event_key).split(':', 1)
            pass_id = parts[1] if len(parts) > 1 else 'launch'
            # get relative level for this pass id
            lvl, _cur, _need = sp_mod.get_relative_level_progress(pass_id)
            return int(lvl)
    except Exception:
        pass
    # Daily events use delta from baseline since last 19h reset
    if _is_daily_event_key(event_key):
        base_key = _base_event_key(event_key)
        return _get_daily_progress_for(base_key)
    return int(d.get('events', {}).get(event_key, 0))


def add_progress(event_key: str, amount: int = 1):
    if amount <= 0:
        return
    d = _load()
    ev = d.setdefault('events', {})
    ev[event_key] = int(ev.get(event_key, 0)) + amount
    _save(d)


def is_claimed(defi_id: str) -> bool:
    # daily defis are claimed per-cycle
    if str(defi_id).startswith('daily_'):
        return _is_daily_claimed(defi_id)
    d = _load()
    return bool(d.get('claimed', {}).get(defi_id))


def can_claim(defi: Defi) -> bool:
    # Daily defis depend on per-cycle state
    if _is_daily_event_key(defi.event_key) or str(defi.id).startswith('daily_') or defi.group == 'Quotidien':
        return (not _is_daily_claimed(defi.id)) and (get_progress(defi.event_key) >= defi.target)
    # Sequential gating for Tomori — World Tour series: each step requires the previous to be claimed
    try:
        if str(defi.id).startswith('tomori_world_tour_'):
            try:
                suf = int(str(defi.id).split('_')[-1])
            except Exception:
                suf = None
            if isinstance(suf, int) and suf > 1:
                prev_id = f"tomori_world_tour_{suf-1}"
                if not is_claimed(prev_id):
                    return False
        # Sequential gating for Garcia — Fondations
        if str(defi.id).startswith('garcia_foundations_'):
            try:
                suf = int(str(defi.id).split('_')[-1])
            except Exception:
                suf = None
            if isinstance(suf, int) and suf > 1:
                prev_id = f"garcia_foundations_{suf-1}"
                if not is_claimed(prev_id):
                    return False
    except Exception:
        pass
    return (not is_claimed(defi.id)) and (get_progress(defi.event_key) >= defi.target)


def claim(defi: Defi) -> bool:
    if not can_claim(defi):
        return False
    typ, amt = defi.reward
    if typ == 'coins':
        try:
            wallet.add_coins(amt)
        except Exception:
            pass
    elif typ == 'xp':
        try:
            xp.add_xp(amt)
        except Exception:
            pass
    # grant a special card to the collection if configured
    try:
        if defi.grant_card_name:
            game_db.add_to_collection_by_names([defi.grant_card_name])
    except Exception:
        pass
    # mark claimed with appropriate scope
    if _is_daily_event_key(defi.event_key) or str(defi.id).startswith('daily_') or defi.group == 'Quotidien':
        _mark_daily_claimed(defi.id)
    else:
        d = _load()
        d.setdefault('claimed', {})[defi.id] = True
        _save(d)
    return True


def get_defi_only_players() -> List[Dict]:
    """Special players obtainable only via Défis (not packable)."""
    specials = [
        {"name": "Jérôme Boateng", "rating": 90, "rarity": "fin d'une ère"},
        {"name": "Juninho", "rating": 91, "rarity": "hero"},
        {"name": "Lacazette", "rating": 90, "rarity": "flashback"},
        {"name": "Iniesta", "rating": 86, "rarity": "icon"},
        {"name": "Emil Forsberg", "rating": 83, "rarity": "flashback"},
        # Use a variant suffix so Collection can list both 81 (Or rare) and 86 (World Tour)
        {"name": "Tomori#world tour", "rating": 86, "rarity": "world tour", "image": str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\World Tour\\Tomori.png"))},
        # Garcia (Défi Lancement — Fondations)
        {"name": "Garcia", "rating": 84, "rarity": "Squad fondation", "image": str(Path("C:\\Users\\Utilisateur\\Desktop\\Minefut\\cards\\Squad Fondations\\Garcia.png"))},
    ]
    return specials


def groups() -> List[str]:
    return sorted(list({d.group for d in DEFI_LIST}))


def list_defis(group: Optional[str] = None) -> List[Defi]:
    if group is None:
        return DEFI_LIST
    return [d for d in DEFI_LIST if d.group == group]
