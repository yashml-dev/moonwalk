@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   MOONWALK - first-time setup and launch
echo ==========================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.10-3.12 and enable Add Python to PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 goto failed
)
echo Installing or updating dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Starting MOONWALK at http://localhost:8501 ...
".venv\Scripts\python.exe" -m streamlit run PotholeDetectionApp.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Setup or launch failed. Read the error above and see README.md for troubleshooting.
pause
exit /b 1
