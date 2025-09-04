# 📋 INSTRUCCIONES RÁPIDAS - BLE Scanner Windows

## ⚠️ IMPORTANTE: Requisito de Python 3.10

**PROBLEMA**: Tu Python 3.13.5 es incompatible con `pc-ble-driver-py`
**SOLUCIÓN**: Instalar Python 3.10.11 en paralelo (no reemplazar)

### 🚀 INICIO RÁPIDO (4 pasos)

#### Paso 0: Instalar Python 3.10 (CRÍTICO)
```
1. Descargar Python 3.10.11 desde: https://python.org/downloads/release/python-31011/
2. Durante instalación: ✅ Marcar "Add Python to PATH" 
3. ✅ Permitir instalación junto a Python 3.13 (no reemplazar)
4. Verificar: py -3.10 --version
```

#### Paso 1: Preparar Hardware
```
1. Conectar nRF52DK al puerto USB
2. Abrir "Device Manager" (Administrador de dispositivos)
3. Buscar en "Ports (COM & LPT)" → Anotar número (ej: COM3)
```

#### Paso 2: Configurar Puerto
```
1. Abrir archivo: config.py
2. Buscar línea: COM_PORT: str = "COM3"
3. Cambiar COM3 por el puerto correcto (del Paso 1)
4. Guardar archivo
```

#### Paso 3: Ejecutar
```
1. Hacer doble clic en: run_scanner.bat
2. Seleccionar opción "1" para verificar sistema
3. Seleccionar opción "2" para instalar dependencias
4. Seleccionar opción "4" para ejecutar scanner
```

## 🔧 Si hay Problemas

### Error: "Python no reconocido"
```
Solución:
1. Descargar Python desde: https://python.org
2. Durante instalación: ✅ Marcar "Add Python to PATH"
3. Reiniciar Command Prompt
```

### ⚠️ ERROR CRÍTICO: "pc-ble-driver incompatible con Python 3.13+"
```
PROBLEMA: pc-ble-driver-py requiere Python 3.10.x específicamente
TU VERSIÓN: Python 3.13.5 (incompatible)

SOLUCIÓN RÁPIDA:
1. Descargar Python 3.10.11 desde: https://python.org/downloads/release/python-31011/
2. Instalar EN PARALELO (no desinstalar 3.13)
3. Durante instalación: ✅ Marcar "Add Python to PATH"
4. Usar comando específico: py -3.10 ble_scanner.py

VERIFICAR VERSIÓN CORRECTA:
py -3.10 --version
py -3.10 -m pip install -r requirements.txt
```

### Error: "COM port no funciona"
```
Solución:
1. Win + X → Device Manager
2. Ports (COM & LPT) → Ver puerto del nRF52DK
3. Actualizar COM_PORT en config.py
4. Probar COM3, COM4, COM5, etc.
```

### Error: "No se encuentran dispositivos"
```
Solución:
1. Verificar que dispositivos BLE estén encendidos
2. Acercar dispositivos al nRF52DK (< 2 metros)
3. Aumentar SCAN_TIME en config.py (ej: 20 segundos)
```

## 📊 Entender Resultados

### Categorías de Batería:
- 🟢 **NEW**: Batería nueva (3000-3300mV)
- 🟡 **OK**: Buen estado (2850-2999mV)  
- 🟠 **LOW**: Reemplazar pronto (2750-2849mV)
- 🔴 **DEAD**: Reemplazar ya (≤2750mV)

### Archivos Generados:
- `battery_scan_results_*.json` → Datos detallados
- `battery_scan_results_*.csv` → Para Excel
- `ble_scanner.log` → Logs técnicos

## ⚡ Comandos de Emergencia

### Si run_scanner.bat no funciona:
```cmd
# IMPORTANTE: Usar Python 3.10 específicamente
cd "C:\ruta\al\proyecto"
py -3.10 ble_scanner.py

# Si solo tienes Python 3.13, instalar 3.10 primero:
# Descargar Python 3.10.11 desde python.org
```

### Verificar que todo está bien:
```cmd
# Verificar versión correcta de Python
py -3.10 --version

# Verificar driver con versión correcta
py -3.10 -m pip show pc-ble-driver-py

# Test de configuración
py -3.10 -c "from config import config; print(config.COM_PORT)"
```

### Reinstalar dependencias:
```cmd
# Usar Python 3.10 específicamente
py -3.10 -m pip install -r requirements.txt --force-reinstall
```

## 📞 Ayuda Rápida

### Verificar Puerto COM Correcto:
```
1. Win + R → "devmgmt.msc" → Enter
2. Expandir "Ports (COM & LPT)"
3. Buscar "nRF52" o dispositivo similar
4. Anotar número COM
```

### Ver Resultados:
```
Opción 5 en el menú principal
O abrir manualmente:
- battery_scan_results_*.csv (Excel)
- battery_scan_results_*.json (Notepad)
```

---

## 🎯 Flujo Típico de Trabajo

```
0. PRIMERO: Instalar Python 3.10 (solo una vez)
   - Ejecutar: setup_python310.bat (automático)
   - O manual desde: https://python.org/downloads/release/python-31011/

1. Conectar nRF52DK → Puerto USB
2. Ejecutar run_scanner.bat  
3. Opción 1: Verificar sistema (detecta Python 3.10)
4. Opción 2: Instalar dependencias (con Python 3.10)
5. Editar config.py si es necesario
6. Opción 4: Ejecutar scanner principal (usa Python 3.10)
7. Opción 5: Ver resultados
```

### 🛠️ Scripts de Ayuda Disponibles:
- `setup_python310.bat` → Configuración automática de Python 3.10
- `verificar_windows.bat` → Verificación completa del sistema
- `run_scanner.bat` → Menú principal (ya configurado para Python 3.10)

**¡Listo! El sistema está preparado para Windows con Python 3.10** 🪟✅
