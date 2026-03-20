import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- CONFIGURATION ---
# Ensure these match the output names in analytics.py
INPUT_REPORT_CSV = 'report_finale.csv'
INPUT_STOCKS_CSV = 'stocks_profit.csv'
OUTPUT_HTML = 'dashboard.html'
CSS_FILE = 'style.css'

# Colors
BG_COLOR = '#1e1e1e' 
GRID_COLOR = '#333333'
GREEN_ACCENT = '#81c784'
RED_ACCENT = '#e57373'
LINE_ACCENT = '#4db6ac'
AVG_ACCENT = '#ffb74d'

# 1. Load reports
if not os.path.exists(INPUT_REPORT_CSV) or not os.path.exists(INPUT_STOCKS_CSV):
    print(f"Error: {INPUT_REPORT_CSV} or {INPUT_STOCKS_CSV} not found.")
    print("Please run the analytics script first.")
    exit()

df = pd.read_csv(INPUT_REPORT_CSV)
df_stocks = pd.read_csv(INPUT_STOCKS_CSV)

# Ensure the date column matches the English name from analytics.py
df['Date'] = pd.to_datetime(df['Date'])

# 2. Create Dashboard with 4 ROWS
fig = make_subplots(
    rows=4, cols=1,
    shared_xaxes=False, # 4th chart uses Tickers (categories), not Dates
    vertical_spacing=0.07,
    subplot_titles=(
        "Total Cumulative Wealth (€)", 
        "Daily Profit/Loss (€)", 
        "Progressive Average Trend (€)",
        "Net Profit per Stock (€) - Hover for Full Name"
    )
)

# --- TRACE 1: Total Cumulative ---
fig.add_trace(go.Scatter(
    x=df['Date'], 
    y=df['Cumulative_Total'], 
    fill='tozeroy', 
    name='Total', 
    line=dict(color=LINE_ACCENT)
), row=1, col=1)

# --- TRACE 2: Daily Gain ---
daily_colors = [RED_ACCENT if x < 0 else GREEN_ACCENT for x in df['Daily_Gain']]
fig.add_trace(go.Bar(
    x=df['Date'], 
    y=df['Daily_Gain'], 
    marker_color=daily_colors, 
    name='Daily'
), row=2, col=1)

# --- TRACE 3: Progressive Average ---
fig.add_trace(go.Scatter(
    x=df['Date'], 
    y=df['Progressive_Average'], 
    name='Average', 
    line=dict(color=AVG_ACCENT, width=3)
), row=3, col=1)

# --- TRACE 4: Profit per Stock ---
stock_colors = [RED_ACCENT if x < 0 else GREEN_ACCENT for x in df_stocks['Result']]
fig.add_trace(go.Bar(
    x=df_stocks['Ticker'], 
    y=df_stocks['Result'],
    marker_color=stock_colors,
    name='Stock Profit',
    # CUSTOM TOOLTIP using customdata for full name
    hovertemplate="<b>Ticker:</b> %{x}<br><b>Name:</b> %{customdata}<br><b>Profit:</b> %{y:,.2f} €<extra></extra>",
    customdata=df_stocks['Name']
), row=4, col=1)

# General Y-axis config
fig.update_yaxes(showgrid=True, gridcolor=GRID_COLOR)

# Specific X-axis config for first 3 charts (Dates)
for i in range(1, 4):
    fig.update_xaxes(
        type='date', 
        tickformat='%m-%d-%y', 
        tickangle=-90, 
        gridcolor=GRID_COLOR, 
        row=i, col=1,
        rangebreaks=[dict(bounds=["sat", "mon"])] # Hide weekends
    )

# Specific X-axis config for 4th chart (Tickers)
fig.update_xaxes(type='category', row=4, col=1)

# Layout settings
fig.update_layout(
    height=1300, 
    autosize=True,
    template="plotly_dark",
    paper_bgcolor=BG_COLOR,
    plot_bgcolor=BG_COLOR,
    showlegend=False,
    hovermode="x unified",
    margin=dict(t=80, b=120, l=60, r=40)
)

# Apply nticks and minor grid to the first 3 time-based charts
for i in range(1, 4):
    fig.update_xaxes(
        nticks=20, 
        minor=dict(tickvals=df['Date'], showgrid=True, gridwidth=0.5, gridcolor='#2a2a2a'), 
        row=i, col=1
    )

# 3. SAVE TO HTML
try:
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html>\n<html>\n<head>\n')
        f.write('    <meta charset="utf-8">\n')
        f.write(f'    <title>Investment Analysis Dashboard</title>\n')
        f.write(f'    <link rel="stylesheet" href="{CSS_FILE}">\n')
        f.write('</head>\n<body>\n')
        f.write('    <div class="dashboard-container">\n')
        f.write(fig.to_html(full_html=False, include_plotlyjs='cdn', config={'responsive': True}))
        f.write('    </div>\n')
        f.write('</body>\n</html>')
    print(f"Dashboard generated successfully in {OUTPUT_HTML}")
except Exception as e:
    print(f"Error saving dashboard: {e}")