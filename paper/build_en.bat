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
if not exist paper_en.typ (
  echo *** paper_en.typ not found ***
  exit /b 1
)
echo === GUARD: no ** in paper_en.typ ===
findstr /C:"**" paper_en.typ >nul
if not errorlevel 1 (
  echo *** FOUND ** IN paper_en.typ - Typst only accepts single stars: ***
  findstr /N /C:"**" paper_en.typ
  exit /b 2
)
echo guard passed
echo === typst compile paper_en.typ (en) ===
typst compile --root "%ROOT%" paper_en.typ paper-typst-en.pdf 2>warn_en.txt
type warn_en.txt
echo [END-OF-WARNINGS]
if not exist paper-typst-en.pdf (
  echo *** paper-typst-en.pdf was not produced ***
  exit /b 3
)
dir /b paper-typst-en.pdf
endlocal
