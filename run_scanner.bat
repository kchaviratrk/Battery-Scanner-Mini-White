@echo off
title BLE Scanner for CR2032 Batteries

:MENU
cls
echo.
echo 🔋 BLE SCANNER FOR CR2032 BATTERIES
echo ====================================================
echo Windows deployment: c:/Battery-Scanner-Mini-White
echo.
echo 1. System Check
echo 2. Install Dependencies
echo 3. Run Scanner
echo 4. View Results
echo 5. Configuration
echo 6. Help
echo 0. Exit
echo.
set /p choice="Select option (0-6): "

if "%choice%"=="1" goto CHECK
if "%choice%"=="2" goto INSTALL
if "%choice%"=="3" goto SCAN
if "%choice%"=="4" goto RESULTS
if "%choice%"=="5" goto CONFIG
if "%choice%"=="6" goto HELP
if "%choice%"=="0" goto EXIT
goto MENU

:CHECK
cls
echo 🔍 SYSTEM CHECK
echo ====================================================
python --version 2>nul || echo ❌ Python not found - install from python.org
echo.
echo COM Ports:
wmic path Win32_SerialPort get DeviceID,Name 2>nul | findstr COM
echo.
if not exist "c:\Battery-Scanner-Mini-White" mkdir "c:\Battery-Scanner-Mini-White"
if not exist "c:\Battery-Scanner-Mini-White\results" mkdir "c:\Battery-Scanner-Mini-White\results" 
if not exist "c:\Battery-Scanner-Mini-White\logs" mkdir "c:\Battery-Scanner-Mini-White\logs"
echo ✅ Directory structure ready
echo.
python -c "import pc_ble_driver_py; print('✅ Nordic driver OK')" 2>nul || echo ❌ Nordic driver missing
pause
goto MENU

:INSTALL
cls
echo 📦 INSTALLING DEPENDENCIES
echo ====================================================
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
if %errorlevel% equ 0 (echo ✅ Installation complete) else (echo ❌ Installation failed)
pause
goto MENU

:SCAN
cls
echo 📡 RUNNING BLE SCANNER
echo ====================================================
echo ⚠️  Ensure nRF52DK is connected and COM port configured
echo.
set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" goto MENU
echo.
python ble_scanner.py
echo.
echo Results saved to c:/Battery-Scanner-Mini-White/results/
pause
goto MENU

:RESULTS
cls
echo 📊 VIEWING RESULTS
echo ====================================================
if exist "c:\Battery-Scanner-Mini-White\results\battery_results.json" (
    echo ✅ JSON results available
    set /p open="Open results? (y/N): "
    if /i "%open%"=="y" start notepad "c:\Battery-Scanner-Mini-White\results\battery_results.json"
) else (
    echo ❌ No results found - run scanner first
)
pause
goto MENU

:CONFIG
cls
echo ⚙️  CONFIGURATION
echo ====================================================
echo Opening config.py for editing...
echo.
echo Key settings:
echo - COM_PORT: nRF52DK COM port
echo - VALID_MAC_IDS: Target device addresses
echo.
start notepad config.py
pause
goto MENU

:HELP
cls
echo 📖 HELP
echo ====================================================
echo.
echo SETUP:
echo 1. Install Python from python.org
echo 2. Connect nRF52DK to USB
echo 3. Check Device Manager for COM port
echo 4. Update COM_PORT in config.py
echo.
echo BATTERY LEVELS:
echo 🟢 NEW (3000-3300mV) - Fresh battery
echo 🟡 OK (2850-2999mV) - Good condition
echo 🟠 LOW (2750-2849mV) - Replace soon
echo 🔴 DEAD (≤2750mV) - Replace immediately
echo.
pause
goto MENU

:EXIT
echo.
echo 👋 Thank you for using BLE Scanner!
echo Results: c:/Battery-Scanner-Mini-White/results/
pause
exit
