#!/usr/bin/env python3
"""Write the RF board spec pcb/boards/RF.json and its project build/kicad/boards/RF/RF.kicad_pro (W2 PCB-RF-1).

Standard library only. Run from any directory:
  python3 build/kicad/boards/RF/rf_layout.py           write both files
  python3 build/kicad/boards/RF/rf_layout.py --check   fail unless both reproduce and the layout checks pass

The layout is written here as code (anchors, packed rows, RF50 paths), so a placement change is one edit and
the geometry checks below run on every write: courtyard overlaps, pads against the outline and the hole
keepouts, scripted RF copper against foreign pads and tracks, tap and decoupling distances. pcb/board_gen.py
reads only the written spec. CI/model geometry; no hardware or bench gate is closed by it.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3] if (HERE.parents[3] / 'pcb/board_gen.py').is_file() else Path(os.environ['SR_RX_BASE'])
sys.path.insert(0, str(BASE / 'pcb'))
import board_gen as bg  # noqa: E402

SPEC = BASE / 'pcb/boards/RF.json'
PROJECT = BASE / 'build/kicad/boards/RF/RF.kicad_pro'
ENC_PROJECT = BASE / 'build/kicad/boards/ENC/ENC.kicad_pro'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
DOMAINS = ['RF_HMC', 'RF_HF', 'RF_INJECTOR', 'DC_CORE']
TAPER_W, RF_W = 0.25, 0.36          # HMC pin entry width, RF50 width (netclasses.json RF50)
TAPER_LEN = 0.84                    # from the pin centre: pad half-length 0.4125 + 0.43 mm

# Placeholders: board ends that the graph does not have yet (boundary audit 'provisional').
UFL_IMAGE = {'footprint': 'Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical',
             'sha256': '8f227fecc7252e97f349d06841694c60e3df4c0cb58c6c59a5123f1cd631860c',
             'source': 'https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/10.0.7/Connector_Coaxial.pretty/'
                       'U.FL_Hirose_U.FL-R-SMT-1_Vertical.kicad_mod read 2026-11-07 (the same file that '
                       'SR_RX_Custom:U.FL_Hirose_U.FL-R-SMT-1_Vertical_CS names as its origin); checked against '
                       'the kicad/kicad:10.0.7 image copy at run time'}
TP_IMAGE = {'footprint': 'TestPoint:TestPoint_Pad_D2.0mm',
            'sha256': '0a1ce94753a7b270c8ff6c20698b4de7ce95606b643549926acc04bb698d0120',
            'source': 'https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/10.0.7/TestPoint.pretty/'
                      'TestPoint_Pad_D2.0mm.kicad_mod read 2026-11-07; checked against the kicad/kicad:10.0.7 '
                      'image copy at run time'}
PLACEHOLDERS = {
    'PH401': ('E4_RF_CH1', 'A402 SAWbird+ NOAA OUT (E4_RF_CH1)', UFL_IMAGE),
    'PH402': ('E4_RF_CH5_DC', 'A405 VAT attenuator IN (E4_RF_CH5_DC)', UFL_IMAGE),
    'PH403': ('E4_RF_CH5_ATT', 'A405 VAT attenuator OUT (E4_RF_CH5_ATT)', UFL_IMAGE),
    'PH404': ('E4_HF_BT', 'A406 Boni bias-tee RF port (E4_HF_BT)', UFL_IMAGE),
    'PH405': ('E4_HF_CM', 'W408 OUT / A406 ANT tap point (E4_HF_CM)', UFL_IMAGE),
    'PH406': ('E4_HFP_ANT', 'A414 Airspy HF+ ANT (E4_HFP_ANT)', UFL_IMAGE),
    'PH407': ('CHASSIS', 'BOND-RF chassis land of NT401 (CHASSIS)', TP_IMAGE),
}

GEO, PLACED, ANCHORS, TRACKS, CHECK_PAIRS, GAPS = {}, {}, {}, [], [], []


def geo(ref):
    return GEO[ref]


def anchor(ref, at, rot=0, align='origin'):
    a = {'at': [bg.r4(at[0]), bg.r4(at[1])], 'align': align, 'rotation': rot, 'side': 'F'}
    ANCHORS[ref] = a
    PLACED[ref] = bg.placed_geometry(geo(ref), a)
    return PLACED[ref]


def pad_at(ref, pad, at, rot=0):
    """Anchor ref so that its pad (one pad, or the centroid of a pad number) lands on at."""
    return anchor(ref, at, rot, {'pad': str(pad)})


def pad(ref, number):
    pts = PLACED[ref]['pads'][str(number)]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def box_of(ref, rot):
    return bg.rotate_box(geo(ref)['courtyard'], rot)


def row(items, x0, y, gap=0.4):
    """Pack [(ref, rot)] left to right by courtyard boxes; the row is centred on y. Returns the right edge."""
    x = x0
    for ref, rot in items:
        b = box_of(ref, rot)
        w, cy = b[2] - b[0], (b[1] + b[3]) / 2
        # origin so that the box spans [x, x + w] and is centred on y (KiCad y down: board y = at - local y)
        anchor(ref, (x - b[0], y + cy), rot)
        x += w + gap
    return x - gap


def track(net, pts, width=RF_W, why='RF50 CPWG on F.Cu over solid In1.Cu GND (scripted, locked)'):
    TRACKS.append({'id': f'{net}-{len([t for t in TRACKS if t["net"] == net]) + 1}', 'net': net, 'layer': 'F.Cu',
                   'width_mm': width, 'path': [[bg.r4(x), bg.r4(y)] for x, y in pts], 'locked': True, 'why': why})


def hmc_line(net_pin, net_out, ref, pin, direction, end):
    """Taper from an HMC7992 pin (0.25 mm, pad width) for TAPER_LEN, then RF50 to end."""
    x, y = pad(ref, pin)
    dx, dy = direction
    mid = (x + dx * TAPER_LEN, y + dy * TAPER_LEN)
    track(net_pin, [(x, y), mid], TAPER_W, 'RF50 entry at the HMC7992 pin: pad width 0.25 mm for 0.84 mm (rf50_taper)')
    track(net_pin, [mid, end])


# --------------------------------------------------------------------------------------------- layout
def layout():
    # ---------------- HF section (x 0-46): relays, HF+/Boni ends, HF tap and bleeds, P6, ch5 IF
    anchor('K401', (16.0, 20.0), 0)
    anchor('K402', (40.0, 20.0), 180)
    pad_at('R417', 1, (15.4, 13.3), 270)
    pad_at('R419', 1, (40.6, 13.3), 270)
    pad_at('R418', 1, (40.6, 26.7), 90)
    pad_at('J425', 'CENTER', (38.4, 40.475), 90)
    pad_at('PH404', 1, (17.6, 3.825), 270)
    pad_at('PH406', 1, (26.0, 3.825), 270)
    pad_at('PH405', 1, (32.0, 3.825), 270)
    pad_at('R4440', 1, (32.0, 6.2), 0)
    anchor('C4440', (34.6, 6.2), 0)
    pad_at('R4468', 1, (32.0, 9.0), 0)
    anchor('R4469', (38.6, 9.0), 0)
    anchor('R4470', (43.7, 9.0), 0)
    anchor('R4471', (43.7, 5.4), 180)
    # ch5 IF: J426 edge SMA on the top edge (board edge at footprint x -4.76), L406 LNB feed, C412 DC block
    anchor('J426', (26.0, 44.5 - 4.76), 270)
    pad_at('L406', 1, (26.0, 35.3), 0)
    pad_at('C412', 1, (26.0, 33.0), 270)
    pad_at('PH402', 1, (28.6, 31.3), 0)

    k401 = {n: pad('K401', n) for n in '12345678'}
    k402 = {n: pad('K402', n) for n in '12345678'}
    track('E4_HF_LINK', [k401['4'], k401['5']])
    track('E4_VHF_LINK', [k402['5'], k402['4']])
    track('E4_P6', [k402['3'], pad('J425', 'CENTER')])
    track('E4_PARK_VHF', [k402['2'], pad('R418', 1)])
    track('E4_PARK_HFP', [k402['7'], pad('R419', 1)])
    track('E4_PARK_HF', [k401['2'], pad('R417', 1)])
    track('E4_HF_BT', [k401['3'], pad('PH404', 1)])
    x6, y6 = k401['6']
    track('E4_HFP_ANT', [(x6, y6), (x6, 26.5), (26.0, 26.5), pad('PH406', 1)])
    x7, y7 = k401['7']
    xs, ys = k402['6']
    track('E4_RELAY_STAGE', [(x7, y7), (x7, 28.5), (30.0, 28.5), (30.0, 12.0), (xs, 12.0), (xs, ys)])
    track('E4_HF_CM', [pad('PH405', 1), pad('R4468', 1)])
    jx = pad('J426', 'CENTER')[0]
    track('E4_RF_CH5', [(jx, 40.0), pad('C412', 1)])
    c412b = pad('C412', 2)
    track('E4_RF_CH5_DC', [c412b, (c412b[0], pad('PH402', 1)[1]), pad('PH402', 1)])

    # ---------------- RF section: three HMC7992 (U406 RTL-B, U407 Lime, U405 RTL-A), top-edge ports
    anchor('U406', (65.5, 27.0), 0)
    anchor('U407', (79.0, 27.0), 270)
    anchor('U405', (123.25, 27.0), 0)
    for ref, x in (('J409', 52.6), ('J411', pad('U406', 15)[0]), ('J412', pad('U407', 4)[0]),
                   ('J410', pad('U405', 15)[0])):
        anchor(ref, (x, 44.5 - 4.76), 270)
    pad_at('J424', 'CENTER', (98.0, 40.475), 90)
    pad_at('J423', 'CENTER', (107.0, 40.475), 90)

    # U406 RTL-B
    pad_at('C410', 1, (pad('U406', 15)[0], 30.52), 90)
    anchor('C409', (61.4, 27.75), 0)
    anchor('C408', (62.4, 26.25), 0)
    anchor('C407', (68.8, 26.25), 180)
    anchor('C406', (68.8, 27.75), 0)
    pad_at('R406', 1, (70.475, 27.75), 0)
    pad_at('PH403', 1, (60.0, 23.0), 270)
    hmc_line('E4_RTLB_RFC', None, 'U406', 15, (0, 1), pad('C410', 1))
    track('E4_RFC_B', [pad('C410', 2), (pad('C410', 2)[0], 41.0)])
    hmc_line('E4_RTLB_RF4', None, 'U406', 1, (-1, 0), pad('C409', 2))
    b = pad('C409', 1)
    track('E4_BENCH', [b, (54.6, b[1]), (52.6, b[1] + 2.0), (52.6, 41.0)])
    hmc_line('E4_RTLB_RF3', None, 'U406', 4, (-1, 0), pad('C408', 2))
    a = pad('C408', 1)
    track('E4_RF_CH5_ATT', [a, (60.0, a[1]), pad('PH403', 1)])
    hmc_line('E4_RTLB_RF2', None, 'U406', 9, (1, 0), pad('C407', 2))
    hmc_line('E4_RTLB_RF1', None, 'U406', 12, (1, 0), pad('C406', 1))
    track('E4_PARK_B', [pad('C406', 2), pad('R406', 1)])

    # U407 Lime router (rot 270: RFC right, RF3/RF4 top, RF2/RF1 bottom, controls left)
    pad_at('C416', 1, (pad('U407', 9)[0], 24.2), 270)
    pad_at('C414', 1, (pad('U407', 12)[0], 24.2), 270)
    pad_at('R407', 1, (pad('U407', 12)[0], 21.6), 270)
    pad_at('C415', 1, (pad('U407', 4)[0], 29.82), 90)
    pad_at('A407', 2, (pad('U407', 4)[0], 32.25), 0)
    pad_at('C418', 1, (pad('U407', 4)[0], 35.37), 90)
    pad_at('C417', 1, (pad('U407', 1)[0], 29.82), 90)
    pad_at('R416', 1, (pad('U407', 1)[0] + 0.9, 32.2), 90)
    pad_at('C411', 2, (82.0, pad('U407', 15)[1]), 180)
    hmc_line('E4_LIME_TO_RTLB', None, 'U407', 9, (0, -1), pad('C416', 1))
    c7, c16 = pad('C407', 1), pad('C416', 2)
    track('E4_RF_CH3_B', [c7, (70.0, c7[1]), (73.75, 22.5), (c16[0] - 0.75, 22.5), c16])
    hmc_line('E4_LIME_RF1', None, 'U407', 12, (0, -1), pad('C414', 1))
    track('E4_PARK_C', [pad('C414', 2), pad('R407', 1)])
    hmc_line('E4_LIME_RF3', None, 'U407', 4, (0, 1), pad('C415', 1))
    track('E4_YAT_IN', [pad('C415', 2), pad('A407', 2)])
    track('E4_YAT_OUT', [pad('A407', 5), pad('C418', 1)])
    track('E4_RX1_EDGE', [pad('C418', 2), (pad('C418', 2)[0], 41.0)])
    hmc_line('E4_LIME_RFSPARE', None, 'U407', 1, (0, 1), pad('C417', 1))
    s, r = pad('C417', 2), pad('R416', 1)
    track('E4_PARK_C_SPARE', [s, (r[0], s[1] + (r[0] - s[0])), r])
    hmc_line('E4_LIME_RFC', None, 'U407', 15, (1, 0), pad('C411', 2))
    p3 = pad('C411', 1)
    track('E4_P3', [p3, (96.0, p3[1]), (98.0, p3[1] + 2.0), pad('J424', 'CENTER')])
    # P3 port: tap, injector and first bleed with pad 1 on the RF50 line (DC-01)
    pad_at('R4430', 1, (98.0, 37.6), 0)
    anchor('C4430', (100.6, 37.6), 0)
    pad_at('L404', 1, (98.0, 35.4), 0)
    pad_at('R4464', 1, (98.0, 31.8), 0)
    anchor('R4465', (103.0, 27.6), 270)
    anchor('R4466', (103.0, 22.9), 270)
    anchor('R4467', (103.0, 18.2), 270)
    # NT401: the single GND/CHASSIS tie next to the BOND-RF hole (92, 40.5), outside its keepout
    anchor('NT401', (92.0, 32.0), 90)
    anchor('PH407', (88.8, 34.0), 0)
    track('CHASSIS', [pad('PH407', 1), pad('NT401', 2)], 1.0, 'CHASSIS land to the NT401 net tie (scripted, locked)')

    # U405 RTL-A
    pad_at('C405', 1, (pad('U405', 15)[0], 30.52), 90)
    anchor('C404', (120.1, 27.75), 0)
    anchor('C403', (120.1, 26.25), 0)
    anchor('C402', (126.4, 26.25), 180)
    anchor('C401', (126.4, 27.75), 0)
    pad_at('R405', 1, (128.1, 27.75), 0)
    anchor('A424', (112.6, 31.0), 90)
    anchor('C446', (111.2, 27.6), 0)
    pad_at('J427', 'CENTER', (pad('A424', 3)[0], 40.475), 90)
    hmc_line('E4_RTLA_RFC', None, 'U405', 15, (0, 1), pad('C405', 1))
    track('E4_RFC_A', [pad('C405', 2), (pad('C405', 2)[0], 41.0)])
    hmc_line('E4_RTLA_RF4', None, 'U405', 1, (-1, 0), pad('C404', 2))
    c4, a4 = pad('C404', 1), pad('A424', 4)
    track('E4_CH4_RF_ONLY', [c4, (a4[0] + 0.6, c4[1]), (a4[0], c4[1] + 0.6), a4])
    track('E4_RF_CH4', [pad('A424', 3), pad('J427', 'CENTER')])
    hmc_line('E4_RTLA_RF3', None, 'U405', 4, (-1, 0), pad('C403', 2))
    p2 = pad('C403', 1)
    track('E4_P2', [p2, (109.0, p2[1]), (107.0, p2[1] + 2.0), pad('J423', 'CENTER')])
    pad_at('R4420', 1, (107.0, 37.6), 0)
    anchor('C4420', (109.6, 37.6), 0)
    pad_at('L403', 1, (107.0, 35.4), 0)
    pad_at('R4460', 1, (107.0, 31.6), 180)
    anchor('R4461', (106.3, 23.3), 270)
    anchor('R4462', (106.3, 18.6), 270)
    anchor('R4463', (106.3, 13.9), 270)
    hmc_line('E4_RTLA_RF2', None, 'U405', 9, (1, 0), pad('C402', 2))
    hmc_line('E4_RTLA_RF1', None, 'U405', 12, (1, 0), pad('C401', 1))
    track('E4_PARK_A', [pad('C401', 2), pad('R405', 1)])
    pad_at('L402', 1, (129.6, 22.4), 180)
    pad_at('PH401', 1, (129.6, 18.6), 270)
    c2 = pad('C402', 1)
    track('E4_RF_CH1', [c2, (127.6, c2[1]), (129.6, c2[1] - 2.0), pad('PH401', 1)])

    # ---------------- injector decoupling and tap capacitors (anchors next to their pads, <= 2 mm)
    l2 = pad('L402', 2)
    anchor('C447', (l2[0] - 1.9, l2[1]), 0)
    anchor('C448', (l2[0] - 1.875, l2[1] - 2.0), 0)
    l3 = pad('L403', 2)
    anchor('C449', (l3[0] + 1.275, l3[1]), 90)
    anchor('C450', (l3[0] + 2.675, l3[1]), 90)
    l4 = pad('L404', 2)
    anchor('C451', (l4[0] + 2.225, l4[1] + 0.5), 0)
    anchor('C452', (l4[0] + 2.775, l4[1] - 1.0), 0)
    CHECK_PAIRS.extend([('C447', 'L402', '2'), ('C448', 'L402', '2'), ('C449', 'L403', '2'), ('C450', 'L403', '2'),
                        ('C451', 'L404', '2'), ('C452', 'L404', '2'), ('C446', 'A424', '1'),
                        ('C4420', 'R4420', '2'), ('C4430', 'R4430', '2'), ('C4440', 'R4440', '2')])

    # ---------------- HMC controls (1k / 100k / 100 pF) and VDD decoupling below or beside each switch
    pad6 = pad('U406', 6)
    anchor('C441', (pad6[0] + 0.25, 23.9), 0)
    row([('R442', 90), ('R443', 90), ('R410', 90), ('R411', 90)], 62.9, 20.6)
    row([('C421', 0), ('C422', 0)], 63.1, 17.9)
    pad6 = pad('U407', 6)
    anchor('C442', (75.2, pad6[1]), 0)
    row([('R444', 90), ('R445', 90), ('R434', 90)], 73.0, 19.9)
    row([('R435', 90), ('C434', 90), ('C435', 90)], 73.0, 16.4)
    pad6 = pad('U405', 6)
    anchor('C440', (pad6[0] + 0.25, 23.9), 0)
    row([('R440', 90), ('R441', 90), ('R408', 90), ('R409', 90)], 116.0, 21.0)
    row([('C419', 0), ('C420', 0)], 116.0, 18.3)
    CHECK_PAIRS.extend([('C441', 'U406', '6'), ('C442', 'U407', '6'), ('C440', 'U405', '6')])

    # ---------------- relay drivers (HF section, above the relays)
    row([('Q401', 0), ('Q402', 0), ('D401', 0)], 9.0, 34.6)
    row([('R412', 0), ('R414', 0), ('R413', 0), ('R415', 0)], 9.0, 31.2)

    # ---------------- harness headers S03/S04 on the bottom edge, openings to the edge (rot 0: body to -y)
    for ref, x in (('J419', 122.0), ('J418', 134.95), ('J420', 155.0)):
        pad_at(ref, 1, (x, 7.6), 0)

    # ---------------- DC_CORE (x 132-184): three channel blocks after the prototype's channel order
    # (generate_routed.py:35-43: two TLV3012 side by side, clamp, sense filter and divider at the input,
    # the 100 ohm / 100 k gate pairs and the AO3400A pair beside them), compacted into rows for 44.5 mm.
    for i, (y0, name) in enumerate(((40.4, 'UHF'), (31.4, 'LBAND'), (22.4, 'HF'))):
        r, u, q = 4420 + i * 10, 450 + i * 2, 450 + i * 2
        x0 = 133.0
        row([(f'U{u + 1}', 180), (f'U{u}', 180), (f'D{451 + i}', 0), (f'Q{q}', 0), (f'Q{q + 1}', 0)], x0, y0)
        row([(f'C{4411 + i * 2}', 0), (f'C{4410 + i * 2}', 0), (f'C{r + 1}', 0), (f'R{r + 1}', 0), (f'R{r + 2}', 0)],
            x0, y0 - 2.75)
        row([(f'R{r + 3}', 0), (f'R{r + 4}', 0), (f'R{r + 5}', 0), (f'R{r + 6}', 0)], x0 + 2.0, y0 - 4.75)
        CHECK_PAIRS.extend([(f'C{4411 + i * 2}', f'U{u + 1}', '6'), (f'C{4410 + i * 2}', f'U{u}', '6')])
    # reference and reference-good blocks (generate_routed.py:27-34), right of the channels
    row([('D450', 0), ('U458', 180), ('C4400', 90)], 157.5, 40.4)
    row([('R4400', 90), ('R4401', 90), ('R4402', 90), ('R4403', 90), ('R4404', 90), ('R4405', 90)], 157.5, 35.9)
    row([('C4401', 90), ('C4402', 90)], 157.5 + 6 * 1.86, 35.9)
    row([('C4403', 90), ('U456', 180), ('Q456', 0), ('C4404', 90), ('U457', 180), ('Q457', 0)], 157.5, 31.0)
    for cap, u in (('C4416', 'U456'), ('C4417', 'U457')):
        anchor(cap, (pad(u, 6)[0] + 0.6, 28.3), 0)
    row([('R4406', 90), ('R4407', 90), ('C4405', 90), ('R4450', 90), ('R4451', 90)], 157.5, 24.6)
    row([('R4408', 90), ('R4409', 90), ('C4406', 90), ('R4452', 90), ('R4453', 90)], 157.5, 20.4)
    # 3V3 local decoupling of the reference-good comparators (DC-03)
    CHECK_PAIRS.extend([('C4416', 'U456', '6'), ('C4417', 'U457', '6'), ('C4400', 'U458', '1'),
                        ('C4403', 'U456', '5'), ('C4404', 'U457', '5')])


# --------------------------------------------------------------------------------------------- checks
def seg_point(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def seg_box(a, b, box):
    """Distance from segment ab to an axis-aligned box (0 when they touch)."""
    x0, y0, x1, y1 = box

    def inside(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    if inside(a) or inside(b):
        return 0.0
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for c, d in zip(corners, corners[1:] + corners[:1]):
        if seg_seg(a, b, c, d) == 0.0:
            return 0.0
    return min([seg_point(c, a, b) for c in corners] +
               [bg.box_circle_distance(box, a), bg.box_circle_distance(box, b)])


def seg_seg(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0) and o1 * o2 < 0 and o3 * o4 < 0:
        return 0.0
    return min(seg_point(c, a, b), seg_point(d, a, b), seg_point(a, c, d), seg_point(b, c, d))


def pad_boxes(template_pads):
    """Board pad boxes with their template nets: [(ref, number, net, box)]."""
    out = []
    for ref, placed in PLACED.items():
        g = geo(ref)
        rot = ANCHORS[ref]['rotation']
        for p in g['pads']:
            if not p['number'] and p['type'] == 'smd' and ref.startswith('U4'):
                continue  # EPAD paste windows (unnumbered, paste only)
            if p['type'] == 'np_thru_hole':
                continue
            w, h = p['size']
            if int(round(rot / 90.0)) % 2:
                w, h = h, w
            at_origin = {'at': placed['origin'], 'align': 'origin', 'rotation': rot, 'side': 'F'}
            loc = bg.placed_geometry({'pads': [dict(p, number='X')], 'courtyard': None}, at_origin)['pads']['X'][0]
            net = template_pads.get(ref, {}).get(str(p['number']))
            out.append((ref, str(p['number']), net, [loc[0] - w / 2, loc[1] - h / 2, loc[0] + w / 2, loc[1] + h / 2]))
    return out


def checks(template, contract, classes):
    problems = []
    tpads = {t['ref']: t['pads'] for t in template}
    outline = contract['outline_mm']
    W, H = outline[2][0], outline[2][1]
    holes = [(x, y) for x, y in contract['holes_mm']]
    ko = contract['hole_keepout_d'] / 2
    boxes = {r: p['box'] for r, p in PLACED.items() if p['box']}
    refs = sorted(boxes)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            if bg.rects_overlap(boxes[a], boxes[b]):
                problems.append(f'courtyards overlap: {a} {b}')
    pads = pad_boxes(tpads)
    edge_parts = {'J409', 'J410', 'J411', 'J412', 'J426'}
    for ref, num, net, box in pads:
        if ref not in edge_parts and (box[0] < 0.3 or box[1] < 0.3 or box[2] > W - 0.3 or box[3] > H - 0.3):
            problems.append(f'pad {ref}.{num} within 0.3 mm of the edge {[round(v, 3) for v in box]}')
        for hx, hy in holes:
            if bg.box_circle_distance(box, (hx, hy)) < ko:
                problems.append(f'pad {ref}.{num} in the keepout of hole ({hx}, {hy})')
    for ref, b in boxes.items():
        if ref in edge_parts:
            continue
        if b[0] < -1e-6 or b[1] < -1e-6 or b[2] > W + 1e-6 or b[3] > H + 1e-6:
            problems.append(f'courtyard of {ref} outside the outline {b}')
    for t in TRACKS:
        cls = classes.get(t['net'], 'Default')
        for a, b in zip(t['path'], t['path'][1:]):
            for ref, num, net, box in pads:
                if net == t['net']:
                    continue
                need = max(CLEAR.get(cls, 0.15), CLEAR.get(classes.get(net, 'Default'), 0.15) if net else 0.15)
                d = seg_box(a, b, box) - t['width_mm'] / 2
                GAPS.append((d - need, t['id'], f'{ref}.{num}'))
                if d < need - 1e-6:
                    problems.append(f'track {t["id"]} {a}->{b} {d:.3f} mm from pad {ref}.{num} ({net}), needs {need}')
            for hx, hy in holes:
                if seg_point((hx, hy), a, b) - t['width_mm'] / 2 < ko:
                    problems.append(f'track {t["id"]} in the keepout of hole ({hx}, {hy})')
            for p in (a, b):
                if not (0.3 <= p[0] <= W - 0.3 and 0.3 <= p[1] <= H - 0.3):
                    problems.append(f'track {t["id"]} point {p} near or outside the edge')
    for i, (ra, na, neta, ba) in enumerate(pads):
        for rb, nb, netb, bb in pads[i + 1:]:
            if ra == rb or (neta and neta == netb):
                continue
            need = max(CLEAR.get(classes.get(neta, 'Default'), 0.15) if neta else 0.15,
                       CLEAR.get(classes.get(netb, 'Default'), 0.15) if netb else 0.15)
            gx = max(ba[0] - bb[2], bb[0] - ba[2], 0.0)
            gy = max(ba[1] - bb[3], bb[1] - ba[3], 0.0)
            if math.hypot(gx, gy) < need - 1e-6:
                problems.append(f'pads {ra}.{na} ({neta}) and {rb}.{nb} ({netb}) {math.hypot(gx, gy):.3f} mm apart, need {need}')
    for i, t in enumerate(TRACKS):
        for u in TRACKS[i + 1:]:
            if u['net'] == t['net']:
                continue
            need = max(CLEAR.get(classes.get(t['net'], 'Default'), 0.15), CLEAR.get(classes.get(u['net'], 'Default'), 0.15))
            for a, b in zip(t['path'], t['path'][1:]):
                for c, d in zip(u['path'], u['path'][1:]):
                    gap = seg_seg(a, b, c, d) - (t['width_mm'] + u['width_mm']) / 2
                    if gap < need - 1e-6:
                        problems.append(f'tracks {t["id"]} and {u["id"]} {gap:.3f} mm apart, need {need}')
    for cap, ref, num in CHECK_PAIRS:
        d = bg.box_circle_distance(boxes[cap], pad(ref, num))
        if d > 2.0 + 1e-6:
            problems.append(f'{cap} is {d:.2f} mm from {ref}.{num} (limit 2.0)')
    # each RF50 net is one connected chain of locked copper between its pads
    for net in sorted({t['net'] for t in TRACKS if classes.get(t['net']) == 'RF50'}):
        ends = [(ref, num) for ref, num, n, _b in pads if n == net]
        segs = [(a, b) for t in TRACKS if t['net'] == net for a, b in zip(t['path'], t['path'][1:])]
        for ref, num, n, box in pads:
            if n != net:
                continue
            if not any(seg_box(a, b, box) == 0.0 for a, b in segs):
                problems.append(f'RF50 net {net}: pad {ref}.{num} has no scripted copper')
    return problems


CLEAR = {'Default': 0.15, 'RF50': 0.2, 'DCTAP': 0.3, 'PWR1A': 0.15}


def net_classes(nets):
    nc = bg.read_json(NETCLASSES)
    out = {}
    for n in nets:
        cls = (nc['nets'].get(n) or {}).get('class')
        if cls in ('RF50', 'DCTAP', 'PWR1A'):
            out[n] = cls
    return out


def project_text(classes):
    proj = json.loads(ENC_PROJECT.read_text(encoding='utf-8'))
    proj['meta']['filename'] = 'RF.kicad_pro'
    base = proj['net_settings']['classes'][0]
    base.update({'clearance': 0.15, 'track_width': 0.2})
    rows = [base]
    for prio, (name, width, clear) in enumerate((('RF50', 0.36, 0.2), ('DCTAP', 0.2, 0.3), ('PWR1A', 0.35, 0.15))):
        rows.append(dict(base, name=name, priority=prio, track_width=width, clearance=clear))
    proj['net_settings']['classes'] = rows
    proj['net_settings']['netclass_patterns'] = [{'netclass': c, 'pattern': n} for n, c in sorted(classes.items())]
    return json.dumps(proj, indent=2, ensure_ascii=False) + '\n'


def spec_doc(template_nets, parts, enc):
    nc = bg.read_json(NETCLASSES)
    floor = nc['fab_floor']['jlc_4l_1oz']
    return {
        'schema': bg.SPEC_SCHEMA,
        'board_id': 'RF',
        'status': 'RF1_PLACED_FIRST_ROUTE_NOT_FOR_FABRICATION',
        'title': 'RF / detector board (RF_HMC, RF_HF, RF_INJECTOR, DC_CORE) 184 x 44.5 - placement and scripted RF copper',
        'note': ('W2 PCB-RF-1: every RF-domain ref placed, RF50 copper scripted and locked, first route run. Written by '
                 'build/kicad/boards/RF/rf_layout.py (edit the layout there, then rerun it). PCB-RF-2 routes to DRC 0, '
                 'adds the coupon tab and the fab set. Nothing here is a fabrication release; bench gates stay OPEN.'),
        'contract': {'file': 'mechanical/generated/contract/boards.json', 'board': 'RF'},
        'domains': DOMAINS,
        'partition': 'pcb/generated/partition.json',
        'layers': {
            'copper': 4, 'thickness_mm': 1.6,
            'source': ('contract stackup JLC04161H-7628, 4 layers, 1.6 mm (mechanical/generated/contract/boards.json '
                       'stackup; build/15); RF50 geometry from pcb/generated/netclasses.json (L1 over L2, h 0.2104 mm)'),
            'plan': {'F.Cu': 'all parts, RF50 CPWG (scripted, locked), signals, GND pour (coplanar ground)',
                     'In1.Cu': 'solid GND reference plane under RF50 (pre-route zone, a DSN plane)',
                     'In2.Cu': 'signals, GND pour', 'B.Cu': 'signals, GND pour'}},
        'project': 'build/kicad/boards/RF/RF.kicad_pro',
        'rules_file': None,
        'rules_note': ('rules_file stays null (pcb/board_gen.py does not copy .kicad_dru files yet); the net classes '
                       'RF50 0.36/0.20, DCTAP 0.20/0.30 (project rule, not IPC-verified), PWR1A 0.35/0.15 and the '
                       'default 0.20/0.15 live in RF.kicad_pro, values from pcb/generated/netclasses.json.'),
        'fab_floor': {
            'source': f'{nc["fab_floor"]["source"]} read {nc["fab_floor"]["read"]}, 4-layer 1 oz values (pcb/generated/netclasses.json fab_floor.jlc_4l_1oz)',
            'min_track_width': floor['track_width_min'], 'min_clearance': floor['track_spacing_min'],
            'min_drill': floor['via_hole_min'], 'min_via_diameter': floor['via_diameter_min'],
            'min_hole_to_hole': floor['pad_hole_to_hole_min'],
            'min_hole_to_hole_note': '0.45 = pad hole-to-hole of different nets; via hole-to-hole is 0.2',
            'min_copper_edge_clearance': floor['copper_to_routed_edge_min'],
            'min_text_height': floor['silk_text_height_min'], 'min_text_thickness': floor['silk_line_min'],
            'npth_min_diameter': floor['npth_hole_min'], 'pth_annular_min': floor['pth_annular_min'],
            'pth_annular_recommended': floor['pth_annular_recommended']},
        'instances': {
            'template_nets': template_nets,
            'list': [{'id': 'RF', 'placement': 'default', 'qty': 1,
                      'refs': {p['ref']: (None if p['source'] == 'pilot_placeholder' else p['ref']) for p in parts},
                      'nets': {n: n for n in template_nets},
                      'source': 'one RF board per device (mechanical/params/boards.json RF; contract placement default)'}],
            'spares': 0,
            'spares_source': 'no spare stated for the RF board (mechanical/params/boards.json RF)'},
        'parts': parts,
        'holes': {'from_contract': True, 'ref_prefix': 'H', 'keepout_layers': ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'],
                  'keepout_blocks': ['tracks', 'vias', 'zone_fills']},
        'groups': [],
        'rf50_taper': {ref: {'max_len_mm': TAPER_LEN, 'min_width_mm': TAPER_W,
                             'reason': ('HMC7992 QFN-16 pins are 0.25 mm wide at 0.5 mm pitch: the RF50 line enters each '
                                        'RF pin at pad width for 0.84 mm (pad half-length 0.4125 + 0.43), then widens to '
                                        '0.36 mm; the board_gen side has no RF_TAPER rule area yet (rf_copper_not_drawn)')}
                       for ref in ('U405', 'U406', 'U407')},
        'pre_route': {
            'tracks': TRACKS,
            'zones': [{'id': 'GND-L2', 'net': 'GND', 'layer': 'In1.Cu', 'outline': 'board', 'priority': 0,
                       'why': 'solid L2 GND under the RF50 CPWG; exported to Freerouting as a plane, so GND pads fan out to it'}]},
        'post_route_zones': [
            {'id': 'GND-F', 'net': 'GND', 'layer': 'F.Cu', 'outline': 'board', 'priority': 0},
            {'id': 'GND-L3', 'net': 'GND', 'layer': 'In2.Cu', 'outline': 'board', 'priority': 0},
            {'id': 'GND-B', 'net': 'GND', 'layer': 'B.Cu', 'outline': 'board', 'priority': 0}],
        'height_zones': enc['height_zones'],
        'router': {'tool': 'freerouting', 'max_passes': 40, 'threads': 1, 'job_timeout': '00:20:00', 'timeout_s': 1500},
        'drc_policy': enc['drc_policy'],
        'rf_copper_not_drawn': {
            'status': 'OPEN: pcb/board_gen.py has no via, plated-hole or rule-area primitive in pre_route (W2 PCB-RF-1 finding)',
            'items': [
                'GND via fences 0.3/0.6 mm at <= 2.0 mm pitch along every RF50 line (netclasses.json RF50 fence_pitch_max_mm, fence_row_max_from_gap_mm)',
                'HMC7992 EPAD via arrays (ADI land pattern) under U405/U406/U407; Freerouting fans each EPAD out to the In1.Cu plane with single vias only',
                'GND stitching of the four GND layers outside the pad fan-outs',
                'GND fence ring around each HMC section for an optional shield can (no can fitted, no MPN)',
                'BOND-RF: plated M3 hole on CHASSIS at (92, 40.5); here H5 stays NPTH and PH407 is the CHASSIS land',
                'DC_CORE SENSE nets pre-routed with a GND guard (Freerouting routes them in this revision)',
                'RF_TAPER rule areas for the 0.25 mm HMC pin entries (check_boards rf50_taper names them)',
                'keeping Freerouting off In1.Cu (layer type power or plane_as_obstacle; the board_gen command line fixes neither)'],
            'owner': 'board_gen.py owner (PCB-PIPE lineage) or INT; PCB-RF-2 draws them once the primitive exists'},
        'decisions': [
            {'topic': 'Shield can over the HMC sections',
             'choice': 'no can fitted in this revision; a GND fence ring per HMC section is reserved (rf_copper_not_drawn)',
             'reason': 'STACK.md names an optional shield wall or lid; a ring costs only copper and invents no MPN (A-PCB-06 decision)'},
            {'topic': 'Impedance coupon', 'choice': 'breakaway tab of the RF panel, built in PCB-RF-2',
             'reason': 'same lamination and etch as the board (A-PCB-06 decision)'},
            {'topic': 'Edge SMA side (J409-J412, J426)',
             'choice': 'top edge (y 44.5), beside the U.FL ports, instead of the bottom edge [100,184]',
             'reason': ('the 73251-1153 body reaches 9.5 mm beyond the board edge (footprint courtyard -14.29 to -4.76 mm '
                        'local), while RF.r0 is 0.4 mm from rfbay.wall.bottom (mechanical/generated/fit-report.md); '
                        'beyond the top edge the bay has 18.3 mm (bay inner height 62.7 from y 99.1; board top at '
                        'enclosure y 143.5). The V4L SMA ends sit at board x 81.6 (arrangement b), so J410/J411 at '
                        'x 65-123 keep the cables short. MODEL reasoning; MECH must model the SMA overhang (OPEN).')},
            {'topic': 'Board ends that the graph lacks',
             'choice': ('U.FL lands (KiCad 10.0.7 U.FL_Hirose_U.FL-R-SMT-1_Vertical, the land of GR-2 J423-J427) as '
                        'pilot placeholders PH401-PH406, and a 2 mm pad PH407 for CHASSIS'),
             'reason': 'design/** is outside PCB-RF-1; the boundary audit reports them provisional until GR-4/SRC-2 add the refs'},
            {'topic': 'S03/S04 headers', 'choice': 'bottom edge x 120-171, openings to the edge',
             'reason': 'harness routes S03/S04 reach the RF bottom edge at board x 163.3 and 167.5 (mechanical/generated/harness-routes.json)'},
            {'topic': 'DC_CORE placement',
             'choice': 'x 132-176 in channel rows (UHF, LBAND, HF top to bottom) with the reference and reference-good blocks to the right',
             'reason': ('the prototype positions (generate_routed.py:25-44) span 59 x 67 mm for 2-layer routing and do not '
                        'fit the 44.5 mm board; the channel order and part grouping are kept, the 12 bleeds stay at the '
                        'ports 25-100 mm away (DC-01, DC-02)')}],
    }


def build():
    GEO.clear(); PLACED.clear(); ANCHORS.clear(); TRACKS.clear(); CHECK_PAIRS.clear()
    graph = bg.load_graph()
    manifest = bg.read_json(bg.MANIFEST)
    fps = {f['footprint']: f for f in manifest['footprints']}
    partition = bg.read_json(BASE / 'pcb/generated/partition.json')
    refs = sorted((p['ref'] for p in partition['parts'] if p['board_candidate'] in DOMAINS and not p['dnp']), key=bg.sort_ref)
    lib = bg.image_library_dir()
    for ref in refs:
        fp = graph[ref]['footprint']
        GEO[ref] = bg.footprint_geometry((BASE / fps[fp]['file']).read_text(encoding='utf-8'))
    for ref, (net, what, img) in PLACEHOLDERS.items():
        nick, name = img['footprint'].split(':')
        path = (lib / f'{nick}.pretty' / f'{name}.kicad_mod') if lib else None
        if path is None or not path.is_file():
            raise SystemExit(f'rf_layout: KiCad image footprint {img["footprint"]} not found (set KICAD10_FOOTPRINT_DIR)')
        if bg.sha256_file(path) != img['sha256']:
            raise SystemExit(f'rf_layout: {path} sha256 differs from the recorded {img["sha256"]}')
        GEO[ref] = bg.footprint_geometry(path.read_text(encoding='utf-8'))
    layout()
    missing = sorted(set(GEO) - set(ANCHORS), key=bg.sort_ref)
    if missing:
        raise SystemExit(f'rf_layout: not placed: {missing}')
    nets = sorted({p['net'] for r in refs for p in graph[r]['pins'] if p.get('net')} |
                  {n for n, _w, _i in PLACEHOLDERS.values()} | {'GND'})
    parts = []
    for ref in refs:
        parts.append({'ref': ref, 'source': 'graph', 'anchor': ANCHORS[ref]})
    for ref, (net, what, img) in PLACEHOLDERS.items():
        pins = {'1': net} if img is TP_IMAGE else {'1': net, '2': 'GND'}
        parts.append({
            'ref': ref, 'source': 'pilot_placeholder', 'footprint': img['footprint'], 'footprint_library': 'kicad-image',
            'footprint_sha256': img['sha256'], 'footprint_sha256_source': img['source'],
            'value': f'{what} board end, placeholder', 'pins': pins,
            'pins_source': ('design/E4.json: the net reaches only off-board modules (boundary would be dangling); '
                            'pad 1 = centre / land, pad 2 = shield (GND)'),
            'replaced_by': 'GR-4 graph ref for this board end (cable assembly and length: SRC-2)'
                           if ref != 'PH407' else 'BOND-RF plated hole once board_gen.py has a plated-hole primitive',
            'pending': (f'board end of {net} pending GR-4' if ref != 'PH407'
                        else 'BOND-RF plated hole pending a board_gen primitive'),
            'why_placeholder': (f'{what}: no board-side connector ref exists in design/E*.json, and design/** is outside '
                                'PCB-RF-1' if ref != 'PH407' else
                                'parts DB NT-RF-CHASSIS: the chassis side of NT401 lands on a plated mounting hole and '
                                'M3 screw; board_gen.py draws only NPTH contract holes, so the land sits beside H5'),
            'anchor': ANCHORS[ref]})
    enc = bg.read_json(BASE / 'pcb/boards/ENC.json')
    classes = net_classes(nets)
    spec = spec_doc(nets, parts, enc)
    contract, _stack = bg.load_contract(spec)
    template = bg.resolve(spec, graph, manifest)
    problems = checks(template, contract, classes)
    return spec, project_text(classes), problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args(argv)
    spec, project, problems = build()
    text = bg.dump(spec)
    for p in problems:
        print('layout:', p)
    if args.check:
        stale = [str(p.relative_to(BASE)) for p, t in ((SPEC, text), (PROJECT, project))
                 if not p.is_file() or p.read_text(encoding='utf-8') != t]
        for s in stale:
            print('stale:', s)
        return 1 if stale or problems else 0
    bg.atomic_write(SPEC, text)
    bg.atomic_write(PROJECT, project)
    print(f'wrote {SPEC.relative_to(BASE)} ({len(spec["parts"])} parts, {len(TRACKS)} scripted tracks) and '
          f'{PROJECT.relative_to(BASE)}; {len(problems)} layout problem(s)')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
