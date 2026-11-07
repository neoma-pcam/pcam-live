@echo off
cd /d "C:\Users\shs15"
set NEOMA_MODEL=gemini-2.5-flash
start /min "P-CAM Accelerator Bridge" python pcam_bridge.py
timeout /t 1 /nobreak > nul
python -m streamlit run neoma_web_app.py --server.headless false
pause
