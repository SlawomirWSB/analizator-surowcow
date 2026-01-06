import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="XTB PRO V27")
st_autorefresh(interval=60 * 1000, key="data_refresh")

st.markdown("<style>.block-container { padding: 0rem !important; } header { visibility: hidden; }</style>", unsafe_allow_html=True)

# 2. Pełna Baza Instrumentów XTB
DB = {
    "SUROWCE": {
        "ZŁOTO (GOLD)": "TVC:GOLD",
        "KAKAO (COCOA)": "SAXO:COCOA.CMD", # Nowa próba symbolu
        "GAZ NAT. (NATGAS)": "TVC:NATGAS",
        "ROPA (OIL.WTI)": "TVC:USOIL",
        "SREBRO (SILVER)": "TVC:SILVER",
        "MIEDŹ (COPPER)": "CAPITALCOM:COPPER",
        "KAWA (COFFEE)": "TVC:COFFEE"
    },
    "INDEKSY": {
        "DAX (DE30)": "GLOBALPRIME:GER30",
        "NASDAQ (US100)": "NASDAQ:IXIC",
        "S&P500 (US500)": "VANTAGE:SP500",
        "US30 (DOW)": "TVC:DJI",
        "WIG20": "GPW:WIG20"
    },
    "FOREX": {
        "EURUSD": "FX:EURUSD",
        "USDPLN": "OANDA:USDPLN",
        "EURPLN": "OANDA:EURPLN",
        "GBPUSD": "FX:GBPUSD"
    },
    "KRYPTO": {
        "BITCOIN": "BINANCE:BTCUSDT",
        "ETHEREUM": "BINANCE:ETHUSDT",
        "SOLANA": "BINANCE:SOLUSDT"
    }
}

def main():
    # 3. Górne Menu
    c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 1])
    with c1: rynek = st.selectbox("Rynek:", list(DB.keys()))
    with c2: inst = st.selectbox("Instrument:", list(DB[rynek].keys()))
    with c3: itv = st.selectbox("Interwał:", ["1", "5", "15", "60", "D"], index=1)
    with c4: show_analysis = st.checkbox("Analiza", value=True)
    with c5: enable_audio = st.checkbox("Dźwięk", value=False)

    symbol = DB[rynek][inst]

    # 4. Widget Analizy Technicznej (Teraz poprawnie powiązany z symbolem)
    if show_analysis:
        tech_code = f"""
        <div class="tradingview-widget-container" style="display: flex; justify-content: center; background: #131722; padding: 10px; border-radius: 10px;">
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
          {{
          "interval": "{itv}m" if "{itv}".isdigit() else "1D",
          "width": 380,
          "height": 340,
          "isTransparent": true,
          "symbol": "{symbol}",
          "showIntervalTabs": true,
          "displayMode": "single",
          "locale": "pl",
          "colorTheme": "dark"
        }}
          </script>
        </div>
        """
        components.html(tech_code, height=350)

    # 5. Funkcja Audio (Beep przy Strong Buy/Sell)
    if enable_audio:
        st.info("🔔 Powiadomienia dźwiękowe aktywne dla sygnałów 'Strong'.")
        audio_js = """
        <script>
        function playSignal() {
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var osc = ctx.createOscillator();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(1000, ctx.currentTime);
            osc.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.3);
        }
        setInterval(() => {
            const badge = document.body.innerText.toUpperCase();
            if (badge.includes('STRONG')) { playSignal(); }
        }, 30000);
        </script>
        """
        components.html(audio_js, height=0)

    # 6. Główny Wykres
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
