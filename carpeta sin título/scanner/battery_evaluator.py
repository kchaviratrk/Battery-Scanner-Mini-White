"""
CR2032 battery evaluator
Specialized module to classify CR2032 battery state according to Energizer discharge curve
"""
import logging
from typing import Dict
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class CR2032Thresholds:
    """voltage thresholds for CR2032 batteries (in millivolts)"""
    
    # Category boundaries
    NEW_MIN: int = 3000      # 3.0V - New battery minimum
    NEW_MAX: int = 3300      # 3.3V - New battery maximum
    OPERATIONAL: int = 2850  # 2.85V - Operational threshold (OK)
    LOW_BATTERY: int = 2750  # 2.75V - Low battery threshold
    DEAD_BATTERY: int = 2750 # ≤2.75V - Depleted battery
    
    # Load compensation
    PULSE_LOAD_COMPENSATION: int = 50  # mV


class CR2032BatteryEvaluator:
    """
    Specialized evaluator for CR2032 batteries
    Implements specific evaluation rules according to Energizer discharge curve
    """
    
    def __init__(self, thresholds: CR2032Thresholds = None):
        """
        Initialize the CR2032 evaluator
        
        Args:
            thresholds: Custom thresholds (optional)
        """
        self.thresholds = thresholds or CR2032Thresholds()
        logger.debug(f"CR2032Evaluator initialized with thresholds: {self.thresholds}")
    
    def evaluate_battery(self, voltage_mv: int) -> Dict:
        """
        Evaluates CR2032 battery state according to its voltage
        
        Args:
            voltage_mv: voltage in millivolts
            
        Returns:
            Dictionary with complete evaluation:
            - category: NEW, OK, LOW, DEAD
            - status: PASS/FAIL
            - advice: Maintenance recommendation
            - percentage_estimate: Estimated charge percentage
            - expected_life: Estimated remaining life
            - battery_type: Always "CR2032"
        """
        try:
            logger.debug(f"Evaluating CR2032 battery with voltage {voltage_mv}mV")
            
            # Basic validation
            if voltage_mv < 0 or voltage_mv > 4000:
                logger.warning(f"Unusual voltage detected: {voltage_mv}mV")
            
            # Determine category and status
            category = self._determine_category(voltage_mv)
            status = self._determine_status(voltage_mv)
            advice = self._generate_advice(voltage_mv, category)
            percentage = self._estimate_percentage(voltage_mv)
            life_expectancy = self._estimate_life_expectancy(voltage_mv, category)
            
            result = {
                "category": category,
                "status": status,
                "advice": advice,
                "percentage_estimate": round(percentage, 1),
                "expected_life": life_expectancy,
                "battery_type": "CR2032",
                "voltage_mv": voltage_mv,
                "thresholds_used": {
                    "new_min": self.thresholds.NEW_MIN,
                    "operational": self.thresholds.OPERATIONAL,
                    "low_battery": self.thresholds.LOW_BATTERY
                }
            }
            
            logger.info(f"CR2032 evaluation: {voltage_mv}mV -> {category} ({status})")
            return result
            
        except Exception as e:
            logger.error(f"error evaluating CR2032 battery: {e}")
            return {
                "category": "UNKNOWN",
                "status": "FAIL",
                "advice": f"Evaluation error: {e}",
                "percentage_estimate": 0.0,
                "expected_life": "Unknown",
                "battery_type": "CR2032"
            }
    
    def _determine_category(self, voltage_mv: int) -> str:
        """
        Determines battery category according to voltage
        
        Args:
            voltage_mv: voltage in millivolts
            
        Returns:
            Category: NEW, OK, LOW, DEAD
        """
        if voltage_mv >= self.thresholds.NEW_MIN:
            return "NEW"
        elif voltage_mv > self.thresholds.OPERATIONAL:
            return "OK"
        elif voltage_mv > self.thresholds.LOW_BATTERY:
            return "LOW"
        else:
            return "DEAD"
    
    def _determine_status(self, voltage_mv: int) -> str:
        """
        Determines operational status
        
        Args:
            voltage_mv: voltage in millivolts
            
        Returns:
            Status: PASS or FAIL
        """
        # PASS if battery is operational (> 2.85V)
        return "PASS" if voltage_mv > self.thresholds.OPERATIONAL else "FAIL"
    
    def _generate_advice(self, voltage_mv: int, category: str) -> str:
        """
        Generates advisory message based on battery state
        
        Args:
            voltage_mv: voltage in millivolts
            category: Battery category
            
        Returns:
            Advisory message
        """
        if category == "NEW":
            if voltage_mv >= 3200:
                return "Battery in excellent withdition, recently manufactured or unused. Monitor performance closely."
            elif voltage_mv >= 3100:
                return "Battery in excellent withdition, recently installed or lightly used."
            else:
                return "Battery in good withdition, normal operation expected."
                
        elif category == "OK":
            if voltage_mv >= 2950:
                return "Battery operational, good performance expected. Begin replacement planning."
            else:
                return "Battery operational, performance may vary. Consider replacement soon."
                
        elif category == "LOW":
            if voltage_mv >= 2800:
                return "Battery close to depletion, replace soon to avoid device failure. Significant voltage drop expected under load."
            else:
                return "Battery nearly depleted, urgent replacement recommended. Performance significantly degraded."
                
        else:  # DEAD
            return "Battery depleted, immediate replacement required. Critical voltage level reached."
    
    def _estimate_percentage(self, voltage_mv: int) -> float:
        """
        Estimates charge percentage based on non-linear CR2032 discharge curve
        
        Args:
            voltage_mv: voltage in millivolts
            
        Returns:
            Estimated percentage (0-100)
        """
        try:
            # CR2032 discharge curve (non-linear)
            # Based on Energizer CR2032 datasheet
            
            if voltage_mv >= 3300:
                return 100.0
            elif voltage_mv >= 3200:
                # 95-100%: High voltage, new or lightly used battery
                return 95.0 + (voltage_mv - 3200) * 0.05
            elif voltage_mv >= 3100:
                # 80-95%: Good voltage, battery in excellent withdition
                return 80.0 + (voltage_mv - 3100) * 0.15
            elif voltage_mv >= 3000:
                # 60-80%: Stable plateau zone
                return 60.0 + (voltage_mv - 3000) * 0.20
            elif voltage_mv >= 2950:
                # 40-60%: Beginning of discharge
                return 40.0 + (voltage_mv - 2950) * 0.40
            elif voltage_mv >= 2900:
                # 20-40%: Moderate discharge
                return 20.0 + (voltage_mv - 2900) * 0.40
            elif voltage_mv >= 2850:
                # 10-20%: Significant discharge, still operational
                return 10.0 + (voltage_mv - 2850) * 0.20
            elif voltage_mv >= 2800:
                # 5-10%: Low voltage, near depletion
                return 5.0 + (voltage_mv - 2800) * 0.10
            elif voltage_mv >= 2750:
                # 1-5%: Critical voltage
                return 1.0 + (voltage_mv - 2750) * 0.08
            elif voltage_mv >= 2600:
                # 0.5-1%: Depleted
                return 0.5 + (voltage_mv - 2600) * 0.003
            else:
                return max(0.1, (voltage_mv - 2500) * 0.001)  # Minimum 0.1%
                
        except Exception as e:
            logger.error(f"error estimating percentage: {e}")
            return 0.0
    
    def _estimate_life_expectancy(self, voltage_mv: int, category: str) -> str:
        """
        Estimates remaining life expectancy
        
        Args:
            voltage_mv: voltage in millivolts
            category: Battery category
            
        Returns:
            Life expectancy description
        """
        if category == "NEW":
            if voltage_mv >= 3200:
                return "12+ months under normal withditions"
            elif voltage_mv >= 3100:
                return "6-12 months with good performance"
            else:
                return "3-6 months, performance stable"
                
        elif category == "OK":
            if voltage_mv >= 2950:
                return "2-4 months, begin replacement planning"
            else:
                return "1-2 months, replacement recommended"
                
        elif category == "LOW":
            if voltage_mv >= 2800:
                return "2-4 weeks, prepare for replacement"
            else:
                return "1-2 weeks maximum, urgent replacement"
                
        else:  # DEAD
            return "Replace immediately"
    
    def get_thresholds_info(self) -> Dict:
        """
        Returns information about withfigured thresholds
        
        Returns:
            Dictionary with threshold information
        """
        return {
            "new_battery_range": f"{self.thresholds.NEW_MIN}mV - {self.thresholds.NEW_MAX}mV",
            "operational_threshold": f">{self.thresholds.OPERATIONAL}mV",
            "low_battery_threshold": f"{self.thresholds.LOW_BATTERY}mV - {self.thresholds.OPERATIONAL}mV",
            "dead_battery_threshold": f"≤{self.thresholds.DEAD_BATTERY}mV",
            "pulse_compensation": f"{self.thresholds.PULSE_LOAD_COMPENSATION}mV"
        }


