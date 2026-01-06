import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="XTB Terminal V26 - Audio")
st_autorefresh(interval=60 * 1000, key="data_refresh")

st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

# 2. Rozszerzona Baza Instrumentów (XTB)
DB = {
    "SUROWCE": {
        "ZŁOTO (GOLD)": "OANDA:XAUUSD",
        "KAKAO (COCOA)": "TVC:COCOA",
        "GAZ NAT. (NATGAS)": "TVC:NATGAS",
        "ROPA (OIL.WTI)": "TVC:USOIL",
        "SREBRO (SILVER)": "TVC:SILVER"
    },
    "INDEKSY": {
        "DAX (DE30)": "GLOBALPRIME:GER30",
        "NASDAQ (US100)": "NASDAQ:IXIC",
        "S&P500 (US500)": "VANTAGE:SP500"
    },
    "WALUTY (FOREX)": {
        "USDPLN": "OANDA:USDPLN",
        "EURUSD": "FX:EURUSD"
    }
}

def main():
    # 3. Menu Sterowania
    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
    with col1: rynek = st.selectbox("Rynek:", list(DB.keys()))
    with col2: inst = st.selectbox("Instrument:", list(DB[rynek].keys()))
    with col3: itv = st.selectbox("Interwał:", ["1", "5", "15", "60", "D"], index=1)
    with col4: show_analysis = st.checkbox("Pokaż Analizę", value=True)
    with col5: enable_audio = st.checkbox("Sygnał dźwiękowy", value=False)

    symbol = DB[rynek][inst]

    # 4. Widget Analizy Technicznej (Zmniejszony) z funkcją Audio
    if show_analysis:
        st.markdown(f"<div style='text-align: center; color: #aaa; font-size: 11px;'>Analiza Techniczna: {inst}</div>", unsafe_allow_html=True)
        
        # Skrypt JS monitorujący zmiany statusu i odtwarzający dźwięk
        audio_script = ""
        if enable_audio:
            audio_script = """
            <script>
            // Funkcja odtwarzająca dźwięk
            function playAlert() {
                var context = new (window.AudioContext || window.webkitAudioContext)();
                var oscillator = context.createOscillator();
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(880, context.currentTime); // A5 note
                oscillator.connect(context.destination);
                oscillator.start();
                oscillator.stop(context.currentTime + 0.5);
            }

            // Monitorowanie zmian w widgecie co 30 sekund
            setInterval(function() {
                var badge = document.querySelector('.tv-technical-analysis-summary__description');
                if (badge) {
                    var text = badge.innerText.toUpperCase();
                    if (text.includes('STRONG')) {
                        playAlert();
                    }
                }
            }, 30000);
            </script>
            """

        tech_code = f"""
        <div class="tradingview-widget-container" style="display: flex; justify-content: center; flex-direction: column; align-items: center;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
          {{
          "interval": "{itv}m" if "{itv}".isdigit() else "1D",
          "width": 380,
          "height": 330,
          "isTransparent": true,
          "symbol": "{symbol}",
          "showIntervalTabs": false,
          "displayMode": "single",
          "locale": "pl",
          "colorTheme": "dark"
        }}
          </script>
          {audio_script}
        </div>
        """
        components.html(tech_code, height=340)

    # 5. Widget Wykresu (Główny)
    st.markdown(f"<div style='padding-left: 10px; color: #aaa; font-size: 11px;'>Wykres {inst} (Live)</div>", unsafe_allow_html=True)
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
      "studies": ["EMA@tv-basicstudies", "EMA@tv-basicstudies", "RSI@tv-basicstudies"],
      "container_id": "tv_chart_main"
    }});
    </script>
    """
    components.html(chart_code, height=620)

if __name__ == "__main__":
    main()
