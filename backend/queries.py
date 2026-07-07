import pandas as pd
import psycopg2
import os

# Load .env file if present (useful for local development outside Docker environments)
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

# Dynamic database network host/port setup variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Validate critical environment setup or halt core module execution
try:
    DB_NAME = os.environ["DB_NAME"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
except KeyError as e:
    raise RuntimeError(
        f"Configuration error: Environment variable {e} is not set. "
        "Ensure you have created a valid .env file based on .env.example!"
    )

def run_query(query):
    """Central database execution utility function returning a Pandas DataFrame."""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()

def get_kpi_metrics():
    """Calculates high-level metrics using pure algebraic sums to handle sign logic natively."""
    net_dep_query = """
        SELECT SUM(amount) as total 
        FROM cash_flows 
        WHERE action IN ('Deposit', 'Withdrawal');
    """
    dep_df = run_query(net_dep_query)
    net_deposit = dep_df['total'].fillna(0).iloc[0]

    int_cash = run_query("SELECT SUM(amount) as total FROM cash_flows WHERE action = 'Interest on cash';")
    total_interest = int_cash['total'].fillna(0).iloc[0]
    
    return net_deposit, total_interest

def get_cumulative_wealth():
    """Tracks cumulative ledger cash balance evolution over time."""
    return run_query("""
        SELECT 
            DATE(timestamp) as date,
            SUM(SUM(amount)) OVER (ORDER BY DATE(timestamp)) as cumulative_cash
        FROM cash_flows
        GROUP BY DATE(timestamp)
        ORDER BY date ASC;
    """)

def get_daily_pl():
    """Retrieves aggregated historical performance grouped monthly for UI chart alignment."""
    query = """
        SELECT 
            DATE_TRUNC('month', timestamp) AS date,
            SUM(result) AS net_daily_volume
        FROM stock_transactions
        WHERE 
            result IS NOT NULL 
            AND result_currency = 'EUR'
        GROUP BY DATE_TRUNC('month', timestamp)
        ORDER BY date DESC;
    """
    return run_query(query)

def get_ticker_performance(ticker):
    """Calculates weighted moving cost average for specific asset allocations over time."""
    return run_query(f"""
        SELECT timestamp, quantity, price_per_share,
               AVG(price_per_share) OVER (ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_avg_cost
        FROM stock_transactions
        WHERE ticker = '{ticker}' AND action LIKE '%buy'
        ORDER BY timestamp ASC;
    """)

def get_realized_profit():
    """Processes asset transactions to output closed-position Net Realized Profits."""
    return run_query("""
        WITH buy_costs AS (
            SELECT ticker, SUM(total_amount) / NULLIF(SUM(quantity), 0) as avg_buy_price
            FROM stock_transactions WHERE action LIKE '%buy' GROUP BY ticker
        )
        SELECT 
            s.ticker as "Ticker", SUM(s.quantity) as "Total Units Sold",
            SUM(s.total_amount) as "Gross Revenue", SUM(s.quantity * b.avg_buy_price) as "Estimated Cost Base",
            SUM(s.total_amount) - SUM(s.quantity * b.avg_buy_price) as "Net Realized Profit"
        FROM stock_transactions s
        JOIN buy_costs b ON s.ticker = b.ticker
        WHERE s.action LIKE '%sell' GROUP BY s.ticker ORDER BY "Net Realized Profit" DESC;
    """)
    
def get_portfolio_positions():
    """Aggregates active holding metrics for the grid system overview."""
    return run_query("""
        SELECT 
            ticker as "Asset / Ticker",
            name as "Company Name",
            SUM(quantity) as "Total Shares",
            AVG(price_per_share) as "Avg Buy Price",
            SUM(total_amount) as "Total Value"
        FROM stock_transactions
        GROUP BY ticker, name
        ORDER BY "Total Value" DESC;
    """)
    
def get_asset_allocation():
    """Calculates real-time portfolio allocations valued at the latest recorded market entry."""
    query = """
        WITH last_prices AS (
            SELECT DISTINCT ON (ticker) 
                ticker, 
                price_per_share AS last_price
            FROM stock_transactions
            WHERE ticker IS NOT NULL AND price_per_share IS NOT NULL
            ORDER BY ticker, timestamp DESC
        ),
        net_quantities AS (
            SELECT 
                ticker,
                name,
                SUM(
                    CASE 
                        WHEN LOWER(action) LIKE '%buy%' THEN quantity
                        WHEN LOWER(action) LIKE '%sell%' THEN -quantity
                        ELSE 0
                    END
                ) AS current_quantity
            FROM stock_transactions
            WHERE ticker IS NOT NULL
            GROUP BY ticker, name
        )
        SELECT 
            q.ticker,
            q.name,
            (q.current_quantity * p.last_price) AS asset_value
        FROM net_quantities q
        JOIN last_prices p ON q.ticker = p.ticker
        WHERE q.current_quantity > 0.0001;
    """
    try:
        df = run_query(query)
        df['asset_value'] = pd.to_numeric(df['asset_value'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        print(f"Error calculating asset allocation valuation parameters: {e}")
        return pd.DataFrame()

def get_detailed_pl():
    """Extracts and separates capital gains processing from corporate actions dividend tracking."""
    div_query = """
        SELECT SUM(amount) as total 
        FROM cash_flows 
        WHERE action LIKE '%Dividend%';
    """
    try:
        div_df = run_query(div_query)
        total_dividends = pd.to_numeric(div_df['total'], errors='coerce').fillna(0).iloc[0]
    except Exception:
        total_dividends = 0.0
    
    capital_gain_query = """
        SELECT SUM(result) as total 
        FROM stock_transactions 
        WHERE action LIKE '%sell%';
    """
    try:
        pl_df = run_query(capital_gain_query)
        capital_gain = pd.to_numeric(pl_df['total'], errors='coerce').fillna(0).iloc[0]
    except Exception:
        capital_gain = 0.0
    
    return float(capital_gain), float(total_dividends)
    
def get_ticker_history(ticker):
    """Fetches pure cronological ledger transactions for an isolated asset asset ID."""
    query = f"""
        SELECT action, timestamp, quantity, price_per_share, total_amount, total_currency
        FROM stock_transactions
        WHERE ticker = '{ticker}'
        ORDER BY timestamp ASC;
    """
    return run_query(query)

def calculate_ticker_timeline(ticker):
    """Calculates continuous rolling transaction history records using moving average costs."""
    df = get_ticker_history(ticker)
    if df.empty:
        return []

    timeline = []
    current_shares = 0.0
    total_cost = 0.0  
    avg_buy_price = 0.0

    for idx, row in df.iterrows():
        action = row['action'].lower()
        qty = float(row['quantity']) if row['quantity'] is not None else 0.0
        price = float(row['price_per_share']) if row['price_per_share'] is not None else 0.0
        total_amt = float(row['total_amount']) if row['total_amount'] is not None else 0.0
        timestamp = row['timestamp']

        movement = {
            "date": timestamp,
            "action": row['action'],
            "shares": qty,
            "price": price,
            "total_value": total_amt,
            "notes": "",
            "pnl": 0.0
        }

        if 'buy' in action:
            current_shares += qty
            total_cost += (qty * price)
            avg_buy_price = total_cost / current_shares if current_shares > 0 else 0
            movement["notes"] = f"Buy order. New average cost: {avg_buy_price:.2f}€"

        elif 'sell' in action:
            if current_shares == 0:
                movement["notes"] = "Sell transaction lacks historical records."
                timeline.append(movement)
                continue

            cost_of_sold_shares = qty * avg_buy_price
            revenue_of_sold_shares = qty * price
            pnl = revenue_of_sold_shares - cost_of_sold_shares
            
            current_shares -= qty
            if current_shares <= 0.0001:
                current_shares = 0
                total_cost = 0
                avg_buy_price = 0
            else:
                total_cost = current_shares * avg_buy_price

            movement["pnl"] = pnl
            movement["notes"] = f"Sell order. PnL: {pnl:+.2f}€"

        timeline.append(movement)

    return timeline
    
def get_most_traded_stocks(min_transactions=4):
    """Filters data tracking metrics by setting transaction limits criteria."""
    query = f"""
        SELECT 
            ticker,
            name,
            COUNT(*) AS numero_transazioni
        FROM stock_transactions
        WHERE ticker IS NOT NULL
        GROUP BY ticker, name
        HAVING COUNT(*) >= {min_transactions}
        ORDER BY numero_transazioni DESC;
    """
    return run_query(query)
    
def get_available_months():
    """Returns historical unique Year/Month identifiers."""
    query = """
        SELECT DISTINCT 
            DATE_TRUNC('month', timestamp) AS mese_id,
            TO_CHAR(timestamp, 'YYYY - Month') AS mese_label
        FROM stock_transactions
        WHERE timestamp IS NOT NULL
        ORDER BY mese_id DESC;
    """
    return run_query(query)

def get_transactions_by_month(mese_iso):
    """Filters records containing properties matching input month identifiers."""
    query = f"""
        SELECT * FROM stock_transactions
        WHERE DATE_TRUNC('month', timestamp) = '{mese_iso}'
        ORDER BY timestamp DESC;
    """
    return run_query(query)
    
def get_all_transactions():
    """Returns comprehensive ledger listings without filter limitations."""
    query = "SELECT * FROM stock_transactions ORDER BY timestamp DESC;"
    return run_query(query)
    
def get_data_range_bounds():
    """Extracts the minimum and maximum transaction timestamps using the central run_query engine."""
    try:
        df = run_query("SELECT MIN(timestamp) as min_t, MAX(timestamp) as max_t FROM stock_transactions;")
        if not df.empty and pd.notna(df['min_t'].iloc[0]) and pd.notna(df['max_t'].iloc[0]):
            return df['min_t'].iloc[0], df['max_t'].iloc[0]
        return None, None
    except Exception:
        return None, None