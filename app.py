"""Streamlit dashboard. Reads data/snapshot.json, which refresh.py builds.

    streamlit run app.py

Nothing here calls the API, so the UI is instant and Sleeper stays happy.
Hit "Refresh from Sleeper" to shell out to refresh.py when you want live data.
"""

import json
import os
import subprocess
import sys

import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "data", "snapshot.json")

st.set_page_config(page_title="Sleeper Dash", page_icon="🏀", layout="wide")


# ------------------------------------------------------ SportsCenter broadcast skin

BROADCAST_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@500;600;700;800&family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&display=swap');

:root {
  --sc-red: #d50a0a;
  --sc-red-bright: #ff2b2b;
  --sc-amber: #ff7a00;
  --sc-blue: #2b7de9;
  --sc-ink: #0a0a0d;
  --sc-panel: #16161c;
  --sc-panel-2: #1e1e26;
  --sc-line: #2c2c36;
  --sc-chrome-1: #ffffff;
  --sc-chrome-2: #b9bec6;
  --sc-chrome-3: #7d828b;
  --sc-text: #f4f4f5;
  --sc-muted: #9aa0a6;
}

/* studio background: near black with a warm red floor glow */
.stApp {
  background:
    radial-gradient(1200px 500px at 50% -10%, rgba(213,10,10,0.18), transparent 60%),
    radial-gradient(900px 600px at 50% 120%, rgba(43,125,233,0.10), transparent 60%),
    var(--sc-ink);
}

html, body, [class*="css"], .stApp, p, span, div, label, td, th {
  font-family: 'Barlow', system-ui, sans-serif;
}

