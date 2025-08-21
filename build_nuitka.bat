@echo off

set OUTDIR=core
set EXENAME=RaRaPla
set DISTNAME=RaRaPla

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

python -m pip install --upgrade --quiet nuitka

if exist %OUTDIR% rmdir /s /q %OUTDIR%

python -m nuitka ^
    --enable-plugin=pyside6 ^
    --include-data-files=icon.ico=icon.ico ^
    --include-data-files=rb_presets.json=rb_presets.json ^
    --output-dir=%OUTDIR% ^
    --windows-icon-from-ico=icon.ico ^
    --output-filename=%EXENAME% ^
    src\rarapla\__main__.py

if exist "%OUTDIR%\%EXENAME%.dist" (
    ren "%OUTDIR%\%EXENAME%.dist" "%DISTNAME%"
)

pause
