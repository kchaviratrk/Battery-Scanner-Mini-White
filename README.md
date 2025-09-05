# BLE Scanner for CR2032 Battery Monitoring

**Windows optimized BLE scanner for c:/Battery-Scanner-Mini-White deployment**

## 🎯 Purpose

Monitor CR2032 battery health in BLE devices using Nordic nRF52DK development kit.

## 🚀 Quick Start

1. **Install Python 3.7+** from [python.org](https://python.org)
2. **Connect nRF52DK** to USB port
3. **Run:** `run_scanner.bat`
4. **Select:** Option 1 (System Check)
5. **Select:** Option 2 (Install Dependencies)
6. **Configure:** Option 5 (Edit COM port)
7. **Scan:** Option 3 (Run Scanner)

## 🔋 Battery Categories

- 🟢 **NEW** (3000-3300mV): Fresh battery
- 🟡 **OK** (2850-2999mV): Good condition
- 🟠 **LOW** (2750-2849mV): Replace soon
- 🔴 **DEAD** (≤2750mV): Replace immediately

## 📁 Files

- `ble_scanner.py` - Main application
- `config.py` - Settings (edit COM port here)
- `run_scanner.bat` - Windows menu system
- `scanner/` - Core modules

## 📊 Results

All output saved to `c:/Battery-Scanner-Mini-White/`:
- `results/battery_results.json` - Detailed data
- `results/battery_results.csv` - Excel format
- `logs/scanner.log` - Technical logs

## 🔧 Configuration

Edit `config.py`:
```python
COM_PORT = "COM3"  # Change to your nRF52DK port
VALID_MAC_IDS = ["A1B2C3D4E5F6"]  # Add your device MACs
```

## 💡 Troubleshooting

- **Python error:** Install from python.org, check PATH
- **COM port error:** Check Device Manager, update config.py
- **No devices:** Ensure devices powered on, within 2m range

---
**Target:** `c:/Battery-Scanner-Mini-White/` | **Language:** English | **Platform:** Windows
