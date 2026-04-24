@echo off
REM ============================================================
REM  Magische Miesmuschel — Statistik neu berechnen
REM  Doppelklick startet dieses Script.
REM  (wird automatisch auch von ergebnisse_holen.bat aufgerufen)
REM ============================================================
setlocal

cd /d "%~dp0"

echo.
echo =====================================================
echo   MAGISCHE MIESMUSCHEL — Statistik berechnen
echo =====================================================
echo.

set "PYCMD="
where py >nul 2>&1 && set "PYCMD=py -3"
if not defined PYCMD (
  where python >nul 2>&1 && set "PYCMD=python"
)
if not defined PYCMD (
  echo [FEHLER] Python nicht gefunden.
  echo          Installieren: https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

%PYCMD% "%~dp0statistik_berechnen.py"
set "RC=%ERRORLEVEL%"

echo.
echo Fertig. Druecke eine Taste zum Schliessen.
pause >nul
exit /b %RC%
