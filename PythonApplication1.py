import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja mobilna
st.set_page_config(layout="wide", page_title="PRO Trader V7")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Pełny minimalizm XTB
st.markdown("""
    <style>
    .block-container { padding: 0rem !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    .xtb-header {
        background: #000; padding: 12px 15px;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #1e1e1e;
    }
    .inst-title { color: #f39c12; font-size: 18px; font-weight: bold; }
    .price-val { color: #fff; font-size: 18px; font-family: monospace; }
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
    # Sterowanie na dole
    with st.expander("⚙️ KONFIGURACJA"):
        c1, c2, c3 = st.columns(3)
        kat = c1.selectbox("Rynek", list(DB.keys()))
        inst = c2.selectbox("Instrument", list(DB[kat].keys()))
        itv = c3.selectbox("Interwał", ["1m", "5m", "15m", "1h", "1d"], index=2)
        syg = st.toggle("Sygnały", value=True)

    symbol = DB[kat][inst]

    try:
        # Pobieramy 100 świec, by mieć historię do przesuwania
        df = yf.download(symbol, period="5d", interval=itv, progress=False)
        if df.empty: return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['E9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['E21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['R'] = get_rsi(df['Close'])
        
        v = df.tail(100).copy()
        curr = v.iloc[-1]
        
        # --- PASEK GÓRNY ---
        st.markdown(f"""
            <div class="xtb-header">
                <div class="inst-title">{inst.upper()}</div>
                <div class="price-val">{curr['Close']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        # --- WYKRES ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.8, 0.2])
        
        fig.add_trace(go.Candlestick(
            x=v.index, open=v['Open'], high=v['High'], low=v['Low'], close=v['Close'],
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=v.index, y=v['E9'], line=dict(color='#FF9800', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E21'], line=dict(color='#9C27B0', width=1)), row=1, col=1)

        if syg:
            v['b'] = (v['E9'] > v['E21']) & (v['R'] < 65)
            v['s'] = (v['E9'] < v['E21']) & (v['R'] > 35)
            fig.add_trace(go.Scatter(x=v[v['b']].index, y=v[v['b']]['Low']*0.999, mode='markers', 
                                   marker=dict(symbol='triangle-up', size=10, color='lime')), row=1, col=1)
            fig.add_trace(go.Scatter(x=v[v['s']].index, y=v[v['s']]['High']*1.001, mode='markers', 
                                   marker=dict(symbol='triangle-down', size=10, color='red')), row=1, col=1)

        fig.add_trace(go.Scatter(x=v.index, y=v['R'], line=dict(color='#2196F3', width=1)), row=2, col=1)

        # --- KLUCZOWE USTAWIENIA CZYTELNOŚCI XTB ---
        
        # 1. Widok tylko ostatnich 30 świec (reszta dostępna po przesunięciu)
        last_idx = len(v)
        start_idx = max(0, last_idx - 30)
        
        fig.update_xaxes(
            type='category', 
            range=[start_idx, last_idx], # To ustawia przybliżenie na start
            rangeslider_visible=False,
            showgrid=False
        )
        
        fig.update_yaxes(side="right", gridcolor='#1e1e1e') # Cena po prawej

        fig.update_layout(
            height=750, margin=dict(l=0, r=0, t=0, b=0),
            template="plotly_dark", paper_bgcolor="black", plot_bgcolor="black",
            dragmode='zoom', # Przełączenie na zoom dla lepszej obsługi dotyku
            hovermode='x'
        )
        
        st.plotly_chart(fig, use_container_width=True, config={
            'scrollZoom': True, 
            'displayModeBar': False,
            'doubleClick': 'reset'
        })

    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
