import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Analizator Gieldowy XTB")

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Rozszerzone listy instrumentow zgodnie z oferta XTB
METALE_I_ENERGIA = {
    "Zloto": "GC=F", "Srebro": "SI=F", "Ropa (WTI)": "CL=F", "Ropa (Brent)": "BZ=F",
    "Gaz Ziemny": "NG=F", "Miedz": "HG=F", "Aluminium": "ALI=F", "Platyna": "PL=F"
}

ROLNICTWO = {
    "Kakao": "CC=F", "Kawa": "KC=F", "Cukier": "SB=F", "Bawelna": "CT=F",
    "Kukurydza": "ZC=F", "Pszenica": "ZW=F", "Soja": "ZS=F"
}

KRYPTO_XTB = {
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", 
    "Cardano": "ADA-USD", "Ripple": "XRP-USD", "Dogecoin": "DOGE-USD",
    "Litecoin": "LTC-USD", "Chainlink": "LINK-USD", "Polkadot": "DOT-USD"
}

INDEKSY = {
    "DAX (DE30)": "^GDAXI", "NASDAQ (US100)": "^IXIC", "S&P 500 (US500)": "^GSPC",
    "Dow Jones (US30)": "^DJI", "Nikkei 225": "^N225"
}

INTERVALS = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}
PERIODS = {"1m": "7d", "5m": "60d", "15m": "60d", "1h": "730d", "1d": "max"}

def main():
    st.sidebar.title("Panel Sterowania")
    
    # Wybor kategorii
    kat = st.sidebar.radio("Rynek:", ["Metale/Energia", "Rolnictwo", "Kryptowaluty", "Indeksy"])
    
    if kat == "Metale/Energia": lista = METALE_I_ENERGIA
    elif kat == "Rolnictwo": lista = ROLNICTWO
    elif kat == "Kryptowaluty": lista = KRYPTO_XTB
    else: lista = INDEKSY
        
    selected_name = st.sidebar.selectbox("Instrument:", list(lista.keys()))
    symbol = lista[selected_name]

    # Wybor interwalu
    int_name = st.sidebar.selectbox("Interwal:", list(INTERVALS.keys()))
    interval = INTERVALS[int_name]
    period = PERIODS[interval]

    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if not df.empty:
            # Obliczenia techniczne
            df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            # Wartosci do metryk
            cena = float(df['Close'].iloc[-1].iloc[0] if isinstance(df['Close'].iloc[-1], pd.Series) else df['Close'].iloc[-1])
            rsi_v = float(df['RSI'].iloc[-1].iloc[0] if isinstance(df['RSI'].iloc[-1], pd.Series) else df['RSI'].iloc[-1])
            e9 = float(df['EMA_9'].iloc[-1].iloc[0] if isinstance(df['EMA_9'].iloc[-1], pd.Series) else df['EMA_9'].iloc[-1])
            e21 = float(df['EMA_21'].iloc[-1].iloc[0] if isinstance(df['EMA_21'].iloc[-1], pd.Series) else df['EMA_21'].iloc[-1])

            st.title(f"{selected_name} - Analiza {int_name}")
            
            # Kolumny z sygnalami
            m1, m2, m3 = st.columns(3)
            m1.metric("Cena", f"{cena:.2f}")
            m2.metric("RSI", f"{rsi_v:.1f}")
            
            if e9 > e21 and rsi_v < 70:
                m3.success("SYGNAL: KUPNO")
            elif e9 < e21 and rsi_v > 30:
                m3.error("SYGNAL: SPRZEDAZ")
            else:
                m3.warning("CZEKAJ / NEUTRALNIE")

            # Wykres interaktywny
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Cena'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], name='EMA 9', line=dict(color='orange', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], name='EMA 21', line=dict(color='purple', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='cyan', width=1.5)), row=2, col=1)
            
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Oczekiwanie na dane rynkowe... (Gielda moze byc zamknieta)")
            
    except Exception as e:
        st.error(f"Blad: {e}")

if __name__ == "__main__":
    main()
