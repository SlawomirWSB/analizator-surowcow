import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="PRO Chart V12")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS dla pełnej szerokości
st.markdown("<style>.block-container { padding: 0rem !important; }</style>", unsafe_allow_html=True)

DB = {
    "Złoto": {"symbol": "GC=F", "tv_id": "COMEX:GC1!"},
    "Kakao": {"symbol": "CC=F", "tv_id": "ICEUS:CC1!"},
    "BTC": {"symbol": "BTC-USD", "tv_id": "BINANCE:BTCUSDT"}
}

def get_signal(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="15m", progress=False)
        if df.empty: return "BRAK DANYCH", "#555"
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
        ema21 = df['Close'].ewm(span=21).mean().iloc[-1]
        
        if ema9 > ema21: return "SYGNAŁ: KUPNO", "#26a69a"
        else: return "SYGNAŁ: SPRZEDAŻ", "#ef5350"
    except:
        return "ŁADOWANIE...", "#555"

def main():
    # Wybór na samej górze (bardzo wąski pasek)
    c1, c2 = st.columns([2, 1])
    inst_name = c1.selectbox("Zmień instrument:", list(DB.keys()), label_visibility="collapsed")
    
    # Obliczanie sygnału w tle
    status, s_color = get_signal(DB[inst_name]["symbol"])
    
    # Pasek statusu a'la XTB
    st.markdown(f"""
        <div style="background:#000; padding:10px; border-bottom:1px solid #333; display:flex; justify-content:space-between; align-items:center;">
            <b style="color:#f39c12; font-size:16px;">{inst_name.upper()}</b>
            <div style="background:{s_color}; color:white; padding:4px 12px; border-radius:4px; font-weight:bold; font-size:12px;">{status}</div>
        </div>
    """, unsafe_allow_html=True)

    # WSTAWIENIE ORYGINALNEGO WYKRESU TRADINGVIEW (Widget)
    # To zapewnia idealne przesuwanie i brak luk
    tv_code = f"""
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{DB[inst_name]['tv_id']}",
        "interval": "15",
        "timezone": "Europe/Warsaw",
        "theme": "dark",
        "style": "1",
        "locale": "pl",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "hide_top_toolbar": false,
        "save_image": false,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    
    components.html(tv_code, height=700)

if __name__ == "__main__":
    main()
