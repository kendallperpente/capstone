#!/bin/bash
# Install dependencies and run streamlit app

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Starting Streamlit app..."
streamlit run streamlit_app.py
