#!/usr/bin/env python3
"""Parts database checker and generator (stdlib only, offline).

  python tools/build_parts.py           # write graph part fields, footprint manifest, BOM outputs
  python tools/build_parts.py --check   # fail if the database is inconsistent or an output is stale

Source of truth: design/parts/parts.json (one entry per orderable part or non-purchased role,
every schematic reference exactly once) plus the dated distributor snapshots it names.
Outputs written from it:
  design/E1..E5.json        footprint / mpn / manufacturer / lcsc fields of each component
  build/kicad/footprints/manifest.json, build/kicad/fp-lib-table
  build/10-zakupivlia.csv, build/10-zakupivlia.md   consolidated v2.1 purchase BOM
  build/10-jlc-bom.csv                              JLC assembly BOM per board (LCSC parts)
  build/10-parts-coverage.json                      coverage counts and open items
Nothing here measures hardware: an orderable MPN is a procurement fact, not a qualification.
"""
from __future__ import annotations
import argparse
import collections
import csv
import datetime
import hashlib
import importlib.util
import io
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'design/parts/parts.json'
LIBDIR = ROOT / 'build/kicad/footprints'
KICAD_TAG = '10.0.7'
PCB_MOUNTS = ('pcb_smt', 'pcb_tht', 'pcb_pad', 'pcb_module')
BUY_MOUNTS = ('pcb_smt', 'pcb_tht', 'pcb_module', 'module', 'panel', 'harness', 'remote', 'rework')
MOUNTS = PCB_MOUNTS + ('module', 'panel', 'harness', 'remote', 'rework', 'on_module', 'existing', 'assembly', 'virtual')
PASSIVE = ('resistor', 'capacitor', 'inductor')
BOARD3 = {'PWR_MAIN': 'POWER', 'PWR_BRANCH': 'POWER', 'USB_POWER': 'POWER', 'RF_HMC': 'RF', 'RF_HF': 'RF', 'RF_INJECTOR': 'RF', 'DC_CORE': 'RF', 'CTRL_HMI': 'CTRL'}
SHEET_BOARD = {'E1': 'POWER', 'E2': 'POWER', 'E3': 'CTRL', 'E4': 'RF', 'E5': 'POWER'}
SECTIONS = [('pcb_smt', 'Плати: SMD (збирання JLC PCBA)'), ('pcb_tht', 'Плати: THT (ручне паяння або THT-збирання)'),
            ('pcb_module', 'Модулі, що паяються на плату'), ('module', 'Готові модулі й вузли'), ('panel', 'Панель'),
            ('harness', 'Кабелі та джгути'), ('remote', 'Виносні деталі'), ('rework', 'Переробка готових плат'), ('extra', 'Супутні деталі')]

# ------------------------------------------------------------------------------------------- values
NUM = r'(\d+(?:\.\d+)?)'
FREE = r'(?<![A-Za-z0-9.])'
UNIT_R = {'mΩ': 1e-3, 'mR': 1e-3, 'Ω': 1, 'Ohm': 1, 'ohm': 1, 'R': 1, 'k': 1e3, 'K': 1e3, 'kΩ': 1e3, 'M': 1e6, 'MΩ': 1e6, '': 1}
UNIT_C = {'p': 1e-12, 'pF': 1e-12, 'n': 1e-9, 'nF': 1e-9, 'u': 1e-6, 'uF': 1e-6, 'µ': 1e-6, 'µF': 1e-6, 'μF': 1e-6}
UNIT_L = {'nH': 1e-9, 'uH': 1e-6, 'µH': 1e-6, 'μH': 1e-6, 'mH': 1e-3}


def _core(value):
    """A gated start value 'RILIM TBD (start 56.2k 1%)' is checked as its start value."""
    m = re.search(r'\bstart\s+([^)]*)\)', value)
    return m.group(1) if m else value


def resistance(value):
    m = re.search(FREE + NUM + r'\s*(mΩ|mR|kΩ|MΩ|Ω|Ohm|ohm|R(?![a-zA-Z])|k|K|M(?![a-zA-Z]))?(?=[\s%\d≥(Ω]|$|[A-Za-z])', _core(value))
    return float(m.group(1)) * UNIT_R[m.group(2) or ''] if m else None


def tolerance(value):
    m = re.search(NUM + r'\s*%', _core(value))
    return float(m.group(1)) if m else None


def power_w(value):
    m = re.search(NUM + r'\s*W(?![A-Za-z])', value)
    return float(m.group(1)) if m else None


def tcr_ppm(value):
    m = re.search(NUM + r'\s*ppm', value)
    return float(m.group(1)) if m else None


