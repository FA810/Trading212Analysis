#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting Trading 212 Analytics in Docker Mode..."

# 1. Check and create the exports directory if it is missing
if [ ! -d "exports" ]; then
    echo "'exports/' directory not found. Creating it now..."
    mkdir -p exports
fi

# 2. Check and clean up any stale or orphan containers on the same ports
echo "Checking and cleaning up any residual containers..."
# Shuts down containers for this specific compose file without wiping persistent data volumes
docker compose down

# 3. Build and launch the infrastructure
echo "Building and launching services (Postgres, pgAdmin, Streamlit)..."
# --build ensures that any code or Dockerfile modifications are compiled into the app
# -d launches the containers in detached mode (background)
docker compose up --build -d

echo "------------------------------------------------------------"
echo "Services successfully started in the background!"
echo "Streamlit UI: http://localhost:8501"
echo "pgAdmin:      http://localhost:8080"
echo "------------------------------------------------------------"
echo "Note: If this is the first execution, the database schema"
echo "   will initialize automatically. Place your CSV files inside"
echo "   'exports/' and run the importer script when ready."
echo "------------------------------------------------------------"
echo "To view real-time runtime logs, run: docker compose logs -f"