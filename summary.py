"""Print a markdown digest of the current snapshot.

Used by the GitHub Action to fill the run summary page, so you get a readable
gameday brief without opening the app. Also fine to run locally.
"""

import json
import os

SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "snapshot.json")


def main():
    if not os.path.exists(SNAP):
        print("no snapshot")
        return
    with open(SNAP) as f:
        snap = json.load(f)

    print(f"# Sleeper brief\n\n_generated {snap['generated_at']}_")
    if snap.get("demo"):
        print("\n> **DEMO DATA** - numbers are fake.\n")

    for lg in snap["leagues"]:
        p = lg.get("playoffs") or {}
        print(f"\n## {lg['name']} ({lg['sport'].upper()}) - week {lg['week']}\n")
        print(f"Seed **{p.get('seed','?')}** of {p.get('teams','?')}, "
              f"top {p.get('spots','?')} make it. Status: **{p.get('status','?')}**, "
              f"{p.get('games_left','?')} games left.\n")

        ctx = lg.get("context") or {}
        d = ctx.get("weeks_to_deadline")
        if ctx.get("deadline_passed"):
            print(f"> Trade deadline (week {ctx.get('trade_deadline')}) has passed.\n")
        elif isinstance(d, int) and d <= 3:
            print(f"> **Trade deadline in {d} week(s)** "
                  f"(week {ctx.get('trade_deadline')}).\n")

        m = lg.get("matchup")
        if m:
            side = "favored" if m["edge"] > 0 else "underdog"
            print(f"### Week {m['week']} vs {m['opp']['team']}\n")
            print(f"Live: {m['me']['points']} - {m['opp']['points']}. "
                  f"On season averages you are **{side} by {abs(m['edge']):.1f}**.\n")
            if m["me"]["hurt"]:
                print(f"- Starting hurt: {', '.join(m['me']['hurt'])}")
            for a in m.get("bench_alerts") or []:
                print(f"- Bench watch: {a['bench']} ({a['bench_avg']}/wk) > "
                      f"{a['starter']} ({a['starter_avg']}/wk)")
            print()

        shape = [r for r in lg.get("roster_shape") or [] if r["buried_value"] > 0]
        if shape:
            print("### Tradeable surplus\n")
            print("| pos | rostered | slots | buried pts/wk | best buried |")
            print("| --- | --- | --- | --- | --- |")
            for r in shape[:5]:
                print(f"| {r['pos']} | {r['rostered']} | {r['slots']} | "
                      f"{r['buried_value']} | {r['best_buried'] or '-'} |")
            print()

        targets = lg.get("trade_targets") or []
        if targets:
            print("### Trade fits\n")
            for t in targets[:3]:
                print(f"- **{t['team']}** (fit {t['fit_score']}): {t['notes']}")
            print()

    print("\n_Sleeper's API is read-only. Offers still get built in the app._")


if __name__ == "__main__":
    main()
