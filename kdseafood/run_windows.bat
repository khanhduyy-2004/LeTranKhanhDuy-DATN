@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist venv (
  echo Chua cai dat. Hay chay setup_windows.bat truoc.
  pause & exit /b 1
)
call venv\Scripts\activate.bat
echo Dang chay KDSeaFood tai http://127.0.0.1:5000  (dong cua so nay de tat)
start "" http://127.0.0.1:5000
python run.py
pause
