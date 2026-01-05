import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="PRO Mobile Trader")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Nowoczesny wygląd i brak Sidebaru
st.markdown("""
    <style>
    .block-container { padding: 0.2rem 0.4rem !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    .top-bar {
        background: #000; padding: 10px; border-radius: 5px;
        border-bottom: 2px solid #f39c12; margin-bottom: 5px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .instr-title { color: #f39c12; font-size: 1.1rem; font-weight: bold; }
    .data-label { color: white; font-size: 0.9rem; font-family: monospace; }
    .status-box { padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

def get_rsi(prices, n=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=n).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

DB = {
    "Metale": {"Złoto": "GC=F", "Srebro": "SI=F", "Miedź": "HG=F"},
    "Krypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Indeksy": {"DAX": "^GDAXI", "SP500": "^GSPC"}
}

def main():
    # --- PANEL STEROWANIA (ROZWIJANY) ---
    with st.expander("⚙️ USTAWNIENIA I WYBÓR INSTRUMENTU", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            kat = st.selectbox("Rynek", list(DB.keys()))
            inst = st.selectbox("Instrument", list(DB[kat].keys()))
        with c2:
            itv = st.selectbox("Interwał", ["1m", "5m", "15m", "1h", "1d"], index=2)
            syg = st.checkbox("Pokaż sygnały (trójkąty)", value=True)

    symbol = DB[kat][inst]

    try:
        df = yf.download(symbol, period="5d", interval=itv, progress=False)
        if df.empty: return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['E9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['E21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['R'] = get_rsi(df['Close'])
        df.dropna(inplace=True)

        v = df.tail(80).copy()
        curr = v.iloc[-1]
        prev = v.iloc[-2]
        
        # Logika
        diff = (curr['E9'] - curr['E21']) / curr['E21']
        buy = (curr['E9'] > curr['E21']) and (curr['R'] < 65) and (abs(diff) > 0.00015)
        sel = (curr['E9'] < curr['E21']) and (curr['R'] > 35) and (abs(diff) > 0.00015)

        # --- PASEK GÓRNY ---
        st.markdown(f"""
            <div class="top-bar">
                <div class="instr-title">{inst.upper()} ({itv})</div>
                <div class="data-label">C: {curr['Close']:.2f} | R: {curr['R']:.0f}</div>
                <div class="status-box" style="background:{'#28a745' if buy else '#dc3545' if sel else '#333'}; color:white;">
                    {'KUPNO' if buy else 'SPRZEDAŻ' if sel else 'CZEKAJ'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- WYKRES ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.85, 0.15])
        
        # Świece i EMA
        fig.add_trace(go.Candlestick(x=v.index, open=v['Open'], high=v['High'], low=v['Low'], close=v['Close']), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E9'], line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E21'], line=dict(color='purple', width=1)), row=1, col=1)

        # Sygnały
        if syg:
            v['b'] = (v['E9']>v['E21']) & (v['R']<65) & ((v['E9']-v['E21'])/v['E21']>0.00015)
            v['s'] = (v['E9']<v['E21']) & (v['R']>35) & ((v['E9']-v['E21'])/v['E21']<-0.00015)
            fig.add_trace(go.Scatter(x=v[v['b']].index, y=v[v['b']]['Low']*0.9997, mode='markers', marker=dict(symbol='triangle-up', size=12, color='lime')), row=1, col=1)
            fig.add_trace(go.Scatter(x=v[v['s']].index, y=v[v['s']]['High']*1.0003, mode='markers', marker=dict(symbol='triangle-down', size=12, color='red')), row=1, col=1)

        fig.add_trace(go.Scatter(x=v.index, y=v['R'], line=dict(color='#00d4ff', width=1.5)), row=2, col=1)

        # Ustawienia techniczne wykresu
        fig.update_xaxes(type='category', nticks=8) # Naprawia "pływanie" wykresu
        fig.update_layout(height=800, margin=dict(l=0, r=0, t=5, b=0), template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
