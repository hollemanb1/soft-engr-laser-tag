@echo off
:: Ensure the script runs as administrator
NET SESSION >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo This script must be run as Administrator.
    pause
    exit /b
)

echo Updating package lists...
:: Chocolatey update (you can skip this if unnecessary)
choco upgrade chocolatey -y

echo Installing Python and PostgreSQL...
:: Install packages
choco install -y python postgresql

echo Installing Python packages...
:: Use pip to install dependencies
pip install pyqt5 pyqt5-qt5 pyqt5-tools psycopg2 pillow

echo Starting PostgreSQL service...
net start postgresql || echo PostgreSQL may already be running.

:: Wait until PostgreSQL is ready
echo Waiting for PostgreSQL to become available...
:wait_pg
powershell -Command "try { & 'C:\Program Files\PostgreSQL\16\bin\pg_isready.exe' -q } catch { exit 1 }"
IF %ERRORLEVEL% NEQ 0 (
    timeout /t 1 >nul
    goto wait_pg
)

echo Setting up database (idempotent)...
:: Run SQL setup using psql
SET PGPASSWORD=postgres
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -v ON_ERROR_STOP=1 -c "DO $$BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='student') THEN CREATE ROLE student LOGIN PASSWORD 'student'; END IF; END$$;"
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -v ON_ERROR_STOP=1 -c "DO $$BEGIN IF NOT EXISTS (SELECT FROM pg_database WHERE datname='photon') THEN CREATE DATABASE photon OWNER student; END IF; END$$;"

"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d photon -v ON_ERROR_STOP=1 -c "CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY, codename VARCHAR(255) NOT NULL);"

echo Packages installed. Opening application...
python main.py

pause
