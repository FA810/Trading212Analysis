import streamlit as st
import pandas as pd
from theme_manager import inject_theme_sidebar
from backend.queries import get_all_transactions

st.set_page_config(
    page_title="Trading 212 Analytics", 
    page_icon="📈", 
    layout="wide"
)
TEMA_ATTIVO = inject_theme_sidebar()
st.title("Complete Transaction Log")
st.markdown("---")

try:
    df_tutto = get_all_transactions()
    if df_tutto is not None and not df_tutto.empty:
        df_lavoro = df_tutto.copy()
        colonna_data = 'timestamp' if 'timestamp' in df_lavoro.columns else df_lavoro.columns[0]
        df_lavoro[colonna_data] = pd.to_datetime(df_lavoro[colonna_data])
        
        # Create a Period object to allow proper chronological and mathematical sorting
        df_lavoro['Periodo_Obj'] = df_lavoro[colonna_data].dt.to_period('M')
        
        # Format the user-facing display string
        df_lavoro['Mese_Filtro'] = df_lavoro[colonna_data].dt.strftime('%Y - %B')
        
        # Extract unique month pairs and sort from most recent to oldest
        mappa_mesi = df_lavoro[['Periodo_Obj', 'Mese_Filtro']].drop_duplicates().sort_values('Periodo_Obj', ascending=False)
        elenco_mesi = mappa_mesi['Mese_Filtro'].tolist()
        
        mese_scelto = st.selectbox("Select month:", options=elenco_mesi)
        
        # Filter data and drop internal sorting columns
        df_filtrato = df_lavoro[df_lavoro['Mese_Filtro'] == mese_scelto].copy()
        df_filtrato = df_filtrato.drop(columns=['Mese_Filtro', 'Periodo_Obj'])
        
        # Stringify datetime fields to prevent serialization issues in the frontend grid view
        for col in df_filtrato.columns:
            if pd.api.types.is_datetime64_any_dtype(df_filtrato[col]):
                df_filtrato[col] = df_filtrato[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_filtrato = df_filtrato.fillna("")
        
        st.info(f"Showing {len(df_filtrato)} transactions out of {len(df_tutto)}")
        st.dataframe(df_filtrato, use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Error loading transaction registry: {e}")