import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import datetime
import requests
import gzip
import io
import pytz

# --- 1. CONFIG ---
st.set_page_config(page_title="Momentum Radar Pro (Live)", layout="wide", page_icon="📡")

# --- 2. GLOBAL STORE ---
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
    .stock-price { font-size: 26px; font-weight: bold; color: #fff; }
    .time-badge { font-size: 12px; color: #aaa; background: #333; padding: 2px 5px; border-radius: 4px; }
    .stButton>button { width: 100%; background-color: #262730; color: white; border: 1px solid #4c4c4c; }
</style>
""", unsafe_allow_html=True)

# --- 5. ADMIN ---
st.sidebar.title("⚙️ Admin")
admin_pass = st.sidebar.text_input("Login", type="password")

if admin_pass == "1234":
    new_token = st.sidebar.text_area("Token:", value=store.access_token if store.access_token else "")
    if st.sidebar.button("Save Token"):
        store.access_token = new_token
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.write("🛠️ **Debugger**")
    test_symbol = st.sidebar.text_input("Test Symbol", value="SBIN")
    
    if st.sidebar.button("Check 5-Min Data"):
        if store.access_token:
            key = get_instrument_key(test_symbol)
            if key:
                # Testing with Historical URL (5 Days Safe Limit)
                end = datetime.datetime.now().strftime("%Y-%m-%d")
                start = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
                url = f"https://api.upstox.com/v2/historical-candle/{key}/5minute/{end}/{start}"
                headers = {'Accept': 'application/json', 'Api-Version': '2.0', 'Authorization': f'Bearer {store.access_token}'}
                res = requests.get(url, headers=headers)
                
                if res.status_code == 200:
                    data = res.json()
                    if 'data' in data and 'candles' in data['data']:
                        st.sidebar.success(f"Success! Got {len(data['data']['candles'])} candles")
                    else:
                        st.sidebar.warning("Empty Data")
                else:
                    st.sidebar.error(f"Error {res.status_code}: {res.text}")

# --- 6. SETTINGS ---
use_autorefresh = st.sidebar.checkbox("Auto-Refresh")
if use_autorefresh:
    st_autorefresh(interval=60000)

tf_selection = st.sidebar.selectbox("Timeframe:", ("1 Minute", "5 Minutes", "15 Minutes", "30 Minutes"))
trend_mode = st.sidebar.radio("Signal:", ("Bullish (Buy)", "Bearish (Sell)"))

upstox_tf_map = {
    "1 Minute": "1minute", "5 Minutes": "5minute", "15 Minutes": "15minute", "30 Minutes": "30minute"
}
interval_str = upstox_tf_map[tf_selection]

all_tickers = ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'ITC', 'INDUSINDBK', 'INFY', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIM', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'ULTRACEMCO', 'UPL', 'WIPRO', 'BANKBARODA', 'PNB', 'AUBANK', 'IDFCFIRSTB', 'FEDERALBNK', 'BANDHANBNK', 'POLYCAB', 'TATACOMM', 'PERSISTENT', 'COFORGE', 'LTTS', 'MPHASIS', 'ASHOKLEY', 'ASTRAL', 'JUBLFOOD', 'VOLTAS', 'TRENT', 'BEL', 'HAL', 'DLF', 'GODREJPROP', 'INDHOTEL', 'TATACHEM', 'TATAPOWER', 'JINDALSTEL', 'SAIL', 'NMDC', 'ZEEL', 'CANBK', 'REC', 'PFC', 'IRCTC', 'BOSCHLTD', 'CUMMINSIND', 'OBEROIRLTY', 'ESCORTS', 'SRF', 'PIIND', 'CONCOR', 'AUROPHARMA', 'LUPIN']

# --- 7. SCANNER ---
def scan_market(tickers, interval, mode):
    found_stocks = []
    logs = []
    
    if not store.access_token:
        st.error("Admin Token Required")
        return [], []

    progress = st.progress(0)
    status = st.empty()
    headers = {'Accept': 'application/json', 'Api-Version': '2.0', 'Authorization': f'Bearer {store.access_token}'}

    # --- DATE SETTINGS (Safe Limit) ---
    # Upstox doesn't like large ranges for minute data.
    # We use 5 days, which is enough for indicators and safe from Error 400.
    to_date = datetime.datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%d")

    for i, symbol in enumerate(tickers):
        status.text(f"Scanning {symbol}...")
        progress.progress((i+1)/len(tickers))

        try:
            key = get_instrument_key(symbol)
            if not key: continue

            # Using HISTORICAL endpoint with DATES (This supports 5min/15min)
            url = f"https://api.upstox.com/v2/historical-candle/{key}/{interval}/{to_date}/{from_date}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logs.append(f"{symbol}: API Error {response.status_code}")
                continue
            
            data = response.json()
            if 'data' not in data or 'candles' not in data['data']:
                logs.append(f"{symbol}: No Data")
                continue

            candles = data['data']['candles']
            df = pd.DataFrame(candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
            
            # Clean & Sort
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.sort_values('Timestamp').reset_index(drop=True)
            ist = pytz.timezone('Asia/Kolkata')
            df['Timestamp'] = df['Timestamp'].dt.tz_convert(ist)

            # --- INDICATORS ---
            df['Date'] = df['Timestamp'].dt.date
            
            # VWAP
            df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['Vol_Price'] = df['TP'] * df['Volume']
            df['Cum_Vol_Price'] = df.groupby('Date')['Vol_Price'].cumsum()
            df['Cum_Vol'] = df.groupby('Date')['Volume'].cumsum()
            df['VWAP'] = df['Cum_Vol_Price'] / df['Cum_Vol']

            # Stoch (Variable Names FIXED Here)
            low_14 = df['Low'].rolling(14).min()
            high_14 = df['High'].rolling(14).max() # <--- Variable name fixed (was high_max)
            
            # Check for ZeroDivisionError (if High == Low)
            denominator = high_14 - low_14
            denominator = denominator.replace(0, 0.0001) # Avoid division by zero
            
            df['%K'] = 100 * ((df['Close'] - low_14) / denominator)
            df['Stoch'] = df['%K'].rolling(3).mean()
            df['Vol_Avg'] = df['Volume'].rolling(20).mean()

            last = df.iloc[-1]
            if pd.isna(last['VWAP']) or pd.isna(last['Stoch']): 
                logs.append(f"{symbol}: Calculating...")
                continue

            # --- LOGIC ---
            cond_vol = last['Volume'] > last['Vol_Avg']
            cond_stoch = 20 < last['Stoch'] < 80
            
            is_match = False
            
            if mode == "Bullish (Buy)":
                if last['Close'] > last['VWAP'] and cond_vol and cond_stoch: is_match = True
            else:
                if last['Close'] < last['VWAP'] and cond_vol and cond_stoch: is_match = True
            
            if is_match:
                found_stocks.append({
                    'Symbol': symbol,
                    'Price': last['Close'],
                    'Time': last['Timestamp'].strftime('%H:%M:%S'),
                    'Date': last['Timestamp'].strftime('%Y-%m-%d'),
                    'VWAP': round(last['VWAP'], 2),
                    'Stoch': round(last['Stoch'], 2),
                    'Vol_Ratio': round(last['Volume'] / last['Vol_Avg'], 2)
                })

        except Exception as e:
            logs.append(f"{symbol}: {str(e)}")
            pass
            
    progress.empty()
    status.empty()
    found_stocks.sort(key=lambda x: x['Vol_Ratio'], reverse=True)
    return found_stocks, logs

# --- 8. UI ---
st.title("📡 Momentum Radar (Fixed & Robust)")
st.write(f"Scanning **{trend_mode}** on **{tf_selection}**")

if st.button("🚀 SCAN NOW"):
    with st.spinner("Scanning Market..."):
        results, debug_logs = scan_market(all_tickers, interval_str, trend_mode)
    
    if results:
        st.success(f"Found {len(results)} Stocks")
        for stock in results:
            css = "buy-card" if trend_mode == "Bullish (Buy)" else "sell-card"
            tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{stock['Symbol']}"
            st.markdown(f"""
            <div class="{css}">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-size:22px; font-weight:bold; color:white;">
                        <a href="{tv_link}" target="_blank" style="color:white;text-decoration:none;">{stock['Symbol']} 🔗</a>
                    </span>
                    <span class="time-badge">🕒 {stock['Time']}</span>
                </div>
                <div class="stock-price">₹{stock['Price']}</div>
                <div style="color:#ccc; font-size:14px;">
                    VWAP: {stock['VWAP']} | Stoch: {stock['Stoch']} | Vol: {stock['Vol_Ratio']}x
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No matches found.")
        with st.expander("See Scan Logs"):
            st.write(debug_logs)
