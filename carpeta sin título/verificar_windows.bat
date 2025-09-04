@echo off
REM ====================================================
REM    VERIFICACION COMPLETA DEL SISTEMA WINDOWS
REM ====================================================

echo.
echo 🪟 VERIFICACION DEL SISTEMA WINDOWS
echo ====================================================
echo.

REM Verificar Python
echo 1. VERIFICANDO PYTHON 3.10 (REQUERIDO)...
py -3.10 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python 3.10 instalado correctamente (COMPATIBLE)
    py -3.10 --version
) else (
    echo ❌ Python 3.10 NO encontrado (REQUERIDO para pc-ble-driver)
    echo.
    echo 🚨 CRÍTICO: pc-ble-driver-py solo funciona con Python 3.10.x
    echo � Descargar Python 3.10.11 desde: 
    echo     https://python.org/downloads/release/python-31011/
    echo.
    echo ⚠️  IMPORTANTE: Instalar JUNTO a tu Python 3.13 (no reemplazar)
    echo 💡 Después usar: py -3.10 para ejecutar comandos
    echo.
    pause
    exit /b 1
)

echo.

REM Verificar pip
echo 2. VERIFICANDO PIP PARA PYTHON 3.10...
py -3.10 -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ pip disponible para Python 3.10
    py -3.10 -m pip --version
) else (
    echo ❌ pip NO encontrado para Python 3.10
    pause
    exit /b 1
)

echo.

REM Verificar dependencias críticas
echo 3. VERIFICANDO DEPENDENCIAS...

echo Verificando pc-ble-driver-py...
py -3.10 -c "import pc_ble_driver_py; print('✅ Nordic driver OK')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Nordic driver faltante
    echo 🔧 Instalando automáticamente con Python 3.10...
    py -3.10 -m pip install pc-ble-driver-py
)

echo Verificando pandas...
py -3.10 -c "import pandas; print('✅ pandas OK')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ pandas faltante
    echo 🔧 Instalando automáticamente...
    py -3.10 -m pip install pandas
)

echo Verificando numpy...
py -3.10 -c "import numpy; print('✅ numpy OK')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ numpy faltante
    echo 🔧 Instalando automáticamente...
    py -3.10 -m pip install numpy
)

echo.

REM Verificar configuración
echo 4. VERIFICANDO CONFIGURACION...
if exist config.py (
    echo ✅ config.py encontrado
    py -3.10 -c "from config import config; print(f'Puerto COM configurado: {config.COM_PORT}')"
    py -3.10 -c "from config import config; print(f'MACs válidas: {len(config.VALID_MAC_IDS)}')"
) else (
    echo ❌ config.py NO encontrado
    pause
    exit /b 1
)

echo.

REM Verificar archivos principales
echo 5. VERIFICANDO ARCHIVOS PRINCIPALES...
if exist ble_scanner.py (
    echo ✅ ble_scanner.py
) else (
    echo ❌ ble_scanner.py faltante
)

if exist scanner\ (
    echo ✅ Carpeta scanner/
) else (
    echo ❌ Carpeta scanner/ faltante
)

if exist requirements.txt (
    echo ✅ requirements.txt
) else (
    echo ❌ requirements.txt faltante
)

echo.

REM Verificar puertos COM disponibles
echo 6. VERIFICANDO PUERTOS COM...
echo Puertos COM disponibles:
wmic path Win32_SerialPort get Name,DeviceID 2>nul | findstr COM
if %errorlevel% neq 0 (
    echo ⚠️  No se detectaron puertos COM específicos
    echo 💡 Conectar nRF52DK y verificar en Device Manager
)

echo.

REM Test básico del scanner
echo 7. TEST BASICO DEL SCANNER CON PYTHON 3.10...
py -3.10 -c "from scanner.driver import BLEDriverManager; print('✅ Driver manager OK')" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Módulos del scanner funcionando con Python 3.10
) else (
    echo ❌ Error en módulos del scanner
    echo 🔧 Verificar instalación de dependencias con Python 3.10
)

echo.

REM Resumen final
echo ====================================================
echo 📊 RESUMEN DE VERIFICACION - PYTHON 3.10
echo ====================================================

py -3.10 -c "
import sys
from config import config
print(f'✅ Python: {sys.version.split()[0]} (Compatible con Nordic)')
print(f'✅ Puerto COM: {config.COM_PORT}')
print(f'✅ Tiempo de escaneo: {config.SCAN_TIME}s')
print(f'✅ MACs configuradas: {len(config.VALID_MAC_IDS)}')
print()
print('🎯 SIGUIENTE PASO: Conectar nRF52DK y ejecutar scanner')
print('📝 COMANDO: py -3.10 ble_scanner.py')
"

echo.
echo ====================================================
echo 🚀 SISTEMA LISTO PARA WINDOWS CON PYTHON 3.10
echo ====================================================
echo.
echo 💡 Para ejecutar el scanner:
echo    1. Conectar nRF52DK al USB
echo    2. Verificar puerto COM en Device Manager
echo    3. Actualizar config.py si es necesario
echo    4. Ejecutar: py -3.10 ble_scanner.py
echo.
echo 📋 Para usar menú interactivo:
echo    1. Ejecutar: run_scanner.bat
echo.

pause