/* broadcast headings: condensed, uppercase, chrome */
h1, h2, h3, h4 {
  font-family: 'Saira Condensed', 'Barlow Condensed', sans-serif !important;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 800 !important;
}
h1 {
  background: linear-gradient(180deg, var(--sc-chrome-1) 0%, var(--sc-chrome-2) 55%, var(--sc-chrome-3) 100%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}
h2, h3, h4 { color: #e9eaec !important; }

/* the wordmark banner */
.sc-banner {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 20px; margin: -8px 0 6px 0;
  background: linear-gradient(90deg, #000 0%, #17070a 40%, #2a0608 100%);
  border: 1px solid var(--sc-line);
  border-left: 6px solid var(--sc-red);
  border-radius: 8px;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.02), 0 12px 30px rgba(0,0,0,0.5), inset 0 0 40px rgba(213,10,10,0.08);
}
.sc-wordmark {
  font-family: 'Saira Condensed', sans-serif; font-weight: 800;
  font-size: 40px; line-height: 1; letter-spacing: 0.02em;
  background: linear-gradient(180deg, #fff 0%, #c7ccd3 55%, #83888f 100%);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.sc-puck {
  display: inline-flex; align-items: center; justify-content: center;
  width: 46px; height: 46px; border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #ff4d4d, var(--sc-red) 60%, #8a0606 100%);
  box-shadow: 0 0 18px rgba(255,43,43,0.6), inset 0 -3px 8px rgba(0,0,0,0.4);
  font-family: 'Saira Condensed', sans-serif; font-weight: 800; font-size: 20px;
  color: #fff; letter-spacing: -0.03em; text-shadow: 0 1px 2px rgba(0,0,0,0.5);
  flex: 0 0 auto;
}
.sc-sub {
  margin-left: auto; text-align: right;
  font-family: 'Saira Condensed', sans-serif; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--sc-muted); font-size: 13px;
}
.sc-sub b { color: var(--sc-amber); }

/* the scrolling ticker */
.sc-ticker {
  position: relative; overflow: hidden; white-space: nowrap;
  background: linear-gradient(180deg, #cc0000, #8a0000);
  border-radius: 6px; margin: 8px 0 4px 0;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08), 0 6px 18px rgba(0,0,0,0.4);
}
.sc-ticker .tag {
  position: absolute; left: 0; top: 0; bottom: 0; z-index: 2;
  display: flex; align-items: center; padding: 0 14px;
  background: #0a0a0d; color: #fff;
  font-family: 'Saira Condensed', sans-serif; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.08em; font-size: 14px;
  border-right: 3px solid var(--sc-amber);
}
.sc-ticker .track {
  display: inline-block; padding: 8px 0 8px 130px;
  animation: sc-scroll 32s linear infinite;
  font-family: 'Barlow Condensed', sans-serif; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.04em; font-size: 15px; color: #fff;
}
.sc-ticker .track span { margin: 0 26px; opacity: 0.95; }
.sc-ticker .track b { color: #ffe08a; }
@keyframes sc-scroll { from { transform: translateX(0); } to { transform: translateX(-50%); } }

/* metrics as broadcast stat boxes */
[data-testid="stMetric"] {
  background: linear-gradient(180deg, var(--sc-panel-2), var(--sc-panel));
  border: 1px solid var(--sc-line);
  border-top: 3px solid var(--sc-red);
  border-radius: 8px; padding: 12px 14px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.35);
}
[data-testid="stMetricLabel"] p {
  font-family: 'Saira Condensed', sans-serif !important; font-weight: 700 !important;
  text-transform: uppercase; letter-spacing: 0.08em; color: var(--sc-muted) !important;
  font-size: 12px !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Saira Condensed', sans-serif !important; font-weight: 800 !important;
  color: #fff !important; letter-spacing: 0.01em;
}

/* tabs like a broadcast nav rail */
[data-baseweb="tab-list"] {
  gap: 2px; background: var(--sc-panel); padding: 4px; border-radius: 8px;
  border: 1px solid var(--sc-line);
}
[data-baseweb="tab"] {
  font-family: 'Saira Condensed', sans-serif !important; font-weight: 700 !important;
  text-transform: uppercase; letter-spacing: 0.06em; color: var(--sc-muted) !important;
  border-radius: 6px; padding: 6px 16px !important;
}
[data-baseweb="tab"][aria-selected="true"] {
  background: linear-gradient(180deg, var(--sc-red), #9c0606) !important;
  color: #fff !important;
}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { background: transparent !important; }

/* dataframes: dark stat sheet */
[data-testid="stDataFrame"] {
  border: 1px solid var(--sc-line); border-radius: 8px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.3);
}

/* buttons: red broadcast button */
.stButton > button {
  font-family: 'Saira Condensed', sans-serif; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.05em;
  background: linear-gradient(180deg, var(--sc-red), #9c0606);
  color: #fff; border: 1px solid #6d0505; border-radius: 6px;
}
.stButton > button:hover { background: linear-gradient(180deg, var(--sc-red-bright), var(--sc-red)); border-color: var(--sc-red); }

/* sidebar as a control desk */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #101014, #0b0b0e);
  border-right: 1px solid var(--sc-line);
}
[data-testid="stSidebar"] h1 { font-size: 26px; }

/* section captions */
[data-testid="stCaptionContainer"] p { color: var(--sc-muted) !important; letter-spacing: 0.02em; }

/* Dynatyze-style player value cards */
.sc-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(215px, 1fr)); gap: 12px; margin: 6px 0 14px 0; }
.sc-card {
  position: relative; display: flex; align-items: center; gap: 12px;
  background: linear-gradient(180deg, var(--sc-panel-2), var(--sc-panel));
  border: 1px solid var(--sc-line); border-left: 4px solid var(--sc-red);
  border-radius: 10px; padding: 12px 14px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.35);
}
.sc-ovr {
  flex: 0 0 auto; width: 52px; height: 52px; border-radius: 10px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  font-family: 'Saira Condensed', sans-serif; line-height: 1;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.12), 0 4px 10px rgba(0,0,0,0.4);
}
.sc-ovr .n { font-size: 24px; font-weight: 800; }
.sc-ovr .l { font-size: 9px; font-weight: 700; letter-spacing: 0.12em; opacity: 0.85; }
.tier-elite  { background: linear-gradient(180deg,#ffd45a,#e0940c); color:#1a1200; }
.tier-gold   { background: linear-gradient(180deg,#f0f0f2,#b7bcc4); color:#15151a; }
.tier-silver { background: linear-gradient(180deg,#aeb4bd,#6f757e); color:#0c0c10; }
.tier-bronze { background: linear-gradient(180deg,#c98a5a,#7c4a25); color:#160c04; }
.tier-base   { background: linear-gradient(180deg,#3a3a44,#26262e); color:#c9ccd2; }
.sc-meta { min-width: 0; }
.sc-name {
  font-family: 'Saira Condensed', sans-serif; font-weight: 700; font-size: 16px;
  color: #fff; text-transform: uppercase; letter-spacing: 0.02em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sc-line2 { font-size: 12px; color: var(--sc-muted); margin: 2px 0 5px 0; letter-spacing: 0.03em; }
.sc-line2 b { color: #d7dade; }
.sc-chip {
  display: inline-block; font-family: 'Saira Condensed', sans-serif; font-weight: 700;
  font-size: 10px; letter-spacing: 0.09em; text-transform: uppercase;
  padding: 2px 8px; border-radius: 999px;
}
.chip-buy  { background: rgba(34,197,94,0.16);  color:#4ade80; border:1px solid rgba(34,197,94,0.4); }
.chip-sell { background: rgba(255,122,0,0.16);  color:#ff9d3d; border:1px solid rgba(255,122,0,0.45); }
.chip-hold { background: rgba(154,160,166,0.14);color:#b6bcc4; border:1px solid rgba(154,160,166,0.35); }
.sc-mkt { font-size: 11px; color: var(--sc-muted); margin-top: 4px; }
.sc-mkt b { color: var(--sc-blue); }
</style>
"""


TIERS = [(90, "tier-elite"), (80, "tier-gold"), (70, "tier-silver"),
         (60, "tier-bronze"), (0, "tier-base")]


def _tier(ovr):
    for cut, cls in TIERS:
        if ovr >= cut:
            return cls
    return "tier-base"


def player_card(v):
    chip = {"BUY": "chip-buy", "SELL": "chip-sell"}.get(v["signal"], "chip-hold")
    age = f"{v['age']}y" if v.get("age") is not None else "age n/a"
    line2 = f"<b>{v['pos1']}</b> · {v.get('team') or 'FA'} · {age}"
    mkt = (f'<div class="sc-mkt">mkt <b>{v["market"]:,}</b></div>'
           if v.get("market") else "")
    return (
        f'<div class="sc-card">'
        f'<div class="sc-ovr {_tier(v["ovr"])}"><span class="n">{v["ovr"]}</span>'
        f'<span class="l">OVR</span></div>'
        f'<div class="sc-meta">'
        f'<div class="sc-name">{v["name"]}</div>'
        f'<div class="sc-line2">{line2}</div>'
        f'<span class="sc-chip {chip}">{v["signal"]}</span>'
        f'<div class="sc-mkt">{v["ppw"]} ppw · val {v["value"]}</div>'
        f'{mkt}'
        f'</div></div>'
    )


def card_grid(rows):
    cards = "".join(player_card(v) for v in rows)
    st.markdown(f'<div class="sc-cards">{cards}</div>', unsafe_allow_html=True)


def broadcast_skin():
    st.markdown(BROADCAST_CSS, unsafe_allow_html=True)


def banner(subtitle_html=""):
    st.markdown(
        f'<div class="sc-banner">'
        f'<span class="sc-puck">SC</span>'
        f'<span class="sc-wordmark">SPORTSCENTER</span>'
        f'<span class="sc-sub">{subtitle_html}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def ticker(tag, items):
    """A looping broadcast crawl. items is a list of html-safe strings."""
    body = "".join(f"<span>{it}</span>" for it in items) or "<span>Standby...</span>"
    run = body * 2  # doubled so the -50% loop is seamless
    st.markdown(
        f'<div class="sc-ticker"><div class="tag">{tag}</div>'
        f'<div class="track">{run}</div></div>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load(path, mtime):
    with open(path) as f:
        return json.load(f)


def snapshot():
    if not os.path.exists(SNAPSHOT):
        return None
    return load(SNAPSHOT, os.path.getmtime(SNAPSHOT))


def refresh(username, sport):
    cmd = [sys.executable, os.path.join(HERE, "refresh.py")]
    cmd += ["--demo"] if not username else ["--user", username, "--sport", sport]
    with st.spinner("pulling from sleeper..."):
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    st.cache_data.clear()
    return r


# ----------------------------------------------------------------- sidebar

broadcast_skin()

st.sidebar.title("Sleeper Dash")
username = st.sidebar.text_input("Sleeper username", value="ddillonn")
sport = st.sidebar.selectbox("Sport", ["all", "nba", "nfl"])
col_a, col_b = st.sidebar.columns(2)
if col_a.button("Refresh", use_container_width=True):
    res = refresh(username, sport)
    st.sidebar.code((res.stdout or "") + (res.stderr or ""), language="text")
if col_b.button("Demo data", use_container_width=True):
    res = refresh(None, sport)
    st.sidebar.code((res.stdout or "") + (res.stderr or ""), language="text")

snap = snapshot()
if not snap or not snap.get("leagues"):
    banner("Off air")
    st.info("No snapshot yet. Hit **Demo data** to see the app, or **Refresh** to pull live.")
    st.stop()

if snap.get("demo"):
    st.sidebar.warning("Showing DEMO data. Numbers are fake.")
st.sidebar.caption(f"generated {snap['generated_at']}")

names = [f"{l['name']} ({l['sport'].upper()})" for l in snap["leagues"]]
choice = st.sidebar.radio("League", names)
lg = snap["leagues"][names.index(choice)]


# ------------------------------------------------------------------- header

p = lg.get("playoffs") or {}
ctx = lg.get("context") or {}

sport_tag = lg["sport"].upper()
subtitle = (f"{sport_tag} <b>WEEK {lg['week']}</b> &nbsp;|&nbsp; "
            f"SEED {p.get('seed', '?')} OF {p.get('teams', '?')}")
banner(subtitle)

# the crawl: top standings + your status, broadcast style
crawl = [f"<b>{lg['name'].upper()}</b>"]
for row in (lg.get("standings") or [])[:6]:
    crawl.append(f"{row['seed']}. {row['team'].upper()} ({row['record']}) "
                 f"<b>{row['pf']}</b> PF")
if p.get("status"):
    crawl.append(f"PLAYOFF WATCH: <b>{p['status'].upper()}</b>")
m = lg.get("matchup")
if m:
    crawl.append(f"THIS WEEK: {m['me']['team'].upper()} VS {m['opp']['team'].upper()} "
                 f"(EDGE <b>{m['edge']:+.1f}</b>)")
ticker(sport_tag, crawl)

st.markdown(f"### {lg['name']}")
if lg.get("note"):
    st.caption(lg["note"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Week", lg["week"])
c2.metric("Seed", f"{p.get('seed', '?')} of {p.get('teams', '?')}")
c3.metric("Playoff status", p.get("status", "unknown"))
c4.metric("Games left", p.get("games_left", "?"))

d = ctx.get("weeks_to_deadline")
if ctx.get("deadline_passed"):
    st.error(f"Trade deadline passed (week {ctx.get('trade_deadline')}). "
             "The trade tab is now a museum exhibit.")
elif isinstance(d, int) and d <= 3:
    st.warning(f"Trade deadline in **{d} week(s)** (week {ctx.get('trade_deadline')}).")

bits = []
if ctx.get("waiver_mode") == "FAAB":
    left = ctx.get("faab_left")
    bits.append(f"FAAB{f': {left} left' if left is not None else ''}")
elif ctx.get("waiver_position"):
    bits.append(f"waiver priority #{ctx['waiver_position']}")
if ctx.get("playoff_share"):
    bits.append(f"{int(ctx['playoff_share'] * 100)}% of the league makes playoffs")
if not ctx.get("pick_trading"):
    bits.append("no pick trading")
if bits:
    st.caption(" · ".join(bits))

tabs = st.tabs(["Standings", "This Week", "Values", "Trade Calc",
                "Power", "Trends", "Roster", "Settings"])


# ---------------------------------------------------------------- standings

with tabs[0]:
    spots = p.get("spots", 6)
    df = pd.DataFrame(lg["standings"])
    df["playoffs"] = df["seed"].apply(lambda s: "IN" if s <= spots else "out")
    st.dataframe(
        df[["seed", "team", "record", "pf", "pa", "diff", "playoffs"]],
        hide_index=True, use_container_width=True,
    )
    st.subheader("Roster strength (points per week of your best startable lineup)")
    sdf = pd.DataFrame(lg["strengths"]).set_index("team")
    st.bar_chart(sdf["strength"], horizontal=True, color="#d50a0a")
    st.caption("Strength uses season-to-date scoring from this league's own settings, "
               "so custom scoring is already baked in.")


# ---------------------------------------------------------------- this week

with tabs[1]:
    m = lg.get("matchup")
    if not m:
        st.info("No matchup this week (offseason, bye, or playoffs bracket).")
    else:
        left, right = st.columns(2)
        left.metric(m["me"]["team"], m["me"]["points"],
                    f"expected {m['me']['expected']}")
        right.metric(m["opp"]["team"], m["opp"]["points"],
                     f"expected {m['opp']['expected']}")
        verdict = "favored" if m["edge"] > 0 else "underdog"
        st.subheader(f"You are {verdict} by {abs(m['edge']):.1f} points per week")

        if m["me"]["hurt"]:
            st.error("Starting hurt: " + ", ".join(m["me"]["hurt"]))
        if m["opp"]["hurt"]:
            st.success("They are starting hurt: " + ", ".join(m["opp"]["hurt"]))

        for a in m.get("bench_alerts") or []:
            st.warning(f"Bench watch: {a['bench']} ({a['bench_avg']}/wk) is out-scoring "
                       f"starter {a['starter']} ({a['starter_avg']}/wk)")

        lc, rc = st.columns(2)
        lc.caption("Your lineup")
        lc.dataframe(pd.DataFrame(m["me"]["lineup"]), hide_index=True,
                     use_container_width=True)
        rc.caption("Their lineup")
        rc.dataframe(pd.DataFrame(m["opp"]["lineup"]), hide_index=True,
                     use_container_width=True)


# ---------------------------------------------------------------- values

with tabs[2]:
    vals = lg.get("values") or []
    if not vals:
        st.info("No player values yet. Once your roster is drafted and games are "
                "scored, dynasty values populate here.")
    else:
        my_vals = [v for v in vals if v["roster_id"] == lg["my_roster_id"]]
        st.subheader("Your dynasty assets")
        card_grid((my_vals or vals)[:8])

        st.subheader("League dynasty rankings")
        f1, f2 = st.columns([1, 1])
        pos_sel = f1.selectbox("Position", ["All"] + sorted({v["pos1"] for v in vals}))
        mine_only = f2.toggle("My roster only")
        rows = vals
        if pos_sel != "All":
            rows = [v for v in rows if v["pos1"] == pos_sel]
        if mine_only:
            rows = [v for v in rows if v["roster_id"] == lg["my_roster_id"]]
        st.dataframe(pd.DataFrame([{
            "OVR": v["ovr"], "player": v["name"], "pos": v["pos"], "team": v["team"],
            "age": v["age"], "value": v["value"], "ppw": v["ppw"],
            "signal": v["signal"], "market": v.get("market"),
        } for v in rows]), hide_index=True, use_container_width=True, height=460)
        st.caption(
            "OVR 0-99 is normalized within this league's rostered pool. " +
            ("NBA OVR is the dashboard's derived model: your league scoring adjusted "
             "by an age curve (no free market API exists for NBA)."
             if lg["sport"] == "nba" else
             "NFL 'market' is FantasyCalc consensus value, shown for reference."))


# --------------------------------------------------------------- trade calc

with tabs[3]:
    vals = lg.get("values") or []
    if not vals:
        st.info("The trade calculator needs a drafted roster with scoring history.")
    else:
        by_id = {v["player_id"]: v for v in vals}
        opts = {f"{v['name']} ({v.get('team') or 'FA'}, {v['pos1']}, OVR {v['ovr']})":
                v["player_id"] for v in sorted(vals, key=lambda x: -x["value"])}
        picks = lg.get("pick_values") or {}
        use_picks = bool(picks and ctx.get("pick_trading"))
        if ctx.get("deadline_passed"):
            st.error(f"Trade deadline (week {ctx.get('trade_deadline')}) has passed. "
                     "This is now a what-if machine.")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Side A sends")
            a_pl = st.multiselect("Players", list(opts), key="a_pl")
            a_pk = st.multiselect("Picks", list(picks), key="a_pk") if use_picks else []
        with c2:
            st.markdown("#### Side B sends")
            b_pl = st.multiselect("Players", list(opts), key="b_pl")
            b_pk = st.multiselect("Picks", list(picks), key="b_pk") if use_picks else []

        def total(pls, pks):
            return round(sum(by_id[opts[l]]["value"] for l in pls if l in opts)
                         + sum(picks[k] for k in pks if k in picks), 1)
        ta, tb = total(a_pl, a_pk), total(b_pl, b_pk)

        m1, m2, m3 = st.columns(3)
        m1.metric("Side A value", ta)
        m2.metric("Side B value", tb)
        m3.metric("Difference", round(ta - tb, 1))

        if ta == 0 and tb == 0:
            st.info("Add players (and picks) to each side to grade the deal.")
        else:
            hi, lo = max(ta, tb), min(ta, tb)
            margin = (hi - lo) / hi * 100 if hi else 0
            if margin <= 10:
                st.success(f"Fair trade, within {margin:.0f} percent.")
            else:
                st.warning(f"{'Side A' if ta > tb else 'Side B'} wins by "
                           f"{hi - lo:.1f} value ({margin:.0f} percent).")
        st.caption(
            "Value is age-adjusted production in this league's scoring. " +
            ("NBA values are the dashboard's derived model; pick values are rough "
             "estimates." if lg["sport"] == "nba" else
             "NFL cards also carry FantasyCalc market value for reference."))

        targets = lg.get("trade_targets") or []
        if targets:
            with st.expander("Suggested targets: teams that need your surplus"):
                st.dataframe(pd.DataFrame(targets), hide_index=True,
                             use_container_width=True)
        st.warning("Sleeper's API is read-only. Build the offer in the app yourself.")


# ------------------------------------------------------------------- power

with tabs[4]:
    pr = lg.get("power_rankings") or []
    if not pr:
        st.info("Power rankings need drafted rosters with scoring history.")
    else:
        st.subheader("Team power rankings (by startable value)")
        st.bar_chart(pd.DataFrame(pr).set_index("team")["starters_value"],
                     horizontal=True, color="#d50a0a")
        st.dataframe(pd.DataFrame([{
            "rank": t["rank"], "team": t["team"],
            "starters_value": t["starters_value"], "total_value": t["total_value"],
            "avg_age": t["avg_age"], "window": t["window"],
            "top_player": t["top_player"], "top_ovr": t["top_ovr"],
        } for t in pr]), hide_index=True, use_container_width=True)
        st.caption("Window: juggernaut = contender and young, win-now = contender and "
                   "older, rising = young rebuild, rebuild = older and light on value.")


# ------------------------------------------------------------------ trends

with tabs[5]:
    tr = lg.get("trends") or {}
    if not any(tr.values()):
        st.info("Buy-low and sell-high signals appear once there is week-to-week "
                "scoring history.")
    else:
        def trend_df(rows):
            return pd.DataFrame([{
                "OVR": v["ovr"], "player": v["name"], "pos": v["pos1"],
                "age": v["age"], "ppw": v["ppw"], "recent": v["recent"],
                "why": v["signal_reason"],
            } for v in rows])

        st.subheader("Sell high, your roster")
        sm = tr.get("sell_mine") or []
        if sm:
            st.dataframe(trend_df(sm), hide_index=True, use_container_width=True)
        else:
            st.caption("Nobody on your roster is flashing sell-high right now.")

        st.subheader("Buy low, target on other rosters")
        bt = tr.get("buy_targets") or []
        if bt:
            st.dataframe(trend_df(bt), hide_index=True, use_container_width=True)
        else:
            st.caption("No clear buy-low targets across the league right now.")

        st.subheader("Hold or buy more, your young slumpers")
        bm = tr.get("buy_mine") or []
        if bm:
            st.dataframe(trend_df(bm), hide_index=True, use_container_width=True)
        else:
            st.caption("None flagged.")
        st.caption("Signals blend age vs positional peak with recent form vs season "
                   "baseline. Directional, not gospel.")


# ------------------------------------------------------------------- roster

with tabs[6]:
    shape = pd.DataFrame(lg["roster_shape"])
    st.subheader("Where value is stuck on your bench")
    st.dataframe(shape, hide_index=True, use_container_width=True)
    st.caption("buried_value = points per week sitting behind your startable slots "
               "at that position. That is your tradeable surplus.")
    st.subheader("Players by production")
    st.dataframe(pd.DataFrame(lg["my_players"]), hide_index=True,
                 use_container_width=True)


# ----------------------------------------------------------------- settings

with tabs[7]:
    st.subheader("Scoring")
    ss = lg.get("scoring_settings") or {}
    if ss:
        st.dataframe(
            pd.DataFrame(sorted(ss.items()), columns=["stat", "value"]),
            hide_index=True, use_container_width=True,
        )
    st.subheader("League settings")
    st.json(lg.get("settings") or {})
    st.subheader("Lineup slots")
    st.write(" · ".join(lg["roster_positions"]))
