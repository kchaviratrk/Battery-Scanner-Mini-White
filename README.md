# BLE Universal Scanner (simplified version)

Universal BLE scanner to check CR2032 battery status on BLE devices using an nRF52DK (Windows).

Summary
-------
This repository provides a Windows command-line tool that performs universal BLE scans and evaluates CR2032 battery voltage from devices advertising battery data. The project now supports batch processing, a double-scan workflow (pre-test and post-test), environment validation for Python and pc-ble-driver-py, and structured JSON/CSV output including diagnostics and metrics.

Key features
------------
- Universal protocol parsing for multiple advertising formats.
- Batch input: load up to N QR codes/MACs (configurable, default 50) from a file or manual entry.
- Concurrent batch scan: single scan session that searches for all targets and records results.
- Double-scan workflow (pre-test and post-test) with operator confirmation.
- Delta evaluation: compare pre and post voltages and mark failures when voltage drop exceeds a configurable threshold.
- Environment validation: Python version check and pc-ble-driver-py compatibility check before starting.
- Results exported to JSON and CSV with metrics (total, processed, failed, elapsed time).

Requirements
------------
- Windows (batch menu and default paths are Windows-focused)
- Python 3.7 to 3.10 (Python 3.11 and higher is not supported by pc-ble-driver-py in this project)
- nRF52DK connected to the PC COM port
- pc-ble-driver-py installed and compatible with the target firmware

Installation (Windows)
----------------------
1. Install Python 3.7-3.10 (recommended: 3.10.11). Do not use Python 3.11+.
2. Open Command Prompt with appropriate permissions.
3. From the project folder run:
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
4. Connect the nRF52DK by USB and note the COM port in Device Manager.

Environment validation
----------------------
Before starting the scanner the tool runs environment checks:
- Python version: must be < 3.11 and >= 3.7. If Python 3.11+ is detected the program exits with a clear error and instructions.
- pc-ble-driver-py: the installed version is checked and compared against the compatibility mapping in `config.py` (PC_BLE_DRIVER_COMPAT). If there is an incompatibility the scanner reports the mismatch and suggests a reinstall command.

Configuration
-------------
Primary settings are in `config.py` (ScannerConfig):
- COM_PORT: primary nRF52DK COM port (e.g. "COM17")
- COM_PORT_BACKUP: backup COM port
- MAX_QR_BATCH: maximum number of QR codes/MACs per batch (default 50)
- QR_INPUT_FILE: default input file (default "qrcodes.txt")
- POST_TEST_ENABLED: enable or disable post-test confirmation (default False)
- SCAN_TIME: duration (s) for each scan phase (pre/post) when used
- SCAN_TIMEOUT: timeout used for scanning calculations
- BATTERY_THRESHOLD: voltage in V considered good (e.g. 2.90)
- RSSI_THRESHOLD: RSSI threshold in dBm
- DELTA_VOLTAGE_FAIL: voltage drop in mV considered a FAIL in post-test (default 100)
- SUPPORTED_PYTHON_VERSION: recommended Python version string (e.g. "3.10.11")
- PC_BLE_DRIVER_COMPAT: mapping of pc-ble-driver-py versions to required firmware strings

Usage
-----
1. Run `run_scanner.bat` and select the option to run the scanner, or run directly:
   python ble_scanner.py
2. Choose input mode when prompted:
   - file: load QR codes / MACs from a text or CSV file (one entry per line, first CSV column accepted). Default file is `qrcodes.txt`.
   - manual: paste a comma-separated list of QR codes or MAC addresses.
3. The tool resolves QR codes to MAC addresses via the configured backend endpoint, deduplicates entries and limits the batch to `MAX_QR_BATCH`.
4. The scanner runs the pre-test scan for the entire batch. When pre-test completes the terminal will show a message:

Pre-test complete. Place units in chamber. Press ENTER when ready for post-test.

5. After the operator presses ENTER, the post-test scan runs for the same batch and the tool produces a combined report comparing pre and post results.

Double-scan details
-------------------
- Each unit is recorded with pre-test and post-test readings: voltage (mV), RSSI, timestamp and PASS/FAIL status.
- Delta voltage is calculated as post.voltage_mv - pre.voltage_mv (negative if voltage dropped).
- If the voltage drop magnitude exceeds `DELTA_VOLTAGE_FAIL` the unit is marked as FAIL in the final status.

Output and reporting
--------------------
- JSON: `c:/Battery-Scanner-Mini-White/results/scan_results.json` contains an object with `metrics` and `results`. Each result includes `pre_test`, `post_test`, `delta_voltage`, and `final_status`.
- CSV: `c:/Battery-Scanner-Mini-White/results/scan_results.csv` contains rows for each unit with columns for pre/post voltage, RSSI, timestamps, delta and final status.
- Terminal: progress messages during scanning and a final summary with totals.

Example terminal output (plain text)
------------------------------------
[PRE-TEST]  A1:B2:C3:D4:E5:F6 -> 3100 mV, PASS
[PRE-TEST]  11:22:33:44:55:66 -> 2800 mV, FAIL

Pre-test complete. Place units in chamber. Press ENTER when ready for post-test.

[POST-TEST] A1:B2:C3:D4:E5:F6 -> 3050 mV, PASS (Δ -50 mV)
[POST-TEST] 11:22:33:44:55:66 -> 2700 mV, FAIL (Δ -100 mV)

SUMMARY:
Total Units: 2
Pass: 1
Fail: 1

Files of interest
-----------------
- `ble_scanner.py` — main scanner, batch and double-scan logic, environment validation
- `config.py` — configuration including compatibility mapping
- `battery_evaluator.py` — CR2032 battery classification logic
- `run_scanner.bat` — Windows menu to run checks and scanner
- `requirements.txt` — required Python packages
- `test_system.py` — validation tests (may require adjustments after refactor)

Troubleshooting
---------------
- If Python 3.11+ is installed, install Python 3.10.x and run the scanner with that interpreter.
- If pc-ble-driver-py version is incompatible, reinstall a compatible version using the suggested pip command shown by the environment checker.
- If no devices are detected, verify hardware connections, drivers, COM port and that units are powered and within range.

Contributing and license
------------------------
Add a LICENSE file and contribution guidelines if the project will be shared or accept external contributions.

Contact
-------
Open an issue in the repository for questions or report bugs.

---
Version: simplified — updated with batch processing and double-scan workflow.
