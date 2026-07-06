import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import os
from theme_manager import inject_theme_sidebar

# 1. Configurazione della pagina e iniezione del tema attivo
st.set_page_config(layout="wide")
TEMA_ATTIVO = inject_theme_sidebar()

st.title("Dividends Analysis")
st.caption(f"Track your monthly passive income streams • Current theme: {st.session_state.tema_scelto}")
st.markdown("---")

# 2. Funzione di connessione al database ereditata dal setup di db_importer
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"]
    )

# 3. Caricamento e aggregazione dati dei dividendi
@st.cache_data(ttl=30)
def load_dividend_data():
    try:
        conn = get_db_connection()
        # Estraiamo i dividendi storici aggregando per data e ticker
        query = """
            SELECT 
                timestamp as date,
                ticker,
                total_amount as amount
            FROM stock_transactions
            WHERE LOWER(action) LIKE '%dividend%'
              AND total_amount IS NOT NULL
              AND total_amount > 0;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
            
        # Trasformazioni temporali stabili
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['month_num'] = df['date'].dt.month
        df['month_label'] = df['date'].dt.strftime('%b') # Jan, Feb, Mar...
        return df
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return pd.DataFrame()

df_raw = load_dividend_data()

if df_raw.empty:
    st.info("No dividend transaction data available in the database yet. Make sure to import your CSV reports.")
else:
    # 4. Selezione dell'anno in cima alla pagina
    elenco_anni = sorted(df_raw['year'].unique(), reverse=True)
    selected_year = st.selectbox("Select historical year:", options=elenco_anni)
    
    # Filtro dei dati per l'anno selezionato
    df_year = df_raw[df_raw['year'] == selected_year].copy()
    
    if df_year.empty:
        st.warning(f"No dividends found for the year {selected_year}.")
    else:
        # ==========================================================
        # 5. RAGGRUPPAMENTO DINAMICO SOGLIA % (Sotto 5% va in Others)
        # ==========================================================
        ticker_totals = df_year.groupby('ticker')['amount'].sum()
        total_year_amount = ticker_totals.sum()
        
        # Soglia dinamica del 5% per l'esposizione annuale dell'asset
        soglia_percentuale = 0.05 
        
        top_tickers = ticker_totals[
            (ticker_totals / total_year_amount) >= soglia_percentuale
        ].index.tolist()
        
        # Salvaguardia: Forza MAIN a stare fuori da "Others" indipendentemente dalla soglia
        if 'MAIN' in ticker_totals.index and 'MAIN' not in top_tickers:
            top_tickers.append('MAIN')
            
        df_year['ticker_grouped'] = df_year['ticker'].apply(
            lambda x: x if x in top_tickers else 'Others'
        )
        
        # ==========================================================
        # 6. PREPARAZIONE STRUTTURA COMPLETA A 12 MESI (Jan - Dec)
        # ==========================================================
        mesi_anno = pd.DataFrame({
            'month_num': range(1, 13),
            'month_label': ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        })
        
        # Raggruppiamo i dati reali post-filtro ticker
        df_grouped = df_year.groupby(['month_num', 'month_label', 'ticker_grouped'])['amount'].sum().reset_index()
        
        # Generiamo la matrice fissa a 12 mesi combinando tutti i cluster attivi nell'anno
        all_tickers = df_year['ticker_grouped'].unique()
        griglia_completa = pd.MultiIndex.from_product(
            [range(1, 13), all_tickers], 
            names=['month_num', 'ticker_grouped']
        ).to_frame().reset_index(drop=True)
        griglia_completa = griglia_completa.merge(mesi_anno, on='month_num')
        
        # Creazione del DataFrame definitivo per l'alimentazione del grafico
        df_grafico = griglia_completa.merge(df_grouped, on=['month_num', 'month_label', 'ticker_grouped'], how='left')
        df_grafico['amount'] = df_grafico['amount'].fillna(0.0)
        df_grafico = df_grafico.sort_values('month_num')
        
        # Generazione sicura del testo interno escludendo i blocchi con 0 euro
        df_grafico['text_inside'] = [
            f"{row['ticker_grouped']}<br>€{row['amount']:.2f}" if row['amount'] > 0 else ""
            for _, row in df_grafico.iterrows()
        ]

        # ==========================================================
        # 7. CALCOLO METRICHE (KPI) CORRETTE (Escluso Mese Corrente)
        # ==========================================================
        current_time = pd.Timestamp.now()
        
        # Isolamento puro dei mesi chiusi per evitare alterazioni sulla media
        if selected_year == current_time.year:
            df_media_base = df_year[df_year['month_num'] < current_time.month]
            total_for_average = df_media_base['amount'].sum()
            months_to_divide = current_time.month - 1
            if months_to_divide == 0:
                months_to_divide = 1
        else:
            total_for_average = df_year['amount'].sum()
            months_to_divide = 12
            
        media_mensile = total_for_average / months_to_divide
        total_received = df_year['amount'].sum()
        
        # Analisi del picco storico mensile
        stats_mensili = df_year.groupby('month_label')['amount'].sum()
        best_month = stats_mensili.idxmax() if not stats_mensili.empty else "N/A"
        best_month_val = stats_mensili.max() if not stats_mensili.empty else 0.0
        
        # Render dei KPI Widget
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric(label=f"Total Dividends ({selected_year})", value=f"€{total_received:,.2f}")
        with kpi2:
            st.metric(label="Monthly Average", value=f"€{media_mensile:,.2f}", help=f"Calculated over {months_to_divide} fully completed months (current month data and divider excluded)")
        with kpi3:
            st.metric(label="Best Month Peak", value=f"€{best_month_val:,.2f}", delta=best_month, delta_color="off")
            
        st.markdown("---")
        
        # ==========================================================
        # 8. CREAZIONE GRAFICO CON PLOTLY (Testi Interni + Totale in Cima, Senza Tooltip)
        # ==========================================================
        st.subheader("Monthly Dividend Breakdown")
        
        fig_bar = px.bar(
            df_grafico,
            x='month_label',
            y='amount',
            color='ticker_grouped',
            text='text_inside', 
            template="plotly_dark",
            labels={'month_label': 'Month', 'amount': 'Amount Generated (€)', 'ticker_grouped': 'Asset Ticker'},
            color_discrete_sequence=TEMA_ATTIVO["palette_pie"],
            category_orders={"month_label": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
        )
        
        # Pulizia totale degli specchi hover e ancoraggio testi all'interno dei mattoncini
        fig_bar.update_traces(
            hoverinfo="skip",
            hovertemplate=None,
            textposition="inside", 
            insidetextanchor="middle" 
        )
        
        fig_bar.update_layout(
            barmode='stack',
            margin=dict(t=30, b=20, l=20, r=20), 
            height=500,
            xaxis_title="",
            yaxis_title="Dividends Cash (€)",
            hovermode=False, 
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
        )
        
        # Calcolo dinamico aggregato per piazzare l'etichetta del totale in cima alle colonne
        fig_bar.update_layout(
            annotations=[
                dict(
                    x=month,
                    y=total,
                    text=f"<b>€{total:.2f}</b>" if total > 0 else "",
                    showarrow=False,
                    yshift=10, 
                    font=dict(color="#ffffff", size=11)
                )
                for month, total in df_grafico.groupby('month_label', sort=False)['amount'].sum().items()
            ]
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # ==========================================================
        # 9. TABELLA DI DETTAGLIO IN FONDO (Mesi Alternati e Fullname)
        # ==========================================================
        st.markdown("---")
        st.subheader("Granular Dividend Log")
        
        # Registro anagrafico centralizzato per la normalizzazione dei Ticker
        TICKER_NAMES = {
            "NOV": "Novo Nordisk",
            "RY6": "Realty Income",
            "MBG": "Mercedes-Benz Group",
            "TRIN": "Trinity Capital",
            "ARCC": "Ares Capital",
            "MAIN": "Main Street Capital",
            "STWD": "Starwood Property Trust",
            "1YD": "Broadcom",
            "SHELL": "Shell"
        }
        
        # Estrazione log storico per l'anno in esame
        df_log = df_year[['date', 'ticker', 'amount']].sort_values('date', ascending=False).copy()
        df_log['month_num'] = df_log['date'].dt.month
        
        # Abbinamento del Nome Esteso societario
        df_log['Asset Name'] = df_log['ticker'].apply(lambda x: TICKER_NAMES.get(x, x))
        
        # Pulizia estetica delle stringhe valutarie e temporali
        df_log['Formatted Date'] = df_log['date'].dt.strftime('%Y-%m-%d')
        df_log['Formatted Amount'] = df_log['amount'].apply(lambda x: f"€ {x:,.2f}")
        
        # Selezione dei campi finali per il rendering utente
        df_display = df_log[['Formatted Date', 'ticker', 'Asset Name', 'Formatted Amount', 'month_num']].copy()
        df_display.columns = ['Date', 'Ticker', 'Company Name', 'Amount', 'month_num']
        
        # Algoritmo di colorazione per blocco mensile alternato (ottimizzato tema scuro)
        def color_by_month(row):
            bg_color = 'background-color: #1e2638;' if row['month_num'] % 2 != 0 else ''
            return [bg_color] * len(row)
        
        styled_df = df_display.style.apply(color_by_month, axis=1)
        
        # Visualizzazione del log tabellare filtrato
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={"month_num": None}
        )