import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja i odświeżanie (co 60s)
st.set_page_config(layout="wide", page_title="XTB Clone V18")
st_autorefresh(interval=60 * 1000, key="data_refresh")

st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

# ROZBUDOWANA BAZA INSTRUMENTÓW (XTB Style)
DB = {
    "SUROWCE": {
        "ZŁOTO": {"yf": "GC=F", "tv": "TVC:GOLD"},
        "SREBRO": {"yf": "SI=F", "tv": "TVC:SILVER"},
        "KAKAO": {"yf": "CC=F", "tv": "TVC:COCOA"}, # Najbardziej stabilny symbol
        "ROPA WTI": {"yf": "CL=F", "tv": "TVC:USOIL"},
        "NATGAS": {"yf": "NG=F", "tv": "TVC:NATGAS"},
        "MIEDŹ": {"yf": "HG=F", "tv": "COMEX:HG1!"}
    },
    "INDEKSY": {
        "DAX (DE30)": {"yf": "^GDAXI", "tv": "GLOBALPRIME:GER30"},
        "US500 (SP500)": {"yf": "^GSPC", "tv": "VANTAGE:SP500"},
        "US100 (NASDAQ)": {"yf": "^IXIC", "tv": "VANTAGE:NAS100"},
        "WIG20": {"yf": "^WIG20", "tv": "GPW:WIG20"}
    },
    "KRYPTO": {
        "BITCOIN": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},
        "ETHEREUM": {"yf": "ETH-USD", "tv": "BINANCE:ETHUSDT"},
        "SOLANA": {"yf": "SOL-USD", "tv": "BINANCE:SOLUSDT"}
    },
    "FOREX": {
        "EURUSD": {"yf": "EURUSD=X", "tv": "FX_IDC:EURUSD"},
        "USDPLN": {"yf": "USDPLN=X", "tv": "FX_IDC:USDPLN"},
        "EURPLN": {"yf": "EURPLN=X", "tv": "FX_IDC:EURPLN"}
    }
}

def get_signal_and_price(symbol):
    try:
        data = yf.download(symbol, period="5d", interval="15m", progress=False)
        if data.empty: return "Brak", 0.0, 0.0, "00:00", "#444"
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        # Wskaźniki
        data['EMA9'] = data['Close'].ewm(span=9, adjust=False).mean()
        data['EMA21'] = data['Close'].ewm(span=21, adjust=False).mean()
        
        last = data.iloc[-1]
        price = last['Close']
        time_str = datetime.now().strftime("%H:%M:%S")
        
        # Logika
        if last['EMA9'] > last['EMA21']:
            return "KUPNO", price, time_str, "#26a69a"
        else:
            return "SPRZEDAŻ", price, time_str, "#ef5350"
    except:
        return "BŁĄD", 0.0, "00:00", "#444"

def main():
    # MENU
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: rynek = st.selectbox("Rynek", list(DB.keys()))
    with c2: inst = st.selectbox("Instrument", list(DB[rynek].keys()))
    with c3: itv = st.selectbox("Interwał", ["1", "5", "15", "60", "D"], index=2)

    # DANE
    status, price, update_time, color = get_signal_and_price(DB[rynek][inst]["yf"])

    # PASEK STATUSU (XTB Style)
    st.markdown(f"""
    <div style="background:#131722; padding:15px; border-bottom:1px solid #333; color:white; font-family:sans-serif;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <b style="font-size:20px; color:#FFB400;">{price:,.2f}</b> 
                <span style="font-size:12px; color:#aaa; margin-left:10px;">Aktualizacja: {update_time}</span>
            </div>
            <div style="background:{color}; padding:6px 20px; border-radius:4px; font-weight:bold; letter-spacing:1px;">
                {status}
            </div>
        </div>
        <div style="font-size:11px; color:#666; margin-top:5px;">Dane sygnału opóźnione o ok. 15 min (Yahoo Finance)</div>
    </div>
    """, unsafe_allow_html=True)

    # WIDGET TRADINGVIEW
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
      "studies": ["EMA@tv-basicstudies", "EMA@tv-basicstudies", "RSI@tv-basicstudies"],
      "container_id": "tv_chart"
    }});
    </script>
    """
    components.html(tv_code, height=700)

if __name__ == "__main__":
    main()
