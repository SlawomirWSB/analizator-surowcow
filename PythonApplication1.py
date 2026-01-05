import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# 1. Konfiguracja strony i auto-odświeżanie (co 60 sekund)
st.set_page_config(layout="wide", page_title="PRO Analizator")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Naprawa widoczności metryk i wyglądu
st.markdown("""
    <style>
    .main-title { font-size: 1.1rem !important; font-weight: bold; color: white; margin-bottom: 10px; }
    /* Stylizacja kafelków z ceną i RSI */
    [data-testid="stMetric"] {
        background-color: #262730;
        border-radius: 10px;
        padding: 15px !important;
        border: 1px solid #464855;
    }
    [data-testid="stMetricValue"] { color: white !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] { color: #a3a8b4 !important; }
    </style>
    """, unsafe_allow_html=True)

# Funkcja Powiadomień
def send_push(title, body):
    js = f"""
    <script>
    if (Notification.permission === "granted") {{
        new Notification("{title}", {{ body: "{body}", icon: "https://cdn-icons-png.flaticon.com/512/1991/1991047.png" }});
    }}
    </script>
    """
    components.html(js, height=0)

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

RYNKI = {
    "Krypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Metale": {"Złoto": "GC=F", "Srebro": "SI=F", "Miedź": "HG=F"},
    "Indeksy": {"DAX": "^GDAXI", "NASDAQ": "^IXIC", "SP500": "^GSPC"}
}

def main():
    st.sidebar.title("PRO Menu")
    
    # Przycisk aktywacji (kluczowy dla powiadomień)
    if st.sidebar.button("🔔 Aktywuj Powiadomienia"):
        components.html("<script>Notification.requestPermission();</script>", height=0)
        st.sidebar.success("Kliknij 'Zezwól' w przeglądarce")

    kat = st.sidebar.radio("Rynek:", list(RYNKI.keys()))
    inst = st.sidebar.selectbox("Instrument:", list(RYNKI[kat].keys()))
    inter_label = st.sidebar.selectbox("Interwał:", ["1 m", "5 m", "15 m", "1 h", "1 d"])
    
    # PRZYWRÓCONE OPCJE
    show_markers = st.sidebar.toggle("Pokaż sygnały (trójkąty)", value=True)
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

            # Wyświetlanie instrumentu
            st.markdown(f'<p class="main-title">{inst} ({inter_label})</p>', unsafe_allow_html=True)
            
            # Kolumny metryk
            m1, m2, m3 = st.columns([1, 1, 1])
            m1.metric("Cena", f"{last_row['Close']:.2f}")
            m2.metric("RSI", f"{last_row['RSI']:.1f}")

            # Sygnał tekstowy
            if last_row['EMA9'] > last_row['EMA21'] and last_row['RSI'] < 70:
                m3.success("KUPNO")
                if alerty_on: send_push(f"KUPNO {inst}", f"Cena: {last_row['Close']:.2f}")
            elif last_row['EMA9'] < last_row['EMA21'] and last_row['RSI'] > 30:
                m3.error("SPRZEDAŻ")
                if alerty_on: send_push(f"SPRZEDAŻ {inst}", f"Cena: {last_row['Close']:.2f}")
            else:
                m3.warning("CZEKAJ")

            # Wykres
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            
            # Świece
            fig.add_trace(go.Candlestick(
                x=v_df.index, open=v_df['Open'], high=v_df['High'], low=v_df['Low'], close=v_df['Close'],
                increasing_line_color='#26a69a', decreasing_line_color='#ef5350', name='Cena'
            ), row=1, col=1)

            # Średnie
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['EMA9'], line=dict(color='orange', width=2), name='EMA9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['EMA21'], line=dict(color='purple', width=2), name='EMA21'), row=1, col=1)

            # Sygnały (trójkąty) - WARUNKOWO
            if show_markers:
                buys = v_df[(v_df['EMA9'] > v_df['EMA21']) & (v_df['RSI'] < 70)]
                sells = v_df[(v_df['EMA9'] < v_df['EMA21']) & (v_df['RSI'] > 30)]
                fig.add_trace(go.Scatter(x=buys.index, y=buys['Low']*0.999, mode='markers', marker=dict(symbol='triangle-up', size=12, color='lime'), name='B'), row=1, col=1)
                fig.add_trace(go.Scatter(x=sells.index, y=sells['High']*1.001, mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name='S'), row=1, col=1)

            # RSI
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['RSI'], line=dict(color='#00d4ff', width=2), name='RSI'), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.3, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.3, row=2, col=1)

            fig.update_layout(height=600, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
