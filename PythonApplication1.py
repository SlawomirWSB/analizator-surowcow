import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja i odświeżanie
st.set_page_config(layout="wide", page_title="PRO Trader V15")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS dla lepszego wyglądu mobilnego
st.markdown("""
<style>
    .block-container { padding: 0rem !important; }
    header { visibility: hidden; }
    .stSelectbox { margin-bottom: -15px; }
</style>
""", unsafe_allow_html=True)

# ROZBUDOWANA BAZA INSTRUMENTÓW
DB = {
    "SUROWCE": {
        "ZŁOTO": {"yf": "GC=F", "tv": "TVC:GOLD"},
        "SREBRO": {"yf": "SI=F", "tv": "TVC:SILVER"},
        "KAKAO": {"yf": "CC=F", "tv": "PEPPERSTONE:COCOA"}, # Poprawiony symbol
        "ROPA WTI": {"yf": "CL=F", "tv": "TVC:USOIL"},
        "GAZ NAT.": {"yf": "NG=F", "tv": "TVC:NATGAS"}
    },
    "KRYPTOWALUTY": {
        "BTC (Bitcoin)": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},
        "ETH (Ethereum)": {"yf": "ETH-USD", "tv": "BINANCE:ETHUSDT"},
        "SOL (Solana)": {"yf": "SOL-USD", "tv": "BINANCE:SOLUSDT"}
    },
    "INDEKSY": {
        "DAX (Niemcy)": {"yf": "^GDAXI", "tv": "GLOBALPRIME:GER30"},
        "SP500 (USA)": {"yf": "^GSPC", "tv": "VANTAGE:SP500"},
        "NASDAQ": {"yf": "^IXIC", "tv": "VANTAGE:NAS100"}
    },
    "WALUTY (Forex)": {
        "EUR/USD": {"yf": "EURUSD=X", "tv": "FX_IDC:EURUSD"},
        "USD/PLN": {"yf": "USDPLN=X", "tv": "FX_IDC:USDPLN"}
    }
}

def get_signal(symbol):
    try:
        data = yf.download(symbol, period="2d", interval="15m", progress=False)
        if data.empty: return "ŁADOWANIE...", "#444"
        if isinstance(data.columns, pd.MultiIndex): 
            data.columns = data.columns.get_level_values(0)
        e9 = data['Close'].ewm(span=9).mean().iloc[-1]
        e21 = data['Close'].ewm(span=21).mean().iloc[-1]
        return ("KUPNO", "#26a69a") if e9 > e21 else ("SPRZEDAŻ", "#ef5350")
    except:
        return "CZEKAJ...", "#444"

def main():
    # MENU WYBORU (Dwa stopnie: Rynek -> Instrument)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        rynek = st.selectbox("Rynek:", list(DB.keys()))
    with col2:
        inst_list = list(DB[rynek].keys())
        inst = st.selectbox("Instrument:", inst_list)
    with col3:
        itv = st.selectbox("Interwał:", ["1", "5", "15", "60", "D", "W"], index=2)

    # Dane i Sygnał
    selected = DB[rynek][inst]
    status, color = get_signal(selected["yf"])

    # Pasek statusu
    st.markdown(f"""
    <div style="background:#131722; padding:10px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333;">
        <b style="color:#FFB400; font-size:16px;">{inst.upper()}</b>
        <div style="background:{color}; color:white; padding:4px 15px; border-radius:3px; font-weight:bold; font-size:12px;">
            {status}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Widget TradingView
    tv_code = f"""
    <div id="tradingview_widget" style="height: 80vh;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{
      "autosize": true,
      "symbol": "{selected['tv']}",
      "interval": "{itv}",
      "timezone": "Europe/Warsaw",
      "theme": "dark",
      "style": "1",
      "locale": "pl",
      "enable_publishing": false,
      "allow_symbol_change": true,
      "container_id": "tradingview_widget"
    }});
    </script>
    """
    components.html(tv_code, height=750)

if __name__ == "__main__":
    main()
