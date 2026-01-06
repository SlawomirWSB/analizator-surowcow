import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="XTB FIX V32")
st_autorefresh(interval=60 * 1000, key="data_refresh")

st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

DB = {
    "SUROWCE": {
        "ZŁOTO (GOLD)": "OANDA:XAUUSD",
        "KAKAO (COCOA)": "PEPPERSTONE:COCOA"
    },
    "INDEKSY": {
        "NASDAQ (US100)": "NASDAQ:IXIC"
    }
}

def main():
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    with c1: rynek = st.selectbox("Rynek:", list(DB.keys()))
    with c2: inst = st.selectbox("Instrument:", list(DB[rynek].keys()))
    with c3: itv = st.selectbox("Interwał:", ["1", "5", "15", "60", "D"], index=1)
    with c4: enable_audio = st.checkbox("Dźwięk", value=True)

    symbol = DB[rynek][inst]

    # Analiza Techniczna (Zegar)
    tech_code = f"""
    <div style="display: flex; justify-content: center; background: #131722; padding: 10px;">
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
      {{
      "interval": "{itv}m" if "{itv}".isdigit() else "1D",
      "width": 420, "height": 380,
      "isTransparent": true, "symbol": "{symbol}",
      "showIntervalTabs": false, "displayMode": "single",
      "locale": "pl", "colorTheme": "dark"
    }}
      </script>
    </div>
    """
    components.html(tech_code, height=390)

    # WYKRES - NOWA KONFIGURACJA WSKAŹNIKÓW
    chart_code = f"""
    <div id="tv_chart_container" style="height: 600px;"></div>
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
      "enable_publishing": false,
      "withdateranges": true,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "container_id": "tv_chart_container",
      "studies": [
        "RSI@tv-basicstudies",
        "MASimple@tv-basicstudies",
        "MASimple@tv-basicstudies"
      ],
      "studies_overrides": {{
        "ma.precision": 2,
        "ma.length": 9
      }}
    }});
    </script>
    """
    components.html(chart_code, height=620)

if __name__ == "__main__":
    main()
