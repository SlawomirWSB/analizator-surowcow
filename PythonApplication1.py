import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="PRO Trader V16")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# Ukrywanie zbędnych elementów
st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

# Baza danych (Symbole)
DB = {
    "SUROWCE": {
        "ZŁOTO": {"yf": "GC=F", "tv": "TVC:GOLD"},
        "KAKAO": {"yf": "CC=F", "tv": "PEPPERSTONE:COCOA"},
        "ROPA WTI": {"yf": "CL=F", "tv": "TVC:USOIL"}
    },
    "KRYPTO": {
        "BTC": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},
        "ETH": {"yf": "ETH-USD", "tv": "BINANCE:ETHUSDT"}
    }
}

def get_advanced_signal(symbol):
    try:
        # Pobieranie danych
        data = yf.download(symbol, period="5d", interval="15m", progress=False)
        if data.empty: return "BRAK DANYCH", "Brak", "#444"
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        # Obliczenia techniczne (EMA i RSI)
        data['EMA9'] = ta.ema(data['Close'], length=9)
        data['EMA21'] = ta.ema(data['Close'], length=21)
        data['RSI'] = ta.rsi(data['Close'], length=14)
        
        last = data.iloc[-1]
        rsi_val = round(last['RSI'], 1)
        
        # LOGIKA SYGNAŁU:
        # KUPNO: EMA9 > EMA21 ORAZ RSI < 70 (nie jest za drogo)
        # SPRZEDAŻ: EMA9 < EMA21 ORAZ RSI > 30 (nie jest za tanio)
        if last['EMA9'] > last['EMA21']:
            if rsi_val < 70: return "KUPNO", rsi_val, "#26a69a"
            else: return "CZEKAJ (Wykupienie)", rsi_val, "#f39c12"
        else:
            if rsi_val > 30: return "SPRZEDAŻ", rsi_val, "#ef5350"
            else: return "CZEKAJ (Wyprzedanie)", rsi_val, "#f39c12"
    except:
        return "BŁĄD", "0", "#444"

def main():
    # Menu wyboru
    c1, c2 = st.columns([2, 1])
    with c1:
        rynek = st.selectbox("Rynek:", list(DB.keys()), label_visibility="collapsed")
        inst = st.selectbox("Instrument:", list(DB[rynek].keys()), label_visibility="collapsed")
    with c2:
        itv = st.selectbox("Interwał wykresu:", ["1", "5", "15", "60", "D"], index=2, label_visibility="collapsed")

    # Pobieranie sygnału
    status, rsi, color = get_advanced_signal(DB[rynek][inst]["yf"])

    # Pasek statusu
    st.markdown(f"""
    <div style="background:#131722; padding:10px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; color:white;">
        <div><b>{inst}</b> | RSI: <span style="color:#FFB400">{rsi}</span></div>
        <div style="background:{color}; padding:4px 15px; border-radius:3px; font-weight:bold; font-size:12px;">{status}</div>
    </div>
    """, unsafe_allow_html=True)

    # WIDGET Z DODANYMI WSKAŹNIKAMI (EMA 9, 21 i RSI)
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
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "studies": [
        "EMA@tv-basicstudies", 
        "EMA@tv-basicstudies", 
        "RSI@tv-basicstudies"
      ],
      "container_id": "tv_chart"
    }});
    </script>
    """
    components.html(tv_code, height=750)

if __name__ == "__main__":
    main()
