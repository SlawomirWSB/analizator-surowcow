import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja i Auto-odświeżanie
st.set_page_config(layout="wide", page_title="PRO Analizator")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Optymalizacja pod telefon i czytelność
st.markdown("""
    <style>
    .block-container { padding: 0.1rem 0.2rem !important; }
    header { visibility: hidden; }
    .top-info {
        background: #1e1e1e; padding: 5px 10px; border-radius: 4px;
        margin-bottom: 5px; border-left: 4px solid #f39c12;
        display: flex; justify-content: space-between; align-items: center;
    }
    .instr-name { font-size: 1rem; color: #f39c12; font-weight: bold; }
    .metric-text { font-size: 0.9rem; color: white; font-weight: bold; }
    .status-badge { padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

def get_rsi(prices, n=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=n).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Baza instrumentów
DB = {
    "Metale": {"Złoto": "GC=F", "Srebro": "SI=F", "Miedź": "HG=F"},
    "Krypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Indeksy": {"DAX": "^GDAXI", "SP500": "^GSPC", "NASDAQ": "^IXIC"}
}

def main():
    # --- MENU BOCZNE (Sidebar po prawej/lewej steruje Streamlit) ---
    st.sidebar.header("USTAWIENIA")
    kat = st.sidebar.selectbox("Kategoria", list(DB.keys()))
    inst_name = st.sidebar.selectbox("Instrument", list(DB[kat].keys()))
    itv = st.sidebar.selectbox("Interwał", ["1m", "5m", "15m", "1h", "1d"], index=2)
    show_signals = st.sidebar.checkbox("Pokaż trójkąty sygnałów", value=True)
    
    symbol = DB[kat][inst_name]

    try:
        # Pobieranie danych
        df = yf.download(symbol, period="5d", interval=itv, progress=False)
        if df.empty:
            st.warning("Brak danych dla tego instrumentu.")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['RSI'] = get_rsi(df['Close'])
        df.dropna(inplace=True)

        v = df.tail(70).copy()
        curr = v.iloc[-1]
        prev = v.iloc[-2]
        
        # Logika sygnału
        diff = (curr['EMA9'] - curr['EMA21']) / curr['EMA21']
        is_trend = abs(diff) > 0.00015
        buy = (curr['EMA9'] > curr['EMA21']) and (curr['RSI'] < 65) and is_trend and (curr['EMA21'] > prev['EMA21'])
        sel = (curr['EMA9'] < curr['EMA21']) and (curr['RSI'] > 35) and is_trend and (curr['EMA21'] < prev['EMA21'])

        # --- NOWY PASEK INFORMACYJNY ---
        s_bg = "#28a745" if buy else ("#dc3545" if sel else "#444")
        s_txt = "KUPNO" if buy else ("SPRZEDAŻ" if sel else "CZEKAJ")
        
        st.markdown(f"""
            <div class="top-info">
                <div class="instr-name">{inst_name.upper()} ({itv})</div>
                <div class="metric-text">Cena: {curr['Close']:.2f} | RSI: {curr['RSI']:.0f}</div>
                <div class="status-badge" style="background:{s_bg}; color:white;">{s_txt}</div>
            </div>
            """, unsafe_allow_html=True)

        # --- WYKRES ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.85, 0.15])
        
        # Świece i EMA
        fig.add_trace(go.Candlestick(x=v.index, open=v['Open'], high=v['High'], low=v['Low'], close=v['Close'], name="Cena"), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['EMA9'], line=dict(color='orange', width=1.2), name="EMA9"), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['EMA21'], line=dict(color='purple', width=1.2), name="EMA21"), row=1, col=1)

        # Sygnały (Trójkąty)
        if show_signals:
            v['b_sig'] = (v['EMA9']>v['EMA21']) & ((v['EMA9']-v['EMA21'])/v['EMA21']>0.00015) & (v['RSI']<65)
            v['s_sig'] = (v['EMA9']<v['EMA21']) & ((v['EMA9']-v['EMA21'])/v['EMA21']<-0.00015) & (v['RSI']>35)
            
            fig.add_trace(go.Scatter(x=v[v['b_sig']].index, y=v[v['b_sig']]['Low']*0.9997, mode='markers', marker=dict(symbol='triangle-up', size=10, color='lime'), name="BUY"), row=1, col=1)
            fig.add_trace(go.Scatter(x=v[v['s_sig']].index, y=v[v['s_sig']]['High']*1.0003, mode='markers', marker=dict(symbol='triangle-down', size=10, color='red'), name="SELL"), row=1, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=v.index, y=v['RSI'], line=dict(color='#00d4ff', width=1.5), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.3, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.3, row=2, col=1)

        # Formatowanie osi i usuwanie luk
        fig.update_xaxes(type='category') # To wymusza równe odstępy między świecami (naprawia "pływanie")
        fig.update_layout(height=800, margin=dict(l=0, r=0, t=5, b=0), template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Wystąpił błąd podczas ładowania: {e}")

if __name__ == "__main__":
    main()
