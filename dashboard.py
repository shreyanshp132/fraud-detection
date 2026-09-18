import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

# 1. Load Environment Config
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

st.set_page_config(page_title="Fraud Review Dashboard", layout="wide")
st.title("🛡️ Live Fraud Decision Queue")

# 2. Database Connection & Query (Cached for 5 seconds to prevent spamming DB)
@st.cache_data(ttl=5)
def load_data():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        # Pull the latest transactions logged by app.py
        query = "SELECT transaction_id, risk_score, decision FROM predictions;"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Failed to connect to Database: {e}")
        return pd.DataFrame()

df = load_data()

# 3. Dashboard UI Construction
if not df.empty:
    # Calculate live pipeline metrics
    total_tx = len(df)
    blocked_tx = len(df[df['decision'] == 'Block'])
    flagged_tx = len(df[df['decision'] == 'Flag'])
    
    # Render KPI Cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions", total_tx)
    col2.metric("Manual Review (Flagged)", flagged_tx)
    col3.metric("Auto-Blocked", blocked_tx)

    st.divider()

    # Filter for high-risk items (Flags and Blocks)
    st.subheader("⚠️ High-Risk Transaction Queue")
    high_risk_df = df[df['decision'].isin(['Flag', 'Block'])].copy()
    
    # Sort so highest risk scores are at the top
    if not high_risk_df.empty:
        high_risk_df = high_risk_df.sort_values(by='risk_score', ascending=False)
        st.dataframe(high_risk_df, use_container_width=True)
    else:
        st.success("No high-risk transactions detected recently.")

    st.divider()
    
    # Full Audit Log
    with st.expander("View Full Transaction Audit Log"):
        st.dataframe(df.sort_values(by='risk_score', ascending=False), use_container_width=True)

else:
    st.info("No data found in the predictions table. Ensure app.py and your data generator are running.")

# Manual refresh trigger
if st.button("🔄 Refresh Live Feed"):
    st.rerun()