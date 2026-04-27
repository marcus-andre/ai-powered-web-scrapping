import streamlit as st
import requests
import os
import pandas as pd

# API configurations connecting to the FastAPI container
API_URL = os.getenv("API_URL", "http://app:8000")
API_KEY = os.getenv("API_KEY", "super-secret-key-123")
HEADERS = {"X-API-Key": API_KEY}

st.set_page_config(page_title="Data Collector Dashboard", page_icon="🕷️", layout="wide")

st.title("🕷️ Web Collector Dashboard")
st.markdown("Welcome to the data extraction control panel.")

col1, col2 = st.columns(2)

with col1:
    st.header("⚡ Manual Execution")
    st.info("Click the button below to force a site scan right now.")
    if st.button("🚀 Run Collection Now", use_container_width=True):
        with st.spinner("Sending command to the server..."):
            resp = requests.post(f"{API_URL}/trigger-pipeline/", headers=HEADERS)
            if resp.status_code == 200:
                st.success("Command sent successfully! The bot is running in the background.")
            else:
                st.error(f"Error starting: {resp.status_code}")

with col2:
    st.header("⏱️ Automatic Scheduler")
    st.info("Configure the bot to run automatically on a schedule.")
    interval = st.number_input("Scan interval (in minutes):", min_value=1, value=60, step=1)
    
    if st.button("⏳ Save Schedule", use_container_width=True):
        with st.spinner("Configuring scheduler..."):
            resp = requests.post(f"{API_URL}/schedule-pipeline/?interval_minutes={interval}", headers=HEADERS)
            if resp.status_code == 200:
                st.success(f"All set! The bot will scan the site every {interval} minutes.")
            else:
                st.error("Error configuring scheduler.")

st.divider()

st.header("📊 Collected Data (Gold Layer)")
if st.button("🔄 Refresh Table"):
    resp = requests.get(f"{API_URL}/products/?limit=10", headers=HEADERS)
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        st.dataframe(df, use_container_width=True)