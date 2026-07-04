import streamlit as st
import pandas as pd
import plotly.express as px
from backend.queries import get_kpi_metrics, get_detailed_pl, get_asset_allocation, get_daily_pl
from theme_manager import inject_theme_sidebar

st.set_page_config(
    page_title="Trading 212 Analytics", 
    page_icon="📈", 
    layout="wide"
)

TEMA_ATTIVO = inject_theme_sidebar()

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .main div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)
    
st.title("Trading 212 Analytics")
st.caption(f"Real-time portfolio management powered by PostgreSQL • Active theme: {st.session_state.tema_scelto}")
st.markdown("---")

try:
    net_invested, total_interest = get_kpi_metrics()
    capital_gain, total_dividends = get_detailed_pl()
except Exception as e:
    st.error(f"Error retrieving KPI data: {e}")
    net_invested, total_interest, capital_gain, total_dividends = 0, 0, 0, 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Net Invested Capital", value=f"€{net_invested:,.2f}")
with col2:
    st.metric(label="Total Cash Interest", value=f"€{total_interest:,.2f}")
with col3:
    cg_pct = (capital_gain / net_invested * 100) if net_invested > 0 else 0.0
    st.metric(
        label="Capital Gain", 
        value=f"€{capital_gain:,.2f}", 
        delta=f"{cg_pct:+.2f}%",
        delta_color="normal" if capital_gain >= 0 else "inverse"
    )
with col4:
    st.metric(label="Total Dividends Received", value=f"€{total_dividends:,.2f}")

st.markdown("---")

graph_col1, graph_col2 = st.columns([1, 1])

with graph_col1:
    st.subheader("Asset Allocation")
    try:
        allocation_df = get_asset_allocation()
        if not allocation_df.empty:
            df_pie = allocation_df[allocation_df['asset_value'] > 10].copy()
            
            total_portfolio = df_pie['asset_value'].sum()
            df_pie['percentage'] = (df_pie['asset_value'] / total_portfolio) * 100
            
            percentage_threshold = 1.5
            large_holdings = df_pie[df_pie['percentage'] >= percentage_threshold].copy()
            small_holdings = df_pie[df_pie['percentage'] < percentage_threshold].copy()
            
            if not small_holdings.empty:
                others_row = pd.DataFrame([{
                    'ticker': 'Others',
                    'asset_value': small_holdings['asset_value'].sum(),
                    'percentage': small_holdings['percentage'].sum()
                }])
                df_pie = pd.concat([large_holdings, others_row], ignore_index=True)
            
            fig_pie = px.pie(
                df_pie, 
                values='asset_value', 
                names='ticker',      
                hole=0.4,
                template="plotly_dark",
                color_discrete_sequence=TEMA_ATTIVO["palette_pie"]
            )
            
            fig_pie.update_traces(
                textinfo='percent+label', 
                textposition='inside',
                insidetextorientation='radial',
                marker=dict(line=dict(color='#0e1117', width=2))
            )
            
            fig_pie.update_layout(
                margin=dict(t=20, b=20, l=20, r=20), 
                showlegend=True, 
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No asset allocation data available.")
    except Exception as e:
        st.error(f"Error rendering Asset Allocation chart: {e}")

with graph_col2:
    st.subheader("Monthly Performance History (Last 12 Months)")
    try:
        daily_pl_df = get_daily_pl()
        if not daily_pl_df.empty:
            daily_pl_df['date'] = pd.to_datetime(daily_pl_df['date'])
            
            current_time = pd.Timestamp.now()
            one_year_ago = (current_time - pd.DateOffset(months=11)).replace(day=1)
            
            month_range = pd.period_range(start=one_year_ago.to_period('M'), end=current_time.to_period('M'), freq='M')
            
            rolling_df = daily_pl_df[daily_pl_df['date'] >= one_year_ago].copy()
            
            if not rolling_df.empty:
                rolling_df['year_month'] = rolling_df['date'].dt.to_period('M')
                monthly_df = rolling_df.groupby('year_month')['net_daily_volume'].sum().reset_index()
                
                monthly_df = monthly_df.set_index('year_month').reindex(month_range, fill_value=0.0).reset_index()
                monthly_df.columns = ['year_month', 'net_daily_volume']
                
                monthly_df['month_label'] = monthly_df['year_month'].dt.strftime('%b %y')
                
                fig_bar = px.bar(
                    monthly_df,
                    x='month_label',
                    y='net_daily_volume',
                    template="plotly_dark",
                    labels={'net_daily_volume': 'Net Volume (€)', 'month_label': 'Month'}
                )
                fig_bar.update_xaxes(type='category')
                fig_bar.update_traces(marker_color=TEMA_ATTIVO["colore_barre"])
                fig_bar.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=450)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No data available for the last 12 months.")
        else:
            st.info("No historical monthly data available.")
    except Exception as e:
        st.error(f"Error rendering Monthly Performance chart: {e}")