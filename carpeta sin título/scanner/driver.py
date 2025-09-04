"""
BLE Driver for nRF52DK
Handles initialization and control of BLEDriver
"""
import logging
from typing import Optional
from pc_ble_driver_py import BLEDriver, BLEDriverError, BLEAdvData
from pc_ble_driver_py.exceptions import NordicSemiException


logger = logging.getLogger(__name__)


class BLEDriverManager:
    """Handles initialization and control of Nordic BLEDriver"""
    
    def __init__(self, com_port: str):
        """
        Initialize the BLE driver manager
        
        Args:
            com_port: COM port where nRF52DK is connected
        """
        self.com_port = com_port
        self.driver: Optional[BLEDriver] = None
        self._is_initialized = False
    
    def initialize_driver(self) -> BLEDriver:
        """
        Initialize the BLE driver
        
        Returns:
            Initialized BLEDriver instance
            
        Raises:
            BLEDriverError: If driver initialization fails
            NordicSemiException: If there are problems with Nordic hardware
        """
        try:
            logger.info(f"Initializing BLE driver on port {self.com_port}")
            
            # Create driver instance
            self.driver = BLEDriver(
                serial_port=self.com_port,
                auto_flash=True  # Automatically flash firmware if necessary
            )
            
            # Open connection
            self.driver.open()
            
            # Enable BLE receiver
            self.driver.ble_enable()
            
            self._is_initialized = True
            logger.info("BLE driver initialized correctly")
            
            return self.driver
            
        except BLEDriverError as e:
            logger.error(f"Error initializing BLE driver: {e}")
            raise
        except NordicSemiException as e:
            logger.error(f"Nordic hardware error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing driver: {e}")
            raise BLEDriverError(f"Unexpected error: {e}")
    
    def close_driver(self) -> None:
        """
        Close the BLE driver connection
        """
        try:
            if self.driver and self._is_initialized:
                logger.info("Closing BLE driver")
                self.driver.close()
                self._is_initialized = False
                logger.info("BLE driver closed correctly")
        except Exception as e:
            logger.error(f"Error closing BLE driver: {e}")
    
    def is_initialized(self) -> bool:
        """
        Check if driver is initialized
        
        Returns:
            True if driver is initialized, False otherwise
        """
        return self._is_initialized and self.driver is not None
    
    def start_scan(self) -> None:
        """
        Start BLE scan
        
        Raises:
            BLEDriverError: If driver is not initialized or scan fails
        """
        if not self.is_initialized():
            raise BLEDriverError("Driver not initialized")
        
        try:
            logger.info("Starting BLE scan")
            self.driver.ble_gap_scan_start()
            logger.info("BLE scan started")
        except Exception as e:
            logger.error(f"Error starting scan: {e}")
            raise BLEDriverError(f"Error starting scan: {e}")
    
    def stop_scan(self) -> None:
        """
        Stop BLE scan
        
        Raises:
            BLEDriverError: If driver is not initialized or stop fails
        """
        if not self.is_initialized():
            raise BLEDriverError("Driver not initialized")
        
        try:
            logger.info("Stopping BLE scan")
            self.driver.ble_gap_scan_stop()
            logger.info("BLE scan stopped")
        except Exception as e:
            logger.error(f"Error stopping scan: {e}")
            raise BLEDriverError(f"Error stopping scan: {e}")


def initialize_driver(com_port: str) -> BLEDriverManager:
    """
    Convenience function to initialize BLE driver
    
    Args:
        com_port: nRF52DK COM port
        
    Returns:
        Initialized BLEDriverManager instance
    """
    manager = BLEDriverManager(com_port)
    manager.initialize_driver()
    return manager
