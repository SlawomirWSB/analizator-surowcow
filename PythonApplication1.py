import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="PRO Trader V21")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# Stylizacja paska sygnału i menu
st.markdown("""
<style>
    .block-container { padding: 0rem !important; }
    header { visibility: hidden; }
    .main-signal-card {
        background: #1e222d;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        margin: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .stSelectbox { margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# Baza danych - Kakao ustawione na dostawcę ICEUS (najbardziej wiarygodny dla widgetu)
DB = {
    "SUROWCE": {
        "ZŁOTO": {"yf": "GC=F", "tv": "TVC:GOLD"},
        "KAKAO": {"yf": "CC=F", "tv": "ICEUS:CC1!"}, 
        "SREBRO": {"yf": "SI=F", "tv": "TVC:SILVER"},
        "ROPA": {"yf": "CL=F", "tv": "TVC:USOIL"}
    },
    "KRYPTO": {
        "BITCOIN": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},
        "ETHEREUM": {"yf": "ETH-USD", "tv": "BINANCE:ETHUSDT"}
    },
    "INDEKSY/FOREX": {
        "DAX": {"yf": "^GDAXI", "tv": "GLOBALPRIME:GER30"},
        "SP500": {"yf": "^GSPC", "tv": "VANTAGE:SP500"},
        "EURUSD": {"yf": "EURUSD=X", "tv": "FX:EURUSD"}
    }
}

def get_logic(symbol):
    try:
        data = yf.download(symbol, period="5d", interval="15m", progress=False)
        if data.empty: return "Brak Danych", 0.0, "#444"
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        data['EMA9'] = data['Close'].ewm(span=9, adjust=False).mean()
        data['EMA21'] = data['Close'].ewm(span=21, adjust=False).mean()
        
        last = data.iloc[-1]
        price = last['Close']
        
        if last['EMA9'] > last['EMA21']:
            return "KUPNO", price, "#26a69a"
        else:
            return "SPRZEDAŻ", price, "#ef5350"
    except:
        return "Błąd", 0.0, "#444"

def main():
    # 1. Menu Wyboru na środku
    m1, m2, m3 = st.columns([1, 1, 1])
    with m1: rynek = st.selectbox("Rynek", list(DB.keys()))
    with m2: inst = st.selectbox("Instrument", list(DB[rynek].keys()))
    with m3: itv = st.selectbox("Interwał", ["1", "5", "15", "60", "D"], index=2)

    # 2. Obliczenia
    status, price, s_color = get_logic(DB[rynek][inst]["yf"])
    update_time = datetime.now().strftime("%H:%M:%S")

    # 3. Karta Sygnału
    st.markdown(f"""
    <div class="main-signal-card">
        <div>
            <span style="color:#aaa; font-size:12px;">Cena ({inst}):</span><br>
            <b style="font-size:24px; color:white;">{price:,.2f}</b>
        </div>
        <div style="text-align:center;">
            <div style="background:{s_color}; color:white; padding:8px 30px; border-radius:5px; font-weight:bold; font-size:18px; box-shadow: 0 4px 12px {s_color}66;">
                {status}
            </div>
            <div style="color:#666; font-size:10px; margin-top:4px;">Sygnał EMA 9/21 (Opóźnienie 15m+)</div>
        </div>
        <div style="text-align:right;">
            <span style="color:#aaa; font-size:12px;">Aktualizacja:</span><br>
            <b style="color:white;">{update_time}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Widget TradingView (z automatycznym RSI i EMA)
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
    components.html(tv_code, height=600)

if __name__ == "__main__":
    main()
