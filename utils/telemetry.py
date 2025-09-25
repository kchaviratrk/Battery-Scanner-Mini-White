"""
Telemetry and centralization utilities for BLE scanner results.
- Loads station/operator from .env
- Posts per-device and batch summary events to manufacturing API
- Builds safe notes content (bounded to varchar(8000))
"""
from __future__ import annotations

import json
import os
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timezone

import requests

# Lazy import to avoid hard dependency at import time
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # type: ignore

MANUF_API_URL = os.getenv("MANUF_API_URL", "http://20.97.201.175:6699/postManufEvent")


def load_env() -> Dict[str, str]:
    """Load .env and return relevant settings."""
    if load_dotenv is not None:
        try:
            load_dotenv()
        except Exception:
            pass
    return {
        "station_id": os.getenv("STATION_ID", "269"),
        "operator_id": os.getenv("OPERATOR_ID", "Pilot"),
        "api_url": os.getenv("MANUF_API_URL", MANUF_API_URL),
    }


def format_ts(dt: datetime) -> str:
    """Format datetime as 'YYYY-MM-DD HH:MM:SS.fff' in UTC (no timezone suffix)."""
    dt_utc = dt.astimezone(timezone.utc)
    # Milliseconds precision
    return dt_utc.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


# Retained helper (unused now) in case future needs arise
def _read_csv_head(csv_path: str, max_lines: int = 80) -> str:
    try:
        p = Path(csv_path)
        if not p.exists():
            return ""
        lines = []
        with p.open("r", encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh):
                lines.append(line.rstrip("\n"))
                if i + 1 >= max_lines:
                    break
        return "\n".join(lines)
    except Exception:
        return ""


def _sha256_file(path: str) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def post_manuf_event(curr_qr: str, failure_code: str, start_time: datetime, end_time: datetime, notes: str,
                     station_id: str, operator_id: str, api_url: Optional[str] = None) -> Optional[int]:
    """Post a manufacturing event using form-encoded params. Returns HTTP status or None on exception."""
    url = api_url or MANUF_API_URL
    params = {
        'currQr': curr_qr,
        'stationID': station_id,
        'operatorID': operator_id,
        'failureCode': failure_code,
        'startTime': format_ts(start_time),
        'endTime': format_ts(end_time),
        'notes': notes,
    }
    try:
        resp = requests.post(url, data=params, timeout=10)
        return resp.status_code
    except Exception:
        return None


def build_summary_notes(metrics: Dict, csv_path: str, run_id: str, app_version: str = "", driver_version: str = "") -> str:
    """Build minimal compact JSON notes (no CSV snippet)."""
    sha = _sha256_file(csv_path)
    base = {
        'run_id': run_id,
        'totals': metrics,
        'csv_path': csv_path,
        'csv_sha256': sha,
        'app_version': app_version,
        'driver_version': driver_version,
        'tz': 'UTC'
    }
    notes = json.dumps(base, separators=(',', ':'))
    # Keep a hard limit just in case
    if len(notes) > 7900:
        notes = notes[:7900] + '...'
    return notes


def send_batch_summary(metrics: Dict, csv_path: str, run_start: datetime, run_end: datetime, run_id: str,
                        app_version: str = "", driver_version: str = "") -> Optional[int]:
    env = load_env()
    notes = build_summary_notes(metrics, csv_path, run_id, app_version, driver_version)
    # Summary desired as ALL-PASS-000 regardless of failures per user preference
    status = post_manuf_event(
        curr_qr=run_id,
        failure_code='ALL-PASS-000',
        start_time=run_start,
        end_time=run_end,
        notes=notes,
        station_id=env['station_id'],
        operator_id=env['operator_id'],
        api_url=env['api_url']
    )
    return status


def send_batch_csv_details(csv_path: str, run_id: str, max_notes_len: int = 7900, lines_per_event_hint: int = 120, *, per_row: bool = False) -> int:
    """Send CSV content to the DB as manufacturing events.
    Modes:
    - per_row=False (default): send in parts with many rows per event (failureCode='BATCH-DETAIL-000').
    - per_row=True: send one event per device row (failureCode='BATCH-ROW-000'), currQr set to the first CSV column (qr_or_mac).
    Returns count of events posted (best-effort).
    """
    env = load_env()
    p = Path(csv_path)
    if not p.exists():
        return 0

    try:
        lines: List[str] = p.read_text(encoding='utf-8', errors='ignore').splitlines()
    except Exception:
        return 0

    if not lines:
        return 0

    header = lines[0]
    rows = lines[1:]

    parts_posted = 0
    now = datetime.now(timezone.utc)

    if per_row:
        # One event per row; notes = single CSV row; currQr = first column token; failureCode from pass_fail
        for i, row in enumerate(rows, start=1):
            # Split into max 10 fields to avoid breaking if comment contains commas
            fields = row.split(',', 9)
            # Extract first column (qr_or_mac)
            curr_qr = fields[0].strip() if fields and fields[0].strip() else f"{run_id}-ROW-{i:05d}"
            # Determine failure code from pass_fail column (index 6)
            failure_code = 'ALL-PASS-000'
            if len(fields) > 6:
                pf_raw = fields[6].strip().lower()
                if pf_raw in ('false', '0', 'no'):
                    failure_code = 'ALL-FAIL-000'
                else:
                    failure_code = 'ALL-PASS-000'
            # Notes only the CSV row
            notes = row[:max_notes_len]
            post_manuf_event(
                curr_qr=curr_qr,
                failure_code=failure_code,
                start_time=now,
                end_time=now,
                notes=notes,
                station_id=env['station_id'],
                operator_id=env['operator_id'],
                api_url=env['api_url']
            )
            parts_posted += 1
        return parts_posted

    # Default: chunked parts with header + many rows per event
    idx = 0
    part = 1
    while idx < len(rows):
        chunk: List[str] = []
        content_lines = [header]
        while idx < len(rows):
            tentative = content_lines + chunk + [rows[idx]]
            notes = "\n".join(tentative)
            if len(notes) > max_notes_len:
                break
            chunk.append(rows[idx])
            idx += 1
            if len(chunk) >= lines_per_event_hint:
                break
        notes = "\n".join(content_lines + chunk)
        curr_qr = f"{run_id}-PART-{part:02d}"
        post_manuf_event(
            curr_qr=curr_qr,
            failure_code='BATCH-DETAIL-000',
            start_time=now,
            end_time=now,
            notes=notes,
            station_id=env['station_id'],
            operator_id=env['operator_id'],
            api_url=env['api_url']
        )
        parts_posted += 1
        part += 1

    return parts_posted
