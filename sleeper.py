"""Thin Sleeper API client. Read-only, no auth, no key.

Sleeper asks callers to stay under 1000 requests/min. This client caches
to disk so a full refresh is a few dozen calls, not a few thousand.
"""

import json
import os
import time
from urllib.request import urlopen, Request

BASE = "https://api.sleeper.app/v1"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
PLAYER_TTL = 60 * 60 * 24        # player dump: once a day, it's ~5MB
DEFAULT_TTL = 60 * 10            # everything else: 10 min


def _cache_path(key):
    safe = key.strip("/").replace("/", "_")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def get(path, ttl=DEFAULT_TTL, use_cache=True):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cp = _cache_path(path)
    if use_cache and os.path.exists(cp) and (time.time() - os.path.getmtime(cp)) < ttl:
        with open(cp) as f:
            return json.load(f)
    req = Request(BASE + path, headers={"User-Agent": "sleeper-dash/1.0"})
    with urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    with open(cp, "w") as f:
        json.dump(data, f)
    return data


# ------------------------------------------------------------------ endpoints

def state(sport):
    return get(f"/state/{sport}", ttl=60 * 30)


def user(username):
    return get(f"/user/{username}", ttl=60 * 60 * 24)


def leagues(user_id, sport, season):
    return get(f"/user/{user_id}/leagues/{sport}/{season}", ttl=60 * 60)


def league(league_id):
    return get(f"/league/{league_id}", ttl=60 * 60)


def rosters(league_id):
    return get(f"/league/{league_id}/rosters")


def league_users(league_id):
    return get(f"/league/{league_id}/users", ttl=60 * 60)


def matchups(league_id, week):
    return get(f"/league/{league_id}/matchups/{week}")


def traded_picks(league_id):
    return get(f"/league/{league_id}/traded_picks", ttl=60 * 60)


def players(sport):
    """~5MB. Slimmed on the way in so nothing downstream carries the bulk."""
    raw = get(f"/players/{sport}", ttl=PLAYER_TTL)
    return {
        pid: {
            "name": p.get("full_name") or p.get("last_name") or pid,
            "pos": p.get("fantasy_positions") or [],
            "team": p.get("team"),
            "age": p.get("age"),
            "status": p.get("injury_status"),
        }
        for pid, p in raw.items()
    }
