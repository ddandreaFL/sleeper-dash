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
</style>
"""


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

tabs = st.tabs(["Standings", "This week", "My roster", "Trades", "Settings"])


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


# ---------------------------------------------------------------- my roster

with tabs[2]:
    shape = pd.DataFrame(lg["roster_shape"])
    st.subheader("Where value is stuck on your bench")
    st.dataframe(shape, hide_index=True, use_container_width=True)
    st.caption("buried_value = points per week sitting behind your startable slots "
               "at that position. That is your tradeable surplus.")
    st.subheader("Players by production")
    st.dataframe(pd.DataFrame(lg["my_players"]), hide_index=True,
                 use_container_width=True)


# ------------------------------------------------------------------- trades

with tabs[3]:
    if ctx.get("deadline_passed"):
        st.error(f"Deadline was week {ctx.get('trade_deadline')}. Nothing to do here.")
    targets = lg.get("trade_targets") or []
    if not targets:
        st.info("No clear positional mismatches right now.")
    else:
        st.subheader("Who needs what you have")
        st.dataframe(pd.DataFrame(targets), hide_index=True, use_container_width=True)
        st.caption("fit_score pairs your surplus against how far below league median "
                   "their production at that position sits.")
    if ctx.get("pick_trading"):
        st.caption("Draft picks are tradeable in this league, so surplus can also be "
                   "converted into future capital.")
    else:
        st.caption("No pick trading in this league. Players only.")
    st.warning("Sleeper's API is read-only. Build the offer in the app yourself.")


# ----------------------------------------------------------------- settings

with tabs[4]:
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
