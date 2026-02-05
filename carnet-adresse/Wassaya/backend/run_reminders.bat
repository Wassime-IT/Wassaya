@echo off
setlocal

REM --- 1) Chemin du projet (backend où se trouve manage.py)
set "PROJECT_DIR=C:\Users\wassi\OneDrive\Desktop\POO Python\Mini projet\carnet-adresse\Wassaya\backend"

REM --- 2) Python à utiliser
set "PYTHON=C:\Users\wassi\AppData\Local\Microsoft\WindowsApps\python.exe"

REM --- 3) Log file (historique d'exécution)
set "LOG_DIR=%PROJECT_DIR%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\send_reminders.log"

cd /d "%PROJECT_DIR%"

echo ================================================== >> "%LOG_FILE%"
echo [%date% %time%] Running send_reminders... >> "%LOG_FILE%"

REM --- Appliquer migrations (safe)
"%PYTHON%" manage.py migrate >> "%LOG_FILE%" 2>&1

REM --- Lancer la commande reminders
"%PYTHON%" manage.py send_reminders >> "%LOG_FILE%" 2>&1

echo [%date% %time%] Done. >> "%LOG_FILE%"

endlocal
