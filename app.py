import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import requests
import gzip
import io
import pytz
from datetime import datetime

# --- 1. CONFIGURATION (NEW NAME) ---
st.set_page_config(page_title="SniperTrade Live 🎯", layout="wide", page_icon="🎯")

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
    with st.spinner("Calibrating Sniper Scope..."):
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

# --- 4. CSS (PREMIUM LOOK) ---
st.markdown("""
<style>
    /* Sniper Green for Buy */
    .buy-card { 
        background: linear-gradient(145deg, #0f2015, #1e1e1e);
        border: 1px solid #333; 
        border-radius: 8px; 
        padding: 15px; 
        margin-bottom: 15px; 
        border-left: 5px solid #00ff41; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    /* Sniper Red for Sell */
    .sell-card { 
        background: linear-gradient(145deg, #2a0f0f, #1e1e1e);
        border: 1px solid #333; 
        border-radius: 8px; 
        padding: 15px; 
        margin-bottom: 15px; 
        border-left: 5px solid #ff4b4b; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .stock-symbol a { color: white; text-decoration: none; font-size: 20px; font-weight: 700; letter-spacing: 1px; }
    .stock-price { font-size: 28px; font-weight: 800; color: #fff; margin: 5px 0; font-family: 'Courier New', monospace; }
    
    .trade-setup {
        background-color: rgba(0,0,0,0.4);
        border-radius: 4px;
        padding: 8px;
        margin-top: 10px;
        display: flex;
        justify-content: space-between;
        font-weight: bold;
        border: 1px solid #444;
    }
    
    .target-txt { color: #00ff41; text-shadow: 0 0 5px rgba(0, 255, 65, 0.5); }
    .sl-txt { color: #ff4b4b; text-shadow: 0 0 5px rgba(255, 75, 75, 0.5); }
    
    .time-badge { font-size: 11px; color: #aaa; background: #222; padding: 2px 6px; border-radius: 4px; border: 1px solid #333; }
    
    .stButton>button { width: 100%; background-color: #262730; color: white; border: 1px solid #4c4c4c; }
</style>
""", unsafe_allow_html=True)

# --- 5. ADMIN ---
st.sidebar.title("⚙️ Sniper Control")
admin_pass = st.sidebar.text_input("Access Key", type="password")

if admin_pass == "1234":
    new_token = st.sidebar.text_area("Upstox Token:", value=store.access_token if store.access_token else "")
    if st.sidebar.button("Arm System 🚀"):
        store.access_token = new_token
        st.rerun()

# --- 6. AUTO REFRESH (60 Sec) ---
st_autorefresh(interval=60000, key="sniper_refresh")

trend_mode = st.sidebar.radio("Mission Mode:", ("Bullish (Buy)", "Bearish (Sell)"))

# --- 7. STOCK LIST ---
all_tickers = ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'ITC', 'INDUSINDBK', 'INFY', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIM', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'ULTRACEMCO', 'UPL', 'WIPRO', 'BANKBARODA', 'PNB', 'AUBANK', 'IDFCFIRSTB', 'FEDERALBNK', 'BANDHANBNK', 'POLYCAB', 'TATACOMM', 'PERSISTENT', 'COFORGE', 'LTTS', 'MPHASIS', 'ASHOKLEY', 'ASTRAL', 'JUBLFOOD', 'VOLTAS', 'TRENT', 'BEL', 'HAL', 'DLF', 'GODREJPROP', 'INDHOTEL', 'TATACHEM', 'TATAPOWER', 'JINDALSTEL', 'SAIL', 'NMDC', 'ZEEL', 'CANBK', 'REC', 'PFC', 'IRCTC', 'BOSCHLTD', 'CUMMINSIND', 'OBEROIRLTY', 'ESCORTS', 'SRF', 'PIIND', 'CONCOR', 'AUROPHARMA', 'LUPIN']

