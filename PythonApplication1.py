import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Analizator Gieldowy")

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Slowniki aktywow
SUROWCE = {
    "Zloto": "GC=F", "Srebro": "SI=F", "Ropa": "CL=F", "Gaz": "NG=F", "Miedz": "HG=F"
}

KRYPTO_XTB = {
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", 
    "Cardano": "ADA-USD", "Ripple": "XRP-USD", "Dogecoin": "DOGE-USD",
    "Polkadot": "DOT-USD", "Chainlink": "LINK-USD", "Litecoin": "LTC-USD"
}

INTERVALS = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}
PERIODS = {"1m": "7d", "5m": "60d", "15m": "60d", "1h": "730d", "1d": "max"}

def main():
    st.sidebar.title("Panel Sterowania")
    
    # Wybor kategorii i aktywa
    kategoria = st.sidebar.radio("Wybierz rynek:", ["Surowce", "Kryptowaluty"])
    
    if kategoria == "Surowce":
        lista = SUROWCE
    else:
        lista = KRYPTO_XTB
        
    selected_name = st.sidebar.selectbox("Wybierz instrument:", list(lista.keys()))
    symbol = lista[selected_name]

    # Wybor interwalu
    selected_int_name = st.sidebar.selectbox("Interwal czasowy:", list(INTERVALS.keys()))
    interval = INTERVALS[selected_int_name]
    period = PERIODS[interval]

    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if not df.empty:
            # Obliczenia
            df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            # Wyciaganie wartosci (naprawa bledu Series)
            cena = float(df['Close'].iloc[-1].iloc[0] if isinstance(df['Close'].iloc[-1], pd.Series) else df['Close'].iloc[-1])
            rsi_v = float(df['RSI'].iloc[-1].iloc[0] if isinstance(df['RSI'].iloc[-1], pd.Series) else df['RSI'].iloc[-1])
            ema9 = float(df['EMA_9'].iloc[-1].iloc[0] if isinstance(df['EMA_9'].iloc[-1], pd.Series) else df['EMA_9'].iloc[-1])
            ema21 = float(df['EMA_21'].iloc[-1].iloc[0] if isinstance(df['EMA_21'].iloc[-1], pd.Series) else df['EMA_21'].iloc[-1])

            # Naglowek i Sygnaly
            st.title(f"Analiza: {selected_name} ({selected_int_name})")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Cena", f"{cena:.2f} USD")
            c2.metric("RSI (14)", f"{rsi_v:.1f}")
            
            if ema9 > ema21 and rsi_v < 70:
                c3.success("SYGNAL: KUPNO")
            elif ema9 < ema21 and rsi_v > 30:
                c3.error("SYGNAL: SPRZEDAZ")
            else:
                c3.warning("SYGNAL: CZEKAJ")

            # Wykres
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Cena'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], name='EMA 9', line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], name='EMA 21', line=dict(color='purple')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='cyan')), row=2, col=1)
            
            fig.update_layout(height=650, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("Brak danych dla wybranego interwalu.")
            
    except Exception as e:
        st.error(f"Blad: {e}")

if __name__ == "__main__":
    main()
