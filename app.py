import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Momentum Radar Pro", layout="wide", page_icon="📡")

# --- 2. CSS FOR PRO UI ---
st.markdown("""
<style>
    /* Buy Card (Green) */
    .buy-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #00ff41;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
        transition: transform 0.2s;
    }
    .buy-card:hover { transform: scale(1.02); border-color: #00ff41; }
    
    /* Sell Card (Red) */
    .sell-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
        transition: transform 0.2s;
    }
    .sell-card:hover { transform: scale(1.02); border-color: #ff4b4b; }

    /* Links & Text */
    .stock-symbol a {
        font-size: 22px;
        font-weight: bold;
        color: #ffffff !important;
        text-decoration: none;
    }
    .stock-symbol a:hover { text-decoration: underline; }
    
    .stock-price { font-size: 26px; font-weight: bold; color: #ffffff; }
    .buy-text { color: #00ff41; }
    .sell-text { color: #ff4b4b; }
    
    .vol-badge {
        background-color: #262730;
        color: #ffcc00;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid #ffcc00;
    }
    .stock-info { font-size: 14px; color: #cccccc; margin-top: 8px; }
    
    /* Button */
    .stButton>button {
        width: 100%;
        background-color: #262730;
        color: white;
        border: 1px solid #4c4c4c;
    }
    .stButton>button:hover { border-color: #00ff41; color: #00ff41; }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR SETTINGS ---
st.sidebar.title("📡 Settings")

# Auto Refresh
use_autorefresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh")
if use_autorefresh:
    refresh_rate = st.sidebar.slider("Refresh Interval (s)", 60, 300, 60)
    count = st_autorefresh(interval=refresh_rate * 1000, key="market_scanner")

st.sidebar.markdown("---")
st.sidebar.subheader("⏳ Timeframe")
tf_selection = st.sidebar.selectbox("Select Chart Time:", ("5 Minutes", "15 Minutes", "30 Minutes", "1 Hour"))

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Signal Type")
trend_mode = st.sidebar.radio("Find Stocks for:", ("Bullish (Buy)", "Bearish (Sell)"))

st.sidebar.markdown("---")
st.sidebar.info("Tip: Click stock name for Chart.")

# Timeframe Logic
timeframe_map = {"5 Minutes": "5m", "15 Minutes": "15m", "30 Minutes": "30m", "1 Hour": "1h"}
tf_code = timeframe_map[tf_selection]
period_map = "5d" if tf_code in ["5m", "15m", "30m"] else "1mo"

# --- 4. STOCK LISTS ---
nifty50 = [
    'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS',
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BPCL.NS', 'BHARTIARTL.NS',
    'BRITANNIA.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DIVISLAB.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS',
    'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS',
    'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS',
    'LTIM.NS', 'M&M.NS', 'MARUTI.NS', 'NESTLEIND.NS', 'NTPC.NS',
    'ONGC.NS', 'POWERGRID.NS', 'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS',
    'SUNPHARMA.NS', 'TCS.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS',
    'TECHM.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'UPL.NS', 'WIPRO.NS'
]
banknifty = ['BANKBARODA.NS', 'PNB.NS', 'AUBANK.NS', 'IDFCFIRSTB.NS', 'FEDERALBNK.NS', 'BANDHANBNK.NS']
midcap = ['POLYCAB.NS', 'TATACOMM.NS', 'PERSISTENT.NS', 'COFORGE.NS', 'LTTS.NS', 'MPHASIS.NS', 'ASHOKLEY.NS', 'ASTRAL.NS', 'JUBLFOOD.NS', 'VOLTAS.NS', 'TRENT.NS', 'BEL.NS', 'HAL.NS', 'DLF.NS', 'GODREJPROP.NS', 'INDHOTEL.NS', 'TATACHEM.NS', 'TATAPOWER.NS', 'JINDALSTEL.NS', 'SAIL.NS', 'NMDC.NS', 'ZEEL.NS', 'CANBK.NS', 'REC.NS', 'PFC.NS', 'IRCTC.NS', 'BOSCHLTD.NS', 'CUMMINSIND.NS', 'OBEROIRLTY.NS', 'ESCORTS.NS', 'SRF.NS', 'PIIND.NS', 'CONCOR.NS', 'AUROPHARMA.NS', 'LUPIN.NS']
all_tickers = list(set(nifty50 + banknifty + midcap))

# --- 5. SCANNING FUNCTION (LIGHTWEIGHT) ---
@st.cache_data(ttl=60, show_spinner=False)
def scan_market(tickers, timeframe_code, period_duration, mode):
    found_stocks = []
    
    for symbol in tickers:
        try:
            df = yf.download(symbol, period=period_duration, interval=timeframe_code, progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            if df.empty: continue

            # --- MANUAL CALCULATIONS (Replacing Pandas_TA) ---
            
            # 1. VWAP Calculation
            # Formula: Cumulative(Price * Volume) / Cumulative(Volume)
            df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['Cum_Vol_Price'] = (df['TP'] * df['Volume']).cumsum()
            df['Cum_Vol'] = df['Volume'].cumsum()
            df['VWAP'] = df['Cum_Vol_Price'] / df['Cum_Vol']
            
            # 2. Stochastic Calculation (14, 3, 3)
            # Formula: %K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
            low_min = df['Low'].rolling(window=14).min()
            high_max = df['High'].rolling(window=14).max()
            df['%K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
            df['Stoch'] = df['%K'].rolling(window=3).mean() # Smoothing (Default=3)

            # 3. Average Volume
            df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()

            # --- LOGIC ---
            last = df.iloc[-1]
            close = last['Close']
            vol = last['Volume']
            vol_avg = last['Vol_Avg']
            vwap_val = last['VWAP']
            stoch_val = last['Stoch']

            # Check if Data is Valid (NaN check)
            if pd.isna(vwap_val) or pd.isna(stoch_val): continue

            cond_vol = vol > vol_avg
            cond_stoch = 20 < stoch_val < 80
            
            is_match = False
            if mode == "Bullish (Buy)":
                if close > vwap_val and cond_vol and cond_stoch: is_match = True
            else:
                if close < vwap_val and cond_vol and cond_stoch: is_match = True

            if is_match:
                vol_multiplier = round(vol / vol_avg, 2)
                found_stocks.append({
                    'Symbol': symbol,
                    'Price': round(close, 2),
                    'Stoch': round(stoch_val, 2),
                    'VWAP': round(vwap_val, 2),
                    'Vol_Ratio': vol_multiplier
                })
        except Exception:
            pass
    
    found_stocks.sort(key=lambda x: x['Vol_Ratio'], reverse=True)
    return found_stocks

# --- 6. MAIN UI ---
st.title("📡 Momentum Radar Pro")
st.write(f"Scanning **{trend_mode}** opportunities on **{tf_selection}**.")

if st.button('🚀 START SCAN') or use_autorefresh:
    with st.spinner('Analyzing Market Data...'):
        results = scan_market(all_tickers, tf_code, period_map, trend_mode)
    
    if results:
        st.success(f"Found {len(results)} Stocks matching criteria!")
        cols = st.columns(3)
        
        for i, stock in enumerate(results):
            with cols[i % 3]:
                clean_symbol = stock['Symbol'].replace('.NS', '')
                tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{clean_symbol}"
                
                card_class = "buy-card" if trend_mode == "Bullish (Buy)" else "sell-card"
                text_class = "buy-text" if trend_mode == "Bullish (Buy)" else "sell-text"

                st.markdown(f"""
                <div class="{card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="stock-symbol">
                            <a href="{tv_link}" target="_blank">{stock['Symbol']} 🔗</a>
                        </div>
                        <div class="vol-badge">⚡ {stock['Vol_Ratio']}x Vol</div>
                    </div>
                    <div class="stock-price {text_class}">₹{stock['Price']}</div>
                    <div class="stock-info">
                        📊 Stoch: {stock['Stoch']}<br>
                        🌊 VWAP: {stock['VWAP']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No stocks found right now.")
