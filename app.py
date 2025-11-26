import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import requests
import gzip
import io
import pytz

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Pro Live Scanner (1-Min)", layout="wide", page_icon="⚡")

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
    with st.spinner("Downloading 91 Stocks List..."):
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
    new_token = st.sidebar.text_area("Upstox Token:", value=store.access_token if store.access_token else "")
    if st.sidebar.button("Save Token"):
        store.access_token = new_token
        st.rerun()

# --- 6. SETTINGS ---
# AUTO REFRESH SET TO 60 SECONDS
st_autorefresh(interval=60000, key="market_scanner")

trend_mode = st.sidebar.radio("Signal Mode:", ("Bullish (Buy)", "Bearish (Sell)"))

# --- 7. STOCK LIST (91 Stocks) ---
all_tickers = ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'ITC', 'INDUSINDBK', 'INFY', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIM', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'ULTRACEMCO', 'UPL', 'WIPRO', 'BANKBARODA', 'PNB', 'AUBANK', 'IDFCFIRSTB', 'FEDERALBNK', 'BANDHANBNK', 'POLYCAB', 'TATACOMM', 'PERSISTENT', 'COFORGE', 'LTTS', 'MPHASIS', 'ASHOKLEY', 'ASTRAL', 'JUBLFOOD', 'VOLTAS', 'TRENT', 'BEL', 'HAL', 'DLF', 'GODREJPROP', 'INDHOTEL', 'TATACHEM', 'TATAPOWER', 'JINDALSTEL', 'SAIL', 'NMDC', 'ZEEL', 'CANBK', 'REC', 'PFC', 'IRCTC', 'BOSCHLTD', 'CUMMINSIND', 'OBEROIRLTY', 'ESCORTS', 'SRF', 'PIIND', 'CONCOR', 'AUROPHARMA', 'LUPIN']

# --- 8. SCANNER LOGIC ---
def scan_market(tickers, mode):
    matches = []
    all_data = [] # To store data of ALL stocks for verification
    
    if not store.access_token:
        st.error("⚠️ Admin Token Required in Sidebar")
        return [], []

    progress = st.progress(0)
    status = st.empty()
    headers = {'Accept': 'application/json', 'Api-Version': '2.0', 'Authorization': f'Bearer {store.access_token}'}
    total = len(tickers)

    for i, symbol in enumerate(tickers):
        status.text(f"Scanning {symbol} ({i+1}/{total})...")
        progress.progress((i+1)/total)

        try:
            key = get_instrument_key(symbol)
            if not key: continue

            # Intraday API (No Date Issues)
            url = f"https://api.upstox.com/v2/historical-candle/intraday/{key}/1minute"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200: continue
            
            data = response.json()
            if 'data' not in data or 'candles' not in data['data']: continue

            candles = data['data']['candles']
            df = pd.DataFrame(candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
            
            # Cleaning
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.sort_values('Timestamp').reset_index(drop=True)
            ist = pytz.timezone('Asia/Kolkata')
            df['Timestamp'] = df['Timestamp'].dt.tz_convert(ist)

            # Indicators
            df['Date'] = df['Timestamp'].dt.date
            df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['Vol_Price'] = df['TP'] * df['Volume']
            df['Cum_Vol_Price'] = df.groupby('Date')['Vol_Price'].cumsum()
            df['Cum_Vol'] = df.groupby('Date')['Volume'].cumsum()
            df['VWAP'] = df['Cum_Vol_Price'] / df['Cum_Vol']

            low_14 = df['Low'].rolling(14).min()
            high_14 = df['High'].rolling(14).max()
            denom = high_14 - low_14
            denom = denom.replace(0, 0.001)
            df['%K'] = 100 * ((df['Close'] - low_14) / denom)
            df['Stoch'] = df['%K'].rolling(3).mean()
            df['Vol_Avg'] = df['Volume'].rolling(20).mean()

            last = df.iloc[-1]
            if pd.isna(last['VWAP']) or pd.isna(last['Stoch']): continue

            # Logic
            cond_vol = last['Volume'] > last['Vol_Avg']
            cond_stoch = 20 < last['Stoch'] < 80
            
            is_match = False
            status_msg = "Weak"
            
            if mode == "Bullish (Buy)":
                if last['Close'] > last['VWAP'] and cond_vol and cond_stoch: 
                    is_match = True
                    status_msg = "Match ✅"
                elif last['Close'] <= last['VWAP']: status_msg = "Below VWAP"
                elif not cond_vol: status_msg = "Low Vol"
                elif not cond_stoch: status_msg = "Stoch Range"
            else:
                if last['Close'] < last['VWAP'] and cond_vol and cond_stoch: 
                    is_match = True
                    status_msg = "Match ✅"
                elif last['Close'] >= last['VWAP']: status_msg = "Above VWAP"
                elif not cond_vol: status_msg = "Low Vol"

            # Save Data
            stock_data = {
                'Symbol': symbol,
                'Price': last['Close'],
                'Time': last['Timestamp'].strftime('%H:%M'),
                'VWAP': round(last['VWAP'], 2),
                'Stoch': round(last['Stoch'], 2),
                'Vol': last['Volume'],
                'Vol_Avg': round(last['Vol_Avg'], 0),
                'Vol_Ratio': round(last['Volume'] / last['Vol_Avg'], 2),
                'Status': status_msg
            }
            
            all_data.append(stock_data)
            
            if is_match:
                matches.append(stock_data)

        except:
            pass
            
    progress.empty()
    status.empty()
    matches.sort(key=lambda x: x['Vol_Ratio'], reverse=True)
    return matches, all_data

# --- 9. UI ---
st.title("⚡ Pro 1-Min Scanner (All 91 Stocks)")
st.write(f"Mode: **{trend_mode}** | Auto-Refresh: **60s**")

if st.button("🚀 SCAN NOW"):
    with st.spinner("Analyzing Live Data..."):
        results, full_data = scan_market(all_tickers, trend_mode)
    
    # 1. SHOW MATCHES
    if results:
        st.success(f"🔥 Found {len(results)} Perfect Matches")
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
        st.warning("No Perfect Matches Found right now.")

    # 2. SHOW ALL DATA (USER REQUIREMENT)
    st.markdown("---")
    st.subheader("📋 All 91 Stocks Status")
    if full_data:
        df_all = pd.DataFrame(full_data)
        # Reorder columns
        df_all = df_all[['Symbol', 'Price', 'Status', 'VWAP', 'Stoch', 'Vol_Ratio', 'Time']]
        st.dataframe(df_all, use_container_width=True)
