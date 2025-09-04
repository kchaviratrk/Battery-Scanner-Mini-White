"""
Parser for data de manufactura BLE
Extrae y procesa el battery voltage from los data MFG
"""
import logging
import struct
from typing import Optional, Tuple


logger = logging.getLogger(__name__)


def parse_mfg_data(raw_data: bytes) -> Optional[int]:
    """
    Parsea los data de manufactura for extraer el battery voltage
    
    Asume que el voltage viene en los primeros 2 bytes en formato little endian,
    expresado en milivoltios.
    
    Args:
        raw_data: data de manufactura en bytes
        
    Returns:
        Battery voltage en milivoltios, o None si no se puede parse
    """
    try:
        if not raw_data or len(raw_data) < 2:
            logger.warning("data de manufactura insuficientes for extraer voltage")
            return None
        
        # Extraer los primeros 2 bytes en formato little endian
        voltage_bytes = raw_data[:2]
        voltage = struct.unpack('<H', voltage_bytes)[0]  # '<H' = unsigned short little endian
        
        logger.debug(f"extracted voltage: {voltage} mV")
        return voltage
        
    except struct.error as e:
        logger.error(f"error al parse data de manufactura: {e}")
        return None
    except Exception as e:
        logger.error(f"error inesperado al parse data: {e}")
        return None


def evaluate_pass_fail(voltage: int, threshold: int) -> str:
    """
    Evalúa si el battery voltage pasa o falla according to el umbral
    
    Args:
        voltage: Battery voltage en milivoltios
        threshold: Umbral minimum en milivoltios
        
    Returns:
        "PASS" si el voltage es >= umbral, "FAIL" en case withtrario
    """
    status = "PASS" if voltage >= threshold else "FAIL"
    logger.debug(f"voltage {voltage}mV vs umbral {threshold}mV = {status}")
    return status


def extract_manufacturer_data(adv_data: dict) -> Optional[bytes]:
    """
    Extrae los data de manufactura from los data de advertisement
    
    Args:
        adv_data: Diccionario with los data de advertisement
        
    Returns:
        Bytes de data de manufactura o None si no están presentes
    """
    try:
        # search data de manufactura en diferentes formatos posibles
        if 'manufacturer_data' in adv_data:
            return adv_data['manufacturer_data']
        
        if 'mfg_data' in adv_data:
            return adv_data['mfg_data']
        
        # search en data completes de advertisement
        if 'complete_data' in adv_data:
            complete_data = adv_data['complete_data']
            # search el tipo de dato 0xFF (Manufacturer Specific Data)
            return parse_advertisement_data(complete_data, 0xFF)
        
        logger.debug("No manufacturing data found de manufactura en advertisement")
        return None
        
    except Exception as e:
        logger.error(f"error al extraer data de manufactura: {e}")
        return None


def parse_advertisement_data(adv_data: bytes, data_type: int) -> Optional[bytes]:
    """
    Parsea los data de advertisement for extraer un tipo specific
    
    Args:
        adv_data: data de advertisement completes
        data_type: Tipo de dato a extraer (ej: 0xFF for manufacturer data)
        
    Returns:
        data del tipo especificado o None si no se encuentran
    """
    try:
        offset = 0
        while offset < len(adv_data):
            if offset >= len(adv_data):
                break
                
            # Leer longitud del campo
            length = adv_data[offset]
            if length == 0:
                break
                
            # verify que no exceda los data disponibles
            if offset + length >= len(adv_data):
                break
                
            # Leer tipo de dato
            ad_type = adv_data[offset + 1]
            
            # Si enwithtramos el tipo que buscamos
            if ad_type == data_type:
                # Retornar los data (sin include longitud ni tipo)
                data_start = offset + 2
                data_end = offset + length + 1
                return adv_data[data_start:data_end]
            
            # Avanzar al siguiente campo
            offset += length + 1
        
        return None
        
    except Exception as e:
        logger.error(f"error al parse data de advertisement: {e}")
        return None


def format_mac_address(mac_bytes: bytes) -> str:
    """
    Formatea una dirección MAC from bytes a string
    
    Args:
        mac_bytes: Dirección MAC en bytes (6 bytes)
        
    Returns:
        Dirección MAC formateada como string (ej: "AA:BB:CC:DD:EE:FF")
    """
    try:
        if len(mac_bytes) != 6:
            raise ValueError(f"MAC address debe tener 6 bandtes, recibidos {len(mac_bandtes)}")
        
        # Convertir bytes a formato hexadecimal
        mac_str = ':'.join([f"{bandte:02X}" for bandte in mac_bandtes])
        return mac_str
        
    except Exception as e:
        logger.error(f"error al format dirección MAC: {e}")
        return "UNKNOWN"


