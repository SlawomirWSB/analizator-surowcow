from __future__ import annotations
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Ustawienia strony Streamlit
st.set_page_config(layout="wide", page_title="Analizator Surowców")

# --- Funkcje obliczeniowe ---
def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    with pd.option_context('mode.use_inf_as_na', True):
        rs = gain / loss
    
    return 100 - (100 / (1 + rs))

# --- Konfiguracja surowców i interwa³ów ---
COMMODITIES = {
    "Zloto (GC=F)": "GC=F",
    "Srebro (SI=F)": "SI=F",
    "Ropa Naftowa (CL=F)": "CL=F",
    "Gaz Ziemny (NG=F)": "NG=F",
    "Miedz (HG=F)": "HG=F",
    "Platyna (PL=F)": "PL=F",
    "Kawa (KC=F)": "KC=F",
    "Pszenica (ZW=F)": "ZW=F",
}

INTERVALS = {
    "1 minuta": "1m",
    "5 minut": "5m",
    "15 minut": "15m",
    "30 minut": "30m",
    "1 godzina": "1h",
    "1 dzien": "1d",
}

PERIODS = {
    "1 minuta": "7d", 
    "5 minut": "60d",
    "15 minut": "60d",
    "30 minut": "60d",
    "1 godzina": "730d", 
    "1 dzien": "max",
}

def main():
    st.title("Analizator Surowców z Wykresami i RSI/EMA")
    
    # --- Sidebar ---
    st.sidebar.header("Ustawienia Analizy")
    selected_commodity_name = st.sidebar.selectbox("Wybierz Surowiec", list(COMMODITIES.keys()))
    selected_symbol = COMMODITIES[selected_commodity_name]

    selected_interval_name = st.sidebar.selectbox("Wybierz Interwa³", list(INTERVALS.keys()))
    selected_interval = INTERVALS[selected_interval_name]
    selected_period = PERIODS[selected_interval_name]

    # W wersji webowej lepiej u¿yæ przycisku lub st.empty do odœwie¿ania
    if st.sidebar.button("Odœwie¿ Dane"):
        st.rerun()

    # --- Pobieranie i analiza danych ---
    try:
        df = yf.download(selected_symbol, period=selected_period, interval=selected_interval, progress=False)
        
        if df.empty:
            st.error("Brak danych. Spróbuj innego interwa³u.")
            return

        # Obliczenia techniczne
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['RSI'] = oblicz_rsi(df['Close'])
        df.dropna(inplace=True)

        cena = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        ema_s = float(df['EMA_9'].iloc[-1])
        ema_w = float(df['EMA_21'].iloc[-1])

        # Wyœwietlanie wyników
        col1, col2, col3 = st.columns(3)
        col1.metric("Cena", f"{cena:.2f} USD")
        col2.metric("RSI (14)", f"{rsi:.1f}")
        col3.metric("EMA 9/21", f"{ema_s:.1f} / {ema_w:.1f}")

        # Sygna³y
        if ema_s > ema_w and rsi < 70:
            st.success(">>> SYGNA£ KUPNA <<<")
        elif ema_s < ema_w and rsi > 30:
            st.error(">>> SYGNA£ SPRZEDA¯Y <<<")
        else:
            st.warning(">>> OCZEKIWANIE <<<")

        # --- Wykres ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Cena'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], name='EMA 9', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], name='EMA 21', line=dict(color='purple', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='blue', width=2)), row=2, col=1)
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"B³¹d: {e}")

if __name__ == "__main__":
    main()