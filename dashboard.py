import streamlit as st
import pandas as pd
import random
import plotly.express as px
import time

# -------------------
# CONFIG
# -------------------
PROXY_URL = "http://localhost:8000"
REFRESH_SECONDS = 10
# -------------------

st.set_page_config(page_title="Firewall Dashboard", page_icon="📊", layout="wide")

# Sidebar for configuration
st.sidebar.header("⚙️ Dashboard Settings")
USE_DUMMY = st.sidebar.toggle(
    "Use Dummy Data", 
    value=False, 
    help="Toggle between real observability data and dummy data"
)

if USE_DUMMY:
    st.sidebar.success("📊 Using dummy data")
    st.title("📊 AI Sanitizer Proxy Dashboard (Demo Mode)")
else:
    st.sidebar.info("🔴 Using live observability data")
    st.title("📊 AI Sanitizer Proxy Dashboard (Live Mode)")

auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh", value=True, help=f"Automatically refresh every {REFRESH_SECONDS}s")

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

def get_metrics():
    if USE_DUMMY:
        return dummy_metrics()
    else:
        try:
            import requests
            response = requests.get(f"{PROXY_URL}/metrics?group=agent_id", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "total": data.get("total", 0),
                    "allowed": data.get("allowed", 0),
                    "redacted": data.get("redacted", 0),
                    "blocked": data.get("blocked", 0),
                    "p50_latency_ms": 25.5,  # Placeholder
                    "p95_latency_ms": 89.2,  # Placeholder
                    "group_by": data.get("group_by", {})
                }
            else:
                st.error(f"Failed to fetch metrics: {response.status_code}")
                return dummy_metrics()
        except Exception as e:
            st.error(f"Error connecting to observability API: {e}")
            return dummy_metrics()

def get_per_agent_df():
    if USE_DUMMY:
        return dummy_per_agent()
    else:
        try:
            import requests
            response = requests.get(f"{PROXY_URL}/metrics?group=agent_id", timeout=10)
            if response.status_code == 200:
                data = response.json()
                group_by_data = data.get("group_by", {})
                
                agent_list = []
                for agent_id, counts in group_by_data.items():
                    if isinstance(counts, dict):
                        agent_list.append({
                            "Agent": agent_id,
                            "Allowed": counts.get("allowed", 0),
                            "Redacted": counts.get("redacted", 0),
                            "Blocked": counts.get("blocked", 0)
                        })
                
                return pd.DataFrame(agent_list) if agent_list else dummy_per_agent()
            else:
                return dummy_per_agent()
        except Exception as e:
            st.warning(f"Could not fetch per-agent data: {e}")
            return dummy_per_agent()

def get_time_series():
    # For now, return dummy data as real-time series requires more complex backend
    return dummy_time_series()

# -------------------
# UI
# -------------------

# Status indicator
if USE_DUMMY:
    st.info(f"📊 Demo mode active — showing simulated data")
else:
    st.success(f"🔴 Live mode — showing real observability data")

# Manual refresh button
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Refresh Now"):
        st.rerun()

# Get data
m = get_metrics()

# Main metrics
st.subheader("📊 Current Status")
cols = st.columns(4)
cols[0].metric("Total Requests", f"{m['total']:,}")
cols[1].metric("✅ Allowed", f"{m['allowed']:,}", delta=f"{(m['allowed']/m['total']*100):.1f}%" if m['total'] > 0 else "0%")
cols[2].metric("✂️ Redacted", f"{m['redacted']:,}", delta=f"{(m['redacted']/m['total']*100):.1f}%" if m['total'] > 0 else "0%")
cols[3].metric("⛔ Blocked", f"{m['blocked']:,}", delta=f"{(m['blocked']/m['total']*100):.1f}%" if m['total'] > 0 else "0%")

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

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"🔄 Auto-refresh: {'ON' if auto_refresh else 'OFF'}")
with col2:
    st.caption(f"🕒 Last updated: {time.strftime('%H:%M:%S')}")
with col3:
    st.caption(f"📡 API: {PROXY_URL}")

# Auto-refresh logic
if auto_refresh:
    time.sleep(REFRESH_SECONDS)
    st.rerun()
