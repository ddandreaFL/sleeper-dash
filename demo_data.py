"""Synthetic fixtures shaped like real Sleeper payloads.

Everything here is fake. It exists so you can run the full pipeline and the
Streamlit app before pointing anything at the live API, and so the GitHub
Action has something to test against.
"""

import random

random.seed(7)

PLAYERS = {
    "1": ("G. Antetokounmpo", ["PF"], "MIA", 31, None, 52),
    "2": ("Z. Williamson", ["PF", "SF"], "NOP", 26, "Out", 38),
    "3": ("K. Ware", ["C", "PF"], "MIL", 24, None, 31),
    "4": ("Y. Missi", ["C"], "NOP", 23, None, 24),
    "5": ("W. Carter", ["C"], "ORL", 27, None, 26),
    "6": ("K. Filipowski", ["C", "PF"], "UTA", 24, None, 22),
    "7": ("J. Poeltl", ["C"], "TOR", 30, None, 28),
    "8": ("B. Portis", ["C", "PF"], "MIA", 31, None, 21),
    "9": ("J. Collins", ["PF", "C"], "DET", 28, None, 23),
    "10": ("A. Nembhard", ["PG", "SG"], "IND", 26, None, 27),
    "11": ("S. Henderson", ["PG"], "POR", 24, None, 25),
    "12": ("T. Camara", ["SF", "PF"], "POR", 26, None, 24),
    "13": ("T. Johnson", ["SG", "PG"], "WAS", 21, None, 19),
    "14": ("K. George", ["SF", "SG"], "WAS", 23, None, 20),
    "15": ("D. Mitchell", ["PG"], "MIA", 27, None, 17),
    "16": ("J. Jaquez", ["SF", "SG"], "MIL", 26, None, 18),
    "17": ("K. Jakucionis", ["PG", "SG"], "MIL", 22, None, 14),
    "18": ("R. Rival", ["SG"], "BKN", 25, None, 33),
    "19": ("O. Opponent", ["SF"], "CHI", 28, None, 30),
    "20": ("F. Filler", ["PG"], "SAS", 24, None, 16),
    "21": ("Player 21", ["PG"], "FA", 31, None, 23),
    "22": ("Player 22", ["SG"], "FA", 32, None, 22),
    "23": ("Player 23", ["SF"], "FA", 33, None, 21),
    "24": ("Player 24", ["PF"], "FA", 22, None, 20),
    "25": ("Player 25", ["C"], "FA", 23, None, 19),
    "26": ("Player 26", ["PG"], "FA", 24, None, 18),
    "27": ("Player 27", ["SG"], "FA", 25, None, 17),
    "28": ("Player 28", ["SF"], "FA", 26, None, 30),
    "29": ("Player 29", ["PF"], "FA", 27, None, 29),
    "30": ("Player 30", ["C"], "FA", 28, None, 28),
    "31": ("Player 31", ["PG"], "FA", 29, None, 27),
    "32": ("Player 32", ["SG"], "FA", 30, None, 26),
    "33": ("Player 33", ["SF"], "FA", 31, None, 25),
    "34": ("Player 34", ["PF"], "FA", 32, None, 24),
    "35": ("Player 35", ["C"], "FA", 33, None, 23),
    "36": ("Player 36", ["PG"], "FA", 22, None, 22),
    "37": ("Player 37", ["SG"], "FA", 23, None, 21),
    "38": ("Player 38", ["SF"], "FA", 24, None, 20),
    "39": ("Player 39", ["PF"], "FA", 25, None, 19),
    "40": ("Player 40", ["C"], "FA", 26, None, 18),
    "41": ("Player 41", ["PG"], "FA", 27, None, 17),
    "42": ("Player 42", ["SG"], "FA", 28, None, 30),
    "43": ("Player 43", ["SF"], "FA", 29, None, 29),
    "44": ("Player 44", ["PF"], "FA", 30, None, 28),
    "45": ("Player 45", ["C"], "FA", 31, None, 27),
    "46": ("Player 46", ["PG"], "FA", 32, None, 26),
    "47": ("Player 47", ["SG"], "FA", 33, None, 25),
    "48": ("Player 48", ["SF"], "FA", 22, None, 24),
    "49": ("Player 49", ["PF"], "FA", 23, None, 23),
    "50": ("Player 50", ["C"], "FA", 24, None, 22),
    "51": ("Player 51", ["PG"], "FA", 25, None, 21),
    "52": ("Player 52", ["SG"], "FA", 26, None, 20),
    "53": ("Player 53", ["SF"], "FA", 27, None, 19),
    "54": ("Player 54", ["PF"], "FA", 28, None, 18),
    "55": ("Player 55", ["C"], "FA", 29, None, 17),
    "56": ("Player 56", ["PG"], "FA", 30, None, 30),
}

