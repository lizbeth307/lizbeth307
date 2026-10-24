#!/usr/bin/env python3
"""Opt-in network snapshot of LCSC availability for every LCSC SKU in design/parts/parts.json.

Usage (needs Internet; never part of the offline host regression):
  python tools/check_parts_availability.py --date 2026-10-24

Queries the public JLCPCB parts search (no API key) by the stored LCSC C-code, keeps only the
exact C-code hit and writes design/parts/snapshots/<date>-lcsc.json with manufacturer, MPN,
package, distributor description and attributes, stock, price ladder (USD) and JLC library class.
The offline checker (tools/build_parts.py --check) compares the database against the newest
snapshot and only warns when it is older than the age limit. A snapshot is a dated reading,
not a reservation: stock and prices change daily.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
LIB = {'base': 'basic', 'expand': 'extended'}


def query(code):
    body = json.dumps({'keyword': code, 'currentPage': 1, 'pageSize': 10}).encode()
    req = urllib.request.Request(API, data=body, headers={'Content-Type': 'application/json', 'User-Agent': 'sr-rx-parts-snapshot'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read().decode('utf-8', 'replace'))
            break
        except OSError:
            if attempt == 2:
                raise
            time.sleep(3)
    for c in ((data.get('data') or {}).get('componentPageInfo') or {}).get('list') or []:
        if c.get('componentCode') == code:
            return c
    return None


def record(c):
    lib = LIB.get(c.get('componentLibraryType'), c.get('componentLibraryType'))
    if c.get('preferredComponentFlag'):
        lib = 'preferred'
    return {
        'mpn': c.get('componentModelEn'), 'manufacturer': c.get('componentBrandEn'),
        'package': c.get('componentSpecificationEn'), 'description': c.get('describe'),
        'attributes': {a['attribute_name_en']: a['attribute_value_name'] for a in c.get('attributes') or []
                       if a.get('attribute_value_name') not in (None, '', '-')},
        'stock': c.get('stockCount'), 'jlc_library': lib,
        'price_usd': [[p['startNumber'], p['productPrice']] for p in c.get('componentPrices') or []],
        'url': c.get('lcscGoodsUrl'), 'datasheet': c.get('dataManualUrl'),
    }


def codes(db):
    out = set()
    for p in db['parts']:
        for entry in [p] + p.get('alternates', []) + p.get('extras', []):
            sku = (entry.get('sku') or {}).get('lcsc')
            if sku:
                out.add(sku)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--date', required=True, help='snapshot date YYYY-MM-DD (file name)')
    ap.add_argument('--db', type=Path, default=ROOT / 'design/parts/parts.json')
    args = ap.parse_args()
    db = json.loads(args.db.read_text(encoding='utf-8'))
    entries, missing = {}, []
    for code in codes(db):
        c = query(code)
        if c is None:
            missing.append(code)
            continue
        entries[code] = dict(record(c), fetched_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
        time.sleep(0.4)
    snap = {'schema': 1, 'date': args.date, 'distributor': 'LCSC',
            'source': 'JLCPCB parts search ' + API + ' queried by exact LCSC C-code (no API key)',
            'tool': 'tools/check_parts_availability.py', 'not_found': missing, 'entries': entries}
    out = ROOT / f'design/parts/snapshots/{args.date}-lcsc.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(entries)} LCSC SKUs written to {out.relative_to(ROOT).as_posix()}; not found: {missing}')
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
