@echo off
REM ====================================================
REM    CONFIGURACION PYTHON 3.10 PARA BLE SCANNER
REM ====================================================

echo.
echo 🐍 CONFIGURACION PYTHON 3.10 - BLE Scanner
echo ====================================================
echo.

echo 🔍 DETECTANDO VERSIONES DE PYTHON INSTALADAS...
echo.

REM Detectar Python 3.13 (actual)
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python por defecto detectado:
    python --version
) else (
    echo ❌ Python por defecto no encontrado
)

echo.

REM Detectar Python 3.10 (requerido)
py -3.10 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python 3.10 detectado (COMPATIBLE):
    py -3.10 --version
    goto :python310_found
) else (
    echo ❌ Python 3.10 NO detectado (REQUERIDO)
    goto :install_python310
)

:install_python310
echo.
echo 🚨 PROBLEMA CRÍTICO: pc-ble-driver-py requiere Python 3.10.x
echo.
echo 📥 DESCARGA REQUERIDA:
echo    URL: https://python.org/downloads/release/python-31011/
echo    Archivo: Windows installer (64-bit)
echo.
echo ⚠️  IMPORTANTE: Durante la instalación
echo    1. ✅ Marcar "Add Python to PATH"
echo    2. ✅ Permitir instalación junto a Python 3.13
echo    3. ✅ NO desinstalar Python 3.13 existente
echo.
echo 💡 Después de instalar, ejecutar este script nuevamente
echo.
set /p open_url="¿Abrir página de descarga? (s/N): "
if /i "%open_url%"=="s" start https://python.org/downloads/release/python-31011/
echo.
pause
exit /b 1

:python310_found
echo.
echo ✅ PYTHON 3.10 ENCONTRADO - Procediendo con configuración
echo.

REM Verificar pip para Python 3.10
echo 🔧 VERIFICANDO PIP PARA PYTHON 3.10...
py -3.10 -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ pip funcionando con Python 3.10
    py -3.10 -m pip --version
) else (
    echo ❌ pip no disponible para Python 3.10
    echo 🔧 Instalando pip...
    py -3.10 -m ensurepip --upgrade
)

echo.

REM Instalar dependencias con Python 3.10
echo 📦 INSTALANDO DEPENDENCIAS CON PYTHON 3.10...
echo.

echo Instalando pc-ble-driver-py...
py -3.10 -m pip install pc-ble-driver-py>=0.17.0

echo Instalando pandas...
py -3.10 -m pip install pandas>=1.5.0

echo Instalando numpy...
py -3.10 -m pip install numpy>=1.21.0

echo.

REM Verificar instalación
echo 🧪 VERIFICANDO INSTALACION...
echo.

py -3.10 -c "import pc_ble_driver_py; print('✅ Nordic driver: OK')" 2>nul
if %errorlevel% neq 0 echo ❌ Error: Nordic driver no instalado

py -3.10 -c "import pandas; print('✅ pandas: OK')" 2>nul
if %errorlevel% neq 0 echo ❌ Error: pandas no instalado

py -3.10 -c "import numpy; print('✅ numpy: OK')" 2>nul
if %errorlevel% neq 0 echo ❌ Error: numpy no instalado

echo.

REM Test del scanner
echo 🔬 TEST DEL SCANNER...
py -3.10 -c "from scanner.driver import BLEDriverManager; print('✅ Scanner modules: OK')" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Módulos del scanner funcionando correctamente
) else (
    echo ❌ Error en módulos del scanner
)

echo.

REM Configuración final
echo ====================================================
echo 🎯 CONFIGURACION COMPLETADA
echo ====================================================
echo.

echo 📋 COMANDOS PARA USAR:
echo.
echo ▶️  Ejecutar scanner:
echo    py -3.10 ble_scanner.py
echo.
echo 🔍 Verificar configuración:
echo    py -3.10 -c "from config import config; print(config.COM_PORT)"
echo.
echo 📦 Instalar más dependencias:
echo    py -3.10 -m pip install [paquete]
echo.
echo 📝 Script interactivo:
echo    run_scanner.bat (ya configurado para Python 3.10)
echo.

echo ====================================================
echo 🚀 SISTEMA LISTO PARA USAR CON PYTHON 3.10
echo ====================================================
echo.
echo 💡 RECORDATORIO:
echo    - Tu Python 3.13 sigue disponible como "python"
echo    - Usar "py -3.10" para este proyecto específicamente
echo    - El menú run_scanner.bat ya está configurado
echo.

pause