ROSTER_POSITIONS = ["PG", "SG", "G", "SF", "PF", "F", "C", "UTIL", "UTIL",
                    "BN", "BN", "BN", "BN", "BN", "BN", "BN", "IR", "IR"]

MY_PLAYERS = [str(i) for i in range(1, 18)]
OTHER_ROSTERS = {
    rid: [str(21 + (rid - 2) * 5 + k) for k in range(5)] + seed
    for rid, seed in {
        2: ["18", "19", "20"], 3: ["51", "52"], 4: ["53", "54"],
        5: ["55", "56"], 6: ["49", "50"], 7: ["47", "48"], 8: ["45", "46"],
    }.items()
}


def players():
    return {pid: {"name": n, "pos": p, "team": t, "age": a, "status": s}
            for pid, (n, p, t, a, s, _) in PLAYERS.items()}


def _settings(w, l, pf, pa):
    return {"wins": w, "losses": l, "ties": 0, "fpts": pf, "fpts_decimal": 0,
            "fpts_against": pa, "fpts_against_decimal": 0}


def rosters():
    out = [{"roster_id": 1, "owner_id": "me", "players": MY_PLAYERS,
            "starters": MY_PLAYERS[:9],
            "settings": dict(_settings(9, 4, 1440, 1310),
                             waiver_budget_used=35, waiver_position=2)}]
    recs = {2: (10, 3, 1502, 1288), 3: (9, 4, 1399, 1350), 4: (9, 4, 1301, 1377),
            5: (8, 5, 1188, 1450), 6: (8, 5, 1420, 1390), 7: (5, 8, 1240, 1460),
            8: (3, 10, 1150, 1520)}
    for rid, pl in OTHER_ROSTERS.items():
        w, l, pf, pa = recs[rid]
        out.append({"roster_id": rid, "owner_id": f"team{rid}", "players": pl,
                    "starters": pl, "settings": _settings(w, l, pf, pa)})
    return out


def team_names():
    return {"me": "ddillonn", "team2": "Gkdall", "team3": "remydunz",
            "team4": "Tkays", "team5": "Epoole10", "team6": "FantasyHeadshot",
            "team7": "benchwarmer", "team8": "rebuilding"}


def weekly_matchups(weeks=13):
    """Every roster scores every week, the way the real endpoint returns it."""
    rs = {r["roster_id"]: r for r in rosters()}
    pairs = [(1, 2), (3, 4), (5, 6), (7, 8)]
    all_weeks = {}
    for wk in range(1, weeks + 1):
        entries = []
        for mid, (a, b) in enumerate(pairs, start=1):
            for rid in (a, b):
                pts = {}
                for pid in rs[rid]["players"]:
                    base = PLAYERS[pid][5]
                    if PLAYERS[pid][4] == "Out" and wk > 9:
                        pts[pid] = 0.0
                    else:
                        pts[pid] = round(max(base + random.gauss(0, base * 0.22), 0), 1)
                starters = rs[rid]["players"][:9]
                entries.append({
                    "roster_id": rid, "matchup_id": mid,
                    "points": round(sum(pts[p] for p in starters), 1),
                    "starters": starters,
                    "players": rs[rid]["players"],
                    "players_points": pts,
                })
        all_weeks[wk] = entries
    return all_weeks


def league():
    return {
        "league_id": "demo-nba",
        "name": "12-Team Dynasty (DEMO)",
        "sport": "nba",
        "season": "2026",
        "total_rosters": 12,
        "roster_positions": ROSTER_POSITIONS,
        "settings": {"playoff_teams": 6, "playoff_week_start": 22,
                     "trade_deadline": 18, "reserve_slots": 2, "type": 2,
                     "waiver_type": 2, "waiver_budget": 100, "draft_picks": 1,
                     "num_teams": 12},
        "scoring_settings": {"pts": 0.5, "reb": 1, "ast": 1.3, "stl": 2, "blk": 2,
                             "to": -1, "dd": 2, "td": 3, "tech": -1, "flag": -2,
                             "fg3m": 0.5, "bonus_pts_40": 2, "bonus_pts_50": 2,
                             "bonus_ast_15": 2, "bonus_reb_20": 2.5},
    }

# ------------------------------------------------------------------ NFL demo

