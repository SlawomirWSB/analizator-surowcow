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

# CSS - Wymuszenie jednego wiersza na telefonie i miniaturyzacja
st.markdown("""
    <style>
    /* Nagłówek */
    .main-title { font-size: 0.8rem !important; font-weight: bold; color: white; margin: 0px 0px 5px 0px; }
    
    /* Wymuszenie kolumn w jednym wierszu na mobile */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 5px !important;
    }
    
    /* Stylizacja pojedynczego kafelka metryki */
    [data-testid="stMetric"] { 
        background-color: #1e2130; 
        border-radius: 5px; 
        padding: 2px 8px !important; 
        border: 1px solid #3e414f;
        min-width: 80px;
    }
    
    /* Zmniejszenie czcionek w metrykach */
    [data-testid="stMetricValue"] { color: white !important; font-size: 0.9rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #8a8d97 !important; font-size: 0.65rem !important; margin-bottom: -8px; }
    
    /* Stylizacja alertu (Kupno/Sprzedaż/Czekaj) */
    .stAlert { 
        padding: 5px 10px !important; 
        margin: 0px !important; 
        font-size: 0.7rem !important;
        min-width: 100px;
    }
    
    /* Ukrycie paddingu głównego kontenera */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
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
    show_markers = st.sidebar.toggle("Pokaż sygnały", value=True)
    alerty_on = st.sidebar.toggle("Włącz alerty Push", value=True)
    
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
            
            kupno_cond = (last_row['EMA9'] > last_row['EMA21']) and (last_row['RSI'] < 65) and trend_strength and (last_row['EMA21'] > prev_row['EMA21'])
            sprzedaz_cond = (last_row['EMA9'] < last_row['EMA21']) and (last_row['RSI'] > 35) and trend_strength and (last_row['EMA21'] < prev_row['EMA21'])

            # TYTUŁ
            st.markdown(f'<p class="main-title">{inst} ({inter_label})</p>', unsafe_allow_html=True)
            
            # PASEK METRYK (3 kolumny w jednym wierszu)
            col1, col2, col3 = st.columns([1, 1, 1.2])
            
            with col1:
                st.metric("Cena", f"{last_row['Close']:.2f}")
            with col2:
                st.metric("RSI", f"{last_row['RSI']:.0f}") # Bez miejsc po przecinku dla oszczędności miejsca
            with col3:
                if kupno_cond:
                    st.success("KUPNO")
                    if alerty_on: send_push(f"KUPNO {inst}", f"Cena: {last_row['Close']:.2f}")
                elif sprzedaz_cond:
                    st.error("SPRZEDAŻ")
                    if alerty_on: send_push(f"SPRZEDAŻ {inst}", f"Cena: {last_row['Close']:.2f}")
                else:
                    st.warning("CZEKAJ")

            # Wykres
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8, 0.2])
