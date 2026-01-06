import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja i Autoodświeżanie
st.set_page_config(layout="wide", page_title="XTB FIX V31")
st_autorefresh(interval=60 * 1000, key="data_refresh")

st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

# 2. Baza Instrumentów
DB = {
    "SUROWCE": {
        "ZŁOTO (GOLD)": "OANDA:XAUUSD",
        "KAKAO (COCOA)": "PEPPERSTONE:COCOA",
        "GAZ NAT. (NATGAS)": "TVC:NATGAS"
    },
    "INDEKSY": {
        "NASDAQ (US100)": "NASDAQ:IXIC",
        "DAX (DE30)": "GLOBALPRIME:GER30"
    }
}

def main():
    # 3. Górny Panel Wyboru
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    with c1: rynek = st.selectbox("Rynek:", list(DB.keys()))
    with c2: inst = st.selectbox("Instrument:", list(DB[rynek].keys()))
    with c3: itv = st.selectbox("Interwał:", ["1", "5", "15", "60", "D"], index=1)
    with c4: enable_audio = st.checkbox("Dźwięk", value=True)

    symbol = DB[rynek][inst]

    # 4. Widget Analizy Technicznej (Teraz poprawnie powiązany)
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

    # 5. NAPRAWIONY WYKRES: RSI + EMA 9 (Niebieska) + EMA 21 (Pomarańczowa)
    chart_code = f"""
    <div id="tv_chart_main" style="height: 600px;"></div>
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
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "container_id": "tv_chart_main",
      "studies": [
        "RSI@tv-basicstudies",
        "EMA@tv-basicstudies",
        "EMA@tv-basicstudies"
      ],
      "overrides": {{
        "mainSeriesProperties.style": 1
      }}
    }});
    </script>
    """
    components.html(chart_code, height=620)

    # 6. Obsługa Audio
    if enable_audio:
        audio_js = """
        <script>
        setInterval(() => {
            const text = document.body.innerText.toUpperCase();
            if (text.includes('STRONG') || text.includes('MOCNE')) {
                const ctx = new AudioContext();
                const osc = ctx.createOscillator();
                osc.connect(ctx.destination);
                osc.start(); osc.stop(ctx.currentTime + 0.3);
            }
        }, 30000);
        </script>
        """
        components.html(audio_js, height=0)

if __name__ == "__main__":
    main()
