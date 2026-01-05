import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Analizator XTB PRO")

# Zaawansowany CSS dla maksymalnej czytelnosci na telefonie
st.markdown("""
    <style>
    .main-title { font-size: 1.0rem !important; font-weight: bold; margin-bottom: 5px; }
    /* Zmniejszenie czcionki metryk (Cena i RSI) */
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    .stMetric { padding: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Baza instrumentow
METALE_I_ENERGIA = {"Zloto": "GC=F", "Srebro": "SI=F", "Ropa (WTI)": "CL=F", "Gaz Ziemny": "NG=F", "Miedz": "HG=F"}
ROLNICTWO = {"Kakao": "CC=F", "Kawa": "KC=F", "Cukier": "SB=F", "Kukurydza": "ZC=F", "Pszenica": "ZW=F"}
KRYPTO_XTB = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Ripple": "XRP-USD"}
INDEKSY = {"DAX (DE30)": "^GDAXI", "NASDAQ (US100)": "^IXIC", "S&P 500": "^GSPC"}

INTERVALS = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}
PERIODS = {"1m": "7d", "5m": "60d", "15m": "60d", "1h": "730d", "1d": "max"}

def main():
    # Sidebar - Panel sterowania
    st.sidebar.title("Ustawienia")
    kat = st.sidebar.radio("Rynek:", ["Metale/Energia", "Rolnictwo", "Kryptowaluty", "Indeksy"])
    
    if kat == "Metale/Energia": lista = METALE_I_ENERGIA
    elif kat == "Rolnictwo": lista = ROLNICTWO
    elif kat == "Kryptowaluty": lista = KRYPTO_XTB
    else: lista = INDEKSY
        
    selected_name = st.sidebar.selectbox("Instrument:", list(lista.keys()))
    int_name = st.sidebar.selectbox("Interwal:", list(INTERVALS.keys()))
    
    # OPCJA: Pokazywanie sygnalow na wykresie
    show_signals = st.sidebar.checkbox("Pokaż sygnały na wykresie", value=True)
    
    interval = INTERVALS[int_name]

    try:
        df = yf.download(lista[selected_name], period=PERIODS[interval], interval=interval, progress=False)
        
        if not df.empty:
            # Obliczenia techniczne
            df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            # Logika sygnalow dla calego zbioru danych (do wykresu)
            df['Buy_Sig'] = (df['EMA_9'] > df['EMA_21']) & (df['RSI'] < 70)
            df['Sell_Sig'] = (df['EMA_9'] < df['EMA_21']) & (df['RSI'] > 30)

            # Wartosci biezace
            cena = float(df['Close'].iloc[-1])
            rsi_v = float(df['RSI'].iloc[-1])
            e9, e21 = float(df['EMA_9'].iloc[-1]), float(df['EMA_21'].iloc[-1])

            st.markdown(f'<p class="main-title">{selected_name} - {int_name}</p>', unsafe_allow_html=True)
            
            # Kompaktowe metryki
            m1, m2, m3 = st.columns(3)
            m1.metric("Cena", f"{cena:.2f}")
            m2.metric("RSI", f"{rsi_v:.1f}")
            
            if e9 > e21 and rsi_v < 70: m3.success("KUPNO")
            elif e9 < e21 and rsi_v > 30: m3.error("SPRZEDAZ")
            else: m3.warning("CZEKAJ")

            # Wykres Swieczkowy
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.75, 0.25])
            
            # Swiece
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Cena'), row=1, col=1)
            
            # Linie EMA
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], name='EMA 9', line=dict(color='orange', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], name='EMA 21', line=dict(color='purple', width=1)), row=1, col=1)
            
            # SYGNALY NA WYKRESIE (Trójkąty)
            if show_signals:
                buy_points = df[df['Buy_Sig']]
                sell_points = df[df['Sell_Sig']]
                
                fig.add_trace(go.Scatter(x=buy_points.index, y=buy_points['Low'] * 0.998, mode='markers', 
                                         marker=dict(symbol='triangle-up', size=10, color='#00ff00'), name='Sygnał Kupna'), row=1, col=1)
                
                fig.add_trace(go.Scatter(x=sell_points.index, y=sell_points['High'] * 1.002, mode='markers', 
                                         marker=dict(symbol='triangle-down', size=10, color='#ff0000'), name='Sygnał Sprzedaży'), row=1, col=1)
            
            # RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#00d4ff', width=1.2)), row=2, col=1)
            fig
