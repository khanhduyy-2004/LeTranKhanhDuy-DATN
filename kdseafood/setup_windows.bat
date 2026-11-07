@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ==========================================================
echo   KDSeaFood - CAI DAT TU DONG (Windows)
echo ==========================================================

REM ---- 1. Kiem tra Python ----
where python >nul 2>nul
if errorlevel 1 (
  echo [LOI] Chua cai Python hoac chua tick "Add python.exe to PATH".
  echo       Tai tai: https://www.python.org/downloads/windows/
  pause & exit /b 1
)
python --version

REM ---- 2. Tao moi truong ao + cai thu vien ----
if not exist venv (
  echo [1/4] Tao moi truong ao venv...
  python -m venv venv || (echo [LOI] Khong tao duoc venv & pause & exit /b 1)
)
call venv\Scripts\activate.bat
echo [2/4] Cai thu vien Python (Flask, PyMySQL, Flask-WTF...)
python -m pip install --upgrade pip >nul
pip install -r requirements.txt || (echo [LOI] Cai thu vien that bai - kiem tra mang Internet & pause & exit /b 1)

REM ---- 3. Tim MySQL ----
set "MYSQL="
for %%V in (9.5 9.4 9.3 9.2 9.1 9.0 8.4 8.0) do (
  if not defined MYSQL if exist "C:\Program Files\MySQL\MySQL Server %%V\bin\mysql.exe" set "MYSQL=C:\Program Files\MySQL\MySQL Server %%V\bin\mysql.exe"
)
if not defined MYSQL if exist "C:\xampp\mysql\bin\mysql.exe" set "MYSQL=C:\xampp\mysql\bin\mysql.exe"
if not defined MYSQL (
  where mysql >nul 2>nul && set "MYSQL=mysql"
)
if not defined MYSQL (
  echo [LOI] Khong tim thay MySQL. Cai MySQL 8.4 tai: https://dev.mysql.com/downloads/mysql/8.4.html
  pause & exit /b 1
)
echo [3/4] Tim thay MySQL: %MYSQL%

set /p DBPASS=Nhap mat khau tai khoan root cua MySQL (XAMPP de trong thi nhan Enter): 
if "%DBPASS%"=="" (
  "%MYSQL%" -u root --default-character-set=utf8mb4 < database\kdseafood.sql
) else (
  "%MYSQL%" -u root -p"%DBPASS%" --default-character-set=utf8mb4 < database\kdseafood.sql
)
if errorlevel 1 (
  echo [LOI] Nap co so du lieu that bai. Kiem tra MySQL dang chay va mat khau root.
  pause & exit /b 1
)
echo       Da tao CSDL "kdseafood" + du lieu mau.

REM ---- 4. Tao file .env ----
for /f %%K in ('python -c "import secrets;print(secrets.token_hex(24))"') do set "SKEY=%%K"
(
  echo SECRET_KEY=%SKEY%
  echo DB_HOST=127.0.0.1
  echo DB_PORT=3306
  echo DB_USER=root
  echo DB_PASSWORD=%DBPASS%
  echo DB_NAME=kdseafood
  echo FLASK_DEBUG=1
) > .env
echo [4/4] Da tao file .env

echo.
echo ==========================================================
echo   CAI DAT XONG!  Bam dup run_windows.bat de chay website.
echo   Tai khoan: admin / 123456  -  khach01 / 123456
echo ==========================================================
pause
