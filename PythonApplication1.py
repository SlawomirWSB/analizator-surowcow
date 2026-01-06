import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja i odświeżanie
st.set_page_config(layout="wide", page_title="Real-Time Signal V23")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# Ukrywanie elementów interfejsu
st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

# Poprawiona baza danych (CAPITALCOM dla stabilności Kakao)
DB = {
    "SUROWCE": {
        "ZŁOTO": {"yf": "GC=F", "tv": "OANDA:XAUUSD"},
        "KAKAO": {"yf": "CC=F", "tv": "CAPITALCOM:COCOA"}, # CFD zazwyczaj działa bez blokad
        "SREBRO": {"yf": "SI=F", "tv": "OANDA:XAGUSD"}
    },
    "KRYPTO": {
        "BTC": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},
        "ETH": {"yf": "ETH-USD", "tv": "BINANCE:ETHUSDT"}
    }
}

def main():
    # Menu wyboru
    c1, c2, c3 = st.columns(3)
    with c1: rynek = st.selectbox("Rynek", list(DB.keys()))
    with c2: inst = st.selectbox("Instrument", list(DB[rynek].keys()))
    with c3: itv = st.selectbox("Interwał", ["1", "5", "15", "60", "D"], index=1)

    # Informacja o sygnale
    st.info("Sygnały KUPNO/SPRZEDAŻ są generowane w czasie rzeczywistym bezpośrednio na wykresie przez przecięcia średnich EMA.")

    # WIDGET Z WBUDOWANYMI SYGNAŁAMI
    # Dodajemy 'MA Cross' - wskaźnik, który rysuje krzyżyki przy przecięciu średnich
    tv_code = f"""
    <div id="tv_chart_v23" style="height: 75vh;"></div>
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
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "studies": [
        "EMA@tv-basicstudies",
        "EMA@tv-basicstudies",
        "RSI@tv-basicstudies",
        "MAExpCross@tv-basicstudies" 
      ],
      "container_id": "tv_chart_v23"
    }});
    </script>
    """
    # MAExpCross (Moving Average Exponential Cross) automatycznie zaznaczy sygnały na wykresie.
    components.html(tv_code, height=700)

if __name__ == "__main__":
    main()
