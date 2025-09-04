# 🪟 Guía Completa para Windows - BLE Scanner CR2032

## 📋 Requisitos del Sistema

### Software Requerido:
- **Windows 10/11** (64-bit recomendado)
- **Python 3.7+** desde [python.org](https://python.org)
- **Nordic nRF52DK** conectado por USB
- **Drivers USB** (se instalan automáticamente)

### Hardware Necesario:
- Nordic nRF52DK development board
- Cable USB tipo micro-USB
- Dispositivos BLE con baterías CR2032 para escanear

## 🚀 Instalación Paso a Paso

### Paso 1: Instalación de Python
1. Descarga Python desde https://python.org/downloads/
2. **IMPORTANTE**: Marca "Add Python to PATH" durante la instalación
3. Verifica la instalación:
   ```cmd
   python --version
   pip --version
   ```

### Paso 2: Preparación del Proyecto
1. Abre **Command Prompt** o **PowerShell** como Administrador
2. Navega a la carpeta del proyecto:
   ```cmd
   cd "C:\ruta\a\Battery Scanner Mini White"
   ```

### Paso 3: Instalación de Dependencias
```cmd
pip install -r requirements.txt
```

### Paso 4: Conexión del Hardware
1. Conecta el nRF52DK al puerto USB
2. Abre **Device Manager** (Administrador de dispositivos)
3. Busca en "Ports (COM & LPT)" el puerto asignado (ej: COM3, COM4)
4. Anota el número de puerto para la configuración

## ⚙️ Configuración Inicial

### Configurar Puerto COM
Edita el archivo `config.py`:
```python
# nRF52DK COM port (adjust according to system)
COM_PORT: str = "COM3"  # Cambia por tu puerto (COM3, COM4, etc.)
```

### Configurar MACs de Dispositivos
Agrega las direcciones MAC de tus dispositivos BLE:
```python
VALID_MAC_IDS: List[str] = [
    "A1B2C3D4E5F6",  # Reemplaza con MACs reales
    "112233445566", 
    "AABBCCDDEEFF",
    "123456789ABC"
]
```

## 🎯 Métodos de Ejecución

### Método 1: Script Automático (Recomendado)
```cmd
run_scanner.bat
```
Este script incluye un menú interactivo con todas las opciones.

### Método 2: Ejecución Directa
```cmd
python ble_scanner.py
```

### Método 3: Con Parámetros Personalizados
```cmd
python ble_scanner.py --scan-time 15 --min-rssi -100
```

## 📊 Interpretación de Resultados

### Categorías de Batería CR2032:
- 🟢 **NEW (3000-3300mV)**: Batería nueva, excelente estado
- 🟡 **OK (2850-2999mV)**: Buen estado operacional
- 🟠 **LOW (2750-2849mV)**: Cerca del agotamiento, reemplazar pronto
- 🔴 **DEAD (≤2750mV)**: Agotada, reemplazar inmediatamente

### Archivos de Salida:
- `battery_scan_results_*.json`: Datos detallados en formato JSON
- `battery_scan_results_*.csv`: Datos tabulares para Excel
- `ble_scanner.log`: Logs técnicos del sistema

## 🔧 Solución de Problemas Windows

### Error "nRF52DK no detectado"
```cmd
# Verificar puerto COM en Device Manager
# Cambiar puerto en config.py
# Probar diferentes puertos USB
```

### Error "Python no reconocido"
```cmd
# Reinstalar Python marcando "Add to PATH"
# O usar ruta completa:
C:\Python\python.exe ble_scanner.py
```

### Error "Módulo no encontrado"
```cmd
# Instalar dependencias específicas:
pip install pc-ble-driver-py
pip install pandas numpy
```

### Problemas de Permisos
```cmd
# Ejecutar Command Prompt como Administrador
# O usar PowerShell con permisos elevados
```

## 🎛️ Configuraciones Avanzadas Windows

### Variables de Entorno
```cmd
set PYTHONPATH=%PYTHONPATH%;C:\ruta\proyecto
set COM_PORT=COM4
```

### Configuración para Múltiples Usuarios
1. Instalar Python para todos los usuarios
2. Colocar proyecto en carpeta compartida
3. Configurar permisos de lectura/escritura

### Automatización con Task Scheduler
1. Abrir **Task Scheduler**
2. Crear nueva tarea básica
3. Configurar trigger (horario)
4. Acción: Ejecutar `run_scanner.bat`

## 📝 Comandos Útiles Windows

### Verificación del Sistema:
```cmd
# Ver dispositivos USB
wmic path Win32_USBHub get Name,DeviceID

# Ver puertos COM
wmic path Win32_SerialPort get Name,DeviceID

# Verificar Python y módulos
python -c "import pc_ble_driver_py; print('OK')"
```

### Monitoreo en Tiempo Real:
```cmd
# Ver logs en tiempo real
powershell Get-Content ble_scanner.log -Wait -Tail 10

# Monitor de puertos
mode COM3: BAUD=115200 PARITY=n DATA=8
```

## 🔄 Automatización y Scripts

### Script de Verificación Completa:
```batch
@echo off
echo Verificando sistema Windows...
python --version || goto :error
echo Verificando dependencias...
pip show pc-ble-driver-py || goto :error
echo Verificando hardware...
python -c "from scanner.driver import BLEDriverManager; print('Hardware OK')"
echo ✅ Sistema listo para escanear
goto :end

:error
echo ❌ Error en la verificación
pause

:end
```

### Monitoreo Continuo:
```batch
:loop
python ble_scanner.py
timeout /t 300 /nobreak
goto :loop
```

## 🛡️ Seguridad y Mejores Prácticas

### Firewall Windows:
- Permitir conexiones del Python.exe
- Configurar excepción para nRF52DK

### Antivirus:
- Agregar carpeta del proyecto a exclusiones
- Permitir ejecución de scripts Python

### Backup Automático:
```batch
xcopy "battery_scan_results_*.json" "C:\Backup\" /Y
xcopy "ble_scanner.log" "C:\Backup\" /Y
```

## 📞 Soporte Técnico

### Logs de Diagnóstico:
```cmd
python ble_scanner.py > diagnostico.txt 2>&1
```

### Información del Sistema:
```cmd
systeminfo > system_info.txt
wmic path Win32_USBHub get Name,DeviceID > usb_devices.txt
```

## 🚨 Solución Rápida de Emergencia

Si nada funciona, ejecuta estos comandos en orden:

```cmd
# 1. Reinstalar dependencias
pip uninstall pc-ble-driver-py -y
pip install pc-ble-driver-py

# 2. Verificar hardware
python -c "from scanner.driver import initialize_driver; print('Test OK')"

# 3. Ejecución mínima
python -c "from config import config; print(f'Puerto: {config.COM_PORT}')"

# 4. Test básico
python ble_scanner.py --scan-time 5
```

---

**¡Listo para escanear baterías CR2032 en Windows!** 🔋⚡

Para soporte adicional, revisa los archivos de log y la documentación técnica en README.md.
