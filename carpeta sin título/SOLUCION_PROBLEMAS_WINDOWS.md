# 🛠️ Solución de Problemas Windows - BLE Scanner

## 🚨 Problemas Comunes y Soluciones

### 1. **Error: "Python no es reconocido como comando interno"**

**Causa**: Python no está en el PATH del sistema
**Solución**:
```cmd
# Opción A: Reinstalar Python
1. Descargar Python desde https://python.org
2. Durante instalación: ✅ MARCAR "Add Python to PATH"
3. Reiniciar Command Prompt

# Opción B: Agregar manualmente al PATH
1. Win + R → "sysdm.cpl" → Enter
2. Pestaña "Advanced" → "Environment Variables"
3. Agregar ruta de Python (ej: C:\Python\)
```

### 2. **Error: "COM port no responde" o "Device not found"**

**Diagnóstico**:
```cmd
# Ver puertos COM disponibles
wmic path Win32_SerialPort get Name,DeviceID

# Ver dispositivos USB
wmic path Win32_USBHub get Name,DeviceID
```

**Soluciones**:
1. **Verificar conexión física**:
   - Cable USB funcionando
   - nRF52DK encendido (LEDs activos)
   - Probar diferentes puertos USB

2. **Actualizar drivers**:
   - Device Manager → nRF52DK → Update Driver
   - Descargar drivers Nordic desde su web oficial

3. **Configurar puerto correcto**:
   ```python
   # En config.py cambiar:
   COM_PORT: str = "COM4"  # Probar COM3, COM4, COM5, etc.
   ```

### 3. **Error: "No module named 'pc_ble_driver_py'"**

**Solución completa**:
```cmd
# 1. Verificar versión de Python (debe ser 3.7+)
python --version

# 2. Actualizar pip
python -m pip install --upgrade pip

# 3. Instalar driver específico
pip install pc-ble-driver-py --no-cache-dir

# 4. Si falla, instalar desde requirements
pip install -r requirements.txt --force-reinstall

# 5. Verificar instalación
python -c "import pc_ble_driver_py; print('✅ Driver OK')"
```

### 4. **Error: "Permission denied" o "Access denied"**

**Soluciones**:
```cmd
# Opción A: Ejecutar como Administrador
1. Click derecho en Command Prompt
2. "Run as administrator"
3. Navegar al proyecto y ejecutar

# Opción B: Cambiar permisos de carpeta
1. Click derecho en carpeta del proyecto
2. Properties → Security → Edit
3. Dar permisos completos al usuario actual
```

### 5. **Error: "No devices found" durante el escaneo**

**Diagnóstico paso a paso**:
```cmd
# 1. Verificar configuración
python -c "from config import config; print(f'Puerto: {config.COM_PORT}, MACs: {config.VALID_MAC_IDS}')"

# 2. Test de conectividad
python -c "from scanner.driver import BLEDriverManager; mgr = BLEDriverManager('COM3'); mgr.initialize_driver(); print('✅ Conexión OK')"
```

**Soluciones**:
1. **Verificar dispositivos BLE**:
   - Dispositivos encendidos y funcionando
   - Distancia < 2 metros del nRF52DK
   - Baterías suficientes para transmitir

2. **Ajustar configuración**:
   ```python
   # En config.py:
   SCAN_TIME: int = 20        # Aumentar tiempo de escaneo
   BATTERY_THRESHOLD: int = 2500  # Bajar umbral si es necesario
   ```

3. **Verificar MACs**:
   - Usar MACs reales de dispositivos BLE
   - Formato correcto: "AABBCCDDEEFF" (sin `:` ni `-`)

### 6. **Problemas con Antivirus/Firewall**

**Configuración Windows Defender**:
```cmd
# Agregar excepción para la carpeta del proyecto
1. Windows Security → Virus & threat protection
2. Exclusions → Add or remove exclusions
3. Agregar carpeta del proyecto completa

# Permitir Python en Firewall
1. Windows Security → Firewall & network protection
2. Allow an app through firewall
3. Buscar Python.exe y permitir
```

### 7. **Error: "Failed to initialize BLE driver"**

**Solución Nordic específica**:
```cmd
# 1. Verificar que no hay otros programas usando nRF52DK
# (nRF Connect, J-Link, etc.)

# 2. Reset del dispositivo
# Desconectar USB → Esperar 10s → Reconectar

# 3. Verificar firmware
# El driver puede flashear automáticamente si auto_flash=True

# 4. Test manual de conexión
python -c "
from pc_ble_driver_py import BLEDriver
driver = BLEDriver(serial_port='COM3', auto_flash=True)
driver.open()
print('✅ Driver inicializado correctamente')
driver.close()
"
```

### 8. **Rendimiento Lento en Windows**

**Optimizaciones**:
```python
# En config.py:
SCAN_TIME: int = 15           # Tiempo óptimo para Windows
LOG_LEVEL: str = "WARNING"    # Reducir logs para mejor rendimiento

# Variables de entorno Windows:
set PYTHONUNBUFFERED=1
set PYTHONOPTIMIZE=1
```

### 9. **Problemas con Archivos de Resultados**

**Permisos de escritura**:
```cmd
# Verificar permisos de la carpeta
icacls "." /grant "%USERNAME%":(F)

# Cambiar ubicación de salida si es necesario
# En config.py:
OUTPUT_JSON_FILE: str = "C:\\temp\\battery_results.json"
OUTPUT_CSV_FILE: str = "C:\\temp\\battery_results.csv"
```

### 10. **Script de Diagnóstico Automático**

```batch
@echo off
echo 🔍 DIAGNOSTICO AUTOMATICO WINDOWS
echo ================================

echo Información del sistema:
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"

echo.
echo Verificando Python:
python --version 2>nul || echo "❌ Python no encontrado"

echo.
echo Verificando dependencias:
pip show pc-ble-driver-py 2>nul || echo "❌ Nordic driver faltante"

echo.
echo Puertos COM disponibles:
wmic path Win32_SerialPort get Name,DeviceID 2>nul

echo.
echo Variables de entorno PATH (Python):
echo %PATH% | findstr /I python

echo.
echo Test básico del proyecto:
cd /d "%~dp0"
python -c "import sys; print(f'Python desde: {sys.executable}')" 2>nul

echo.
echo ✅ Diagnóstico completado
pause
```

---

## 📋 Lista de Verificación Final

**Antes de ejecutar el scanner**:
- [ ] Python 3.7+ instalado con PATH configurado
- [ ] nRF52DK conectado y reconocido
- [ ] Puerto COM identificado y configurado
- [ ] Dependencias instaladas (pc-ble-driver-py, pandas, numpy)
- [ ] MACs de dispositivos BLE configuradas
- [ ] Permisos de escritura en carpeta del proyecto
- [ ] Ningún otro software usando el nRF52DK

**Para soporte adicional**: Ejecutar `verificar_windows.bat` y revisar logs en `ble_scanner.log`
