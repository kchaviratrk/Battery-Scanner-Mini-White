#!/usr/bin/env python3
"""
Quick results viewer for BLE Scanner results.
Shows summary of most recent scan results.
"""
import json
import os
from pathlib import Path
from datetime import datetime

def view_results():
    results_dir = Path("c:/Battery-Scanner-Mini-White/results")
    json_file = results_dir / "scan_results.json"
    csv_file = results_dir / "scan_results.csv"
    
    print("BLE Scanner Results Summary")
    print("=" * 50)
    print(f"Results directory: {results_dir}")
    print()
    
    # Check if files exist
    if not json_file.exists() and not csv_file.exists():
        print("No results found. Run a scan first (option 3 in menu).")
        return
    
    # Display JSON results if available
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print("📊 Latest Scan Results:")
            print("-" * 30)
            
            # Show metrics
            metrics = data.get('metrics', {})
            print(f"Total devices: {metrics.get('total', 'N/A')}")
            print(f"Successfully processed: {metrics.get('processed', 'N/A')}")
            print(f"Failed: {metrics.get('failed', 'N/A')}")
            print(f"Scan time: {metrics.get('elapsed_s', 'N/A'):.1f} seconds")
            print()
            
            # Show sample results
            results = data.get('results', [])
            if results:
                print("🔋 Sample devices found:")
                print("-" * 30)
                for i, device in enumerate(results[:10]):  # Show first 10
                    mac = device.get('qr_or_mac', 'Unknown')
                    voltage = device.get('voltage_v', 0)
                    status = device.get('status', 'Unknown')
                    rssi = device.get('rssi', 'N/A')
                    print(f"{i+1:2d}. {mac} | {voltage:.2f}V | {status} | RSSI: {rssi}")
                
                if len(results) > 10:
                    print(f"    ... and {len(results) - 10} more devices")
                print()
                
                # Show status summary
                pass_count = sum(1 for r in results if r.get('pass_fail', False))
                fail_count = len(results) - pass_count
                print(f"✅ Passed: {pass_count}")
                print(f"❌ Failed: {fail_count}")
                print()
                
        except Exception as e:
            print(f"Error reading JSON results: {e}")
    
    # Show file information
    print("📁 Files available:")
    print("-" * 20)
    
    if json_file.exists():
        size = json_file.stat().st_size
        modified = datetime.fromtimestamp(json_file.stat().st_mtime)
        print(f"JSON: {json_file.name} ({size:,} bytes, modified: {modified.strftime('%Y-%m-%d %H:%M:%S')})")
    
    if csv_file.exists():
        size = csv_file.stat().st_size
        modified = datetime.fromtimestamp(csv_file.stat().st_mtime)
        print(f"CSV:  {csv_file.name} ({size:,} bytes, modified: {modified.strftime('%Y-%m-%d %H:%M:%S')})")
    
    print()
    print("📍 Full path to results:")
    print(f"   {results_dir.absolute()}")

if __name__ == "__main__":
    view_results()