@echo off
chcp 65001 > nul
setlocal

for /F "delims=" %%e in ('echo prompt $E^| cmd') do set "ESC=%%e"
set "RESET=%ESC%[0m"
set "GREEN=%ESC%[1;32m"
set "RED=%ESC%[1;31m"
set "CYAN=%ESC%[1;36m"

echo 🐍 Python Environment Setup

cd /d %~dp0

echo.

echo %CYAN%[Step 1]%RESET% Refresh Virtual Environment
if exist .venv (
    echo ├─ Deleting existing .venv...
    rmdir /s /q .venv 2>nul
    echo ├─ ✅ %GREEN%.venv deleted successfully%RESET%
) else (
    echo ├─ No existing .venv found
)
echo ├─ Creating new virtual environment...
py -3.11 -m venv .venv
if %errorlevel% equ 0 (
    echo └─ ✅ %GREEN%Virtual environment created successfully%RESET%
) else (
    echo └─ ❌ %RED%Failed to create virtual environment%RESET%
    pause
    exit /b 1
)

echo.

echo %CYAN%[Step 2]%RESET% Activate Virtual Environment
echo ├─ Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% equ 0 (
    echo └─ ✅ %GREEN%Virtual environment activated successfully%RESET%
) else (
    echo └─ ❌ %RED%Failed to activate virtual environment%RESET%
    pause
    exit /b 1
)

echo.

echo %CYAN%[Step 3]%RESET% Upgrade pip
echo ├─ Upgrading pip...
python -m pip install --upgrade pip --quiet
if %errorlevel% equ 0 (
    echo └─ ✅ %GREEN%pip upgraded successfully%RESET%
) else (
    echo └─ ❌ %RED%Failed to upgrade pip%RESET%
    pause
    exit /b 1
)

echo.

echo %CYAN%[Step 4]%RESET% Install Dependencies
echo ├─ Installing dependencies from pyproject.toml...
pip install -e . --quiet
if %errorlevel% equ 0 (
    echo └─ ✅ %GREEN%Dependencies installed successfully%RESET%
) else (
    echo └─ ❌ %RED%Failed to install dependencies%RESET%
    pause
    exit /b 1
)

echo.

echo %CYAN%[Done]%RESET% 🎉 Setup completed successfully!

pause
