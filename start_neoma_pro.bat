@echo off
cd /d "C:\Users\shs15"
set NEOMA_MODEL=gemini-3.1-pro-preview
start /min "P-CAM Accelerator Bridge" python pcam_bridge.py
timeout /t 1 /nobreak > nul
python -m streamlit run neoma_web_app.py --server.headless false
pause
