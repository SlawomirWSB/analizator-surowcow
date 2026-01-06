import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="PRO Trader V5")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Wygląd klasy Premium
st.markdown("""
    <style>
    .block-container { padding: 0.1rem 0.3rem !important; }
    header { visibility: hidden; }
    .top-bar {
        background: #000; padding: 12px; border-radius: 0 0 8px 8px;
        border-bottom: 2px solid #f39c12; margin-bottom: 8px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .instr-name { color: #f39c12; font-size: 1.2rem; font-weight: bold; text-transform: uppercase; }
    .metrics { color: white; font-family: 'Courier New', monospace; font-size: 1rem; }
    .status-badge { padding: 4px 12px; border-radius: 5px; font-weight: 900; }
    /* Styl dla expandera */
    .p-menu { background: #111; border-radius: 5px; padding: 10px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

def get_rsi(prices, n=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=n).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Rozszerzona baza danych - KAKAO dodane
DB = {
    "Surowce": {
        "Kakao": "CC=F", 
        "Złoto": "GC=F", 
        "Srebro": "SI=F", 
        "Miedź": "HG=F", 
        "Ropa WTI": "CL=F",
        "Kawa": "KC=F"
    },
    "Krypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Indeksy": {"DAX": "^GDAXI", "SP500": "^GSPC", "NASDAQ": "^IXIC"}
}

def main():
    # --- PANEL STEROWANIA (Zmienne sterujące) ---
    with st.expander("🛠️ MENU: ZMIEŃ INSTRUMENT / INTERWAŁ", expanded=False):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            kat = st.selectbox("Rynek", list(DB.keys()))
        with c2:
            inst = st.selectbox("Instrument", list(DB[kat].keys()))
        with c3:
            itv = st.selectbox("Interwał", ["1m", "5m", "15m", "1h", "1d"], index=2)
        
        show_syg = st.toggle("Pokaż sygnały wejścia", value=True)

    symbol = DB[kat][inst]

    try:
        # Pobieranie danych (więcej dni, by umożliwić przesuwanie)
        df = yf.download(symbol, period="7d", interval=itv, progress=False)
        if df.empty:
            st.warning("Błąd pobierania danych. Spróbuj innego interwału.")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['E9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['E21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['R'] = get_rsi(df['Close'])
        df.dropna(inplace=True)

        v = df.tail(100).copy() # Więcej świec w pamięci dla płynności
        curr = v.iloc[-1]
        prev = v.iloc[-2]
        
        # Logika trendu i sygnałów
        diff = (curr['E9'] - curr['E21']) / curr['E21']
        buy = (curr['E9'] > curr['E21']) and (curr['R'] < 68) and (diff > 0.0001)
        sel = (curr['E9'] < curr['E21']) and (curr['R'] > 32) and (diff < -0.0001)

        # --- PASEK GÓRNY (Wzorowany na zdjęciu) ---
        st.markdown(f"""
            <div class="top-bar">
                <div class="instr-name">{inst} ({itv})</div>
                <div class="metrics">CENA: {curr['Close']:.2f} | RSI: {curr['R']:.1f}</div>
                <div class="status-badge" style="background:{'#28a745' if buy else '#dc3545' if sel else '#ffc107'}; color:{'white' if (buy or sel) else 'black'};">
                    {'KUPNO' if buy else 'SPRZEDAŻ' if sel else 'CZEKAJ'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- WYKRES (Interaktywny) ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8, 0.2])
        
        # Świece
        fig.add_trace(go.Candlestick(x=v.index, open=v['Open'], high=v['High'], low=v['Low'], close=v['Close'], name="Cena"), row=1, col=1)
        
        # EMA
        fig.add_trace(go.Scatter(x=v.index, y=v['E9'], line=dict(color='#ff9900', width=1.5), name="EMA 9"), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E21'], line=dict(color='#9900ff', width=1.5), name="EMA 21"), row=1, col=1)

        # Sygnały
        if show_syg:
            v['b'] = (v['E9']>v['E21']) & (v['R']<68) & ((v['E9']-v['E21'])/v['E21']>0.0001)
            v['s'] = (v['E9']<v['E21']) & (v['R']>32) & ((v['E9']-v['E21'])/v['E21']<-0.0001)
            fig.add_trace(go.Scatter(x=v[v['b']].index, y=v[v['b']]['Low']*0.999, mode='markers', marker=dict(symbol='triangle-up', size=12, color='#00ff00'), name="BUY"), row=1, col=1)
            fig.add_trace(go.Scatter(x=v[v['s']].index, y=v[v['s']]['High']*1.001, mode='markers', marker=dict(symbol='triangle-down', size=12, color='#ff0000'), name="SELL"), row=1, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=v.index, y=v['R'], line=dict(color='#00d4ff', width=2)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

        # --- FUNKCJA PRZESUWANIA I USUNIĘCIE LUK ---
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]), # ukryj weekendy
                dict(values=["2024-12-25", "2025-01-01"]) # ukryj święta (opcjonalnie)
            ]
        )
        
        fig.update_layout(
            height=850, 
            margin=dict(l=0, r=0, t=0, b=0), 
            template="plotly_dark", 
            xaxis_rangeslider_visible=False, 
            showlegend=False,
            dragmode='pan' # Domyślne przesuwanie wykresu palcem/myszką
        )
        
        # Konfiguracja Streamlit dla obsługi dotyku
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})

    except Exception as e:
        st.error(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    main()
