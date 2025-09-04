# BLE Scanner with nRF52DK - CR2032 Battery Evaluation System

## 📖 Project Overview

This project is a sophisticated **Bluetooth Low Energy (BLE) scanner system** specifically designed for **CR2032 battery evaluation**. It uses the **Nordic nRF52DK** development kit as a BLE sniffer to scan, analyze, and intelligently evaluate the health of CR2032 batteries in nearby BLE devices.

### 🎯 What This Project Does

- **Scans BLE advertisements** from nearby devices using nRF52DK
- **Extracts battery voltage information** from manufacturer-specific data
- **Intelligently evaluates CR2032 battery health** using specialized algorithms
- **Provides predictive maintenance recommendations** based on real discharge curves
- **Generates comprehensive reports** in both terminal display and exportable formats (JSON/CSV)

### 🔋 CR2032 Specialized Features

This system goes beyond simple voltage thresholds by implementing:

- **Real Energizer CR2032 discharge curve analysis**
- **Non-linear battery degradation modeling** 
- **Intelligent categorization**: NEW 🟢, OK 🟡, LOW 🟠, DEAD 🔴
- **Precise percentage estimates** based on actual battery behavior
- **Life expectancy predictions** (weeks/months remaining)
- **Maintenance advice** tailored to each voltage level
- **Load compensation** for temporary voltage drops during operation

## 🏗️ Project Architecture

```
Battery Scanner Mini White/
├── ble_scanner.py              # Main application entry point
├── config.py                   # System configuration and CR2032 thresholds  
├── requirements.txt            # Python dependencies
├── run_scanner.bat            # Windows execution script
├── README.md                  # This documentation
└── scanner/                   # Core scanning modules
    ├── __init__.py            # Module initialization
    ├── battery_evaluator.py   # CR2032 specialized evaluation engine
    ├── driver.py              # nRF52DK hardware communication
    ├── observer.py            # BLE advertisement processing
    ├── parser.py              # Data extraction and parsing
    └── results.py             # Results formatting and export
```

### 🧠 Core Components

1. **BLE Scanner Engine** (`ble_scanner.py`)
   - Orchestrates the entire scanning process
   - Manages hardware communication with nRF52DK
   - Coordinates data flow between components

2. **CR2032 Battery Evaluator** (`scanner/battery_evaluator.py`)
   - Implements specialized CR2032 evaluation algorithms
   - Uses real Energizer discharge curve data
   - Provides intelligent categorization and predictions

3. **BLE Observer** (`scanner/observer.py`)
   - Processes incoming BLE advertisements
   - Filters and validates device data
   - Handles scan event management

4. **Data Parser** (`scanner/parser.py`)
   - Extracts battery voltage from manufacturer data
   - Validates data integrity
   - Handles different BLE advertisement formats

5. **Results Manager** (`scanner/results.py`)
   - Formats output for terminal display
   - Exports data to JSON and CSV
   - Generates statistical summaries

## 🚀 How to Execute This Project

### Prerequisites

1. **Hardware Requirements**
   - Nordic nRF52DK development board
   - USB cable for nRF52DK connection
   - Computer with USB port (Windows, macOS, or Linux)

2. **Software Requirements**
   - Python 3.7 or higher
   - USB drivers for nRF52DK (usually auto-installed)

### 📥 Installation Steps

1. **Clone or Download the Project**
   ```bash
   git clone <repository-url>
   cd "Battery Scanner Mini White"
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Core dependencies installed:**
   - `pc-ble-driver-py`: Nordic's official Python driver for nRF52DK
   - `pandas`: Data manipulation and analysis (optional but recommended)
   - `numpy`: Numerical computations

3. **Connect nRF52DK Hardware**
   - Connect the nRF52DK to your computer via USB
   - Ensure the device is recognized by your operating system
   - No additional firmware flashing required

### ▶️ Execution Methods

#### Method 1: Python Command (All Platforms)
```bash
python ble_scanner.py
```

#### Method 2: Python3 Command (Linux/macOS)
```bash
python3 ble_scanner.py
```

#### Method 3: Windows Batch Script
```cmd
run_scanner.bat
```

#### Method 4: Direct Module Execution
```bash
python -m scanner
```

### ⚙️ Configuration Options

Before running, you can customize the system behavior by editing `config.py`:

#### CR2032 Battery Thresholds
```python
# Voltage thresholds in millivolts
CR2032_NEW_MIN = 3000      # Minimum voltage for NEW category
CR2032_NEW_MAX = 3300      # Maximum voltage for NEW category  
CR2032_OPERATIONAL = 2850  # Operational threshold (OK category)
CR2032_LOW_BATTERY = 2750  # Low battery warning threshold
CR2032_DEAD_BATTERY = 2750 # Dead battery threshold
```

#### Scanning Parameters
```python
SCAN_DURATION = 10         # How long to scan (seconds)
MIN_RSSI = -90            # Minimum signal strength to consider
SAVE_RESULTS = True       # Auto-save results to files
OUTPUT_FORMAT = "both"    # "json", "csv", or "both"
```

#### Evaluation Features
```python
USE_CR2032_EVALUATION = True     # Enable specialized CR2032 analysis
INCLUDE_BATTERY_ADVICE = True    # Include maintenance recommendations
INCLUDE_LIFE_ESTIMATE = True     # Include life expectancy predictions
CONSIDER_PULSE_LOAD = True       # Compensate for temporary voltage drops
PULSE_LOAD_COMPENSATION = 50     # Compensation amount in mV
```

## 📊 Understanding the Output

### Terminal Display
```
🔍 BLE SCANNER STARTED - Scanning for 10 seconds...