def package(value):
    m = re.search(r'(?<![0-9A-Za-z])(0402|0603|0805|1206|1210|1812|2512)(?![0-9])', value)
    return m.group(1) if m else None


def capacitance(value):
    m = re.search(FREE + NUM + r'\s*(pF|nF|µF|μF|uF|p|n|u|µ)(?![A-Za-z])', value) or re.search(FREE + NUM + r'\s*(pF|nF|µF|μF|uF)', value)
    return float(m.group(1)) * UNIT_C[m.group(2)] if m else None


def voltage(value):
    for m in re.finditer(NUM + r'\s*V(?!\d)', value):
        prev = value[m.start(1) - 1] if m.start(1) else ' '
        if (prev.isalpha() and prev != 'F') or prev.isdigit() or prev == '.':
            continue
        return float(m.group(1))
    return None


def dielectric(value):
    m = re.search(r'(C0G|NP0|X7R|X5R|X7S|X6S)', value)
    return {'NP0': 'C0G'}.get(m.group(1), m.group(1)) if m else None


def inductance(value):
    m = re.search(FREE + NUM + r'\s*(nH|uH|µH|μH|mH)', value)
    return float(m.group(1)) * UNIT_L[m.group(2)] if m else None


SI = {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'µ': 1e-6, 'μ': 1e-6, 'm': 1e-3, '': 1, 'k': 1e3, 'K': 1e3, 'M': 1e6}


def si(text, unit):
    if not text:
        return None
    t = text.replace(' ', '')
    m = re.match(r'^(\d+(?:\.\d+)?)([pnuµμmkKM]?)' + unit, t)
    if m:
        return float(m.group(1)) * SI[m.group(2)]
    m = re.match(r'^(\d+)/(\d+)' + unit, t)
    return float(m.group(1)) / float(m.group(2)) if m else None


def close(a, b):
    return a is not None and b is not None and abs(a - b) <= 1e-6 * max(abs(a), abs(b))


def requirement_problems(kind, value, attrs, deviation=None):
    """Compare a graph value with the attributes a distributor shows for the chosen part."""
    out = []
    pct = lambda t: float(re.search(NUM, t).group(1)) if t and re.search(NUM, t) else None
    if kind == 'resistor':
        need = resistance(value)
        got = si(attrs.get('Resistance'), 'Ω')
        if need is None or not close(need, got):
            out.append(f'resistance {need} != {got}')
        tol, got_tol = tolerance(value), pct(attrs.get('Tolerance'))
        allowed = (deviation or {}).get('tolerance_pct', tol if tol is not None else 5)
        if got_tol is None or got_tol > allowed + 1e-9:
            out.append(f'tolerance {got_tol}% > {allowed}%')
        w, got_w = power_w(value), si(attrs.get('Power(Watts)'), 'W')
        if w and (got_w is None or got_w + 1e-9 < w):
            out.append(f'power {got_w} W < {w} W')
        tcr, got_tcr = tcr_ppm(value), pct(attrs.get('Temperature Coefficient'))
        if tcr and (got_tcr is None or got_tcr > tcr):
            out.append(f'TCR {got_tcr} > {tcr} ppm')
    elif kind == 'capacitor':
        need, got = capacitance(value), si(attrs.get('Capacitance'), 'F')
        if need is None or not close(need, got):
            out.append(f'capacitance {need} != {got}')
        v, got_v = voltage(value), si(attrs.get('Voltage Rating'), 'V')
        if v and (got_v is None or got_v < v):
            out.append(f'voltage {got_v} < {v}')
        d = dielectric(value)
        got_d = {'NP0': 'C0G', 'NPO': 'C0G'}.get(attrs.get('Temperature Coefficient'), attrs.get('Temperature Coefficient'))
        if d and got_d != d:
            out.append(f'dielectric {got_d} != {d}')
    elif kind == 'inductor':
        need, got = inductance(value), si(attrs.get('Inductance'), 'H')
        if need is None or not close(need, got):
            out.append(f'inductance {need} != {got}')
    return out


def norm_mpn(s):
    """Distributors drop spaces, dashes and leading zeros differently (43650-0315 = 436500315)."""
    return re.sub(r'[\s\-]+', '', s or '').upper().lstrip('0')


# ------------------------------------------------------------------------------------------- loading
def load_graphs():
    graphs = []
    for i in range(1, 6):
        path = ROOT / f'design/E{i}.json'
        graphs.append((path, json.loads(path.read_text(encoding='utf-8'))))
    return graphs


