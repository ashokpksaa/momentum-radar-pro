import streamlit as st
import pandas as pd
import upstox_client
from upstox_client.rest import ApiException
from streamlit_autorefresh import st_autorefresh
import datetime
import requests
import gzip
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Momentum Radar Pro (Live)", layout="wide", page_icon="📡")

# --- 2. GLOBAL CACHE FOR TOKEN & INSTRUMENTS ---
# Ye class token ko server par zinda rakhegi taaki public ko dikh sake
@st.cache_resource
class GlobalStore:
    def __init__(self):
        self.access_token = None
        self.instrument_df = None

store = GlobalStore()

# --- 3. HELPER FUNCTIONS (Upstox Specific) ---

# Function to get NSE Instruments (Mapping Reliance -> NSE_EQ|INE...)
@st.cache_data(ttl=86400) # Cache for 24 hours
def get_instrument_list():
    url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
    response = requests.get(url)
    with gzip.open(io.BytesIO(response.content), 'rt') as f:
        df = pd.read_csv(f)
    return df

# Initialize Instruments once
if store.instrument_df is None:
    with st.spinner("Initializing Master Stock List..."):
        store.instrument_df = get_instrument_list()

def get_instrument_key(symbol):
    # Symbol se Key dhundhna (Eg: RELIANCE -> NSE_EQ|INE002A01018)
    try:
        # User input me .NS ho sakta hai, use hatana padega
        clean_symbol = symbol.replace('.NS', '').upper() 
        res = store.instrument_df[store.instrument_df['tradingsymbol'] == clean_symbol]
        res = res[res['instrument_type'] == 'EQUITY'] # Sirf Equity chaiye
        if not res.empty:
            return res.iloc[0]['instrument_key']
    except:
        pass
    return None

# --- 4. CSS FOR UI (SAME AS BEFORE) ---
st.markdown("""
<style>
    .buy-card {
        background-color: #1e1e1e; border: 1px solid #333; border-radius: 10px;
        padding: 15px; margin-bottom: 15px; border-left: 5px solid #00ff41;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5); transition: transform 0.2s;
    }
    .buy-card:hover { transform: scale(1.02); border-color: #00ff41; }
    
    .sell-card {
        background-color: #1e1e1e; border: 1px solid #333; border-radius: 10px;
        padding: 15px; margin-bottom: 15px; border-left: 5px solid #ff4b4b;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5); transition: transform 0.2s;
    }
    .sell-card:hover { transform: scale(1.02); border-color: #ff4b4b; }

    .stock-symbol a { font-size: 22px; font-weight: bold; color: #ffffff !important; text-decoration: none; }
    .stock-price { font-size: 26px; font-weight: bold; color: #ffffff; }
    .buy-text { color: #00ff41; } .sell-text { color: #ff4b4b; }
    .vol-badge { background-color: #262730; color: #ffcc00; padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; border: 1px solid #ffcc00; }
    .stock-info { font-size: 14px; color: #cccccc; margin-top: 8px; }
    .stButton>button { width: 100%; background-color: #262730; color: white; border: 1px solid #4c4c4c; }
    .stButton>button:hover { border-color: #00ff41; color: #00ff41; }
</style>
""", unsafe_allow_html=True)

# --- 5. ADMIN PANEL (SIDEBAR) ---
st.sidebar.title("⚙️ Control Panel")

# Secret Admin Section
admin_pass = st.sidebar.text_input("Admin Login", type="password")

if admin_pass == "1234":  # <--- Change Password Here
    st.sidebar.success("Unlocked! 🔓")
    new_token = st.sidebar.text_area("Paste Daily Upstox Token:", value=store.access_token if store.access_token else "")
    if st.sidebar.button("Save Token 💾"):
        store.access_token = new_token
        st.sidebar.success("Token Saved Globally! 🚀")
        st.rerun()
else:
    # Public view me kuch nahi dikhega extra
    pass

# --- 6. SETTINGS ---
use_autorefresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh")
if use_autorefresh:
    refresh_rate = st.sidebar.slider("Refresh (s)", 30, 300, 60)
    st_autorefresh(interval=refresh_rate * 1000, key="market_scanner")

st.sidebar.markdown("---")
tf_selection = st.sidebar.selectbox("Timeframe:", ("1 Minute", "5 Minutes", "15 Minutes", "30 Minutes"))
trend_mode = st.sidebar.radio("Signal Type:", ("Bullish (Buy)", "Bearish (Sell)"))

# Timeframe Mapping for Upstox
# Upstox format: 1minute, 5minute, 15minute, 30minute
upstox_tf_map = {
    "1 Minute": "1minute",
    "5 Minutes": "5minute",
    "15 Minutes": "15minute",
    "30 Minutes": "30minute"
}
interval_str = upstox_tf_map[tf_selection]

