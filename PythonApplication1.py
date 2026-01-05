import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Analizator Sygnalow")

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

COMMODITIES = {"Zloto": "GC=F", "Srebro": "SI=F", "Ropa": "CL=F", "Gaz": "NG=F", "Miedz": "HG=F"}
INTERVALS = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}
PERIODS = {"1m": "7d", "5m": "60d", "15m": "60d", "1h": "730d", "1d": "max"}

def main():
    st.sidebar.title("Ustawienia")
    selected_name = st.sidebar.selectbox("Surowiec", list(COMMODITIES.keys()))
    interval = INTERVALS[st.sidebar.selectbox("Interwal", list(INTERVALS.keys()))]
    
    try:
        df = yf.download(COMMODITIES[selected_name], period=PERIODS[interval], interval=interval, progress=False)
        if not df.empty:
            # Obliczenia techniczne
            df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            # Pobranie ostatnich wartosci
            cena = float(df['Close'].iloc[-1].iloc[0] if isinstance(df['Close'].iloc[-1], pd.Series) else df['Close'].iloc[-1])
            rsi_val = float(df['RSI'].iloc[-1].iloc[0] if isinstance(df['RSI'].iloc[-1], pd.Series) else df['RSI'].iloc[-1])
            ema9 = float(df['EMA_9'].iloc[-1].iloc[0] if isinstance(df['EMA_9'].iloc[-1], pd.Series) else df['EMA_9'].iloc[-1])
            ema21 = float(df['EMA_21'].iloc[-1].iloc[0] if isinstance(df['EMA_21'].iloc[-1], pd.Series) else df['EMA_21'].iloc[-1])

            # --- SEKCJA SYGNAŁÓW ---
            st.subheader(f"Analiza dla: {selected_name}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Aktualna Cena", f"{cena:.2f} USD")
            col2.metric("RSI (14)", f"{rsi_val:.1f}")
            
            # Logika sygnałów
            if ema9 > ema21 and rsi_val < 70:
                col3.success("SYGNAL: KUPNO")
                st.info("EMA 9 jest powyzej EMA 21, a rynek nie jest jeszcze wykupiony (RSI < 70).")
            elif ema9 < ema21 and rsi_val > 30:
                col3.error("SYGNAL: SPRZEDAZ")
                st.info("EMA 9 spadlo ponizej EMA 21, a rynek nie jest jeszcze wyprzedany (RSI > 30).")
            else:
                col3.warning("SYGNAL: CZEKAJ")

            # Wykres
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Cena'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], name='EMA 9', line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], name='EMA 21', line=dict(color='purple')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='blue')), row=2, col=1)
            
            fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Blad danych: {e}")

if __name__ == "__main__":
    main()
