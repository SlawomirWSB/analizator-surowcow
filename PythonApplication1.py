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

# CSS - Maksymalna optymalizacja pod pionowy widok telefonu
st.markdown("""
    <style>
    .main-title { font-size: 0.75rem !important; font-weight: bold; color: white; margin: 0px 0px 2px 0px; }
    
    /* Wymuszenie jednego wiersza dla metryk */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
        margin-bottom: -15px !important;
    }
    
    /* Miniaturowe kafelki */
    [data-testid="stMetric"] { 
        background-color: #1e2130; 
        border-radius: 4px; 
        padding: 2px 5px !important; 
        border: 1px solid #3e414f;
        min-width: 65px;
    }
    
    [data-testid="stMetricValue"] { color: white !important; font-size: 0.85rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #8a8d97 !important; font-size: 0.6rem !important; margin-bottom: -10px; }
    
    /* Status (Kupno/Sprzedaż) */
    .stAlert { padding: 4px 8px !important; font-size: 0.65rem !important; border-radius: 4px !important; }
    
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
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

RYNKI = {
    "Metale": {"Złoto": "GC=F", "Srebro": "SI=F", "Miedź": "HG=F"},
    "Krypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Indeksy": {"DAX": "^GDAXI", "NASDAQ": "^IXIC", "SP500": "^GSPC"}
}

def main():
    st.sidebar.title("PRO Menu")
    if st.sidebar.button("🔔 Aktywuj Powiadomienia"):
        components.html("<script>Notification.requestPermission();</script>", height=0)

    kat = st.sidebar.radio("Rynek:", list(RYNKI.keys()), index=0)
    inst_list = list(RYNKI[kat].keys())
    d_idx = inst_list.index("Złoto") if "Złoto" in inst_list else 0
    inst = st.sidebar.selectbox("Instrument:", inst_list, index=d_idx)
    
    inter_label = st.sidebar.selectbox("Interwał:", ["1 m", "5 m", "15 m", "1 h", "1 d"], index=2)
    show_markers = st.sidebar.toggle("Sygnały", value=True)
    alerty_on = st.sidebar.toggle("Alerty Push", value=True)
    
    mapping = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}
    interval = mapping[inter_label]

    try:
        df = yf.download(RYNKI[kat][inst], period="5d" if interval != "1d" else "max", interval=interval, progress=False)
        
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df[df['Open'] > 0].copy()
            df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            v_df = df.tail(50).copy()
            last_row = v_df.iloc[-1]
            prev_row = v_df.iloc[-2]

            ema_diff_pct = (last_row['EMA9'] - last_row['EMA21']) / last_row['EMA21']
            trend_strength = abs(ema_diff_pct) > 0.00015 
            
            kupno = (last_row['EMA9'] > last_row['EMA21']) and (last_row['RSI'] < 65) and trend_strength and (last_row['EMA21
