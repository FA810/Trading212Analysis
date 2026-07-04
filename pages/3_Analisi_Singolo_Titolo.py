import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from backend.queries import run_query, calculate_ticker_timeline
from theme_manager import inject_theme_sidebar

st.set_page_config(layout="wide")
TEMA_ATTIVO = inject_theme_sidebar()
st.title("Historical Timeline of Realized Sales")
st.markdown("---")

try:
    tickers_df = run_query("SELECT DISTINCT ticker FROM stock_transactions WHERE ticker IS NOT NULL ORDER BY ticker;")
    if not tickers_df.empty:
        selected_ticker = st.selectbox("Select stock to analyze:", tickers_df['ticker'].tolist())
        
        if selected_ticker:
            history_data = calculate_ticker_timeline(selected_ticker)
            if history_data:
                df_timeline = pd.DataFrame(history_data)
                df_timeline['date'] = pd.to_datetime(df_timeline['date']).dt.date
                df_sales = df_timeline[df_timeline['pnl'] != 0].copy()
                
                if not df_sales.empty:
                    df_daily_pnl = df_sales.groupby('date')['pnl'].sum().reset_index().sort_values('date')
                    
                    # Assign bar colors based on positive or negative PnL using theme preferences
                    df_daily_pnl['color'] = df_daily_pnl['pnl'].apply(
                        lambda x: TEMA_ATTIVO["colore_barre"] if x > 0 else TEMA_ATTIVO["colore_perdita"]
                    )
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=df_daily_pnl['date'], 
                        y=df_daily_pnl['pnl'],
                        marker_color=df_daily_pnl['color'],
                        text=df_daily_pnl['pnl'].apply(lambda x: f"{x:+.2f}€"),
                        textposition='auto'
                    ))
                    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.metric(label="Total Realized Net Profit", value=f"€{df_daily_pnl['pnl'].sum():,.2f}")
except Exception as e:
    st.error(f"Timeline error: {e}")