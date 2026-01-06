import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="PRO Trader V9")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Czysty styl XTB
st.markdown("""
    <style>
    .block-container { padding: 0rem !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    .xtb-header {
        background: #000; padding: 10px 15px;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #333;
    }
    .inst-title { color: #f39c12; font-size: 16px; font-weight: bold; }
    .price-val { color: #fff; font-size: 16px; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

def get_rsi(prices, n=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=n).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

DB = {
    "Surowce": {"Kakao": "CC=F", "Złoto": "GC=F", "Srebro": "SI=F", "Ropa": "CL=F"},
    "Krypto": {"BTC": "BTC-USD", "ETH": "ETH-USD"},
    "Indeksy": {"DAX": "^GDAXI", "SP500": "^GSPC"}
}

def main():
    # Inicjalizacja stanu zoomu w pamięci przeglądarki
    if 'zoom_level' not in st.session_state:
        st.session_state.zoom_level = 40 # Domyślnie widzimy 40 świec

    # --- MENU STEROWANIA ---
    with st.expander("⚙️ USTAWIENIA I WYBÓR"):
        c1, c2, c3 = st.columns(3)
        kat = c1.selectbox("Rynek", list(DB.keys()))
        inst = c2.selectbox("Instrument", list(DB[kat].keys()))
        itv = c3.selectbox("Interwał", ["1m", "5m", "15m", "1h", "1d"], index=2)
        
        col_s1, col_s2, col_s3 = st.columns([1,1,1])
        with col_s1:
            show_syg = st.toggle("Włącz Sygnały (Kupno/Sprzedaż)", value=True)
        with col_s2:
            if st.button("🔍 PRZYBLIŻ (+)", use_container_width=True):
                st.session_state.zoom_level = max(15, st.session_state.zoom_level - 10)
        with col_s3:
            if st.button("🔍 ODDAL (-)", use_container_width=True):
                st.session_state.zoom_level = min(150, st.session_state.zoom_level + 10)

    symbol = DB[kat][inst]

    try:
        # Pobieranie danych (większy zapas)
        df = yf.download(symbol, period="10d", interval=itv, progress=False)
        if df.empty: return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['E9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['E21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['R'] = get_rsi(df['Close'])
        df.dropna(inplace=True)
        
        v = df.tail(200).copy() # Dane do przesuwania
        curr = v.iloc[-1]
        
        # Nagłówek
        st.markdown(f'<div class="xtb-header"><div class="inst-title">{inst.upper()} ({itv})</div><div class="price-val">{curr["Close"]:.2f}</div></div>', unsafe_allow_html=True)

        # --- WYKRES ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.8, 0.2])
        
        # Świece i EMA
        fig.add_trace(go.Candlestick(x=v.index, open=v['Open'], high=v['High'], low=v['Low'], close=v['Close'], name="Cena"), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E9'], line=dict(color='orange', width=1.2), hoverinfo='skip'), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E21'], line=dict(color='purple', width=1.2), hoverinfo='skip'), row=1, col=1)

        # Sygnały Kupna/Sprzedaży
        if show_syg:
            v['buy'] = (v['E9'] > v['E21']) & (v['R'] < 65)
            v['sell'] = (v['E9'] < v['E21']) & (v['R'] > 35)
            fig.add_trace(go.Scatter(x=v[v['buy']].index, y=v[v['buy']]['Low']*0.999, mode='markers', marker=dict(symbol='triangle-up', size=11, color='lime'), name="BUY"), row=1, col=1)
            fig.add_trace(go.Scatter(x=v[v['sell']].index, y=v[v['sell']]['High']*1.001, mode='markers', marker=dict(symbol='triangle-down', size=11, color='red'), name="SELL"), row=1, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=v.index, y=v['R'], line=dict(color='#00d4ff', width=1.5)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="rgba(255,0,0,0.3)", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="rgba(0,255,0,0.3)", row=2, col=1)

        # --- KLUCZOWE USTAWIENIA: BRAK LUK + ZOOM ---
        total_candles = len(v)
        # Ustawienie zakresu widoczności na podstawie przycisków zoom
        fig.update_xaxes(
            type='category', 
            range=[total_candles - st.session_state.zoom_level, total_candles],
            showgrid=False,
            zeroline=False
        )
        
        fig.update_yaxes(side="right", gridcolor='#1e1e1e')
        fig.update_layout(
            height=750, margin=dict(l=0, r=0, t=0, b=0),
            template="plotly_dark", paper_bgcolor="black", plot_bgcolor="black",
            dragmode='pan', xaxis_rangeslider_visible=False, showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})

    except Exception as e:
        st.error(f"Błąd aplikacji: {e}")

if __name__ == "__main__":
    main()
