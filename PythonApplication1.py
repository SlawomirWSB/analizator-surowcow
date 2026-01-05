import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# 1. Konfiguracja i Auto-odświeżanie
st.set_page_config(layout="wide", page_title="PRO Trader")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# CSS - Optymalizacja paska i menu
st.markdown("""
    <style>
    .block-container { padding: 0.1rem 0.2rem !important; }
    header { visibility: hidden; }
    .top-info {
        background: #1e1e1e; padding: 8px 12px; border-radius: 4px;
        margin-bottom: 5px; border-bottom: 2px solid #f39c12;
        display: flex; justify-content: space-between; align-items: center;
    }
    .instr-label { font-size: 1.1rem; color: #f39c12; font-weight: bold; }
    .price-label { font-size: 1rem; color: white; font-weight: bold; }
    .status-tag { padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
    
    /* Stylizacja menu bocznego */
    section[data-testid="stSidebar"] {
        background-color: #111 !important;
        min-width: 250px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def get_rsi(prices, n=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=n).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Baza danych
DB = {
    "Metale": {"Złoto": "GC=F", "Srebro": "SI=F", "Miedź": "HG=F"},
    "Krypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Indeksy": {"DAX": "^GDAXI", "SP500": "^GSPC", "NASDAQ": "^IXIC"}
}

def main():
    # --- MENU BOCZNE (SIDEBAR) ---
    # Tutaj znajdują się wszystkie opcje zmiany
    with st.sidebar:
        st.title("PRO Menu")
        st.markdown("---")
        kat = st.selectbox("Wybierz Rynek:", list(DB.keys()))
        inst_name = st.selectbox("Wybierz Instrument:", list(DB[kat].keys()))
        itv = st.selectbox("Interwał czasowy:", ["1m", "5m", "15m", "1h", "1d"], index=2)
        st.markdown("---")
        show_signals = st.toggle("Pokaż sygnały (trójkąty)", value=True)
        st.markdown("---")
        st.info("Menu możesz schować strzałką w lewym górnym rogu.")

    symbol = DB[kat][inst_name]

    try:
        # Pobieranie danych
        df = yf.download(symbol, period="5d", interval=itv, progress=False)
        if df.empty:
            st.error("Brak połączenia z giełdą. Spróbuj zmienić interwał.")
            return

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df[df['Open'] > 0].copy()
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['RSI'] = get_rsi(df['Close'])
        df.dropna(inplace=True)

        v = df.tail(80).copy()
        curr = v.iloc[-1]
        prev = v.iloc[-2]
        
        # Logika sygnału
        diff = (curr['EMA9'] - curr['EMA21']) / curr['EMA21']
        buy = (curr['EMA9'] > curr['EMA21']) and (curr['RSI'] < 65) and (abs(diff) > 0.00015)
        sel = (curr['EMA9'] < curr['EMA21']) and (curr['RSI'] > 35) and (abs(diff) > 0.00015)

        # --- GÓRNY PASEK ---
        st.markdown(f"""
            <div class="top-info">
                <div class="instr-label">{inst_name.upper()} ({itv})</div>
                <div class="price-label">Cena: {curr['Close']:.2f} | RSI: {curr['RSI']:.0f}</div>
                <div class="status-tag" style="background:{'#28a745' if buy else '#dc3545' if sel else '#444'}; color:white;">
                    {'KUPNO' if buy else 'SPRZEDAŻ' if sel else 'CZEKAJ'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- WYKRES ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.85, 0.15])
        
        fig.add_trace(go.Candlestick(x=v.index, open=v['Open'], high=v['High'], low=v['Low'], close=v['Close'], name="Cena"), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['EMA9'], line=dict(color='orange', width=1.2), name="EMA9"), row=1, col=1)
        fig.add_trace(go.Scatter(x=v.index, y=v['EMA21'], line=dict(color='purple', width=1.2), name="EMA21"), row=1, col=1)

        if show_signals:
            v['b_sig'] = (v['EMA9']>v['EMA21']) & (v['RSI']<65)
            v['s_sig'] = (v['EMA9']<v['EMA21']) & (v['RSI']>35)
            fig.add_trace(go.Scatter(x=v[v['b_sig']].index, y=v[v['b_sig']]['Low']*0.9997, mode='markers', marker=dict(symbol='triangle-up', size=10, color='lime'), name="BUY"), row=1, col=1)
            fig.add_trace(go.Scatter(x=v[v['s_sig']].index, y=v[v['s_sig']]['High']*1.0003, mode='markers', marker=dict(symbol='triangle-down', size=10, color='red'), name="SELL"), row=1, col=1)

        fig.add_trace(go.Scatter(x=v.index, y=v['RSI'], line=dict(color='#00d4ff', width=1.5), name="RSI"), row=2, col=1)

        # Naprawa osi X (usuwanie dziur czasowych)
        fig.update_xaxes(type='category', nticks=10)
        fig.update_layout(height=800, margin=dict(l=0, r=0, t=5, b=0), template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
