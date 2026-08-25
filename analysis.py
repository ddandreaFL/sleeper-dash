"""Analysis layer. Pure functions over already-fetched data.

Key idea: we never compute fantasy points ourselves. The matchups endpoint
returns players_points, which Sleeper has already scored using YOUR league's
settings (assists at 1.3, double-double bonus, all of it). Summing that across
weeks gives a season-to-date value for every rostered player, correct by
construction, with no external stats provider needed.
"""

from collections import Counter, defaultdict

NON_LINEUP = {"BN", "IR", "TAXI"}
OUT_STATUSES = {"Out", "IR", "Doubtful", "Suspended"}

FLEX = {
    "nba": {"G": {"PG", "SG"}, "F": {"SF", "PF"},
            "UTIL": {"PG", "SG", "SF", "PF", "C"}},
    "nfl": {"FLEX": {"RB", "WR", "TE"}, "WRRB_FLEX": {"RB", "WR"},
            "REC_FLEX": {"WR", "TE"}, "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
            "IDP_FLEX": {"DL", "LB", "DB"}},
}
CORE = {"nba": ["PG", "SG", "SF", "PF", "C"],
        "nfl": ["QB", "RB", "WR", "TE", "K", "DEF"]}


# ------------------------------------------------------------------ standings

def record(roster):
    s = roster.get("settings") or {}
    return s.get("wins", 0), s.get("losses", 0), s.get("ties", 0)


def points_for(roster):
    s = roster.get("settings") or {}
    return s.get("fpts", 0) + s.get("fpts_decimal", 0) / 100


def points_against(roster):
    s = roster.get("settings") or {}
    return s.get("fpts_against", 0) + s.get("fpts_against_decimal", 0) / 100


def standings(rosters, team_names):
    table = sorted(rosters, key=lambda r: (record(r)[0], points_for(r)), reverse=True)
    rows = []
    for seed, r in enumerate(table, 1):
        w, l, t = record(r)
        rows.append({
            "seed": seed,
            "roster_id": r["roster_id"],
            "team": team_names.get(r.get("owner_id")) or f"roster {r['roster_id']}",
            "record": f"{w}-{l}" + (f"-{t}" if t else ""),
            "wins": w,
            "pf": round(points_for(r), 1),
            "pa": round(points_against(r), 1),
            "diff": round(points_for(r) - points_against(r), 1),
        })
    return rows


def playoff_picture(rows, league, current_week, my_roster_id):
    settings = league.get("settings") or {}
    spots = settings.get("playoff_teams", 6)
    start = settings.get("playoff_week_start", 22)
    left = max(start - current_week, 0)

    me = next((r for r in rows if r["roster_id"] == my_roster_id), None)
    if not me:
        return {}
    out = {"seed": me["seed"], "spots": spots, "games_left": left,
           "playoff_week_start": start, "teams": len(rows)}

    if me["seed"] <= spots:
        first_out = rows[spots] if len(rows) > spots else None
        cushion = me["wins"] - first_out["wins"] if first_out else 99
        out["cushion"] = cushion
        out["status"] = "clinched (on wins)" if cushion > left else "in, catchable"
    else:
        cut = rows[spots - 1]
        back = cut["wins"] - me["wins"]
        out["games_back"] = back
        out["status"] = "eliminated" if back > left else "alive"
    return out


# -------------------------------------------------------------- player values

def accumulate_player_points(weekly_matchups):
    """
    weekly_matchups: {week: [matchup dicts]}
    Returns {player_id: {"total": float, "weeks": int, "by_week": {wk: pts}}}
    """
    agg = defaultdict(lambda: {"total": 0.0, "weeks": 0, "by_week": {}})
    for week, ms in sorted(weekly_matchups.items(), key=lambda kv: int(kv[0])):
        for m in ms or []:
            for pid, pts in (m.get("players_points") or {}).items():
                if pts is None:
                    continue
                a = agg[pid]
                a["total"] += pts
                a["by_week"][int(week)] = pts
                if pts != 0:
                    a["weeks"] += 1
    return {k: v for k, v in agg.items()}


def player_value(agg, pid):
    a = agg.get(pid)
    if not a or not a["weeks"]:
        return 0.0
    return a["total"] / a["weeks"]


def roster_values(roster, agg, players):
    rows = []
    for pid in roster.get("players") or []:
        p = players.get(pid, {})
        rows.append({
            "player_id": pid,
            "name": p.get("name", pid),
            "pos": "/".join(p.get("pos") or []),
            "team": p.get("team"),
            "age": p.get("age"),
            "status": p.get("status"),
            "ppw": round(player_value(agg, pid), 1),
            "total": round((agg.get(pid) or {}).get("total", 0.0), 1),
        })
    return sorted(rows, key=lambda r: -r["ppw"])


