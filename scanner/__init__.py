"""
BLE Scanner Package for nRF52DK
CR2032 battery monitoring system - Windows optimized
"""

__version__ = "1.0.0"
__author__ = "Battery Scanner Team"

# Core modules
from .driver import BLEDriverManager
from .observer import BLEScannerObserver  
from .battery_evaluator import CR2032BatteryEvaluator
from .results import ResultsManager

__all__ = [
    'BLEDriverManager',
    'BLEScannerObserver', 
    'CR2032BatteryEvaluator',
    'ResultsManager'
]
