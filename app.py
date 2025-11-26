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
    with st.spinner("Initializing Master Stock List..."):
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
    
    # Token Input
    new_token = st.sidebar.text_area("Upstox Token:", value=store.access_token if store.access_token else "")
    if st.sidebar.button("Save Token 💾"):
        store.access_token = new_token
        st.sidebar.success("Saved!")
        st.rerun()

    # --- DEBUGGING BUTTON (FIXED) ---
    st.sidebar.markdown("---")
    if st.sidebar.button("🛠️ Test API Connection"):
        if not store.access_token:
            st.sidebar.error("No Token Found!")
        else:
            try:
                st.sidebar.info("Testing connection with SBIN...")
                conf = upstox_client.Configuration()
                conf.access_token = store.access_token
                api = upstox_client.HistoryApi(upstox_client.ApiClient(conf))
                
                key = get_instrument_key("SBIN")
                if not key:
                    st.sidebar.error("Instrument List Error!")
                else:
                    # FIX: Removed dates, kept only api_version
                    res = api.get_intra_day_candle_data(
                        instrument_key=key, 
                        interval="30minute", 
                        api_version='2.0'
                    )
                    
                    if res.data and res.data.candles:
                        st.sidebar.success(f"Success! Data Received. Last Price: {res.data.candles[0][4]}")
                        st.sidebar.write(res.data.candles[0])
                    else:
                        st.sidebar.warning("Token working, but NO DATA returned. Market closed?")
            except Exception as e:
                st.sidebar.error(f"API Error: {str(e)}")

else:
    pass

# --- 6. SETTINGS ---
use_autorefresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh")
if use_autorefresh:
    refresh_rate = st.sidebar.slider("Refresh (s)", 30, 300, 60)
    st_autorefresh(interval=refresh_rate * 1000, key="market_scanner")

st.sidebar.markdown("---")
tf_selection = st.sidebar.selectbox("Timeframe:", ("1 Minute", "5 Minutes", "15 Minutes", "30 Minutes"))
trend_mode = st.sidebar.radio("Signal Type:", ("Bullish (Buy)", "Bearish (Sell)"))

upstox_tf_map = {"1 Minute": "1minute", "5 Minutes": "5minute", "15 Minutes": "15minute", "30 Minutes": "30minute"}
interval_str = upstox_tf_map[tf_selection]

# --- 7. STOCKS ---
nifty50 = ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'ITC', 'INDUSINDBK', 'INFY', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIM', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'ULTRACEMCO', 'UPL', 'WIPRO']
banknifty = ['BANKBARODA', 'PNB', 'AUBANK', 'IDFCFIRSTB', 'FEDERALBNK', 'BANDHANBNK']
midcap = ['POLYCAB', 'TATACOMM', 'PERSISTENT', 'COFORGE', 'LTTS', 'MPHASIS', 'ASHOKLEY', 'ASTRAL', 'JUBLFOOD', 'VOLTAS', 'TRENT', 'BEL', 'HAL', 'DLF', 'GODREJPROP', 'INDHOTEL', 'TATACHEM', 'TATAPOWER', 'JINDALSTEL', 'SAIL', 'NMDC', 'ZEEL', 'CANBK', 'REC', 'PFC', 'IRCTC', 'BOSCHLTD', 'CUMMINSIND', 'OBEROIRLTY', 'ESCORTS', 'SRF', 'PIIND', 'CONCOR', 'AUROPHARMA', 'LUPIN']
all_tickers = list(set(nifty50 + banknifty + midcap))

# --- 8. SCANNER ---
def scan_market_upstox(tickers, interval, mode):
    found_stocks = []
    
    if not store.access_token:
        st.error("⚠️ System Offline. Admin needs to set Token.")
        return []

    config = upstox_client.Configuration()
    config.access_token = store.access_token
    api_instance = upstox_client.HistoryApi(upstox_client.ApiClient(config))
    
    progress_bar = st.progress(0)
    status = st.empty()
    total = len(tickers)

    for i, symbol in enumerate(tickers):
        status.text(f"Scanning {symbol}...")
        progress_bar.progress((i + 1) / total)

        try:
            inst_key = get_instrument_key(symbol)
            if not inst_key: continue

            # FIX: Removed to_date/from_date
            api_response = api_instance.get_intra_day_candle_data(
                instrument_key=inst_key, 
                interval=interval,
                api_version='2.0'
            )
            
            if not api_response.data or not api_response.data.candles: continue

            candles = api_response.data.candles
            columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI']
            df = pd.DataFrame(candles, columns=columns)
            
            # REVERSE DATA (Latest at bottom for calculation, but Upstox gives Latest at Top)
            # Upstox gives: [Latest, Old, Older...]
            # We need: [Older, Old, Latest] for rolling window
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
st.write(f"Scanning **{trend_mode}** | Source: **Upstox API**")

if st.button('🚀 START LIVE SCAN') or use_autorefresh:
    if not store.access_token:
        st.warning("⚠️ Waiting for Admin Token...")
    else:
        with st.spinner('Fetching Live Data...'):
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
            st.info("Market is sideways. No high-momentum stocks found.")