def starting_strength(roster, agg, roster_positions, sport):
    """Sum of your best N players where N = number of startable slots."""
    slots = sum(1 for s in roster_positions if s not in NON_LINEUP)
    vals = sorted((player_value(agg, pid) for pid in roster.get("players") or []),
                  reverse=True)
    return round(sum(vals[:slots]), 1)


# -------------------------------------------------------------- roster shape

def slot_capacity(roster_positions, sport):
    flex = FLEX.get(sport, {})
    dedicated, flex_pool = Counter(), Counter()
    for slot in roster_positions:
        if slot in NON_LINEUP:
            continue
        if slot in flex:
            for pos in flex[slot]:
                flex_pool[pos] += 1
        else:
            dedicated[slot] += 1
    return dedicated, flex_pool


def roster_shape(roster, players, agg, roster_positions, sport):
    """
    Headcount is the crude version. This also reports the value of the players
    beyond your startable slots at each position, which is what you can trade
    without weakening the lineup.
    """
    dedicated, flex_pool = slot_capacity(roster_positions, sport)
    by_pos = defaultdict(list)
    for pid in roster.get("players") or []:
        for pos in players.get(pid, {}).get("pos") or []:
            by_pos[pos].append((players[pid].get("name", pid), player_value(agg, pid)))

    rows = []
    for pos in CORE.get(sport, []):
        have = by_pos.get(pos, [])
        cap = max(dedicated.get(pos, 0), 1)
        ranked = sorted(have, key=lambda x: -x[1])
        buried = ranked[cap:]
        rows.append({
            "pos": pos,
            "rostered": len(have),
            "slots": dedicated.get(pos, 0),
            "flex": flex_pool.get(pos, 0),
            "surplus": len(have) - cap,
            "buried_value": round(sum(v for _, v in buried), 1),
            "best_buried": buried[0][0] if buried else None,
        })
    return sorted(rows, key=lambda r: -r["surplus"])


# ------------------------------------------------------------------- matchup

def matchup_detail(matchups, rosters, team_names, players, agg, my_roster_id, week):
    mine = next((m for m in matchups if m["roster_id"] == my_roster_id), None)
    if not mine:
        return None
    opp = next((m for m in matchups
                if m.get("matchup_id") == mine.get("matchup_id")
                and m["roster_id"] != my_roster_id), None)
    if not opp:
        return None

    by_id = {r["roster_id"]: r for r in rosters}
    opp_roster = by_id.get(opp["roster_id"], {})

    def side(m, roster):
        starters = m.get("starters") or []
        pts = m.get("players_points") or {}
        lineup = [{
            "name": players.get(p, {}).get("name", p),
            "status": players.get(p, {}).get("status"),
            "live": round(pts.get(p, 0.0), 1),
            "avg": round(player_value(agg, p), 1),
        } for p in starters if p and p != "0"]
        return {
            "team": team_names.get(roster.get("owner_id"))
                    or f"roster {m['roster_id']}",
            "points": round(m.get("points") or 0.0, 1),
            "expected": round(sum(x["avg"] for x in lineup), 1),
            "lineup": sorted(lineup, key=lambda x: -x["avg"]),
            "hurt": [x["name"] for x in lineup if x["status"] in OUT_STATUSES],
        }

    me_side = side(mine, by_id.get(my_roster_id, {}))
    opp_side = side(opp, opp_roster)

    return {"week": week, "me": me_side, "opp": opp_side,
            "edge": round(me_side["expected"] - opp_side["expected"], 1),
            "bench_alerts": bench_alerts(mine, players, agg)}


def bench_alerts(side, players, agg):
    """Bench players whose season average beats a starter's. Gameday nudge."""
    starters = [p for p in (side.get("starters") or []) if p and p != "0"]
    bench = [p for p in (side.get("players") or []) if p not in starters]
    if not starters or not bench:
        return []
    ranked_starters = sorted(starters, key=lambda p: player_value(agg, p))
    alerts, used = [], set()
    for b in sorted(bench, key=lambda p: -player_value(agg, p))[:3]:
        bv = player_value(agg, b)
        for s in ranked_starters:
            if s in used:
                continue
            sv = player_value(agg, s)
            if bv > sv * 1.15 and bv > 0:
                alerts.append({
                    "bench": players.get(b, {}).get("name", b), "bench_avg": round(bv, 1),
                    "starter": players.get(s, {}).get("name", s), "starter_avg": round(sv, 1),
                })
                used.add(s)
                break
    return alerts


