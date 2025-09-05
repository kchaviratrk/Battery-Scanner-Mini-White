"""
BLE Battery Scanner for nRF52DK
Main application for scanning and evaluating CR2032 batteries in BLE devices
Windows optimized version for c:/Battery-Scanner-Mini-White
"""
import logging
import time
import signal
import sys
import os
from typing import List, Dict
from threading import Event
from pathlib import Path

from config import config
from scanner.driver import BLEDriverManager
from scanner.observer import BLEScannerObserver
from scanner.results import ResultsManager


def setup_logging():
    """Configure logging for Windows deployment"""
    log_dir = Path("c:/Battery-Scanner-Mini-White/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / 'scanner.log')
        ]
    )


logger = logging.getLogger(__name__)


class BLEBatteryScanner:
    """Main BLE scanner for CR2032 battery monitoring"""
    
    def __init__(self):
        """Initialize the BLE scanner"""
        self.driver_manager: BLEDriverManager = None
        self.observer: BLEScannerObserver = None
        self.results_manager: ResultsManager = None
        self.scan_complete_event = Event()
        self.running = True
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Signal {signum} received, shutting down...")
        self.running = False
        self.scan_complete_event.set()
    
    def initialize(self) -> bool:
        """Initialize all scanner components"""
        try:
            logger.info("Initializing BLE Scanner for CR2032 battery monitoring")
            logger.info(f"Target location: c:/Battery-Scanner-Mini-White")
            
            # Create results directory
            results_dir = Path("c:/Battery-Scanner-Mini-White/results")
            results_dir.mkdir(parents=True, exist_ok=True)
            
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
            logger.error(f"Failed to initialize scanner: {e}")
            return False
    
    def _on_scan_complete(self):
        """Callback when scan completes"""
        logger.info("Scan completed - all target devices processed")
        self.scan_complete_event.set()
    
    def start_scan(self, mac_list: List[str]) -> List[Dict]:
        """Start BLE scan for specified MAC addresses"""
        try:
            if not self.running:
                return []
            
            logger.info(f"Starting scan for {len(mac_list)} target devices")
            
            # Reset observer with new MAC list
            self.observer.reset_scan(mac_list)
            self.scan_complete_event.clear()
            
            # Start scanning
            self.driver_manager.start_scan()
            
            # Wait for scan completion or timeout
            logger.info(f"Scanning for {config.SCAN_TIME} seconds...")
            
            if self.scan_complete_event.wait(timeout=config.SCAN_TIME):
                logger.info("Scan completed - all devices found")
            else:
                logger.info("Scan timeout reached")
            
            # Stop scanning
            self.driver_manager.stop_scan()
            
            # Get results
            results = self.observer.get_scan_results()
            pending_macs = self.observer.get_pending_macs()
            
            if pending_macs:
                logger.warning(f"Devices not found: {pending_macs}")
            
            logger.info(f"Scan finished. Devices processed: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Error during scanning: {e}")
            return []
    
    def run_full_scan(self) -> bool:
        """Execute complete scan of all configured devices"""
        try:
            if not self.initialize():
                return False
            
            # Get target MAC list
            mac_list = config.VALID_MAC_IDS.copy()
            all_results = []
            
            logger.info(f"Starting full scan of {len(mac_list)} target devices")
            
            # Execute scans with retry logic
            max_iterations = 3
            iteration = 0
            
            while mac_list and self.running and iteration < max_iterations:
                iteration += 1
                logger.info(f"Scan iteration {iteration}: {len(mac_list)} devices remaining")
                
                # Perform scan
                scan_results = self.start_scan(mac_list)
                
                if scan_results:
                    all_results.extend(scan_results)
                    
                    # Remove processed MACs from pending list
                    processed_macs = {result['macid'] for result in scan_results}
                    mac_list = [mac for mac in mac_list if mac not in processed_macs]
                    
                    logger.info(f"Processed {len(scan_results)} devices. Remaining: {len(mac_list)}")
                
                # Brief pause between iterations
                if mac_list and self.running:
                    time.sleep(2)
            
            # Save results
            if all_results:
                success_json, success_csv = self.results_manager.save_results(all_results)
                
                if success_json and success_csv:
                    logger.info("Results saved successfully to c:/Battery-Scanner-Mini-White/results/")
                else:
                    logger.warning("Some result files could not be saved")
                
                # Display summary
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
    """Main application entry point"""
    try:
        setup_logging()
        
        logger.info("=== BLE SCANNER FOR CR2032 BATTERY MONITORING ===")
        logger.info("Windows optimized version for c:/Battery-Scanner-Mini-White")
        logger.info(f"COM port: {config.COM_PORT}")
        logger.info(f"Scan duration: {config.SCAN_TIME} seconds")
        logger.info(f"Target devices: {len(config.VALID_MAC_IDS)}")
        
        # Create and run scanner
        scanner = BLEBatteryScanner()
        success = scanner.run_full_scan()
        
        if success:
            logger.info("=== SCAN COMPLETED SUCCESSFULLY ===")
            print("\n✅ Results saved to c:/Battery-Scanner-Mini-White/results/")
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
