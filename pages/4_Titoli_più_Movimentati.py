import streamlit as st
import plotly.express as px
from backend.queries import get_most_traded_stocks
from theme_manager import inject_theme_sidebar

st.set_page_config(
    page_title="Trading 212 Analytics", 
    page_icon="📈", 
    layout="wide"
)
TEMA_ATTIVO = inject_theme_sidebar()
st.title("Trading Frequency Analysis")
st.markdown("---")

try:
    soglia_x = st.slider("Show stocks with minimum transactions:", min_value=1, max_value=50, value=30)
    df_moved = get_most_traded_stocks(min_transactions=soglia_x)
    
    if not df_moved.empty:
        # Sort dataframe descending for the data table representation
        df_moved = df_moved.sort_values(by='numero_transazioni', ascending=False).reset_index(drop=True)
        
        # Sort ascending for Plotly horizontal bar display order (highest values on top)
        df_grafico = df_moved.sort_values(by='numero_transazioni', ascending=True)
        
        fig_freq = px.bar(
            df_grafico,
            x='numero_transazioni',
            y='ticker',
            hover_data=['name'],
            orientation='h',
            template="plotly_dark",
            labels={'ticker': 'Ticker', 'numero_transazioni': 'Transaction Count'},
            text_auto=True
        )
        
        fig_freq.update_traces(
            marker_color=TEMA_ATTIVO["colore_barre"],
            textposition="outside"
        )
        
        fig_freq.update_layout(
            margin=dict(t=20, b=40, l=80, r=20), 
            height=150 + (len(df_grafico) * 30), 
            xaxis_title="Number of Operations",
            yaxis_title="",
            xaxis=dict(showticklabels=False), 
            yaxis=dict(tickangle=0)
        )
        
        st.plotly_chart(fig_freq, use_container_width=True)
        
        st.markdown("### Transaction Details")
        st.dataframe(df_moved, use_container_width=True, hide_index=True)
        
    else:
        st.info("No stocks match the selected transaction criteria.")
        
except Exception as e:
    st.error(f"Frequency analysis error: {e}")