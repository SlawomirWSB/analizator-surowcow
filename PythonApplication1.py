import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja mobilna
st.set_page_config(layout="wide", page_title="Trader Mobile")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Maksymalna redukcja marginesów i stylizacja XTB
st.markdown("""
    <style>
    .block-container { padding: 0rem !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    
    /* Wąski pasek górny a'la XTB */
    .xtb-bar {
        background: #000; padding: 10px 15px;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #222; position: sticky; top: 0; z-index: 1000;
    }
    .xtb-title { color: #FFB400; font-size: 16px; font-weight: bold; }
    .xtb-price { color: #FFF; font-size: 16px; font-family: monospace; }
    .xtb-status { 
        padding: 4px 10px; border-radius: 2px; font-size: 12px; font-weight: bold;
    }
    
    /* Stylizacja menu na dole */
    .stExpander { border: none !important; background: #111 !important; }
    </style>
    """, unsafe_allow_html=True)

def get_rsi(prices, n=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=n).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

DB = {
    "Surowce": {"Kakao": "CC=F", "Złoto": "GC=F", "Srebro": "SI=F", "Ropa": "CL=F"},
    "Krypto": {"BTC": "BTC-USD", "ETH": "ETH-USD"},
    "Indeksy": {"DAX": "^GDAXI", "SP500": "^GSPC"}
}

def main():
    # MENU na dole strony w formie expandera (oszczędność miejsca)
    with st.expander("📊 Zmień instrument / Interwał"):
        c1, c2, c3 = st.columns(3)
        kat = c1.selectbox("Rynek", list(DB.keys()), label_visibility="collapsed")
        inst = c2.selectbox("Instrument", list(DB[kat].keys()), label_visibility="collapsed")
        itv = c3.selectbox("Interwał", ["1m", "5m", "15m", "1h", "1d"], index=2, label_visibility="collapsed")
        show_signals = st.toggle("Sygnały", value=True)

    symbol = DB[kat][inst]

    try:
        # Pobieranie danych
        df = yf.download(symbol, period="5d", interval=itv, progress=False)
        if df.empty: return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['E9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['E21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['R'] = get_rsi(df['Close'])
        
        v = df.tail(60).copy()
        curr = v.iloc[-1]
        
        # Logika sygnału (uproszczona pod mobile)
        buy = (curr['E9'] > curr['E21']) and (curr['R'] < 65)
        sel = (curr['E9'] < curr['E21']) and (curr['R'] > 35)

        # --- PASEK GÓRNY XTB ---
        s_bg = "#28a745" if buy else ("#dc3545" if sel else "#333")
        s_txt = "KUP" if buy else ("SPRZEDAJ" if sel else "NEUTRAL")
        
        st.markdown(f"""
            <div class="xtb-bar">
                <div class="xtb-title">{inst.upper()} <span style="font-size:10px; color:#666;">{itv}</span></div>
                <div class="xtb-price">{curr['Close']:.2f}</div>
                <div class="xtb-status" style="background:{s_bg};">{s_txt}</div>
            </div>
            """, unsafe_allow_html=True)

        # --- WYKRES ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.8, 0.2])
        
        # Świece (cieńsze linie dla czytelności)
        fig.add_trace(go.Candlestick(
            x=v.index, open=v['Open'], high=v['High'], low=v['Low'], close=v['Close'],
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
            increasing_fillcolor='#26a69a', decreasing_fillcolor='#ef5350'
        ), row=1, col=1)
        
        # EMA (cieńsze linie)
        fig.add_trace(go.Scatter(x=v.index, y=v['E9'], line=dict(color='#FF9800', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['E21'], line=dict(color='#9C27B0', width=1)), row=1, col=1)

        if show_signals:
            v['b'] = (v['E9'] > v['E21']) & (v['R'] < 65)
            v['s'] = (v['E9'] < v['E21']) & (v['R'] > 35)
            fig.add_trace(go.Scatter(x=v[v['b']].index, y=v[v['b']]['Low']*0.999, mode='markers', 
                                   marker=dict(symbol='triangle-up', size=8, color='#00FF00')), row=1, col=1)
            fig.add_trace(go.Scatter(x=v[v['s']].index, y=v[v['s']]['High']*1.001, mode='markers', 
                                   marker=dict(symbol='triangle-down', size=8, color='#FF0000')), row=1, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=v.index, y=v['R'], line=dict(color='#2196F3', width=1.5)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#333", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#333", row=2, col=1)

        # Konfiguracja osi i gestów
        fig.update_xaxes(type='category', showgrid=False, zeroline=False, rangeslider_visible=False)
        fig.update_yaxes(showgrid=True, gridcolor='#111', side="right") # Cena po prawej jak w XTB
        
        fig.update_layout(
            height=700, margin=dict(l=0, r=0, t=0, b=0),
            template="plotly_dark", paper_bgcolor="black", plot_bgcolor="black",
            dragmode='pan', hovermode='x unified', showlegend=False
        )
        
        # KLUCZOWE: scrollZoom włącza pinch-to-zoom na mobile
        st.plotly_chart(fig, use_container_width=True, config={
            'scrollZoom': True, 
            'displayModeBar': False,
            'responsive': True
        })

    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
