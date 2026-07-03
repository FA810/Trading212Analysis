import os
import psycopg2
from dotenv import load_dotenv

# Load .env file if present (useful for local development outside Docker environments)
if os.path.exists(".env"):
    load_dotenv()

try:
    # Establish connection using secure environment variables with default fallbacks
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"]
    )
    cursor = connection.cursor()
    
    # RESTART IDENTITY resets auto-incrementing sequences, CASCADE handles any foreign key dependencies
    cursor.execute("TRUNCATE TABLE stock_transactions, cash_flows RESTART IDENTITY CASCADE;")
    connection.commit()
    print("Database cleared successfully! Ready for a fresh import.")
    
except Exception as e:
    print(f"Error occurred while clearing the database: {e}")
finally:
    # Ensure database database resources are properly released
    if 'cursor' in locals(): 
        cursor.close()
    if 'connection' in locals(): 
        connection.close()