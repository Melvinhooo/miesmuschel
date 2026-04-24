@echo off
REM ============================================================
REM  Magische Miesmuschel — Ergebnisse von APIs holen
REM  Doppelklick startet dieses Script.
REM ============================================================
setlocal

cd /d "%~dp0"

echo.
echo =====================================================
echo   MAGISCHE MIESMUSCHEL — Ergebnisse holen
echo =====================================================
echo.

REM Python-Kommando bestimmen (py Launcher bevorzugt, sonst python)
set "PYCMD="
where py >nul 2>&1 && set "PYCMD=py -3"
if not defined PYCMD (
  where python >nul 2>&1 && set "PYCMD=python"
)
if not defined PYCMD (
  echo [FEHLER] Python nicht gefunden.
  echo          Installieren: https://www.python.org/downloads/
  echo          Waehrend der Installation 'Add Python to PATH' ankreuzen.
  echo.
  pause
  exit /b 1
)

REM requests-Paket sicherstellen
%PYCMD% -c "import requests" 2>nul
if errorlevel 1 (
  echo [INFO] Python-Paket 'requests' fehlt — installiere ...
  %PYCMD% -m pip install --user requests
  if errorlevel 1 (
    echo [FEHLER] pip install requests fehlgeschlagen.
    pause
    exit /b 1
  )
)

%PYCMD% "%~dp0ergebnisse_holen.py" %*
set "RC=%ERRORLEVEL%"

echo.
echo Fertig. Druecke eine Taste zum Schliessen.
pause >nul
exit /b %RC%
