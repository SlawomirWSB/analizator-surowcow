from __future__ import annotations
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Analizator Surowcow")

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

COMMODITIES = {
    "Zloto (GC=F)": "GC=F",
    "Srebro (SI=F)": "SI=F",
    "Ropa Naftowa (CL=F)": "CL=F",
    "Gaz Ziemny (NG=F)": "NG=F",
    "Miedz (HG=F)": "HG=F"
}

def main():
    st.title("Analizator Surowcow")
    
    selected_name = st.sidebar.selectbox("Wybierz Surowiec", list(COMMODITIES.keys()))
    selected_symbol = COMMODITIES[selected_name]

    try:
        df = yf.download(selected_symbol, period="60d", interval="1h", progress=False)
        if df.empty:
            st.error("Brak danych.")
            return

        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['RSI'] = oblicz_rsi(df['Close'])
        df.dropna(inplace=True)

        cena = float(df['Close'].iloc[-1])
        st.metric("Ostatnia cena", f"{cena:.2f} USD")

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Cena'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI'), row=2, col=1)
        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
        
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Blad: {e}")

if __name__ == "__main__":
    main()