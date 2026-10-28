@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo MOONWALK environment not found. Run SETUP_MOONWALK.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run PotholeDetectionApp.py
if errorlevel 1 (
  echo.
  echo MOONWALK stopped with an error. See README.md for troubleshooting.
  pause
  exit /b 1
)
