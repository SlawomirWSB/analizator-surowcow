import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="PRO Trader")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Optymalizacja Mobile
st.markdown("""
    <style>
    .block-container { padding: 0.1rem 0.3rem !important; }
    header { visibility: hidden; }
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
    }
    [data-testid="stMetric"] { 
        background: #1a1c24; border-radius: 4px; 
        padding: 1px 4px !important; border: 1px solid #3e414f;
    }
    [data-testid="stMetricValue"] { font-size: 0.8rem !important; color: white !important; }
    [data-testid="stMetricLabel"] { font-size: 0.5rem !important; margin-bottom: -12px; }
    .stAlert { padding: 2px 4px !important; font-size: 0.6rem !important; }
    </style>
    """, unsafe_allow_html=True)

def send_push(t, b):
    js = f"<script>if(window.Notification && Notification.permission==='granted'){{new Notification('{t}',{{body:'{b}'}});}}</script>"
    components.html(js, height=0)

def get_rsi(prices, n=14):
    deltas = prices.diff()
    gains = deltas.where(deltas > 0, 0).rolling(window=n).mean()
    losses = (-deltas.where(deltas < 0, 0)).rolling(window=n).mean()
    rs = gains / losses
    return 100 - (100 / (1 + rs))

# Baza danych
DB = {"Metale": {"Złoto": "GC=F", "Srebro": "SI=F"}, "Krypto": {"BTC": "BTC-USD"}}

def main():
    # Sidebar
    if st.sidebar.button("🔔 Aktywuj Powiadomienia"):
        components.html("<script>Notification.requestPermission();</script>", height=0)
    
    cat = st.sidebar.radio("Rynek", list(DB.keys()), index=0)
    inst = st.sidebar.selectbox("Instrument", list(DB[cat].keys()), index=0)
    itv_map = {"1m":"1m","5m":"5m","15m":"15m","1h":"1h"}
    itv = st.sidebar.selectbox("Interwał", list(itv_map.keys()), index=2)

    try:
        df = yf.download(DB[cat][inst], period="5d", interval=itv, progress=False)
        if df.empty: return

        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['E9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['E21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['R'] = get_rsi(df['Close'])
        df.dropna(inplace=True)

        v = df.tail(50).copy()
        curr = v.iloc[-1]
        prev = v.iloc[-2]
        
        # Logika sygnałów
        diff = (curr['E9'] - curr['E21']) / curr['E21']
        is_trend = abs(diff) > 0.00015
        buy = (curr['E9'] > curr['E21']) and (curr['R'] < 65) and is_trend and (curr['E21'] > prev['E21'])
        sel = (curr['E9'] < curr['E21']) and (curr['R'] > 35) and is_trend and (curr['E21'] < prev['E21'])

        # Nagłówek i metryki
        st.markdown(f"**{inst} ({itv})**")
        c1, c2, c3 = st.columns([1, 1, 1.2])
        c1.metric("Cena", f"{curr['Close']:.1f}")
        c2.metric("RSI", f"{curr['R']:.0f}")
        
        with c3:
            if buy: 
                st.success("KUPNO")
                send_push(f"KUPNO {inst}", f"Cena: {curr['Close']:.1f}")
            elif sel: 
                st.error("SPRZEDAŻ")
                send_push(f"SPRZEDAŻ {inst}", f"Cena: {curr['Close']:.1f}")
            else: 
                st.warning("CZEKAJ")

        # Wykres
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.01, row_heights=[0.88, 0.12])
        
        # świece
        fig.add_trace(go.Candlestick(x=v.index, open=v['Open'], high=v['High'], 
                                   low=v['Low'], close=v['Close'], name='C'), row=1, col=1)
        # Średnie
        fig.add_trace(go.Scatter(x=v.index, y=v['E9'], line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E21'], line=dict(color='purple', width=1)), row=1, col=1)

        # Trójkąty
        v['b_sig'] = (v['E9']>v['E21']) & ((v['E9']-v['E21'])/v['E21']>0.00015) & (v['R']<65)
        v['s_sig'] = (v['E9']<v['E21']) & ((v['E9']-v['E21'])/v['E21']<-0.00015) & (v['R']>35)
        
        fig.add_trace(go.Scatter(x=v[v['b_sig']].index, y=v[v['b_sig']]['Low']*0.9998, 
                               mode='markers', marker=dict(symbol='triangle-up', size=8, color='lime')), row=1, col=1)
        fig.add_trace(go.Scatter(x=v[v['s_sig']].index, y=v[v['s_sig']]['High']*1.0002, 
                               mode='markers', marker=dict(symbol='triangle-down', size=8, color='red')), row=1, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=v.index, y=v['R'], line=dict(color='#00d4ff', width=1)), row=2, col=1)

        fig.update_layout(height=800, margin=dict(l=0, r=0, t=2, b=0), 
                          template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Błąd: {str(e)}")

if __name__ == "__main__":
    main()
