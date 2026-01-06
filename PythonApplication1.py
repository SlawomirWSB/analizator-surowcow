import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja strony pod telefon
st.set_page_config(layout="wide", page_title="Trader PRO V13")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Maksymalna przestrzeń na wykres
st.markdown("""
    <style>
    .block-container { padding: 0rem !important; }
    header { visibility: hidden; }
    .status-bar {
        background: #131722; color: white; padding: 10px;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #333; font-family: sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# Baza symboli: yfinance (do sygnałów) | TradingView (do wykresu)
DB = {
    "ZŁOTO": {"yf": "GC=F", "tv": "OANDA:XAU_USD"},
    "KAKAO": {"yf": "CC=F", "tv": "CAPITALCOM:COCOA"},
    "BTC": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},
    "SREBRO": {"yf": "SI=F", "tv": "OANDA:XAG_USD"}
}

def get_logic_signal(symbol):
    try:
        # Pobieramy dane do obliczeń (sygnały)
        df = yf.download(symbol, period="2d", interval="15m", progress=False)
        if df.empty: return "BRAK DANYCH", "#444"
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        ema9 = df['Close'].ewm(span=9).mean().iloc[-1]
        ema21 = df['Close'].ewm(span=21).mean().iloc[-1]
        
        if ema9 > ema21: return "KUPNO", "#26a69a"
        return "SPRZEDAŻ", "#ef5350"
    except:
        return "ŁADOWANIE", "#444"

def main():
    # 1. Menu wyboru
    with st.expander("⚙️ ZMIEŃ INSTRUMENT"):
        inst = st.selectbox("Wybierz:", list(DB.keys()))
        itv = st.selectbox("Interwał wykresu:", ["1", "5", "15", "60", "D"], index=2)

    # 2. Obliczanie sygnału
    status, color = get_logic_signal(DB[inst]["yf"])

    # 3. Nagłówek a'la XTB
    st.markdown(f"""
        <div class="status-bar">
            <div style="font-weight:bold; color:#FFB400;">{inst}</div>
            <div style="background:{color}; padding:5px 15px; border-radius:3px; font-weight:bold; font-size:12px;">
                {status}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 4. Profesjonalny Widget TradingView (Z obsługą dotyku)
    tv_widget = f"""
    <div id="tv_chart_container" style="height: 80vh;"></div>
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
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "container_id": "tv_chart_container"
    }});
    </script>
    """
    
    components.html(tv_widget, height=750)

if __name__ == "__main__":
    main()