📱 DISCOVERED DEVICES:
─────────────────────────────────────────────────────────────────────────
✅ A1:B2:C3:D4:E5:F6: 3100mV (85.0%), 🟢 NEW, Battery excellent..., RSSI: -65dBm
✅ 11:22:33:44:55:66: 2900mV (35.0%), 🟡 OK, Good performance..., RSSI: -72dBm  
❌ AA:BB:CC:DD:EE:FF: 2800mV (8.0%), 🟠 LOW, Replace soon..., RSSI: -78dBm
❌ FF:EE:DD:CC:BB:AA: 2700mV (1.0%), 🔴 DEAD, Replace immediately..., RSSI: -85dBm

📊 CR2032 BATTERY STATISTICS:
─────────────────────────────────────────────────
Total devices: 4
  🟢 NEW: 1 (25.0%) - Excellent condition
  🟡 OK: 1 (25.0%) - Good operational state  
  🟠 LOW: 1 (25.0%) - Replacement recommended
  🔴 DEAD: 1 (25.0%) - Immediate replacement required

✅ Results saved to: ble_scan_results_2025-09-04_143022.json
✅ Results saved to: ble_scan_results_2025-09-04_143022.csv
```

### Battery Categories Explained

| Category | Voltage Range | Status | Description | Action Required |
|----------|---------------|--------|-------------|-----------------|
| 🟢 **NEW** | 3000-3300mV | PASS | Fresh battery, excellent performance | Monitor normally |
| 🟡 **OK** | 2850-2999mV | PASS | Good operational state | Plan replacement in 1-6 months |
| 🟠 **LOW** | 2750-2849mV | FAIL | Near depletion, declining performance | Replace within 1-4 weeks |
| 🔴 **DEAD** | ≤2750mV | FAIL | Depleted, unreliable operation | Replace immediately |

### Exported Data Formats

#### JSON Export (`ble_scan_results_*.json`)
```json
{
  "macid": "A1:B2:C3:D4:E5:F6",
  "rssi": -65,
  "battery_voltage": 3100,
  "battery_category": "NEW", 
  "status": "PASS",
  "timestamp": "2025-09-04T14:30:22",
  "advice": "Battery in excellent condition, recently manufactured or unused. Monitor performance closely.",
  "percentage_estimate": 85.0,
  "expected_life": "6-12 months with good performance",
  "battery_type": "CR2032"
}
```

#### CSV Export (`ble_scan_results_*.csv`)
Tabular format suitable for Excel or data analysis tools with all the same information in spreadsheet format.

## 🔧 Troubleshooting

### Common Issues and Solutions

#### "nRF52DK not detected"
- **Check USB connection**: Try a different USB cable or port
- **Verify drivers**: Ensure nRF52DK drivers are installed
- **Device permissions**: On Linux/macOS, may need `sudo` permissions

#### "No devices found"
- **Check BLE devices**: Ensure target devices are actively advertising
- **Adjust RSSI threshold**: Lower `MIN_RSSI` in config.py (e.g., -100)
- **Increase scan time**: Raise `SCAN_DURATION` in config.py

#### "Import errors" 
- **Install dependencies**: Run `pip install -r requirements.txt`
- **Python version**: Ensure Python 3.7+ is installed
- **Virtual environment**: Consider using `venv` for isolated dependencies

#### "Permission denied" (Linux/macOS)
```bash
sudo python ble_scanner.py
```

### Advanced Usage

#### Running with Custom Parameters
```bash
# Scan for longer duration
python ble_scanner.py --scan-time 30

# Lower RSSI threshold for distant devices  
python ble_scanner.py --min-rssi -100

# Save only JSON format
python ble_scanner.py --format json
```

#### Programmatic Usage
```python
from scanner import BLEScanner

scanner = BLEScanner()
results = scanner.scan(duration=10)
for device in results:
    print(f"{device['macid']}: {device['battery_category']}")
```

## 🎯 Use Cases

### 1. **Medical Device Maintenance**
Monitor CR2032 batteries in medical equipment to prevent unexpected failures during critical operations.

### 2. **Industrial IoT Monitoring** 
Track battery health across sensor networks to schedule preventive maintenance.

### 3. **Smart Home Management**
Keep tabs on battery levels in door sensors, temperature monitors, and other BLE devices.

### 4. **Research and Development**
Study real-world CR2032 battery behavior and discharge patterns in various applications.

## 📝 Technical Notes

- **Discharge Curve**: Based on authentic Energizer CR2032 specifications
- **Load Compensation**: Accounts for temporary voltage drops during device operation
- **Prediction Algorithm**: Uses non-linear modeling for realistic life expectancy estimates
- **Data Accuracy**: Voltage readings accurate to within ±50mV under normal conditions

## 🤝 Support and Contributing

For technical support, bug reports, or feature requests, please create an issue in the project repository. Contributions are welcome following standard open-source practices.

## 📄 License

This project is provided for educational and research purposes. See the license file for specific terms and conditions.

---

**Ready to start monitoring your CR2032 batteries intelligently? Follow the execution steps above and begin gaining insights into your BLE device ecosystem!**