def evaluate_battery(voltage_mv: int, custom_thresholds: CR2032Thresholds = None) -> Dict:
    """
    Convenience function to evaluate a CR2032 battery
    
    Args:
        voltage_mv: voltage in millivolts
        custom_thresholds: Custom thresholds (optional)
        
    Returns:
        Dictionary with complete evaluation
    """
    evaluator = CR2032BatteryEvaluator(custom_thresholds)
    return evaluator.evaluate_battery(voltage_mv)


def get_cr2032_voltage_chart() -> Dict:
    """
    Gets a voltage vs state reference table for CR2032
    
    Returns:
        Dictionary with reference table
    """
    return {
        "title": "CR2032 voltage Reference Chart",
        "voltage_ranges": [
            {"range": "3.0V - 3.3V", "category": "NEW", "status": "PASS", "description": "Fresh battery"},
            {"range": "> 2.85V", "category": "OK", "status": "PASS", "description": "Operational"},
            {"range": "2.75V - 2.85V", "category": "LOW", "status": "FAIL", "description": "Near depletion"},
            {"range": "≤ 2.75V", "category": "DEAD", "status": "FAIL", "description": "Depleted"}
        ],
        "notes": [
            "CR2032 discharge is non-linear",
            "voltage drops slowly then rapidly",
            "Load pulses can cause temporary voltage drops",
            "Temperature affects voltage readings"
        ]
    }


