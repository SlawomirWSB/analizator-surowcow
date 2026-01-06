import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="Sygnały LIVE V24")
st_autorefresh(interval=60 * 1000, key="data_refresh")

st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

# Baza danych (Najbardziej stabilne symbole dla widgetów)
DB = {
    "SUROWCE": {
        "ZŁOTO": "OANDA:XAUUSD",
        "KAKAO": "CAPITALCOM:COCOA", 
        "SREBRO": "OANDA:XAGUSD",
        "ROPA": "TVC:USOIL"
    },
    "KRYPTO": {
        "BITCOIN": "BINANCE:BTCUSDT",
        "ETHEREUM": "BINANCE:ETHUSDT"
    }
}

def main():
    # Menu wyboru
    c1, c2, c3 = st.columns(3)
    with c1: rynek = st.selectbox("Rynek", list(DB.keys()))
    with c2: inst = st.selectbox("Instrument", list(DB[rynek].keys()))
    with c3: itv = st.selectbox("Interwał", ["1", "5", "15", "60", "D"], index=1)

    symbol = DB[rynek][inst]

    # --- WIDGET 1: PANEL ANALIZY TECHNICZNEJ (Sygnały Kupno/Sprzedaż) ---
    # Ten widget pokazuje zegar z werdyktem: Strong Buy / Sell
    st.markdown("### ⚡ Analiza Techniczna LIVE (Bez opóźnień)")
    
    tech_analysis_code = f"""
    <div class="tradingview-widget-container" style="margin: auto;">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
      {{
      "interval": "{itv}m" if "{itv}".isdigit() else "1D",
      "width": "100%",
      "isTransparent": false,
      "height": 350,
      "symbol": "{symbol}",
      "showIntervalTabs": true,
      "displayMode": "single",
      "locale": "pl",
      "colorTheme": "dark"
    }}
      </script>
    </div>
    """
    components.html(tech_analysis_code, height=360)

    # --- WIDGET 2: WYKRES INTERAKTYWNY ---
    st.markdown("### 📈 Wykres Podglądowy")
    chart_code = f"""
    <div id="tv_chart_main" style="height: 500px;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{
      "autosize": true,
      "symbol": "{symbol}",
      "interval": "{itv}",
      "timezone": "Europe/Warsaw",
      "theme": "dark",
      "style": "1",
      "locale": "pl",
      "studies": ["EMA@tv-basicstudies", "RSI@tv-basicstudies"],
      "container_id": "tv_chart_main"
    }});
    </script>
    """
    components.html(chart_code, height=520)

if __name__ == "__main__":
    main()
