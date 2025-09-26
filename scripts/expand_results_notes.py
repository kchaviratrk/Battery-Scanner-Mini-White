#!/usr/bin/env python3
"""Expand 'notes' rows into explicit columns and enrich with qrcode from two SQL Server sources.

Sources:
  1) External:   [flexport].[qrmac_db]   (env: EXTERNAL_SERVER, EXTERNAL_DATABASE, EXTERNAL_SERVER_USER, EXTERNAL_SERVER_PASS)
  2) Internal:   [trk].[qrmac_db]        (env: MFG_SERVER,      INTERNAL_DATABASE,  MFG_SERVER_USER,      MFG_SERVER_PASS)

If a MAC is found in external it is used; missing ones then queried in internal.
Output always includes a qrcode column (fallback: 'no encontrado en la base de datos el QR').
"""
from __future__ import annotations
import csv
import argparse
from pathlib import Path
import os
import re
import sys
from typing import List, Dict, Optional, Iterable, Tuple, Set

# dotenv optional
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    def load_dotenv(*_, **__):
        return False

# pyodbc optional
try:
    import pyodbc  # type: ignore
except ImportError:  # pragma: no cover
    pyodbc = None  # type: ignore

EXPECTED_DEVICE_FIELDS = 10
DEVICE_FIELD_NAMES = [
    'MAC','BATTERY_VOLTAGE_MV','BATTERY_VOLTAGE_V','STATUS','CONDITION','BATTERY_LEVEL',
    'CONNECTED','RSSI','INFO','TIMESTAMP'
]
BASE_FIELD_NAMES = ['stationID','failureCode','startTime']
OUTPUT_FIELD_NAMES = BASE_FIELD_NAMES + DEVICE_FIELD_NAMES + ['qrcode']
ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / '.env'

FALLBACK_QR = 'no encontrado en la base de datos el QR'


def load_env():
    if ENV_PATH.exists():
        try:
            load_dotenv(dotenv_path=ENV_PATH, override=False)
        except Exception as e:  # pragma: no cover
            print(f'Advertencia: error cargando .env: {e}', file=sys.stderr)
    # manual fallback (lines not loaded)
    if ENV_PATH.exists():
        try:
            for line in ENV_PATH.read_text(encoding='utf-8').splitlines():
                if not line or line.lstrip().startswith('#') or '=' not in line:
                    continue
                k,v = line.split('=',1)
                k=k.strip(); v=v.strip()
                if k and v and os.getenv(k) is None:
                    os.environ[k]=v
        except Exception as e:  # pragma: no cover
            print(f'Advertencia: fallback .env fallo: {e}', file=sys.stderr)

def normalize_mac(value: str) -> str:
    return re.sub(r'[^0-9A-Fa-f]', '', value or '').upper()


def expand_notes_row(row: Dict[str,str], include_json: bool) -> Optional[List[str]]:
    notes = (row.get('notes','') or '').strip().strip('"')
    if not notes:
        return None
    if notes.startswith('{'):
        if include_json:
            return [row['stationID'], row['failureCode'], row['startTime']] + [''] * EXPECTED_DEVICE_FIELDS
        return None
    parts = notes.split(',')
    if len(parts) != EXPECTED_DEVICE_FIELDS:
        return None
    return [row['stationID'], row['failureCode'], row['startTime']] + parts


def load_rows(input_path: Path, include_json: bool) -> List[List[str]]:
    out: List[List[str]] = []
    with input_path.open('r', encoding='utf-8', newline='') as fin:
        reader = csv.DictReader(fin)
        for r in reader:
            exp = expand_notes_row(r, include_json)
            if exp:
                out.append(exp)
    return out


def _detect_driver() -> str:
    if pyodbc is None:
        return ''
    drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
    if any('ODBC Driver 18' in d for d in drivers):
        return '{ODBC Driver 18 for SQL Server}'
    return '{' + (drivers[-1] if drivers else 'ODBC Driver 18 for SQL Server') + '}'


