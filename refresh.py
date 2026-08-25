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
                         my_roster_id, sport, market_index=None):
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

    # dynasty value layer (Dynatyze-style)
    values = analysis.build_player_values(rosters, agg, players, sport, market_index)
    teams = [{"roster_id": r["roster_id"],
              "team": team_names.get(r.get("owner_id")) or f"roster {r['roster_id']}"}
             for r in rosters]

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
        "values": values,
        "teams": teams,
        "power_rankings": analysis.power_rankings(values, rosters, team_names, rp, sport),
        "trends": analysis.value_trends(values, my_roster_id),
        "pick_values": analysis.pick_value_table(sport),
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


def _pull_league(lg, players, sport, uid, week, back_weeks):
    """Build one league's payload. Returns (payload, scored) where scored is
    True if any real points were logged in the weeks pulled."""
    import sleeper
    rs = sleeper.rosters(lg["league_id"])
    mine = next((r for r in rs if r["owner_id"] == uid), None)
    if not mine:
        return None, False
    names = {x["user_id"]: ((x.get("metadata") or {}).get("team_name")
                            or x.get("display_name"))
             for x in sleeper.league_users(lg["league_id"])}
    weekly = {}
    first = max(1, week - back_weeks + 1)
    for wk in range(first, week + 1):
        try:
            weekly[wk] = sleeper.matchups(lg["league_id"], wk)
        except Exception as e:  # noqa: BLE001
            print(f"  week {wk} failed: {e}")
    scored = any(pts for ms in weekly.values() for m in (ms or [])
                 for pts in (m.get("players_points") or {}).values())
    market_index = market_for(lg, players, sport)
    payload = build_league_payload(lg, rs, names, players, weekly, week,
                                   mine["roster_id"], sport, market_index)
    payload["season"] = lg.get("season")
    return payload, scored


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
            payload, scored = _pull_league(lg, players, sport, u["user_id"],
                                           week, back_weeks)
            if payload is None:
                continue
            # Offseason / pre-draft: current season has no games yet. Fall back
            # to the completed previous season so the dashboard is never empty.
            if not scored and lg.get("previous_league_id") and not season_override:
                prev = sleeper.league(lg["previous_league_id"])
                p2, s2 = _pull_league(prev, players, sport, u["user_id"], 25, 25)
                if p2 is not None and s2:
                    p2["note"] = (f"{lg.get('season')} season has not started; "
                                  f"showing completed {prev.get('season')} season")
                    payload = p2
                    print(f"  {lg['name']}: {lg.get('season')} empty, "
                          f"fell back to {prev.get('season')}")
            out.append(payload)
            print(f"built {payload['name']} ({sport}, "
                  f"season {payload.get('season')})")
    return out


def market_for(league, players, sport):
    """FantasyCalc market values matched to Sleeper player ids. NFL only;
    tuned to the league's own format (superflex, team count, PPR)."""
    if sport != "nfl":
        return {}
    import market
    s = league.get("settings") or {}
    rp = league.get("roster_positions") or []
    num_qbs = 2 if "SUPER_FLEX" in rp else 1
    teams = s.get("num_teams") or 8
    is_dyn = (s.get("type") == 2)  # Sleeper type 2 == keeper/dynasty
    mkt = market.nfl_market(is_dynasty=is_dyn, num_qbs=num_qbs,
                            num_teams=teams, ppr=1)
    idx = market.index_by_player(players, mkt)
    print(f"  matched {len(idx)} market values for {league['name']}")
    return idx


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
