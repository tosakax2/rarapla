@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

for /F "delims=" %%e in ('echo prompt $E^| cmd') do set "ESC=%%e"
set "RESET=%ESC%[0m"
set "GREEN=%ESC%[1;32m"
set "RED=%ESC%[1;31m"
set "CYAN=%ESC%[1;36m"

echo 🔨 RaRaPla Nuitka Build

cd /d %~dp0

set "OUTDIR=build"
set "EXENAME=RaRaPla"

echo.

echo %CYAN%[Step 1]%RESET% Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    if %errorlevel% neq 0 (
        echo └─ ❌ %RED%Failed to activate venv%RESET%
        pause & exit /b 1
    )
    echo └─ ✅ %GREEN%venv activated%RESET%
) else (
    echo └─ ❌ %RED%.venv not found - please run setup_env.bat first%RESET%
    pause & exit /b 1
)

echo.

echo %CYAN%[Step 2]%RESET% Upgrade Nuitka
python -m pip install --upgrade --quiet nuitka wheel
if %errorlevel% neq 0 (
    echo └─ ❌ %RED%Failed to install/upgrade Nuitka%RESET%
    pause & exit /b 1
)
echo └─ ✅ %GREEN%Nuitka ready%RESET%

echo.

echo %CYAN%[Step 3]%RESET% Clean previous build directory
if exist "%OUTDIR%" (
    rmdir /s /q "%OUTDIR%"
    echo └─ ✅ %GREEN%Old build removed%RESET%
) else (
    echo └─ No existing build directory
)

echo.

echo %CYAN%[Step 4]%RESET% Compile project with Nuitka
python -m nuitka ^
    --standalone ^
    --windows-disable-console
    --enable-plugin=pyside6 ^
    --include-data-files=icon.ico=icon.ico ^
    --include-data-files=rb_presets.json=rb_presets.json ^
    --windows-icon-from-ico=icon.ico ^
    --output-dir="%OUTDIR%" ^
    --output-filename="%EXENAME%" ^
    src\rarapla\__main__.py
if %errorlevel% neq 0 (
    echo └─ ❌ %RED%Build failed%RESET%
    pause & exit /b 1
)
echo └─ ✅ %GREEN%Build succeeded%RESET%

echo.

echo %CYAN%[Done]%RESET% 🎉 Build finished successfully!

pause
