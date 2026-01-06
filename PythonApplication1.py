import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja strony
st.set_page_config(layout="wide", page_title="XTB PRO V29 - EMA Auto")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# Stylizacja interfejsu
st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

# 2. Baza Instrumentów (Z działającym Kakao Pepperstone)
DB = {
    "SUROWCE": {
        "KAKAO (COCOA)": "PEPPERSTONE:COCOA",
        "ZŁOTO (GOLD)": "OANDA:XAUUSD",
        "GAZ NAT. (NATGAS)": "TVC:NATGAS",
        "ROPA (OIL.WTI)": "TVC:USOIL",
        "SREBRO (SILVER)": "TVC:SILVER"
    },
    "INDEKSY": {
        "DAX (DE30)": "GLOBALPRIME:GER30",
        "NASDAQ (US100)": "NASDAQ:IXIC",
        "S&P500 (US500)": "VANTAGE:SP500",
        "US30 (DOW)": "TVC:DJI"
    },
    "FOREX": {
        "EURUSD": "FX:EURUSD",
        "USDPLN": "OANDA:USDPLN",
        "EURPLN": "OANDA:EURPLN"
    }
}

def main():
    # 3. Panel Sterowania
    c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 1])
    with c1: rynek = st.selectbox("Rynek:", list(DB.keys()))
    with c2: inst = st.selectbox("Instrument:", list(DB[rynek].keys()))
    with c3: itv = st.selectbox("Interwał:", ["1", "5", "15", "60", "D"], index=1)
    with c4: show_analysis = st.checkbox("Analiza", value=True)
    with c5: enable_audio = st.checkbox("Dźwięk", value=False)

    symbol = DB[rynek][inst]

    # 4. Mniejszy Widget Analizy Technicznej (Dynamiczny)
    if show_analysis:
        tech_code = f"""
        <div style="display: flex; justify-content: center; background: #131722; padding: 10px; border-radius: 8px;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
          {{
          "interval": "{itv}m" if "{itv}".isdigit() else "1D",
          "width": 380,
          "height": 340,
          "isTransparent": true,
          "symbol": "{symbol}",
          "showIntervalTabs": false,
          "displayMode": "single",
          "locale": "pl",
          "colorTheme": "dark"
        }}
          </script>
        </div>
        """
        components.html(tech_code, height=350)

    # 5. System Audio i Test (Aktywacja po kliknięciu przycisku)
    if enable_audio:
        if st.button("🔊 AKTYWUJ/TESTUJ DŹWIĘK"):
            test_js = "<script>var c=new AudioContext();var o=c.createOscillator();o.connect(c.destination);o.start();o.stop(c.currentTime+0.1);</script>"
            components.html(test_js, height=0)
        
        audio_js = """
        <script>
        setInterval(() => {
            if (document.body.innerText.toUpperCase().includes('STRONG') || document.body.innerText.toUpperCase().includes('MOCNE')) {
                var c=new AudioContext();var o=c.createOscillator();o.connect(c.destination);o.start();o.stop(c.currentTime+0.5);
            }
        }, 30000);
        </script>
        """
        components.html(audio_js, height=0)

    # 6. Wykres z Automatycznymi Liniami EMA 9 i 21
    st.markdown(f"<div style='padding-left:15px; color:#666; font-size:12px;'>Wykres {inst} + EMA 9/21 + RSI</div>", unsafe_allow_html=True)
    
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
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "container_id": "tv_chart_main",
      "studies": [
        "EMA@tv-basicstudies",
        "EMA@tv-basicstudies",
        "RSI@tv-basicstudies"
      ]
    }});
    </script>
    """
    # Uwaga: Po załadowaniu wykresu, kliknij w ustawienia (koło zębate) 
    # jednej z EMA na wykresie, aby zmienić jej 'Długość' na 21.
    components.html(chart_code, height=620)

if __name__ == "__main__":
    main()
