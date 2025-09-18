# Configuration for BLE Scanner - Simplified Version
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ScannerConfig:
    """Simplified configuration for the universal BLE scanner"""
    
    # COM port configuration
    COM_PORT: str = "COM5"  # Main port
    COM_PORT_BACKUP: str = "COM4"  # Backup port
    
    # Scan parameters
    SCAN_TIMEOUT: int = 30  # Scan duration in seconds (legacy per-device)
    SCAN_TIME: int = 10  # Scan duration used for pre/post tests (seconds)
    BATTERY_THRESHOLD: float = 2.90  # Minimum battery voltage (V)
    RSSI_THRESHOLD: int = -200  # Minimum RSSI (dBm) - Set to very low value to capture all devices
    
    # Distance-based filtering (approximate RSSI thresholds)
    RSSI_DISTANCE_THRESHOLDS: Dict[str, int] = field(default_factory=lambda: {
        "1m": -45,    # ~1 meter range
        "2m": -55,    # ~2 meters range  
        "3m": -65,    # ~3 meters range
        "5m": -75,    # ~5 meters range
        "10m": -85    # ~10+ meters range
    })
    
    # Batch processing
    POST_TEST_ENABLED: bool = False  # Enable operator-confirmed post-test (set to False by default)
    MAX_QR_BATCH: int = 14000
    QR_INPUT_FILE: str = "qrcodes.txt"
    
    # Delta evaluation
    DELTA_VOLTAGE_FAIL: int = 100  # mV drop considered FAIL in post-test
    
    # Environment validation
    SUPPORTED_PYTHON_VERSION: str = "3.10.11"
    PC_BLE_DRIVER_COMPAT: Dict[str, str] = field(default_factory=lambda: {
        "0.11": "FW v3",
        "0.16": "FW v5",
        "0.17": "FW v5"
    })
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    
    # Output files
    OUTPUT_JSON_FILE: str = "c:/Battery-Scanner-Mini-White/results/scan_results.json"
    OUTPUT_CSV_FILE: str = "c:/Battery-Scanner-Mini-White/results/scan_results.csv"
    
    # Valid MACs (empty list = accept any MAC)
    VALID_MAC_IDS: List[str] = field(default_factory=list)

# Configuration instance
config = ScannerConfig()
