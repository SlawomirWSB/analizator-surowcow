import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="PRO Trader V22")
st_autorefresh(interval=60 * 1000, key="data_refresh")

st.markdown("""
<style>
    .block-container { padding: 0rem !important; }
    header { visibility: hidden; }
    .signal-box {
        background: #1e222d; border: 1px solid #333;
        border-radius: 8px; padding: 15px; margin: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# Baza danych - CAPITALCOM zazwyczaj nie jest blokowany dla Kakao
DB = {
    "SUROWCE": {
        "ZŁOTO": {"yf": "GC=F", "tv": "OANDA:XAUUSD"},
        "KAKAO": {"yf": "CC=F", "tv": "CAPITALCOM:COCOA"}, 
        "SREBRO": {"yf": "SI=F", "tv": "OANDA:XAGUSD"},
        "ROPA": {"yf": "CL=F", "tv": "TVC:USOIL"}
    },
    "KRYPTO (Live)": {
        "BITCOIN": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},
        "ETHEREUM": {"yf": "ETH-USD", "tv": "BINANCE:ETHUSDT"}
    }
}

def get_logic(symbol):
    try:
        # Pobieramy dane 1-minutowe dla większej szybkości (tylko dla krypto/forex)
        period = "1d"
        interval = "1m" if "-" in symbol else "15m" 
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if data.empty: return "Czekam...", 0.0, "#444"
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        ema9 = data['Close'].ewm(span=9).mean().iloc[-1]
        ema21 = data['Close'].ewm(span=21).mean().iloc[-1]
        price = data['Close'].iloc[-1]
        
        return ("KUPNO", price, "#26a69a") if ema9 > ema21 else ("SPRZEDAŻ", price, "#ef5350")
    except:
        return "Błąd", 0.0, "#444"

def main():
    # Przywrócone Menu
    m1, m2, m3 = st.columns(3)
    with m1: rynek = st.selectbox("Rynek", list(DB.keys()))
    with m2: inst = st.selectbox("Instrument", list(DB[rynek].keys()))
    with m3: itv = st.selectbox("Interwał", ["1", "5", "15", "60", "D"], index=1)

    status, price, color = get_logic(DB[rynek][inst]["yf"])
    
    # Wyświetlanie sygnału
    st.markdown(f"""
    <div class="signal-box">
        <div><span style="color:#aaa;">Cena:</span><br><b style="font-size:24px; color:white;">{price:,.2f}</b></div>
        <div style="background:{color}; color:white; padding:10px 40px; border-radius:5px; font-weight:bold; font-size:22px;">{status}</div>
        <div style="text-align:right;"><span style="color:#aaa;">Odświeżono:</span><br><b style="color:white;">{datetime.now().strftime("%H:%M:%S")}</b></div>
    </div>
    """, unsafe_allow_html=True)

    # Widget TradingView z naniesionymi wskaźnikami
    tv_code = f"""
    <div id="tv_chart" style="height: 65vh;"></div>
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
      "studies": ["EMA@tv-basicstudies", "EMA@tv-basicstudies", "RSI@tv-basicstudies"],
      "container_id": "tv_chart"
    }});
    </script>
    """
    components.html(tv_code, height=600)

if __name__ == "__main__":
    main()
