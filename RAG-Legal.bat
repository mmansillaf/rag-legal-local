@echo off
cd /d "C:\Users\%USERNAME%\rag-legal-local"
start "" http://localhost:8501
streamlit run app.py
pause
