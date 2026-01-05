import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja
st.set_page_config(layout="wide", page_title="PRO Trader Mobile")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Optymalizacja pod czysty widok z chowanym menu
st.markdown("""
    <style>
    .block-container { padding: 0.1rem 0.2rem !important; }
    header { visibility: hidden; }
    .top-bar {
        display: flex; justify-content: space-between; align-items: center;
        background: #111; padding: 5px 10px; border-bottom: 1px solid #333;
    }
    .m-item { display: flex; flex-direction: column; }
    .m-l { font-size: 0.55rem; color: #777; }
    .m-v { font-size: 0.9rem; color: #fff; font-weight: bold; }
    .status { font-size: 0.7rem; padding: 2px 6px; border-radius: 3px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def get_rsi(prices, n=14):
    deltas = prices.diff()
    gains = deltas.where(deltas > 0, 0).rolling(window=n).mean()
    losses = (-deltas.where(deltas < 0, 0)).rolling(window=n).mean()
    rs = gains / losses
    return 100 - (100 / (1 + rs))

DB = {
    "Metale": {"Złoto": "GC=F", "Srebro": "SI=F", "Miedź": "HG=F"},
    "Krypto": {"BTC": "BTC-USD", "ETH": "ETH-USD"},
    "Indeksy": {"DAX": "^GDAXI", "SP500": "^GSPC"}
}

def main():
    # --- SIDEBAR (Menu chowane) ---
    st.sidebar.title("Ustawienia")
    kat = st.sidebar.selectbox("Rynek", list(DB.keys()))
    inst = st.sidebar.selectbox("Instrument", list(DB[kat].keys()))
    itv = st.sidebar.selectbox("Interwał", ["1m","5m","15m","1h","1d"], index=2)
    show_s = st.sidebar.toggle("Pokaż sygnały", value=True)
    
    try:
        # Pobieranie danych (z ograniczeniem do ostatnich 100 świec dla czytelności)
        df = yf.download(DB[kat][inst], period="5d", interval=itv, progress=False)
        if df.empty: return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['E9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['E21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['R'] = get_rsi(df['Close'])
        df.dropna(inplace=True)

        v = df.tail(60).copy()
        c = v.iloc[-1]
        p = v.iloc[-2]
        
        # Logika
        diff = (c['E9'] - c['E21']) / c['E21']
        trend = abs(diff) > 0.00015
        buy = (c['E9'] > c['E21']) and (c['R'] < 65) and trend and (c['E21'] > p['E21'])
        sel = (c['E9'] < c['E21']) and (c['R'] > 35) and trend and (c['E21'] < p['E21'])

        # --- PASEK GÓRNY ---
        st.markdown(f"""
            <div class="top-bar">
                <div class="m-item"><span class="m-l">CENA</span><span class="m-v">{c['Close']:.1f}</span></div>
                <div class="m-item"><span class="m-l">RSI</span><span class="m-v">{c['R']:.0f}</span></div>
                <div class="status" style="background:{'#28a745' if buy else '#dc3545' if sel else '#333'}; color:white;">
                    {'KUPNO' if buy else 'SPRZEDAŻ' if sel else 'CZEKAJ'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- WYKRES ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.85, 0.15])
        
        # Główny wykres
        fig.add_trace(go.Candlestick(x=v.index, open=v['Open'], high=v['High'], low=v['Low'], close=v['Close'], name="Cena"), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E9'], line=dict(color='orange', width=1), name="EMA9"), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E21'], line=dict(color='purple', width=1), name="EMA21"), row=1, col=1)

        if show_s:
            v['b'] = (v['E9']>v['E21']) & ((v['E9']-v['E21'])/v['E21']>0.00015) & (v['R']<65)
            v['s'] = (v['E9']<v['E21']) & ((v['E9']-v['E21'])/v['E21']<-0.00015) & (v['R']>35)
            fig.add_trace(go.Scatter(x=v[v['b']].index, y=v[v['b']]['Low']*0.9995, mode='markers', marker=dict(symbol='triangle-up', size=10, color='lime'), name="B"), row=1, col=1)
            fig.add_trace(go.Scatter(x=v[v['s']].index, y=v[v['s']]['High']*1.0005, mode='markers', marker=dict(symbol='triangle-down', size=10, color='red'), name="S"), row=1, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=v.index, y=v['R'], line=dict(color='#00d4ff', width=1.5), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.3, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.3, row=2, col=1)

        fig.update_layout(height=800, margin=dict(l=0, r=0, t=5, b=0), template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])]) # Usuwa luki weekendowe
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Błąd danych: {e}")

if __name__ == "__main__":
    main()
