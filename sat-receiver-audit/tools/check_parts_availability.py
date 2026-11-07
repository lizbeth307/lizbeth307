#!/usr/bin/env python3
"""Opt-in network snapshot of LCSC availability for every LCSC SKU in design/parts/parts.json.

Usage (needs Internet; never part of the offline host regression):
  python tools/check_parts_availability.py --date 2026-10-24
  python tools/check_parts_availability.py --date 2026-11-08 --codes C55266,C111738 \\
      --out design/parts/snapshots/2026-11-08-w2-reads-e-lcsc.json

Queries the public JLCPCB parts search (no API key) by the stored LCSC C-code, keeps only the
exact C-code hit and writes design/parts/snapshots/<date>-lcsc.json with manufacturer, MPN,
package, distributor description and attributes, stock, price ladder (USD) and JLC library class.
The offline checker (tools/build_parts.py --check) compares the database against the newest
snapshot and only warns when it is older than the age limit. A snapshot is a dated reading,
not a reservation: stock and prices change daily.

Partial snapshot (--codes together with --out): reads only the listed C-codes, whether or not
parts.json already names them, and writes them with the same row schema and distributor 'LCSC'
(plus scope 'partial' and requested_codes) to design/parts/snapshots/<date>-w2-<package>-lcsc.json.
That name is enforced, its date must equal --date (YYYY-MM-DD), and --out resolves against the
current directory, so it works from the project or the repository root. tools/build_parts.py takes
LCSC SKUs only from snapshots whose distributor is 'LCSC' and loads the parts.json 'snapshots' list
in order, a later row replacing an earlier one, so one later full re-read (no --codes) supersedes
every partial snapshot. Append the file to 'snapshots' yourself: this tool never edits the database.
Without --codes the run is the full re-read described above, unchanged.
"""
from __future__ import annotations
import argparse
import datetime
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
LIB = {'base': 'basic', 'expand': 'extended'}
# A partial snapshot never takes the full re-read's name <date>-lcsc.json; one file per wave-2 package.
PARTIAL_NAME = re.compile(r'design/parts/snapshots/(\d{4}-\d{2}-\d{2})-w2-([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)-lcsc\.json')
LCSC_CODE = re.compile(r'C[0-9]+')
PAUSE_S = 0.4


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
    entries = []
    for p in db['parts']:
        entries += [p] + p.get('alternates', []) + p.get('extras', [])
    for fam in db.get('harness_families', []):
        entries += [fam['terminal']] if fam.get('terminal') else []
        entries += [size[role] for size in fam.get('sizes', []) for role in ('header_top', 'header_side', 'housing') if role in size]
    for entry in entries:
        sku = (entry.get('sku') or {}).get('lcsc')
        if sku:
            out.add(sku)
    return sorted(out)


def utc_now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def read_codes(wanted):
    """Snapshot rows of the codes the search returns as an exact hit, and the codes it does not."""
    entries, missing = {}, []
    for code in wanted:
        c = query(code)
        if c is None:
            missing.append(code)
            continue
        entries[code] = dict(record(c), fetched_utc=utc_now())
        time.sleep(PAUSE_S)
    return entries, missing


def requested_codes(text):
    """--codes C1,C2,...: exact LCSC C-codes as parts.json stores them; sorted, duplicates dropped."""
    items = [c.strip() for c in text.split(',')]
    bad = [c for c in items if not LCSC_CODE.fullmatch(c)]
    if bad:
        raise ValueError(f'not an LCSC C-code: {bad}')
    return sorted(set(items))


def partial_target(out, date):
    """The resolved --out path, or the reason it is refused: it must be inside this project at
    design/parts/snapshots/<date>-w2-<package>-lcsc.json, with the date of --date."""
    try:
        if datetime.date.fromisoformat(date).isoformat() != date:
            raise ValueError(date)
    except ValueError:
        return None, f'--date {date!r} is not YYYY-MM-DD (build_parts.py parses it with date.fromisoformat)'
    path = (Path.cwd() / out).resolve()
    try:
        rel = path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None, f'--out {out} is outside {ROOT}'
    m = PARTIAL_NAME.fullmatch(rel)
    if not m:
        return None, f'--out {rel} must be design/parts/snapshots/<YYYY-MM-DD>-w2-<package>-lcsc.json'
    if m[1] != date:
        return None, f'--out {rel} is dated {m[1]}, not --date {date}'
    return ROOT / rel, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--date', required=True, help='snapshot date YYYY-MM-DD (file name)')
    ap.add_argument('--db', type=Path, default=ROOT / 'design/parts/parts.json')
    ap.add_argument('--codes', help='partial snapshot: comma-separated LCSC C-codes to read (needs --out)')
    ap.add_argument('--out', help='partial snapshot file design/parts/snapshots/<date>-w2-<package>-lcsc.json (needs --codes)')
    args = ap.parse_args(argv)
    if (args.codes is None) != (args.out is None):
        ap.error('--codes and --out go together: a partial snapshot never takes the full re-read name <date>-lcsc.json')
    db = json.loads(args.db.read_text(encoding='utf-8'))
    if args.codes is None:
        wanted, out = codes(db), ROOT / f'design/parts/snapshots/{args.date}-lcsc.json'
    else:
        try:
            wanted = requested_codes(args.codes)
        except ValueError as e:
            ap.error(f'--codes: {e}')
        out, reason = partial_target(args.out, args.date)
        if reason:
            ap.error(reason)
    entries, missing = read_codes(wanted)
    snap = {'schema': 1, 'date': args.date, 'distributor': 'LCSC',
            'source': 'JLCPCB parts search ' + API + ' queried by exact LCSC C-code (no API key)',
            'tool': 'tools/check_parts_availability.py', 'not_found': missing, 'entries': entries}
    if args.codes is not None:
        snap.update(scope='partial', requested_codes=wanted)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(entries)} LCSC SKUs written to {out.relative_to(ROOT).as_posix()}; not found: {missing}')
    if args.codes is not None:
        unlisted = sorted(set(wanted) - set(codes(db)))
        if unlisted:
            print(f'not yet named by any {args.db.name} entry: {unlisted}')
        print(f"partial snapshot: append it to the 'snapshots' list of {args.db.name}, then run tools/build_parts.py")
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
