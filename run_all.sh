#!/bin/bash

# --- CONFIGURATION ---
SCRIPT_CALC="analytics.py"
SCRIPT_DASH="dashboard_gen.py"
OUTPUT_HTML="dashboard.html"
DATA_FOLDER="exports"

# 1. Function to check and install Python libraries
check_python_lib() {
    python -c "import $1" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Library '$1' not found. Installing..."
        pip install $1
    else
        echo "Library '$1' is already installed."
    fi
}

echo "------------------------------------------------------------"
echo "SYSTEM CHECK"
echo "------------------------------------------------------------"

# Check dependencies
check_python_lib "pandas"
check_python_lib "plotly"

# Check and create exports folder
if [ ! -d "$DATA_FOLDER" ]; then
    echo "Directory '$DATA_FOLDER' not found. Creating it now..."
    mkdir "$DATA_FOLDER"
    echo "!!! ACTION REQUIRED: Place your CSV files in the '$DATA_FOLDER' folder and run this script again."
    exit 0
fi

echo "Data folder '$DATA_FOLDER' is ready."
echo "------------------------------------------------------------"

# 2. Executing Data Analytics
if [ -f "$SCRIPT_CALC" ]; then
    echo "Starting $SCRIPT_CALC..."
    python "$SCRIPT_CALC"
    if [ $? -ne 0 ]; then
        echo "Error during $SCRIPT_CALC execution. Aborting."
        exit 1
    fi
else
    echo "Error: $SCRIPT_CALC not found."
    exit 1
fi

echo "------------------------------------------------------------"

# 3. Executing Dashboard Generation
if [ -f "$SCRIPT_DASH" ]; then
    echo "Starting $SCRIPT_DASH..."
    python "$SCRIPT_DASH"
    if [ $? -ne 0 ]; then
        echo "Error during $SCRIPT_DASH execution. Aborting."
        exit 1
    fi
else
    echo "Error: $SCRIPT_DASH not found."
    exit 1
fi

echo "------------------------------------------------------------"
echo "All processes completed successfully."

# 4. Automatically opening the dashboard
if [ -f "$OUTPUT_HTML" ]; then
    echo "Opening $OUTPUT_HTML..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$OUTPUT_HTML"                       # macOS
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        start "$OUTPUT_HTML"                      # Windows (Git Bash / MSYS)
    else
        xdg-open "$OUTPUT_HTML" 2>/dev/null || echo "Could not open browser automatically." # Linux
    fi
fi