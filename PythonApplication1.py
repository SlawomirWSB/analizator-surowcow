# Poprawiona baza symboli (Darmowe i Stabilne w TradingView)
DB = {
    "ZŁOTO": {"yf": "GC=F", "tv": "OANDA:XAUUSD"},      # XAUUSD to standard dla Złota Spot
    "KAKAO": {"yf": "CC=F", "tv": "CAPITALCOM:COCOA"},  # Stabilne źródło CFD dla Kakao
    "BTC": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},  # Real-time z Binance
    "SREBRO": {"yf": "SI=F", "tv": "OANDA:XAGUSD"},     # Srebro Spot
    "DAX": {"yf": "^GDAXI", "tv": "GLOBALPRIME:GER30"}  # DAX jako CFD
}

# ... (reszta kodu bez zmian, ale upewnij się, że w widgecie jest ten fragment):

    # 4. Widget TradingView (Z poprawionym przesyłaniem symbolu)
    tv_widget = f"""
    <div id="tv_chart_container" style="height: 80vh;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({{
      "autosize": true,
      "symbol": "{DB[inst]['tv']}",
      "interval": "{itv}",
      "timezone": "Europe/Warsaw",
      "theme": "dark",
      "style": "1",
      "locale": "pl",
      "toolbar_bg": "#131722",
      "enable_publishing": false,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "container_id": "tv_chart_container"
    }});
    </script>
    """
