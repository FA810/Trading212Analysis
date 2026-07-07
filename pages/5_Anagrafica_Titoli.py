import streamlit as st
import pandas as pd
import psycopg2
import os
from theme_manager import inject_theme_sidebar

# 1. Page Configuration & Custom Theme Integration
st.set_page_config(
    page_title="Trading 212 Analytics", 
    page_icon="📈", 
    layout="wide"
)
TEMA_ATTIVO = inject_theme_sidebar()

st.title("Asset Registry Lookup")
st.caption("Comprehensive mapping of stock tickers and company full names parsed from your imported CSV statements.")
st.markdown("---")

# 2. Secure Database Connection Factory
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"]
    )

# 3. Fetch Unique Ticker and Name Mapping from PostgreSQL
@st.cache_data(ttl=60)
def load_ticker_registry():
    try:
        conn = get_db_connection()
        # Select distinct pairs where ticker and name are valid and populated
        query = """
            SELECT DISTINCT 
                UPPER(ticker) as ticker, 
                name as company_name
            FROM stock_transactions
            WHERE ticker IS NOT NULL 
              AND ticker NOT IN ('', 'CASH')
              AND name IS NOT NULL
              AND name != ''
            ORDER BY ticker ASC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database extraction error: {e}")
        return pd.DataFrame()

df_registry = load_ticker_registry()

# 4. Rendering UI Data Table Components
if df_registry.empty:
    st.info("No mapped assets found in the database. Please run your 'db_importer.py' pipeline first.")
else:
    # Quick search feature input field
    search_query = st.text_input("🔍 Search by Ticker or Company Name:", "").strip().lower()
    
    # Filter dataset dynamically on user keystrokes
    if search_query:
        df_filtered = df_registry[
            df_registry['ticker'].str.lower().str.contains(search_query) | 
            df_registry['company_name'].str.lower().str.contains(search_query)
        ]
    else:
        df_filtered = df_registry

    st.markdown(f"**Total unique assets identified:** {len(df_filtered)}")

    # Clean display column layout headers
    df_display = df_filtered.copy()
    df_display.columns = ["Ticker Symbol", "Official Company Full Name"]

    # Render data inside a clean, modern Streamlit UI component frame
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )