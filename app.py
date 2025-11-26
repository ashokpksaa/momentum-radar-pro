import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import datetime
import requests
import gzip
import io
import pytz

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Momentum Radar (Debug Mode)", layout="wide", page_icon="🛠️")

# --- 2. GLOBAL STORAGE ---
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
    except:
        return None

if store.instrument_df is None:
    with st.spinner("Loading Stock List..."):
        store.instrument_df = get_instrument_list()

def get_instrument_key(symbol):
    try:
        if store.instrument_df is None: return None
        clean_symbol = symbol.replace('.NS', '').upper()
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
    .stock-price { font-size: 24px; font-weight: bold; color: #fff; }
    .time-badge { font-size: 12px; color: #aaa; background: #333; padding: 2px 5px; border-radius: 4px; }
    .stButton>button { width: 100%; background-color: #333; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
st.sidebar.title("🛠️ Admin Panel")
admin_pass = st.sidebar.text_input("Admin Password", type="password")

if admin_pass == "1234":
    st.sidebar.success("Login Success")
    new_token = st.sidebar.text_area("Upstox Token:", value=store.access_token if store.access_token else "")
    if st.sidebar.button("Save Token"):
        store.access_token = new_token
        st.sidebar.success("Token Updated!")
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.write("🔍 **Debug Tools**")
    test_stock = st.sidebar.text_input("Test Stock (e.g. SBIN)", value="SBIN")
    
    # --- DATA INSPECTOR BUTTON ---
    # Isse aap check kar sakte hain ki API kya bhej rahi hai
    if st.sidebar.button("Show Raw Data"):
        if store.access_token and test_stock:
            key = get_instrument_key(test_stock)
            if key:
                to_date = datetime.datetime.now().strftime("%Y-%m-%d")
                from_date = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
                url = f"https://api.upstox.com/v2/historical-candle/{key}/5minute/{to_date}/{from_date}"
                headers = {'Accept': 'application/json', 'Authorization': f'Bearer {store.access_token}'}
                res = requests.get(url, headers=headers)
                data = res.json()
                
                if 'data' in data and 'candles' in data['data']:
                    candles = data['data']['candles']
                    df = pd.DataFrame(candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
                    
                    st.sidebar.write("Raw Data (First 5 rows - as received):")
                    st.sidebar.write(df.head())
                    
                    # Sort Test
                    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                    df = df.sort_values('Timestamp')
                    st.sidebar.write("Sorted Data (Last 5 rows - Correct Order):")
                    st.sidebar.write(df.tail())
                    
                    last = df.iloc[-1]
                    st.sidebar.warning(f"Software thinks Current Price is: {last['Close']} at Time: {last['Timestamp']}")
                else:
                    st.sidebar.error("No Data")

# --- 6. MAIN SETTINGS ---
use_autorefresh = st.sidebar.checkbox("Auto-Refresh")
if use_autorefresh:
    st_autorefresh(interval=60000)

tf_selection = st.sidebar.selectbox("Timeframe:", ("1 Minute", "5 Minutes", "15 Minutes", "30 Minutes"))
trend_mode = st.sidebar.radio("Mode:", ("Bullish (Buy)", "Bearish (Sell)"))
upstox_tf_map = {"1 Minute": "1minute", "5 Minutes": "5minute", "15 Minutes": "15minute", "30 Minutes": "30minute"}
interval_str = upstox_tf_map[tf_selection]

# --- 7. STOCKS ---
all_tickers = ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'ITC', 'INDUSINDBK', 'INFY', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIM', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'ULTRACEMCO', 'UPL', 'WIPRO', 'BANKBARODA', 'PNB', 'AUBANK', 'IDFCFIRSTB', 'FEDERALBNK', 'BANDHANBNK', 'POLYCAB', 'TATACOMM', 'PERSISTENT', 'COFORGE', 'LTTS', 'MPHASIS', 'ASHOKLEY', 'ASTRAL', 'JUBLFOOD', 'VOLTAS', 'TRENT', 'BEL', 'HAL', 'DLF', 'GODREJPROP', 'INDHOTEL', 'TATACHEM', 'TATAPOWER', 'JINDALSTEL', 'SAIL', 'NMDC', 'ZEEL', 'CANBK', 'REC', 'PFC', 'IRCTC', 'BOSCHLTD', 'CUMMINSIND', 'OBEROIRLTY', 'ESCORTS', 'SRF', 'PIIND', 'CONCOR', 'AUROPHARMA', 'LUPIN']

# --- 8. SCANNER (NO CACHE - FRESH DATA) ---
def scan_market(tickers, interval, mode):
    found_stocks = []
    if not store.access_token:
        st.error("Please set Token in Admin Panel")
        return []

    progress = st.progress(0)
    status = st.empty()
    
    # Dates
    to_date = datetime.datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.datetime.now() - datetime.timedelta(days=20)).strftime("%Y-%m-%d")
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {store.access_token}'}

    for i, symbol in enumerate(tickers):
        status.text(f"Scanning {symbol}...")
        progress.progress((i+1)/len(tickers))
        
        try:
            key = get_instrument_key(symbol)
            if not key: continue

            # API Call
            url = f"https://api.upstox.com/v2/historical-candle/{key}/{interval}/{to_date}/{from_date}"
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if 'data' not in data or 'candles' not in data['data']: continue
            
            candles = data['data']['candles']
            df = pd.DataFrame(candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
            
            # --- CRITICAL FIX: SORTING & TIMEZONE ---
            # 1. Parse Date correctly
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            
            # 2. Sort Ascending (Oldest -> Newest)
            df = df.sort_values('Timestamp').reset_index(drop=True)
            
            # 3. Convert Timezone to IST (Indian Time)
            ist = pytz.timezone('Asia/Kolkata')
            df['Timestamp'] = df['Timestamp'].dt.tz_convert(ist)

            # --- INDICATORS ---
            # Intraday VWAP Logic
            df['Date'] = df['Timestamp'].dt.date
            df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['Vol_Price'] = df['TP'] * df['Volume']
            df['Cum_Vol_Price'] = df.groupby('Date')['Vol_Price'].cumsum()
            df['Cum_Vol'] = df.groupby('Date')['Volume'].cumsum()
            df['VWAP'] = df['Cum_Vol_Price'] / df['Cum_Vol']
            
            # Stochastic
            low_14 = df['Low'].rolling(14).min()
            high_14 = df['High'].rolling(14).max()
            df['%K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
            df['Stoch'] = df['%K'].rolling(3).mean()
            df['Vol_Avg'] = df['Volume'].rolling(20).mean()

            # --- CHECK LAST CANDLE ---
            last = df.iloc[-1]
            
            # Null Check
            if pd.isna(last['VWAP']) or pd.isna(last['Stoch']): continue

            # Logic
            cond_vol = last['Volume'] > last['Vol_Avg']
            cond_stoch = 20 < last['Stoch'] < 80
            
            match = False
            if mode == "Bullish (Buy)":
                if last['Close'] > last['VWAP'] and cond_vol and cond_stoch: match = True
            else:
                if last['Close'] < last['VWAP'] and cond_vol and cond_stoch: match = True
            
            if match:
                found_stocks.append({
                    'Symbol': symbol,
                    'Price': last['Close'],
                    'Time': last['Timestamp'].strftime('%H:%M:%S'), # Show Exact Time
                    'VWAP': round(last['VWAP'], 2),
                    'Stoch': round(last['Stoch'], 2),
                    'Vol_Ratio': round(last['Volume'] / last['Vol_Avg'], 2)
                })

        except:
            pass
            
    progress.empty()
    status.empty()
    found_stocks.sort(key=lambda x: x['Vol_Ratio'], reverse=True)
    return found_stocks

# --- 9. UI ---
st.title("📡 Fixed Live Scanner")
st.write(f"Scanning **{tf_selection}** for **{trend_mode}**")

if st.button("🚀 SCAN NOW"):
    with st.spinner("Fetching Fresh Data..."):
        results = scan_market(all_tickers, interval_str, trend_mode)
    
    if results:
        st.success(f"Found {len(results)} Stocks")
        for stock in results:
            css_class = "buy-card" if trend_mode == "Bullish (Buy)" else "sell-card"
            st.markdown(f"""
            <div class="{css_class}">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-size:22px; font-weight:bold; color:white;">{stock['Symbol']}</span>
                    <span class="time-badge">🕒 Candle: {stock['Time']}</span>
                </div>
                <div class="stock-price">₹{stock['Price']}</div>
                <div style="color:#ccc; font-size:14px;">
                    VWAP: {stock['VWAP']} | Stoch: {stock['Stoch']} | Vol: {stock['Vol_Ratio']}x
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No stocks found. Check 'Raw Data' in Admin panel to verify timestamps.")
