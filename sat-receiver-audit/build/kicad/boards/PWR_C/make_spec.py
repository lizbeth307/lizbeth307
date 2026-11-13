#!/usr/bin/env python3
"""Board spec generator of PWR-C, the F2-C front-slab power-entry board (W2 PWRJ-F2C probe). Standard library only.

  python -I build/kicad/boards/PWR_C/make_spec.py            write pcb/boards/PWR_C.json and PWR_C.kicad_pro
  python -I build/kicad/boards/PWR_C/make_spec.py --check    exit 1 unless both reproduce
  python -I build/kicad/boards/PWR_C/make_spec.py --draft    print placement and copper problems, write nothing

Inputs: the graph (design/E1.json, E5.json: the PWR_ENTRY refs of pcb/generated/partition.json, which pcb/prepare.py
takes from pcb/partition-spec.json partition.domain_override_pwr_c), contract-proposal.json (outline, holes, vent
cut-out), pcb/generated/netclasses.json, and the KiCad 10.0.7 library copies in footprints-image/ (geometry of the
pilot placeholders; CI loads the same files from the kicad/kicad:10.0.7 image and checks their SHA256).

Design (probe choices, recorded in README.md):
- The battery path runs on scripted locked copper: J105.2 (S05 from PACK_FUSE) -> XR101 (the 15 mOhm shunt of the
  INA228 monitor, on PWR-C instead of the Adafruit 5832 board) -> E1_N -> the VIN pins of the Pololu #2813 land
  (XU106A) -> VOUT (XU106B) -> XJC1 (W-C1 to PWR-A J107); E1_N also feeds F103 -> J115 (S12) and J108.2 (S10).
- Every power net is routed by Freerouting only where the scripted copper stops: class PWRC_BRANCH (0.5 mm) joins the
  small pads (AON LDO, dividers, TVS, test points); check_boards branch_exempt names those refs.
- In1.Cu and In2.Cu are GND planes; every SMD GND pad gets a locked plane via (gnd_fanout of the PWR_A make_board.py).
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]  # sat-receiver-audit
sys.path.insert(0, str(BASE / 'pcb'))
sys.path.insert(0, str(BASE / 'build/kicad/boards/PWR_A'))
import board_gen as bg  # noqa: E402
import make_board as mb  # noqa: E402  (PWR_A: Placed, pad_copper, gnd_fanout)

BOARD = 'PWR_C'
SPEC = BASE / 'pcb/boards/PWR_C.json'
PROJECT = HERE / 'PWR_C.kicad_pro'
CONTRACT = HERE / 'contract-proposal.json'
ENC_PROJECT = BASE / 'build/kicad/boards/ENC/ENC.kicad_pro'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
PARTITION = BASE / 'pcb/generated/partition.json'
PWRA_SPEC = BASE / 'build/kicad/boards/PWR_A/board-spec.json'
IMG = HERE / 'footprints-image'
TAG = 'W2 PWRJ-F2C probe'
SRC_LIB = ('https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/10.0.7/{lib}.pretty/{name}.kicad_mod read '
           '2026-11-13 (curl default User-Agent, HTTP 200); copy in build/kicad/boards/PWR_C/footprints-image/ for the '
           'generator geometry; checked against the kicad/kicad:10.0.7 image copy at run time')

# Pilot placeholders: lands of parts that the graph does not carry as PWR-C board parts yet (GR package pending).
PLACEHOLDERS = {
    'XU102': {'fp': 'Package_SO:MSOP-10_3x3mm_P0.5mm', 'value': 'INA228AIDGSR (U102 of the Adafruit 5832, on PWR-C)',
              'pins': {'1': 'GND', '2': 'GND', '3': 'INA228_ALERT', '4': 'I2C0_SDA', '5': 'I2C0_SCL', '6': 'AON3V3',
                       '7': 'GND', '8': 'E1_SHUNT_P', '9': 'E1_N', '10': 'E1_SHUNT_P'},
              'pending': 'GR package: U102 INA228AIDGSR becomes a PWR-C board part (today a detail of the Adafruit 5832 '
                         'module); its VS decoupling and the A0/A1 straps come with it',
              'replaced_by': 'U102'},
    'XR101': {'fp': 'Resistor_SMD:R_2512_6332Metric', 'value': '15 mOhm 2512 shunt (R1 of the Adafruit 5832 board)',
              'pins': {'1': 'E1_SHUNT_P', '2': 'E1_N'},
              'pending': 'GR package: the 15 mOhm shunt becomes a PWR-C board part; MPN TBD (the Adafruit Eagle board '
                         'names HoLLR2512-2W-15mR-1%, no manufacturer data sheet read)',
              'replaced_by': 'R101'},
    'XU106A': {'fp': 'Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical',
               'value': 'Pololu #2813 land, VIN column (module flush on header pins)',
               'pins': {'1': 'E1_N', '2': 'E1_N', '3': 'GND', '4': 'GND', '6': 'E1_MASTER_OFF', '8': 'GND'},
               'pending': 'Pololu #2813 mounted on PWR-C (S07 deleted); column of the VIN side: VIN x2, GND x2, ON, OFF, '
                          'CTRL, GND from the Pololu dimension diagram psw03b (view 3), ON and CTRL unused',
               'replaced_by': 'U106'},
    'XU106B': {'fp': 'Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical',
               'value': 'Pololu #2813 land, VOUT column (module flush on header pins)',
               'pins': {'1': 'E1_SW', '2': 'E1_SW', '3': 'GND', '4': 'GND', '6': 'E1_SWITCH_A', '8': 'GND'},
               'pending': 'Pololu #2813 mounted on PWR-C; column of the VOUT side: VOUT x2, GND x2, B, A, -, GND as read '
                          'from the dimension diagram view 3; the A/B hole order is not certain there (TBD at GR)',
               'replaced_by': 'U106'},
    'XJC1': {'fp': 'Connector_Wire:SolderWire-1sqmm_1x02_P5.4mm_D1.4mm_OD2.7mm',
             'value': 'W-C1 E1_SW feed to PWR-A J107 (18 AWG wire lands)', 'pins': {'1': 'GND', '2': 'E1_SW'},
             'pending': 'GR package: PWR-C end of harness W-C1 (to PWR-A J107)', 'replaced_by': 'a PWR-C graph ref'},
    'XJC2': {'fp': 'Connector_Wire:SolderWire-1sqmm_1x02_P5.4mm_D1.4mm_OD2.7mm',
             'value': 'W-C1 LAB5 feed from PWR-A J106 (18 AWG wire lands)', 'pins': {'1': 'GND', '2': 'LAB5'},
             'pending': 'GR package: PWR-C end of harness W-C1 (from PWR-A J106)', 'replaced_by': 'a PWR-C graph ref'},
    'XJW2': {'fp': 'Connector_PinHeader_2.00mm:PinHeader_2x06_P2.00mm_Horizontal',
             'value': 'W-C2 to CTRL J306/J307: 2x6 2.00 mm land of a JST PHD S12B-PHDSS side-entry header',
             'pins': {'1': 'CHG_INHIBIT', '2': 'GND', '3': 'E1_BAT_ADC', '4': 'PWR_BUTTON', '5': 'I2C0_SCL', '6': 'GND',
                      '7': 'I2C0_SDA', '8': 'IMU_RX', '9': 'INA228_ALERT', '10': 'IMU_TX', '11': 'PICO_OFF', '12': 'GND'},
             'pending': 'GR package: PWR-C end of harness W-C2 (the 9 E1/E5 signals that left S02), CTRL end on the same '
                        'J306/J307 contacts', 'replaced_by': 'a PWR-C graph ref'},
}

# Anchors (board mm, y up, align origin; design choice of the probe). The #2813 sits flush on its two header columns:
# its body (20.3 x 25.4, 1.57 + 2.4 mm, Pololu psw03b) covers MODULE_BODY, which no other part enters.
X_VOUT, X_VIN, Y_P1 = 35.27, 53.05, 25.78  # header columns; pin 1 (power node) on top, pins run down 2.54 mm
MODULE_BODY = [X_VOUT - 1.27, Y_P1 + 5.08 - 25.4, X_VOUT - 1.27 + 20.3, Y_P1 + 5.08]
ANCHORS = {
    'XJW2': (11.8, 22.6, 270), 'J105': (11.0, 3.5, 90), 'XR101': (26.8, 3.2, 0), 'XU102': (24.1, 8.4, 0),
    'F103': (29.4, 12.0, 90), 'J115': (26.4, 30.0, 0),
    'XU106B': (X_VOUT, Y_P1, 0), 'XU106A': (X_VIN, Y_P1, 0),
    'XJC1': (65.0, 31.0, 180), 'J108': (66.0, 17.0, 180),
    'XJC2': (79.0, 30.0, 0),
    'J507': (103.95, 26.5, 180), 'J112': (115.45, 26.5, 180), 'J109': (122.95, 26.5, 180), 'J113': (130.45, 26.5, 180),
    'J114': (137.33, 25.0, 0), 'U109': (139.0, 15.0, 0),
}
# Placement groups (region [x0, y0, x1, y1], members); board_gen packs them in this order.
GROUPS = [
    ('AON', [13.8, 10.6, 27.3, 25.6], ['D104', 'D105', 'U103', 'C103', 'C104', 'C105', 'TP104', 'TP106']),
    ('SWITCH', [57.9, 6.4, 68.4, 12.8], ['D102', 'D103', 'R111', 'TP105']),
    ('UV', [95.6, 6.6, 112.4, 14.6], ['U104', 'R103', 'R104', 'R105', 'R106', 'R107', 'C106', 'D101', 'TP108', 'Q101',
                                     'R121', 'R122', 'R123']),
    ('E5', [95.6, 15.0, 112.4, 24.2], ['U553', 'U551', 'C552', 'C553', 'R553', 'TP503', 'R112', 'C114', 'TP107']),
    ('USBPD', [113.0, 6.6, 137.0, 20.5], ['C115', 'C116', 'C117', 'R113', 'R114', 'R115', 'R116', 'TP103']),
]

# Scripted locked copper: (id, net, layer, width, path); paths end on pad centres.
BATT_W, PWR3A_W, NECK_W, HOTROD_W = 3.2, 1.85, 1.6, 0.3
TRUNKS = [
    ('SHUNTP', 'E1_SHUNT_P', 'F.Cu', BATT_W, [('J105', '2'), ('XR101', '1')]),
    ('N-BUS', 'E1_N', 'F.Cu', BATT_W, [('XR101', '2'), (56.0, 3.2), (56.0, Y_P1), ('XU106A', '1')]),
    ('N-MOD2', 'E1_N', 'F.Cu', NECK_W, [('XU106A', '1'), ('XU106A', '2')]),
    ('N-F103', 'E1_N', 'F.Cu', BATT_W, [(29.4, 3.2), ('F103', '1')]),
    ('N-J108', 'E1_N', 'F.Cu', BATT_W, [(56.0, 17.0), ('J108', '2')]),
    ('SW-OUT', 'E1_SW', 'F.Cu', BATT_W, [('XU106B', '1'), (X_VOUT, 31.0), ('XJC1', '2')]),
    ('SW-MOD2', 'E1_SW', 'F.Cu', NECK_W, [('XU106B', '1'), ('XU106B', '2')]),
    ('SERV', 'E1_SERVICE_P', 'F.Cu', PWR3A_W, [('F103', '2'), ('J115', '2')]),
    ('PD-RAW', 'E1_USB_PD_RAW', 'F.Cu', PWR3A_W, [('J114', '2'), (140.33, 18.5), (138.75, 18.5)]),
    ('PD-RAW-IN', 'E1_USB_PD_RAW', 'F.Cu', HOTROD_W, [(138.75, 18.5), ('U109', '5')]),
    ('PD-SAFE-OUT', 'E1_USB_PD_SAFE', 'F.Cu', HOTROD_W, [('U109', '6'), (139.25, 11.5)]),
    ('PD-SAFE', 'E1_USB_PD_SAFE', 'F.Cu', PWR3A_W, [(139.25, 11.5), (139.25, 4.6), (69.6, 4.6), (69.6, 22.5),
                                                   ('J108', '3')]),
]


def r4(v):
    return round(float(v) + 0.0, 4)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


class Inputs:
    def __init__(self):
        self.graph = bg.load_graph()
        self.manifest = bg.read_json(bg.MANIFEST)
        self.fps = {f['footprint']: f for f in self.manifest['footprints']}
        self.netclasses = read(NETCLASSES)
        self.cfile = read(CONTRACT)
        self.contract = self.cfile['boards'][BOARD]
        self.outline = [tuple(p) for p in self.contract['outline_mm']]
        part = read(PARTITION)
        self.refs = sorted((p['ref'] for p in part['parts'] if p['board_candidate'] == 'PWR_ENTRY' and not p['dnp']),
                           key=bg.sort_ref)
        self.text, self.fpid = {}, {}
        for r in self.refs:
            fp = self.graph[r]['footprint']
            self.fpid[r] = fp
            self.text[r] = (BASE / self.fps[fp]['file']).read_text(encoding='utf-8')
        for r, ph in PLACEHOLDERS.items():
            self.fpid[r] = ph['fp']
            self.text[r] = (IMG / (ph['fp'].split(':', 1)[1] + '.kicad_mod')).read_text(encoding='utf-8')
        self.nets_of = {}
        for r in self.refs:
            self.nets_of[r] = {str(p['number']): p.get('net') for p in self.graph[r]['pins'] if p.get('net')}
        for r, ph in PLACEHOLDERS.items():
            self.nets_of[r] = dict(ph['pins'])
        self.geo = {}
        for r, text in self.text.items():
            geo = bg.footprint_geometry(text)
            keep = []
            for p, (cu, fbox) in zip(geo['pads'], mb.pad_copper(text)):
                if cu or p['type'] == 'np_thru_hole':
                    keep.append({**p, 'fbox': fbox})
            self.geo[r] = {**geo, 'pads': keep}


def anchor_of(at, rot):
    return {'at': [r4(at[0]), r4(at[1])], 'align': 'origin', 'rotation': rot, 'side': 'F'}


def spec_parts(inp):
    parts = []
    grouped = {m for _, _, ms in GROUPS for m in ms}
    for r in inp.refs + sorted(PLACEHOLDERS):
        if r in PLACEHOLDERS:
            ph = PLACEHOLDERS[r]
            lib, name = ph['fp'].split(':', 1)
            proj = ph['fp'] in inp.fps  # vendored in the project library: no fp-lib-table clash with the graph parts
            parts.append({'source': 'pilot_placeholder', 'ref': r, 'footprint': ph['fp'],
                          'footprint_library': 'project' if proj else 'kicad-image',
                          'footprint_sha256': bg.sha256_file(IMG / f'{name}.kicad_mod'),
                          'footprint_sha256_source': ('build/kicad/footprints/manifest.json (KiCad 10.0.7 official, '
                                                      'unmodified)') if proj else SRC_LIB.format(lib=lib, name=name),
                          'value': ph['value'], 'pins': dict(ph['pins']), 'replaced_by': ph['replaced_by'],
                          'pending': ph['pending'], 'anchor': anchor_of(ANCHORS[r][:2], ANCHORS[r][2]),
                          'anchor_source': f'{TAG}: make_spec.py ANCHORS (design choice)'})
        elif r in grouped:
            parts.append({'ref': r, 'source': 'graph'})
        else:
            if r not in ANCHORS:
                raise SystemExit(f'make_spec: {r} has neither an anchor nor a group')
            parts.append({'ref': r, 'source': 'graph', 'anchor': anchor_of(ANCHORS[r][:2], ANCHORS[r][2]),
                          'anchor_source': f'{TAG}: make_spec.py ANCHORS (design choice)'})
    return parts


def groups_json():
    out = []
    for gid, region, members in GROUPS:
        out.append({'id': gid, 'region': region, 'side': 'F', 'gap_mm': 0.4,
                    'members': [{'ref': m, 'rotation': 0} for m in members]})
    return out


def template_of(inp, parts):
    """Template rows as board_gen.resolve() makes them (graph pads by number, placeholders by their pins)."""
    rows = []
    for p in parts:
        r = p['ref']
        rows.append({'ref': r, 'anchor': p.get('anchor'), 'pads': inp.nets_of[r]})
    return rows


def plan(inp, parts):
    """Group anchors as board_gen computes them in CI (place_groups, deterministic)."""
    spec = {'groups': groups_json(), 'parts': parts}
    holes = [{'ref': f'H{i}', 'at': list(h), 'd': inp.contract['hole_d'], 'keepout_d': inp.contract['hole_keepout_d']}
             for i, h in enumerate(inp.contract['holes_mm'], 1)]
    template = [{'ref': p['ref'], 'anchor': p.get('anchor')} for p in parts]
    geometry = {r: bg.footprint_geometry(inp.text[r]) for r in inp.text}
    cut = [[x, y, x + w, y + h] for x, y, w, h in inp.contract.get('cutouts_mm', [])]
    # exactly what board_gen.group_plan does in CI (contract cut-outs only); the regions avoid MODULE_BODY themselves
    anchors, rows = bg.place_groups(spec, template, geometry, holes, inp.contract['outline_mm'], cut)
    return anchors, rows


def placed_all(inp, parts, anchors):
    out = {}
    for p in parts:
        a = p.get('anchor') or anchors[p['ref']]
        out[p['ref']] = mb.Placed(p['ref'], inp.geo[p['ref']], a, inp.nets_of[p['ref']])
    return out


def pad_at(placed, ref, num):
    for p in placed[ref].pads:
        if p['number'] == num:
            return p['at']
    raise SystemExit(f'make_spec: {ref} has no pad {num}')


def trunks(placed):
    tracks = []
    for tid, net, layer, w, pts in TRUNKS:
        path = [list(pad_at(placed, *pt)) if isinstance(pt[0], str) else list(pt) for pt in pts]
        tracks.append({'id': f'CU-{tid}', 'net': net, 'layer': layer, 'width_mm': w,
                       'path': [[r4(x), r4(y)] for x, y in path], 'locked': True,
                       'why': f'{TAG}: scripted battery-path copper (make_spec.py TRUNKS); the router joins only branches'})
    return tracks


def box_overlap(a, b, gap=0.0):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def problems(inp, placed, tracks):
    out = []
    outline = inp.outline
    cuts = [[x, y, x + w, y + h] for x, y, w, h in inp.contract.get('cutouts_mm', [])]
    holes = [tuple(h) for h in inp.contract['holes_mm']]
    kr = inp.contract['hole_keepout_d'] / 2
    refs = sorted(placed)
    for i, a in enumerate(refs):
        A = placed[a].box
        if not all(bg.point_in_outline(c, outline) for c in ((A[0], A[1]), (A[2], A[1]), (A[2], A[3]), (A[0], A[3]))):
            out.append(f'{a}: courtyard {[round(v, 2) for v in A]} leaves the outline')
        for c in cuts:
            if box_overlap(A, c):
                out.append(f'{a}: courtyard in the vent cut-out')
        if not a.startswith('XU106') and box_overlap(A, MODULE_BODY):
            out.append(f'{a}: courtyard under the #2813 body {MODULE_BODY}')
        for hx, hy in holes:
            dx = max(A[0] - hx, 0, hx - A[2])
            dy = max(A[1] - hy, 0, hy - A[3])
            if math.hypot(dx, dy) < kr - 1e-9:
                out.append(f'{a}: courtyard in the keepout of hole ({hx}, {hy})')
        for b in refs[i + 1:]:
            if {a, b} == {'XU106A', 'XU106B'}:
                continue
            if box_overlap(A, placed[b].box):
                out.append(f'{a} / {b}: courtyards overlap')
    for t in tracks:
        r = t['width_mm'] / 2
        for (x1, y1), (x2, y2) in zip(t['path'], t['path'][1:]):
            for ref, pa in placed.items():
                for p in pa.pads:
                    if p['net'] == t['net'] or (t['layer'][0] not in p['layers']):
                        continue
                    d = mb.seg_box_dist((x1, y1), (x2, y2), p['box'])
                    if d - r < mb.CLEAR + mb.MARGIN - 1e-6:
                        out.append(f'{t["id"]}: {round(d - r, 3)} mm to {ref}.{p["number"]} ({p["net"]})')
            for q in ((x1, y1), (x2, y2)):
                if mb.edge_dist(q, outline) - r < mb.EDGE + mb.MARGIN:
                    out.append(f'{t["id"]}: closer than the edge clearance at {q}')
    return out


def project_json(inp, nets):
    proj = read(ENC_PROJECT)
    proj['meta']['filename'] = 'PWR_C.kicad_pro'
    nc = inp.netclasses
    default = proj['net_settings']['classes'][0]
    pd = nc['project_defaults']['values_mm']
    classes = []
    for name, width, clearance in (('Default', nc['classes']['SIG']['outer_min_width_mm'], nc['classes']['SIG']['clearance_mm']),
                                   ('PWR1A', nc['classes']['PWR1A']['outer_min_width_mm'], nc['classes']['PWR1A']['clearance_mm']),
                                   ('PWRC_BRANCH', 0.5, nc['classes']['BATT']['clearance_mm']),
                                   ('SCRIPTED_GND', nc['classes']['SIG']['outer_min_width_mm'], nc['classes']['SIG']['clearance_mm'])):
        row = copy.deepcopy(default)
        row['name'] = name
        row['track_width'] = width
        row['clearance'] = clearance
        row['via_diameter'] = mb.VIA_D
        row['via_drill'] = pd['via_hole']
        if name != 'Default':
            row['priority'] = len(classes) - 1
        classes.append(row)
    proj['net_settings']['classes'] = classes
    pats = []
    for n in sorted(nets):
        cls = (nc['nets'].get(n) or {}).get('class', 'SIG')
        if n == 'GND':
            pats.append({'netclass': 'SCRIPTED_GND', 'pattern': n})
        elif cls in ('BATT', 'PWR3A', 'PWR2A'):
            pats.append({'netclass': 'PWRC_BRANCH', 'pattern': n})
        elif cls == 'PWR1A':
            pats.append({'netclass': 'PWR1A', 'pattern': n})
    proj['net_settings']['netclass_patterns'] = pats
    rules = proj['board']['design_settings']['rules']
    rules['min_track_width'] = pd['track_width']
    rules['min_clearance'] = pd['clearance']
    rules['min_copper_edge_clearance'] = pd['edge_clearance']
    rules['min_hole_to_hole'] = pd['hole_to_hole']
    return json.dumps(proj, indent=2) + '\n'


def branch_exempt(inp, placed, tracks):
    """Refs whose pads on a power-class net take router branches narrower than the class (0.5 mm PWRC_BRANCH)."""
    nc = inp.netclasses
    power = {n for n, c in nc['nets'].items() if c.get('class') in ('BATT', 'PWR3A', 'PWR2A')}
    out = {}
    for ref, pa in sorted(placed.items(), key=lambda kv: bg.sort_ref(kv[0])):
        nets = sorted({p['net'] for p in pa.pads if p['net'] in power})
        if not nets:
            continue
        out[ref] = {'max_mm': 40.0, 'min_width_mm': 0.5,
                    'reason': f'{TAG}: router branch of {", ".join(nets)} at the 0.5 mm PWRC_BRANCH width to a pad that the '
                              'class width does not enter; the high-current path is the scripted copper (make_spec.py '
                              'TRUNKS); the branch carries the current of this part only (divider, LDO, TVS, test point, '
                              'sense or a header contact whose full current the scripted copper does not carry: OPEN, '
                              'see README)'}
    return out


def build():
    inp = Inputs()
    parts = spec_parts(inp)
    anchors, rows = plan(inp, parts)
    placed = placed_all(inp, parts, anchors)
    tracks = trunks(placed)
    pre = {'tracks': tracks, 'vias': [], 'zones': [
        {'id': 'GND-In1', 'net': 'GND', 'layer': 'In1.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
         'why': 'GND plane (layer type power: a plane in the DSN); joined by the scripted via of every SMD GND pad'},
        {'id': 'GND-In2', 'net': 'GND', 'layer': 'In2.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
         'why': 'second GND plane, as PWR_A'}]}
    fan_inp = SimpleNamespace(contract=inp.contract, parts=placed, outline=inp.outline)
    gt, gv, skipped = mb.gnd_fanout(fan_inp, pre)
    pre['tracks'] = tracks + gt
    pre['vias'] = gv
    nets = set()
    for r, ns in inp.nets_of.items():
        nets |= {n for n in ns.values() if n}
    probs = problems(inp, placed, tracks)
    refs_map = {r: (r if r in inp.refs else None) for r in inp.refs + sorted(PLACEHOLDERS)}
    pwra = read(PWRA_SPEC)
    spec = {
        'schema': bg.SPEC_SCHEMA, 'board_id': BOARD,
        'status': 'PROBE_W2_PWRJ_F2C_NOT_FOR_FABRICATION',
        'title': 'PWR-C front-slab power-entry board (F2-C): E1 battery front end, INA228 shunt, Pololu #2813, E5 IMU service',
        'note': (f'{TAG} (wip/w2-pwrj-f2c, never merged): generated by build/kicad/boards/PWR_C/make_spec.py; outline, '
                 'holes and the vent cut-out come from build/kicad/boards/PWR_C/contract-proposal.json (no PWR_C entry in '
                 'the mechanical contract). CI/MODEL output only; every bench gate stays OPEN.'),
        'contract': {'file': 'build/kicad/boards/PWR_C/contract-proposal.json', 'board': BOARD},
        'domains': ['PWR_ENTRY'], 'partition': 'pcb/generated/partition.json',
        'layers': {'copper': 4, 'thickness_mm': 1.6,
                   'source': "as PWR-A: JLC04161H-7628, 1 oz outer / 0.5 oz inner (build/15 'Шари')",
                   'plan': {'F.Cu': 'parts, signals, the scripted battery-path copper', 'In1.Cu': 'GND plane',
                            'In2.Cu': 'GND plane', 'B.Cu': 'signals'},
                   'types': {'In1.Cu': 'power', 'In2.Cu': 'power'},
                   'types_why': 'plane layers in the DSN, as PWR_A and PWR_B: Freerouting puts only vias through them'},
        'project': 'build/kicad/boards/PWR_C/PWR_C.kicad_pro',
        'rules_file': None,
        'rules_note': 'the rules live in the committed project file (as PWR_A): project defaults of pcb/generated/netclasses.json, '
                      'classes Default (SIG), PWR1A, PWRC_BRANCH 0.5 mm and SCRIPTED_GND',
        'fab_floor': pwra['fab_floor'],
        'instances': {'template_nets': sorted(nets),
                      'list': [{'id': 'PWRC', 'placement': 'default', 'qty': 1, 'refs': refs_map,
                                'nets': {n: n for n in sorted(nets)},
                                'source': 'identity map: the PWR_ENTRY refs of pcb/generated/partition.json and the pilot '
                                          'placeholders of make_spec.py'}],
                      'spares': 0, 'spares_source': 'one board per device'},
        'parts': parts,
        'holes': {'from_contract': True, 'ref_prefix': 'H', 'keepout_layers': ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'],
                  'keepout_blocks': ['tracks', 'vias', 'zone_fills']},
        'groups': groups_json(),
        'pre_route': pre,
        'post_route_zones': [],
        'edge_keepout': {'width_mm': 0.2, 'layers': ['F.Cu', 'B.Cu'], 'blocks': ['tracks', 'vias'],
                         'why': 'rule-area strips (half-width 0.2) on every outline and cut-out edge, as PWR_A and PWR_B'},
        'router': {'tool': 'freerouting', 'max_passes': 60, 'threads': 1, 'job_timeout': '00:20:00', 'timeout_s': 1320,
                   'fanout': False, 'ignore_net_classes': ['SCRIPTED_GND'],
                   'why': 'as PWR_A: no fan-out pre-pass; GND joins the planes through the scripted vias (SCRIPTED_GND not '
                          'autorouted)'},
        'drc_policy': pwra['drc_policy'],
        'branch_exempt': branch_exempt(inp, placed, tracks),
        'neck_exempt': {r: {'escape_mm': 3.0, 'reason': f'{TAG}: the 1.6 mm entry of the scripted battery copper between '
                                                         'the two 0.1 in header pins of a #2813 power node (TRUNKS N-MOD2, '
                                                         'SW-MOD2); the pins share the module current'}
                        for r in ('XU106A', 'XU106B')},
        'gnd_fanout': {'vias': len(gv), 'stubs': len(gt), 'pads_joined_by_scripted_gnd_pours': skipped,
                       'rule': 'build/kicad/boards/PWR_A/make_board.py gnd_fanout: stub 0.25 mm to a 0.7 / 0.3 via'},
        'module_body_keepout': {'rect': MODULE_BODY, 'why': 'Pololu #2813 (psw03b: 20.3 x 25.4 mm, PCB 1.57 mm, parts '
                                'to 2.4 mm above it) flush on its header columns: no PWR-C part under it'},
        'generator': 'build/kicad/boards/PWR_C/make_spec.py',
    }
    bg.validate_spec(spec, BOARD)
    return spec, project_json(inp, nets), probs, placed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--draft', action='store_true')
    args = ap.parse_args(argv)
    spec, proj, probs, placed = build()
    for p in probs:
        print('PROBLEM', p)
    text = json.dumps(spec, ensure_ascii=False, indent=2) + '\n'
    print(f'{len(probs)} problem(s); {len(spec["parts"])} parts; {len(spec["pre_route"]["tracks"])} tracks; '
          f'{len(spec["pre_route"]["vias"])} vias')
    if args.draft:
        return 0
    if args.check:
        ok = SPEC.is_file() and SPEC.read_text(encoding='utf-8') == text and PROJECT.is_file() and \
            PROJECT.read_text(encoding='utf-8') == proj
        print('PWR_C spec and project', 'reproduce' if ok else 'are stale: rerun build/kicad/boards/PWR_C/make_spec.py')
        return 0 if ok else 1
    if probs:
        print('make_spec: not written while problems remain')
        return 1
    SPEC.write_text(text, encoding='utf-8', newline='\n')
    PROJECT.write_text(proj, encoding='utf-8', newline='\n')
    print('wrote pcb/boards/PWR_C.json and build/kicad/boards/PWR_C/PWR_C.kicad_pro')
    return 0


if __name__ == '__main__':
    sys.exit(main())