def query_source(name: str, server: str, database: str, user: str, password: str,
                 schema: str, table: str, macs: Iterable[str], chunk_size: int) -> Dict[str,str]:
    mapping: Dict[str,str] = {}
    if pyodbc is None:
        print(f'Advertencia: pyodbc no disponible; omitiendo fuente {name}', file=sys.stderr)
        return mapping
    driver = _detect_driver()
    conn_str = (
        f'Driver={driver};Server=tcp:{server},1433;Database={database};Uid={user};Pwd={password};'
        'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    )
    mac_list = list(macs)
    if not mac_list:
        return mapping
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            # Smoke test quick
            try:
                cur.execute(f'SELECT TOP 1 qrcode, macid FROM [{schema}].[{table}]')
                cur.fetchall()
            except Exception as e:
                print(f'Error verificación tabla {schema}.{table} ({name}): {e}', file=sys.stderr)
                return mapping
            for i in range(0, len(mac_list), chunk_size):
                chunk = mac_list[i:i+chunk_size]
                placeholders = ','.join(['?']*len(chunk))
                sql = f'SELECT qrcode, macid FROM [{schema}].[{table}] WHERE macid IN ({placeholders})'
                if i == 0:
                    print(f'DEBUG {name}: batch {len(chunk)} (total {len(mac_list)})', file=sys.stderr)
                cur.execute(sql, chunk)
                for qrcode, macid in cur.fetchall():
                    norm = normalize_mac(str(macid))
                    if norm and norm not in mapping and qrcode:
                        mapping[norm] = str(qrcode).strip()
    except Exception as e:
        print(f'Error consultando {name}: {e}', file=sys.stderr)
    return mapping


# MODIFIED: add internal_only & external_only parameters AND return remaining + mac_norms
def enrich(rows: List[List[str]], chunk_size: int, internal_only: bool=False, external_only: bool=False) -> Tuple[Dict[str,str], Set[str], Dict[str,str]]:
    load_env()
    mac_norms: Dict[str,str] = {}
    for r in rows:
        if len(r) >= 4 and r[3].strip():
            norm = normalize_mac(r[3])
            if norm:
                mac_norms.setdefault(norm, r[3].upper())
    all_norms = set(mac_norms.keys())
    print(f'INFO: MACs únicos a resolver: {len(all_norms)}', file=sys.stderr)
    ext_server = os.getenv('EXTERNAL_SERVER')
    ext_db = os.getenv('EXTERNAL_DATABASE')
    ext_user = os.getenv('EXTERNAL_SERVER_USER')
    ext_pass = os.getenv('EXTERNAL_SERVER_PASS')
    int_server = os.getenv('MFG_SERVER')
    int_db = os.getenv('INTERNAL_DATABASE') or os.getenv('TRACEABILITY_DATABASE')
    int_user = os.getenv('MFG_SERVER_USER')
    int_pass = os.getenv('MFG_SERVER_PASS')
    mapping: Dict[str,str] = {}
    if not internal_only:
        if all([ext_server, ext_db, ext_user, ext_pass]):
            mapping.update(query_source('EXTERNAL', ext_server, ext_db, ext_user, ext_pass,
                                        'flexport','qrmac_db', all_norms, chunk_size))
        else:
            print('Advertencia: Credenciales externas incompletas.', file=sys.stderr)
    remaining = all_norms - set(mapping.keys())
    print(f'INFO: Tras externa faltan {len(remaining)} MACs', file=sys.stderr)
    if not external_only:
        if remaining and all([int_server, int_db, int_user, int_pass]):
            mapping_internal = query_source('INTERNAL', int_server, int_db, int_user, int_pass,
                                            'trk','qrmac_db', remaining if not internal_only else all_norms, chunk_size)
            still = (remaining if not internal_only else all_norms) - set(mapping_internal.keys())
            if still:
                colon_forms = [mac_norms[n] for n in still if n in mac_norms]
                colon_plain = [normalize_mac(c) for c in colon_forms]
                second_try_set = set(colon_plain) - set(mapping_internal.keys())
                if second_try_set:
                    mapping_internal.update(query_source('INTERNAL2', int_server, int_db, int_user, int_pass,
                                                         'trk','qrmac_db', second_try_set, chunk_size))
            for k,v in mapping_internal.items():
                mapping.setdefault(k,v)
        else:
            if remaining and not internal_only:
                print('Advertencia: Credenciales internas incompletas.', file=sys.stderr)
    final_remaining = all_norms - set(mapping.keys())
    print(f'INFO: Total encontrados={len(mapping)} no_encontrados={len(final_remaining)}', file=sys.stderr)
    if final_remaining:
        sample = list(final_remaining)[:10]
        print(f'INFO: Ejemplo faltantes {sample}', file=sys.stderr)
    return mapping, final_remaining, mac_norms


# NEW: fuzzy lookup for remaining MACs using suffix patterns in internal first then external
def fuzzy_lookup(mapping: Dict[str,str], remaining: Set[str], mac_norms: Dict[str,str], chunk_size: int):
    if not remaining:
        return
    if pyodbc is None:
        print('INFO: Fuzzy lookup omitido (pyodbc no disponible)', file=sys.stderr)
        return
    ext_server = os.getenv('EXTERNAL_SERVER')
    ext_db = os.getenv('EXTERNAL_DATABASE')
    ext_user = os.getenv('EXTERNAL_SERVER_USER')
    ext_pass = os.getenv('EXTERNAL_SERVER_PASS')
    int_server = os.getenv('MFG_SERVER')
    int_db = os.getenv('INTERNAL_DATABASE') or os.getenv('TRACEABILITY_DATABASE')
    int_user = os.getenv('MFG_SERVER_USER')
    int_pass = os.getenv('MFG_SERVER_PASS')
    driver = _detect_driver()
    def _conn(s, db, u, p):
        return pyodbc.connect(f'Driver={driver};Server=tcp:{s},1433;Database={db};Uid={u};Pwd={p};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
    # Build ordered list of suffix strategies
    strategies = [6,8]
    def run_fuzzy(name, server, db, user, pwd, schema, table):
        if not all([server, db, user, pwd]):
            return
        try:
            with _conn(server, db, user, pwd) as conn:
                cur = conn.cursor()
                try:
                    cur.execute(f'SELECT TOP 1 qrcode, macid FROM [{schema}].[{table}]')
                    cur.fetchall()
                except Exception as e:
                    print(f'Fuzzy verificación falla {name}: {e}', file=sys.stderr)
                    return
                to_try = list(remaining - set(mapping.keys()))
                print(f'FUZZY {name}: intentando {len(to_try)} MACs', file=sys.stderr)
                for norm in to_try:
                    orig = mac_norms.get(norm, norm)
                    # Skip if already found during loop
                    if norm in mapping:
                        continue
                    for size in strategies:
                        if len(norm) < size:
                            continue
                        suffix = norm[-size:]
                        pattern = f'%{suffix}'
                        sql = f"SELECT TOP 1 qrcode, macid FROM [{schema}].[{table}] WHERE REPLACE(macid,':','') LIKE ? OR macid LIKE ?"
                        try:
                            cur.execute(sql, pattern, pattern)
                            row = cur.fetchone()
                            if row:
                                qrcode, macid = row
                                n2 = normalize_mac(str(macid))
                                if n2 and n2 not in mapping:
                                    mapping[n2] = str(qrcode).strip()
                                    print(f'FUZZY {name}: {orig} -> {qrcode} (sufijo {suffix})', file=sys.stderr)
                                    break
                        except Exception as e:
                            print(f'FUZZY error {name} {orig}: {e}', file=sys.stderr)
        except Exception as e:
            print(f'FUZZY conexión falla {name}: {e}', file=sys.stderr)
    # Internal first, then external
    run_fuzzy('INTERNAL_FUZZY', int_server, int_db, int_user, int_pass, 'trk','qrmac_db')
    run_fuzzy('EXTERNAL_FUZZY', ext_server, ext_db, ext_user, ext_pass, 'flexport','qrmac_db')
    print(f'FUZZY completo. Nuevos hallados: {len(mapping)}', file=sys.stderr)


def apply_mapping(rows: List[List[str]], mapping: Dict[str,str]) -> List[List[str]]:
    out: List[List[str]] = []
    for r in rows:
        mac = r[3] if len(r)>=4 else ''
        norm = normalize_mac(mac)
        qrcode = mapping.get(norm, FALLBACK_QR)
        out.append(r + [qrcode])
    return out


def write_output(rows: List[List[str]], output_path: Path):
    with output_path.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(OUTPUT_FIELD_NAMES)
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description='Expand notes and enrich with qrcode from two DB sources.')
    ap.add_argument('--input','-i', default='results/Results.csv')
    ap.add_argument('--output','-o', default='results/Results_extendent.csv')
    ap.add_argument('--include-json', action='store_true')
    ap.add_argument('--chunk-size', type=int, default=400)
    ap.add_argument('--no-db', action='store_true')
    ap.add_argument('--internal-only', action='store_true', help='Consultar solo la base interna (trk)')
    ap.add_argument('--external-only', action='store_true', help='Consultar solo la base externa (flexport)')
    ap.add_argument('--fuzzy', action='store_true', help='Activar búsqueda fuzzy para MACs faltantes (sufijos)')
    ap.add_argument('--export-missing', help='Ruta CSV para exportar MACs sin qrcode tras proceso')
    args = ap.parse_args()

    if args.internal_only and args.external_only:
        print('Error: use solo --internal-only o --external-only, no ambos.', file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = load_rows(input_path, include_json=args.include_json)

    if args.no_db:
        enriched = [r + [''] for r in rows]
    else:
        mapping, remaining_set, mac_norms = enrich(rows, chunk_size=args.chunk_size, internal_only=args.internal_only, external_only=args.external_only)
        if args.fuzzy and remaining_set:
            fuzzy_lookup(mapping, remaining_set, mac_norms, args.chunk_size)
            # recompute remaining after fuzzy
            remaining_set = (set(mac_norms.keys()) - set(mapping.keys()))
        enriched = apply_mapping(rows, mapping)
        if args.export_missing:
            miss_path = Path(args.export_missing)
            miss_path.parent.mkdir(parents=True, exist_ok=True)
            with miss_path.open('w', encoding='utf-8', newline='') as fmiss:
                w = csv.writer(fmiss)
                w.writerow(['original_mac','normalized_mac'])
                for norm in sorted(remaining_set):
                    w.writerow([mac_norms.get(norm, norm), norm])
            print(f'Exportados {len(remaining_set)} MACs faltantes a {miss_path}', file=sys.stderr)

    write_output(enriched, output_path)
    print(f'Wrote {len(enriched)} rows to {output_path} (con qrcode).')

if __name__ == '__main__':
    main()