def load_snapshots(db):
    lcsc, manual, dates = {}, {}, []
    for rel in db['snapshots']:
        snap = json.loads((ROOT / rel).read_text(encoding='utf-8'))
        dates.append(snap['date'])
        if snap.get('distributor') == 'LCSC':
            lcsc.update(snap['entries'])
        else:
            manual.update(snap['entries'])
    return lcsc, manual, dates


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pads_of(path):
    return sorted({p for p in re.findall(r'\(pad\s+"([^"]*)"', path.read_text(encoding='utf-8')) if p})


def sort_ref(s):
    m = re.fullmatch(r'([^0-9]+)([0-9]+)', s)
    return (m[1], int(m[2])) if m else (s, 0)


def prepare_module():
    spec = importlib.util.spec_from_file_location('sr_rx_pcb_prepare', ROOT / 'pcb/prepare.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------------------------------- core
class Model:
    def __init__(self):
        self.db = json.loads(DB_PATH.read_text(encoding='utf-8'))
        self.graphs = load_graphs()
        self.lcsc, self.manual, self.snapshot_dates = load_snapshots(self.db)
        self.comps = {}
        for path, g in self.graphs:
            for c in g['components']:
                self.comps[c['ref']] = (g['sheet'], c)
        self.part_of = {}
        self.errors, self.warnings = [], []

    def err(self, msg):
        self.errors.append(msg)

    def lcsc_rec(self, entry):
        code = (entry.get('sku') or {}).get('lcsc')
        return self.lcsc.get(code) if code else None

    def sku_known(self, entry):
        sku = entry.get('sku') or {}
        hits = []
        for dist, key in sku.items():
            if dist == 'lcsc':
                rec = self.lcsc.get(key)
            else:
                rec = self.manual.get(f'{dist}:{key}')
            if rec is None:
                self.err(f'{entry.get("mpn") or entry.get("id")}: {dist} SKU {key} has no snapshot entry')
                continue
            if rec.get('mpn') and entry.get('mpn') and norm_mpn(rec['mpn']) != norm_mpn(entry['mpn']):
                self.err(f'{entry.get("mpn")}: {dist} {key} snapshot shows MPN {rec["mpn"]}')
            hits.append((dist, rec))
        return hits

    def check(self):
        parts = self.db['parts']
        ids = [p['id'] for p in parts]
        for dup in [i for i, n in collections.Counter(ids).items() if n > 1]:
            self.err(f'duplicate part id {dup}')
        manifest_fps = {f'{d.stem}:{f.stem}' for d in LIBDIR.glob('*.pretty') for f in d.glob('*.kicad_mod')}
        for p in parts:
            if p['mount'] not in MOUNTS:
                self.err(f'{p["id"]}: unknown mount {p["mount"]}')
            for ref in p['refs']:
                if ref in self.part_of:
                    self.err(f'{ref} assigned twice ({self.part_of[ref]["id"]}, {p["id"]})')
                self.part_of[ref] = p
                if ref not in self.comps:
                    self.err(f'{p["id"]}: unknown ref {ref}')
            self.check_part(p, manifest_fps)
        for ref in sorted(set(self.comps) - set(self.part_of), key=sort_ref):
            self.err(f'{ref} has no parts-database entry')
        newest = max(self.snapshot_dates)
        age = (datetime.date.today() - datetime.date.fromisoformat(newest)).days
        if age > self.db['policy']['snapshot_max_age_days']:
            self.warnings.append(f'newest availability snapshot is {age} days old ({newest}); run tools/check_parts_availability.py')

    def check_part(self, p, manifest_fps):
        mount, fp = p['mount'], p.get('footprint')
        refs = [r for r in p['refs'] if r in self.comps]
        if mount in PCB_MOUNTS:
            if not fp:
                self.err(f'{p["id"]}: board mount {mount} without footprint')
            elif fp not in manifest_fps:
                self.err(f'{p["id"]}: footprint {fp} is not in build/kicad/footprints')
            else:
                lib, name = fp.split(':', 1)
                pads = set(pads_of(LIBDIR / f'{lib}.pretty' / f'{name}.kicad_mod'))
                for ref in refs:
                    missing = sorted({str(x['number']) for x in self.comps[ref][1]['pins']} - pads)
                    if missing:
                        self.err(f'{ref}: pins {missing} have no pad in {fp}')
        elif fp and fp not in manifest_fps:
            self.err(f'{p["id"]}: footprint {fp} is not vendored')
        if p.get('polarized'):
            for ref in refs:
                pin = next((x for x in self.comps[ref][1]['pins'] if str(x['number']) in ('1', '+')), None)
                if pin is None or pin.get('net') == 'GND':
                    self.err(f'{ref}: polarized part with pin 1/+ on GND')
        buy = mount in BUY_MOUNTS and any(not self.comps[r][1].get('dnp') for r in refs)
        if buy and not p.get('tbd'):
            if not (p.get('mpn') and p.get('manufacturer')):
                self.err(f'{p["id"]}: purchased part needs mpn and manufacturer (or tbd with a reason)')
            if not p.get('sku') and not p.get('source'):
                self.err(f'{p["id"]}: purchased part needs a distributor SKU read in a snapshot, a source, or tbd')
            if not p.get('alternates') and not p.get('single_source'):
                self.err(f'{p["id"]}: needs an alternate or a single_source reason')
        if p.get('tbd') and not isinstance(p['tbd'], str):
            self.err(f'{p["id"]}: tbd must be a reason text')
        hits = self.sku_known(p)
        for alt in p.get('alternates', []):
            self.sku_known(alt)
        for ex in p.get('extras', []):
            self.sku_known(ex)
            if not ex.get('qty_per_ref'):
                self.err(f'{p["id"]}: extra {ex.get("mpn")} needs qty_per_ref')
        kind = p.get('kind')
        if kind in PASSIVE and not p.get('tbd'):
            checked = 0
            for entry in [p] + p.get('alternates', []):
                rec = self.lcsc_rec(entry)
                if rec is None:
                    continue
                checked += 1
                if p.get('package') and rec.get('package') != p['package']:
                    self.err(f'{p["id"]}: {entry["mpn"]} LCSC package {rec.get("package")} != {p["package"]}')
                for ref in refs:
                    for problem in requirement_problems(kind, self.comps[ref][1]['value'], rec.get('attributes', {}), p.get('deviation')):
                        self.err(f'{ref} {self.comps[ref][1]["value"]!r} vs {entry["mpn"]}: {problem}')
            if not checked and kind != 'inductor':
                self.warnings.append(f'{p["id"]}: no LCSC attributes to check the value against')
        elif p.get('match'):
            want = norm_mpn(p['match'])
            for ref in refs:
                if want not in norm_mpn(self.comps[ref][1]['value']):
                    self.err(f'{ref}: value {self.comps[ref][1]["value"]!r} does not contain {p["match"]!r}')
        for dist, rec in hits:
            if rec.get('stock') == 0 and not p.get('tbd'):
                self.warnings.append(f'{p["id"]}: {dist} stock 0 on the snapshot date')

    # ------------------------------------------------------------------------------- generation
    def graph_texts(self):
        out = {}
        for path, g in self.graphs:
            for c in g['components']:
                p = self.part_of.get(c['ref'])
                if p is None:
                    continue
                want = {}
                if p.get('footprint'):
                    want['footprint'] = p['footprint']
                if p['mount'] in BUY_MOUNTS and p.get('mpn') and p.get('manufacturer'):
                    want['mpn'] = p['mpn']
                    want['manufacturer'] = p['manufacturer']
                if p['mount'] in ('pcb_smt', 'pcb_tht') and (p.get('sku') or {}).get('lcsc') and not p.get('tbd'):
                    want['lcsc'] = p['sku']['lcsc']
                for key in ('footprint', 'mpn', 'manufacturer', 'lcsc'):
                    if key in want:
                        if key in c:
                            c[key] = want[key]
                        else:
                            items = list(c.items())
                            at = next((i for i, (k, _) in enumerate(items) if k == 'pins'), len(items))
                            items.insert(at, (key, want[key]))
                            c.clear(); c.update(items)
                    elif key in c and key != 'footprint':
                        del c[key]
            out[path] = json.dumps(g, ensure_ascii=False, indent=2) + '\n'
        return out

    def board_of(self, prep, ref):
        sheet, c = self.comps[ref]
        if self.part_of[ref]['mount'] not in PCB_MOUNTS:
            return ''
        if sheet == 'E4':
            return BOARD3[prep.board({**c, '_sheet': sheet}, 'bare_board_part')]
        return SHEET_BOARD[sheet]

    def manifest_text(self):
        uses = collections.defaultdict(list)
        for ref, (sheet, c) in self.comps.items():
            if c.get('footprint'):
                uses[c['footprint']].append(ref)
        prov = json.loads((LIBDIR / 'SR_RX_Custom.pretty/provenance.json').read_text(encoding='utf-8'))
        derived_sources = {v['source'].split(' ', 2)[2] for v in prov.values() if v['kind'] == 'derived'}
        rows = []
        for d in sorted(LIBDIR.glob('*.pretty')):
            for f in sorted(d.glob('*.kicad_mod')):
                ident = f'{d.stem}:{f.stem}'
                origin = (f'SR_RX_Custom {prov[f.stem]["kind"]}' if d.stem == 'SR_RX_Custom' else f'KiCad {KICAD_TAG} official, unmodified')
                refs = sorted(uses.get(ident, []), key=sort_ref)
                if not refs and ident not in derived_sources:
                    self.err(f'vendored footprint {ident} is not used')
                row = {'footprint': ident, 'file': f.relative_to(ROOT).as_posix(), 'sha256': sha(f), 'pads': pads_of(f), 'origin': origin, 'refs': refs}
                if ident in derived_sources and not refs:
                    row['role'] = 'source of a derived SR_RX_Custom footprint'
                rows.append(row)
        missing = sorted(set(uses) - {r['footprint'] for r in rows})
        for m in missing:
            self.err(f'graph footprint {m} is not vendored')
        manifest = {'kicad_version': KICAD_TAG, 'assignments': sum(len(v) for v in uses.values()), 'footprints': rows,
                    'source': 'https://gitlab.com/kicad/libraries/kicad-footprints/-/tree/' + KICAD_TAG,
                    'generator': 'tools/build_parts.py from design/parts/parts.json'}
        return json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'

    def fp_table_text(self):
        lines = ['(fp_lib_table', '  (version 7)']
        for d in sorted(LIBDIR.glob('*.pretty')):
            descr = 'SR-RX project footprints (custom and derived, see provenance.json)' if d.stem == 'SR_RX_Custom' else f'Selected official KiCad {KICAD_TAG} footprints'
            lines.append(f'  (lib (name "{d.stem}")(type "KiCad")(uri "${{KIPRJMOD}}/footprints/{d.name}")(options "")(descr "{descr}"))')
        return '\n'.join(lines + [')']) + '\n'

    def availability(self, p):
        """(state, note) from snapshots: ok / zero-stock / listed / carried / tbd / none."""
        if p.get('tbd'):
            return 'TBD', p['tbd']
        states = []
        for dist, key in (p.get('sku') or {}).items():
            rec = self.lcsc.get(key) if dist == 'lcsc' else self.manual.get(f'{dist}:{key}')
            if rec is None:
                continue
            stock = rec.get('stock')
            states.append('ok' if stock else 'zero-stock' if stock == 0 else 'listed')
        if 'ok' in states:
            return 'в наявності', ''
        if 'listed' in states:
            return 'у каталозі', 'кількість на складі не показано'
        if states:
            return 'склад 0', 'на дату знімка немає на складі'
        if p.get('source'):
            return 'з 10-bom', p['source']
        return '—', ''

    def bom(self, prep):
        pol = self.db['policy']['spares']
        rows, extras = [], []
        for p in self.db['parts']:
            if p['mount'] not in BUY_MOUNTS:
                continue
            live = [r for r in p['refs'] if not self.comps[r][1].get('dnp')]
            if not live:
                continue
            qty = len(live)
            spare = max(math.ceil(qty * pol['passive_pct'] / 100), pol['passive_min']) if p.get('kind') in PASSIVE and p['mount'] in ('pcb_smt', 'pcb_tht') else 0
            state, why = self.availability(p)
            rec = self.lcsc_rec(p)
            boards = sorted({self.board_of(prep, r) for r in live} - {''})
            rows.append({'section': p['mount'], 'part': p['id'], 'qty': qty, 'spare': spare, 'order': qty + spare, 'refs': ' '.join(sorted(live, key=sort_ref)),
                         'boards': ' '.join(boards), 'manufacturer': p.get('manufacturer', ''), 'mpn': p.get('mpn', ''), 'footprint': p.get('footprint', ''),
                         'lcsc': (p.get('sku') or {}).get('lcsc', ''), 'digikey': (p.get('sku') or {}).get('digikey', ''),
                         'other': (p.get('sku') or {}).get('web', '') or p.get('source', ''),
                         'lcsc_stock': '' if rec is None else rec.get('stock'), 'lcsc_usd': '' if rec is None else unit_price(rec, qty + spare),
                         'alternates': '; '.join(f'{a.get("manufacturer", "")} {a["mpn"]}'.strip() for a in p.get('alternates', [])),
                         'state': state, 'note': '; '.join(x for x in (why if state == 'TBD' else '', p.get('note', ''), p.get('single_source', '') and 'одне джерело: ' + p['single_source']) if x)})
            for ex in p.get('extras', []):
                rec = self.lcsc_rec(ex)
                n = ex['qty_per_ref'] * qty
                extras.append({'section': 'extra', 'part': p['id'], 'qty': n, 'spare': 0, 'order': n, 'refs': ' '.join(sorted(live, key=sort_ref)), 'boards': '',
                               'manufacturer': ex.get('manufacturer', ''), 'mpn': ex.get('mpn', ''), 'footprint': '', 'lcsc': (ex.get('sku') or {}).get('lcsc', ''),
                               'digikey': (ex.get('sku') or {}).get('digikey', ''), 'other': (ex.get('sku') or {}).get('web', ''),
                               'lcsc_stock': '' if rec is None else rec.get('stock'), 'lcsc_usd': '' if rec is None else unit_price(rec, n),
                               'alternates': '', 'state': self.availability(ex)[0] if ex.get('sku') else 'без SKU', 'note': ex.get('item', '') + ('; ' + ex['note'] if ex.get('note') else '')})
        order = {m: i for i, (m, _) in enumerate(SECTIONS)}
        rows.sort(key=lambda r: (order[r['section']], r['part']))
        return rows + extras

    def jlc_rows(self, prep):
        rows = []
        for p in self.db['parts']:
            if p['mount'] not in ('pcb_smt', 'pcb_tht') or p.get('tbd'):
                continue
            live = [r for r in p['refs'] if not self.comps[r][1].get('dnp')]
            by_board = collections.defaultdict(list)
            for r in live:
                by_board[self.board_of(prep, r)].append(r)
            for b, refs in sorted(by_board.items()):
                rows.append({'Board': b, 'Comment': p.get('mpn', ''), 'Designator': ','.join(sorted(refs, key=sort_ref)), 'Footprint': p['footprint'].split(':', 1)[1],
                             'LCSC Part #': (p.get('sku') or {}).get('lcsc', ''), 'Mount': 'SMD' if p['mount'] == 'pcb_smt' else 'THT'})
        rows.sort(key=lambda r: (r['Board'], r['Mount'], r['Comment']))
        return rows

    def coverage(self, prep):
        mounts = collections.Counter(self.part_of[r]['mount'] for r in self.comps)
        bare = [r for r, (s, c) in self.comps.items() if prep.category({**c, '_sheet': s})[0] == 'bare_board_part']
        pcb_refs = [r for r in self.comps if self.part_of[r]['mount'] in PCB_MOUNTS]
        buy_refs = [r for r in self.comps if self.part_of[r]['mount'] in BUY_MOUNTS and not self.comps[r][1].get('dnp')]
        state = collections.Counter(self.availability(self.part_of[r])[0] for r in buy_refs)
        tbd = [{'part': p['id'], 'refs': p['refs'], 'reason': p['tbd']} for p in self.db['parts'] if p.get('tbd')]
        carried = [{'part': p['id'], 'refs': p['refs'], 'source': p['source']} for p in self.db['parts'] if p.get('source') and not p.get('tbd')]
        origins = collections.Counter()
        for r in pcb_refs:
            fp = self.part_of[r].get('footprint', '')
            origins['SR_RX_Custom' if fp.startswith('SR_RX_Custom:') else f'KiCad {KICAD_TAG}'] += 1
        prov = json.loads((LIBDIR / 'SR_RX_Custom.pretty/provenance.json').read_text(encoding='utf-8'))
        return {
            'schema': 1, 'generator': 'tools/build_parts.py', 'database': 'design/parts/parts.json', 'snapshots': self.db['snapshots'],
            'refs': len(self.comps), 'parts': len(self.db['parts']), 'refs_by_mount': dict(sorted(mounts.items())),
            'bare_board_parts': len(bare), 'bare_board_parts_with_footprint': sum(bool(self.comps[r][1].get('footprint')) for r in bare),
            'board_refs': len(pcb_refs), 'board_refs_with_footprint': sum(bool(self.part_of[r].get('footprint')) for r in pcb_refs),
            'board_footprint_origin': dict(sorted(origins.items())),
            'purchased_refs': len(buy_refs), 'purchased_refs_by_availability': dict(sorted(state.items())),
            'purchased_refs_with_mpn': sum(bool(self.part_of[r].get('mpn')) for r in buy_refs),
            'tbd': tbd, 'carried_from_10_bom': carried,
            'deviations': [{'part': p['id'], 'refs': p['refs'], **p['deviation']} for p in self.db['parts'] if p.get('deviation')],
            'footprint_checks_open': [{'footprint': f'SR_RX_Custom:{k}', 'note': v.get('note') or v.get('drawing')} for k, v in sorted(prov.items())
                                      if 'verify' in json.dumps(v) or 'must be checked' in json.dumps(v)],
            'open_items': OPEN_ITEMS,
        }


OPEN_ITEMS = [
    'SW308/SW309 are the push switches inside ENC301/ENC302: the graph keeps them as separate refs, so the encoder pads S1/S2 stay unconnected in the netlist until the E3 owner moves the switch nets onto encoder pins.',
    'Board-side connectors of harnesses that have no graph ref yet (power-board end of J302, LAB BUS header behind J505, fan, buzzer-less HMI leads, NTC TH301/TH302 leads, inter-board links of the three-board split) are bought as extras where named; their schematic refs are pending (PCB/partition owner).',
    'Panel parts without MPN (SMA/F/BNC bulkheads, USB-A/USB-C feedthroughs, power and EDL buttons) wait for the IP-rating selection of the mechanics package (MECH-07).',
    'HMC7992LP3DE exposed-pad size and CPT-1207-3TH pin pitch must be checked against the manufacturer drawings before PCB release (see SR_RX_Custom/provenance.json).',
]


def unit_price(rec, qty):
    best = ''
    for start, price in rec.get('price_usd', []):
        if qty >= start:
            best = price
    return best


def csv_text(rows, fields):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator='\n', extrasaction='ignore')
    w.writeheader()
    w.writerows(rows)
    return s.getvalue()


