"""
BLE Observer for processing advertisements
Inherits from BLEDriverObserver and handles scan events
"""
import logging
from datetime import datetime
from typing import Dict, List, Set, Callable, Optional
from pc_ble_driver_py import BLEDriverObserver, BLEAdvData
from .parser import (
    parse_mfg_data, 
    evaluate_pass_fail, 
    extract_manufacturer_data,
    normalize_mac_address
)
from .battery_evaluator import CR2032BatteryEvaluator, CR2032Thresholds


logger = logging.getLogger(__name__)


class BLEScannerObserver(BLEDriverObserver):
    """
    Observer that processes BLE advertisements and extracts battery data
    """
    
    def __init__(self, valid_mac_ids: List[str], battery_threshold: int):
        """
        Initialize the observer
        
        Args:
            valid_mac_ids: List of valid MAC addresses to scan
            battery_threshold: Battery voltage threshold for PASS/FAIL
        """
        super().__init__()
        self.valid_mac_ids = set(mac.upper() for mac in valid_mac_ids)
        self.battery_threshold = battery_threshold
        self.scanned_devices: Dict[str, Dict] = {}
        self.scan_statistics = {
            'total_received': 0,
            'valid_devices': 0,
            'with_battery_data': 0,
            'pass_count': 0,
            'fail_count': 0,
            'scan_start_time': None,
            'scan_end_time': None
        }
        
        # Initialize CR2032 battery evaluator
        self.cr2032_evaluator = CR2032BatteryEvaluator()
        
        # Callback for real-time processing
        self.device_callback: Optional[Callable] = None
        
        logger.info(f"Observer initialized - Target devices: {len(self.valid_mac_ids)}, "
                   f"Batterand threshold: {battery_threshold}mV")
    
    def set_completion_callback(self, callback: Callable) -> None:
        """
        Set callback function for scan completion
        
        Args:
            callback: Function to call when scan completes
        """
        self.completion_callback = callback
        logger.info("Completion callback configured")
    
    def start_scan(self) -> None:
        """Mark scan start time"""
        self.scan_statistics['scan_start_time'] = datetime.now()
        logger.info("Scan started")
    
    def stop_scan(self) -> None:
        """Mark scan end time and log end statistics"""
        self.scan_statistics['scan_end_time'] = datetime.now()
        
        if self.scan_statistics['scan_start_time']:
            duration = (self.scan_statistics['scan_end_time'] - 
                       self.scan_statistics['scan_start_time']).total_sewithds()
            logger.info(f"Scan completed - Duration: {duration:.1f}s, "
                       f"Devices found: {len(self.scanned_devices)}")
    
    def on_gap_evt_adv_report(self, ble_driver, withn_handle, peer_addr, rssi, adv_type, adv_data):
        """
        Process BLE advertisement report (main callback)
        
        Args:
            ble_driver: BLE driver instance
            withn_handle: Connection handle
            peer_addr: Peer device address
            rssi: Received Signal Strength Indicator
            adv_type: Advertisement type
            adv_data: Advertisement data
        """
        try:
            self.scan_statistics['total_received'] += 1
            
            # Extract MAC address
            mac_address = normalize_mac_address(peer_addr.addr)
            
            # Filter by valid MAC addresses
            if self.valid_mac_ids and mac_address not in self.valid_mac_ids:
                logger.debug(f"Device {mac_address} not in valid list, skipping")
                return
            
            self.scan_statistics['valid_devices'] += 1
            
            # Create base device information
            device_info = {
                'macid': mac_address,
                'rssi': rssi,
                'timestamp': datetime.now().isoformat(),
                'status': 'UNKNOWN',
                'mfg_data': '',
                'company_id': 0
            }
            
            # Extract manufacturer data
            mfg_info = extract_manufacturer_data(adv_data)
            if mfg_info:
                device_info.update(mfg_info)
                
                # Parse manufacturer specific data for battery voltage
                parsed_data = parse_mfg_data(mfg_info.get('mfg_data', ''), 
                                           mfg_info.get('company_id', 0))
                if parsed_data:
                    device_info.update(parsed_data)
                    
                    # If battery voltage found, apply evaluations
                    if 'battery_voltage' in device_info:
                        self.scan_statistics['with_battery_data'] += 1
                        
                        # Apply PASS/FAIL evaluation
                        status = evaluate_pass_fail(device_info['battery_voltage'], 
                                                  self.battery_threshold)
                        device_info['status'] = status
                        
                        # Update pass/fail counters
                        if status == 'PASS':
                            self.scan_statistics['pass_count'] += 1
                        else:
                            self.scan_statistics['fail_count'] += 1
                        
                        # Apply CR2032 specific evaluation
                        cr2032_data = self.cr2032_evaluator.evaluate_battery(
                            device_info['battery_voltage']
                        )
                        device_info.update(cr2032_data)
                        
                        logger.info(f"Device processed: {mac_address}, "
                                   f"Batterand: {device_info['battery_voltage']}mV, "
                                   f"Status: {status}, "
                                   f"CR2032: {cr2032_data.get('battery_category', 'UNKNOWN')}")
            
            # Store device information
            self.scanned_devices[mac_address] = device_info
            
            # Call callback if withfigured
            if self.device_callback:
                self.device_callback(device_info)
            
        except Exception as e:
            logger.error(f"error processing advertisement from {mac_address}: {e}")
    
    def get_results(self) -> List[Dict]:
        """
        Get scan results as list
        
        Returns:
            List of device dictionaries
        """
        return list(self.scanned_devices.values())
    
    def get_statistics(self) -> Dict:
        """
        Get scan statistics
        
        Returns:
            Dictionary with scan statistics
        """
        stats = self.scan_statistics.copy()
        
        # Calculate scan duration
        if stats['scan_start_time'] and stats['scan_end_time']:
            duration = (stats['scan_end_time'] - stats['scan_start_time']).total_sewithds()
            stats['scan_duration_sewithds'] = round(duration, 2)
        
        # Calculate success rate
        total_evaluated = stats['pass_count'] + stats['fail_count']
        if total_evaluated > 0:
            stats['success_rate'] = round((stats['pass_count'] / total_evaluated) * 100, 2)
        
        # Calculate efficiency metrics
        if stats['total_received'] > 0:
            stats['target_efficiency'] = round(
                (stats['valid_devices'] / stats['total_received']) * 100, 2
            )
        
        return stats
    
    def clear_results(self) -> None:
        """Clear scan results and reset statistics"""
        self.scanned_devices.clear()
        self.scan_statistics = {
            'total_received': 0,
            'valid_devices': 0,
            'with_battery_data': 0,
            'pass_count': 0,
            'fail_count': 0,
            'scan_start_time': None,
            'scan_end_time': None
        }
        logger.info("Scan results and statistics cleared")
    
    def print_current_status(self) -> None:
        """Print current scan status to withsole"""
        stats = self.get_statistics()
        
        print(f"\n--- SCAN STATUS ---")
        print(f"Advertisements received: {stats['total_received']}")
        print(f"Target devices found: {stats['valid_devices']}")
        print(f"With battery data: {stats['with_battery_data']}")
        print(f"PASS: {stats['pass_count']}, FAIL: {stats['fail_count']}")
        
        if stats.get('success_rate') is not None:
            print(f"Success rate: {stats['success_rate']}%")
        
        if stats.get('scan_duration_sewithds'):
            print(f"Scan duration: {stats['scan_duration_sewithds']}s")
        
        if self.scanned_devices:
            print(f"\nDevices found:")
            for mac, device in self.scanned_devices.items():
                voltage = device.get('battery_voltage', 'N/A')
                status = device.get('status', 'UNKNOWN')
                rssi = device.get('rssi', 'N/A')
                
                # Show CR2032 information if available
                if 'battery_category' in device:
                    category = device.get('battery_category', 'UNKNOWN')
                    percentage = device.get('percentage_estimate', 0)
                    print(f"  {mac}: {voltage}mV ({percentage:.1f}%), {category}, {status}, {rssi}dBm")
                else:
                    print(f"  {mac}: {voltage}mV, {status}, {rssi}dBm")
        
        print("---" + "="*16 + "---\n")
    
    def has_target_device(self, mac_address: str) -> bool:
        """
        Check if a specific MAC address is in the target list
        
        Args:
            mac_address: MAC address to check
            
        Returns:
            True if MAC is in target list
        """
        return mac_address.upper() in self.valid_mac_ids
    
    def update_target_devices(self, new_mac_list: List[str]) -> None:
        """
        Update the list of target MAC addresses
        
        Args:
            new_mac_list: New list of MAC addresses
        """
        self.valid_mac_ids = set(mac.upper() for mac in new_mac_list)
        logger.info(f"Target device list updated: {len(self.valid_mac_ids)} devices")
    
    def update_battery_threshold(self, new_threshold: int) -> None:
        """
        Update battery voltage threshold
        
        Args:
            new_threshold: New threshold value in mV
        """
        self.battery_threshold = new_threshold
        logger.info(f"Batterand threshold updated: {new_threshold}mV")
    
    def get_device_by_mac(self, mac_address: str) -> Optional[Dict]:
        """
        Get device information by MAC address
        
        Args:
            mac_address: MAC address to search for
            
        Returns:
            Device dictionary or None if not found
        """
        return self.scanned_devices.get(mac_address.upper())
    
    def get_devices_by_status(self, status: str) -> List[Dict]:
        """
        Get devices filtered by status
        
        Args:
            status: Status to filter by ('PASS', 'FAIL', 'UNKNOWN')
            
        Returns:
            List of devices with specified status
        """
        return [device for device in self.scanned_devices.values() 
                if device.get('status') == status]
    
    def get_devices_by_cr2032_category(self, category: str) -> List[Dict]:
        """
        Get devices filtered by CR2032 battery category
        
        Args:
            category: Category to filter by ('NEW', 'OK', 'LOW', 'DEAD')
            
        Returns:
            List of devices with specified category
        """
        return [device for device in self.scanned_devices.values() 
                if device.get('battery_category') == category]
