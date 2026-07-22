import csv
import psycopg2
import os
import glob
from datetime import datetime

# Load .env file if present (useful for local testing outside Docker)
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

# Secure and dynamic host/port configuration fallback for development environments
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Enforce environment configuration or halt execution if critical keys are missing
try:
    DB_NAME = os.environ["DB_NAME"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
except KeyError as e:
    raise RuntimeError(
        f"Configuration error: Environment variable {e} is not set. "
        "Ensure you have created a valid .env file based on .env.example!"
    )

def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def initialize_database():
    """Creates the target schema tables if they do not exist (Idempotent schema initialization)."""
    connection = get_db_connection()
    cursor = connection.cursor()

    create_stock_transactions_table = """
    CREATE TABLE IF NOT EXISTS stock_transactions (
        id VARCHAR(100) PRIMARY KEY,
        action VARCHAR(50) NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        ticker VARCHAR(50),
        isin VARCHAR(50),
        name VARCHAR(255),
        quantity NUMERIC(20, 10),
        price_per_share NUMERIC(20, 6),
        price_currency VARCHAR(10),
        total_amount NUMERIC(20, 4),
        total_currency VARCHAR(10),
        result NUMERIC(20, 4),
        result_currency VARCHAR(10)
    );
    """

    create_cash_flows_table = """
    CREATE TABLE IF NOT EXISTS cash_flows (
        id VARCHAR(100) PRIMARY KEY,
        action VARCHAR(50) NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        amount NUMERIC(20, 4) NOT NULL,
        currency VARCHAR(10),
        notes TEXT
    );
    """

    try:
        cursor.execute(create_stock_transactions_table)
        cursor.execute(create_cash_flows_table)
        connection.commit()
        print("Database initialization completed successfully (Tables verified/created).")
    except Exception as error:
        connection.rollback()
        print(f"Error during database initialization: {error}")
    finally:
        cursor.close()
        connection.close()

def parse_numeric(value):
    """Safely converts a string to float, or returns None if empty."""
    if not value or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None

def parse_string(value):
    """Cleans string values by stripping quotes and spaces, returns None if empty."""
    if not value or value.strip() == "":
        return None
    return value.strip().replace('"', '')

def import_csv_to_database(csv_file_path):
    """Reads the CSV file line-by-line and streams data into Postgres safely (Idempotent upsert process)."""
    connection = get_db_connection()
    cursor = connection.cursor()

    # Avoid duplicate entry errors by utilizing ON CONFLICT DO NOTHING
    insert_stock_query = """
    INSERT INTO stock_transactions (
        id, action, timestamp, ticker, isin, name, 
        quantity, price_per_share, price_currency, total_amount, total_currency,
        result, result_currency
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING;
    """

    insert_cash_query = """
    INSERT INTO cash_flows (
        id, action, timestamp, amount, currency, notes
    ) VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING;
    """

    inserted_stocks = 0
    inserted_cash = 0

    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            for row in csv_reader:
                action = parse_string(row.get('Action'))
                
                # Flexible timestamp lookup: handles both 'Time' and updated 'Time (UTC)' CSV column headers
                raw_time = row.get('Time') or row.get('Time (UTC)')
                
                # Check for mandatory keys; skip incomplete rows
                if not action or not raw_time:
                    continue 
                
                # Sanitize ISO timezone suffixes (e.g., '2026-06-21 01:08:39+00:00' -> '2026-06-21 01:08:39')
                raw_time_clean = raw_time.split('+')[0].strip()
                try:
                    timestamp = datetime.strptime(raw_time_clean, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # Skip row if timestamp parsing fails on unexpected formatting
                    continue
                
                # ID Handling: If the CSV does not provide an ID (common in older dividend lines), generate a deterministic slug
                row_id = parse_string(row.get('ID'))
                if not row_id:
                    ticker_slug = parse_string(row.get('Ticker')) if row.get('Ticker') else "CASH"
                    time_slug = timestamp.strftime("%Y%m%d%H%M%S")
                    row_id = f"gen_{ticker_slug}_{time_slug}"

                # --- 1. STOCK TRANSACTIONS AND DIVIDENDS MANAGEMENT ---
                # Intercept any trading action containing 'buy', 'sell' or 'dividend' keywords
                if any(keyword in action.lower() for keyword in ['buy', 'sell', 'dividend']):
                    quantity = parse_numeric(row.get('No. of shares'))
                    price = parse_numeric(row.get('Price / share'))
                    price_curr = parse_string(row.get('Currency (Price / share)'))
                    
                    # Fallback pattern: If 'Total' field is missing or blank, draw numerical value from 'Result'
                    total_val = row.get('Total') if row.get('Total') and row.get('Total').strip() != "" else row.get('Result')
                    total = parse_numeric(total_val)
                    
                    # Apply identical fallback strategy for total value currency mapping
                    total_curr_val = row.get('Currency (Total)') if row.get('Currency (Total)') and row.get('Currency (Total)').strip() != "" else row.get('Currency (Result)')
                    total_curr = parse_string(total_curr_val)
                    
                    ticker = parse_string(row.get('Ticker'))
                    isin = parse_string(row.get('ISIN'))
                    name = parse_string(row.get('Name'))
                    result = parse_numeric(row.get('Result'))
                    result_curr = parse_string(row.get('Currency (Result)'))

                    # Execute statement applying dynamic inline evaluation wrapper logic to guarantee a valid currency string
                    cursor.execute(insert_stock_query, (
                        row_id, action, timestamp, ticker, isin, name,
                        quantity, price, price_curr, total, total_curr if total_curr else result_curr,
                        result, result_curr
                    ))
                    inserted_stocks += cursor.rowcount

                # --- 2. CASH FLOWS MANAGEMENT (Deposits, Withdrawals, Interest, and Dividends mapping) ---
                if action in ['Deposit', 'Withdrawal', 'Interest on cash'] or 'Dividend' in action:
                    # Dividends store gross amounts inside 'Result' column while leaving 'Total' empty.
                    # Pull values from 'Result' if 'Total' field is evaluated as blank.
                    cash_val = row.get('Total') if row.get('Total') and row.get('Total').strip() != "" else row.get('Result')
                    amount = parse_numeric(cash_val)
                    
                    currency_val = row.get('Currency (Total)') if row.get('Currency (Total)') and row.get('Currency (Total)').strip() != "" else row.get('Currency (Result)')
                    currency = parse_string(currency_val)
                    
                    notes = parse_string(row.get('Notes')) if row.get('Notes') else f"Dividend from {row.get('Ticker')}"

                    if amount is not None:
                        # Append a unique cash suffix code to prevent Primary Key collisions on the shared schema structure
                        cash_id = f"{row_id}_cash" if 'Dividend' in action else row_id
                        cursor.execute(insert_cash_query, (
                            cash_id, action, timestamp, amount, currency, notes
                        ))
                        inserted_cash += cursor.rowcount

        connection.commit()
        print(f"[{csv_file_path}] Import finished. New stocks: {inserted_stocks}. New cash rows: {inserted_cash}.")

    except Exception as error:
        connection.rollback()
        print(f"Error during CSV import for {csv_file_path}: {error}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    initialize_database()
    
    # Locate all exported CSV files stored inside the designated 'exports/' workspace directory
    search_path = os.path.join("exports", "*.csv")
    csv_files = glob.glob(search_path)
    
    if not csv_files:
        print("No CSV files found in 'exports/' folder. Ensure reports are placed in the directory.")
    else:
        for file in csv_files:
            print(f"Starting import routine for: {file}")
            import_csv_to_database(file)