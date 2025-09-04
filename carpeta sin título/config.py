"""
Global configuration for the BLE scanner
"""
from dataclasses import dataclass
from typing import List


@dataclass
class ScannerConfig:
    """BLE scanner configuration"""
    
    # nRF52DK COM port (adjust according to system)
    COM_PORT: str = "COM3"  # On Windows typically COM3, COM4, etc.
    
    # Scan time in seconds
    SCAN_TIME: int = 10
    
    # Battery voltage threshold in millivolts (for compatibility)
    BATTERY_THRESHOLD: int = 2850  # Adjusted for CR2032 operational
    
    # List of valid MAC IDs to filter (format: "AABBCCDDEEFF")
    VALID_MAC_IDS: List[str] = [
        "A1B2C3D4E5F6",
        "112233445566", 
        "AABBCCDDEEFF",
        "123456789ABC"
    ]
    
    # Output file configuration
    OUTPUT_JSON_FILE: str = "battery_scan_results.json"
    OUTPUT_CSV_FILE: str = "battery_scan_results.csv"
    
    # Log configuration
    LOG_LEVEL: str = "INFO"
    
    # ========== CR2032 CONFIGURATION ==========
    
    # Specific thresholds for CR2032 batteries (in millivolts)
    CR2032_NEW_MIN: int = 3000      # 3.0V - New battery minimum
    CR2032_NEW_MAX: int = 3300      # 3.3V - New battery maximum  
    CR2032_OPERATIONAL: int = 2850  # 2.85V - Operational (OK)
    CR2032_LOW_BATTERY: int = 2750  # 2.75V - Near depleted
    CR2032_DEAD_BATTERY: int = 2750 # ≤2.75V - Depleted
    
    # Evaluation configuration
    USE_CR2032_EVALUATION: bool = True  # Use CR2032 specific evaluation
    INCLUDE_BATTERY_ADVICE: bool = True # Include advice in results
    INCLUDE_LIFE_ESTIMATE: bool = True  # Include life expectancy estimation
    
    # Pulse load configuration (to compensate fluctuations)
    CONSIDER_PULSE_LOAD: bool = True    # Consider voltage drops from load
    PULSE_LOAD_COMPENSATION: int = 50   # Compensation in mV for pulse loads
    
    # Battery configuration
    BATTERY_MIN_VOLTAGE: int = 2500  # mV - Minimum voltage (0%)
    BATTERY_MAX_VOLTAGE: int = 4200  # mV - Maximum voltage (100%)
    USE_LITHIUM_CURVE: bool = True   # Use lithium characteristic curve


# Global configuration instance
config = ScannerConfig()
