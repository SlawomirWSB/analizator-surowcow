import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="XTB Real-Time V19")
st_autorefresh(interval=60 * 1000, key="data_refresh")

st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

# BAZA DANYCH - Zmienione symbole dla stabilności
DB = {
    "SUROWCE": {
        "KAKAO": {"yf": "CC=F", "tv": "CAPITALCOM:COCOA"},
        "ZŁOTO": {"yf": "GC=F", "tv": "OANDA:XAUUSD"},
        "SREBRO": {"yf": "SI=F", "tv": "OANDA:XAGUSD"},
        "ROPA WTI": {"yf": "CL=F", "tv": "TVC:USOIL"}
    },
    "INDEKSY": {
        "DAX (DE30)": {"yf": "^GDAXI", "tv": "GLOBALPRIME:GER30"},
        "US500": {"yf": "^GSPC", "tv": "VANTAGE:SP500"}
    },
    "KRYPTO": {
        "BITCOIN": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"}
    }
}

def get_market_data(symbol):
    try:
        data = yf.download(symbol, period="2d", interval="15m", progress=False)
        if data.empty: return 0.0, 0.0, "00:00", "#444"
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        last_price = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[0]
        change = ((last_price - prev_close) / prev_close) * 100
        time_now = datetime.now().strftime("%H:%M:%S")
        
        color = "#26a69a" if change >= 0 else "#ef5350"
        return last_price, change, time_now, color
    except:
        return 0.0, 0.0, "00:00", "#444"

def main():
    # MENU
    c1, c2 = st.columns([2, 1])
    with c1:
        rynek = st.selectbox("Wybierz rynek:", list(DB.keys()))
        inst = st.selectbox("Instrument:", list(DB[rynek].keys()))
    with c2:
        itv = st.selectbox("Interwał:", ["1", "5", "15", "60", "D"], index=2)

    price, change, update_time, color = get_market_data(DB[rynek][inst]["yf"])

    # PASEK STATUSU
    st.markdown(f"""
    <div style="background:#131722; padding:15px; border-bottom:1px solid #333; color:white;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="color:#aaa; font-size:12px;">Cena (opóźniona):</span><br>
                <b style="font-size:22px;">{price:,.2f}</b>
                <span style="color:{color}; font-weight:bold; margin-left:10px;">{change:+.2f}%</span>
            </div>
            <div style="text-align:right;">
                <span style="color:#aaa; font-size:12px;">Aktualizacja apki:</span><br>
                <b>{update_time}</b>
            </div>
        </div>
        <div style="font-size:10px; color:#ef5350; margin-top:5px;">⚠️ Sygnał na wykresie poniżej jest w CZASIE RZECZYWISTYM. Napis powyżej ma opóźnienie.</div>
    </div>
    """, unsafe_allow_html=True)

    # WIDGET Z WSKAŹNIKAMI: EMA9, EMA21, RSI, WOLUMEN
    # Wskaźniki wstudies dodają sygnały bezpośrednio na wykres!
    tv_code = f"""
    <div id="tv_chart" style="height: 75vh;"></div>
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
        "Volume@tv-basicstudies"
      ],
      "container_id": "tv_chart"
    }});
    </script>
    """
    components.html(tv_code, height=700)

if __name__ == "__main__":
    main()
