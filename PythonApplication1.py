import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Analizator XTB PRO")

# Styl CSS dla czytelności na telefonie
st.markdown("""
    <style>
    .main-title { font-size: 0.9rem !important; font-weight: bold; margin-bottom: 2px; }
    [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
    .stMetric { padding: 0px !important; }
    div[data-testid="stMetric"] { background-color: rgba(28, 131, 225, 0.1); padding: 5px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Baza instrumentów
METALE_ENERGIA = {"Złoto": "GC=F", "Srebro": "SI=F", "Ropa WTI": "CL=F", "Gaz": "NG=F", "Miedź": "HG=F"}
ROLNICTWO = {"Kakao": "CC=F", "Kawa": "KC=F", "Cukier": "SB=F", "Kukurydza": "ZC=F"}
KRYPTO = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"}
INDEKSY = {"DAX": "^GDAXI", "NASDAQ": "^IXIC", "SP500": "^GSPC"}

INTERVALS = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}
PERIODS = {"1m": "7d", "5m": "60d", "15m": "60d", "1h": "730d", "1d": "max"}

def main():
    st.sidebar.title("PRO Menu")
    kat = st.sidebar.radio("Rynek:", ["Metale/Energia", "Rolnictwo", "Krypto", "Indeksy"])
    
    if kat == "Metale/Energia": lista = METALE_ENERGIA
    elif kat == "Rolnictwo": lista = ROLNICTWO
    elif kat == "Krypto": lista = KRYPTO
    else: lista = INDEKSY
        
    inst = st.sidebar.selectbox("Instrument:", list(lista.keys()))
    inter = st.sidebar.selectbox("Interwał:", list(INTERVALS.keys()))
    show_markers = st.sidebar.toggle("Pokaż trójkąty sygnałów", value=True)
    
    interval = INTERVALS[inter]

    try:
        df = yf.download(lista[inst], period=PERIODS[interval], interval=interval, progress=False)
        
        if not df.empty:
            df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            # Sygnały do znaczników
            df['Buy_Tag'] = (df['EMA_9'] > df['EMA_21']) & (df['RSI'] < 70)
            df['Sell_Tag'] = (df['EMA_9'] < df['EMA_21']) & (df['RSI'] > 30)

            cena = float(df['Close'].iloc[-1])
            rsi_v = float(df['RSI'].iloc[-1])
            e9, e21 = float(df['EMA_9'].iloc[-1]), float(df['EMA_21'].iloc[-1])

            st.markdown(f'<p class="main-title">{inst} ({inter})</p>', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Cena", f"{cena:.2f}")
            c2.metric("RSI", f"{rsi_v:.1f}")
            
            if e9 > e21 and rsi_v < 70: c3.success("KUPNO")
            elif e9 < e21 and rsi_v > 30: c3.error("SPRZEDAŻ")
            else: c3.warning("CZEKAJ")

            # --- WYKRES ŚWIECZKOWY ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
            
            # Świece
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], 
                name='Cena', increasing_line_color='#00ff00', decreasing_line_color='#ff0000'
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], line=dict(color='orange', width=1), name='EMA9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], line=dict(color='purple', width=1), name='EMA21'), row=1, col=1)
            
            # Znaczniki trójkątne
            if show_markers:
                buys = df[df['Buy_Tag']]
                sells = df[df['Sell_Tag']]
                fig.add_trace(go.Scatter(x=buys.index, y=buys['Low']*0.999, mode='markers', 
                                         marker=dict(symbol='triangle-up', size=10, color='lime'), name='B'), row=1, col=1)
                fig.add_trace(go.Scatter(x=sells.index, y=sells['High']*1.001, mode='markers', 
                                         marker=dict(symbol='triangle-down', size=10, color='red'), name='S'), row=1, col=1)

            # RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#00d4ff', width=1.5)), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            # Zoom i Layout
            zoom = 120 if interval == "1m" else 80
            fig.update_xaxes(range=[df.index[-min(len(df), zoom)], df.index[-1]])
            fig.update_layout(height=500, margin=dict(l=5, r=5, t=5, b=5), template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
