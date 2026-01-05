import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# 1. Konfiguracja i Auto-odświeżanie
st.set_page_config(layout="wide", page_title="PRO Trader Mobile")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Ekstremalna optymalizacja pod telefon w pionie
st.markdown("""
    <style>
    /* Ukrycie zbędnych marginesów Streamlit */
    .block-container { padding: 0.2rem 0.4rem !important; }
    header { visibility: hidden; }
    
    /* Wymuszenie jednego wiersza dla metryk */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
        margin-bottom: -15px !important;
    }
    
    /* Mini-metryki */
    [data-testid="stMetric"] { 
        background-color: #1a1c24; 
        border-radius: 4px; 
        padding: 1px 5px !important; 
        border: 1px solid #3e414f;
    }
    [data-testid="stMetricValue"] { color: white !important; font-size: 0.8rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #8a8d97 !important; font-size: 0.5rem !important; margin-bottom: -12px; }
    
    /* Mały status alertu */
    .stAlert { padding: 2px 5px !important; font-size: 0.6rem !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

def send_push(title, body):
    js = f"<script>if(Notification.permission==='granted'){{new Notification('{title}',{{body:'{body}'}});}}</script>"
    components.html(js, height=0)

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

RYNKI = {"Metale": {"Złoto": "GC=F", "Srebro": "SI=F"}, "Krypto": {"BTC": "BTC-USD"}}

def main():
    st.sidebar.title("Menu")
    if st.sidebar.button("🔔 Aktywuj"):
        components.html("<script>Notification.requestPermission();</script>", height=0)

    kat = st.sidebar.radio("Rynek:", list(RYNKI.keys()), index=0)
    inst = st.sidebar.selectbox("Instrument:", list(RYNKI[kat].keys()), index=0)
    inter_label = st.sidebar.selectbox("Interwał:", ["1 m", "5 m", "15 m", "1 h", "1 d"], index=2)
    mapping = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}
    interval = mapping[inter_label]

    try:
        df = yf.download(RYNKI[kat][inst], period="5d", interval=interval, progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df[df['Open'] > 0].copy()
            df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            v_df = df.tail(50).copy()
            last = v_df.iloc[-1]
            prev = v_df.iloc[-2]
            
            diff = (last['EMA9'] - last['EMA21']) / last['EMA21']
            strong = abs(diff) > 0.00015
            kup = (last['EMA9'] > last['EMA21']) and (last['RSI'] < 65) and strong and (last['EMA21'] > prev['EMA21'])
            sprz = (last['EMA9'] < last['EMA21']) and (last['RSI'] > 35) and strong and (last['EMA21'] < prev['EMA21'])

            # Pasek górny
            c1, c2, c3 = st.columns([1, 1, 1.3])
            c1.metric("Cena", f"{last['Close']:.1f}")
            c2.metric("RSI", f"{last['RSI']:.0f}")
            with c3:
                if kup: st.success("KUPNO")
                elif sprz: st.error("SPRZEDAŻ")
                else: st.warning("CZEKAJ")

            # Wykres
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.88, 0.12])
            
            # Cena i EMA
            fig.add_trace(go.Candlestick(x=v_df.index, open=v_df['Open'], high=v_df['High'], low=v_df['Low'], close=v_df['Close'], showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['EMA9'], line=dict(color='orange', width=1.5), showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['EMA21'], line=dict(color='purple', width=1.5), showlegend=False), row=1, col=1)

            # Sygnały
            v_df['b'] = (v_df['EMA9']>v_df['EMA21']) & ((v_df['EMA9']-v_df['EMA21'])/v_df['EMA21']>0.00015) & (v_df['RSI']<65)
            v_df['s'] = (v_df['EMA9']<v_df['EMA21']) & ((v_df['EMA9']-v_df['EMA21'])/v_df['EMA21']<-0.00015) & (v_df['RSI']>35)
            
            fig.add_trace(go.Scatter(x=v_df[v_df['b']].index, y=v_df[v_df['b']]['Low']*0.9998, mode='markers', marker=dict(symbol='triangle-up', size=7, color='lime'), showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=v_df[v_df['s']].index, y=v_df[v_df['s']]['High']*1.0002, mode='markers', marker=dict(symbol='triangle-down', size=7, color='
