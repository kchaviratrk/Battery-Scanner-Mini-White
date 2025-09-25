#!/usr/bin/env python3
"""
Test quick discover functionality to verify BLE scanning works
"""
from ble_scanner import discover_nearby_devices
from config import ScannerConfig
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_discover():
    """Test discover functionality briefly"""
    print("Testing BLE device discovery with COM6...")
    print("=" * 50)
    
    config = ScannerConfig()
    
    try:
        # Quick 10-second discover test
        print(f"Using COM port: {config.COM_PORT}")
        print("Scanning for 10 seconds...")
        
        # Discover nearby devices with short timeout
        devices = discover_nearby_devices(scan_duration=10, scan_all_rssi=True)
        
        print(f"\nDiscovered {len(devices)} devices:")
        
        # Parse the device info if it's in the expected format
        if devices and len(devices) > 0:
            print("First few devices found:")
            for i, device_info in enumerate(devices[:5]):  # Show only first 5
                print(f"  {i+1}. {device_info}")
        
        if len(devices) > 5:
            print(f"  ... and {len(devices) - 5} more devices")
            
        print(f"\n✅ DISCOVER TEST PASSED - Found {len(devices)} devices")
        return True
        
    except Exception as e:
        print(f"❌ DISCOVER TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_discover()
    exit(0 if success else 1)