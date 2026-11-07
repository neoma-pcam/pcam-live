@echo off
cd /d "C:\Users\shs15"
start /min "P-CAM Accelerator Bridge" python pcam_bridge.py
timeout /t 1 /nobreak > nul
python -m streamlit run neoma_web_app.py --server.port 8501 --server.headless false
pause