if __name__ == "__main__":
    # demo usage
    print("=== demo: CR2032 Battery Evaluator ===")
    
    evaluator = CR2032BatteryEvaluator()
    
    test_voltages = [3300, 3100, 2900, 2800, 2700]
    
    for voltage in test_voltages:
        result = evaluator.evaluate_battery(voltage)
        print(f"{voltage}mV: {result['category']}, {result['status']}, {result['percentage_estimate']:.1f}%")
    
    print("\nThreshold info:")
    thresholds = evaluator.get_thresholds_info()
    for key, value in thresholds.items():
        print(f"  {key}: {value}")
    
    print("\nvoltage chart:")
    chart = get_cr2032_voltage_chart()
    for range_info in chart['voltage_ranges']:
        print(f"  {range_info['range']}: {range_info['category']} ({range_info['status']})")
import logging
from typing import Dict
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class CR2032Thresholds:
    """voltage thresholds for CR2032 batteries (in millivolts)"""
    
    # Ranges according to Energizer specifications and discharge curve
    NEW_MIN: int = 3000      # 3.0V - New battery minimum
    NEW_MAX: int = 3300      # 3.3V - New battery maximum
    OPERATIONAL: int = 2850  # 2.85V - Operational (OK)
    LOW_BATTERY: int = 2750  # 2.75V - Near dead
    DEAD_BATTERY: int = 2750 # ≤2.75V - Dead
    
    # Note: CR2032 discharge is non-linear - voltage drops slowly then sharply


