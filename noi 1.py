import streamlit as st
import pandas as pd
from nsepython import *
import time
import os

# --- SETUP ---
st.set_page_config(page_title="Nifty Live AI Scanner", layout="wide")
CSV_FILE = "nifty_trading_data.csv"

def get_nifty_data():
    try:
        oi_data = nse_optionchain_scrapper('NIFTY')
        spot = oi_data['records']['underlyingValue']
        # Filter ATM +/- 100 points
        atm_data = [i for i in oi_data['filtered']['data'] if abs(i['strikePrice'] - spot) <= 100]
        
        ce_oi_chg = sum(i['CE']['changeinOpenInterest'] for i in atm_data)
        pe_oi_chg = sum(i['PE']['changeinOpenInterest'] for i in atm_data)
        ce_vol = sum(i['CE']['totalTradedVolume'] for i in atm_data)
        pe_vol = sum(i['PE']['totalTradedVolume'] for i in atm_data)

        signal = "NEUTRAL"
        if pe_oi_chg > ce_oi_chg * 1.5 and pe_vol > ce_vol: signal = "BUY CALL"
        elif ce_oi_chg > pe_oi_chg * 1.5 and ce_vol > pe_vol: signal = "BUY PUT"

        return {"Time": time.strftime("%H:%M:%S"), "Spot": spot, "Signal": signal, 
                "CE_OI": ce_oi_chg, "PE_OI": pe_oi_chg, "CE_Vol": ce_vol, "PE_Vol": pe_vol}
    except: return None

# --- AUTO-REFRESHING FRAGMENT ---
# run_every="3m" tells Streamlit to rerun this specific function every 3 minutes
@st.fragment(run_every="3m")
def live_scanner_fragment():
    data = get_nifty_data()
    if data:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Nifty Spot", data['Spot'])
        with col2:
            if "CALL" in data['Signal']: st.success(f"{data['Signal']} 🚀")
            elif "PUT" in data['Signal']: st.error(f"{data['Signal']} 📉")
            else: st.info("NEUTRAL - Waiting for Setup")
        
        # Log to CSV automatically
        pd.DataFrame([data]).to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
        
        # Visual Chart of Trend
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            st.subheader("OI Trend (Call vs Put)")
            st.bar_chart(df.set_index('Time')[['CE_OI', 'PE_OI']])

st.title("📊 Nifty 50 Auto-Scanner (3-Min Refresh)")
st.info("The scanner below updates automatically. No need to click refresh!")

# Call the fragment function
live_scanner_fragment()

# --- MANUAL DOWNLOAD SECTION ---
if os.path.exists(CSV_FILE):
    st.markdown("---")
    df_history = pd.read_csv(CSV_FILE)
    csv_bytes = df_history.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Download Full Backtest CSV", data=csv_bytes, file_name='nifty_backtest.csv', mime='text/csv')