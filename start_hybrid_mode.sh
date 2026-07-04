#!/bin/bash

echo "------------------------------------------------------------"
echo "🏎️  AVVIO IN MODALITÀ IBRIDA (DB in Docker + UI in Locale)"
echo "------------------------------------------------------------"

# 1. LIBERA LA PORTA: Se il container Streamlit di Docker è attivo, lo spegniamo al volo
if [ "$(docker ps -q -f name=t212_streamlit)" ]; then
    echo "⚠️ Rilevato container Streamlit interno a Docker attivo. Spegnimento in corso per liberare la porta 8501..."
    docker compose stop streamlit_app
fi

# 2. Forziamo l'host su localhost per il Python locale
export DB_HOST="localhost"

# 3. Accendiamo il container del database (se era spento)
echo "Verifica/Accensione del Database in Docker..."
docker compose up -d postgres_db

# 4. Lanciamo la UI di Streamlit usando il Python in locale
echo "Avvio dell'interfaccia Streamlit locale..."
echo "------------------------------------------------------------"
# Lanciamo app.py: grazie al nostro menu custom in theme_manager, 
# la navigazione mostrerà comunque "Main Dashboard" pur lasciando i file intatti!
streamlit run app.py