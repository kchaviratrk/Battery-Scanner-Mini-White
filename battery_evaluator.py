"""
CR2032 Battery Evaluator - Simplified Version
Specialized evaluator for classifying CR2032 battery state
Completely independent, no Nordic driver dependencies
"""
import logging
from typing import Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CR2032Thresholds:
    """Voltage thresholds for CR2032 batteries (in millivolts)"""
    
    # Categories according to Energizer specifications
    NEW_MIN: int = 3000      # 3.0V - Minimum new battery
    NEW_MAX: int = 3300      # 3.3V - Maximum new battery
    GOOD: int = 2900         # 2.9V - Good battery (unified threshold)
    LOW: int = 2800          # 2.8V - Low battery
    DEAD: int = 2750         # ≤2.75V - Dead battery

class CR2032BatteryEvaluator:
    """Simplified CR2032 battery evaluator"""
    
    def __init__(self, custom_thresholds: CR2032Thresholds = None):
        self.thresholds = custom_thresholds or CR2032Thresholds()
        
    def evaluate_battery(self, voltage_mv: int) -> Dict:
        """
        Evaluate the state of a CR2032 battery
        
        Args:
            voltage_mv: Voltage in millivolts
            
        Returns:
            Dict with category, status, percentage estimate and recommendation
        """
        if voltage_mv >= self.thresholds.NEW_MIN:
            category = "NEW"
            status = "GOOD"
            percentage = min(100, ((voltage_mv - self.thresholds.NEW_MIN) / 
                                 (self.thresholds.NEW_MAX - self.thresholds.NEW_MIN)) * 100)
            recommendation = "New battery - continue use"
            
        elif voltage_mv >= self.thresholds.GOOD:
            category = "GOOD"
            status = "GOOD"
            percentage = 80 - ((self.thresholds.NEW_MIN - voltage_mv) / 10)
            recommendation = "Good battery - continue use"
            
        elif voltage_mv >= self.thresholds.LOW:
            category = "LOW"
            status = "WARN"
            percentage = 20 - ((self.thresholds.GOOD - voltage_mv) / 5)
            recommendation = "Low battery - monitor closely"
            
        else:
            category = "DEAD"
            status = "FAIL"
            percentage = 0
            recommendation = "Dead battery - replace immediately"
        
        return {
            'voltage_mv': voltage_mv,
            'voltage_v': voltage_mv / 1000,
            'category': category,
            'status': status,
            'percentage_estimate': max(0, min(100, percentage)),
            'recommendation': recommendation,
            'pass_fail': status in ['GOOD']
        }

def evaluate_battery_simple(voltage_v: float) -> str:
    """
    Quick battery evaluation
    
    Args:
        voltage_v: Voltage in volts
        
    Returns:
        String with simple result
    """
    evaluator = CR2032BatteryEvaluator()
    voltage_mv = int(voltage_v * 1000)
    result = evaluator.evaluate_battery(voltage_mv)
    
    return f"{result['category']} ({result['voltage_v']:.2f}V) - {result['recommendation']}"

if __name__ == "__main__":
    # Demo of simplified evaluator
    print("=== Demo: CR2032 Simplified Evaluator ===")
    
    test_voltages = [3300, 3100, 2950, 2850, 2750, 2650]
    
    evaluator = CR2032BatteryEvaluator()
    
    print("\nEvaluation of test voltages:")
    print("-" * 70)
    print(f"{'Voltage':<8} {'Category':<8} {'Status':<6} {'%':<6} {'Recommendation'}")
    print("-" * 70)
    
    for voltage in test_voltages:
        result = evaluator.evaluate_battery(voltage)
        print(f"{voltage}mV   {result['category']:<8} {result['status']:<6} "
              f"{result['percentage_estimate']:<5.1f}% {result['recommendation']}")
    
    print("\n=== Test of simple function ===")
    for voltage_v in [3.3, 3.0, 2.9, 2.8, 2.7]:
        print(f"{voltage_v}V: {evaluate_battery_simple(voltage_v)}")