NFL_PLAYERS = {
    "n1": ("QB Alpha", ["QB"], "PHI", 27, None, 22),
    "n2": ("RB Bravo", ["RB"], "SF", 25, None, 18),
    "n3": ("RB Charlie", ["RB"], "DET", 24, "Questionable", 14),
    "n4": ("WR Delta", ["WR"], "CIN", 26, None, 19),
    "n5": ("WR Echo", ["WR"], "MIA", 23, None, 15),
    "n6": ("WR Foxtrot", ["WR"], "LAR", 28, None, 12),
    "n7": ("TE Golf", ["TE"], "KC", 30, None, 13),
    "n8": ("K Hotel", ["K"], "BAL", 29, None, 8),
    "n9": ("DEF India", ["DEF"], "PIT", None, None, 9),
    "n10": ("RB Juliet", ["RB"], "NYJ", 26, None, 11),
    "n11": ("WR Kilo", ["WR"], "GB", 24, None, 10),
    "n12": ("QB Lima", ["QB"], "HOU", 28, None, 17),
}
for i in range(13, 75):
    NFL_PLAYERS[f"n{i}"] = (
        f"NFL Player {i}", [["QB", "RB", "WR", "TE", "K", "DEF"][i % 6]],
        "FA", 25, None, 16 - (i % 11),
    )

NFL_ROSTER_POSITIONS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF",
                        "BN", "BN", "BN", "BN", "BN", "BN", "IR", "IR"]

NFL_MY = [f"n{i}" for i in range(1, 13)]
NFL_OTHERS = {rid: [f"n{13 + (rid - 2) * 7 + k}" for k in range(7)]
              for rid in range(2, 9)}


def nfl_players():
    return {pid: {"name": n, "pos": p, "team": t, "age": a, "status": s}
            for pid, (n, p, t, a, s, _) in NFL_PLAYERS.items()}


def nfl_rosters():
    recs = {1: (7, 3, 1120, 1010), 2: (8, 2, 1180, 980), 3: (6, 4, 1050, 1030),
            4: (6, 4, 1010, 1040), 5: (5, 5, 990, 1060), 6: (4, 6, 940, 1100),
            7: (3, 7, 900, 1150), 8: (1, 9, 840, 1200)}
    out = [{"roster_id": 1, "owner_id": "me", "players": NFL_MY,
            "starters": NFL_MY[:9],
            "settings": dict(_settings(*recs[1]), waiver_position=6,
                             waiver_budget_used=0)}]
    for rid, pl in NFL_OTHERS.items():
        out.append({"roster_id": rid, "owner_id": f"team{rid}", "players": pl,
                    "starters": pl[:9],
                    "settings": dict(_settings(*recs[rid]), waiver_position=rid)})
    return out


def nfl_weekly(weeks=10):
    rs = {r["roster_id"]: r for r in nfl_rosters()}
    pairs = [(1, 2), (3, 4), (5, 6), (7, 8)]
    out = {}
    for wk in range(1, weeks + 1):
        entries = []
        for mid, (a, b) in enumerate(pairs, start=1):
            for rid in (a, b):
                pts = {}
                for pid in rs[rid]["players"]:
                    base = NFL_PLAYERS[pid][5]
                    pts[pid] = round(max(base + random.gauss(0, base * 0.35), 0), 1)
                starters = rs[rid]["players"][:9]
                entries.append({
                    "roster_id": rid, "matchup_id": mid,
                    "points": round(sum(pts[p] for p in starters), 1),
                    "starters": starters, "players": rs[rid]["players"],
                    "players_points": pts,
                })
        out[wk] = entries
    return out


def nfl_league():
    return {
        "league_id": "demo-nfl",
        "name": "NFL Redraft (DEMO)",
        "sport": "nfl",
        "season": "2026",
        "total_rosters": 8,
        "roster_positions": NFL_ROSTER_POSITIONS,
        "settings": {"playoff_teams": 6, "playoff_week_start": 15,
                     "trade_deadline": 11, "reserve_slots": 2,
                     "waiver_type": 0, "draft_picks": 0, "num_teams": 8},
        "scoring_settings": {"rec": 1, "rush_yd": 0.1, "rush_td": 6, "rec_yd": 0.1,
                             "rec_td": 6, "pass_td": 4, "fum_lost": -2,
                             "fgm_40_49": 4, "fgm_50_59": 5, "fgm_60p": 6,
                             "pts_allow_0": 10, "pts_allow_35p": -4, "sack": 1,
                             "int": 2, "def_st_td": 6},
    }
