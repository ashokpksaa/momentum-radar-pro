import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import datetime
import requests
import gzip
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Momentum Radar Pro (Live)", layout="wide", page_icon="📡")

# --- 2. GLOBAL CACHE ---
@st.cache_resource
class GlobalStore:
    def __init__(self):
        self.access_token = None
        self.instrument_df = None

store = GlobalStore()

# --- 3. HELPER FUNCTIONS ---
@st.cache_data(ttl=86400)
def get_instrument_list():
    try:
        url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
        response = requests.get(url)
        with gzip.open(io.BytesIO(response.content), 'rt') as f:
            df = pd.read_csv(f)
        return df
    except Exception as e:
        return None

if store.instrument_df is None:
    with st.spinner("Initializing Master Stock List (90+ Stocks)..."):
        store.instrument_df = get_instrument_list()

def get_instrument_key(symbol):
    try:
        if store.instrument_df is None: return None
        # Symbol cleaning
        clean_symbol = symbol.replace('.NS', '').upper()
        
        # Upstox me kuch naam alag ho sakte hain (Jaise M&M)
        # Hum direct match try karenge
        res = store.instrument_df[store.instrument_df['tradingsymbol'] == clean_symbol]
        res = res[res['instrument_type'] == 'EQUITY']
        
        if not res.empty:
            return res.iloc[0]['instrument_key']
    except:
        pass
    return None

# --- 4. CSS ---
st.markdown("""
<style>
    .buy-card { background-color: #1e1e1e; border: 1px solid #333; border-radius: 10px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #00ff41; }
    .sell-card { background-color: #1e1e1e; border: 1px solid #333; border-radius: 10px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #ff4b4b; }
    .stock-symbol a { font-size: 22px; font-weight: bold; color: #ffffff !important; text-decoration: none; }
    .stock-price { font-size: 26px; font-weight: bold; color: #ffffff; }
    .buy-text { color: #00ff41; } .sell-text { color: #ff4b4b; }
    .vol-badge { background-color: #262730; color: #ffcc00; padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: bold; border: 1px solid #ffcc00; }
    .stock-info { font-size: 14px; color: #cccccc; margin-top: 8px; }
    .stButton>button { width: 100%; background-color: #262730; color: white; border: 1px solid #4c4c4c; }
    .stButton>button:hover { border-color: #00ff41; color: #00ff41; }
</style>
""", unsafe_allow_html=True)

# --- 5. ADMIN PANEL ---
st.sidebar.title("⚙️ Control Panel")
admin_pass = st.sidebar.text_input("Admin Login", type="password")

if admin_pass == "1234":
    st.sidebar.success("Unlocked! 🔓")
    new_token = st.sidebar.text_area("Upstox Token:", value=store.access_token if store.access_token else "")
    if st.sidebar.button("Save Token 💾"):
        store.access_token = new_token
        st.sidebar.success("Saved!")
        st.rerun()

    # --- DEBUGGING BUTTON ---
    st.sidebar.markdown("---")
    if st.sidebar.button("🛠️ Test API (Historical)"):
        if not store.access_token:
            st.sidebar.error("No Token Found!")
        else:
            try:
                st.sidebar.info("Testing connection with SBIN on 30min...")
                key = get_instrument_key("SBIN")
                if key:
                    # Direct API Call to Historical Endpoint
                    to_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    from_date = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
                    url = f"https://api.upstox.com/v2/historical-candle/{key}/30minute/{to_date}/{from_date}"
                    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {store.access_token}'}
                    response = requests.get(url, headers=headers)
                    data = response.json()
                    
                    if 'data' in data and 'candles' in data['data'] and data['data']['candles']:
                        st.sidebar.success(f"Success! Got {len(data['data']['candles'])} candles.")
                        st.sidebar.write(data['data']['candles'][0])
                    else:
                        st.sidebar.warning(f"No Data received: {data}")
            except Exception as e:
                st.sidebar.error(f"Error: {str(e)}")
else:
    pass

