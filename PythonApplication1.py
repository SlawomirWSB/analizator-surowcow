import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja i automatyczne odświeżanie
st.set_page_config(layout="wide", page_title="Trader PRO V14")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Ukrywanie zbędnych elementów i styl paska
st.markdown("""
<style>
    .block-container { padding: 0rem !important; }
    header { visibility: hidden; }
    .stSelectbox { margin-bottom: -20px; }
</style>
""", unsafe_allow_html=True)

# Stabilna baza danych symboli
DB = {
    "ZŁOTO": {"yf": "GC=F", "tv": "OANDA:XAUUSD"},
    "KAKAO": {"yf": "CC=F", "tv": "CAPITALCOM:COCOA"},
    "BTC": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},
    "DAX": {"yf": "^GDAXI", "tv": "GLOBALPRIME:GER30"}
}

def get_signal(symbol):
    try:
        data = yf.download(symbol, period="2d", interval="15m", progress=False)
        if data.empty: return "BRAK DANYCH", "#444"
        if isinstance(data.columns, pd.MultiIndex): 
            data.columns = data.columns.get_level_values(0)
        
        e9 = data['Close'].ewm(span=9).mean().iloc[-1]
        e21 = data['Close'].ewm(span=21).mean().iloc[-1]
        return ("KUPNO", "#26a69a") if e9 > e21 else ("SPRZEDAŻ", "#ef5350")
    except:
        return "BŁĄD", "#444"

def main():
    # Wybór instrumentu na górze
    col1, col2 = st.columns([2, 1])
    with col1:
        inst = st.selectbox("Instrument:", list(DB.keys()))
    with col2:
        itv = st.selectbox("Interwał:", ["1", "5", "15", "60", "D"], index=2)

    # Obliczanie sygnału
    status, color = get_signal(DB[inst]["yf"])

    # Pasek statusu
    st.markdown(f"""
    <div style="background:#131722; padding:10px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333;">
        <b style="color:#FFB400; font-size:18px; margin-left:10px;">{inst}</b>
        <div style="background:{color}; color:white; padding:5px 20px; border-radius:4px; font-weight:bold; margin-right:10px;">
            {status}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Widget TradingView - Poprawiony kod HTML/JS
    tv_code = f"""
    <div id="tv-widget" style="height: 80vh;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{
      "autosize": true,
      "symbol": "{DB[inst]['tv']}",
      "interval": "{itv}",
      "timezone": "Europe/Warsaw",
      "theme": "dark",
      "style": "1",
      "locale": "pl",
      "enable_publishing": false,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "container_id": "tv-widget"
    }});
    </script>
    """
    components.html(tv_code, height=750)

if __name__ == "__main__":
    main()
