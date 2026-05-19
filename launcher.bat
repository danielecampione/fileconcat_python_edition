@echo off
cd /d "%~dp0"

echo Avvio dell'applicazione Python...

:: Prova a usare il launcher "py"
py -3 main.py 2>nul
if %errorlevel%==0 goto end

:: Se fallisce, prova "python"
python main.py 2>nul
if %errorlevel%==0 goto end

echo.
echo ERRORE: Python non trovato sul sistema.
echo Installa Python da https://www.python.org/downloads/
echo.
pause
exit /b

:end
echo.
