# HANDOFF: sleeper-dash

Written for a fresh Claude Code session picking this project up cold.
Everything below was built in a sandbox **with no network access to
api.sleeper.app**, so read the "verified vs not" section before trusting
anything.

---

## What this is

A personal dashboard for two Sleeper fantasy leagues (one NBA dynasty, one
NFL redraft) owned by user `ddillonn`. Standings, playoff picture, weekly
matchup analysis, roster surplus, and a trade finder. Streamlit UI, refreshed
by a scheduled GitHub Action.

**The Sleeper API is read-only.** No auth, no key, no writes. The tool
recommends; the human executes in the Sleeper app. Do not add code that
attempts to set lineups, claim waivers, or send trade offers. It is not
possible and any such code is a hallucination.

Rate limit guidance from Sleeper: stay under 1000 calls/min. `sleeper.py`
caches to `.cache/` to stay far below that.

---

## Architecture

```
sleeper.py     API client + disk cache. Only file that touches the network.
analysis.py    Pure functions. No I/O. All the actual logic lives here.
refresh.py     Orchestrates: fetch -> analyze -> write data/snapshot.json
app.py         Streamlit UI. Reads the snapshot. Never calls the API directly.
summary.py     Prints a markdown brief (used for the Actions job summary).
demo_data.py   Fixtures shaped like real payloads. Powers --demo.
```

The snapshot is the contract between the backend and the UI. If you change a
key in `refresh.build_league_payload`, update `app.py` in the same commit.

### The one design decision that matters

We do **not** compute fantasy points. `/league/{id}/matchups/{week}` returns
`players_points`, already scored using that league's own settings. Summing
across weeks gives season-to-date value per player, correct by construction,
with no external stats provider.

Consequences to keep in mind:
- Values only exist for players **rostered during the weeks pulled**. Free
  agents are 0. The trade finder is therefore blind to the waiver wire.
- Custom scoring (assists at 1.3, DD +2, 20+ reb +2.5, full PPR in the NFL
  league) is handled automatically. Never hardcode scoring weights.

---

## Verified vs not

**Verified in the sandbox:**
- `python refresh.py --demo` builds a two-league snapshot cleanly.
- `streamlit run app.py` boots and serves HTTP 200 with no errors in the log.
- `python summary.py` produces valid markdown.
- `git init && git add -A && git commit` produces a clean 11-file tree.
- `bash -n setup.sh` passes.

**NOT verified. Assume these are wrong until proven otherwise:**
- Every live API code path. Nothing has ever hit api.sleeper.app.
- Sleeper settings key names: `waiver_type`, `waiver_budget`, `draft_picks`,
  `trade_deadline`, `reserve_slots`. All read defensively in
  `analysis.league_context`, all degrade to None instead of crashing.
- Roster settings keys `waiver_position` and `waiver_budget_used`.
- Whether the NBA dynasty league lives under season `"2026"` or `"2025"`.
  Sleeper labels NBA seasons by starting year and the app is being set up in
  Aug 2026. If a league comes back empty, try the other year.
- Whether `/state/nba` returns a sensible `week` in the offseason.

---

## First session, in order

1. **Prove the API works at all.**
   ```bash
   python -c "import sleeper, json; print(json.dumps(sleeper.user('ddillonn'), indent=2))"
   ```
   If this fails, nothing else matters.

2. **Find the leagues.** Try both season strings for NBA:
   ```bash
   python -c "import sleeper; u=sleeper.user('ddillonn'); \
   print([(l['name'],l['season']) for s in ('2026','2025') \
   for l in sleeper.leagues(u['user_id'],'nba',s)])"
   ```
   Then set the right default in `SPORTS`/`refresh.py` if `/state/nba` is wrong.

3. **Dump one real league object** and diff the settings keys against what
   `analysis.league_context` expects. Fix the key names. This is the single
   most likely source of wrong output. Expected ground truth from the app UI:

   | | NBA dynasty | NFL redraft |
   | --- | --- | --- |
   | Teams | 12 | 8 |
   | Playoffs | 6 teams, week 22 | 6 teams, week 15 |
   | Trade deadline | week 18 | week 11 |
   | Waivers | FAAB | reverse standings |
   | Pick trading | yes | no |

   If the header renders "priority" for the NBA league, the key name is wrong,
   not the league.

4. **Run a real refresh** and sanity-check player values against the Sleeper
   app. A top NBA player in this scoring should land somewhere around 45-55
   points per week. If everyone shows 0, `players_points` is empty for the
   weeks pulled (likely offseason) and you should pull last season instead.

5. **Then** run `./setup.sh` to create the private repo.

---

## Known gaps worth fixing, roughly by value

- **Free agents are invisible.** Highest-value fix. Pull `/players/{sport}` +
  trending adds, or accumulate `players_points` league-wide rather than only
  from matchup rosters.
- **Matchup projection uses season averages.** No rest days, no back-to-backs,
  no games-this-week count. For NBA specifically, a player on a 4-game week is
  worth far more than the same player on a 2-game week, and the tool currently
  cannot see that. This is probably the biggest real-world accuracy gap.
- **Playoff clinch counts wins only.** Ignores tiebreakers and remaining
  schedule. Deliberately conservative; label it as such rather than making it
  confidently wrong.
- **Bench alerts use season averages, not tonight's slate.** A bench player who
  plays tonight beats a starter who doesn't, regardless of averages.
- **No dynasty asset values.** Draft picks are ignored entirely, which matters
  in the NBA league where pick trading is allowed.

---

## Ground rules for this project

- Demo data before live data. Keep `--demo` working; it is how the UI gets
  tested without hammering the API.
- Be honest in the output about what is estimated vs measured. The user
  explicitly prefers a caveat over false confidence.
- No em dashes in generated docs or UI copy.
- Do not add features that imply write access to Sleeper.

---

## Paste this to start the Claude Code session

> I'm picking up a project called sleeper-dash. Read HANDOFF.md and README.md
> first, then work through the "First session, in order" list. The code has
> never touched the live Sleeper API, so expect the settings key names and the
> NBA season string to be wrong. Verify each step against real API responses
> before moving on, and tell me what you actually confirmed vs what you're
> assuming. Do not create the GitHub repo until step 4 passes.
