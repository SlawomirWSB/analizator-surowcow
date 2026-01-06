import streamlit as st
from tvdatafeed import TvDatafeed, Interval
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="TV Real-Time Reader")
st_autorefresh(interval=30 * 1000, key="data_refresh") # Odświeżanie co 30s

def main():
    st.title("Wykres z danymi TradingView")
    
    # Inicjalizacja (bez logowania - jako gość)
    tv = TvDatafeed()
    
    # Wybór instrumentu (Format TV: Giełda:Symbol)
    # Złoto = COMEX:GC1! lub TVC:GOLD
    # Kakao = ICEUS:CC1!
    symbol = st.selectbox("Wybierz instrument", ["TVC:GOLD", "ICEUS:CC1!", "CAPITALCOM:BITCOIN"])
    
    try:
        # Pobieranie danych z TV
        # n_bars=100 to ostatnie 100 świec
        df = tv.get_hist(symbol=symbol, exchange='', interval=Interval.in_15_minute, n_bars=100)
        
        if df is not None:
            # Obliczanie RSI i EMA w Pythonie na danych z TV
            df['EMA9'] = df['close'].ewm(span=9).mean()
            df['EMA21'] = df['close'].ewm(span=21).mean()
            
            curr_price = df['close'].iloc[-1]
            
            # Prosty sygnał
            signal = "KUP" if df['EMA9'].iloc[-1] > df['EMA21'].iloc[-1] else "SPRZEDAJ"
            color = "green" if signal == "KUP" else "red"
            
            st.markdown(f"### Cena: `{curr_price:.2f}` | Sygnał: <span style='color:{color}'>{signal}</span>", unsafe_allow_html=True)
            
            # Wykres Plotly (możesz go przesuwać i powiększać)
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close']
            )])
            fig.update_layout(template="plotly_dark", height=600, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error("Problem z połączeniem z TradingView. Prawdopodobnie limit zapytań.")

if __name__ == "__main__":
    main()
