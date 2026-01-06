import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

# 1. Konfiguracja pod mobile
st.set_page_config(layout="wide", page_title="PRO Trader V8")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Czysty interfejs
st.markdown("""
    <style>
    .block-container { padding: 0rem !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    .xtb-header {
        background: #000; padding: 10px 15px;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #222;
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
    # Menu schowane na dole
    with st.expander("⚙️ MENU"):
        c1, c2, c3 = st.columns(3)
        kat = c1.selectbox("Rynek", list(DB.keys()))
        inst = c2.selectbox("Instrument", list(DB[kat].keys()))
        itv = c3.selectbox("Interwał", ["1m", "5m", "15m", "1h", "1d"], index=2)

    symbol = DB[kat][inst]

    try:
        # Pobieramy szerszy zakres danych dla płynnego przesuwania
        df = yf.download(symbol, period="7d", interval=itv, progress=False)
        if df.empty: return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['E9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['E21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['R'] = get_rsi(df['Close'])
        
        # --- PASEK GÓRNY ---
        curr = df.iloc[-1]
        st.markdown(f'<div class="xtb-header"><div class="inst-title">{inst.upper()}</div><div class="price-val">{curr["Close"]:.2f}</div></div>', unsafe_allow_html=True)

        # --- WYKRES ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.8, 0.2])
        
        # Świece
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350', name="Cena"
        ), row=1, col=1)
        
        # Wskaźniki
        fig.add_trace(go.Scatter(x=df.index, y=df['E9'], line=dict(color='#FF9800', width=1), hoverinfo='skip'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['E21'], line=dict(color='#9C27B0', width=1), hoverinfo='skip'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['R'], line=dict(color='#2196F3', width=1.5)), row=2, col=1)

        # --- LOGIKA PRZESUWANIA I ZOOMU ---
        
        # Ustawienie domyślnego widoku na ostatnie 30 świec (XTB style)
        last_time = df.index[-1]
        # Obliczamy dynamiczny zakres czasu w zależności od interwału
        minutes_map = {"1m": 30, "5m": 150, "15m": 450, "1h": 1800, "1d": 30}
        delta = minutes_map.get(itv, 450)
        
        if itv == "1d":
            start_time = last_time - timedelta(days=30)
        else:
            start_time = last_time - timedelta(minutes=delta)

        # Usunięcie luk (weekendów) - kluczowe dla przesuwania
        fig.update_xaxes(
            range=[start_time, last_time],
            rangebreaks=[dict(bounds=["sat", "mon"])], # Wyłącza weekendy
            rangeslider_visible=False,
            showgrid=False,
            type='date' # Zmiana z category na date przywraca przesuwanie
        )
        
        fig.update_yaxes(side="right", gridcolor='#1e1e1e')

        fig.update_layout(
            height=750, margin=dict(l=0, r=0, t=0, b=0),
            template="plotly_dark", paper_bgcolor="black", plot_bgcolor="black",
            dragmode='pan', # 'pan' umożliwia przesuwanie palcem
            hovermode='x'
        )
        
        # Konfiguracja mobilna: scrollZoom włącza pinch-to-zoom (dwa palce)
        st.plotly_chart(fig, use_container_width=True, config={
            'scrollZoom': True, 
            'displayModeBar': False,
            'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
            'responsive': True
        })

    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
