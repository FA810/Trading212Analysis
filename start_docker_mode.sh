#!/bin/bash

echo "------------------------------------------------------------"
echo "🚀 AVVIO IN MODALITÀ COMPLETAMENTE IN DOCKER"
echo "------------------------------------------------------------"

# 1. Forziamo l'host verso il nome del servizio Docker
export DB_HOST="postgres_db"

# 2. Avviamo tutti i servizi definiti nel compose (DB + UI)
echo "Accensione dei container (Database + Streamlit App)..."
docker compose up -d --build

echo "------------------------------------------------------------"
echo "🎯 Tutto pronto! L'applicazione è isolata dentro Docker."
echo "🔗 Apri il browser su: http://localhost:8501"
echo "------------------------------------------------------------"