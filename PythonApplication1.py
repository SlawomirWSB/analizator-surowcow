import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja strony
st.set_page_config(layout="wide", page_title="Analizator Sygnałów PRO")

# 2. Automatyczne odświeżanie co 60 sekund
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS dla lepszego wyglądu na telefonie
st.markdown("""
    <style>
    .main-title { font-size: 1rem !important; font-weight: bold; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Baza rynków
RYNKI = {
    "Metale/Energia": {"Złoto": "GC=F", "Srebro": "SI=F", "Ropa": "CL=F", "Gaz": "NG=F"},
    "Krypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Indeksy": {"DAX": "^GDAXI", "NASDAQ": "^IXIC", "SP500": "^GSPC"}
}

def main():
    st.sidebar.title("PRO Panel")
    kat = st.sidebar.radio("Rynek:", list(RYNKI.keys()))
    inst = st.sidebar.selectbox("Instrument:", list(RYNKI[kat].keys()))
    inter_label = st.sidebar.selectbox("Interwał:", ["1 m", "5 m", "15 m", "1 h", "1 d"])
    
    # Przycisk aktywacji alertów (wymagany przez przeglądarki, by puścić dźwięk)
    alerty_on = st.sidebar.toggle("Włącz alerty (Dźwięk/Wibracja)", value=False)
    
    mapping = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}
    interval = mapping[inter_label]

    try:
        # Pobieranie danych
        df = yf.download(RYNKI[kat][inst], period="5d" if interval != "1d" else "max", interval=interval, progress=False)
        
        if not df.empty:
            # Standaryzacja i wskaźniki
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df[df['Open'] > 0].copy()
            df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            v_df = df.tail(50).copy()
            last_row = v_df.iloc[-1]

            # Wyświetlanie metryk
            st.markdown(f'<p class="main-title">{inst} - Interwał {inter_label}</p>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Cena", f"{last_row['Close']:.2f}")
            c2.metric("RSI", f"{last_row['RSI']:.1f}")

            # --- LOGIKA SYGNAŁÓW I ALERTÓW ---
            sygnal = "CZEKAJ"
            color = "gray"
            
            if last_row['EMA9'] > last_row['EMA21'] and last_row['RSI'] < 70:
                sygnal = "KUPNO"
                c3.success(sygnal)
                if alerty_on:
                    st.components.v1.html("""
                        <script>
                        if (window.navigator && window.navigator.vibrate) window.navigator.vibrate(500);
                        new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.pid').play();
                        </script>
                    """, height=0)
            
            elif last_row['EMA9'] < last_row['EMA21'] and last_row['RSI'] > 30:
                sygnal = "SPRZEDAŻ"
                c3.error(sygnal)
                if alerty_on:
                    st.components.v1.html("""
                        <script>
                        if (window.navigator && window.navigator.vibrate) window.navigator.vibrate([200, 100, 200]);
                        new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.pid').play();
                        </script>
                    """, height=0)
            else:
                c3.warning(sygnal)

            # --- WYKRES ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(
                x=v_df.index, open=v_df['Open'], high=v_df['High'], low=v_df['Low'], close=v_df['Close'],
                increasing_line_color='#26a69a', decreasing_line_color='#ef5350', name='Cena'
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['EMA9'], line=dict(color='orange', width=1.5), name='EMA9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['EMA21'], line=dict(color='purple', width=1.5), name='EMA21'), row=1, col=1)
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['RSI'], line=dict(color='#00d4ff', width=2)), row=2, col=1)

            fig.update_layout(height=480, margin=dict(l=5, r=5, t=5, b=5), template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
