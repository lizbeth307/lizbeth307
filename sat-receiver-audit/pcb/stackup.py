#!/usr/bin/env python3
"""Stackup, impedance and current-width calculators; net classes and JLC DRC rule files (MODEL values).

Run from any directory: python pcb/stackup.py [--check]
Writes pcb/generated/netclasses.json, pcb/rules/jlc-4l-1oz.kicad_dru and pcb/rules/jlc-2l.kicad_dru;
--check compares them with the committed files. Stdlib only; no CI job runs --check yet (PCB-FAB wires it into sr-rx-pcb).

Nothing here is a measurement. The impedance is a closed-form quasi-static model (t = 0, no solder mask),
the widths are the IPC-2221 curve fit, the via current is a barrel cross-section estimate. The finished
impedance (coupon TDR), the trace and via temperature rise stay bench gates (OPEN).
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / 'pcb/generated/netclasses.json'
OUT_RULES = {'4l': ROOT / 'pcb/rules/jlc-4l-1oz.kicad_dru', '2l': ROOT / 'pcb/rules/jlc-2l.kicad_dru'}
ASSEMBLY_DATA = ROOT / 'tools/assembly_data.py'
GRAPHS = [ROOT / f'design/E{i}.json' for i in range(1, 6)]
CONSTRAINTS = ROOT / 'pcb/generated/constraints.json'

READ = '2026-11-07'
URL_STACKUP = 'https://jlcpcb.com/impedance'
URL_CAPS = 'https://jlcpcb.com/capabilities/pcb-capabilities'
URL_CPW = 'https://qucs.sourceforge.net/tech/node86.html'
URL_IPC_K = 'https://www.digikey.ca/en/resources/conversion-calculators/conversion-calculator-pcb-trace-width'
URL_IPC_A = 'https://jlcpcb.com/blog/pcb-trace-width-guide'
URL_IPC2221B = 'https://shop.ipc.org/ipc-2221/ipc-2221-standard-only'
MIL = 0.0254  # mm per mil

# --- JLC04161H-7628, 4 layers 1.6 mm (jlcpcb.com/impedance, read 2026-11-07). The page names the stackup
# "JLC04161H-7628" and lists: Top copper 0.035 mm; prepreg 7628x1 0.21040 mm, Dk 4.4; inner copper 0.0152 mm;
# core 1.065 mm, "Core dielectric constant 4.6"; inner copper 0.0152; prepreg 0.21040; bottom copper 0.035.
# Solder mask: C1 1.2 mil, C2 0.6 mil, C3 1.2 mil, CEr 3.8. The page states no impedance tolerance.
STACKUP = {
    'id': 'JLC04161H-7628', 'board_thickness_mm': 1.6, 'source': URL_STACKUP, 'read': READ,
    'layers': [
        {'kicad': 'F.Cu', 'plan': 'L1', 'copper_mm': 0.035},
        {'dielectric': 'prepreg 7628x1', 'thickness_mm': 0.2104, 'er': 4.4},
        {'kicad': 'In1.Cu', 'plan': 'L2', 'copper_mm': 0.0152},
        {'dielectric': 'core', 'thickness_mm': 1.065, 'er': 4.6},
        {'kicad': 'In2.Cu', 'plan': 'L3', 'copper_mm': 0.0152},
        {'dielectric': 'prepreg 7628x1', 'thickness_mm': 0.2104, 'er': 4.4},
        {'kicad': 'B.Cu', 'plan': 'L4', 'copper_mm': 0.035},
    ],
    'solder_mask': {'c1_above_substrate_mil': 1.2, 'c2_above_trace_mil': 0.6, 'c3_between_traces_mil': 1.2, 'er': 3.8},
    'note': 'Layer thicknesses sum to 1.5862 mm (computed). Copper weights: outer 0.035 mm = 1 oz, inner 0.0152 mm = 0.5 oz finished (JLC "H/HOZ").',
}
OUTER_CU, INNER_CU, PREPREG_H, PREPREG_ER = 0.035, 0.0152, 0.2104, 4.4

# --- JLC rigid PCB capabilities (jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-07). Hard floors.
# key: (multilayer 1 oz value, 2-layer 1 oz value, quoted row)
CAPS = {
    'track_width_min': (0.09, 0.10, 'Min. track width and spacing (1 oz): multilayer 0.09/0.09 mm; 1- and 2-layer 0.10/0.10 mm'),
    'track_spacing_min': (0.09, 0.10, 'Min. track width and spacing (1 oz): multilayer 0.09/0.09 mm; 1- and 2-layer 0.10/0.10 mm'),
    'pad_to_track_min': (0.10, 0.10, 'Pad to track clearance (1oz): 0.1 mm'),
    'smd_pad_to_pad_min': (0.15, 0.15, 'SMD pad to pad clearance (different nets): 0.15 mm'),
    'via_hole_min': (0.15, 0.15, 'Min. via hole size/diameter: 0.15/0.25 mm (multilayer and 2-layer)'),
    'via_diameter_min': (0.25, 0.25, 'Min. via hole size/diameter: 0.15/0.25 mm (multilayer and 2-layer)'),
    'pth_annular_min': (0.15, 0.18, 'PTH annular ring: multilayer 1 oz absolute minimum 0.15 mm, recommended 0.20; 2-layer 1 oz absolute minimum 0.18, recommended 0.25'),
    'pth_annular_recommended': (0.20, 0.25, 'PTH annular ring: multilayer 1 oz recommended 0.20 mm; 2-layer 1 oz recommended 0.25 mm'),
    'via_hole_to_hole_min': (0.20, 0.20, 'Via hole-to-hole spacing: 0.2 mm'),
    'pad_hole_to_hole_min': (0.45, 0.45, 'Pad hole-to-hole spacing: 0.45 mm'),
    'via_hole_to_track_min': (0.20, 0.20, 'Via hole to Track: 0.2 mm'),
    'pth_to_track_min': (0.28, 0.28, 'PTH to Track: 0.35 mm is recommended, minimum 0.28 mm'),
    'pth_to_track_recommended': (0.35, 0.35, 'PTH to Track: 0.35 mm is recommended'),
    'npth_to_track_min': (0.20, 0.20, 'NPTH to Track: 0.2 mm'),
    'inner_via_hole_to_copper_min': (0.20, None, 'Inner layer via hole to copper clearance: 0.2 mm'),
    'inner_pth_hole_to_copper_min': (0.30, None, 'Inner layer PTH pad hole to copper clearance: 0.3 mm'),
    'copper_to_routed_edge_min': (0.20, 0.20, 'Copper clearance from routed board edges: >=0.2 mm'),
    'npth_hole_min': (0.50, 0.50, 'Min. Non-plated holes: 0.50 mm'),
    'pth_drill_max': (6.3, 6.3, 'PTH drill diameter range 0.15 mm to 6.3 mm (holes >=6.3 mm are CNC routed)'),
    'plated_slot_min': (0.35, 0.50, 'Min. plated slot width: multi-layer 0.35 mm; 2-layer 0.5 mm'),
    'silk_line_min': (0.15, 0.15, 'Silkscreen min. line width >=0.15 mm'),
    'silk_text_height_min': (1.0, 1.0, 'Silkscreen min. text height 40 mil (1.0 mm)'),
    'mask_bridge_min': (0.10, 0.10, 'Solder mask bridge 0.10 mm (1 oz, green and other colours); 0.13 mm black/white'),
    'hole_wall_plating_mm': (0.018, 0.018, 'Hole wall (average plating) thickness 18 um'),
    'impedance_tolerance_pct': (10, 10, 'Impedance control tolerance +/-10 % standard; +/-5 % on special request'),
}

# --- Project defaults: the JLC floor plus margin (project choice). Values in mm.
PROJECT = {
    'track_width': 0.15, 'clearance': 0.15, 'via_hole': 0.30, 'via_diameter': 0.60, 'via_annular': 0.15,
    'hole_to_hole': 0.50, 'via_hole_clearance': 0.25, 'pth_hole_clearance': 0.35, 'npth_hole_clearance': 0.30,
    'edge_clearance': 0.30, 'pth_hole_min': 0.30, 'text_height': 1.0, 'text_thickness': 0.15,
}
PROJECT_WHY = {
    'track_width': 'JLC floor 0.09 (multilayer) / 0.10 (2-layer); 0.15 leaves etch margin',
    'clearance': 'JLC 0.09 track/track, 0.10 pad/track, 0.15 SMD pad/pad (floor)',
    'via': '0.3/0.6 against the JLC floor 0.15/0.25; annulus 0.15 mm',
    'hole_to_hole': 'JLC pad hole-to-hole 0.45, via hole-to-hole 0.2',
    'via_hole_clearance': 'JLC via hole to track 0.2; inner via hole to copper 0.2',
    'pth_hole_clearance': 'JLC PTH to track 0.28 min / 0.35 recommended; inner PTH hole to copper 0.3',
    'npth_hole_clearance': 'JLC NPTH to track 0.2',
    'edge_clearance': 'JLC copper to routed edge >=0.2',
    'pth_hole_min': 'project: no PTH smaller than the via drill',
    'text': 'equal to the JLC silkscreen floor (1.0 mm text, 0.15 mm line)',
}

# --- IPC-2221 curve fit I = k * dT^0.44 * A^0.725 (A in mil^2): k 0.048 external, 0.024 internal
# (DigiKey trace-width calculator: "For IPC-2221 external layers: k = 0.048, b = 0.44, c = 0.725", internal
# k = 0.024; read 2026-11-07). Width = A / copper thickness (JLC blog: A = (I/(k*dT^0.44))^(1/0.725),
# "1 oz copper, 1.378 mil thick"; read 2026-11-07). Copper thickness here: JLC04161H-7628 values above.
IPC_K = {'external': 0.048, 'internal': 0.024}
IPC_B, IPC_C = 0.44, 0.725


def ipc2221_area_mil2(current, dt, layer='external'):
    return (current / (IPC_K[layer] * dt ** IPC_B)) ** (1 / IPC_C)


def ipc2221_width_mm(current, dt, copper_mm=OUTER_CU, layer='external'):
    """IPC-2221 width (mm) for a current (A) at a temperature rise dt (degC) on copper of copper_mm."""
    if current <= 0:
        return 0.0
    return ipc2221_area_mil2(current, dt, layer) / (copper_mm / MIL) * MIL


def ipc2221_current(area_mil2, dt, layer='external'):
    return IPC_K[layer] * dt ** IPC_B * area_mil2 ** IPC_C


# --- Conductor-backed CPW (grounded CPW), quasi-static conformal mapping, t = 0, lateral grounds to infinity.
# k1 = W/(W+2s); k3 = tanh(pi W/4h)/tanh(pi (W+2s)/4h); eps_re = 1 + q(eps_r - 1),
# q = (K(k3)/K'(k3)) / (K(k1)/K'(k1) + K(k3)/K'(k3)); Z = 60 pi / sqrt(eps_re) / (K(k1)/K'(k1) + K(k3)/K'(k3)).
# As read in the QUCS technical documentation (qucs.sourceforge.net/tech/node86.html, 2026-11-07); the textbook
# form is in R. N. Simons, Coplanar Waveguide Circuits, Components, and Systems (Wiley 2001), conductor-backed CPW.
def ellipk(k):
    """Complete elliptic integral of the first kind K(k) (modulus k) by the arithmetic-geometric mean."""
    a, b = 1.0, math.sqrt(1.0 - k * k)
    for _ in range(64):
        if abs(a - b) < 1e-15:
            break
        a, b = (a + b) / 2, math.sqrt(a * b)
    return math.pi / (2 * a)


def cbcpw(w, s, h, er):
    """(Z0 ohm, eps_eff) of a conductor-backed CPW: strip w, gaps s, dielectric h to the ground plane, eps_r er."""
    k1 = w / (w + 2 * s)
    k3 = math.tanh(math.pi * w / (4 * h)) / math.tanh(math.pi * (w + 2 * s) / (4 * h))
    r1 = ellipk(k1) / ellipk(math.sqrt(1 - k1 * k1))
    r3 = ellipk(k3) / ellipk(math.sqrt(1 - k3 * k3))
    eps = 1 + (er - 1) * r3 / (r1 + r3)
    return 60 * math.pi / math.sqrt(eps) / (r1 + r3), eps


def via_current(drill, plating, dt):
    """Barrel ampacity (A): the plated cross-section pi*((d/2+t)^2-(d/2)^2) with the IPC-2221 internal fit
    (project method, conservative for an embedded barrel)."""
    area_mm2 = math.pi * ((drill / 2 + plating) ** 2 - (drill / 2) ** 2)
    return ipc2221_current(area_mm2 / MIL ** 2, dt, 'internal')


def up(value, step=0.05):
    """Round a width up to the next step (mm), so a class width never falls below its requirement."""
    return round(math.ceil(round(value / step, 6)) * step, 3)


# --- Rule inputs (project choices, labelled in the output).
DT_CONT, DT_PROT = 10, 20  # degC: continuous current at +10 degC, protective/limit current at +20 degC
SPLIT_SHARE = 2 / 3        # two outer layers in parallel: each sized for 2/3 of the current (unequal split up to 2:1)
SIG_MAX_A = 0.10           # nets at or below this current (both values) stay SIG
RF = {'w': 0.36, 's': 0.20, 'h': PREPREG_H, 'er': PREPREG_ER, 'w_tol': 0.005, 's_ground_tol': 0.05,
      'l2_band_h': 3, 'fence_pitch_max': 2.0, 'fence_row_max_from_gap': 1.0}
DCTAP = {'width': 0.20, 'clearance': 0.30}
# KiCad rule areas (zone names, wildcard as in A.intersectsArea) for the spec exemptions of pcb/check_boards.py:
# low-current branches of power nets (Kelvin sense, decoupling stubs) and RF50 tapers into IC pins (project rule).
BRANCH_AREA, TAPER_AREA = 'PWR_BRANCH*', 'RF_TAPER*'
VIA_ADVISORY = 'advisory design value: neither KiCad DRC nor pcb/check_boards.py counts vias per transition (review.json lists it under unverified)'

CLASS_CAPACITY = collections.OrderedDict([
    # class: (continuous A at DT_CONT, protective A at DT_PROT, why, split allowed, inner layers carry current)
    ('PWR1A', (1.0, 1.0, 'TPS2553 limits <=0.989 A (VBUS_HFP) and eFuse limits <=1 A', False, True)),
    ('PWR2A', (2.0, 2.2, 'eFuse U203 limit 1.80-2.20 A (LIME3V3)', False, True)),
    ('PWR3A', (3.2, 5.0, 'LAB5 budget 3.2 A (E1-05) and F103 5 A (E1_SERVICE_P)', True, False)),
    ('BATT', (4.6, 7.5, 'battery path 4.6 A model and F101 7.5 A', True, False)),
])
POWER_CLASSES = list(CLASS_CAPACITY)
RF_PIN_NAMES = {
    'ic': {'RF1', 'RF2', 'RF3', 'RF4', 'RFC'},
    'connector': {'CENTER'},
    'relay': {'COM1', 'COM2', 'NO1', 'NO2', 'NC1', 'NC2'},
    'module': {'ANT', 'RF', 'RF_DC', 'RF_IN', 'RF_OUT', 'IF', 'END_A', 'END_B', 'EDGE', 'PAD', 'PANEL', 'LNA', 'FILTER',
               'BLOCK', 'IN_CENTER', 'OUT_CENTER', 'SMA_IN', 'SMA_OUT', 'SMA_A', 'SMA_B', 'SMA_F_A', 'SMA_F_B', 'X1_TX',
               'X2_RX', 'X4_RX', 'J4_REF_IN', 'REF25'},
    'module_e4': {'IN', 'OUT'},
}
DCTAP_NET = re.compile(r'^E4_DCS_(UHF|LBAND|HF)_(TAP|BLEED_\d+)$')
GROUND_NETS = {'GND', 'CHASSIS'}
SUPPLY_PINS = {'VSYS', 'VBUS', '5V', '5V_IN', '3V3_OUT', '+5V'}
PATH_PINS = {'IN', 'VIN', 'OUT', 'OUTS', 'VOUT'}  # only on parts that have an IN/VIN pin (regulators, switches, eFuses)


def rel(path):
    return path.relative_to(ROOT).as_posix()


def assembly_currents():
    """NET_CURRENT / SEG_CURRENT literals of tools/assembly_data.py with the line of each entry (no import)."""
    tree = ast.parse(ASSEMBLY_DATA.read_text(encoding='utf-8'))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ('NET_CURRENT', 'SEG_CURRENT'):
            entries = []
            for key, value in zip(node.value.keys, node.value.values):
                entries.append((ast.literal_eval(key), ast.literal_eval(value), key.lineno))
            found[node.targets[0].id] = entries
    if set(found) != {'NET_CURRENT', 'SEG_CURRENT'}:
        raise SystemExit('stackup: NET_CURRENT/SEG_CURRENT not found in tools/assembly_data.py')
    return found


def graph():
    comps = []
    for path in GRAPHS:
        sheet = json.loads(path.read_text(encoding='utf-8'))
        for c in sheet['components']:
            comps.append({**c, '_sheet': path.stem})
    nets = collections.defaultdict(list)
    for c in comps:
        for p in c['pins']:
            if p.get('net'):
                nets[p['net']].append((c['ref'], str(p['number']), p['name']))
    return comps, nets


def required_width(cont, prot, copper=OUTER_CU, layer='external', share=1.0):
    return max(ipc2221_width_mm(cont * share, DT_CONT, copper, layer), ipc2221_width_mm(prot * share, DT_PROT, copper, layer))


def class_table():
    plating = CAPS['hole_wall_plating_mm'][0]
    i10, i20 = via_current(PROJECT['via_hole'], plating, DT_CONT), via_current(PROJECT['via_hole'], plating, DT_PROT)
    classes = collections.OrderedDict()
    classes['SIG'] = {
        'kind': 'signal', 'capacity': f'<= {SIG_MAX_A} A (both values); logic and unlisted nets (assembly_data: "Signals not listed: 0.05 A")',
        'outer_min_width_mm': PROJECT['track_width'], 'inner_min_width_mm': PROJECT['track_width'], 'clearance_mm': PROJECT['clearance'],
        'vias_per_transition': 1, 'basis': 'project default (JLC floor + margin)'}
    for name, (cont, prot, why, split, inner) in CLASS_CAPACITY.items():
        outer = up(required_width(cont, prot))
        entry = {
            'kind': 'power', 'capacity': {'continuous_a': cont, 'continuous_dt_c': DT_CONT, 'protective_a': prot, 'protective_dt_c': DT_PROT, 'why': why},
            'outer_min_width_mm': outer,
            'outer_ipc_width_mm': round(required_width(cont, prot), 4),
            'split_outer_per_layer_mm': up(required_width(cont, prot, share=SPLIT_SHARE)) if split else None,
            'inner_min_width_mm': up(required_width(cont, prot, INNER_CU, 'internal')) if inner else None,
            'inner_note': None if inner else ('inner 0.5 oz copper is not counted as current path for this class (outer layers carry it): '
                                              f'tracks of the class on inner layers are disallowed (.kicad_dru, except {BRANCH_AREA} rule areas) and a '
                                              'pcb/check_boards.py finding; inner pours are allowed and not counted'),
            'clearance_mm': PROJECT['clearance'],
            'vias_per_transition': max(math.ceil(round(cont / i10, 6)), math.ceil(round(prot / i20, 6))),
            'vias_per_transition_status': VIA_ADVISORY,
            'basis': 'IPC-2221 external k 0.048 on 1 oz (0.035 mm), internal k 0.024 on 0.5 oz (0.0152 mm); width = max(at continuous, +10 degC; at protective, +20 degC)'}
        classes[name] = entry
    z0, eps = cbcpw(RF['w'], RF['s'], RF['h'], RF['er'])
    spread = [cbcpw(w, RF['s'], h, er)[0] for w in (0.34, 0.36, 0.38) for h in (RF['h'] * 0.9, RF['h'], RF['h'] * 1.1) for er in (4.2, 4.4, 4.6)]
    lam = 299.792458 / math.sqrt(eps)  # guided wavelength (mm) at 1 GHz
    classes['RF50'] = {
        'kind': 'rf', 'layer': 'F.Cu over In1.Cu GND (L1 over L2)', 'width_mm': RF['w'], 'width_tol_mm': RF['w_tol'],
        'gap_mm': RF['s'], 'coplanar_ground_within_mm': round(RF['s'] + RF['s_ground_tol'], 3),
        'model': {'z0_ohm': round(z0, 2), 'eps_eff': round(eps, 3), 'method': 'conductor-backed CPW closed form, t = 0, no solder mask (MODEL)',
                  'h_mm': RF['h'], 'er': RF['er'],
                  'sensitivity_ohm': [round(min(spread), 1), round(max(spread), 1)],
                  'sensitivity_inputs': 'w 0.34/0.36/0.38, h 0.2104 +/-10 %, er 4.2/4.4/4.6 (project tolerance assumption)',
                  'not_modelled': 'copper thickness 0.035 mm and solder mask (er 3.8) both lower Z0; magnitude not computed here'},
        'l2_solid_band_mm': round(RF['w'] / 2 + RF['l2_band_h'] * RF['h'], 4),
        'l2_solid_band_basis': 'no In1.Cu void within 3h (3 x 0.2104 mm) of either trace edge (project rule)',
        'fence_pitch_max_mm': RF['fence_pitch_max'], 'fence_row_max_from_gap_mm': RF['fence_row_max_from_gap'],
        'fence_basis': f'project rule: 2.0 mm <= lambda_g/20 up to {round(lam / 20 / RF["fence_pitch_max"], 2)} GHz (eps_eff {eps:.3f}); HMC isolation band in constraints.json RF-03 ends at 1.7 GHz',
        'order_note': 'order impedance control (JLC +/-10 % standard); finished impedance only from the coupon (bench, OPEN)',
        'clearance_mm': RF['s'], 'vias_per_transition': None}
    classes['DCTAP'] = {
        'kind': 'dc_tap', 'width_mm': DCTAP['width'], 'outer_min_width_mm': DCTAP['width'], 'inner_min_width_mm': DCTAP['width'],
        'clearance_mm': 'TBD',
        'clearance_ipc': f'TBD: IPC-2221B Table 6-1 not readable (paid standard, {URL_IPC2221B}; no readable copy found {READ})',
        'project_rule_clearance_mm': DCTAP['clearance'],
        'project_rule_note': 'project choice, not IPC-verified: 0.3 mm to any other net in the .kicad_dru until Table 6-1 is read',
        'envelope': '+/-30 V limited DC (pcb/generated/constraints.json DC-04)', 'vias_per_transition': 1,
        'basis': 'project choice 0.2 mm width (current is mA-level)'}
    via = {'drill_mm': PROJECT['via_hole'], 'plating_mm': plating, 'plating_source': f'{URL_CAPS} ({READ}): hole wall average plating 18 um',
           'current_a_dt10': round(i10, 3), 'current_a_dt20': round(i20, 3),
           'method': 'barrel cross-section with the IPC-2221 internal fit (project method, MODEL)'}
    return classes, via


def width_class(cont, prot):
    """Smallest power class whose outer width covers the net's requirement; SIG for logic currents."""
    if cont <= SIG_MAX_A and prot <= SIG_MAX_A:
        return 'SIG'
    need = required_width(cont, prot)
    for name, (ccont, cprot, *_rest) in CLASS_CAPACITY.items():
        if need <= up(required_width(ccont, cprot)) + 1e-9:
            return name
    raise SystemExit(f'stackup: {cont}/{prot} A needs {need:.3f} mm, more than the BATT class')


