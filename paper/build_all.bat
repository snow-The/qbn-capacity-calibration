@echo off
setlocal
REM One command to reproduce every paper artifact from scratch:
REM   1. regenerate the three figures (vector SVG for the paper, plus PDF and a PNG preview)
REM   2. rebuild the Chinese and the English paper
REM Figures need the capacity grid JSON, so run this inside the repository copy.
pushd "%~dp0..\..\.."
set REPO=%CD%
popd
set PY=%REPO%\.venv\Scripts\python.exe
cd /d "%~dp0"
if not exist "%PY%" (
  echo *** repo venv not found: %PY% ***
  exit /b 1
)
echo === FIGURES ===
"%PY%" -u make_fig_cliff.py
if errorlevel 1 exit /b 10
"%PY%" -u make_fig_grid.py
if errorlevel 1 exit /b 11
"%PY%" -u make_fig_arch.py
if errorlevel 1 exit /b 12
echo === PAPER (zh) ===
call build.bat
if errorlevel 1 exit /b 20
echo === PAPER (en) ===
call build_en.bat
if errorlevel 1 exit /b 21
echo === DONE ===
endlocal
