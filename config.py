"""
BLE Scanner Configuration for nRF52DK
Windows optimized configuration for CR2032 battery monitoring
"""
from dataclasses import dataclass
from typing import List


@dataclass
class ScannerConfig:
    """BLE Scanner Configuration for Windows"""
    
    # ========== HARDWARE CONFIGURATION ==========
    COM_PORT: str = "COM3"  # nRF52DK COM port (check Device Manager)
    
    # ========== SCAN PARAMETERS ==========
    SCAN_TIME: int = 10     # Scan duration in seconds
    BATTERY_THRESHOLD: int = 2850  # Minimum operational voltage (mV)
    
    # Target device MAC addresses (format: "AABBCCDDEEFF")
    VALID_MAC_IDS: List[str] = [
        "A1B2C3D4E5F6",
        "112233445566", 
        "AABBCCDDEEFF",
        "123456789ABC"
    ]
    
    # ========== OUTPUT CONFIGURATION ==========
    OUTPUT_JSON_FILE: str = "c:/Battery-Scanner-Mini-White/results/battery_results.json"
    OUTPUT_CSV_FILE: str = "c:/Battery-Scanner-Mini-White/results/battery_results.csv"
    LOG_LEVEL: str = "INFO"
    
    # ========== CR2032 BATTERY THRESHOLDS ==========
    CR2032_NEW_MIN: int = 3000      # 3.0V - Fresh battery
    CR2032_NEW_MAX: int = 3300      # 3.3V - Maximum voltage
    CR2032_OPERATIONAL: int = 2850  # 2.85V - Good working condition
    CR2032_LOW_BATTERY: int = 2750  # 2.75V - Replace soon
    CR2032_DEAD_BATTERY: int = 2750 # ≤2.75V - Replace immediately
    
    # ========== EVALUATION SETTINGS ==========
    USE_CR2032_EVALUATION: bool = True    # Enable CR2032 specific analysis
    INCLUDE_BATTERY_ADVICE: bool = True   # Include maintenance advice
    INCLUDE_LIFE_ESTIMATE: bool = True    # Predict remaining life
    CONSIDER_PULSE_LOAD: bool = True      # Compensate for voltage drops
    PULSE_LOAD_COMPENSATION: int = 50     # Load compensation (mV)


# Global configuration instance
config = ScannerConfig()
