import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Analizator XTB PRO")

# Styl CSS - ultra kompaktowy na telefon
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

# Rozszerzona baza surowców i indeksów
RYNKI = {
    "Metale/Energia": {"Złoto": "GC=F", "Srebro": "SI=F", "Ropa WTI": "CL=F", "Gaz": "NG=F", "Miedź": "HG=F", "Aluminium": "ALI=F"},
    "Rolnictwo": {"Kakao": "CC=F", "Kawa": "KC=F", "Cukier": "SB=F", "Kukurydza": "ZC=F", "Pszenica": "ZW=F", "Bawełna": "CT=F"},
    "Krypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Ripple": "XRP-USD"},
    "Indeksy": {"DAX": "^GDAXI", "NASDAQ": "^IXIC", "SP500": "^GSPC", "US30": "^DJI"}
}

INTERVALS = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}
PERIODS = {"1m": "5d", "5m": "30d", "15m": "30d", "1h": "180d", "1d": "max"}

def main():
    st.sidebar.title("PRO Menu")
    kat_name = st.sidebar.radio("Rynek:", list(RYNKI.keys()))
    lista = RYNKI[kat_name]
    
    selected_inst = st.sidebar.selectbox("Instrument:", list(lista.keys()))
    inter_name = st.sidebar.selectbox("Interwał:", list(INTERVALS.keys()))
    show_markers = st.sidebar.toggle("Pokaż sygnały (trójkąty)", value=True)
    
    interval = INTERVALS[inter_name]

    try:
        # Pobieranie danych
        df = yf.download(lista[selected_inst], period=PERIODS[interval], interval=interval, progress=False)
        
        if not df.empty:
            # Standaryzacja danych (naprawa błędu z Series/List)
            df = df.copy()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Wymuszenie formatu numerycznego
            for c in ['Open', 'High', 'Low', 'Close']:
                df[c] = pd.to_numeric(df[c], errors='coerce')

            # Wskaźniki
            df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            # Ograniczenie danych do wyświetlenia (zmusza system do pokazania świec)
            # Na telefonie 60 świec to idealna czytelność
            view_df = df.tail(60).copy()

            # Bieżące wartości
            last_price = float(view_df['Close'].iloc[-1])
            last_rsi = float(view_df['RSI'].iloc[-1])
            e9, e21 = float(view_df['EMA_9'].iloc[-1]), float(view_df['EMA_21'].iloc[-1])

            st.markdown(f'<p class="main-title">{selected_inst} - {inter_name}</p>', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Cena", f"{last_price:.2f}")
            c2.metric("RSI", f"{last_rsi:.1f}")
            
            if e9 > e21 and last_rsi < 70: c3.success("KUPNO")
            elif e9 < e21 and last_rsi > 30: c3.error("SPRZEDAŻ")
            else: c3.warning("CZEKAJ")

            # --- GŁÓWNY WYKRES ŚWIECZKOWY ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # Świece (Candlestick)
            fig.add_trace(go.Candlestick(
                x=view_df.index,
                open=view_df['Open'],
                high=view_df['High'],
                low=view_df['Low'],
                close=view_df['Close'],
                name='Cena',
                increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
            ), row=1, col=1)
            
            # Średnie
            fig.add_trace(go.Scatter(x=view_df.index, y=view_df['EMA_9'], line=dict(color='orange', width=1.5), name='EMA9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=view_df.index, y=view_df['EMA_21'], line=dict(color='purple', width=1.5), name='EMA21'), row=1, col=1)
            
            # Sygnały na świecach
            if show_markers:
                buys = view_df[(view_df['EMA_9'] > view_df['EMA_21']) & (view_df['RSI'] < 70)]
                sells = view_df[(view_df['EMA_9'] < view_df['EMA_21']) & (view_df['RSI'] > 30)]
                fig.add_trace(go.Scatter(x=buys.index, y=buys['Low']*0.999, mode='markers', marker=dict(symbol='triangle-up', size=11, color='lime'), name='B'), row=1, col=1)
                fig.add_trace(go.Scatter(x=sells.index, y=sells['High']*1.001, mode='markers', marker=dict(symbol='triangle-down', size=11, color='red'), name='S'), row=1, col=1)

            # RSI na dole
            fig.add_trace(go.Scatter(x=view_df.index, y=view_df['RSI'], line=dict(color='#00d4ff', width=2)), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.3, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.3, row=2, col=1)

            fig.update_layout(
                height=500, margin=dict(l=5, r=5, t=5, b=5),
                template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        else:
            st.warning("Brak danych - sprawdź czy giełda jest otwarta.")
            
    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