def rating_a(value):
    m = re.search(r'(\d+(?:\.\d+)?)\s*A(?![a-zA-Z])', value)
    return float(m[1]) if m else None


def ohms(value):
    # '15 mΩ', '0.330 Ω', '0.22R', '0.200R', '20mR' (graph value notation); the first value in the string.
    m = re.search(r'(\d+(?:\.\d+)?)\s*(m?)\s*(?:Ω|ohm|R(?![A-Za-z0-9]))', value)
    if not m:
        return None
    return float(m[1]) / (1000 if m[2] else 1)


def series_links(comps):
    """Two-pin series elements that carry one current: fuses, inductors and resistors <= 1 ohm (shunts, damping)."""
    links = []
    for c in comps:
        pins = [p for p in c['pins'] if p.get('net')]
        if len(c['pins']) != 2 or len(pins) != 2:
            continue
        a, b = pins[0]['net'], pins[1]['net']
        if a == b or a in GROUND_NETS or b in GROUND_NETS:
            continue
        if c['kind'] == 'fuse':
            links.append((a, b, c['ref'], rating_a(c['value']), 'fuse'))
        elif c['kind'] == 'inductor':
            links.append((a, b, c['ref'], None, 'inductor'))
        elif c['kind'] == 'resistor' and (ohms(c['value']) is not None and ohms(c['value']) <= 1.0):
            links.append((a, b, c['ref'], None, 'resistor <= 1 ohm'))
    return links


