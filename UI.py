import streamlit as st
import pandas as pd
import random
import plotly.express as px
import time

# -------------------
# CONFIG (DUMMY ON)
# -------------------
PROXY_URL = "http://localhost:8000"
USE_DUMMY = True   # <<-- Dummy flag ON by default
REFRESH_SECONDS = 5
# -------------------

st.set_page_config(page_title="Firewall Dashboard", page_icon="📊", layout="wide")
st.title("📊 AI Firewall Monitoring Dashboard (Demo Mode)")

# Dummy metrics generator
def dummy_metrics():
    base_total = random.randint(60, 110)
    allowed = random.randint(30, 70)
    redacted = random.randint(3, 18)
    blocked = random.randint(3, 18)
    return {
        "total": base_total,
        "allowed": allowed,
        "redacted": redacted,
        "blocked": blocked,
        "p50_latency_ms": round(random.uniform(15, 30), 2),
        "p95_latency_ms": round(random.uniform(50, 120), 2),
    }

def dummy_per_agent():
    return pd.DataFrame([
        {"Agent": "summarizer-agent", "Allowed": random.randint(20,50), "Redacted": random.randint(0,8), "Blocked": random.randint(0,5)},
        {"Agent": "retriever-agent",  "Allowed": random.randint(15,45), "Redacted": random.randint(0,10), "Blocked": random.randint(0,7)},
        {"Agent": "slack-bot",        "Allowed": random.randint(5,30),  "Redacted": random.randint(0,5), "Blocked": random.randint(0,10)},
    ])

def dummy_time_series():
    # simple synthetic time series
    xs = list(range(10))
    return pd.DataFrame({
        "t": [f"T-{i}" for i in xs],
        "Allowed": [random.randint(10,60) for _ in xs],
        "Blocked": [random.randint(0,12) for _ in xs],
    })

# If you later want real endpoints, flip this to False and implement the functions to call PROXY_URL
def get_metrics():
    if USE_DUMMY:
        return dummy_metrics()
    else:
        import requests
        return requests.get(f"{PROXY_URL}/metrics").json()

def get_per_agent_df():
    if USE_DUMMY:
        return dummy_per_agent()
    else:
        import requests
        return pd.DataFrame(requests.get(f"{PROXY_URL}/per_agent").json())

def get_time_series():
    if USE_DUMMY:
        return dummy_time_series()
    else:
        # fetch or build from real metrics store
        return pd.DataFrame()

# -------------------
# UI
# -------------------
# Auto-refresh indicator
st.markdown(f"*Demo mode ON — auto-refresh every {REFRESH_SECONDS}s*")

m = get_metrics()
cols = st.columns(4)
cols[0].metric("Total", m["total"])
cols[1].metric("Allowed", m["allowed"])
cols[2].metric("Redacted", m["redacted"])
cols[3].metric("Blocked", m["blocked"])

st.divider()
st.subheader("Per-Agent Statistics")
agent_df = get_per_agent_df()
st.dataframe(agent_df, use_container_width=True)

st.subheader("Action Distribution")
pie_df = pd.DataFrame({
    "Action": ["Allowed", "Redacted", "Blocked"],
    "Count": [m["allowed"], m["redacted"], m["blocked"]]
})
fig = px.pie(pie_df, values="Count", names="Action",
             color="Action",
             color_discrete_map={"Allowed":"green","Redacted":"orange","Blocked":"red"})
st.plotly_chart(fig, use_container_width=True)

st.subheader("Traffic Over Time (synthetic)")
ts = get_time_series()
fig2 = px.line(ts, x="t", y=["Allowed","Blocked"], markers=True, title="Requests per Interval")
st.plotly_chart(fig2, use_container_width=True)

# Simple auto-refresh
with st.empty():
    time.sleep(REFRESH_SECONDS)
    st.rerun()
