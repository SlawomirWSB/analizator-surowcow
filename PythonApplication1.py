import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="Trader PRO V17")
st_autorefresh(interval=60 * 1000, key="data_refresh")

st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

# Baza danych
DB = {
    "SUROWCE": {
        "ZŁOTO": {"yf": "GC=F", "tv": "TVC:GOLD"},
        "KAKAO": {"yf": "CC=F", "tv": "TVC:COCOA"}, # Najbardziej stabilny symbol
        "SREBRO": {"yf": "SI=F", "tv": "TVC:SILVER"}
    },
    "KRYPTO": {
        "BTC": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},
        "ETH": {"yf": "ETH-USD", "tv": "BINANCE:ETHUSDT"}
    }
}

def get_signal(symbol):
    try:
        data = yf.download(symbol, period="5d", interval="15m", progress=False)
        if data.empty: return "BRAK DANYCH", "0", "#444"
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        # Obliczenia EMA (bez dodatkowych bibliotek)
        data['EMA9'] = data['Close'].ewm(span=9, adjust=False).mean()
        data['EMA21'] = data['Close'].ewm(span=21, adjust=False).mean()
        
        # Obliczenia RSI (czysty pandas)
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        last = data.iloc[-1]
        rsi_val = round(last['RSI'], 1)
        
        if last['EMA9'] > last['EMA21']:
            return ("KUPNO", rsi_val, "#26a69a") if rsi_val < 70 else ("WYKUPIONY", rsi_val, "#f39c12")
        else:
            return ("SPRZEDAŻ", rsi_val, "#ef5350") if rsi_val > 30 else ("WYPRZEDANY", rsi_val, "#f39c12")
    except:
        return "BŁĄD", "0", "#444"

def main():
    col1, col2 = st.columns([2, 1])
    with col1:
        rynek = st.selectbox("Rynek:", list(DB.keys()))
        inst = st.selectbox("Instrument:", list(DB[rynek].keys()))
    with col2:
        itv = st.selectbox("Interwał:", ["1", "5", "15", "60", "D"], index=2)

    status, rsi, color = get_signal(DB[rynek][inst]["yf"])

    st.markdown(f"""
    <div style="background:#131722; padding:10px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; color:white;">
        <div><b>{inst}</b> | RSI: <span style="color:#FFB400">{rsi}</span></div>
        <div style="background:{color}; padding:4px 15px; border-radius:3px; font-weight:bold; font-size:12px;">{status}</div>
    </div>
    """, unsafe_allow_html=True)

    tv_code = f"""
    <div id="tv_chart" style="height: 80vh;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{
      "autosize": true,
      "symbol": "{DB[rynek][inst]['tv']}",
      "interval": "{itv}",
      "timezone": "Europe/Warsaw",
      "theme": "dark",
      "style": "1",
      "locale": "pl",
      "enable_publishing": false,
      "studies": ["EMA@tv-basicstudies", "EMA@tv-basicstudies", "RSI@tv-basicstudies"],
      "container_id": "tv_chart"
    }});
    </script>
    """
    components.html(tv_code, height=750)

if __name__ == "__main__":
    main()
