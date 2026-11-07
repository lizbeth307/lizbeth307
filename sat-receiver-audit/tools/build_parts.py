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
  build/10-dzhgut-rodyny.csv                        harness connector families per pin count (no graph refs yet)
  build/10-zakupivlia-kriplennia.csv                fasteners, seals, consumables and tools outside the schematic (assembly_items)
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
# Part fields this generator owns in design/E*.json (tools/generate_kicad.py prints them as KiCad fields).
GRAPH_FIELDS = ('footprint', 'mpn', 'manufacturer', 'lcsc', 'alt_mpn')
# Schema of design/parts/parts.json (described in design/parts/README.md).
PART_KEYS = {'id', 'mount', 'refs', 'kind', 'package', 'footprint', 'manufacturer', 'mpn', 'sku', 'alternates', 'fallbacks', 'extras', 'match',
             'single_source', 'tbd', 'source', 'note', 'polarized', 'deviation', 'unused_pads', 'host', 'interface_open', 'interface_resolved'}
ALT_KEYS = {'manufacturer', 'mpn', 'sku', 'note'}
# pcb/prepare.py category of a connector/feed ref that is not a board part: its entry states what is still open.
INTERFACE_CATEGORY = 'physical_interface_boundary'
EXTRA_KEYS = {'manufacturer', 'mpn', 'sku', 'qty_per_ref', 'item', 'note'}
SKU_KEYS = {'lcsc', 'digikey', 'mouser', 'tme', 'web'}
# harness_families: connector families of the board-to-board harnesses that have no graph refs yet (build/15, build/16).
FAMILY_KEYS = {'id', 'title', 'note', 'terminal', 'sizes'}
FAMILY_ROLES = ('header_top', 'header_side', 'housing')
FAMILY_ITEM_KEYS = {'manufacturer', 'mpn', 'sku', 'footprint', 'note'}
FAMILY_FIELDS = ['family', 'pins', 'role', 'manufacturer', 'mpn', 'lcsc', 'lcsc_stock', 'lcsc_usd_1', 'footprint', 'note']
# assembly_items: purchases outside the schematic that the mechanical and assembly packages require (fasteners, seals,
# consumables, tools). Each has a quantity from the model or the harness table and either a read source or a tbd reason.
ITEM_KEYS = {'id', 'item', 'qty', 'spares', 'for', 'manufacturer', 'mpn', 'sku', 'source', 'tbd', 'note'}
ITEM_FIELDS = ['id', 'item', 'qty', 'spares', 'order', 'for', 'manufacturer', 'mpn', 'sku', 'state', 'note']
ITEM_HEAD = {'id': 'запис', 'item': 'що', 'qty': 'к-сть на виріб', 'spares': 'запас', 'order': 'замовити', 'for': 'де і навіщо (джерело кількості)',
             'manufacturer': 'виробник', 'mpn': 'MPN', 'sku': 'сторінка / SKU', 'state': 'стан', 'note': 'примітка'}
# Harness connector roll-up written by tools/build_assembly_docs.py (quantities per family, pins and role).
HARNESS_ROLLUP = ROOT / 'build/16-dzhgut-pidsumok.csv'
BOARD3 = {'PWR_MAIN': 'PWR', 'PWR_BRANCH': 'PWR', 'USB_POWER': 'PWR', 'RF_HMC': 'RF', 'RF_HF': 'RF', 'RF_INJECTOR': 'RF', 'DC_CORE': 'RF', 'CTRL_HMI': 'CTRL',
          # small boards off the three plate boards (pcb/prepare.py DOMAIN_OVERRIDE): each is its own JLC order line
          'ENC': 'ENC', 'HATCH': 'HATCH', 'T7_INSERT': 'T7_INSERT', 'HDMI_INSERT': 'HDMI_INSERT', 'IMU_CARRIER': 'IMU_CARRIER', 'PACK_FUSE': 'PACK_FUSE'}
SHEET_BOARD = {'E1': 'PWR', 'E2': 'PWR', 'E3': 'CTRL', 'E4': 'RF', 'E5': 'PWR'}
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


def alt_text(p):
    return '; '.join(f'{a.get("manufacturer", "")} {a["mpn"]}'.strip() for a in p.get('alternates', []))


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


