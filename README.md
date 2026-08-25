# Sleeper Dash

A personal dashboard for your Sleeper fantasy leagues. NBA and NFL in one app,
standings, playoff picture, weekly matchup analysis, roster surplus, and a
trade finder.

**The Sleeper API is read-only.** This tool recommends. You still tap accept in
the app. Nothing here can set a lineup, submit a waiver, or send an offer.

## Quick start

```bash
pip install -r requirements.txt
python refresh.py --demo        # builds data/snapshot.json from fake data
streamlit run app.py            # open http://localhost:8501
```

Once the demo looks right:

```bash
python refresh.py --user ddillonn --sport all
```

## How scoring works

We never compute fantasy points ourselves. The `/league/{id}/matchups/{week}`
endpoint returns `players_points`, already scored using **your league's own
settings** (assists at 1.3, the double-double bonus, the 20+ rebound bonus, all
of it). Summing that across weeks gives a season-to-date value per player that
is correct by construction, with no external stats provider and no API key.

Consequence: player values only exist for players who were rostered during the
weeks pulled. Free agents show 0. That is a real limitation, not a bug.

## Files

| file | what it does |
| --- | --- |
| `sleeper.py` | API client, disk cache, rate-limit friendly |
| `analysis.py` | standings, playoff math, player values, matchups, trade finder |
| `refresh.py` | pulls everything, writes `data/snapshot.json` |
| `app.py` | Streamlit UI, reads the snapshot |
| `summary.py` | markdown brief for the Actions run page |
| `demo_data.py` | fixtures so everything runs before touching live data |

## Deploy

**Streamlit Community Cloud** (free): push this repo to GitHub, point Streamlit
at `app.py`. The app reads the committed snapshot, so it boots instantly.

**GitHub Actions** (free on public repos): `.github/workflows/refresh.yml` runs
twice daily, rebuilds the snapshot, writes a brief to the run summary, and
commits the result. Set a repo variable `SLEEPER_USER` to your username
(Settings, Secrets and variables, Actions, Variables tab). No secret needed,
there is no API key.

## Your two leagues

Nothing about these is hardcoded, the app reads them from the API. Listed so
you can tell at a glance whether a live pull looks right.

| | NBA dynasty | NFL redraft |
| --- | --- | --- |
| Teams | 12 | 8 |
| Playoffs | 6 teams, week 22 | 6 teams, week 15 |
| Trade deadline | week 18 | week 11 |
| Waivers | FAAB bidding | reverse standings |
| Pick trading | yes | no |
| Scoring quirks | assists 1.3, DD +2, TD +3, 20+ reb +2.5 | full PPR, tiered FG and points-allowed |

## Known gaps

- Playoff clinch logic counts wins only. It ignores tiebreakers and the actual
  schedule, so treat "clinched" as conservative.
- Matchup projection uses season averages, not real projections. It does not
  know about rest days, back-to-backs, or that someone just got traded.
- Free agents have no value attached, so the trade finder only sees rostered
  players.
- NBA season strings on Sleeper can be the starting year of the season. If a
  league comes back empty, try `--season` with the other year.
