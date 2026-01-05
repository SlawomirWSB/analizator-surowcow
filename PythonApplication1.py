# --- WYMUSZENIE CZYTELNYCH ŚWIEC ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # Candlestick z wymuszoną grubością linii
            fig.add_trace(go.Candlestick(
                x=view_df.index,
                open=view_df['Open'],
                high=view_df['High'],
                low=view_df['Low'],
                close=view_df['Close'],
                name='Cena',
                increasing_line_color='#26a69a', 
                decreasing_line_color='#ef5350',
                increasing_fillcolor='#26a69a', # Wypełnienie kolorem
                decreasing_fillcolor='#ef5350', # Wypełnienie kolorem
                line=dict(width=1.5) # Wymuszona grubość, by nie była to tylko nitka
            ), row=1, col=1)
            
            # Usunięcie efektu "linii" poprzez ograniczenie trybu wyświetlania
            fig.update_layout(
                height=500, 
                margin=dict(l=5, r=5, t=5, b=5),
                template="plotly_dark", 
                xaxis_rangeslider_visible=False, 
                showlegend=False,
                hovermode='x unified'
            )
            
            # Wymuszenie stałego dystansu między świecami (zapobiega zlewaniu się w linię)
            fig.update_xaxes(type='date', row=1, col=1)