BOM_FIELDS = ['section', 'part', 'qty', 'spare', 'order', 'refs', 'boards', 'manufacturer', 'mpn', 'footprint', 'lcsc', 'digikey', 'other', 'lcsc_stock', 'lcsc_usd', 'alternates', 'state', 'note']
BOM_HEAD = {'section': 'розділ', 'part': 'запис бази', 'qty': 'к-сть на виріб', 'spare': 'запас', 'order': 'замовити', 'refs': 'позначення', 'boards': 'плата',
            'manufacturer': 'виробник', 'mpn': 'MPN', 'footprint': 'посадкове місце', 'lcsc': 'LCSC', 'digikey': 'DigiKey DE', 'other': 'інше джерело',
            'lcsc_stock': 'склад LCSC (дата знімка)', 'lcsc_usd': 'ціна LCSC USD за шт. (дата знімка)', 'alternates': 'альтернативи', 'state': 'стан', 'note': 'примітка'}


def bom_md(model, rows, cov):
    date = max(model.snapshot_dates)
    sec = collections.OrderedDict((m, t) for m, t in SECTIONS)
    lines = ['# 10. Закупівля SR-RX-v2.1 (згенеровано з бази деталей)', '',
             f'Файл згенеровано `tools/build_parts.py` з [`design/parts/parts.json`](../design/parts/parts.json) і знімків наявності від {date}. Не редагувати вручну: зміни вносяться в базу деталей, далі `python tools/build_parts.py`.', '',
             'Це закупівельний перелік деталей схеми v2.1 (графи E1–E5) разом із супутніми деталями (тримачі запобіжників, корпуси й контакти роз’ємів, ферити). '
             'Деталі всередині готових модулів (Adafruit, Q6A) не купуються вдруге. Антени, прилади лабораторії, інструменти, корпус і кріплення лишаються в [10-bom.csv](10-bom.csv) (оцінка v2, рядки за STACK.md).',
             'Склад і ціна — показання дистриб’ютора на дату знімка, а не резерв: перед замовленням перевірити ще раз (`python tools/check_parts_availability.py --date РРРР-ММ-ДД`).', '',
             '**Апаратний випуск BLOCKED.** Наявність MPN не кваліфікує деталь: стендові ворота з OPEN_ITEMS лишаються відкритими.', '',
             '## Зведення', '',
             f'- Позначень на схемі: {cov["refs"]}; записів бази: {cov["parts"]}.',
             f'- Позначень на платах з посадковим місцем: {cov["board_refs_with_footprint"]} з {cov["board_refs"]} (KiCad {KICAD_TAG}: {cov["board_footprint_origin"].get("KiCad " + KICAD_TAG, 0)}, власні/похідні SR_RX_Custom: {cov["board_footprint_origin"].get("SR_RX_Custom", 0)}).',
             f'- Позначень, що купуються (без DNP): {cov["purchased_refs"]}; з MPN: {cov["purchased_refs_with_mpn"]}; за станом: ' + ', '.join(f'{k} — {v}' for k, v in cov['purchased_refs_by_availability'].items()) + '.',
             f'- Правило запасу для пасивних на платах: +{model.db["policy"]["spares"]["passive_pct"]} %, щонайменше {model.db["policy"]["spares"]["passive_min"]} шт. Дистриб’ютори: ' + ', '.join(model.db['policy']['distributors']) + '.', '',
             'Стан: «в наявності» — є на складі хоча б в одного прочитаного дистриб’ютора; «у каталозі» — сторінку прочитано, кількість не показано; «склад 0» — лише нульовий склад; «з 10-bom» — продавець з оцінки v2 (18.10.2026), сторінку не перечитано; «TBD» — MPN не підтверджено, причина в примітці.', '']
    for m, title in sec.items():
        part_rows = [r for r in rows if r['section'] == m]
        if not part_rows:
            continue
        lines += [f'## {title}', '', '| замовити | позначення | виробник | MPN | LCSC / DigiKey / інше | стан |', '|---:|---|---|---|---|---|']
        for r in part_rows:
            refs = r['refs'] if len(r['refs']) <= 60 else r['refs'][:57] + '…'
            src = ' / '.join(x for x in (r['lcsc'], r['digikey'], r['other'] if len(r['other']) < 40 else 'див. CSV') if x)
            lines.append(f'| {r["order"]} | {refs} | {r["manufacturer"] or "—"} | {r["mpn"] or "—"} | {src or "—"} | {r["state"]} |')
        lines.append('')
    lines += ['## Відкриті позиції (TBD)', '', '| запис | позначення | причина |', '|---|---|---|']
    for t in cov['tbd']:
        lines.append(f'| {t["part"]} | {" ".join(t["refs"])} | {t["reason"]} |')
    lines += ['', '## Відхилення від номіналу графа', '']
    for d in cov['deviations']:
        lines.append(f'- {d["part"]} ({" ".join(d["refs"])}): допуск {d["tolerance_pct"]} % замість значення графа — {d["reason"]} Рішення: {d["decision"]}.')
    lines += ['', '## Інші відкриті питання', ''] + [f'- {x}' for x in cov['open_items']]
    lines += ['', 'Повні колонки (запас, ціна, альтернативи, примітки) — у [10-zakupivlia.csv](10-zakupivlia.csv); перелік для JLC PCBA за платами — у [10-jlc-bom.csv](10-jlc-bom.csv); лічильники — у [10-parts-coverage.json](10-parts-coverage.json).', '']
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    model = Model()
    model.check()
    prep = prepare_module()
    files = dict(model.graph_texts())
    files[LIBDIR / 'manifest.json'] = model.manifest_text()
    files[ROOT / 'build/kicad/fp-lib-table'] = model.fp_table_text()
    rows = model.bom(prep)
    cov = model.coverage(prep)
    head = io.StringIO()
    csv.writer(head, quoting=csv.QUOTE_ALL, lineterminator='\n').writerow([BOM_HEAD[f] for f in BOM_FIELDS])
    files[ROOT / 'build/10-zakupivlia.csv'] = head.getvalue() + csv_text(rows, BOM_FIELDS).split('\n', 1)[1]
    files[ROOT / 'build/10-zakupivlia.md'] = bom_md(model, rows, cov)
    files[ROOT / 'build/10-jlc-bom.csv'] = csv_text(model.jlc_rows(prep), ['Board', 'Comment', 'Designator', 'Footprint', 'LCSC Part #', 'Mount'])
    files[ROOT / 'build/10-parts-coverage.json'] = json.dumps(cov, ensure_ascii=False, indent=1) + '\n'
    for w in model.warnings:
        print('WARNING:', w)
    if model.errors:
        for e in model.errors:
            print('ERROR:', e)
        raise SystemExit(f'Parts database FAIL: {len(model.errors)} error(s)')
    if args.check:
        stale = [p.relative_to(ROOT).as_posix() for p, t in files.items() if not p.is_file() or p.read_text(encoding='utf-8') != t]
        if stale:
            raise SystemExit('Parts outputs are stale (run python tools/build_parts.py): ' + ', '.join(stale))
    else:
        for p, t in files.items():
            p.write_text(t, encoding='utf-8', newline='\n')
    print(json.dumps({k: cov[k] for k in ('refs', 'parts', 'board_refs', 'board_refs_with_footprint', 'purchased_refs', 'purchased_refs_with_mpn', 'purchased_refs_by_availability')}, ensure_ascii=False))
    print(f'Parts database PASS ({"checked" if args.check else "written"}); TBD parts: {len(cov["tbd"])}; warnings: {len(model.warnings)}')


if __name__ == '__main__':
    main()