class CR2032BatteryEvaluator:
    """
    Evaluador especializado for CR2032 batteries
    Implementa las reglas specifics de evaluation according to la curva de descarga de Energizer
    """
    
    def __init__(self, thresholds: CR2032Thresholds = None):
        """
        Inicializa el evaluador
        
        Args:
            thresholds: Umbrales personalizados (optional)
        """
        self.thresholds = thresholds or CR2032Thresholds()
        logger.debug(f"CR2032 Evaluator initialized with thresholds: {self.thresholds}")
    
    def evaluate_battery(self, voltage_mv: int) -> Dict:
        """
        Evalúa el estado de una battery CR2032 according to su voltage
        
        Args:
            voltage_mv: voltage en milivoltios
            
        Returns:
            Diccionario with evaluation complete:
            {
                "voltage": 3100,
                "category": "NEW | OK | LOW | DEAD",
                "status": "PASS | FAIL", 
                "advice": "message explicativo",
                "percentage_estimate": 85.0,
                "expected_life": "description de life expectancy remaining"
            }
        """
        try:
            logger.debug(f"Evaluating battery CR2032 with voltage {voltage_mv}mV")
            
            # Determinar categoría according to ranges de voltage
            category = self._determine_category(voltage_mv)
            
            # Determinar status PASS/FAIL
            status = self._determine_status(voltage_mv)
            
            # generate message de asesoramiento
            advice = self._generate_advice(voltage_mv, category)
            
            # Estimar porcentaje basado en curva CR2032
            percentage_estimate = self._estimate_percentage(voltage_mv)
            
            # Estimar life expectancy remaining
            expected_life = self._estimate_life_expectancy(voltage_mv, category)
            
            result = {
                "voltage": voltage_mv,
                "category": category,
                "status": status,
                "advice": advice,
                "percentage_estimate": percentage_estimate,
                "expected_life": expected_life,
                "battery_type": "CR2032"
            }
            
            logger.info(f"evaluation CR2032: {voltage_mv}mV -> {category} ({status})")
            return result
            
        except Exception as e:
            logger.error(f"error evaluating battery CR2032: {e}")
            return {
                "voltage": voltage_mv,
                "category": "UNKNOWN",
                "status": "FAIL",
                "advice": f"error in evaluation: {e}",
                "percentage_estimate": 0.0,
                "expected_life": "Indeterminado",
                "battery_type": "CR2032"
            }
    
    def _determine_category(self, voltage_mv: int) -> str:
        """
        Determina la categoría de la battery according to voltage
        
        Args:
            voltage_mv: voltage en milivoltios
            
        Returns:
            Category: "NEW", "OK", "LOW", "DEAD"
        """
        if self.thresholds.NEW_MIN <= voltage_mv <= self.thresholds.NEW_MAX:
            return "NEW"
        elif voltage_mv > self.thresholds.OPERATIONAL:
            return "OK" 
        elif voltage_mv > self.thresholds.LOW_BATTERY:
            return "LOW"
        else:
            return "DEAD"
    
    def _determine_status(self, voltage_mv: int) -> str:
        """
        Determina el status PASS/FAIL
        
        Args:
            voltage_mv: voltage en milivoltios
            
        Returns:
            "PASS" o "FAIL"
        """
        # PASS si la battery está operational (> 2.85V)
        return "PASS" if voltage_mv > self.thresholds.OPERATIONAL else "FAIL"
    
    def _generate_advice(self, voltage_mv: int, category: str) -> str:
        """
        Genera message de asesoramiento basado en el estado de la battery
        
        Args:
            voltage_mv: voltage en milivoltios
            category: Category determinada
            
        Returns:
            message de asesoramiento
        """
        advice_map = {
            "NEW": "Battery in excellent withdition, recently manufactured or unused.",
            "OK": "Battery operational, good performance expected.",
            "LOW": "Battery close to depletion, replace soon to avoid device failure.",
            "DEAD": "Battery depleted, immediate replacement required."
        }
        
        base_advice = advice_map.get(category, "Unknown battery status.")
        
        # add information specific according to voltage
        if voltage_mv >= 3200:
            additional = " Expected long service life."
        elif voltage_mv >= 3000:
            additional = " Monitor performance closely."
        elif voltage_mv >= 2900:
            additional = " Performance may be inwithsistent under load."
        elif voltage_mv >= 2800:
            additional = " Significant voltage drop expected under load."
        else:
            additional = " Critical voltage level reached."
        
        return base_advice + additional
    
    def _estimate_percentage(self, voltage_mv: int) -> float:
        """
        Estima el porcentaje de carga basado en la curva de descarga típica CR2032
        
        Args:
            voltage_mv: voltage en milivoltios
            
        Returns:
            Porcentaje estimado (0.0 - 100.0)
        """
        try:
            # Curva de descarga típica for CR2032 (no lineal)
            # Basada en data de Energizer for cargas típicas de IoT/BLE
            
            if voltage_mv >= 3200:
                # 95-100%: voltage high, new battery o poco usada
                percentage = 95.0 + (voltage_mv - 3200) * 0.05
                percentage = min(100.0, percentage)
            elif voltage_mv >= 3100:
                # 80-95%: voltage stable, buen estado
                percentage = 80.0 + (voltage_mv - 3100) * 0.15
            elif voltage_mv >= 3000:
                # 60-80%: start de descarga notable
                percentage = 60.0 + (voltage_mv - 3000) * 0.20
            elif voltage_mv >= 2950:
                # 40-60%: Descarga moderada
                percentage = 40.0 + (voltage_mv - 2950) * 0.40
            elif voltage_mv >= 2900:
                # 20-40%: Descarga significativa
                percentage = 20.0 + (voltage_mv - 2900) * 0.40
            elif voltage_mv >= 2850:
                # 10-20%: Nivel low pero operational
                percentage = 10.0 + (voltage_mv - 2850) * 0.20
            elif voltage_mv >= 2800:
                # 5-10%: critical pero aún functional
                percentage = 5.0 + (voltage_mv - 2800) * 0.10
            elif voltage_mv >= 2750:
                # 1-5%: Muy critical
                percentage = 1.0 + (voltage_mv - 2750) * 0.08
            else:
                # 0-1%: depleted
                percentage = max(0.0, voltage_mv / 2750)
            
            return round(percentage, 1)
            
        except Exception as e:
            logger.error(f"error calculando porcentaje CR2032: {e}")
            return 0.0
    
    def _estimate_life_expectancy(self, voltage_mv: int, category: str) -> str:
        """
        Estima la life expectancy remaining basada en el voltage actual
        
        Args:
            voltage_mv: voltage en milivoltios
            category: Category de la battery
            
        Returns:
            description de life expectancy esperada
        """
        life_map = {
            "NEW": "6-12 months under typical IoT/BLE load",
            "OK": "3-6 months depending on usage pattern", 
            "LOW": "1-4 weeks, monitor closely",
            "DEAD": "Immediate replacement needed"
        }
        
        base_life = life_map.get(category, "Indeterminado")
        
        # Ajustar according to voltage specific
        if voltage_mv >= 3200:
            return "12+ months under normal withditions"
        elif voltage_mv >= 3100:
            return "6-12 months with good performance"
        elif voltage_mv >= 3000:
            return "3-6 months, performance stable"
        elif voltage_mv >= 2950:
            return "2-4 months, begin replacement planning"
        elif voltage_mv >= 2900:
            return "1-2 months, replacement recommended"
        elif voltage_mv >= 2850:
            return "2-4 weeks, prepare for replacement"
        elif voltage_mv >= 2800:
            return "1-2 weeks maximum, urgent replacement"
        else:
            return "Replace immediately"
    
    def get_thresholds_info(self) -> Dict:
        """
        Obtiene information over los thresholds withfigurados
        
        Returns:
            Diccionario with information de thresholds
        """
        return {
            "battery_type": "CR2032",
            "new_range": f"{self.thresholds.NEW_MIN}-{self.thresholds.NEW_MAX}mV",
            "operational_min": f"{self.thresholds.OPERATIONAL}mV",
            "low_threshold": f"{self.thresholds.LOW_BATTERY}mV",
            "dead_threshold": f"≤{self.thresholds.DEAD_BATTERY}mV",
            "discharge_characteristic": "Non-linear (gradual then rapid drop)",
            "typical_load": "IoT/BLE devices (1-10mA pulses)"
        }


