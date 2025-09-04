@echo off
REM ====================================================
REM    BLE CR2032 SCANNER - WINDOWS MAIN MENU
REM ====================================================

:MENU
cls
echo.
echo 🔋 BLE CR2032 SCANNER - MAIN MENU
echo ====================================================
echo.
echo 1. Verify System
echo 2. Install Dependencies
echo 3. Run CR2032 Demo
echo 4. Run Main Scanner
echo 5. View Results
echo 6. Open Configuration
echo 7. View Help
echo 0. Exit
echo.
set /p choice="Select an option (0-7): "

if "%choice%"=="1" goto VERIFY
if "%choice%"=="2" goto INSTALL
if "%choice%"=="3" goto DEMO
if "%choice%"=="4" goto SCANNER
if "%choice%"=="5" goto RESULTS
if "%choice%"=="6" goto CONFIG
if "%choice%"=="7" goto HELP
if "%choice%"=="0" goto EXIT

echo Invalid option. Press any key to continue...
pause >nul
goto MENU

:VERIFY
cls
echo 🔍 VERIFYING SYSTEM...
echo ====================================================
echo Checking Python 3.10 installation (REQUIRED for pc-ble-driver)...
py -3.10 --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python 3.10 found and compatible
    py -3.10 --version
) else (
    echo ❌ Python 3.10 NOT found - REQUIRED for Nordic driver
    echo.
    echo 🚨 CRITICAL: pc-ble-driver-py requires Python 3.10.x
    echo 📥 Download Python 3.10.11 from: https://python.org/downloads/release/python-31011/
    echo ⚠️  Install alongside your current Python (don't uninstall 3.13)
    echo.
    pause
    goto MENU
)
echo.
echo Checking pip for Python 3.10...
py -3.10 -m pip --version
echo.
echo Checking nRF52DK driver...
echo Make sure nRF52DK is connected to COM port (default: COM3)
echo.
echo Press any key to return to menu...
pause >nul
pause >nul
goto MENU

:INSTALL
cls
echo 📦 INSTALLING DEPENDENCIES...
echo ====================================================
echo Installing dependencies with Python 3.10 (required for Nordic driver)...
py -3.10 -m pip install -r requirements.txt
echo.
if %errorlevel% equ 0 (
    echo ✅ Dependencies installed successfully with Python 3.10!
) else (
    echo ❌ Error installing dependencies.
    echo 💡 Make sure Python 3.10 is installed (required for pc-ble-driver-py)
    echo 📥 Download from: https://python.org/downloads/release/python-31011/
)
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:DEMO
cls
echo 🎬 RUNNING CR2032 DEMO...
echo ====================================================
echo This will show CR2032 battery evaluation examples
py -3.10 -c "from scanner.battery_evaluator import evaluate_battery; print('Demo: CR2032 at 3100mV:', evaluate_battery(3100)); print('Demo: CR2032 at 2800mV:', evaluate_battery(2800))"
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:SCANNER
cls
echo 📡 RUNNING MAIN SCANNER...
echo ====================================================
echo ⚠️  IMPORTANT: Make sure nRF52DK is connected
echo    and COM port is configured correctly.
echo 🐍 Using Python 3.10 (required for Nordic driver)
echo.
set /p continue="Continue? (y/N): "
if /i not "%continue%"=="y" goto MENU

py -3.10 ble_scanner.py
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:RESULTS
cls
echo 📊 VIEWING RESULTS...
echo ====================================================
echo Checking for result files...
if exist battery_scan_results.json (
    echo ✅ JSON results found: battery_scan_results.json
    echo Opening JSON file...
    start notepad battery_scan_results.json
) else (
    echo ❌ No JSON results file found
)
echo.
if exist battery_scan_results.csv (
    echo ✅ CSV results found: battery_scan_results.csv
    echo Opening CSV file...
    start excel battery_scan_results.csv 2>nul || start notepad battery_scan_results.csv
) else (
    echo ❌ No CSV results file found
)
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:CONFIG
cls
echo ⚙️ OPENING CONFIGURATION...
echo ====================================================
echo Opening config.py for editing...
start notepad config.py
echo.
echo 💡 Edit COM_PORT, VALID_MAC_IDS, and other settings as needed
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:HELP
cls
echo 📖 HELP AND INSTRUCTIONS...
echo ====================================================
echo.
echo BLE CR2032 Scanner Help:
echo.
echo 1. SETUP:
echo    - Install Python 3.7+ on Windows
echo    - Connect nRF52DK to USB port
echo    - Install Nordic drivers
echo    - Use option 2 to install Python dependencies
echo.
echo 2. CONFIGURATION:
echo    - Edit config.py to set correct COM port (usually COM3 or COM4)
echo    - Add target MAC addresses to VALID_MAC_IDS list
echo    - Adjust scan time and battery thresholds if needed
echo.
echo 3. USAGE:
echo    - Use option 4 to run main scanner
echo    - Results are saved as JSON and CSV files
echo    - Use option 5 to view results
echo.
echo 4. TROUBLESHOOTING:
echo    - Check Device Manager for nRF52DK COM port
echo    - Ensure no other BLE software is using the device
echo    - Try different COM ports if connection fails
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:EXIT
cls
echo.
echo 👋 Thanks for using BLE CR2032 Scanner!
echo.
pause
exit

REM ====================================================
REM    ERROR HANDLING
REM ====================================================

:ERROR
echo.
echo ❌ An error occurred. Please check:
echo    - Python is installed and in PATH
echo    - nRF52DK is connected
echo    - Dependencies are installed
echo.
pause
goto MENU
echo ====================================================
echo.
if exist battery_scan_results.json (
    echo ✅ battery_scan_results.json encontrado
    echo    Contiene datos detallados con evaluación CR2032
) else (
    echo ❌ battery_scan_results.json no encontrado
    echo    Ejecuta el escáner primero
)
echo.
if exist battery_scan_results.csv (
    echo ✅ battery_scan_results.csv encontrado
    echo    Ideal para análisis en Excel
    set /p open_csv="¿Abrir CSV en Excel? (s/N): "
    if /i "%open_csv%"=="s" start battery_scan_results.csv
) else (
    echo ❌ battery_scan_results.csv no encontrado
    echo    Ejecuta el escáner primero
)
echo.
if exist ble_scanner.log (
    echo ✅ ble_scanner.log encontrado
    echo    Contiene logs técnicos detallados
    set /p open_log="¿Ver logs? (s/N): "
    if /i "%open_log%"=="s" type ble_scanner.log | more
) else (
    echo ❌ ble_scanner.log no encontrado
)
echo.
echo Presiona cualquier tecla para volver al menú...
pause >nul
goto MENU

:CONFIG
cls
echo ⚙️ CONFIGURACIÓN...
echo ====================================================
echo.
echo Archivo de configuración: config.py
echo.
echo 📝 Configuraciones importantes:
echo    - COM_PORT: Puerto del nRF52DK
echo    - VALID_MAC_IDS: MACs de dispositivos a escanear
echo    - SCAN_TIME: Tiempo de escaneo en segundos
echo    - CR2032_*: Umbrales específicos de CR2032
echo.
set /p open_config="¿Abrir config.py para editar? (s/N): "
if /i "%open_config%"=="s" notepad config.py
echo.
echo 💡 Después de modificar config.py, reinicia el escáner.
echo.
echo Presiona cualquier tecla para volver al menú...
pause >nul
goto MENU

:HELP
cls
echo 📚 AYUDA Y DOCUMENTACIÓN
echo ====================================================
echo.
echo 📄 Archivos de documentación disponibles:
echo.
echo 1. INSTRUCTIVO_WINDOWS.md  - Guía completa paso a paso
echo 2. COMANDOS_RAPIDOS.md     - Referencias rápidas
echo 3. README.md               - Documentación técnica
echo 4. RESUMEN_EJECUTIVO.md    - Resumen del proyecto
echo.
echo 🔧 Solución de problemas comunes:
echo.
echo • Puerto COM incorrecto:
echo   - Win + X → Administrador de dispositivos
echo   - Buscar "Puertos (COM y LPT)"
echo   - Actualizar COM_PORT en config.py
echo.
echo • Python no reconocido:
echo   - Reinstalar Python desde python.org
echo   - Marcar "Add Python to PATH"
echo.
echo • No se detectan dispositivos:
echo   - Verificar que estén encendidos
echo   - Acercar al nRF52DK
echo   - Aumentar SCAN_TIME en config.py
echo.
echo • Dependencias faltantes:
echo   - Ejecutar: pip install -r requirements.txt
echo.
set /p open_doc="¿Abrir instructivo completo? (s/N): "
if /i "%open_doc%"=="s" notepad INSTRUCTIVO_WINDOWS.md
echo.
echo Presiona cualquier tecla para volver al menú...
pause >nul
goto MENU

:EXIT
cls
echo.
echo 👋 Gracias por usar el Escáner BLE CR2032
echo.
echo 💡 Recuerda:
echo    - Verificar sistema antes del primer uso
echo    - Configurar puerto COM correctamente
echo    - Mantener nRF52DK conectado durante escaneo
echo.
echo ¡Hasta pronto!
echo.
pause
exit

REM ====================================================
REM  Fin del script - Escáner BLE CR2032 v1.0
REM ====================================================
