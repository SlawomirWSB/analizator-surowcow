import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# 1. Konfiguracja strony i auto-odświeżanie (co 60 sekund)
st.set_page_config(layout="wide", page_title="PRO Analizator z Push")
st_autorefresh(interval=60 * 1000, key="data_refresh")

# Funkcja JavaScript do powiadomień systemowych (Push)
def send_browser_notification(title, body):
    js_code = f"""
    <script>
    function notifyMe() {{
      if (!("Notification" in window)) {{
        console.log("Brak obsługi powiadomień");
      }} else if (Notification.permission === "granted") {{
        new Notification("{title}", {{ 
            body: "{body}", 
            icon: "https://cdn-icons-png.flaticon.com/512/1991/1991047.png",
            vibrate: [200, 100, 200]
        }});
      }} else if (Notification.permission !== "denied") {{
        Notification.requestPermission();
      }}
    }}
    notifyMe();
    </script>
    """
    components.html(js_code, height=0)

# CSS dla czytelności mobilnej
st.markdown("""
    <style>
    .main-title { font-size: 1rem !important; font-weight: bold; margin-bottom: 0px; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    .stMetric { background: #1e2130; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def oblicz_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

RYNKI = {
    "Krypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"},
    "Metale": {"Złoto": "GC=F", "Srebro": "SI=F", "Miedź": "HG=F"},
    "Indeksy": {"DAX": "^GDAXI", "NASDAQ": "^IXIC", "SP500": "^GSPC"}
}

def main():
    st.sidebar.title("PRO Menu")
    
    # Przycisk inicjalizacji powiadomień (wymagany przez przeglądarki)
    if st.sidebar.button("🔔 Aktywuj Powiadomienia"):
        components.html("<script>Notification.requestPermission();</script>", height=0)
        st.sidebar.success("Przeglądarka zapyta o zgodę - kliknij Zezwól.")

    kat = st.sidebar.radio("Rynek:", list(RYNKI.keys()))
    inst = st.sidebar.selectbox("Instrument:", list(RYNKI[kat].keys()))
    inter_label = st.sidebar.selectbox("Interwał:", ["1 m", "5 m", "15 m", "1 h", "1 d"])
    alerty_on = st.sidebar.toggle("Włącz alerty Push", value=True)
    
    mapping = {"1 m": "1m", "5 m": "5m", "15 m": "15m", "1 h": "1h", "1 d": "1d"}
    interval = mapping[inter_label]

    try:
        df = yf.download(RYNKI[kat][inst], period="5d" if interval != "1d" else "max", interval=interval, progress=False)
        
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df[df['Open'] > 0].copy()
            df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['RSI'] = oblicz_rsi(df['Close'])
            df.dropna(inplace=True)

            v_df = df.tail(40).copy() # Mniej świec = większa czytelność na telefonie
            last_row = v_df.iloc[-1]

            # Nagłówek i statystyki
            st.markdown(f'<p class="main-title">{inst} ({inter_label})</p>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Cena", f"{last_row['Close']:.2f}")
            c2.metric("RSI", f"{last_row['RSI']:.1f}")

            # Logika Sygnałów
            if last_row['EMA9'] > last_row['EMA21'] and last_row['RSI'] < 70:
                c3.success("KUPNO")
                if alerty_on:
                    send_browser_notification(f"🟢 KUPNO: {inst}", f"Cena: {last_row['Close']:.2f} (RSI: {last_row['RSI']:.1f})")
            
            elif last_row['EMA9'] < last_row['EMA21'] and last_row['RSI'] > 30:
                c3.error("SPRZEDAŻ")
                if alerty_on:
                    send_browser_notification(f"🔴 SPRZEDAŻ: {inst}", f"Cena: {last_row['Close']:.2f} (RSI: {last_row['RSI']:.1f})")
            else:
                c3.warning("CZEKAJ")

            # Wykres Świecowy
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            fig.add_trace(go.Candlestick(
                x=v_df.index, open=v_df['Open'], high=v_df['High'], low=v_df['Low'], close=v_df['Close'],
                increasing_line_color='#26a69a', decreasing_line_color='#ef5350',
                increasing_fillcolor='#26a69a', decreasing_fillcolor='#ef5350',
                line=dict(width=1.5), name='Cena'
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['EMA9'], line=dict(color='orange', width=2), name='EMA9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['EMA21'], line=dict(color='purple', width=2), name='EMA21'), row=1, col=1)
            fig.add_trace(go.Scatter(x=v_df.index, y=v_df['RSI'], line=dict(color='#00d4ff', width=2)), row=2, col=1)

            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.3, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.3, row=2, col=1)

            fig.update_layout(height=500, margin=dict(l=5, r=5, t=5, b=5), template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.error(f"Błąd: {e}")

if __name__ == "__main__":
    main()
