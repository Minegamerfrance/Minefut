from dataclasses import dataclass
from typing import Optional
import random


@dataclass
class Card:
    name: str
    rarity: str
    bg_color: tuple
    otw: bool = False
    rating: int = 0
    avatar_path: Optional[str] = None  # relative path (e.g., 'data/avatars/name.png')
    # New metadata for reveal sequence
    nation: Optional[str] = None
    league: Optional[str] = None
    club: Optional[str] = None
    # runtime attrs set by main
    x: float = 0
    y: float = 0
    target_y: float = 0
    offset_x: int = 0


RARITIES = [
    # Format: (canonical name, probability, color)
    ("otw", 0.005, (255, 140, 0)),         # Ones To Watch
    ("icon", 0.01, (245, 245, 235)),       # Icon
    ("hero", 0.09, (180, 60, 140)),        # Hero (ex-Epic)
    ("or rare", 0.2, (212, 175, 55)),      # Gold Rare
    ("or non rare", 0.7, (194, 178, 128)), # Gold Non-Rare
]


def weighted_choice(rarities):
    r = random.random()
    acc = 0.0
    for name, prob, color in rarities:
        acc += prob
        if r <= acc:
            return name, color
    # fallback
    return rarities[-1][0], rarities[-1][2]


PLAYER_CATALOG = [
    {"name": "Donnarumma", "avatar": "donnarumma.png", "nation": "Italie", "league": "Ligue 1", "club": "PSG"},
    {"name": "Wirtz", "avatar": "wirtz.png", "nation": "Allemagne", "league": "Bundesliga", "club": "Leverkusen"},
    {"name": "Gyokeres", "avatar": "gyokeres.png", "nation": "Suède", "league": "Primeira Liga", "club": "Sporting CP"},
    {"name": "De Bruyne", "avatar": "de_bruyne.png", "nation": "Belgique", "league": "Premier League", "club": "Manchester City"},
    {"name": "Alexander-Arnold", "avatar": "alexander_arnold.png", "nation": "Angleterre", "league": "Premier League", "club": "Liverpool"},
    {"name": "Son", "avatar": "son.png", "nation": "Corée du Sud", "league": "Premier League", "club": "Tottenham"},
    {"name": "Mbeumo", "avatar": "mbeumo.png", "nation": "Cameroun", "league": "Premier League", "club": "Brentford"},
    {"name": "Xhaka", "avatar": "xhaka.png", "nation": "Suisse", "league": "Bundesliga", "club": "Leverkusen"},
    {"name": "Coman", "avatar": "coman.png", "nation": "France", "league": "Bundesliga", "club": "Bayern Munich"},
    {"name": "Rabiot", "avatar": "rabiot.png", "nation": "France", "league": "Serie A", "club": "Juventus"},
    {"name": "Tillman", "avatar": "tillman.png", "nation": "USA", "league": "Eredivisie", "club": "PSV"},
    {"name": "Paul Pogba", "avatar": "pogba.png", "nation": "France", "league": "Serie A", "club": "Juventus"},
]


def generate_pack(n=5):
    pack = []
    for _ in range(n):
        rarity, color = weighted_choice(RARITIES)
        player = random.choice(PLAYER_CATALOG)
        name = player["name"]
        rating = random.randint(65, 94)
        # mark OTW cards with a boolean and give them slightly higher ratings
        is_otw = (rarity == "otw")
        if is_otw:
            # OTW cards should stand out: boost rating slightly
            rating = max(rating, random.randint(88, 97))
        avatar_rel = f"data/avatars/{player['avatar']}"
        pack.append(Card(
            name=name,
            rarity=rarity,
            bg_color=color,
            rating=rating,
            otw=is_otw,
            avatar_path=avatar_rel,
            nation=player.get("nation"),
            league=player.get("league"),
            club=player.get("club"),
        ))
    return pack
