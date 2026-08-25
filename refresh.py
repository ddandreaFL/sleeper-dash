"""Build data/snapshot.json. Run locally or from GitHub Actions on a cron.

    python refresh.py --demo
    python refresh.py --user ddillonn
    python refresh.py --user ddillonn --sport nba --season 2026

The Streamlit app reads the snapshot, so the app never waits on the API and
Sleeper never sees more than a few dozen calls per refresh.
"""

import argparse
import json
import os
from datetime import datetime, timezone

import analysis
import demo_data

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "snapshot.json")


def build_league_payload(league, rosters, team_names, players, weekly, week,
                         my_roster_id, sport):
    agg = analysis.accumulate_player_points(weekly)
    rows = analysis.standings(rosters, team_names)
    mine = next(r for r in rosters if r["roster_id"] == my_roster_id)
    others = [r for r in rosters if r["roster_id"] != my_roster_id]
    rp = league["roster_positions"]

    strengths = []
    for r in rosters:
        strengths.append({
            "team": team_names.get(r.get("owner_id")) or f"roster {r['roster_id']}",
            "roster_id": r["roster_id"],
            "strength": analysis.starting_strength(r, agg, rp, sport),
        })

    return {
        "league_id": league["league_id"],
        "name": league["name"],
        "sport": sport,
        "week": week,
        "my_roster_id": my_roster_id,
        "settings": league.get("settings") or {},
        "scoring_settings": league.get("scoring_settings") or {},
        "roster_positions": rp,
        "standings": rows,
        "playoffs": analysis.playoff_picture(rows, league, week, my_roster_id),
        "context": analysis.league_context(league, rosters, my_roster_id, week),
        "strengths": sorted(strengths, key=lambda x: -x["strength"]),
        "my_players": analysis.roster_values(mine, agg, players),
        "roster_shape": analysis.roster_shape(mine, players, agg, rp, sport),
        "matchup": analysis.matchup_detail(weekly.get(week, []), rosters, team_names,
                                           players, agg, my_roster_id, week),
        "trade_targets": analysis.trade_targets(mine, others, players, agg, rp,
                                                sport, team_names),
    }


def run_demo():
    nba = demo_data.league()
    nfl = demo_data.nfl_league()
    return [
        build_league_payload(nba, demo_data.rosters(), demo_data.team_names(),
                             demo_data.players(), demo_data.weekly_matchups(13),
                             13, 1, "nba"),
        build_league_payload(nfl, demo_data.nfl_rosters(), demo_data.team_names(),
                             demo_data.nfl_players(), demo_data.nfl_weekly(10),
                             10, 1, "nfl"),
    ]


def run_live(username, sports, season_override, week_override, back_weeks):
    import sleeper
    out = []
    u = sleeper.user(username)
    for sport in sports:
        st = sleeper.state(sport)
        season = season_override or st.get("season")
        week = week_override or st.get("week") or 1
        lgs = sleeper.leagues(u["user_id"], sport, season)
        if not lgs:
            print(f"no {sport} leagues for season {season}")
            continue
        players = sleeper.players(sport)
        for lg in lgs:
            rs = sleeper.rosters(lg["league_id"])
            mine = next((r for r in rs if r["owner_id"] == u["user_id"]), None)
            if not mine:
                continue
            names = {x["user_id"]: ((x.get("metadata") or {}).get("team_name")
                                    or x.get("display_name"))
                     for x in sleeper.league_users(lg["league_id"])}
            weekly = {}
            first = max(1, week - back_weeks + 1)
            for wk in range(first, week + 1):
                try:
                    weekly[wk] = sleeper.matchups(lg["league_id"], wk)
                except Exception as e:
                    print(f"  week {wk} failed: {e}")
            out.append(build_league_payload(lg, rs, names, players, weekly, week,
                                            mine["roster_id"], sport))
            print(f"built {lg['name']} ({sport}, week {week})")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--user")
    ap.add_argument("--sport", default="all", help="nba, nfl, or all")
    ap.add_argument("--season")
    ap.add_argument("--week", type=int)
    ap.add_argument("--back-weeks", type=int, default=25,
                    help="how many weeks of scoring history to pull")
    args = ap.parse_args()

    if args.demo:
        leagues = run_demo()
    else:
        if not args.user:
            raise SystemExit("pass --user <sleeper username> or --demo")
        sports = ["nba", "nfl"] if args.sport == "all" else [args.sport]
        leagues = run_live(args.user, sports, args.season, args.week, args.back_weeks)

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "demo": bool(args.demo),
        "leagues": leagues,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"wrote {OUT} ({len(leagues)} league(s))")


if __name__ == "__main__":
    main()
