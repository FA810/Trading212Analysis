import pandas as pd
import numpy as np
import io
import os

# --- CONFIGURATION ---
DATA_FOLDER = 'exports'  # Folder containing your CSV files
REPORT_CSV = 'final_report.csv'
STOCKS_CSV = 'stocks_profit.csv'
TEXT_REPORT = 'report_readable.txt'

def clean_and_map_csv(file_path):
    """
    Reads a CSV, identifies its headers, and maps them to a Master Format.
    This handles different column orders and missing fields across different files.
    """
    master_order = [
        'Action', 'Time', 'ISIN', 'Ticker', 'Name', 'ID', 
        'No. of shares', 'Price / share', 'Result', 'Total'
    ]
    
    standardized_rows = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            header_line = f.readline().strip()
            # Handle potential BOM or weird encoding in headers
            current_headers = [h.strip().replace('"', '') for h in header_line.split(',')]
            
            standardized_rows.append(','.join(master_order))

            for line in f:
                if not line.strip(): continue
                
                # Split and map to dictionary
                parts = [p.strip().replace('"', '') for p in line.split(',')]
                row_dict = dict(zip(current_headers, parts))
                
                # Build row based on Master Order
                new_row = [row_dict.get(col, '') for col in master_order]
                standardized_rows.append(','.join(new_row))
        
        return pd.read_csv(io.StringIO('\n'.join(standardized_rows)))
    except Exception as e:
        print(f"Skipping {file_path} due to error: {e}")
        return None

def load_all_data(folder_path):
    """
    Scans the folder for CSVs and merges them into a single deduplicated DataFrame.
    """
    if not os.path.exists(folder_path):
        print(f"Creating folder: {folder_path}. Place your CSVs there and re-run.")
        os.makedirs(folder_path)
        exit(1)

    all_dfs = []
    files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    
    if not files:
        print(f"No CSV files found in '{folder_path}' folder.")
        exit(1)

    for file in files:
        full_path = os.path.join(folder_path, file)
        print(f"Processing: {file}")
        temp_df = clean_and_map_csv(full_path)
        if temp_df is not None:
            all_dfs.append(temp_df)
    
    # Merge all files
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Drop duplicates based on the Unique Order ID (prevents double counting)
    if 'ID' in combined_df.columns:
        initial_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['ID'])
        print(f"Removed {initial_count - len(combined_df)} duplicate transactions.")
        
    return combined_df

# --- MAIN EXECUTION ---

# 1. Load and Merge
df = load_all_data(DATA_FOLDER)

# 2. Standardize Types
df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
df = df.dropna(subset=['Time'])

for col in ['Result', 'Total']:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# 3. STOCK PERFORMANCE (Realized Profit)
# Filter for actual trades, excluding interest
df_stocks = df[df['Ticker'].notna() & (df['Action'] != 'Interest on cash')].copy()

stock_stats = df_stocks.groupby('Ticker').agg({
    'Result': 'sum',
    'Name': 'last'
}).sort_values('Result', ascending=False).reset_index()

stock_stats.to_csv(STOCKS_CSV, index=False)

# 4. DAILY PERFORMANCE
df['net_gain'] = df['Result']
df.loc[df['Action'] == 'Interest on cash', 'net_gain'] = df['Total']

df['Date'] = df['Time'].dt.date
daily_data = df.groupby('Date')['net_gain'].sum().reset_index()
daily_data['Date'] = pd.to_datetime(daily_data['Date'])

# Filter Weekends (Keep Mon-Fri)
daily_data = daily_data[daily_data['Date'].dt.weekday < 5].copy()

# Progressive Metrics
daily_data['Cumulative_Total'] = daily_data['net_gain'].cumsum()
daily_data['Progressive_Average'] = daily_data['net_gain'].expanding().mean()
daily_data = daily_data.round(2)

# 5. OUTPUT
print("\n" + "="*55)
print("   MULTI-FILE REALIZED PERFORMANCE SUMMARY   ")
print("="*55)
print(stock_stats[['Ticker', 'Result']].to_string(index=False, formatters={'Result': '{:,.2f} €'.format}))

# Rename and Save for Dashboard
daily_data.columns = ['Date', 'Daily_Gain', 'Cumulative_Total', 'Progressive_Average']
daily_data.to_csv(REPORT_CSV, index=False)

final_avg = round(daily_data['Daily_Gain'].mean(), 2)
with open(TEXT_REPORT, 'w') as f:
    f.write(daily_data.to_string(index=False) + f"\n\nGlobal Average (Weekdays): {final_avg} €")

print(f"\nAnalytics completed successfully. Daily Average: {final_avg} euro")