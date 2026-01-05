import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="PRO Analizator")

# CSS - kompaktowy widok mobilny
st.markdown("""
    <style>
    .main-title { font-size: 0.85rem !important; font-weight: bold; margin: 0px; }
    [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
    .stMetric { padding: 2px !important; }
    </style>
    """, unsafe_allow_html=True)

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

RYNKI = {
    "Metale/Energia": {"Złoto": "GC=F", "Srebro": "SI=F", "Ropa": "CL=F", "Gaz": "NG=F"},
    "Krypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Indeksy": {"DAX": "^GDAXI", "NASDAQ": "^IXIC", "SP500": "^GSPC"}
}

INTERVALS = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}

def main():
    st.sidebar.title("PRO Menu")
    kat = st.sidebar.radio("Rynek:", list(RYNKI.keys()))
    inst = st.sidebar.selectbox("Instrument:", list(RYNKI[kat].keys()))
    inter = st.sidebar.selectbox("Interwał:", list(INTERVALS.keys()))
    show_markers = st.sidebar.toggle("Sygnały", value=True)
    
    interval = INTERVALS[inter]

    try:
        df = yf.download(RYNKI[kat][inst], period="60d" if interval != "1d" else "max", interval=interval, progress=False)
        
        if not df.empty:
            # Czyszczenie danych pod wykres świecowy
            df = df.copy()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)

            df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            # Ograniczenie do 50 ostatnich świec dla czytelności na telefonie
            v_df = df.tail(50).copy()

            # Nagłówek i metryki
            st.markdown(f'<p class="main-title">{inst} ({inter})</p>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Cena", f"{v_df['Close'].iloc[-1]:.2f}")
            c2.metric("RSI", f"{v_df['RSI'].iloc[-1]:.1f}")
            
            # Logika sygnału
            last_e9 = v_df['EMA9'].iloc[-1]
            last_e21 = v_df['EMA21'].iloc[-1]
            last_rsi = v_df['RSI'].iloc[-1]
            
            if last_e9 > last_e21 and last_rsi < 70: c3.success("KUPNO")
            elif last_e9 < last_e21 and last_rsi > 30: c3.error("SPRZEDAŻ")
            else: c3.warning("CZEKAJ")

            # WYKRES
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # Świece z wymuszonym obramowaniem i wypełnieniem
            fig.add_trace(go.Candlestick(
                x=v_df.index, open=v_df['Open'], high=v_df['High'], low=v_df['Low'], close=v_df['Close'],
                increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
                increasing_fillcolor='#26a69a', decreasing_fillcolor='#ef5350',
                line=dict(width=1.5), name='Cena'
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['EMA9'], line=dict(color='orange', width=1.5), name='EMA9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['EMA21'], line=dict(color='purple', width=1.5), name='EMA21'), row=1, col=1)

            if show_markers:
                buys = v_df[(v_df['EMA9'] > v_df['EMA21']) & (v_df['RSI'] < 70)]
                sells = v_df[(v_df['EMA9'] < v_df['EMA21']) & (v_df['RSI'] > 30)]
                fig.add_trace(go.Scatter(x=buys.index, y=buys['Low']*0.999, mode='markers', marker=dict(symbol='triangle-up', size=12, color='lime')), row=1, col=1)
                fig.add_trace(go.Scatter(x=sells.index, y=sells['High']*1.001, mode='markers', marker=dict(symbol='triangle-down', size=12, color='red')), row=1, col=1)

            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['RSI'], line=dict(color='#00d4ff', width=2)), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.3, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.3, row=2, col=1)

            fig.update_layout(height=480, margin=dict(l=5, r=5, t=5, b=5), template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
