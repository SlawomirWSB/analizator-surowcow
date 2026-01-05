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

# CSS - Kompaktowy pasek narzędziowy
st.markdown("""
    <style>
    .block-container { padding: 0.1rem 0.2rem !important; }
    header { visibility: hidden; }
    .top-bar {
        display: flex; justify-content: space-between; align-items: center;
        background: #1a1c24; padding: 4px 8px; border-radius: 4px;
        border: 1px solid #3e414f; margin-bottom: 5px;
    }
    .metric-box { display: flex; flex-direction: column; }
    .m-label { font-size: 0.55rem; color: #8a8d97; line-height: 1; }
    .m-value { font-size: 0.85rem; color: white; font-weight: bold; line-height: 1.2; }
    .status-tag { font-size: 0.7rem; font-weight: bold; padding: 2px 6px; border-radius: 3px; }
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

DB = {"Metale": {"Złoto": "GC=F", "Srebro": "SI=F"}, "Krypto": {"BTC": "BTC-USD"}}

def main():
    # Sidebar
    kat = st.sidebar.radio("Rynek", list(DB.keys()), index=0)
    inst = st.sidebar.selectbox("Instrument", list(DB[kat].keys()), index=0)
    itv = st.sidebar.selectbox("Interwał", ["1m","5m","15m","1h"], index=2)

    try:
        df = yf.download(DB[kat][inst], period="5d", interval=itv, progress=False)
        if df.empty: return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['E9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['E21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['R'] = get_rsi(df['Close'])
        df.dropna(inplace=True)

        v = df.tail(50).copy()
        curr = v.iloc[-1]
        prev = v.iloc[-2]
        
        # Logika
        diff = (curr['E9'] - curr['E21']) / curr['E21']
        is_trend = abs(diff) > 0.00015
        buy = (curr['E9'] > curr['E21']) and (curr['R'] < 65) and is_trend and (curr['E21'] > prev['E21'])
        sel = (curr['E9'] < curr['E21']) and (curr['R'] > 35) and is_trend and (curr['E21'] < prev['E21'])

        # Renderowanie kompaktowego paska
        status_color = "#28a745" if buy else ("#dc3545" if sel else "#ffc107")
        status_text = "KUPNO" if buy else ("SPRZEDAŻ" if sel else "CZEKAJ")
        status_font = "white" if (buy or sel) else "black"

        st.markdown(f"""
            <div class="top-bar">
                <div class="metric-box"><span class="m-label">INSTR</span><span class="m-value">{inst}</span></div>
                <div class="metric-box"><span class="m-label">CENA</span><span class="m-value">{curr['Close']:.1f}</span></div>
                <div class="metric-box"><span class="m-label">RSI</span><span class="m-value">{curr['R']:.0f}</span></div>
                <div class="status-tag" style="background:{status_color}; color:{status_font};">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)

        # Wykres
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.9, 0.1])
        fig.add_trace(go.Candlestick(x=v.index, open=v['Open'], high=v['High'], low=v['Low'], close=v['Close']), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E9'], line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E21'], line=dict(color='purple', width=1)), row=1, col=1)

        # Sygnały
        v['b_sig'] = (v['E9']>v['E21']) & ((v['E9']-v['E21'])/v['E21']>0.00015) & (v['R']<65)
        v['s_sig'] = (v['E9']<v['E21']) & ((v['E9']-v['E21'])/v['E21']<-0.00015) & (v['R']>35)
        
        fig.add_trace(go.Scatter(x=v[v['b_sig']].index, y=v[v['b_sig']]['Low']*0.9998, mode='markers', marker=dict(symbol='triangle-up', size=8, color='lime')), row=1, col=1)
        fig.add_trace(go.Scatter(x=v[v['s_sig']].index, y=v[v['s_sig']]['High']*1.0002, mode='markers', marker=dict(symbol='triangle-down', size=8, color='red')), row=1, col=1)

        fig.add_trace(go.Scatter(x=v.index, y=v['R'], line=dict(color='#00d4ff', width=1)), row=2, col=1)
        fig.update_layout(height=850, margin=dict(l=0, r=0, t=0, b=0), template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
