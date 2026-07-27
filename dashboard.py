import os
import pandas as pd
import requests
import streamlit as st

# API configurations connecting to the FastAPI container
# Fallback to 127.0.0.1 for local/codespaces execution when environment variable is unset
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "my_dev_secret_key_123")
HEADERS = {"X-API-Key": API_KEY}

# Demo mode configuration
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

st.set_page_config(
    page_title="AI Powered Data Collector Dashboard", page_icon="🕷️", layout="wide"
)

st.title("🕷️ Web Collector Dashboard")
st.markdown("Welcome to the data extraction control panel.")

if DEMO_MODE:
    st.warning(
        "🔒 **Demo Mode is Active:** Triggering data collection pipelines is disabled in this public demonstration. You can still view the collected data below."
    )

col1, col2 = st.columns(2)

# Manual Execution Section
with col1:
    st.header("⚡ Manual Execution")
    st.info("Click the button below to force a site scan right now.")

    if st.button("🚀 Run Collection Now", use_container_width=True, disabled=DEMO_MODE):
        with st.spinner("Sending command to the server..."):
            try:
                resp = requests.post(
                    f"{API_URL}/trigger-pipeline/", headers=HEADERS, timeout=10
                )
                if resp.status_code == 200:
                    st.success(
                        "Command sent successfully! The bot is running in the background."
                    )
                else:
                    st.error(
                        f"Error starting pipeline: HTTP {resp.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to the backend API at {API_URL}.")

# Automatic Scheduler Section
with col2:
    st.header("⏱️ Automatic Scheduler")
    st.info("Configure the bot to run automatically on a schedule.")
    interval = st.number_input(
        "Scan interval (in minutes):", min_value=1, value=60, step=1
    )

    if st.button("⏳ Save Schedule", use_container_width=True, disabled=DEMO_MODE):
        with st.spinner("Configuring scheduler..."):
            try:
                resp = requests.post(
                    f"{API_URL}/schedule-pipeline/?interval_minutes={interval}",
                    headers=HEADERS,
                    timeout=10,
                )
                if resp.status_code == 200:
                    st.success(
                        f"All set! The bot will scan the site every {interval} minutes."
                    )
                else:
                    st.error(
                        f"Error configuring scheduler: HTTP {resp.status_code}")
            except requests.exceptions.RequestException:
                st.error(f"Failed to connect to the backend API at {API_URL}.")

st.divider()

# Collected Data Display Section
st.header("📊 Collected Data (Gold Layer)")


def load_data():
    """Fetch stored product data from the FastAPI backend."""
    try:
        resp = requests.get(f"{API_URL}/products/?limit=50",
                            headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return pd.DataFrame(data)
            else:
                st.info("No data found in the Gold Layer yet.")
                return None
        else:
            st.error(f"Failed to load data: HTTP {resp.status_code}")
            return None
    except requests.exceptions.RequestException:
        st.warning(f"Could not connect to {API_URL} to fetch dataset.")
        return None


if st.button("🔄 Refresh Table"):
    df = load_data()
    if df is not None:
        # Sanitize string columns to handle encoding anomalies
        df = df.apply(
            lambda col: col.map(
                lambda x: x.encode("utf-8", "ignore").decode("utf-8")
                if isinstance(x, str)
                else x
            )
        )

        # Filter and order columns according to dashboard UI specifications
        desired_columns = [
            "title",
            "price",
            "rating",
            "url",
            "description",
            "ai_summary",
            "ai_sentiment",
            "ai_entities",
        ]
        df_display = df[[col for col in desired_columns if col in df.columns]]

        # Render data grid with explicit column configurations
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "title": st.column_config.TextColumn(
                    "Title",
                    help="Product Title",
                    width="medium",
                    required=True,
                ),
                "price": st.column_config.NumberColumn(
                    "Price",
                    format="£%.2f",
                    width="small",
                ),
                "rating": st.column_config.NumberColumn(
                    "Rating",
                    format="%d ⭐",
                    width="small",
                ),
                "url": st.column_config.LinkColumn(
                    "Product URL",
                    display_text="Open Link 🔗",
                    width="small",
                ),
                "description": st.column_config.TextColumn(
                    "Description",
                    width="large",
                ),
                "ai_summary": st.column_config.TextColumn(
                    "AI Summary",
                    width="large",
                ),
                "ai_sentiment": st.column_config.TextColumn(
                    "Sentiment",
                    width="small",
                ),
                "ai_entities": st.column_config.ListColumn(
                    "Entities Identified",
                    width="medium",
                ),
            },
        )
else:
    # Initial load when the page is first rendered
    df = load_data()
    if df is not None:
        st.dataframe(df, use_container_width=True)
