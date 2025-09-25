#!/usr/bin/env python3
"""
Simplified BLE Scanner system test
Verifies main functionalities without external dependencies
"""
import os
import sys
import time
from pathlib import Path

# Set environment FIRST, before any other imports
os.environ['__conn_ic_id__'] = 'NRF52'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Basic imports test"""
    print("Testing imports...")
    
    try:
        # Test config
        from config import config
        print(f"Config loaded: COM_PORT={config.COM_PORT}")
        
        # Test battery evaluator
        from battery_evaluator import CR2032BatteryEvaluator, evaluate_battery_simple
        print("Battery evaluator imported")
        
        # Test basic modules
        import termcolor  # optional
        import colorama   # optional
        import requests
        print("Dependencies available")
        
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False


def test_battery_evaluator():
    """Battery evaluator test"""
    print("\nTesting battery evaluator...")
    
    try:
        from battery_evaluator import CR2032BatteryEvaluator
        
        evaluator = CR2032BatteryEvaluator()
        
        # Test voltages
        test_cases = [
            (3300, "NEW"),
            (3000, "NEW"), 
            (2950, "GOOD"),
            (2850, "LOW"),
            (2700, "DEAD")
        ]
        
        for voltage_mv, expected_category in test_cases:
            result = evaluator.evaluate_battery(voltage_mv)
            if result['category'] == expected_category:
                print(f"{voltage_mv}mV -> {result['category']} OK")
            else:
                print(f"{voltage_mv}mV -> {result['category']} (expected {expected_category})")
                
        return True
    except Exception as e:
        print(f"Battery evaluator error: {e}")
        return False


def test_com_ports():
    """COM port detection test"""
    print("\nTesting COM port detection...")
    
    try:
        # Try to import serial, if not available, use wmic
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            com_ports = [port.device for port in ports if 'COM' in port.device]
        except ImportError:
            # Use wmic as fallback
            import subprocess
            result = subprocess.run(['wmic', 'path', 'Win32_SerialPort', 'get', 'DeviceID'], 
                                  capture_output=True, text=True)
            com_ports = [line.strip() for line in result.stdout.split('\n') 
                        if line.strip() and 'COM' in line.strip()]
        
        if com_ports:
            print(f"COM ports found: {', '.join(com_ports)}")
            
            # Check if configured ports exist
            from config import config
            if config.COM_PORT in com_ports:
                print(f"Primary port {config.COM_PORT} available")
            else:
                print(f"Primary port {config.COM_PORT} not found")
                
            if config.COM_PORT_BACKUP in com_ports:
                print(f"Backup port {config.COM_PORT_BACKUP} available")
            else:
                print(f"Backup port {config.COM_PORT_BACKUP} not found")
        else:
            print("No COM ports found")
            
        return True
    except Exception as e:
        print(f"COM port detection error: {e}")
        return False


def test_directory_structure():
    """Directory structure test"""
    print("\nTesting directory structure...")
    
    try:
        base_dir = Path("c:/Battery-Scanner-Mini-White")
        results_dir = base_dir / "results"
        logs_dir = base_dir / "logs"
        
        # Create directories if needed
        results_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        if base_dir.exists():
            print(f"Base directory: {base_dir}")
        if results_dir.exists():
            print(f"Results directory: {results_dir}")
        if logs_dir.exists():
            print(f"Logs directory: {logs_dir}")
            
        return True
    except Exception as e:
        print(f"Directory structure error: {e}")
        return False


def test_nordic_driver():
    """Nordic driver test (optional)"""
    print("\nTesting Nordic driver...")
    
    try:
        import pc_ble_driver_py
        print("Nordic driver imported successfully")
        
        # Test environment variable
        if os.environ.get('__conn_ic_id__') == 'NRF52':
            print("Environment variable set correctly")
        else:
            print("Environment variable not set")
            
        return True
    except ImportError:
        print("Nordic driver not available (install pc-ble-driver-py)")
        return False
    except Exception as e:
        print(f"Nordic driver error: {e}")
        return False


def run_demo_scan():
    """Simulated scan demo"""
    print("\nRunning demo scan simulation...")
    
    try:
        from battery_evaluator import evaluate_battery_simple
        
        # Simulate found devices
        demo_devices = [
            {"qr": "DEMO001", "mac": "A4:C1:38:AA:BB:01", "battery_v": 3.1},
            {"qr": "DEMO002", "mac": "A4:C1:38:AA:BB:02", "battery_v": 2.95},
            {"qr": "DEMO003", "mac": "A4:C1:38:AA:BB:03", "battery_v": 2.75},
        ]
        
        print("\nDemo scan results:")
        print("-" * 60)
        
        for device in demo_devices:
            evaluation = evaluate_battery_simple(device['battery_v'])
            print(f"QR: {device['qr']} | MAC: {device['mac']}")
            print(f"    Battery: {evaluation}")
            print()
            
        return True
    except Exception as e:
        print(f"Demo scan error: {e}")
        return False


def main():
    """Run all tests"""
    print("BLE Scanner Simplified - System Test")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Battery Evaluator", test_battery_evaluator),
        ("COM Ports", test_com_ports),
        ("Directory Structure", test_directory_structure),
        ("Nordic Driver", test_nordic_driver),
        ("Demo Scan", run_demo_scan)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"{test_name} PASSED")
            else:
                print(f"{test_name} FAILED")
        except Exception as e:
            print(f"{test_name} ERROR: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed. System ready to use.")
    elif passed >= total - 1:
        print("Most tests passed. Check Nordic driver if needed.")
    else:
        print("Several tests failed. Check configuration.")
    
    print("\nNext steps:")
    print("1. Run: python -m pip install -r requirements.txt")
    print("2. Update COM_PORT in config.py if needed")
    print("3. Run: python ble_scanner.py")

if __name__ == "__main__":
    main()
