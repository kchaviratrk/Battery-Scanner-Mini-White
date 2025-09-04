"""
Main BLE scanner module for nRF52DK
Orchestrates BLE device scanning and battery data extraction
"""
import logging
import time
import signal
import sys
from typing import List, Dict
from threading import Event

from config import config
from scanner.driver import BLEDriverManager
from scanner.observer import BLEScannerObserver
from scanner.results import ResultsManager


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ble_scanner.log')
    ]
)

logger = logging.getLogger(__name__)


class BLEBatteryScanner:
    """
    scanner principal for detect devices BLE y extraer battery voltage
    """
    
    def __init__(self):
        """Inicializa el scanner BLE"""
        self.driver_manager: BLEDriverManager = None
        self.observer: BLEScannerObserver = None
        self.results_manager: ResultsManager = None
        self.scan_complete_event = Event()
        self.running = True
        
        # withfigure manejo de señales for cierre limpio
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Maneja señales for cierre limpio"""
        logger.info(f"Señal {signum} recibida, cerrando application...")
        self.running = False
        self.scan_complete_event.set()
    
    def initialize(self) -> bool:
        """
        Initialize all scanner components
        
        Returns:
            True si la inicialización fue successful
        """
        try:
            logger.info("Initializing BLE scanner")
            
            # Initialize driver
            self.driver_manager = BLEDriverManager(config.COM_PORT)
            self.driver_manager.initialize_driver()
            
            # Initialize observer
            self.observer = BLEScannerObserver(
                valid_mac_ids=config.VALID_MAC_IDS,
                battery_threshold=config.BATTERY_THRESHOLD
            )
            
            # Configure completion callback
            self.observer.set_completion_callback(self._on_scan_complete)
            
            # Register observer with driver
            self.driver_manager.driver.observer_register(self.observer)
            
            # Initialize results manager
            self.results_manager = ResultsManager(
                json_file=config.OUTPUT_JSON_FILE,
                csv_file=config.OUTPUT_CSV_FILE
            )
            
            logger.info("BLE Scanner initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing scanner: {e}")
            return False
    
    def _on_scan_complete(self):
        """Callback called when scan completes"""
        logger.info("Scan completed, all MACs processed")
        self.scan_complete_event.set()
    
    def start_scan(self, mac_list: List[str]) -> List[Dict]:
        """
        Starts BLE scan for specified MAC list
        
        Args:
            mac_list: List of MAC addresses to search
            
        Returns:
            List of scan results
        """
        try:
            if not self.running:
                return []
            
            logger.info(f"Starting scan for {len(mac_list)} devices")
            
            # Reset observer with new MAC list
            self.observer.reset_scan(mac_list)
            self.scan_complete_event.clear()
            
            # Start scan
            self.driver_manager.start_scan()
            
            # Wait for configured time or until complete
            logger.info(f"Scanning for {config.SCAN_TIME} seconds...")
            
            scan_timeout = False
            if self.scan_complete_event.wait(timeout=config.SCAN_TIME):
                logger.info("Scan completed by detecting all MACs")
            else:
                logger.info("Scan time expired")
                scan_timeout = True
            
            # Stop scan
            self.driver_manager.stop_scan()
            
            # Get results
            results = self.observer.get_scan_results()
            pending_macs = self.observer.get_pending_macs()
            
            if pending_macs and scan_timeout:
                logger.warning(f"MACs not found: {pending_macs}")
            
            logger.info(f"Scan finished. Devices processed: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Error during scan: {e}")
            return []
    
    def run_full_scan(self) -> bool:
        """
        Execute a complete scan of all configured devices
        
        Returns:
            True if scan completed successfully
        """
        try:
            if not self.initialize():
                return False
            
            # Get list of MACs to scan
            mac_list = config.VALID_MAC_IDS.copy()
            all_results = []
            
            logger.info(f"Starting full scan of {len(mac_list)} devices")
            
            # Execute scans until all MACs are processed
            max_iterations = 5  # Limit iterations to avoid infinite loops
            iteration = 0
            
            while mac_list and self.running and iteration < max_iterations:
                iteration += 1
                logger.info(f"Iteration {iteration}: scanning {len(mac_list)} pending devices")
                
                # Perform scan
                scan_results = self.start_scan(mac_list)
                
                if scan_results:
                    all_results.extend(scan_results)
                    
                    # Remove processed MACs from pending list
                    processed_macs = {result['macid'] for result in scan_results}
                    mac_list = [mac for mac in mac_list if mac not in processed_macs]
                    
                    logger.info(f"Processed {len(scan_results)} devices. Pending: {len(mac_list)}")
                else:
                    logger.warning("No results obtained in this iteration")
                
                # Pause between iterations if devices remain
                if mac_list and self.running:
                    logger.info("Waiting before next iteration...")
                    time.sleep(2)
            
            # Save all results
            if all_results:
                success_json, success_csv = self.results_manager.save_results(all_results)
                
                if success_json and success_csv:
                    logger.info("Results saved successfully")
                else:
                    logger.warning("Some files could not be saved")
                
                # Show summary
                self.results_manager.print_summary(all_results)
                
                return True
            else:
                logger.warning("No scan results obtained")
                return False
                
        except Exception as e:
            logger.error(f"Error in full scan: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources and close connections"""
        try:
            logger.info("Cleaning up resources...")
            
            if self.driver_manager:
                self.driver_manager.close_driver()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """Main program function"""
    try:
        logger.info("=== STARTING BLE SCANNER FOR BATTERIES ===")
        logger.info(f"COM port: {config.COM_PORT}")
        logger.info(f"Battery threshold: {config.BATTERY_THRESHOLD} mV")
        logger.info(f"Scan time: {config.SCAN_TIME} seconds")
        logger.info(f"Valid MACs: {len(config.VALID_MAC_IDS)}")
        
        # Create and execute scanner
        scanner = BLEBatteryScanner()
        success = scanner.run_full_scan()
        
        if success:
            logger.info("=== SCAN COMPLETED SUCCESSFULLY ===")
            sys.exit(0)
        else:
            logger.error("=== SCAN FAILED ===")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Scan interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
