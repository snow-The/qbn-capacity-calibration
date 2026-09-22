@echo off
setlocal
REM End to end: typst -> latex -> local build (to get the .bbl) -> arXiv bundle -> verify.
REM
REM The verification step is the point of this script: it copies the bundle to _verify,
REM CLEARS TEXINPUTS and compiles from there. That is what arXiv does, so if it builds
REM there it will build on arXiv -- the TEXINPUTS trick used by build_tex.bat does not
REM exist on their side.
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
echo === STEP 1: typst -^> latex ===
"%PY%" -u make_latex.py
if errorlevel 1 exit /b 10
echo === STEP 2: local build so that paper.bbl exists ===
latexmk -xelatex -g -interaction=nonstopmode -halt-on-error paper.tex
if errorlevel 1 (
  echo *** local build failed, cannot produce a .bbl ***
  exit /b 20
)
echo === STEP 2b: build the Chinese LaTeX paper as well ===
REM paper_zh.tex is not part of the arXiv bundle (arXiv takes the English one),
REM but it is a deliverable, and it used to be built by a separate script that
REM nobody called -- which is why paper_zh.pdf sat stale while everything else
REM was rebuilt.
latexmk -xelatex -g -interaction=nonstopmode -halt-on-error paper_zh.tex
if errorlevel 1 (
  echo *** paper_zh.tex did not compile ***
  exit /b 25
)
echo === STEP 3: assemble the arXiv bundle ===
"%PY%" -u make_submission.py paper.tex
if errorlevel 1 exit /b 30
echo === STEP 4: verify from the bundle with no TEXINPUTS ===
rmdir /s /q _verify 2>nul
xcopy /e /i /q submission _verify >nul
cd /d "%~dp0_verify"
set TEXINPUTS=
latexmk -xelatex -g -interaction=nonstopmode -halt-on-error paper.tex
if errorlevel 1 (
  echo *** arXiv simulation FAILED - the bundle does not build on its own ***
  exit /b 40
)
dir /b paper.pdf
cd /d "%~dp0"
echo === DONE: submission/ and submission.zip are ready ===
endlocal
