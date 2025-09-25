"""
BLE Battery Scanner - Simplified and Unified Version
Universal scanner for CR2032 in BLE devices using Nordic nRF52DK
No differences between device types - unified protocol
"""
import os
import sys

# Environment validation before any other imports
import logging

def check_python_version():
    """Check if Python version is compatible with pc-ble-driver-py."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print("ERROR: pc-ble-driver-py is not compatible with Python 3.11+.")
        print(f"Detected Python {version.major}.{version.minor}.{version.micro}")
        print("Please install Python 3.10.x (recommended: 3.10.11).")
        sys.exit(1)
    elif version.major != 3 or version.minor < 7:
        print("ERROR: Python 3.7+ is required.")
        print(f"Detected Python {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    else:
        # Silent on success
        pass


def check_pc_ble_driver_py_version():
    """Check pc-ble-driver-py version and compatibility."""
    try:
        import pc_ble_driver_py
        version_str = getattr(pc_ble_driver_py, '__version__', 'unknown')
        from config import config
        compat_map = config.PC_BLE_DRIVER_COMPAT
        # Extract major.minor from version string
        try:
            version_parts = version_str.split('.')
            major_minor = f"{version_parts[0]}.{version_parts[1]}"
        except (IndexError, ValueError):
            major_minor = version_str
        if major_minor in compat_map:
            # Silent on success
            pass
        else:
            logging.warning(
                "pc-ble-driver-py version %s compatibility unknown. Supported: %s",
                version_str, ", ".join(sorted(compat_map.keys()))
            )
    except ImportError:
        print("ERROR: pc-ble-driver-py not installed.")
        print("Please run: pip install pc-ble-driver-py")
        sys.exit(1)
    except Exception as e:
        logging.warning("Could not check pc-ble-driver-py version: %s", e)


def validate_environment():
    """Run all environment checks silently unless errors."""
    check_python_version()
    check_pc_ble_driver_py_version()

# Run validation before any other imports
validate_environment()

# Set Nordic driver environment after validation - use SD API v5
os.environ['__conn_ic_id__'] = 'NRF52'
os.environ['SD_API_VER'] = '5'

import pc_ble_driver_py.config as pc_config
pc_config.__conn_ic_id__ = 'NRF52'

import logging
import time
import signal
import sys
import pytz
import requests
import json
import csv
from collections import deque
from time import perf_counter
from typing import List, Dict
from threading import Event
from pathlib import Path
from pc_ble_driver_py.ble_driver import BLEDriver, BLEEnableParams, BLEGapScanParams
from pc_ble_driver_py.observers import BLEDriverObserver
from datetime import datetime, timezone as dt_timezone, timedelta
from pytz import timezone as pytz_timezone, utc
from colorama import init

from config import config
from utils.ports import get_com_port
from utils.telemetry import send_batch_summary, post_manuf_event, load_env
import uuid

# Simplified configuration
COM_PORT = config.COM_PORT
BATTERY_THRESHOLD = config.BATTERY_THRESHOLD

# Global variables for scan results
raw_rssi = ""
raw_battery = ""
rssi_flag = False
battery_flag = False

# API endpoints for traceability
API_ENDPOINT = "http://vmprdate.eastus.cloudapp.azure.com:9000/api/v1/manifest"
QRMAC_ENDPOINT = API_ENDPOINT


def ManufEvent(qr_or_mac, failure_code, details):
    """Post per-device manufacturing event using form-encoded API.
    - qr_or_mac: QR code (preferred). If None, MAC may be used (API may require QR).
    - failure_code: 'ALL-PASS-000' or 'ALL-FAIL-000' (per-device reflects real result).
    - details: dict with device fields to compose CSV row, or plain string for notes.
    """
    try:
        env = load_env()
        now = datetime.now(dt_timezone.utc)
        # Build notes: CSV header + one line, or raw string
        if isinstance(details, dict):
            header = 'qr_or_mac,voltage_v,voltage_mv,category,status,percentage_estimate,pass_fail,rssi,comment,timestamp'
            row = [
                str(details.get('qr_or_mac', qr_or_mac) or ''),
                str(details.get('voltage_v', '')),
                str(details.get('voltage_mv', '')),
                str(details.get('category', '')),
                str(details.get('status', '')),
                str(details.get('percentage_estimate', '')),
                str(details.get('pass_fail', '')),
                str(details.get('rssi', '')),
                str(details.get('comment', '')),
                str(details.get('timestamp', '')),
            ]
            csv_line = ",".join(row)
            notes = f"{header}\n{csv_line}"
            # Guard size
            if len(notes) > 7900:
                notes = notes[:7900] + "\n... (truncated)"
        else:
            notes = str(details)
        status = post_manuf_event(
            curr_qr=str(qr_or_mac or ''),
            failure_code=failure_code,
            start_time=now,
            end_time=now,
            notes=notes,
            station_id=env['station_id'],
            operator_id=env['operator_id'],
            api_url=env['api_url']
        )
        if status and 200 <= status < 300:
            print("Per-device event posted")
        else:
            print(f"Per-device event failed (HTTP {status})")
    except Exception as e:
        print(f"Error posting per-device event: {e}")


def databaseUpdate(qrCode, new_comment):
    """Append new comment without overwriting existing database comment."""
    try:
        response = requests.get(f'{API_ENDPOINT}?qrCode={qrCode}')
        if response.status_code == 200:
            data = response.json()
            existing_comment = data.get('comment', '')
            
            if existing_comment:
                updated_comment = f"{existing_comment} | {new_comment}"
            else:
                updated_comment = new_comment
                
            update_payload = {
                "qrCode": qrCode,
                "comment": updated_comment
            }
            
            update_response = requests.put(API_ENDPOINT, json=update_payload)
            if update_response.status_code == 200:
                print("Database updated successfully")
            else:
                print(f"Failed to update database: {update_response.status_code}")
                
    except Exception as e:
        print(f"Error updating database: {e}")


class UniversalBLEScanObserver(BLEDriverObserver):
    """Universal observer for all BLE devices - no differences by type"""
    
    def __init__(self, ble_driver, formatted_mac, qrcode):
        super().__init__()
        self.ble_driver = ble_driver
        self.formatted_mac = formatted_mac
        self.qrcode = qrcode

    def on_gap_evt_adv_report(self, ble_driver, conn_handle, peer_addr, rssi, adv_type, adv_data):
        global raw_rssi, raw_battery, rssi_flag, battery_flag
        mac_address = ':'.join(f'{byte:02X}' for byte in peer_addr.addr).strip()
        
        if mac_address == self.formatted_mac:
            #print(f"Device found: {self.formatted_mac}")
            
            # Universal protocol - try both formats automatically
            battery_parsed = False
            
            for data_type, adv_payload in adv_data.records.items():
                if str(data_type) == "Types.manufacturer_specific_data":
                    
                    # Protocol 1: Complex format (ex Mini-Gold)
                    if len(adv_payload) == 26 and adv_payload[-2] == 179 and adv_payload[-3] == 255:
                        #print(f"Data received (Protocol 1): RSSI: {rssi}, MAC: {self.formatted_mac}")
                        try:
                            battery_int = float(adv_payload[-1])
                            battery_dec = float(adv_payload[-4]) / 100
                            battery = battery_int + battery_dec
                            #print(f"Battery Voltage: {battery}V")
                            battery_parsed = True
                        except Exception as e:
                            print(f"Error parsing data (Protocol 1): {e}")
                    
                    # Protocol 2: Simple format (ex Mini-White)  
                    elif len(adv_payload) >= 2 and not battery_parsed:
                        #print(f"Data received (Protocol 2): RSSI: {rssi}, MAC: {self.formatted_mac}")
                        try:
                            battery = float(adv_payload[-1]) / 10
                            #print(f"Battery Voltage: {battery}V")
                            battery_parsed = True
                        except Exception as e:
                            print(f"Error parsing data (Protocol 2): {e}")
                    
                    if battery_parsed:
                        raw_rssi = rssi
                        raw_battery = battery
                        
                        # Evaluate parameters - but don't filter out devices based on RSSI
                        rssi_flag = rssi > -55  # This is just for informational purposes
                        battery_flag = battery > BATTERY_THRESHOLD
                        
                        # Always report RSSI - removed filtering based on RSSI value
                        print(f"RSSI: {rssi} dBm ({'Good' if rssi_flag else 'Low'})")
                            
                        if not battery_flag:
                            print(f"Low Battery: {battery}V")
                        else:
                            print(f"Good Battery: {battery}V")
                        
                        break


class MultiTargetObserver(BLEDriverObserver):
    """Observer that looks for multiple target MAC addresses and records results."""

    def __init__(self, ble_driver, targets: Dict[str, str], results: Dict, pending: set):
        super().__init__()
        self.ble_driver = ble_driver
        # targets: {MAC: qr_code_or_none}
        self.targets = {m.upper(): q for m, q in targets.items()}
        self.results = results
        self.pending = pending

    def on_gap_evt_adv_report(self, ble_driver, conn_handle, peer_addr, rssi, adv_type, adv_data):
        global raw_rssi, raw_battery, rssi_flag, battery_flag
        mac_address = ':'.join(f'{byte:02X}' for byte in peer_addr.addr).strip()

        if mac_address in self.pending:
            # Try parsing manufacturer_specific_data records
            battery_parsed = False
            battery = None
            for data_type, adv_payload in adv_data.records.items():
                if str(data_type) == "Types.manufacturer_specific_data":
                    # Protocol 1: Complex format
                    try:
                        if len(adv_payload) == 26 and adv_payload[-2] == 179 and adv_payload[-3] == 255:
                            battery_int = float(adv_payload[-1])
                            battery_dec = float(adv_payload[-4]) / 100
                            battery = battery_int + battery_dec
                            battery_parsed = True
                            break
                    except Exception:
                        pass

                    # Protocol 2: Simple format
                    try:
                        if len(adv_payload) >= 2 and not battery_parsed:
                            battery = float(adv_payload[-1]) / 10
                            battery_parsed = True
                            break
                    except Exception:
                        pass

            # Record result if parsed
            if battery_parsed and battery is not None:
                # Build result entry
                qr = self.targets.get(mac_address)
                voltage_v = battery
                voltage_mv = int(voltage_v * 1000)

                # Evaluate battery
                try:
                    from battery_evaluator import CR2032BatteryEvaluator
                    evaluator = CR2032BatteryEvaluator()
                    eval_res = evaluator.evaluate_battery(voltage_mv)
                    category = eval_res['category']
                    status = eval_res['status']
                    percentage = eval_res['percentage_estimate']
                    pass_fail = eval_res['pass_fail']
                except Exception:
                    category = 'UNKNOWN'
                    status = 'UNKNOWN'
                    percentage = None
                    pass_fail = False

                # Record timestamp (UTC)
                timestamp = datetime.now(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                comment = f"RSSI {rssi} | Battery {voltage_v}V"

                entry = {
                    'qr_or_mac': qr or mac_address,
                    'voltage_v': voltage_v,
                    'voltage_mv': voltage_mv,
                    'category': category,
                    'status': status,
                    'percentage_estimate': percentage,
                    'pass_fail': pass_fail,
                    'rssi': rssi,
                    'comment': comment,
                    'timestamp': timestamp,
                    'elapsed_s': None
                }

                # Save into shared results and mark processed
                self.results[mac_address] = entry
                try:
                    # Send events now that we have data
                    failure_code = 'ALL-PASS-000' if pass_fail else 'ALL-FAIL-000'
                    if qr:
                        databaseUpdate(qr, comment)
                        ManufEvent(qr, failure_code, entry)
                except Exception as e:
                    print(f"Error sending events for {mac_address}: {e}")

                # Remove from pending set
                try:
                    self.pending.remove(mac_address)
                except KeyError:
                    pass


# New helper: run a single multi-target scan session for a given timeout (seconds)
def run_multi_scan(targets: Dict[str, str], timeout_s: int) -> Dict[str, Dict]:
    """Run a concurrent scan for all targets and return results dict.

    Uses MultiTargetObserver to collect results. Returns dict mapping MAC->entry.
    """
    results: Dict[str, Dict] = {}
    pending = set(targets.keys())
    ble_driver = None
    try:
        ble_driver = initialize_driver_multi(get_com_port(), targets, results, pending)
        start = perf_counter()
        deadline = time.time() + timeout_s
        last_print = 0
        total = len(targets)
        while pending and time.time() < deadline:
            now = time.time()
            if now - last_print > 5:
                processed = total - len(pending)
                print(f"Processing batch: {processed}/{total} units complete")
                print(f"Remaining MACs: {len(pending)}")
                last_print = now
            time.sleep(0.5)
        elapsed = perf_counter() - start
    except Exception as e:
        print(f"Error during multi scan: {e}")
        elapsed = 0
    finally:
        if ble_driver:
            try:
                ble_driver.close()
            except Exception as e:
                print(f"Error closing driver: {e}")

    # Return results and pending set (pending will contain MACs not found)
    return results, pending, elapsed


def save_double_results(results_list: List[Dict], json_path: str, csv_path: str, metrics: Dict):
    """Save double-scan results (pre/post) to JSON and CSV."""
    try:
        p = Path(json_path).parent
        p.mkdir(parents=True, exist_ok=True)

        with open(json_path, 'w', encoding='utf-8') as jf:
            out = {'metrics': metrics, 'results': results_list}
            json.dump(out, jf, indent=2)

        # CSV fields for pre/post
        csv_fields = [
            'macid', 'qr',
            'pre_voltage_mv', 'pre_status', 'pre_rssi', 'pre_timestamp',
            'post_voltage_mv', 'post_status', 'post_rssi', 'post_timestamp',
            'delta_voltage_mv', 'final_status'
        ]

        with open(csv_path, 'w', newline='', encoding='utf-8') as cf:
            writer = csv.DictWriter(cf, fieldnames=csv_fields)
            writer.writeheader()
            for r in results_list:
                row = {
                    'macid': r.get('macid'),
                    'qr': r.get('qr'),
                    'pre_voltage_mv': r.get('pre_test', {}).get('voltage_mv'),
                    'pre_status': r.get('pre_test', {}).get('status'),
                    'pre_rssi': r.get('pre_test', {}).get('rssi'),
                    'pre_timestamp': r.get('pre_test', {}).get('timestamp'),
                    'post_voltage_mv': r.get('post_test', {}).get('voltage_mv'),
                    'post_status': r.get('post_test', {}).get('status'),
                    'post_rssi': r.get('post_test', {}).get('rssi'),
                    'post_timestamp': r.get('post_test', {}).get('timestamp'),
                    'delta_voltage_mv': r.get('delta_voltage'),
                    'final_status': r.get('final_status')
                }
                writer.writerow(row)

        print(f"Saved JSON results to {json_path}")
        print(f"Saved CSV results to {csv_path}")
    except Exception as e:
        print(f"Error saving double results: {e}")


def perform_double_scan(mac_list: List[str], scan_time: int):
    """Perform pre-test and post-test scans for a batch of MACs.

    Returns a list of combined result records.
    """
    # Resolve all entries to MACs first
    targets: Dict[str, str] = {}
    unresolved = []
    for entry in mac_list:
        if ':' in entry or len(entry) == 12:
            targets[entry.upper()] = None
        else:
            qrcode = entry
            try:
                resp = requests.get(f'{QRMAC_ENDPOINT}?qrCode={qrcode}')
                if resp.status_code == 200:
                    data = resp.json()
                    mac_address = data.get('macAddress', '')
                    if mac_address:
                        targets[mac_address.upper()] = qrcode
                    else:
                        print(f"MAC not found for QR: {qrcode}")
                        unresolved.append(qrcode)
                else:
                    print(f"Failed to resolve QR {qrcode}: {resp.status_code}")
                    unresolved.append(qrcode)
            except Exception as e:
                print(f"Error resolving QR {qrcode}: {e}")
                unresolved.append(qrcode)

    if not targets:
        print("No MACs to scan after resolving QR codes")
        return

    total = len(targets)
    print(f"Starting pre-test scan for {total} units")

    # Pre-test
    pre_results, pending_pre, elapsed_pre = run_multi_scan(targets, scan_time)

    # Build pre-test summary and print lines
    pre_records = {}
    for mac, qr in targets.items():
        rec = pre_results.get(mac)
        if rec:
            pre_voltage_mv = rec.get('voltage_mv')
            pre_rssi = rec.get('rssi')
            pre_status = 'PASS' if rec.get('pass_fail') else 'FAIL'
            pre_timestamp = rec.get('timestamp')
        else:
            pre_voltage_mv = None
            pre_rssi = None
            pre_status = 'FAIL'
            pre_timestamp = None

        pre_records[mac] = {
            'voltage_mv': pre_voltage_mv,
            'rssi': pre_rssi,
            'status': pre_status,
            'timestamp': pre_timestamp
        }

        if pre_voltage_mv is not None:
            print(f"[PRE-TEST] {mac} -> {pre_voltage_mv} mV, {pre_status}")
        else:
            print(f"[PRE-TEST] {mac} -> No data, {pre_status}")

    # Operator confirmation for post-test
    if config.POST_TEST_ENABLED:
        print("Pre-test complete. Place units in chamber. Press ENTER when ready for post-test.")
        input()

    # Post-test
    print(f"Starting post-test scan for {total} units")
    post_results, pending_post, elapsed_post = run_multi_scan(targets, scan_time)

    # Combine results
    combined = []
    pass_count = 0
    fail_count = 0

    for mac, qr in targets.items():
        pre = pre_records.get(mac, {})
        post_rec = post_results.get(mac)
        if post_rec:
            post_voltage_mv = post_rec.get('voltage_mv')
            post_rssi = post_rec.get('rssi')
            post_status = 'PASS' if post_rec.get('pass_fail') else 'FAIL'
            post_timestamp = post_rec.get('timestamp')
        else:
            post_voltage_mv = None
            post_rssi = None
            post_status = 'FAIL'
            post_timestamp = None

        # Delta: post - pre (mV)
        delta = None
        if pre.get('voltage_mv') is not None and post_voltage_mv is not None:
            delta = post_voltage_mv - pre.get('voltage_mv')
        elif pre.get('voltage_mv') is None and post_voltage_mv is not None:
            delta = 0
        elif pre.get('voltage_mv') is not None and post_voltage_mv is None:
            delta = -pre.get('voltage_mv')

        # Determine final status
        final_status = 'PASS'
        if post_status != 'PASS':
            final_status = 'FAIL'
        if delta is not None and (pre.get('voltage_mv') is not None) and (pre.get('voltage_mv') - post_voltage_mv > config.DELTA_VOLTAGE_FAIL):
            final_status = 'FAIL'

        if final_status == 'PASS':
            pass_count += 1
        else:
            fail_count += 1

        # Print post-test line with delta
        if post_voltage_mv is not None:
            delta_display = f" (Δ {delta} mV)" if delta is not None else ""
            print(f"[POST-TEST] {mac} -> {post_voltage_mv} mV, {post_status}{delta_display}")
        else:
            print(f"[POST-TEST] {mac} -> No data, {post_status}")

        combined_entry = {
            'macid': mac,
            'qr': qr,
            'pre_test': {
                'voltage_mv': pre.get('voltage_mv'),
                'rssi': pre.get('rssi'),
                'status': pre.get('status'),
                'timestamp': pre.get('timestamp')
            },
            'post_test': {
                'voltage_mv': post_voltage_mv,
                'rssi': post_rssi,
                'status': post_status,
                'timestamp': post_timestamp
            },
            'delta_voltage': delta,
            'final_status': final_status
        }
        combined.append(combined_entry)

    # Summary
    print('\nSUMMARY:')
    print(f"Total Units: {total}")
    print(f"Pass: {pass_count}")
    print(f"Fail: {fail_count}")

    metrics = {
        'total': total,
        'processed': total,
        'passed': pass_count,
        'failed': fail_count,
        'elapsed_pre_s': elapsed_pre,
        'elapsed_post_s': elapsed_post
    }

    # Save results
    save_double_results(combined, config.OUTPUT_JSON_FILE, config.OUTPUT_CSV_FILE, metrics)

    return combined


def initialize_driver(serial_port, formatted_mac, qrcode):
    """Initialize BLE driver with universal observer"""
    if not serial_port:
        serial_port = get_com_port()
    print(f"Initializing driver on port: {serial_port}")
    
    ble_driver = BLEDriver(serial_port=serial_port, baud_rate=1000000)
    observer = UniversalBLEScanObserver(ble_driver, formatted_mac, qrcode)
    
    ble_driver.observer_register(observer)
    ble_driver.open()
    ble_driver.ble_enable(None)

    scan_params = BLEGapScanParams(interval_ms=100, window_ms=50, timeout_s=30)
    ble_driver.ble_gap_scan_start(scan_params)
    return ble_driver


def initialize_driver_multi(serial_port, targets: Dict[str, str], results: Dict, pending: set):
    """Initialize BLE driver and register a MultiTargetObserver for a set of MACs."""
    if not serial_port:
        serial_port = get_com_port()
    print(f"Initializing driver on port: {serial_port} for batch scan")
    ble_driver = BLEDriver(serial_port=serial_port, baud_rate=1000000)
    observer = MultiTargetObserver(ble_driver, targets, results, pending)
    ble_driver.observer_register(observer)
    ble_driver.open()
    ble_driver.ble_enable(None)

    scan_params = BLEGapScanParams(interval_ms=100, window_ms=50, timeout_s=0)
    # start scan with no internal timeout (we control timeout externally)
    ble_driver.ble_gap_scan_start(scan_params)
    return ble_driver


def BLE_scanning(formatted_mac, qrcode):
    """Perform BLE scanning for specified device"""
    ble_driver = None
    try:
        print(f"Starting BLE scan for: {formatted_mac}")
        ble_driver = initialize_driver(get_com_port(), formatted_mac, qrcode)
        # Fixed scan duration handled elsewhere; keep short sleep here if needed
        print("Scanning for 30 seconds...")
        time.sleep(30)  # Legacy path
        return True
    except Exception as e:
        print(f"Error during BLE scan: {e}")
        return False
    finally:
        if ble_driver:
            try:
                ble_driver.close()
                print("Driver closed correctly")
            except Exception as e:
                print(f"Error closing driver: {e}")


def StationCheck(qrcode):
    """Check previous station status - simplified, no differences by type"""
    MPS_flag = False
    Current_flag = False
    
    try:
        now = datetime.now(dt_timezone.utc)
        resp = requests.get(f'http://20.97.201.175:6699/getManufEvents?input={qrcode}')
        check_resp = json.loads(resp.text)

        ideal_current_idx = 0
        for idx, row in enumerate(check_resp):
            if 'BLE Functionality' in row['stationName']:
                ideal_current_idx = ideal_current_idx + 1
                continue
                
            endTime = datetime.strptime(row['endTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
            endTime = endTime.replace(tzinfo=dt_timezone.utc)
            time_diff = now - endTime

            if timedelta(hours=0) <= time_diff <= timedelta(hours=72):
                # Look for previous test stations, no distinction by type
                if 'Current/Power Testing' in row['stationName'] and 'pass' in row['failureDescription']:
                    Current_flag = True
                if 'MPS Testing' in row['stationName'] and 'pass' in row['failureDescription']:
                    MPS_flag = True

    except Exception as e:
        print(f"Error checking previous stations: {e}")
        return False, False
    
    return MPS_flag, Current_flag


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


def load_qr_codes(file_path: str) -> List[str]:
    """Load QR codes or MACs from a text/CSV file.

    - Accepts one QR/MAC per line or a CSV file where the first column is the QR/MAC.
    - Normalizes values (strips whitespace, uppercases MACs) and removes duplicates.
    - Returns up to MAX_QR_BATCH entries.
    """
    entries = []
    seen = set()
    try:
        p = Path(file_path)
        if not p.exists():
            print(f"Input file not found: {file_path}")
            return []

        # Try reading as CSV first
        with p.open('r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                # If CSV-like, take first token
                if ',' in line:
                    token = line.split(',')[0].strip()
                else:
                    token = line
                token_norm = token.upper()
                if token_norm not in seen:
                    seen.add(token_norm)
                    entries.append(token_norm)
                if len(entries) >= config.MAX_QR_BATCH:
                    break
    except Exception as e:
        print(f"Error loading QR codes from file: {e}")
        return []

    return entries


def save_results_batch(results: List[Dict], json_path: str, csv_path: str, metrics: Dict):
    """Save aggregated results to JSON and CSV and include metrics in JSON - Optimized for large datasets."""
    try:
        # Ensure directory exists
        p = Path(json_path).parent
        p.mkdir(parents=True, exist_ok=True)

        print(f"Saving {len(results)} results to files...")
        
        # Write JSON with optimization for large files
        with open(json_path, 'w', encoding='utf-8') as jf:
            out = {'metrics': metrics, 'results': results}
            # Use separators to reduce file size and disable indentation for large datasets
            if len(results) > 1000:
                json.dump(out, jf, separators=(',', ':'), ensure_ascii=False)
            else:
                json.dump(out, jf, indent=2, ensure_ascii=False)

        # Write CSV with buffering for large datasets
        csv_fields = ['qr_or_mac', 'voltage_v', 'voltage_mv', 'category', 'status', 'percentage_estimate', 'pass_fail', 'rssi', 'comment', 'timestamp']
        with open(csv_path, 'w', newline='', encoding='utf-8', buffering=8192) as cf:  # 8KB buffer for large files
            writer = csv.DictWriter(cf, fieldnames=csv_fields)
            writer.writeheader()
            
            # Process in chunks to avoid memory issues
            chunk_size = 1000
            for i in range(0, len(results), chunk_size):
                chunk = results[i:i + chunk_size]
                for r in chunk:
                    row = {
                        'qr_or_mac': r.get('qr_or_mac'),
                        'voltage_v': r.get('voltage_v'),
                        'voltage_mv': r.get('voltage_mv'),
                        'category': r.get('category'),
                        'status': r.get('status'),
                        'percentage_estimate': r.get('percentage_estimate'),
                        'pass_fail': r.get('pass_fail'),
                        'rssi': r.get('rssi'),
                        'comment': r.get('comment'),
                        'timestamp': r.get('timestamp')
                    }
                    writer.writerow(row)
                
                # Progress indication for large datasets
                if len(results) > 1000 and (i + chunk_size) % 14000 == 0:
                    print(f"Saved {min(i + chunk_size, len(results))}/{len(results)} records...")

        print(f"Successfully saved {len(results)} results:")
        print(f"  JSON: {json_path}")
        print(f"  CSV: {csv_path}")
    except Exception as e:
        print(f"Error saving results: {e}")


def process_single_device(formatted_mac: str, qrcode: str) -> Dict:
    """Process a single MAC: perform BLE scan until device is found or timeout.

    Returns a dict with result data for aggregation.
    """
    global raw_rssi, raw_battery, rssi_flag, battery_flag

    # Reset per device
    raw_rssi = ""
    raw_battery = ""
    rssi_flag = False
    battery_flag = False

    start_time = perf_counter()
    found = False
    device_result = {
        'qr_or_mac': qrcode or formatted_mac,
        'voltage_v': None,
        'voltage_mv': None,
        'category': None,
        'status': None,
        'percentage_estimate': None,
        'pass_fail': False,
        'rssi': None,
        'comment': ''
    }

    try:
        # Use auto-detected port by default
        ble_driver = initialize_driver(None, formatted_mac, qrcode)
        scan_deadline = time.time() + config.SCAN_TIMEOUT

        # Poll until timeout or until raw_battery is set by observer
        while time.time() < scan_deadline and not raw_battery:
            time.sleep(0.2)

        if raw_battery:
            found = True
            device_result['rssi'] = raw_rssi
            device_result['voltage_v'] = raw_battery
            device_result['voltage_mv'] = int(raw_battery * 1000)

            # Evaluate battery using battery_evaluator module
            try:
                from battery_evaluator import CR2032BatteryEvaluator
                evaluator = CR2032BatteryEvaluator()
                eval_result = evaluator.evaluate_battery(device_result['voltage_mv'])
                device_result.update({
                    'category': eval_result['category'],
                    'status': eval_result['status'],
                    'percentage_estimate': eval_result['percentage_estimate'],
                    'pass_fail': eval_result['pass_fail']
                })
            except Exception:
                # Fallback simple evaluation
                device_result['category'] = 'UNKNOWN'

            device_result['comment'] = f"RSSI {device_result.get('rssi')} | Battery {device_result.get('voltage_v')}V"

            # Send events
            failure_code = 'ALL-PASS-000' if device_result['pass_fail'] else 'ALL-FAIL-000'
            try:
                databaseUpdate(qrcode, device_result['comment'])
                ManufEvent(qrcode, failure_code, device_result)
            except Exception as e:
                print(f"Error sending events: {e}")
        else:
            device_result['comment'] = 'No data obtained'
            ManufEvent(qrcode, 'SCAN-FAIL-001', 'No data obtained')
    except Exception as e:
        device_result['comment'] = f'Error during scan: {e}'
        print(f"Error processing device {formatted_mac}: {e}")
    finally:
        try:
            if ble_driver:
                ble_driver.close()
        except Exception:
            pass

    device_result['elapsed_s'] = perf_counter() - start_time
    return device_result


def process_mac_list(mac_list: List[str]):
    """Process a list of MACs (or QR codes) as a batch using a single concurrent scan.

    Steps:
    1) Resolve QR -> MAC for all QR entries
    2) Build targets dict {MAC: QR}
    3) Start single BLE driver and observe advertising for all MACs
    4) Wait until all MACs processed (no operator input)
    5) Close driver, send failure events for not-found devices, save results
    Returns a tuple: (results_list, metrics_dict)
    """
    # Resolve all entries to MACs first
    targets: Dict[str, str] = {}
    unresolved = []
    for entry in mac_list:
        if ':' in entry or len(entry) == 12:
            targets[entry.upper()] = None
        else:
            qrcode = entry
            try:
                resp = requests.get(f'{QRMAC_ENDPOINT}?qrCode={qrcode}')
                if resp.status_code == 200:
                    data = resp.json()
                    mac_address = data.get('macAddress', '')
                    if mac_address:
                        targets[mac_address.upper()] = qrcode
                    else:
                        print(f"MAC not found for QR: {qrcode}")
                        unresolved.append(qrcode)
                else:
                    print(f"Failed to resolve QR {qrcode}: {resp.status_code}")
                    unresolved.append(qrcode)
            except Exception as e:
                print(f"Error resolving QR {qrcode}: {e}")
                unresolved.append(qrcode)

    if not targets:
        print("No MACs to scan after resolving QR codes")
        return [], {'total': 0, 'processed': 0, 'failed': 0, 'elapsed_s': 0}

    # Prepare shared results store and pending set
    results: Dict[str, Dict] = {}
    pending = set(targets.keys())
    total = len(targets)
    print(f"Starting batch scan for {total} MACs")

    # Initialize driver once for all targets
    ble_driver = None
    try:
        ble_driver = initialize_driver_multi(get_com_port(), targets, results, pending)

        start_time = perf_counter()
        
        # No overall timeout: process until all devices are found
        print("Batch processing without timeout. Waiting for all devices to report...")
        # Progress reporting and periodic checkpoints
        last_print = 0
        print_interval = 10 if total > 1000 else 5
        checkpoint_interval = max(100, total // 50)
        last_checkpoint = 0
        while pending:
            now = time.time()
            processed_count = total - len(pending)
            # Save periodic checkpoints for large batches
            if total > 500 and processed_count > 0 and (processed_count - last_checkpoint) >= checkpoint_interval:
                try:
                    partial_results = list(results.values())
                    if partial_results:
                        checkpoint_metrics = {
                            'total': total,
                            'processed': processed_count,
                            'failed': len(pending),
                            'elapsed_s': now - start_time,
                            'checkpoint': True,
                            'timestamp': datetime.now(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                        }
                        checkpoint_json = config.OUTPUT_JSON_FILE.replace('.json', '_checkpoint.json')
                        checkpoint_csv = config.OUTPUT_CSV_FILE.replace('.csv', '_checkpoint.csv')
                        save_results_batch(partial_results, checkpoint_json, checkpoint_csv, checkpoint_metrics)
                        print(f"Checkpoint saved: {processed_count}/{total} devices")
                        last_checkpoint = processed_count
                except Exception as e:
                    print(f"Warning: Checkpoint save failed: {e}")
            # Regular progress reporting
            if now - last_print > print_interval:
                elapsed_so_far = now - start_time
                progress_pct = (processed_count / total) * 100
                print(f"Processing: {processed_count}/{total} ({progress_pct:.1f}%) - Elapsed: {elapsed_so_far:.1f}s")
                print(f"Remaining devices: {len(pending)}")
                last_print = now
            time.sleep(0.5)
        elapsed = perf_counter() - start_time
    except Exception as e:
        print(f"Error during batch scan: {e}")
    finally:
        # Stop scanning and close driver
        if ble_driver:
            try:
                ble_driver.close()
            except Exception as e:
                print(f"Error closing driver: {e}")

    # For any remaining pending MACs, mark as failed and optionally send events
    for mac in list(pending):
        qr = targets.get(mac)
        entry = {
            'qr_or_mac': qr or mac,
            'voltage_v': None,
            'voltage_mv': None,
            'category': 'NO_DATA',
            'status': 'FAIL',
            'percentage_estimate': 0,
            'pass_fail': False,
            'rssi': None,
            'comment': 'No data obtained'
        }
        results[mac] = entry
        try:
            if qr:
                ManufEvent(qr, 'SCAN-FAIL-001', 'No data obtained')
        except Exception as e:
            print(f"Error sending failure event for {mac}: {e}")

    # Build results list from results dict in input order
    results_list = []
    for mac, qr in targets.items():
        rec = results.get(mac)
        if not rec:
            rec = {
                'qr_or_mac': qr or mac,
                'voltage_v': None,
                'voltage_mv': None,
                'category': 'NO_DATA',
                'status': 'FAIL',
                'percentage_estimate': 0,
                'pass_fail': False,
                'rssi': None,
                'comment': 'No data obtained'
            }
        results_list.append(rec)

    metrics = {
        'total': total,
        'processed': total - len(pending),
        'failed': len(pending),
        'elapsed_s': elapsed
    }

    # Save aggregated results
    save_results_batch(results_list, config.OUTPUT_JSON_FILE, config.OUTPUT_CSV_FILE, metrics)

    # Final report
    print('\nBatch processing complete')
    print(f"Total: {metrics['total']}")
    print(f"Processed: {metrics['processed']}")
    print(f"Failed: {metrics['failed']}")
    print(f"Elapsed (s): {metrics['elapsed_s']:.2f}")

    return results_list, metrics


class DiscoveryObserver(BLEDriverObserver):
    """Observer for discovering nearby BLE devices"""
    def __init__(self, ble_driver, min_rssi_threshold=-200):
        super().__init__()
        self.ble_driver = ble_driver
        self.discovered_devices = {}
        self.last_print_time = 0
        self.min_rssi_threshold = min_rssi_threshold

    def on_gap_evt_adv_report(self, ble_driver, conn_handle, peer_addr, rssi, adv_type, adv_data):
        if rssi < self.min_rssi_threshold:
            return
        mac_address = ':'.join(f'{byte:02X}' for byte in peer_addr.addr).strip()
        if mac_address in self.discovered_devices:
            return
        device_info = {
            'mac': mac_address,
            'rssi': rssi,
            'name': 'Unknown',
            'has_battery_data': False,
            'battery_voltage': None
        }
        for data_type, adv_payload in adv_data.records.items():
            data_type_str = str(data_type)
            if "complete_local_name" in data_type_str or "shortened_local_name" in data_type_str:
                try:
                    device_info['name'] = bytes(adv_payload).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
            elif "manufacturer_specific_data" in data_type_str:
                device_info['has_battery_data'] = True
                try:
                    if len(adv_payload) == 26 and adv_payload[-2] == 179 and adv_payload[-3] == 255:
                        battery_int = float(adv_payload[-1])
                        battery_dec = float(adv_payload[-4]) / 100
                        device_info['battery_voltage'] = battery_int + battery_dec
                    elif len(adv_payload) >= 2:
                        device_info['battery_voltage'] = float(adv_payload[-1]) / 10
                except Exception:
                    pass
        self.discovered_devices[mac_address] = device_info
        current_time = time.time()
        if current_time - self.last_print_time > 2:
            print(f"Discovered {len(self.discovered_devices)} devices so far...")
            self.last_print_time = current_time


def discover_nearby_devices(scan_duration: int = 15, scan_all_rssi: bool = True) -> List[str]:
    """Discover nearby BLE devices and return a list of MACs (process ALL automatically)."""
    rssi_threshold = -200 if scan_all_rssi else config.RSSI_THRESHOLD
    print(f"Scanning for {scan_duration} seconds for ALL BLE devices (no RSSI filter)...")
    ble_driver = None
    try:
        port = get_com_port()
        ble_driver = BLEDriver(serial_port=port, baud_rate=1000000)
        observer = DiscoveryObserver(ble_driver, min_rssi_threshold=rssi_threshold)
        ble_driver.observer_register(observer)
        ble_driver.open()
        ble_driver.ble_enable(None)
        scan_params = BLEGapScanParams(interval_ms=100, window_ms=50, timeout_s=0)
        ble_driver.ble_gap_scan_start(scan_params)
        start_time = time.time()
        while time.time() - start_time < scan_duration:
            time.sleep(0.5)
        discovered_devices = observer.discovered_devices
        if not discovered_devices:
            print("No BLE devices found")
            return []
        sorted_devices = sorted(discovered_devices.items(), key=lambda x: x[1]['rssi'], reverse=True)
        print(f"Discovered {len(sorted_devices)} BLE devices (processing ALL)...")
        return [mac for mac, _ in sorted_devices]
    except Exception as e:
        print(f"Error during device discovery: {e}")
        return []
    finally:
        if ble_driver:
            try:
                ble_driver.close()
            except Exception as e:
                print(f"Error closing discovery driver: {e}")


# Update main to be fully automatic (Windows-only pipeline)
def main():
    """Automatic scanner: discover for fixed time and process all devices (no operator input)."""
    init()  # Initialize colorama
    setup_logging()
    print("BLE Universal Scanner - Automatic Mode")
    print("=" * 60)
    try:
        # Ensure COM port is auto-detected (raises if not found)
        port = get_com_port()
        # Fixed discovery duration from config
        DISCOVERY_SECONDS = config.SCAN_TIME
        run_id = f"BATCH-{uuid.uuid4()}"
        run_start = datetime.now(dt_timezone.utc)
        mac_list = discover_nearby_devices(scan_duration=DISCOVERY_SECONDS, scan_all_rssi=True)
        if not mac_list:
            print("No devices discovered. Exiting.")
            return
        print(f"Discovered {len(mac_list)} devices. Starting batch processing...")
        # Process all discovered devices with no overall timeout
        if config.POST_TEST_ENABLED:
            # If a pre/post flow is ever enabled, use SCAN_TIME for each phase
            perform_double_scan(mac_list, config.SCAN_TIME)
            # No summary for double-scan path yet
            print("Double-scan path executed; summary not sent.")
        else:
            results_list, metrics = process_mac_list(mac_list)
            run_end = datetime.now(dt_timezone.utc)
            try:
                # Send batch summary as ALL-PASS-000 per user preference
                status = send_batch_summary(
                    metrics=metrics,
                    csv_path=config.OUTPUT_CSV_FILE,
                    run_start=run_start,
                    run_end=run_end,
                    run_id=run_id,
                    app_version="",
                    driver_version=""
                )
                if status:
                    print(f"Posted batch summary event (HTTP {status})")
                else:
                    print("Failed to post batch summary event")
            except Exception as e:
                print(f"Error sending batch summary: {e}")
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        print("Scanner finished")


if __name__ == "__main__":
    main()