def by_name(paths):
    """Case-sensitive name order: Windows Path ordering ignores case, which would reorder the manifest."""
    return sorted(paths, key=lambda p: p.name)


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

    def part_of_ref(self, ref):
        return next((p for p in self.db['parts'] if ref in p['refs']), None)

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
            # A page that answered (HTTP 200) proves nothing about the part: the snapshot row must carry the
            # part number the page showed, and it must be this entry's MPN.
            if not rec.get('mpn'):
                self.err(f'{entry.get("mpn") or entry.get("id")}: {dist} {key} snapshot row shows no MPN, so the page does not confirm the part '
                         '(re-read it or move the seller to source)')
                continue
            if entry.get('mpn') and norm_mpn(rec['mpn']) != norm_mpn(entry['mpn']):
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
        self.check_interfaces(prepare_module())
        self.check_families()
        self.check_items()
        newest = max(self.snapshot_dates)
        age = (datetime.date.today() - datetime.date.fromisoformat(newest)).days
        if age > self.db['policy']['snapshot_max_age_days']:
            self.warnings.append(f'newest availability snapshot is {age} days old ({newest}); run tools/check_parts_availability.py')

    def interface_refs(self, prep, p):
        """Refs of p that pcb/prepare.py classifies as physical interface boundaries (not board parts)."""
        return [r for r in p['refs'] if r in self.comps and
                prep.category({**self.comps[r][1], '_sheet': self.comps[r][0], '_mount': p['mount']})[0] == INTERFACE_CATEGORY]

    def check_interfaces(self, prep):
        """A connector or feed that is not a board part is resolved only when its entry says how both the mating part and
        the mounting are fixed (interface_resolved); otherwise interface_open says what is still open, and pcb/prepare.py
        keeps a blocking record. A tbd entry stays open through its tbd text."""
        for p in self.db['parts']:
            refs = self.interface_refs(prep, p)
            opened, resolved = p.get('interface_open'), p.get('interface_resolved')
            if not refs:
                if opened or resolved:
                    self.err(f'{p["id"]}: interface_open/interface_resolved only apply to interface refs (pcb/prepare.py {INTERFACE_CATEGORY})')
                continue
            if p.get('tbd'):
                if opened or resolved:
                    self.err(f'{p["id"]}: a tbd entry keeps its interface open through tbd; drop interface_open/interface_resolved')
                continue
            if bool(opened) == bool(resolved):
                self.err(f'{p["id"]}: interface refs {" ".join(refs)} need exactly one of interface_open (what is still open) or interface_resolved')
                continue
            if resolved and not (isinstance(resolved, str) and resolved.strip()):
                self.err(f'{p["id"]}: interface_resolved must say how the mating part and the mounting are fixed')
            if isinstance(opened, dict):
                if sorted(opened) != sorted(refs):
                    self.err(f'{p["id"]}: interface_open must name exactly the interface refs {" ".join(refs)}')
                texts = list(opened.values())
            else:
                texts = [opened] if opened else []
            if any(not (isinstance(t, str) and t.strip()) for t in texts):
                self.err(f'{p["id"]}: interface_open needs a reason text')

    def family_items(self):
        """(family, pins, role, item) for every orderable item of harness_families."""
        out = []
        for fam in self.db.get('harness_families', []):
            if fam.get('terminal'):
                out.append((fam, '', 'terminal', fam['terminal']))
            for size in fam.get('sizes', []):
                out += [(fam, size.get('pins'), role, size[role]) for role in FAMILY_ROLES if role in size]
        return out

    def check_families(self):
        """Every harness-family item is an LCSC listing of the snapshot; a header names a KiCad footprint with its pin count."""
        for fam in self.db.get('harness_families', []):
            fid = fam.get('id')
            for key in sorted(set(fam) - FAMILY_KEYS):
                self.err(f'harness family {fid}: unknown key {key}')
            seen = set()
            for size in fam.get('sizes', []):
                n = size.get('pins')
                if not isinstance(n, int) or n < 1 or n in seen:
                    self.err(f'harness family {fid}: pin count {n!r} missing or repeated')
                seen.add(n)
                for key in sorted(set(size) - set(FAMILY_ROLES) - {'pins', 'note'}):
                    self.err(f'harness family {fid} {n}: unknown key {key}')
                if 'header_top' not in size and 'header_side' not in size:
                    self.err(f'harness family {fid} {n}: no board header')
        for fam, n, role, item in self.family_items():
            label = f'harness family {fam.get("id")} {n} {role}'.replace('  ', ' ')
            for key in sorted(set(item) - FAMILY_ITEM_KEYS):
                self.err(f'{label}: unknown key {key}')
            if not (item.get('manufacturer') and item.get('mpn') and (item.get('sku') or {}).get('lcsc')):
                self.err(f'{label}: needs manufacturer, mpn and an LCSC SKU')
            if role.startswith('header'):
                m = re.search(r'_(\d+)x(\d+)', item.get('footprint') or '')
                if ':' not in (item.get('footprint') or '') or not m or int(m[1]) * int(m[2]) != n:
                    self.err(f'{label}: footprint {item.get("footprint")!r} is not a KiCad Lib:Name with {n} contacts')
            elif item.get('footprint'):
                self.err(f'{label}: only board headers have a footprint')
            for dist, rec in self.sku_known(item):
                if rec.get('stock') == 0:
                    self.warnings.append(f'{label} {item["mpn"]}: {dist} stock 0 on the snapshot date')

    def check_items(self):
        """assembly_items: a quantity, where it is used, and either a confirmed MPN with a read source or a tbd reason."""
        seen = set()
        for it in self.db.get('assembly_items', []):
            iid = it.get('id')
            if not iid or iid in seen:
                self.err(f'assembly item {iid!r}: id missing or repeated')
            seen.add(iid)
            for key in sorted(set(it) - ITEM_KEYS):
                self.err(f'assembly item {iid}: unknown key {key}')
            if not isinstance(it.get('qty'), int) or it['qty'] < 1 or not isinstance(it.get('spares', 0), int) or it.get('spares', 0) < 0:
                self.err(f'assembly item {iid}: qty must be a positive integer and spares a non-negative integer')
            if not (it.get('item') or '').strip() or not (it.get('for') or '').strip():
                self.err(f'assembly item {iid}: item and for (where it is used, source of the quantity) are required')
            for dist in sorted(set(it.get('sku') or {}) - SKU_KEYS):
                self.err(f'assembly item {iid}: unknown distributor key {dist}')
            if it.get('tbd'):
                if not isinstance(it['tbd'], str) or not it['tbd'].strip():
                    self.err(f'assembly item {iid}: tbd must be a reason text')
                continue
            if not (it.get('mpn') and it.get('manufacturer')):
                self.err(f'assembly item {iid}: needs manufacturer and mpn, or tbd with a reason')
            if not it.get('sku') and not it.get('source'):
                self.err(f'assembly item {iid}: needs a SKU read in a snapshot or a source (page and date), or tbd')
            self.sku_known(it)

    def item_rows(self):
        rows = []
        for it in self.db.get('assembly_items', []):
            sku = ', '.join(f'{d}:{k}' for d, k in (it.get('sku') or {}).items())
            state, why = self.availability(it)
            rows.append({'id': it['id'], 'item': it['item'], 'qty': it['qty'], 'spares': it.get('spares', 0), 'order': it['qty'] + it.get('spares', 0),
                         'for': it['for'], 'manufacturer': '' if it.get('tbd') else it.get('manufacturer', ''), 'mpn': '' if it.get('tbd') else it.get('mpn', ''),
                         'sku': '; '.join(x for x in (sku, it.get('source', '')) if x), 'state': state,
                         'note': '; '.join(x for x in (why if state == 'TBD' else '', it.get('note', '')) if x)})
        return rows

    def family_rows(self):
        rows = []
        for fam, n, role, item in self.family_items():
            rec = self.lcsc_rec(item) or {}
            rows.append({'family': fam['id'], 'pins': n, 'role': role, 'manufacturer': item['manufacturer'], 'mpn': item['mpn'],
                         'lcsc': item['sku']['lcsc'], 'lcsc_stock': rec.get('stock', ''), 'lcsc_usd_1': unit_price(rec, 1) if rec else '',
                         'footprint': item.get('footprint', ''), 'note': item.get('note', '')})
        return rows

    def check_schema(self, p):
        """design/parts/README.md lists these keys; an unknown key is a typo, not data."""
        for key in sorted(set(p) - PART_KEYS):
            self.err(f'{p.get("id")}: unknown key {key}')
        for k in ('id', 'mount', 'refs'):
            if not p.get(k):
                self.err(f'{p.get("id")}: missing {k}')
        for group, allowed in (('alternates', ALT_KEYS), ('fallbacks', ALT_KEYS), ('extras', EXTRA_KEYS)):
            for e in p.get(group, []):
                for key in sorted(set(e) - allowed):
                    self.err(f'{p.get("id")}: {group} entry {e.get("mpn")} has unknown key {key}')
                if not e.get('mpn'):
                    self.err(f'{p.get("id")}: {group} entry without mpn')
        # A fallback changes behaviour or the land/cutout: it is never written as a substitute (alt_mpn, JLC alternate).
        for e in p.get('fallbacks', []):
            if not (e.get('note') or '').strip():
                self.err(f'{p.get("id")}: fallback {e.get("mpn")} needs a note saying what changes and who decides')
        for e in [p] + p.get('alternates', []) + p.get('fallbacks', []) + p.get('extras', []):
            for dist in sorted(set(e.get('sku') or {}) - SKU_KEYS):
                self.err(f'{p.get("id")}: unknown distributor key {dist}')

    def check_part(self, p, manifest_fps):
        self.check_schema(p)
        mount, fp = p['mount'], p.get('footprint')
        refs = [r for r in p['refs'] if r in self.comps]
        if mount == 'virtual':
            host = p.get('host') or {}
            if sorted(host) != sorted(p['refs']):
                self.err(f'{p["id"]}: a virtual part needs host refs for exactly its refs')
            for ref, h in host.items():
                hp = self.part_of_ref(h)
                if hp is None or hp['mount'] not in PCB_MOUNTS or not hp.get('footprint'):
                    self.err(f'{p["id"]}: host {h} of {ref} is not a board part with a footprint')
        elif p.get('host'):
            self.err(f'{p["id"]}: host is only for mount=virtual')
        if mount in PCB_MOUNTS:
            if not fp:
                self.err(f'{p["id"]}: board mount {mount} without footprint')
            elif fp not in manifest_fps:
                self.err(f'{p["id"]}: footprint {fp} is not in build/kicad/footprints')
            else:
                lib, name = fp.split(':', 1)
                pads = set(pads_of(LIBDIR / f'{lib}.pretty' / f'{name}.kicad_mod'))
                unused = p.get('unused_pads', {})
                for ref in refs:
                    pins = {str(x['number']) for x in self.comps[ref][1]['pins']}
                    missing = sorted(pins - pads)
                    if missing:
                        self.err(f'{ref}: pins {missing} have no pad in {fp}')
                    # Every pad is a graph pin or an explained unused/mechanical pad (PIN-01).
                    extra = sorted(pads - pins)
                    unexplained = [x for x in extra if x not in unused]
                    if unexplained:
                        self.err(f'{ref}: pads {unexplained} of {fp} are neither graph pins nor listed in unused_pads')
                    stale = sorted(set(unused) - set(extra))
                    if stale:
                        self.err(f'{ref}: unused_pads {stale} are graph pins or not pads of {fp}')
                for pad, why in unused.items():
                    if not isinstance(why, str) or not why.strip():
                        self.err(f'{p["id"]}: unused pad {pad} needs a reason')
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
        for alt in p.get('alternates', []) + p.get('fallbacks', []):
            self.sku_known(alt)
        for ex in p.get('extras', []):
            self.sku_known(ex)
            if not ex.get('qty_per_ref'):
                self.err(f'{p["id"]}: extra {ex.get("mpn")} needs qty_per_ref')
        kind = p.get('kind')
        checked = 0
        if kind in PASSIVE and not p.get('tbd'):
            for entry in [p] + p.get('alternates', []):
                rec = self.lcsc_rec(entry)
                # A listing without attributes (e.g. LCSC C43824843) cannot be compared; the MPN match below applies instead.
                if rec is None or not rec.get('attributes'):
                    continue
                checked += 1
                if p.get('package') and rec.get('package') != p['package']:
                    self.err(f'{p["id"]}: {entry["mpn"]} LCSC package {rec.get("package")} != {p["package"]}')
                for ref in refs:
                    for problem in requirement_problems(kind, self.comps[ref][1]['value'], rec.get('attributes', {}), p.get('deviation')):
                        self.err(f'{ref} {self.comps[ref][1]["value"]!r} vs {entry["mpn"]}: {problem}')
            if not checked and kind != 'inductor' and not p.get('match'):
                self.warnings.append(f'{p["id"]}: no LCSC attributes to check the value against')
        if p.get('match') and not checked:
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
                # A tbd entry may name a candidate, but the graph (and KiCad MPN field) gets no part number until it is confirmed.
                if p['mount'] in BUY_MOUNTS and p.get('mpn') and p.get('manufacturer') and not p.get('tbd'):
                    want['mpn'] = p['mpn']
                    want['manufacturer'] = p['manufacturer']
                if p['mount'] in ('pcb_smt', 'pcb_tht') and (p.get('sku') or {}).get('lcsc') and not p.get('tbd'):
                    want['lcsc'] = p['sku']['lcsc']
                if 'mpn' in want and p.get('alternates'):
                    want['alt_mpn'] = alt_text(p)
                for key in GRAPH_FIELDS:
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
        if ref in getattr(prep, 'DOMAIN_OVERRIDE', {}):
            return BOARD3[prep.DOMAIN_OVERRIDE[ref]]
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
        for d in by_name(LIBDIR.glob('*.pretty')):
            for f in by_name(d.glob('*.kicad_mod')):
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
        self.manifest_rows = rows
        return json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'

    def readme_text(self):
        rows = self.manifest_rows
        official = [r for r in rows if r['origin'].startswith('KiCad')]
        custom = [r for r in rows if r['origin'] == 'SR_RX_Custom custom']
        derived = [r for r in rows if r['origin'] == 'SR_RX_Custom derived']
        assigned = sum(len(r['refs']) for r in rows)
        libs = sorted({r['footprint'].split(':', 1)[0] for r in official})
        return '\n'.join([
            f'# Project footprint library (KiCad {KICAD_TAG})', '',
            f'Generated by `tools/build_parts.py` from `design/parts/parts.json`; do not edit by hand. {len(rows)} footprints carry {assigned} '
            f'footprint assignments of the schematic graphs design/E1..E5.json; `manifest.json` lists each file with its SHA256, pad names and refs.', '',
            f'- {len(official)} official KiCad {KICAD_TAG} footprints, byte-for-byte unmodified, in {len(libs)} libraries ({", ".join(libs)}). '
            f'Source: https://gitlab.com/kicad/libraries/kicad-footprints/-/tree/{KICAD_TAG} (the first 17 came from the PPA package '
            '`kicad-footprints_10.0.7~ubuntu24.04.1_all.deb`, SHA256 a1c25a690348180d572b73496668cffafdaecf284d6555279fa89d5e4fefa46c, which carries the same files). '
            'The parts workflow compares every one of them with the library inside the kicad/kicad:10.0.7 image.',
            f'- {len(custom)} custom footprints in `SR_RX_Custom.pretty`, written by `tools/make_footprints.py` from the manufacturer land pattern named in '
            '`SR_RX_Custom.pretty/provenance.json` (URL, drawing, page, read date).',
            f'- {len(derived)} derived footprints in `SR_RX_Custom.pretty`: an official footprint with unchanged geometry whose pad numbers are renamed to the '
            'graph pin names (A/K, CENTER/SHIELD, EPAD, SWD pads); the source SHA256 is in provenance.json.', '',
            'The project fp-lib-table uses ${KIPRJMOD} relative paths. See LICENSE.md for the KiCad library licence. No 3D models are committed. '
            'A footprint here is a layout input, not a fabrication release: custom land patterns still need review against the part drawing before an order.', ''])

    def fp_table_text(self):
        lines = ['(fp_lib_table', '  (version 7)']
        for d in by_name(LIBDIR.glob('*.pretty')):
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
            if rec is None or not rec.get('mpn'):
                continue  # not evidence (sku_known reports it)
            stock = rec.get('stock')
            # in_stock: the page says "in stock" without a count (e.g. Mini-Circuits "more than 1,000").
            states.append('ok' if stock or rec.get('in_stock') else 'zero-stock' if stock == 0 else 'listed')
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
            tbd = bool(p.get('tbd'))
            name = lambda e: ' '.join(x for x in (e.get('manufacturer'), e.get('mpn')) if x)
            candidate = f'кандидат, не підтверджено: {name(p)}' if tbd and p.get('mpn') else ''
            fallback = '; '.join(f'не заміна без рішення — {name(a)}: {a["note"]}' for a in p.get('fallbacks', []))
            rows.append({'section': p['mount'], 'part': p['id'], 'qty': qty, 'spare': spare, 'order': qty + spare, 'refs': ' '.join(sorted(live, key=sort_ref)),
                         'boards': ' '.join(boards), 'manufacturer': '' if tbd else p.get('manufacturer', ''), 'mpn': '' if tbd else p.get('mpn', ''),
                         'footprint': p.get('footprint', ''),
                         'lcsc': (p.get('sku') or {}).get('lcsc', ''), 'digikey': (p.get('sku') or {}).get('digikey', ''),
                         'other': (p.get('sku') or {}).get('web', '') or p.get('source', ''),
                         'lcsc_stock': '' if rec is None else rec.get('stock'), 'lcsc_usd': '' if rec is None else unit_price(rec, qty + spare),
                         'alternates': alt_text(p),
                         'state': state, 'note': '; '.join(x for x in (why if state == 'TBD' else '', candidate, p.get('note', ''), p.get('single_source', '') and 'одне джерело: ' + p['single_source'], fallback) if x)})
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
                             'LCSC Part #': (p.get('sku') or {}).get('lcsc', ''), 'Mount': 'SMD' if p['mount'] == 'pcb_smt' else 'THT',
                             'LCSC stock': '' if self.lcsc_rec(p) is None else self.lcsc_rec(p).get('stock'), 'LCSC alternate': self.stocked_alternate(p)})
        rows.sort(key=lambda r: (r['Board'], r['Mount'], r['Comment']))
        return rows

    def v2_rows(self):
        """Rows of the v2 estimate build/10-bom.csv that the schematic database does not replace (MECH-12)."""
        with (ROOT / 'build/10-bom.csv').open(encoding='utf-8', newline='') as f:
            table = list(csv.DictReader(f))
        mapping = self.db.get('bom_v2_rows', {})
        numbers = {r['№'] for r in table}
        for no, v in mapping.items():
            if no not in numbers:
                self.err(f'bom_v2_rows: 10-bom.csv has no row {no}')
            if v.get('status') not in ('db', 'partial') or not v.get('note'):
                self.err(f'bom_v2_rows {no}: status db|partial and a note are required')
            for key in sorted(set(v) - {'status', 'note', 'remaining'}):
                self.err(f'bom_v2_rows {no}: unknown key {key}')
            # A partial row is printed only with what is still bought by it, so the database part is not ordered twice.
            if (v.get('status') == 'partial') != bool((v.get('remaining') or '').strip()):
                self.err(f'bom_v2_rows {no}: a partial row needs remaining (what is still bought by this row, with quantities); a db row has none')
        for p in self.db['parts']:
            for no in re.findall(r'10-bom\.csv №(\d+)', p.get('source', '')):
                if no not in mapping:
                    self.err(f'{p["id"]}: source cites 10-bom row {no}, which bom_v2_rows does not map')
        out = []
        for r in table:
            v = mapping.get(r['№'], {})
            if v.get('status') == 'db':
                continue
            partial = v.get('status') == 'partial'
            # Partial row: only the remaining sub-items; the v2 USD covered the whole row, so no sum is carried.
            out.append({'row': r['№'], 'group': r['група'], 'level': r['рівень'], 'in_total': r['у підсумку рівня'], 'qty': '' if partial else r['к-сть'],
                        'item': r['позиція'], 'model': v.get('remaining', '') if partial else r['модель і номер деталі'], 'seller': r['продавець (основний / запасний)'],
                        'usd_min': '' if partial else r['USD мін (рядок)'], 'usd_max': '' if partial else r['USD макс (рядок)'], 'status_v2': r['статус'],
                        'coverage': v.get('note', '') if partial else ''})
        return out

    def stocked_alternate(self, p):
        """First alternate with LCSC stock when the primary has none (a hint for the JLC order, not an approval)."""
        rec = self.lcsc_rec(p)
        if rec is not None and rec.get('stock'):
            return ''
        for a in p.get('alternates', []):
            arec = self.lcsc_rec(a)
            if arec is not None and arec.get('stock'):
                return f'{(a.get("sku") or {})["lcsc"]} {a["mpn"]}' + (' (see note)' if a.get('note') else '')
        return ''

    def coverage(self, prep):
        mounts = collections.Counter(self.part_of[r]['mount'] for r in self.comps)
        bare = [r for r, (s, c) in self.comps.items() if prep.category({**c, '_sheet': s, '_mount': self.part_of[r]['mount']})[0] == 'bare_board_part']
        pcb_refs = [r for r in self.comps if self.part_of[r]['mount'] in PCB_MOUNTS]
        buy_refs = [r for r in self.comps if self.part_of[r]['mount'] in BUY_MOUNTS and not self.comps[r][1].get('dnp')]
        state = collections.Counter(self.availability(self.part_of[r])[0] for r in buy_refs)
        tbd = [{'part': p['id'], 'refs': p['refs'], 'reason': p['tbd']} for p in self.db['parts'] if p.get('tbd')]
        interfaces = []
        for p in self.db['parts']:
            refs = self.interface_refs(prep, p)
            if refs and not p.get('tbd') and not p.get('interface_resolved'):
                opened = p['interface_open']
                interfaces += ([{'part': p['id'], 'refs': [r], 'open': opened[r]} for r in sorted(opened, key=sort_ref)] if isinstance(opened, dict)
                               else [{'part': p['id'], 'refs': refs, 'open': opened}])
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
            # A tbd candidate is not counted: its MPN is not confirmed and is not written to the graphs.
            'purchased_refs_with_mpn': sum(bool(self.part_of[r].get('mpn')) and not self.part_of[r].get('tbd') for r in buy_refs),
            'harness_family_items': len(self.family_items()),
            'tbd': tbd, 'interfaces_open': interfaces, 'carried_from_10_bom': carried,
            'deviations': [{'part': p['id'], 'refs': p['refs'], **p['deviation']} for p in self.db['parts'] if p.get('deviation')],
            'fallbacks': [{'part': p['id'], 'refs': p['refs'], 'mpn': a['mpn'], 'note': a['note']} for p in self.db['parts'] for a in p.get('fallbacks', [])],
            'footprint_checks_open': [{'footprint': f'SR_RX_Custom:{k}', 'note': v.get('note') or v.get('drawing')} for k, v in sorted(prov.items())
                                      if 'verify' in json.dumps(v) or 'must be checked' in json.dumps(v)],
            'open_items': OPEN_ITEMS,
        }