# --- 7. STOCK LISTS (SYMBOLS) ---
# Note: Upstox needs clean symbols (WITHOUT .NS)
nifty50 = ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'ITC', 'INDUSINDBK', 'INFY', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIM', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'ULTRACEMCO', 'UPL', 'WIPRO']
banknifty = ['BANKBARODA', 'PNB', 'AUBANK', 'IDFCFIRSTB', 'FEDERALBNK', 'BANDHANBNK']
midcap = ['POLYCAB', 'TATACOMM', 'PERSISTENT', 'COFORGE', 'LTTS', 'MPHASIS', 'ASHOKLEY', 'ASTRAL', 'JUBLFOOD', 'VOLTAS', 'TRENT', 'BEL', 'HAL', 'DLF', 'GODREJPROP', 'INDHOTEL', 'TATACHEM', 'TATAPOWER', 'JINDALSTEL', 'SAIL', 'NMDC', 'ZEEL', 'CANBK', 'REC', 'PFC', 'IRCTC', 'BOSCHLTD', 'CUMMINSIND', 'OBEROIRLTY', 'ESCORTS', 'SRF', 'PIIND', 'CONCOR', 'AUROPHARMA', 'LUPIN']
all_tickers = list(set(nifty50 + banknifty + midcap))

# --- 8. SCANNING FUNCTION (UPSTOX API) ---
def scan_market_upstox(tickers, interval, mode):
    found_stocks = []
    
    if not store.access_token:
        st.error("⚠️ Admin has not set the Upstox Token yet. Data Unavailable.")
        return []

    # Configure Upstox
    config = upstox_client.Configuration()
    config.access_token = store.access_token
    api_instance = upstox_client.HistoryApi(upstox_client.ApiClient(config))
    
    progress_bar = st.progress(0)
    status = st.empty()
    total = len(tickers)

    for i, symbol in enumerate(tickers):
        status.text(f"Scanning {symbol} (Real-Time)...")
        progress_bar.progress((i + 1) / total)

        try:
            # 1. Get Instrument Key
            inst_key = get_instrument_key(symbol)
            if not inst_key: continue

            # 2. Fetch Data (Last 50 candles are enough for indicators)
            # Format dates
            to_date = datetime.datetime.now().strftime("%Y-%m-%d")
            from_date = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")

            api_response = api_instance.get_intra_day_candle_data(
                instrument_key=inst_key,
                interval=interval,
                to_date=to_date,
                from_date=from_date
            )
            
            if not api_response.data or not api_response.data.candles:
                continue

            # 3. Convert to DataFrame
            # Upstox returns: [timestamp, open, high, low, close, volume, oi]
            candles = api_response.data.candles
            columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI']
            df = pd.DataFrame(candles, columns=columns)
            
            # Data reverse aata hai (Latest first), usko seedha karna padega for calculation
            df = df[::-1].reset_index(drop=True)

            # --- MANUAL INDICATORS (No Pandas_TA needed) ---
            
            # VWAP
            df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['Cum_Vol_Price'] = (df['TP'] * df['Volume']).cumsum()
            df['Cum_Vol'] = df['Volume'].cumsum()
            df['VWAP'] = df['Cum_Vol_Price'] / df['Cum_Vol']
            
            # Stochastic (14, 3, 3)
            low_min = df['Low'].rolling(window=14).min()
            high_max = df['High'].rolling(window=14).max()
            df['%K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
            df['Stoch'] = df['%K'].rolling(window=3).mean()
            
            # Average Volume (20)
            df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()

            # --- CHECK LOGIC ---
            last = df.iloc[-1]
            close = last['Close']
            vol = last['Volume']
            vol_avg = last['Vol_Avg']
            vwap_val = last['VWAP']
            stoch_val = last['Stoch']

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

        except Exception as e:
            # Token expire ho gaya ya limit cross ho gayi
            if "401" in str(e):
                st.error("🚨 Token Expired! Please update token in Admin Panel.")
                break
            pass
            
    progress_bar.empty()
    status.empty()
    found_stocks.sort(key=lambda x: x['Vol_Ratio'], reverse=True)
    return found_stocks

# --- 9. MAIN UI DISPLAY ---
st.title("📡 Momentum Radar Pro (Live ⚡)")
st.write(f"Scanning **{trend_mode}** | Data Source: **Upstox API (Real-Time)**")

if st.button('🚀 START LIVE SCAN') or use_autorefresh:
    if not store.access_token:
        st.warning("⚠️ System Offline. Waiting for Admin to set Data Token.")
    else:
        with st.spinner('Fetching Live Data from NSE...'):
            results = scan_market_upstox(all_tickers, interval_str, trend_mode)
        
        if results:
            st.success(f"Found {len(results)} Stocks!")
            cols = st.columns(3)
            for i, stock in enumerate(results):
                with cols[i % 3]:
                    # Link logic
                    tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{stock['Symbol']}"
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
            st.info("Market is sideways. No high-momentum stocks found.")
