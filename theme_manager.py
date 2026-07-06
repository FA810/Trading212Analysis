# theme_manager.py
import streamlit as st
import plotly.express as px
from backend.queries import get_kpi_metrics, get_detailed_pl

# Centralized registry for application color schemes, chart palettes, and matching UI emojis
THEME_DICTIONARY = {
    "Gold & Anthracite (Premium)": {
        "colore_barre": "#D4AF37",
        "palette_pie": ['#D4AF37', '#C5A059', '#AA7C11', '#8C6239', '#706F6F', '#4A4A4A', '#2F2F2F', '#1F1F1F'],
        "colore_perdita": "#4A4A4A",
        "emoji_menu": ["📊", "💰", "📜", "📈", "🔥", "🔍"] # Classic/Premium financial set
    },
    "Emerald & Petrol (Teal)": {
        "colore_barre": "#20b2aa",
        "palette_pie": px.colors.sequential.Tealgrn,
        "colore_perdita": "#708090",
        "emoji_menu": ["🏛️", "💸", "📂", "🔍", "⚡", "📋"] # Corporate/Clean set
    },
    "Cyberpunk Tech (Neon)": {
        "colore_barre": "#00f0ff",
        "palette_pie": ['#00f0ff', '#ff007f', '#711c91', '#133e7c', '#091833'],
        "colore_perdita": "#ff007f",
        "emoji_menu": ["🖥️", "💎", "💻", "🔮", "🚀", "💾"] # Futuristic/Tech set
    },
    "Avio Blue (Minimal)": {
        "colore_barre": "#4682B4",
        "palette_pie": px.colors.sequential.Blues_r,
        "colore_perdita": "#2F4F4F",
        "emoji_menu": ["📉", "💵", "📋", "🎯", "🌟", "🗂️"] # Minimal/Geometric set
    }
}

def inject_theme_sidebar():
    """Injects custom sidebar navigation, KPI metric counter, and manages UI global themes."""
    # Initialize global theme state if not already set
    if "tema_scelto" not in st.session_state:
        st.session_state.tema_scelto = "Gold & Anthracite (Premium)"
    
    # Callback triggered immediately when user switches selection in the dropdown
    def on_theme_change():
        st.session_state.tema_scelto = st.session_state.nuovo_tema_selezionato

    # Fetch configuration sub-dictionary for the active theme
    tema_corrente = THEME_DICTIONARY[st.session_state.tema_scelto]
    
    # Extract thematic icons with generic folder icons as a safe fallback (extended to 6 slots)
    emojis = tema_corrente.get("emoji_menu", ["📁", "📁", "📁", "📁", "📁", "📁"])

    # Hide native Streamlit navigation and inject custom CSS overrides for metric fonts and padding
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] { display: none !important; }
            div[data-testid="stSidebar"] section[data-testid="stVerticalBlock"] { padding-top: 1rem; }
            [data-testid="stSidebar"] div[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # 1. Total Return KPI Engine: Aggregates real-time values from database layers
        try:
            _, total_interest = get_kpi_metrics()
            capital_gain, total_dividends = get_detailed_pl()
            total_return = capital_gain + total_dividends + total_interest
        except Exception:
            total_return = 0.0 # Graceful fallback to prevent dashboard crashes on connection drop

        st.markdown("### Total Return Generated")
        st.metric(label="Capital Gains + Dividends + Interest", value=f"€{total_return:,.2f}")
        st.markdown("---")
        
        # 2. Custom Navigation Layout featuring dynamically matched theme emojis
        st.markdown("### Navigation Menu")
        st.page_link("app.py", label=f"{emojis[0]} Main Dashboard") 
        st.page_link("pages/1_Analisi_Dividendi.py", label=f"{emojis[1]} Dividends Analysis")
        st.page_link("pages/2_Registro_Transazioni.py", label=f"{emojis[2]} Transaction Log")
        st.page_link("pages/3_Analisi_Singolo_Titolo.py", label=f"{emojis[3]} Single Ticker Timeline")
        st.page_link("pages/4_Titoli_più_Movimentati.py", label=f"{emojis[4]} Most Active Stocks")
        st.page_link("pages/5_Anagrafica_Titoli.py", label=f"{emojis[5]} Asset Registry")
        
        # 3. Application Theme Customization Selectbox
        st.markdown("---")
        st.markdown("### Customization")
        st.selectbox(
            "Select app theme:",
            options=list(THEME_DICTIONARY.keys()),
            key="nuovo_tema_selezionato",
            index=list(THEME_DICTIONARY.keys()).index(st.session_state.tema_scelto),
            on_change=on_theme_change
        )
        
    return tema_corrente