def rf_nets(comps):
    seeds = {}
    for c in comps:
        names = set(RF_PIN_NAMES.get(c['kind'], set()))
        if c['kind'] == 'module' and c['_sheet'] == 'E4':
            names |= RF_PIN_NAMES['module_e4']
        for p in c['pins']:
            if p.get('net') and p['name'] in names and p['net'] not in GROUND_NETS and not DCTAP_NET.match(p['net']):
                seeds.setdefault(p['net'], f"{c['ref']}.{p['name']}")
    found = dict(seeds)
    changed = True
    while changed:  # DC blocks: a two-pin capacitor between an RF net and another non-ground net
        changed = False
        for c in comps:
            pins = [p for p in c['pins'] if p.get('net')]
            if c['kind'] != 'capacitor' or len(c['pins']) != 2 or len(pins) != 2:
                continue
            a, b = pins[0]['net'], pins[1]['net']
            for x, y in ((a, b), (b, a)):
                if x in found and y not in found and y not in GROUND_NETS and not DCTAP_NET.match(y):
                    found[y] = f"DC block {c['ref']} from {x}"
                    changed = True
    return found


def build():
    currents = assembly_currents()
    comps, nets = graph()
    classes, via = class_table()
    src = rel(ASSEMBLY_DATA)
    out_nets = {}
    for net, (cont, prot, protection, source), line in currents['NET_CURRENT']:
        if net in out_nets:
            raise SystemExit(f'stackup: duplicate NET_CURRENT entry {net}')
        out_nets[net] = {'class': None, 'basis': 'NET_CURRENT', 'source': f'{src}:{line}',
                         'inputs': {'continuous_a': cont, 'protective_a': prot, 'protection': protection, 'current_source': source},
                         'in_graph': net in nets}
    for (seg, net), (cont, prot, protection, source), line in currents['SEG_CURRENT']:
        entry = out_nets.get(net)
        if entry is None:
            raise SystemExit(f'stackup: SEG_CURRENT net {net} has no NET_CURRENT entry')
        entry.setdefault('harness_segments', []).append({'segment': seg, 'continuous_a': cont, 'protective_a': prot, 'source': f'{src}:{line}'})
        # Board copper carries the whole net: a segment value above the net value raises it.
        entry['inputs']['continuous_a'] = max(entry['inputs']['continuous_a'], cont)
        entry['inputs']['protective_a'] = max(entry['inputs']['protective_a'], prot)
    # Series closure: a net that is not listed inherits the current of a listed neighbour through a series element,
    # bounded by the element's rating where the graph value names one (fuse "4 A").
    known = {n: (e['inputs']['continuous_a'], e['inputs']['protective_a']) for n, e in out_nets.items()}
    derived = {}
    links = series_links(comps)
    changed = True
    while changed:
        changed = False
        for a, b, ref, rating, kind in links:
            for x, y in ((a, b), (b, a)):
                if x not in known or y in out_nets:
                    continue
                cont, prot = known[x]
                if rating is not None:
                    cont, prot = min(cont, rating), min(prot, rating)
                old = known.get(y)
                if old is None or cont > old[0] + 1e-12 or prot > old[1] + 1e-12:
                    new = (max(cont, old[0]) if old else cont, max(prot, old[1]) if old else prot)
                    known[y] = new
                    derived[y] = {'class': None, 'basis': 'series element', 'source': 'design/E*.json',
                                  'inputs': {'continuous_a': new[0], 'protective_a': new[1],
                                             'via': f'{ref} ({kind}{", rating %g A" % rating if rating is not None else ""}) from {x}'},
                                  'in_graph': y in nets}
                    changed = True
    for n, e in {**out_nets, **derived}.items():
        cont, prot = e['inputs']['continuous_a'], e['inputs']['protective_a']
        e['class'] = width_class(cont, prot)
        e['required_outer_width_mm'] = round(required_width(cont, prot), 4)
    rf = rf_nets(comps)
    all_nets = {**out_nets, **derived}
    for n, why in sorted(rf.items()):
        e = all_nets.get(n)
        if e is None:
            all_nets[n] = {'class': 'RF50', 'basis': 'RF path', 'source': 'design/E*.json', 'inputs': {'rf_pin': why}, 'in_graph': True}
        else:  # a DC-biased RF line: RF50 geometry, its current requirement must fit the RF50 width
            e['current_class'] = e['class']
            e['class'] = 'RF50'
            e['inputs']['rf_pin'] = why
            e['rf50_current_ok'] = e['required_outer_width_mm'] <= RF['w']
    for n in sorted(nets):
        if DCTAP_NET.match(n):
            all_nets[n] = {'class': 'DCTAP', 'basis': 'DC tap', 'source': f'{rel(CONSTRAINTS)} DC-04',
                           'inputs': {'envelope': '+/-30 V limited DC', 'pins': [f'{r}.{name}' for r, _num, name in nets[n]]}, 'in_graph': True}
    # Review list for the NET_CURRENT owner: unclassified nets on a supply pin of an IC/module or on a series element.
    candidates = sorted({p['net'] for c in comps if c['kind'] in ('ic', 'module') for p in c['pins']
                         if p.get('net') and (p['name'] in SUPPLY_PINS
                                              or (p['name'] in PATH_PINS and {q['name'] for q in c['pins']} & {'IN', 'VIN'}))}
                        | {n for a, b, *_rest in links for n in (a, b)})
    unclassified = [n for n in candidates if n not in all_nets and n not in GROUND_NETS]
    missing = sorted(n for n, e in all_nets.items() if not e['in_graph'])
    bad_rf = sorted(n for n, e in all_nets.items() if e.get('rf50_current_ok') is False)
    if bad_rf:
        raise SystemExit(f'stackup: RF50 width too narrow for the DC current of {bad_rf}')
    counts = collections.Counter(e['class'] for e in all_nets.values())
    patterns = [{'netclass': e['class'], 'pattern': n} for n, e in sorted(all_nets.items()) if e['class'] != 'SIG']
    return {
        'schema': 'srrx-netclasses-v1',
        'status': 'MODEL: IPC-2221 curve fit and closed-form CBCPW; finished impedance, trace and via temperature are bench gates (OPEN)',
        'generator': 'pcb/stackup.py',
        'inputs': [rel(ASSEMBLY_DATA) + ' NET_CURRENT/SEG_CURRENT', *(rel(p) for p in GRAPHS), rel(CONSTRAINTS) + ' DC-04'],
        'stackup': STACKUP,
        'fab_floor': {
            'source': URL_CAPS, 'read': READ,
            'jlc_4l_1oz': {k: v[0] for k, v in CAPS.items() if v[0] is not None},
            'jlc_2l_1oz': {k: v[1] for k, v in CAPS.items() if v[1] is not None},
            'quotes': {k: v[2] for k, v in CAPS.items()},
            'board_setup_note': 'KiCad Board Setup minimums are absolute floors a rule cannot override; board .kicad_pro files take board_setup_floor, the .kicad_dru adds the project defaults.',
            'board_setup_floor_4l': {'min_clearance': CAPS['pad_to_track_min'][0], 'min_track_width': CAPS['track_width_min'][0],
                                     'min_via_diameter': CAPS['via_diameter_min'][0], 'min_through_hole': CAPS['via_hole_min'][0],
                                     'min_via_annular_width': round((CAPS['via_diameter_min'][0] - CAPS['via_hole_min'][0]) / 2, 3),
                                     'min_hole_to_hole': CAPS['via_hole_to_hole_min'][0], 'min_hole_clearance': CAPS['via_hole_to_track_min'][0],
                                     'min_copper_edge_clearance': CAPS['copper_to_routed_edge_min'][0],
                                     'min_silk_text_height': CAPS['silk_text_height_min'][0], 'min_silk_text_thickness': CAPS['silk_line_min'][0]},
            'board_setup_floor_2l': {'min_clearance': CAPS['pad_to_track_min'][1], 'min_track_width': CAPS['track_width_min'][1],
                                     'min_via_diameter': CAPS['via_diameter_min'][1], 'min_through_hole': CAPS['via_hole_min'][1],
                                     'min_via_annular_width': round((CAPS['via_diameter_min'][1] - CAPS['via_hole_min'][1]) / 2, 3),
                                     'min_hole_to_hole': CAPS['via_hole_to_hole_min'][1], 'min_hole_clearance': CAPS['via_hole_to_track_min'][1],
                                     'min_copper_edge_clearance': CAPS['copper_to_routed_edge_min'][1],
                                     'min_silk_text_height': CAPS['silk_text_height_min'][1], 'min_silk_text_thickness': CAPS['silk_line_min'][1]},
        },
        'project_defaults': {'values_mm': PROJECT, 'why': PROJECT_WHY},
        'formulas': {
            'ipc2221': {'k_external': IPC_K['external'], 'k_internal': IPC_K['internal'], 'b': IPC_B, 'c': IPC_C,
                        'area_unit': 'mil^2', 'sources': [f'{URL_IPC_K} ({READ})', f'{URL_IPC_A} ({READ})'],
                        'rule': f'width >= max(IPC-2221 at the continuous current and dT {DT_CONT} degC, at the protective limit and dT {DT_PROT} degC) (project rule)',
                        'split_rule': f'two outer layers in parallel (L1 + L4): each layer sized for {SPLIT_SHARE:.4f} of the current (project choice: unequal split up to 2:1)',
                        'checks': {'4.6 A dT10 1 oz external': round(ipc2221_width_mm(4.6, 10), 3), '7.5 A dT20 1 oz external': round(ipc2221_width_mm(7.5, 20), 3)}},
            'cbcpw': {'source': f'{URL_CPW} ({READ}); R. N. Simons, Coplanar Waveguide Circuits, Components, and Systems, Wiley 2001 (conductor-backed CPW)'},
            'via': via,
        },
        'classes': classes,
        'default_class': 'SIG',
        'nets': {n: all_nets[n] for n in sorted(all_nets)},
        'summary': {'nets': len(all_nets), 'by_class': dict(sorted(counts.items())),
                    'net_current_entries': len(currents['NET_CURRENT']), 'seg_current_entries': len(currents['SEG_CURRENT']),
                    'not_in_graph': missing},
        'unclassified_supply_candidates': {
            'note': 'nets on a supply pin of an IC or module (IN/VIN/OUT/VOUT/OUTS of a part with an IN or VIN pin; VSYS/VBUS/5V/3V3_OUT), or on a series element, that neither NET_CURRENT nor the series '
                    'closure classifies; they default to SIG until tools/assembly_data.py NET_CURRENT lists them (review list, not a finding)',
            'nets': unclassified},
        'kicad': {'netclass_patterns': patterns,
                  'note': 'board .kicad_pro: net_settings classes named as above with outer_min_width_mm as track width, patterns as listed; '
                          'the .kicad_dru conditions use A.hasNetclass(<class>)',
                  'rule_areas': {
                      BRANCH_AREA: f'power-class tracks inside a rule area named so take the project default track {PROJECT["track_width"]} mm as minimum '
                                   '(Kelvin sense, decoupling stubs); the board spec lists each in branch_exempt {ref: {max_mm, min_width_mm, reason}} '
                                   'and pcb/check_boards.py bounds the chain (project rule)',
                      TAPER_AREA: f'RF50 tracks inside a rule area named so may narrow to {PROJECT["track_width"]} mm (taper into an IC pin); the board spec '
                                  'lists each in rf50_taper {ref: {max_len_mm, min_width_mm, reason}} and pcb/check_boards.py bounds it (project rule)'}},
        'open': [
            'Finished RF50 impedance, loss and coupon TDR/S21 (bench).',
            'Trace and via temperature rise under the protective currents (bench).',
            f'DCTAP clearance: IPC-2221B Table 6-1 not read ({URL_IPC2221B}); project rule 0.3 mm meanwhile.',
            'RF50 nets inside the DC-04 +/-30 V envelope keep the CPWG gap 0.20 mm: clearance against Table 6-1 not verified (TBD).',
            'SYS12 and E1_LAB5_RAW carry the F101 7.5 A protective value of NET_CURRENT (D36V50F12 limit TBD there): BATT width until a lower limit is sourced.',
            'Series-derived nets inherit the neighbour values (upper bound): e.g. E2_J21_FUSED takes the SYS12 continuous 4.0 A (bounded by F201 4 A), not the J21 branch 2.5 A.',
            'unclassified_supply_candidates: branch rails reached only through ICs, FETs or diodes default to SIG until NET_CURRENT lists them.',
        ],
    }