def evaluate_battery(voltage_mv: int, custom_thresholds: CR2032Thresholds = None) -> Dict:
    """
    function de withveniencia to evaluate una battery CR2032
    
    Args:
        voltage_mv: voltage en milivoltios
        custom_thresholds: Umbrales personalizados (optional)
        
    Returns:
        Diccionario with evaluation complete
    """
    evaluator = CR2032BatteryEvaluator(custom_thresholds)
    return evaluator.evaluate_battery(voltage_mv)


def get_cr2032_voltage_chart() -> Dict:
    """
    Obtiene una table de reference de voltajes vs estados for CR2032
    
    Returns:
        Diccionario with table de reference
    """
    return {
        "title": "CR2032 voltage Reference Chart",
        "voltage_ranges": [
            {"range": "3.0V - 3.3V", "category": "NEW", "status": "PASS", "description": "Fresh battery"},
            {"range": "> 2.85V", "category": "OK", "status": "PASS", "description": "Operational"},
            {"range": "2.75V - 2.85V", "category": "LOW", "status": "FAIL", "description": "Near depletion"},
            {"range": "≤ 2.75V", "category": "DEAD", "status": "FAIL", "description": "Depleted"}
        ],
        "notes": [
            "CR2032 discharge is non-linear",
            "voltage drops slowly then rapidly",
            "Load pulses can cause temporary voltage drops",
            "Temperature affects voltage readings"
        ]
    }


if __name__ == "__main__":
    # demo del evaluador CR2032
    print("=== demo: Evaluador de CR2032 batteries ===")
    
    test_voltages = [3300, 3200, 3100, 3000, 2950, 2900, 2850, 2800, 2750, 2700, 2600]
    
    evaluator = CR2032BatteryEvaluator()
    
    print("\nEvaluation de voltajes de test:")
    print("-" * 80)
    print(f"{'voltage':<8} {'Category':<8} {'Status':<6} {'%':<6} {'Expected Life':<25} {'Advice'}")
    print("-" * 80)
    
    for voltage in test_voltages:
        result = evaluator.evaluate_battery(voltage)
        print(f"{voltage}mV   {result['category']:<8} {result['status']:<6} "
              f"{result['percentage_estimate']:<5.1f}% {result['expected_life']:<25} "
              f"{result['advice'][:40]}...")
    
    print("\n" + "="*80)
    print("information de thresholds:")
    thresholds_info = evaluator.get_thresholds_info()
    for key, value in thresholds_info.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*80)
