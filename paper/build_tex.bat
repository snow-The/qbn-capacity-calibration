@echo off
setlocal
REM Typst -> LaTeX -> PDF. Two steps, both fail-closed:
REM   1. make_latex.py converts paper_en.typ / paper.typ into paper.tex / paper_zh.tex
REM   2. latexmk -xelatex compiles each one (xelatex because paper_zh.tex is ctexart)
REM arxiv.sty lives in packages/latex-arxiv-style, so TEXINPUTS has to point there.
pushd "%~dp0..\..\.."
set ROOT=%CD%
popd
set PY=%ROOT%\.venv\Scripts\python.exe
cd /d "%~dp0"
set TEXINPUTS=%ROOT%\packages\latex-arxiv-style;
if not exist "%PY%" (
  echo *** repo venv not found: %PY% ***
  exit /b 1
)
echo === CONVERT: typst to latex ===
"%PY%" -u make_latex.py
if errorlevel 1 exit /b 10
echo === COMPILE paper.tex (en) ===
REM -g forces a rebuild: latexmk otherwise refuses to retry after a failed run ("Nothing to do").
latexmk -xelatex -g -interaction=nonstopmode -halt-on-error paper.tex
if errorlevel 1 (
  echo *** paper.tex did not compile ***
  exit /b 20
)
echo === COMPILE paper_zh.tex (zh) ===
latexmk -xelatex -g -interaction=nonstopmode -halt-on-error paper_zh.tex
if errorlevel 1 (
  echo *** paper_zh.tex did not compile ***
  exit /b 21
)
echo === PRODUCED ===
dir /b paper.pdf paper_zh.pdf
endlocal