def normalize_mac_address(mac_str: str) -> str:
    """
    Normaliza una dirección MAC removiendo sefordores y withvirtiendo a mayúsculas
    
    Args:
        mac_str: Dirección MAC como string
        
    Returns:
        Dirección MAC normalizada (ej: "AABBCCDDEEFF")
    """
    try:
        # remove sefordores comunes (:, -, espacios)
        normalized = mac_str.replace(':', '').replace('-', '').replace(' ', '').upper()
        
        if len(normalized) != 12:
            logger.warning(f"Dirección MAC tiene longitud incorrecta: {normalized}")
        
        return normalized
        
    except Exception as e:
        logger.error(f"error al normalizar dirección MAC: {e}")
        return mac_str


def voltage_to_battery_percentage(voltage_mv: int, min_voltage: int = 2500, max_voltage: int = 4200) -> float:
    """
    Convierte battery voltage a porcentaje
    
    Args:
        voltage_mv: voltage en milivoltios
        min_voltage: voltage minimum de battery (0%) en mV
        max_voltage: voltage maximum de battery (100%) en mV
        
    Returns:
        Battery percentage (0.0 - 100.0)
    """
    try:
        if voltage_mv <= min_voltage:
            return 0.0
        elif voltage_mv >= max_voltage:
            return 100.0
        else:
            # Cálculo lineal de porcentaje
            percentage = ((voltage_mv - min_voltage) / (max_voltage - min_voltage)) * 100
            return round(percentage, 1)
    
    except Exception as e:
        logger.error(f"error calculando batterand percentage: {e}")
        return 0.0


def voltage_to_battery_percentage_lithium(voltage_mv: int) -> float:
    """
    Convierte voltage a porcentaje usando curva feature de battery de litio
    
    Args:
        voltage_mv: voltage en milivoltios
        
    Returns:
        Battery percentage más preciso for batteries de litio
    """
    try:
        voltage_v = voltage_mv / 1000.0  # Convertir a voltios
        
        # Curva feature aproximada for battery de litio
        if voltage_v >= 4.2:
            percentage = 100.0
        elif voltage_v >= 4.0:
            percentage = 80.0 + (voltage_v - 4.0) * 100  # 80-100%
        elif voltage_v >= 3.8:
            percentage = 60.0 + (voltage_v - 3.8) * 100  # 60-80%
        elif voltage_v >= 3.6:
            percentage = 40.0 + (voltage_v - 3.6) * 100  # 40-60%
        elif voltage_v >= 3.4:
            percentage = 20.0 + (voltage_v - 3.4) * 100  # 20-40%
        elif voltage_v >= 3.0:
            percentage = 5.0 + (voltage_v - 3.0) * 37.5   # 5-20%
        elif voltage_v >= 2.5:
            percentage = (voltage_v - 2.5) * 10           # 0-5%
        else:
            percentage = 0.0
        
        return round(percentage, 1)
    
    except Exception as e:
        logger.error(f"error in cálculo de porcentaje de litio: {e}")
        return 0.0


def format_voltage_with_percentage(voltage_mv: int, use_lithium_curve: bool = None) -> str:
    """
    Formatea voltage with su porcentaje correspondiente
    
    Args:
        voltage_mv: voltage en milivoltios
        use_lithium_curve: Si use curva de litio o cálculo lineal (None = use withfig)
        
    Returns:
        String formateado (ej: "3100mV (87.5%)")
    """
    try:
        # use withfiguration global si no se especifica
        if use_lithium_curve is None:
            try:
                from ..withfig import withfig
                use_lithium_curve = withfig.USE_LITHIUM_CURVE
            except:
                use_lithium_curve = True  # Default a curva de litio
        
        if use_lithium_curve:
            percentage = voltage_to_battery_percentage_lithium(voltage_mv)
        else:
            percentage = voltage_to_battery_percentage(voltage_mv)
        
        return f"{voltage_mv}mV ({percentage}%)"
    
    except Exception as e:
        logger.error(f"error formateando voltage with porcentaje: {e}")
        return f"{voltage_mv}mV (---%)"