# --- 8. SCANNER LOGIC ---
def scan_market(tickers, mode):
    matches = []
    all_data = [] 
    
    if not store.access_token:
        return [], []

    progress = st.progress(0)
    status_text = st.empty()
    headers = {'Accept': 'application/json', 'Api-Version': '2.0', 'Authorization': f'Bearer {store.access_token}'}
    total = len(tickers)

    for i, symbol in enumerate(tickers):
        if i % 5 == 0: status_text.text(f"Tracking: {symbol}...")
        progress.progress((i+1)/total)

        try:
            key = get_instrument_key(symbol)
            if not key: continue

            # Intraday 1-Min API
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
            status_msg = "Wait"
            
            # --- TARGET & SL CALCULATION ---
            price = last['Close']
            vwap_val = last['VWAP']
            
            risk = abs(price - vwap_val)
            min_risk = price * 0.001 
            if risk < min_risk: risk = min_risk
            
            if mode == "Bullish (Buy)":
                sl_price = vwap_val
                target_price = price + (risk * 2)
                
                if price > vwap_val and cond_vol and cond_stoch: 
                    is_match = True
                    status_msg = "LOCKED 🎯"
                elif price <= vwap_val: status_msg = "Below VWAP"
            
            else: # Sell Mode
                sl_price = vwap_val
                target_price = price - (risk * 2)
                
                if price < vwap_val and cond_vol and cond_stoch: 
                    is_match = True
                    status_msg = "LOCKED 🎯"
                elif price >= vwap_val: status_msg = "Above VWAP"

            stock_data = {
                'Symbol': symbol,
                'Price': price,
                'Time': last['Timestamp'].strftime('%H:%M'),
                'VWAP': round(vwap_val, 2),
                'Stoch': round(last['Stoch'], 2),
                'Vol': last['Volume'],
                'Vol_Ratio': round(last['Volume'] / last['Vol_Avg'], 2),
                'Status': status_msg,
                'SL': round(sl_price, 2),
                'Target': round(target_price, 2)
            }
            
            all_data.append(stock_data)
            if is_match: matches.append(stock_data)

        except:
            pass
            
    progress.empty()
    status_text.empty()
    matches.sort(key=lambda x: x['Vol_Ratio'], reverse=True)
    return matches, all_data

# --- 9. UI DISPLAY ---
current_time = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%H:%M:%S")

st.title(f"🎯 SniperTrade Live")
st.markdown(f"<div style='margin-bottom: 20px;'><b>System Status:</b> <span style='color:#00ff41'>Online 🟢</span> | <b>Last Scan:</b> {current_time}</div>", unsafe_allow_html=True)

if store.access_token:
    results, full_data = scan_market(all_tickers, trend_mode)
    
    # 1. SHOW MATCHES
    if results:
        st.success(f"🔥 Targets Locked: {len(results)}")
        
        cols = st.columns(3)
        for i, stock in enumerate(results):
            with cols[i % 3]:
                css = "buy-card" if trend_mode == "Bullish (Buy)" else "sell-card"
                tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{stock['Symbol']}"
                st.markdown(f"""
                <div class="{css}">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="stock-symbol">
                            <a href="{tv_link}" target="_blank">{stock['Symbol']} 🔗</a>
                        </span>
                        <span class="time-badge">{stock['Time']}</span>
                    </div>
                    <div class="stock-price">₹{stock['Price']}</div>
                    <div class="trade-setup">
                        <span class="sl-txt">🛑 {stock['SL']}</span>
                        <span class="target-txt">🎯 {stock['Target']}</span>
                    </div>
                    <div style="color:#bbb; font-size:12px; margin-top:8px; display:flex; justify-content:space-between;">
                         <span>Vol: {stock['Vol_Ratio']}x</span>
                         <span>Stoch: {stock['Stoch']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Scanning for High-Probability Setups... (No locks yet)")

    # 2. SHOW ALL DATA
    st.markdown("---")
    st.subheader("📋 Recon Data (All Stocks)")
    if full_data:
        df_all = pd.DataFrame(full_data)
        df_all = df_all[['Symbol', 'Price', 'Status', 'SL', 'Target', 'Vol_Ratio', 'Time']]
        st.dataframe(df_all, use_container_width=True, hide_index=True)

else:
    st.warning("⚠️ System Disarmed. Enter Token in Sidebar to Arm.")
