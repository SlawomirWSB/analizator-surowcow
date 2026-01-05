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

# CSS - Optymalizacja paska i kontrolek
st.markdown("""
    <style>
    .block-container { padding: 0.1rem 0.2rem !important; }
    header { visibility: hidden; }
    .top-bar {
        display: flex; justify-content: space-between; align-items: center;
        background: #1a1c24; padding: 4px 8px; border-radius: 4px;
        border: 1px solid #3e414f; margin-bottom: 2px;
    }
    .metric-box { display: flex; flex-direction: column; }
    .m-label { font-size: 0.5rem; color: #8a8d97; line-height: 1; }
    .m-value { font-size: 0.8rem; color: white; font-weight: bold; }
    .status-tag { font-size: 0.65rem; font-weight: bold; padding: 2px 5px; border-radius: 3px; }
    
    /* Ukrycie Sidebar na mobile jeśli niepotrzebny */
    section[data-testid="stSidebar"] { width: 0px; }
    
    /* Stylizacja małych selectboxów */
    div[data-testid="stHorizontalBlock"] { gap: 4px !important; }
    .stSelectbox div[data-baseweb="select"] { min-height: 30px !important; }
    </style>
    """, unsafe_allow_html=True)

def get_rsi(prices, n=14):
    deltas = prices.diff()
    gains = deltas.where(deltas > 0, 0).rolling(window=n).mean()
    losses = (-deltas.where(deltas < 0, 0)).rolling(window=n).mean()
    rs = gains / losses
    return 100 - (100 / (1 + rs))

# Baza danych
DB = {
    "Metale": {"Złoto": "GC=F", "Srebro": "SI=F", "Miedź": "HG=F"},
    "Krypto": {"BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD"},
    "Indeksy": {"DAX": "^GDAXI", "NASDAQ": "^IXIC", "SP500": "^GSPC"}
}

def main():
    # --- PANEL KONTROLNY (ZAMIAST SIDEBARA) ---
    c_cat, c_inst, c_itv = st.columns([1, 1, 1])
    with c_cat:
        kat = st.selectbox("Rynek", list(DB.keys()), label_visibility="collapsed")
    with c_inst:
        inst = st.selectbox("Instrument", list(DB[kat].keys()), label_visibility="collapsed")
    with c_itv:
        itv_label = st.selectbox("Interwał", ["1m","5m","15m","1h","1d"], index=2, label_visibility="collapsed")

    c_opt1, c_opt2 = st.columns(2)
    with c_opt1:
        pokaz_syg = st.toggle("Sygnały", value=True)
    with c_opt2:
        alerty = st.toggle("Alerty", value=False)

    try:
        # Pobieranie danych
        df = yf.download(DB[kat][inst], period="5d", interval=itv_label, progress=False)
        if df.empty: return
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['E9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['E21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['R'] = get_rsi(df['Close'])
        df.dropna(inplace=True)

        v = df.tail(60).copy()
        curr = v.iloc[-1]
        prev = v.iloc[-2]
        
        # Logika sygnałów
        diff = (curr['E9'] - curr['E21']) / curr['E21']
        is_trend = abs(diff) > 0.00015
        buy = (curr['E9'] > curr['E21']) and (curr['R'] < 65) and is_trend and (curr['E21'] > prev['E21'])
        sel = (curr['E9'] < curr['E21']) and (curr['R'] > 35) and is_trend and (curr['E21'] < prev['E21'])

        # --- GÓRNY PASEK METRYK ---
        s_color = "#28a745" if buy else ("#dc3545" if sel else "#444")
        s_text = "KUPNO" if buy else ("SPRZEDAŻ" if sel else "CZEKAJ")
        
        st.markdown(f"""
            <div class="top-bar">
                <div class="metric-box"><span class="m-label">CENA</span><span class="m-value">{curr['Close']:.1f}</span></div>
                <div class="metric-box"><span class="m-label">RSI</span><span class="m-value">{curr['R']:.0f}</span></div>
                <div class="status-tag" style="background:{s_color}; color:white;">{s_text}</div>
            </div>
            """, unsafe_allow_html=True)

        # --- WYKRES ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.85, 0.15])
        
        # Świece i EMA
        fig.add_trace(go.Candlestick(x=v.index, open=v['Open'], high=v['High'], low=v['Low'], close=v['Close']), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E9'], line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E21'], line=dict(color='purple', width=1)), row=1, col=1)

        # Trójkąty sygnałów
        if pokaz_syg:
            v['b_sig'] = (v['E9']>v['E21']) & ((v['E9']-v['E21'])/v['E21']>0.00015) & (v['R']<65)
            v['s_sig'] = (v['E9']<v['E21']) & ((v['E9']-v['E21'])/v['E21']<-0.00015) & (v['R'] > 35)
            
            fig.add_trace(go.Scatter(x=v[v['b_sig']].index, y=v[v['b_sig']]['Low']*0.9998, 
                                   mode='markers', marker=dict(symbol='triangle-up', size=9, color='lime')), row=1, col=1)
            fig.add_trace(go.Scatter(x=v[v['s_sig']].index, y=v[v['s_sig']]['High']*1.0002, 
                                   mode='markers', marker=dict(symbol='triangle-down', size=9, color='red')), row=1, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=v.index, y=v['R'], line=dict(color='#00d4ff', width=1)), row=2, col=1)

        fig.update_layout(height=700, margin=dict(l=0, r=0, t=0, b=0), template="plotly_dark", 
                          xaxis_rangeslider_visible=False, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
