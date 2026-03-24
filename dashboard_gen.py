import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- CONFIGURATION ---
INPUT_REPORT_CSV = 'final_report.csv'
INPUT_STOCKS_CSV = 'stocks_profit.csv'
OUTPUT_HTML = 'dashboard.html'
CSS_FILE = 'style.css'

# Cyberpunk Palette
BG_COLOR = '#0b0e11'
GRID_COLOR = '#23272e'
GREEN_NEON = '#00ff88' 
RED_NEON = '#ff3366'   
CYAN_LINE = '#00d4ff'  
GOLD_AVG = '#ffcc00'   

def generate_dashboard():
    if not os.path.exists(INPUT_REPORT_CSV) or not os.path.exists(INPUT_STOCKS_CSV):
        print(f"Error: Required files ({INPUT_REPORT_CSV}/{INPUT_STOCKS_CSV}) missing.")
        return

    df = pd.read_csv(INPUT_REPORT_CSV)
    df_stocks = pd.read_csv(INPUT_STOCKS_CSV)
    df['Date'] = pd.to_datetime(df['Date'])

    # 2. Setup Subplots
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.12, 
        subplot_titles=(
            "TOTAL CUMULATIVE WEALTH (€)", 
            "DAILY PROFIT / LOSS (€)", 
            "PROGRESSIVE PERFORMANCE AVG (€)",
            "REALIZED PROFIT BY TICKER (€)"
        )
    )

    # --- TRACES ---
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['Cumulative_Total'], 
        fill='tozeroy', name='Wealth', 
        line=dict(color=CYAN_LINE, width=3),
        fillcolor='rgba(0, 212, 255, 0.1)'
    ), row=1, col=1)

    colors = [RED_NEON if x < 0 else GREEN_NEON for x in df['Daily_Gain']]
    fig.add_trace(go.Bar(
        x=df['Date'], y=df['Daily_Gain'], 
        marker_color=colors, name='Daily P&L'
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['Progressive_Average'], 
        name='Avg Trend', 
        line=dict(color=GOLD_AVG, width=4, dash='dot')
    ), row=3, col=1)

    stock_colors = [RED_NEON if x < 0 else GREEN_NEON for x in df_stocks['Result']]
    fig.add_trace(go.Bar(
        x=df_stocks['Ticker'], y=df_stocks['Result'],
        marker_color=stock_colors,
        customdata=df_stocks['Name'],
        hovertemplate="<b>%{x}</b><br>%{customdata}<br>Profit: %{y:,.2f} €<extra></extra>"
    ), row=4, col=1)

    # 3. Styling & Layout - FONT UPDATED TO MONTSERRAT
    fig.update_layout(
        height=1600,
        autosize=True,
        template="plotly_dark",
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        showlegend=False,
        margin=dict(t=100, b=100, l=20, r=20),
        font=dict(family="Montserrat, sans-serif", color="#e0e0e0")
    )

    for i in range(1, 4):
        fig.update_xaxes(
            type='date', tickformat='%b %d', tickangle=-45,
            gridcolor=GRID_COLOR, row=i, col=1,
            rangebreaks=[dict(bounds=["sat", "mon"])]
        )
        fig.update_xaxes(
            minor=dict(tickvals=df['Date'], showgrid=True, gridwidth=0.5, gridcolor='#1a1a1a'), 
            row=i, col=1
        )

    fig.update_xaxes(type='category', row=4, col=1)
    fig.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, zerolinecolor="#555")

    # 4. HTML Generation with Google Fonts Import
    try:
        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write('<!DOCTYPE html><html><head><meta charset="utf-8">')
            # Import Montserrat from Google Fonts
            f.write('<link rel="preconnect" href="https://fonts.googleapis.com">')
            f.write('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
            f.write('<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">')
            f.write(f'<title>TERMINAL | Trading Dashboard</title>')
            f.write(f'<link rel="stylesheet" href="{CSS_FILE}">')
            f.write('</head><body><div class="dashboard-container">')
            f.write(fig.to_html(full_html=False, include_plotlyjs='cdn', config={'responsive': True}))
            f.write('</div></body></html>')
        print(f"Dashboard deployed to {OUTPUT_HTML}")
    except Exception as e:
        print(f"Deployment failed: {e}")

if __name__ == "__main__":
    generate_dashboard()