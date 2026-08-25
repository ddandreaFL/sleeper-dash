"""External dynasty/redraft market values. Read-only, no auth, no key.

FantasyCalc publishes free consensus values (KeepTradeCut style) for NFL and
MLB. There is no free NBA equivalent, so NBA falls back to the derived model in
analysis.py. This module only covers NFL and is used as a reference column and
an optional signal, never as the sole source of truth.

Values are cached to disk the same way sleeper.py caches, so a refresh is one
call, not one per player.
"""

import json
import os
import re
import time
from urllib.request import urlopen, Request

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
TTL = 60 * 60 * 6  # values move slowly, 6h is plenty
BASE = "https://api.fantasycalc.com/values/current"


def _norm(name):
    """Normalize a name for matching across providers: lowercase, strip
    punctuation and common suffixes so 'A.J. Brown' == 'AJ Brown'."""
    n = (name or "").lower()
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", n)
    n = re.sub(r"[^a-z]", "", n)
    return n


def _cache_path(key):
    return os.path.join(CACHE_DIR, f"market_{key}.json")


def _fetch(url, key):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cp = _cache_path(key)
    if os.path.exists(cp) and (time.time() - os.path.getmtime(cp)) < TTL:
        with open(cp) as f:
            return json.load(f)
    req = Request(url, headers={"User-Agent": "sleeper-dash/1.0"})
    with urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    with open(cp, "w") as f:
        json.dump(data, f)
    return data


def nfl_market(is_dynasty=False, num_qbs=2, num_teams=8, ppr=1):
    """Return {normalized_name: {"value": int, "rank": int, "pos": str}}.

    Defaults match a common superflex PPR redraft league. Tune to the actual
    Sleeper league in refresh.py. Returns {} on any failure so the pipeline
    never dies for a missing reference column.
    """
    key = f"nfl_d{int(is_dynasty)}_q{num_qbs}_t{num_teams}_p{ppr}"
    url = (f"{BASE}?isDynasty={str(is_dynasty).lower()}&numQbs={num_qbs}"
           f"&numTeams={num_teams}&ppr={ppr}")
    try:
        rows = _fetch(url, key)
    except Exception as e:  # noqa: BLE001 - reference data, degrade quietly
        print(f"  market values unavailable: {e}")
        return {}
    out = {}
    for row in rows or []:
        p = row.get("player") or {}
        nm = _norm(p.get("name"))
        if not nm:
            continue
        out[nm] = {
            "value": row.get("value") or 0,
            "rank": row.get("overallRank"),
            "pos": p.get("position"),
        }
    return out


def index_by_player(players, market):
    """Map Sleeper player_id -> market value dict, by normalized name."""
    out = {}
    for pid, p in (players or {}).items():
        hit = market.get(_norm(p.get("name")))
        if hit:
            out[pid] = hit
    return out