# -------------------------------------------------------------- trade finder

def league_context(league, rosters, my_roster_id, week):
    """
    The settings that change what you should DO, surfaced instead of buried.
    Sleeper's setting keys vary by sport and league age, so everything here is
    defensive: missing keys degrade to None rather than blowing up.
    """
    s = league.get("settings") or {}
    mine = next((r for r in rosters if r["roster_id"] == my_roster_id), {}) or {}
    ms = mine.get("settings") or {}

    deadline = s.get("trade_deadline")
    weeks_left = (deadline - week) if isinstance(deadline, int) else None

    # waiver_type: 2 is FAAB on Sleeper, other values are priority-based.
    # Sleeper populates waiver_budget (default 100) even for priority leagues,
    # so it cannot be used to infer FAAB. Only waiver_type == 2 means FAAB.
    wt = s.get("waiver_type")
    faab = wt == 2
    budget = s.get("waiver_budget")
    used = ms.get("waiver_budget_used")

    spots = s.get("playoff_teams", 6)
    teams = len(rosters) or s.get("num_teams") or 0

    return {
        "teams": teams,
        "playoff_spots": spots,
        "playoff_share": round(spots / teams, 2) if teams else None,
        "playoff_week_start": s.get("playoff_week_start"),
        "trade_deadline": deadline,
        "weeks_to_deadline": weeks_left,
        "deadline_passed": bool(weeks_left is not None and weeks_left < 0),
        "waiver_mode": "FAAB" if faab else "priority",
        "faab_budget": budget,
        "faab_used": used,
        "faab_left": (budget - used) if isinstance(budget, int)
                     and isinstance(used, int) else None,
        "waiver_position": ms.get("waiver_position"),
        "pick_trading": bool(s.get("pick_trading")),
        "ir_slots": s.get("reserve_slots"),
        "raw": s,
    }


def positional_value(roster, players, agg, roster_positions, sport):
    """Startable value at each position: sum of the best N, N = slots + flex."""
    dedicated, flex_pool = slot_capacity(roster_positions, sport)
    by_pos = defaultdict(list)
    for pid in roster.get("players") or []:
        for pos in players.get(pid, {}).get("pos") or []:
            by_pos[pos].append(player_value(agg, pid))
    out = {}
    for pos in CORE.get(sport, []):
        n = max(dedicated.get(pos, 0) + flex_pool.get(pos, 0), 1)
        out[pos] = round(sum(sorted(by_pos.get(pos, []), reverse=True)[:n]), 1)
    return out


def _median(vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return 0.0
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def trade_targets(mine, others, players, agg, roster_positions, sport, team_names,
                  need_threshold=0.75):
    """
    Value-based, not headcount-based. In a points league nobody cares that you
    roster seven centers, they care that your seventh center outproduces their
    starter. So: find positions where you have startable value going to waste,
    then find teams whose value at that position is well below league median.
    """
    all_rosters = [mine] + list(others)
    pv = {r["roster_id"]: positional_value(r, players, agg, roster_positions, sport)
          for r in all_rosters}
    medians = {pos: _median([pv[rid].get(pos, 0) for rid in pv])
               for pos in CORE.get(sport, [])}

    my_shape = {r["pos"]: r for r in roster_shape(mine, players, agg,
                                                  roster_positions, sport)}
    spare = {p: r["buried_value"] for p, r in my_shape.items()
             if r["surplus"] > 0 and r["buried_value"] > 0}

    out = []
    for r in others:
        rid = r["roster_id"]
        score, notes = 0.0, []
        for pos, buried in spare.items():
            med = medians.get(pos, 0)
            theirs = pv[rid].get(pos, 0)
            if med > 0 and theirs < med * need_threshold:
                deficit = round(med - theirs, 1)
                score += min(buried, deficit)
                notes.append(f"{pos} {theirs:.0f} vs league {med:.0f}")
        if score > 0:
            best = (roster_values(r, agg, players) or [{}])[0]
            out.append({
                "team": team_names.get(r.get("owner_id")) or f"roster {rid}",
                "roster_id": rid,
                "fit_score": round(score, 1),
                "notes": "; ".join(notes),
                "their_best": best.get("name"),
                "their_best_ppw": best.get("ppw"),
            })
    return sorted(out, key=lambda x: -x["fit_score"])