OPEN_ITEMS = [
    'SW308/SW309 — це кнопки всередині енкодерів ENC301/ENC302: граф тримає їх окремими позначеннями, тому контакти S1/S2 футпринта енкодера лишаються без кола в netlist, доки власник E3 не перенесе кола кнопок на виводи енкодера (у pcb/generated/unresolved.csv — блокуючий запис host_pads_unconnected).',
    'Роз’єми з боку плати для джгутів, які ще не мають позначень у графі (відповідь J302 на силовій платі, гніздо LAB BUS за J505, вентилятор, виводи NTC TH301/TH302, міжплатні з’єднання поділу на плати), куплено як супутні деталі там, де їх названо; для решти артикули за кількістю контактів дає розділ «Роз’єми міжплатних джгутів», кількість — підсумок build/16 нижче; позначення J на схемі чекають власників графів (хвиля 2).',
    'Q6A J20 (J301): обрано родину IDC — гніздо XDFH-0258-2*20P на стрічці 40 × 1.27 мм і бокс XDFH-0254-2*20P на CTRL (harness_families IDC); MPN стрічки, висота боксу (обмеження CTRL 5.5 мм) і довжина S01 ≤200 мм — TBD (запис J-Q6A-EXISTING, interface_open; build/16 S01).',
    'Панельні порти P1–P3 і P6 (J401–J403, J406) — TBD: їхній внутрішній бік — кола RF-плати, а роз’єму з боку плати (U.FL/MHF1 чи крайового SMA) у графі E4 немає; потрібні позначення J з боку плати (власник E4) і пігтейл з розрахунком втрат (build/15 «RF-порти»).',
    'Панельні деталі (SMA P8, F, BNC, USB-A IP68, USB-C IP67, кнопки PV6 IP65) обрано за сторінками DigiKey DE від 06.11.2026; вирізи, ущільнення, заглушки й заглиблення кнопки EDL — механічний пакет (MECH-07). Що ще відкрито для кожного інтерфейсу — розділ «Інтерфейси без кріплення». Внутрішній кабель ПЧ W402 і кабель живлення pod W425 лишаються TBD.',
    'Розмір відкритої площадки HMC7992LP3DE і крок виводів CPT-1207-3TH треба звірити з кресленнями виробника до випуску PCB (див. SR_RX_Custom.pretty/provenance.json; analog.com 24.10.2026 не відповідав).',
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


V2_FIELDS = ['row', 'group', 'level', 'in_total', 'qty', 'item', 'model', 'seller', 'usd_min', 'usd_max', 'status_v2', 'coverage']
V2_HEAD = {'row': '№ у 10-bom', 'group': 'група', 'level': 'рівень', 'in_total': 'у підсумку рівня', 'qty': 'к-сть', 'item': 'позиція',
           'model': 'модель і номер деталі (v2; для частково покритого рядка — лише залишок з кількістю)', 'seller': 'продавець (v2)',
           'usd_min': 'USD мін (v2; порожньо для частково покритого)', 'usd_max': 'USD макс (v2; порожньо для частково покритого)',
           'status_v2': 'статус (v2)', 'coverage': 'що вже в базі деталей'}


def bom_md(model, rows, cov):
    date = max(model.snapshot_dates)
    sec = collections.OrderedDict((m, t) for m, t in SECTIONS)
    lines = ['# 10. Закупівля SR-RX-v2.1 (згенеровано з бази деталей)', '',
             f'Файл згенеровано `tools/build_parts.py` з [`design/parts/parts.json`](../design/parts/parts.json) і знімків наявності від {date}. Не редагувати вручну: зміни вносяться в базу деталей, далі `python tools/build_parts.py`.', '',
             'Це закупівельний перелік деталей схеми v2.1 (графи E1–E5) разом із супутніми деталями (тримачі запобіжників, корпуси й контакти роз’ємів, ферити). '
             'Деталі всередині готових модулів (Adafruit, Q6A) не купуються вдруге. Антени, прилади лабораторії, інструменти, корпус, кріплення й запасні модулі зведено нижче в розділі «Решта закупівлі» з рядків оцінки v2 [10-bom.csv](10-bom.csv), без рядків, які вже замінила база, тож цей файл — один перелік закупівлі v2.1. '
             'Специфікацію замовлення друкованих плат (стек, мідь, покриття) дає PCB-пакет, кріплення з довжинами — механічний пакет.',
             'Склад і ціна — показання дистриб’ютора на дату знімка, а не резерв: перед замовленням перевірити ще раз (`python tools/check_parts_availability.py --date РРРР-ММ-ДД`).', '',
             '**Апаратний випуск BLOCKED.** Наявність MPN не кваліфікує деталь: стендові ворота з OPEN_ITEMS лишаються відкритими.', '',
             '## Зведення', '',
             f'- Позначень на схемі: {cov["refs"]}; записів бази: {cov["parts"]}.',
             f'- Позначень на платах з посадковим місцем: {cov["board_refs_with_footprint"]} з {cov["board_refs"]} (KiCad {KICAD_TAG}: {cov["board_footprint_origin"].get("KiCad " + KICAD_TAG, 0)}, власні/похідні SR_RX_Custom: {cov["board_footprint_origin"].get("SR_RX_Custom", 0)}).',
             f'- Позначень, що купуються (без DNP): {cov["purchased_refs"]}; з MPN: {cov["purchased_refs_with_mpn"]}; за станом: ' + ', '.join(f'{k} — {v}' for k, v in cov['purchased_refs_by_availability'].items()) + '.',
             f'- Правило запасу для пасивних на платах: +{model.db["policy"]["spares"]["passive_pct"]} %, щонайменше {model.db["policy"]["spares"]["passive_min"]} шт. Дистриб’ютори: ' + ', '.join(model.db['policy']['distributors']) + '.', '',
             'Стан: «в наявності» — є на складі хоча б в одного прочитаного продавця (кількість або напис «in stock»); «у каталозі» — сторінку прочитано і вона показує цей MPN, кількість не показано; «склад 0» — лише нульовий склад; «з 10-bom» — продавець з оцінки v2 (18.10.2026), сторінку не перечитано; «TBD» — MPN не підтверджено, причина в примітці (кандидат, якщо він є, — лише в примітці). Сторінка рахується доказом лише тоді, коли рядок знімка записує MPN, який вона показала.', '']
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
    fams = model.db.get('harness_families', [])
    if fams:
        lines += ['## Роз’єми міжплатних джгутів (родини)', '',
                  'Поділ на три плати ([build/15](15-rishennia-komplektu.md)) додає роз’єми джгутів, яких ще немає в графах E1–E5. Нижче — артикули для кожної '
                  'кількості контактів, перевірені за знімком LCSC; розміщення дає таблиця роз’ємів джгутів пакета складання (build/16 §4), кількість штук — '
                  'підсумок нижче (з build/16), тому в розділи вище й у зведення ці роз’єми не входять. Посадкові місця — назви бібліотеки KiCad ' + KICAD_TAG + '; '
                  'файли додаються до бібліотеки проєкту разом із позначеннями J. Машинна таблиця — [10-dzhgut-rodyny.csv](10-dzhgut-rodyny.csv).', '']
        cell = lambda item: f'{item["mpn"]} ({item["sku"]["lcsc"]}, склад {(model.lcsc_rec(item) or {}).get("stock", "—")})'
        for fam in fams:
            lines += [f'### {fam["title"]}', '']
            if fam.get('note'):
                lines += [fam['note'], '']
            if fam.get('terminal'):
                t = fam['terminal']
                lines += [f'Клема: {t["manufacturer"]} {cell(t)}.', '']
            lines += ['| контактів | вилка на платі, верхній вхід | вилка, боковий вхід | розетка кабелю | примітка |', '|---:|---|---|---|---|']
            for s in fam['sizes']:
                lines.append(f'| {s["pins"]} | ' + ' | '.join(cell(s[r]) if r in s else '—' for r in FAMILY_ROLES) + f' | {s.get("note", "")} |')
            lines.append('')
    if HARNESS_ROLLUP.is_file():
        with HARNESS_ROLLUP.open(encoding='utf-8', newline='') as f:
            roll = list(csv.DictReader(f))
        lines += ['## Кількість роз’ємів, клем і проводу джгутів (з build/16)', '',
                  'Підсумок таблиць build/16 §4–5 за родиною, кількістю контактів і роллю, з правилом запасу пакета складання (+10 %, щонайменше 2 шт.; '
                  'провід — котушки 100 ft на артикул без запасу, жили й сума довжин моделі — у примітці, довжини уточнює CAD). Згенеровано `tools/build_assembly_docs.py` у [16-dzhgut-pidsumok.csv](16-dzhgut-pidsumok.csv); '
                  'артикули — з родин вище, TBD — у базі деталей немає (причина в рядку).', '',
                  '| родина | контактів | роль | MPN | к-сть | запас | замовити | примітка |', '|---|---:|---|---|---:|---:|---:|---|']
        for r in roll:
            lines.append(f'| {r["family"]} | {r["pins"]} | {r["role"]} | {md_cell(r["mpn"])} | {r["qty"]} | {r["spares"]} | {r["order"]} | {md_cell(r["note"]) or "—"} |')
        lines.append('')
    items = model.item_rows()
    if items:
        lines += ['## Кріплення, ущільнення, витратні матеріали й інструмент (поза схемою)', '',
                  'Деталі, яких вимагають механічна модель (`mechanical/params`, креслення M-07) і пакет складання (build/16–21), але яких немає '
                  'в графах E1–E5 (`assembly_items` у parts.json). Кількість — з моделі або таблиці джгутів (стовпець «де»), запас — правило пакета '
                  'складання (+10 %, щонайменше 2 шт.); TBD — сторінку виробника чи дистриб’ютора не прочитано, причина в примітці. '
                  'Машинна таблиця — [10-zakupivlia-kriplennia.csv](10-zakupivlia-kriplennia.csv).', '',
                  '| запис | що | к-сть + запас | виробник | MPN | де і навіщо | сторінка / SKU | стан |', '|---|---|---|---|---|---|---|---|']
        for r in items:
            lines.append(f'| {r["id"]} | {md_cell(r["item"])} | {r["qty"]} + {r["spares"]} | {r["manufacturer"] or "—"} | {r["mpn"] or "—"} | '
                         f'{md_cell(r["for"])} | {md_cell(r["sku"]) or "—"} | {r["state"]} |')
        lines.append('')
    other = model.v2_rows()
    lines += ['## Решта закупівлі: рядки оцінки v2 поза схемою', '',
              'Рядки [10-bom.csv](10-bom.csv), деталей яких немає в графах E1–E5 (антени, прилади лабораторії, інструменти, корпус, кріплення, запасні модулі, плата Q6A), '
              'або які база покриває лише частково. Модель, продавець і ціна — оцінка v2 від 18.10.2026 у USD, не перечитана. '
              'Для частково покритих рядків нижче стоїть лише залишок, який ще купується за цим рядком, з кількістю; суму v2 не наведено, бо вона охоплювала весь рядок. '
              f'Рядків, повністю замінених базою деталей (не купувати за ними вдруге): {sum(1 for v in model.db["bom_v2_rows"].values() if v["status"] == "db")}; '
              f'частково покритих: {sum(1 for r in other if r["coverage"])}; поза схемою: {sum(1 for r in other if not r["coverage"])}. Відповідність рядків і бази — `bom_v2_rows` у parts.json.', '']
    for level in sorted({r['level'] for r in other}, key=lambda x: [r['level'] for r in other].index(x)):
        lines += [f'### {level}', '', '| № | к-сть | позиція | модель і номер деталі (для часткового — лише залишок) | USD (v2) | що вже в базі |', '|---:|---|---|---|---|---|']
        for r in other:
            if r['level'] == level:
                usd = '—' if r['coverage'] else r['usd_min'] if r['usd_min'] == r['usd_max'] else f'{r["usd_min"]}–{r["usd_max"]}'
                lines.append(f'| {r["row"]} | {r["qty"]} | {md_cell(r["item"])} | {md_cell(r["model"])} | {usd} | {md_cell(r["coverage"]) or "—"} |')
        lines.append('')
    lines += ['## Відкриті позиції (TBD)', '', '| запис | позначення | причина |', '|---|---|---|']
    for t in cov['tbd']:
        lines.append(f'| {t["part"]} | {" ".join(t["refs"])} | {t["reason"]} |')
    lines += ['', '## Інтерфейси без кріплення', '',
              'Роз’єми й вводи, які не є деталями плати (панель, кабель, наявний порт Q6A, зібраний вузол): деталь обрано, але відповідна частина або кріплення ще відкриті. '
              'У `pcb/generated/unresolved.csv` кожен такий запис блокує випуск (`interface_mounting_unresolved`), доки запис бази не отримає `interface_resolved`.', '',
              '| запис | позначення | що відкрито |', '|---|---|---|']
    for i in cov['interfaces_open']:
        lines.append(f'| {i["part"]} | {" ".join(i["refs"])} | {i["open"].replace("|", "/")} |')
    lines += ['', '## Відхилення від номіналу графа', '']
    for d in cov['deviations']:
        lines.append(f'- {d["part"]} ({" ".join(d["refs"])}): допуск {d["tolerance_pct"]} % замість значення графа — {d["reason"]} Рішення: {d["decision"]}.')
    lines += ['', '## Запасні варіанти, що не є заміною', '',
              'Ці деталі змінюють поведінку, площадку або виріз: їх не записано в `alt_mpn` графів, поле KiCad Alt_MPN і колонку альтернатив JLC; ставити лише за рішенням власника аркуша.', '']
    for f in cov['fallbacks']:
        lines.append(f'- {f["part"]} ({" ".join(f["refs"])}): {f["mpn"]} — {f["note"]}')
    lines += ['', '## Інші відкриті питання', ''] + [f'- {x}' for x in cov['open_items']]
    lines += ['', 'Повні колонки (запас, ціна, альтернативи, примітки) — у [10-zakupivlia.csv](10-zakupivlia.csv); рядки оцінки v2 поза схемою — у [10-zakupivlia-inshe.csv](10-zakupivlia-inshe.csv); '
              'перелік для JLC PCBA за платами — у [10-jlc-bom.csv](10-jlc-bom.csv); лічильники — у [10-parts-coverage.json](10-parts-coverage.json).', '']
    return '\n'.join(lines)


def md_cell(text):
    text = (text or '').replace('|', '/').replace('\n', ' ')
    return text if len(text) <= 110 else text[:107] + '…'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    model = Model()
    model.check()
    prep = prepare_module()
    files = dict(model.graph_texts())
    files[LIBDIR / 'manifest.json'] = model.manifest_text()
    files[LIBDIR / 'README.md'] = model.readme_text()
    files[ROOT / 'build/kicad/fp-lib-table'] = model.fp_table_text()
    rows = model.bom(prep)
    cov = model.coverage(prep)
    head = io.StringIO()
    csv.writer(head, quoting=csv.QUOTE_ALL, lineterminator='\n').writerow([BOM_HEAD[f] for f in BOM_FIELDS])
    files[ROOT / 'build/10-zakupivlia.csv'] = head.getvalue() + csv_text(rows, BOM_FIELDS).split('\n', 1)[1]
    files[ROOT / 'build/10-zakupivlia.md'] = bom_md(model, rows, cov)
    other = csv.writer(head := io.StringIO(), quoting=csv.QUOTE_ALL, lineterminator='\n')
    other.writerow([V2_HEAD[k] for k in V2_FIELDS])
    other.writerows([r[k] for k in V2_FIELDS] for r in model.v2_rows())
    files[ROOT / 'build/10-zakupivlia-inshe.csv'] = head.getvalue()
    files[ROOT / 'build/10-jlc-bom.csv'] = csv_text(model.jlc_rows(prep), ['Board', 'Comment', 'Designator', 'Footprint', 'LCSC Part #', 'Mount', 'LCSC stock', 'LCSC alternate'])
    files[ROOT / 'build/10-dzhgut-rodyny.csv'] = csv_text(model.family_rows(), FAMILY_FIELDS)
    head = io.StringIO()
    csv.writer(head, quoting=csv.QUOTE_ALL, lineterminator='\n').writerow([ITEM_HEAD[f] for f in ITEM_FIELDS])
    files[ROOT / 'build/10-zakupivlia-kriplennia.csv'] = head.getvalue() + csv_text(model.item_rows(), ITEM_FIELDS).split('\n', 1)[1]
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
