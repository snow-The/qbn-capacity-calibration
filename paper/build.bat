@echo off
setlocal
REM Typst uses single stars for bold; Markdown ** is only a warning, so fail early.
REM Why --root: paper_en.typ imports the local typst-arxiv-style package through a
REM relative path, and a relative import may not escape the Typst project root.
REM
REM Naming: the Typst builds write paper-typst-zh.pdf / paper-typst-en.pdf.
REM They used to write paper.pdf / paper_en.pdf, which COLLIDED with the LaTeX
REM builds (paper.tex -> paper.pdf) -- whichever ran last silently won, so the
REM file called paper.pdf was sometimes the Chinese Typst paper.
pushd "%~dp0..\..\.."
set ROOT=%CD%
popd
cd /d "%~dp0"
if not exist paper.typ (
  echo *** paper.typ not found ***
  exit /b 1
)
echo === GUARD: no ** in paper.typ ===
findstr /C:"**" paper.typ >nul
if not errorlevel 1 (
  echo *** FOUND ** IN paper.typ - Typst only accepts single stars: ***
  findstr /N /C:"**" paper.typ
  exit /b 2
)
echo guard passed
echo === typst compile paper.typ (zh) ===
typst compile --root "%ROOT%" paper.typ paper-typst-zh.pdf 2>warn.txt
type warn.txt
echo [END-OF-WARNINGS]
if not exist paper-typst-zh.pdf (
  echo *** paper-typst-zh.pdf was not produced ***
  exit /b 3
)
dir /b paper-typst-zh.pdf
endlocal