# --- 6. SETTINGS ---
use_autorefresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh")
if use_autorefresh:
    refresh_rate = st.sidebar.slider("Refresh (s)", 30, 300, 60)
    st_autorefresh(interval=refresh_rate * 1000, key="market_scanner")

st.sidebar.markdown("---")
tf_selection = st.sidebar.selectbox("Timeframe:", ("1 Minute", "5 Minutes", "15 Minutes", "30 Minutes", "1 Hour"))
trend_mode = st.sidebar.radio("Signal Type:", ("Bullish (Buy)", "Bearish (Sell)"))

# Map UI selection to Upstox API interval strings
upstox_tf_map = {
    "1 Minute": "1minute",
    "5 Minutes": "5minute",
    "15 Minutes": "15minute",
    "30 Minutes": "30minute",
    "1 Hour": "60minute" # Upstox uses 60minute, not 1hour
}
interval_str = upstox_tf_map[tf_selection]

# --- 7. COMPLETE STOCK LIST (91 STOCKS) ---
nifty50 = [
    'ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 
    'BAJAJFINSV', 'BPCL', 'BHARTIARTL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 
    'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 
    'ICICIBANK', 'ITC', 'INDUSINDBK', 'INFY', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIM', 'M&M', 
    'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SUNPHARMA', 
    'TCS', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'ULTRACEMCO', 'UPL', 'WIPRO'
]

banknifty = [
    'BANKBARODA', 'PNB', 'AUBANK', 'IDFCFIRSTB', 'FEDERALBNK', 'BANDHANBNK', 'INDUSINDBK', 
    'AU SMALL FINANCE BANK', 'KOTAK MAHINDRA BANK'
]

midcap = [
    'POLYCAB', 'TATACOMM', 'PERSISTENT', 'COFORGE', 'LTTS', 'MPHASIS', 'ASHOKLEY', 'ASTRAL', 
    'JUBLFOOD', 'VOLTAS', 'TRENT', 'BEL', 'HAL', 'DLF', 'GODREJPROP', 'INDHOTEL', 'TATACHEM', 
    'TATAPOWER', 'JINDALSTEL', 'SAIL', 'NMDC', 'ZEEL', 'CANBK', 'REC', 'PFC', 'IRCTC', 
    'BOSCHLTD', 'CUMMINSIND', 'OBEROIRLTY', 'ESCORTS', 'SRF', 'PIIND', 'CONCOR', 'AUROPHARMA', 'LUPIN',
    'ABCAPITAL', 'BALKRISIND', 'BHEL', 'GMRINFRA', 'IDEA', 'IGL', 'INDIGO', 'L&TFH', 
    'LICHSGFIN', 'M&MFIN', 'MANAPPURAM', 'MFSL', 'MOTHERSON', 'NATIONALUM', 'NAUKRI', 
    'PETRONET', 'RAMCOCEM', 'RBLBANK', 'RECLTD', 'SBICARD', 'SIEMENS', 'TVSMOTOR', 'UBL'
]

# Combine and remove duplicates
all_tickers = list(set(nifty50 + banknifty + midcap))

