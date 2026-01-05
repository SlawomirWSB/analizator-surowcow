# --- POPRAWIONY WYKRES ŚWIECZKOWY ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
            
            # Główne świece (Candlestick)
            fig.add_trace(go.Candlestick(
                x=df.index, 
                open=df['Open'], 
                high=df['High'], 
                low=df['Low'], 
                close=df['Close'], 
                name='Cena',
                increasing_line_color='#00ff00', # Wyraźny zielony dla wzrostów
                decreasing_line_color='#ff0000'  # Wyraźny czerwony dla spadków
            ), row=1, col=1)
            
            # Linie średnich EMA
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], line=dict(color='orange', width=1.5), name='EMA9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], line=dict(color='purple', width=1.5), name='EMA21'), row=1, col=1)
            
            # Znaczniki sygnałów (Trójkąty)
            if show_markers:
                buys = df[df['Buy_Tag']]
                sells = df[df['Sell_Tag']]
                fig.add_trace(go.Scatter(x=buys.index, y=buys['Low']*0.999, mode='markers', marker=dict(symbol='triangle-up', size=12, color='lime'), name='Kupno'), row=1, col=1)
                fig.add_trace(go.Scatter(x=sells.index, y=sells['High']*1.001, mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name='Sprzedaż'), row=1, col=1)

            # RSI na dolnym wykresie
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#00d4ff', width=2)), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

            # Wyłączenie suwaka na dole, który zabiera miejsce
            fig.update_layout(xaxis_rangeslider_visible=False)