# --- KiCad DRC rule files (KiCad 10.0.7 custom rules syntax: version/rule/constraint/condition/layer; later rules
# take precedence; Board Setup constraints are absolute minimums; read in the KiCad source docs
# pcbnew/dialogs/panel_setup_rules_help_*.md at tag 10.0.7, github.com/KiCad/kicad-source-mirror, 2026-11-07).
def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.') + 'mm'


def rules(kind, doc):
    four = kind == '4l'
    col = 0 if four else 1
    floor = {k: v[col] for k, v in CAPS.items()}
    cls = doc['classes']
    hdr = 'JLC04161H-7628 4 layers 1.6 mm, outer 1 oz / inner 0.5 oz' if four else 'JLC 2 layers 1.6 mm, 1 oz'
    out = ['(version 1)',
           f'# GENERATED by pcb/stackup.py; do not edit (rerun: python pcb/stackup.py). {hdr}.',
           f'# Fab floors: {URL_CAPS} (read {READ}); they belong in Board Setup (absolute minimums, see netclasses.json',
           f'# fab_floor.board_setup_floor_{kind}). The rules below are the project defaults (floor + margin) and the net classes.',
           '# Values are MODEL/design rules: DRC 0 proves rule compliance only; bench gates stay OPEN.',
           '# KiCad: later rules take precedence; once a matching rule is found no further rules are checked.', '']

    def rule(name, cons, cond=None, layer=None, comments=()):
        out.extend('# ' + c for c in comments)
        out.append(f'(rule "{name}"')
        if layer:
            out.append(f'  (layer {layer})')
        for c in cons:
            out.append(f'  (constraint {c})')
        if cond:
            out.append(f'  (condition "{cond}")')
        out.append(')')
        out.append('')

    p = PROJECT
    rule('project default clearance', [f'clearance (min {fmt(p["clearance"])})'],
         comments=[f'JLC: track/track {fmt(floor["track_spacing_min"])}, pad/track {fmt(floor["pad_to_track_min"])}, SMD pad/pad {fmt(floor["smd_pad_to_pad_min"])} ({URL_CAPS}, {READ})'])
    rule('project default track', [f'track_width (min {fmt(p["track_width"])}) (opt {fmt(p["track_width"])})'],
         comments=[f'JLC floor {fmt(floor["track_width_min"])} ({URL_CAPS}, {READ})'])
    rule('project via', [f'via_diameter (min {fmt(p["via_diameter"])}) (opt {fmt(p["via_diameter"])})', f'hole_size (min {fmt(p["via_hole"])}) (opt {fmt(p["via_hole"])})',
                         f'annular_width (min {fmt(p["via_annular"])})', f'hole_clearance (min {fmt(p["via_hole_clearance"])})'],
         cond="A.Type == 'Via'",
         comments=[f'JLC floor via {fmt(floor["via_hole_min"])}/{fmt(floor["via_diameter_min"])}, via hole to track {fmt(floor["via_hole_to_track_min"])}'
                   + (f', inner via hole to copper {fmt(floor["inner_via_hole_to_copper_min"])}' if four else '') + f' ({URL_CAPS}, {READ})'])
    rule('project hole to hole', [f'hole_to_hole (min {fmt(p["hole_to_hole"])})'],
         comments=[f'JLC: pad hole-to-hole {fmt(floor["pad_hole_to_hole_min"])}, via hole-to-hole {fmt(floor["via_hole_to_hole_min"])} ({URL_CAPS}, {READ})'])
    rule('project board edge', [f'edge_clearance (min {fmt(p["edge_clearance"])})'],
         comments=[f'JLC: copper to routed edge {fmt(floor["copper_to_routed_edge_min"])} ({URL_CAPS}, {READ})'])
    rule('project silkscreen text', [f'text_height (min {fmt(p["text_height"])})', f'text_thickness (min {fmt(p["text_thickness"])})'],
         cond="A.existsOnLayer('F.SilkS') || A.existsOnLayer('B.SilkS')",
         comments=[f'JLC: silkscreen text >= {fmt(floor["silk_text_height_min"])}, line >= {fmt(floor["silk_line_min"])} ({URL_CAPS}, {READ})'])
    rule('project PTH pad hole', [f'hole_size (min {fmt(p["pth_hole_min"])}) (max {fmt(floor["pth_drill_max"])})', f'hole_clearance (min {fmt(p["pth_hole_clearance"])})',
                                  f'annular_width (min {fmt(floor["pth_annular_min"])})'],
         cond="A.Type == 'Pad' && A.isPlated()",
         comments=[f'JLC: PTH to track {fmt(floor["pth_to_track_min"])} min / {fmt(floor["pth_to_track_recommended"])} recommended'
                   + (f', inner PTH hole to copper {fmt(floor["inner_pth_hole_to_copper_min"])}' if four else '')
                   + f', PTH drill max {fmt(floor["pth_drill_max"])} ({URL_CAPS}, {READ})',
                   f'JLC PTH annular ring {"multilayer" if four else "1-2 layer"} 1 oz: absolute minimum {fmt(floor["pth_annular_min"])}, recommended '
                   f'{fmt(floor["pth_annular_recommended"])} ({URL_CAPS}, {READ}); the rule is the minimum (library THT footprints), pcb/check_boards.py uses the same floor'])
    rule('JLC NPTH hole', [f'hole_size (min {fmt(floor["npth_hole_min"])}) (max {fmt(floor["pth_drill_max"])})', f'hole_clearance (min {fmt(p["npth_hole_clearance"])})'],
         cond="A.Pad_Type == 'NPTH, mechanical'",
         comments=[f'JLC: NPTH min {fmt(floor["npth_hole_min"])}, NPTH to track {fmt(floor["npth_to_track_min"])} ({URL_CAPS}, {READ})'])
    # Mounting-hole keepouts from the board contract (mechanical/generated/contract/boards.json hole_d/hole_keepout_d):
    # no copper of another net inside the keepout circle (clearance measured from the hole edge).
    for d, keep in ((3.2, 7.0), (2.7, 6.0)):
        rule(f'mounting hole {d} keepout', [f'hole_clearance (min {fmt((keep - d) / 2)})'],
             cond=f"A.Pad_Type == 'NPTH, mechanical' && A.Hole_Size_X >= {fmt(d - 0.05)} && A.Hole_Size_X <= {fmt(d + 0.05)}",
             comments=[f'contract hole_d {d} / hole_keepout_d {keep} (mechanical/generated/contract/boards.json): ({keep} - {d}) / 2 from the hole edge'])
    if four:  # the RF board (4 layers) carries the single bond
        rule('BOND-RF hole keepout', [f'hole_clearance (min {fmt((7.0 - 3.2) / 2)})'],
             cond="A.memberOfFootprint('HB*')",
             comments=['BOND-RF exception: the single GND/CHASSIS bond hole (footprint reference HB*) is plated and netted (CHASSIS);',
                       'copper of its own net may enter the keepout, other nets keep the 7.0 mm circle (boards.json RF mount)'])
    for name in POWER_CLASSES:
        c = cls[name]
        per = c['split_outer_per_layer_mm'] or c['outer_min_width_mm']
        comments = [f'{name}: capacity {c["capacity"]["continuous_a"]} A at +{DT_CONT} degC / {c["capacity"]["protective_a"]} A at +{DT_PROT} degC ({c["capacity"]["why"]});',
                    f'IPC-2221 1 oz outer {c["outer_ipc_width_mm"]} mm -> class width {c["outer_min_width_mm"]} mm (netclasses.json, MODEL)']
        if c['split_outer_per_layer_mm']:
            comments.append(f'DRC floor is the L1+L4 split width {per} mm per layer; pcb/check_boards.py enforces {c["outer_min_width_mm"]} mm unless the net is split on both outer layers')
        comments.append('pour necks (zones) are measured by pcb/check_boards.py; no KiCad connection_width rule (fine-pitch pad entries)')
        rule(f'{name} outer width', [f'track_width (min {fmt(per)}) (opt {fmt(c["outer_min_width_mm"])})'],
             cond=f"A.hasNetclass('{name}')", layer='outer', comments=comments)
        if four and c['inner_min_width_mm'] is not None:
            rule(f'{name} inner width', [f'track_width (min {fmt(c["inner_min_width_mm"])}) (opt {fmt(c["inner_min_width_mm"])})'],
                 cond=f"A.hasNetclass('{name}')", layer='inner',
                 comments=[f'{name} on 0.5 oz inner copper (IPC-2221 internal k 0.024), MODEL'])
        elif four:
            rule(f'{name} no inner tracks', ['disallow track'],
                 cond=f"A.hasNetclass('{name}') && !A.intersectsArea('{BRANCH_AREA}')", layer='inner',
                 comments=[f'{name}: inner 0.5 oz copper is not counted as a current path, so no {name} track on In1/In2 (a thin inner',
                           f'track would carry the current in series); inner pours stay allowed and uncounted; {BRANCH_AREA} rule areas excepted'])
    power_cond = ' || '.join(f"A.hasNetclass('{n}')" for n in POWER_CLASSES)
    rule('power branch area', [f'track_width (min {fmt(p["track_width"])})'],
         cond=f"({power_cond}) && A.intersectsArea('{BRANCH_AREA}')",
         comments=[f'project rule: low-current branches of power nets (Kelvin sense lines, decoupling stubs) inside rule areas named {BRANCH_AREA}',
                   f'take the project default track {fmt(p["track_width"])} (JLC floor {fmt(floor["track_width_min"])}, {URL_CAPS}, {READ}); each is listed in the board',
                   'spec branch_exempt {ref: {max_mm, min_width_mm, reason}} and bounded by pcb/check_boards.py'])
    if four:
        rf = cls['RF50']
        rule('RF50 CPWG on L1', [f'track_width (min {fmt(rf["width_mm"] - rf["width_tol_mm"])}) (opt {fmt(rf["width_mm"])}) (max {fmt(rf["width_mm"] + rf["width_tol_mm"])})',
                                 f'clearance (min {fmt(rf["gap_mm"])})'],
             cond="A.hasNetclass('RF50')", layer='"F.Cu"',
             comments=[f'CBCPW w {rf["width_mm"]} / s {rf["gap_mm"]} over L2 at h {rf["model"]["h_mm"]}, er {rf["model"]["er"]}: {rf["model"]["z0_ohm"]} ohm closed form (MODEL; {URL_STACKUP}, {READ})',
                       'L2 solid under RF50 (3h band) and the fence pitch are checked by pcb/check_boards.py, not by KiCad'])
        rule('RF50 taper area', [f'track_width (min {fmt(p["track_width"])}) (max {fmt(rf["width_mm"] + rf["width_tol_mm"])})'],
             cond=f"A.hasNetclass('RF50') && A.intersectsArea('{TAPER_AREA}')", layer='"F.Cu"',
             comments=[f'project rule: RF50 tapers into IC pins inside rule areas named {TAPER_AREA} may narrow to {fmt(p["track_width"])}',
                       f'(JLC floor {fmt(floor["track_width_min"])}, {URL_CAPS}, {READ}); clearance stays {fmt(rf["gap_mm"])}; each taper is listed in the board spec',
                       'rf50_taper {ref: {max_len_mm, min_width_mm, reason}} and bounded by pcb/check_boards.py'])
        rule('RF50 only on L1', ['disallow track via'], cond="A.hasNetclass('RF50')", layer='inner',
             comments=['RF50 lines stay on F.Cu over the solid In1.Cu GND (layer plan, build/15)'])
        rule('RF50 not on L4', ['disallow track'], cond="A.hasNetclass('RF50')", layer='"B.Cu"')
        dc = cls['DCTAP']
        rule('DCTAP width and clearance', [f'track_width (min {fmt(dc["width_mm"])}) (opt {fmt(dc["width_mm"])})', f'clearance (min {fmt(dc["project_rule_clearance_mm"])})'],
             cond="A.hasNetclass('DCTAP') || B.hasNetclass('DCTAP')",
             comments=['DCTAP +/-30 V envelope (constraints.json DC-04). Clearance 0.3 mm: project choice, not IPC-verified;',
                       f'IPC-2221B Table 6-1 not readable ({URL_IPC2221B}, {READ}): TBD in netclasses.json'])
    return '\n'.join(out).rstrip('\n') + '\n'


def outputs():
    doc = build()
    return {OUT_JSON: json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
            OUT_RULES['4l']: rules('4l', doc), OUT_RULES['2l']: rules('2l', doc)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true', help='compare with the committed outputs, write nothing')
    args = ap.parse_args(argv)
    files = outputs()
    if args.check:
        stale = [rel(p) for p, text in files.items() if not p.is_file() or p.read_text(encoding='utf-8') != text]
        if stale:
            raise SystemExit('stackup: stale generated output: ' + ', '.join(stale) + ' (rerun python pcb/stackup.py)')
    else:
        for p, text in files.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding='utf-8', newline='\n')
    doc = json.loads(files[OUT_JSON])
    print(json.dumps(doc['summary'], ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