# --- 8. SCANNER FUNCTION (Direct API Call) ---
def scan_market_upstox(tickers, interval, mode):
    found_stocks = []
    
    if not store.access_token:
        st.error("⚠️ System Offline. Admin needs to set Token.")
        return []

    progress_bar = st.progress(0)
    status = st.empty()
    total = len(tickers)

    # Dates for Historical Data (Last 20 days to ensure enough data for 30m/1h indicators)
    to_date = datetime.datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.datetime.now() - datetime.timedelta(days=20)).strftime("%Y-%m-%d")
    
    # Headers for Request
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {store.access_token}'
    }

    for i, symbol in enumerate(tickers):
        status.text(f"Scanning {symbol}...")
        progress_bar.progress((i + 1) / total)

        try:
            # 1. Get Key
            inst_key = get_instrument_key(symbol)
            if not inst_key: continue

            # 2. Direct API Call (Historical Data Endpoint)
            # Documentation: https://upstox.com/developer/api-documentation/historical-candle-data
            url = f"https://api.upstox.com/v2/historical-candle/{inst_key}/{interval}/{to_date}/{from_date}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                continue
                
            data = response.json()
            
            if 'data' not in data or 'candles' not in data['data'] or not data['data']['candles']:
                continue

            # 3. Process Data
            candles = data['data']['candles']
            columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI']
            df = pd.DataFrame(candles, columns=columns)
            
            # Historical API returns: [Oldest, ..., Latest] (Already sorted usually, but let's check)
            # Actually Upstox Historical often returns [Latest, ..., Oldest] in some versions?
            # Let's ensure it is sorted chronologically for rolling calculations: Oldest -> Latest
            
            # Check timestamps to be sure
            t1 = pd.to_datetime(df['Timestamp'].iloc[0])
            t2 = pd.to_datetime(df['Timestamp'].iloc[-1])
            
            if t1 > t2: # If first row is newer than last row (Reverse order)
                df = df[::-1].reset_index(drop=True)

            # Manual Indicators
            df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['Cum_Vol_Price'] = (df['TP'] * df['Volume']).cumsum()
            df['Cum_Vol'] = df['Volume'].cumsum()
            df['VWAP'] = df['Cum_Vol_Price'] / df['Cum_Vol']
            
            low_min = df['Low'].rolling(window=14).min()
            high_max = df['High'].rolling(window=14).max()
            df['%K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
            df['Stoch'] = df['%K'].rolling(window=3).mean()
            df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()

            # Latest Candle
            last = df.iloc[-1]
            
            if pd.isna(last['VWAP']) or pd.isna(last['Stoch']): continue

            # Logic
            cond_vol = last['Volume'] > last['Vol_Avg']
            cond_stoch = 20 < last['Stoch'] < 80
            
            is_match = False
            if mode == "Bullish (Buy)":
                if last['Close'] > last['VWAP'] and cond_vol and cond_stoch: is_match = True
            else:
                if last['Close'] < last['VWAP'] and cond_vol and cond_stoch: is_match = True

            if is_match:
                vol_multiplier = round(last['Volume'] / last['Vol_Avg'], 2)
                found_stocks.append({
                    'Symbol': symbol,
                    'Price': round(last['Close'], 2),
                    'Stoch': round(last['Stoch'], 2),
                    'VWAP': round(last['VWAP'], 2),
                    'Vol_Ratio': vol_multiplier
                })

        except Exception:
            pass
            
    progress_bar.empty()
    status.empty()
    found_stocks.sort(key=lambda x: x['Vol_Ratio'], reverse=True)
    return found_stocks

# --- 9. UI ---
st.title("📡 Momentum Radar Pro (Live ⚡)")
st.write(f"Scanning **{trend_mode}** on **{tf_selection}** | Source: **Upstox API**")

if st.button('🚀 START LIVE SCAN') or use_autorefresh:
    if not store.access_token:
        st.warning("⚠️ Waiting for Admin Token...")
    else:
        with st.spinner('Fetching Historical Data & Scanning...'):
            results = scan_market_upstox(all_tickers, interval_str, trend_mode)
        
        if results:
            st.success(f"Found {len(results)} Stocks!")
            cols = st.columns(3)
            for i, stock in enumerate(results):
                with cols[i % 3]:
                    tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{stock['Symbol']}"
                    card_class = "buy-card" if trend_mode == "Bullish (Buy)" else "sell-card"
                    text_class = "buy-text" if trend_mode == "Bullish (Buy)" else "sell-text"
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div class="stock-symbol"><a href="{tv_link}" target="_blank">{stock['Symbol']} 🔗</a></div>
                            <div class="vol-badge">⚡ {stock['Vol_Ratio']}x Vol</div>
                        </div>
                        <div class="stock-price {text_class}">₹{stock['Price']}</div>
                        <div class="stock-info">📊 Stoch: {stock['Stoch']}<br>🌊 VWAP: {stock['VWAP']}</div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.info(f"Market is sideways on {tf_selection}. No stocks matching VWAP + Vol + Stoch criteria.")
