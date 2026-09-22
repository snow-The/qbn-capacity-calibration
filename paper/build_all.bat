@echo off
setlocal
REM One command to reproduce every paper artifact from scratch:
REM   1. regenerate the four figures (vector SVG for the paper, plus PDF and a PNG preview)
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
REM tau_dose.svg is hand-authored, so its PDF is derived from the SVG.
REM Page size must match the SVG aspect ratio; a mismatch silently yields
REM an A4 page that overflows textheight as Float too large for page.
"%PY%" -u svg2pdf.py tau_dose.svg
if errorlevel 1 exit /b 13
echo === PAPER (zh) ===
call build.bat
if errorlevel 1 exit /b 20
echo === PAPER (en) ===
call build_en.bat
if errorlevel 1 exit /b 21
echo === DONE ===
endlocal
