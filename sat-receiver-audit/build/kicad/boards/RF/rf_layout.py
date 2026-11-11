#!/usr/bin/env python3
"""Write the RF board spec pcb/boards/RF.json and its project build/kicad/boards/RF/RF.kicad_pro (W2 PCB-RF-1, PCB-RF-2).

Standard library only. Run from any directory:
  python3 build/kicad/boards/RF/rf_layout.py           write both files
  python3 build/kicad/boards/RF/rf_layout.py --check   fail unless both reproduce and the layout checks pass

The layout is written here as code (anchors, packed rows, RF50 paths), so a placement change is one edit and
the geometry checks below run on every write: courtyard overlaps, pads against the outline and the hole
keepouts, scripted RF copper against foreign pads and tracks, tap and decoupling distances. PCB-RF-2 adds the
scripted GND vias (exposed pads, pad fan-outs, RF50 fences, HMC rings, stitching; rf_copper.py), the DC_CORE SENSE
copper, the BOND-RF plated hole and the breakaway impedance coupon, with their checks (RF50 fence pitch, SENSE length
against the prototype, bleeds outside the DC_CORE keepout); the spec key rf_checks hands the tap, keepout and SENSE
limits to pcb/check_boards.py, which measures them again on the routed board. pcb/board_gen.py reads only the written spec.
CI/model geometry; no hardware or bench gate is closed by it.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3] if (HERE.parents[3] / 'pcb/board_gen.py').is_file() else Path(os.environ['SR_RX_BASE'])
sys.path.insert(0, str(BASE / 'pcb'))
sys.path.insert(0, str(HERE))
import board_gen as bg  # noqa: E402
import rf_copper as rc  # noqa: E402

SPEC = BASE / 'pcb/boards/RF.json'
PROJECT = BASE / 'build/kicad/boards/RF/RF.kicad_pro'
ENC_PROJECT = BASE / 'build/kicad/boards/ENC/ENC.kicad_pro'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
PROTOTYPE_REVIEW = BASE / 'verification/pcb-prototype-review.json'
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
PLACEHOLDERS = {
    'PH401': ('E4_RF_CH1', 'A402 SAWbird+ NOAA OUT (E4_RF_CH1)', UFL_IMAGE),
    'PH402': ('E4_RF_CH5_DC', 'A405 VAT attenuator IN (E4_RF_CH5_DC)', UFL_IMAGE),
    'PH403': ('E4_RF_CH5_ATT', 'A405 VAT attenuator OUT (E4_RF_CH5_ATT)', UFL_IMAGE),
    'PH404': ('E4_HF_BT', 'A406 Boni bias-tee RF port (E4_HF_BT)', UFL_IMAGE),
    'PH405': ('E4_HF_CM', 'W408 OUT / A406 ANT tap point (E4_HF_CM)', UFL_IMAGE),
    'PH406': ('E4_HFP_ANT', 'A414 Airspy HF+ ANT (E4_HFP_ANT)', UFL_IMAGE),
}
# BOND-RF (W2 PCB-RF-2): the contract hole H5 at (92, 40.5) is plated on CHASSIS with a land of the keepout diameter
# (board_gen bond_hole); NT401 sits outside the keepout and ties it to GND (the PCB-RF-1 land PH407 is gone).
BOND = {'at': [92.0, 40.5], 'net': 'CHASSIS', 'pad_mm': 7.0}
# Impedance coupon (W2 PCB-RF-2): two RF50 CPWG thru lines, 50 and 25 mm board edge to board edge, each between two
# edge SMAs of the J409-J412 land, on separate outlines beside the board (a breakaway part of the same panel).
SMA_FP = 'SR_RX_Custom:SMA_Molex_73251-1153_EdgeMount_Horizontal_CS'
SMA_EDGE = 4.76                      # board edge at footprint x -4.76 (the J409-J412 placement)
COUPON_Y = (-22.0, -4.0)             # coupon outline y span (board mm, below the board; SMA legend 2 mm inside)
# (line net, x0, x1, left SMA, right SMA, ground net): each coupon is a separate piece, so its ground is its own net
# (one GND net on two pieces would be two unconnected GND islands for KiCad)
COUPONS = [('CPN_THRU_50', 0.0, 50.0, 'CPN1', 'CPN2', 'CPN_GND_50'), ('CPN_THRU_25', 70.0, 95.0, 'CPN3', 'CPN4', 'CPN_GND_25')]

GEO, PLACED, ANCHORS, TRACKS, CHECK_PAIRS, GAPS = {}, {}, {}, [], [], []
VIAS, GND_TRACKS, COPPER_LOG, COUPON = [], [], {}, {}


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


def split_at_pads():
    """Insert a vertex at every same-net pad centre that a scripted segment passes over, so each pad on the line
    ends a segment (Freerouting counts a pin as connected only at a wire end; route run 42414473163 listed the
    pass-through pads as unrouted although KiCad connectivity was complete)."""
    centres = {}
    for ref, placed in PLACED.items():
        for num, pts in placed['pads'].items():
            for x, y in pts:
                centres.setdefault(ref, []).append((num, (x, y)))
    for t in TRACKS:
        out = [tuple(t['path'][0])]
        for a, b in zip(t['path'], t['path'][1:]):
            inner = []
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            for ref, items in centres.items():
                for num, c in items:
                    if NET_OF.get((ref, num)) != t['net']:
                        continue
                    if seg_point(c, a, b) < 1e-6 and min(math.hypot(c[0] - a[0], c[1] - a[1]),
                                                         math.hypot(c[0] - b[0], c[1] - b[1])) > 1e-6:
                        inner.append((math.hypot(c[0] - a[0], c[1] - a[1]) / L, c))
            out += [c for _t, c in sorted(set(inner))] + [tuple(b)]
        t['path'] = [[bg.r4(x), bg.r4(y)] for x, y in out]


NET_OF = {}


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
    # NT401: the single GND/CHASSIS tie at the BOND-RF hole (92, 40.5): its CHASSIS pad just outside the 7.0 mm keepout,
    # a 1.0 mm CHASSIS track into the plated land of H5 (board_gen bond_hole, W2 PCB-RF-2)
    anchor('NT401', (92.0, 33.4), 90)
    n2 = pad('NT401', 2)
    track('CHASSIS', [n2, (n2[0], BOND['at'][1] - BOND['pad_mm'] / 2 + 0.6)], 1.0,
          'NT401 CHASSIS pad into the plated BOND-RF land of H5 (scripted, locked)')

    # U405 RTL-A
    pad_at('C405', 1, (pad('U405', 15)[0], 30.52), 90)
    anchor('C404', (120.1, 27.75), 0)
    anchor('C403', (120.1, 26.25), 0)
    anchor('C402', (126.4, 26.25), 180)
    anchor('C401', (126.4, 27.75), 0)
    pad_at('R405', 1, (128.1, 27.75), 0)
    anchor('A424', (112.6, 31.0), 90)
    anchor('C446', (109.57, 29.73), 90)
    track('BIAS_CH4', [pad('C446', 1), pad('A424', 1)], 0.35,
          'BIAS_CH4 at the A424 DC pin: decoupling to pin, then a scripted via (escape) out of the RF50 fences (PWR1A 0.35)')  # beside the A424 DC pin, clear of the E4_P2 fence (W2 PCB-RF-2)
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

    # ---------------- DC_CORE (x 132-152): three channel blocks (UHF, LBAND, HF top to bottom). W2 PCB-RF-2: each block is
    # laid out for a short SENSE node (DC-02): the high comparator (U451-type, rot 90) and the low one (U450-type, rot 270)
    # face each other with IN- (pin 4) and IN+ (pin 3) 1.6 mm apart; the divider (R4421-type 23.2 k from the tap, R4422-type
    # 49.9 k from the reference), the 10 nF filter and the BAV199 clamp sit right above them, so the scripted SENSE copper
    # (sense()) stays far below the prototype SENSE length (verification/pcb-prototype-review.json, 17.641 mm per net).
    # The gate pairs (100 ohm / 100 k) and the AO3400A pair sit to the right, the 100 nF decoupling at each V+ pin (DC-03).
    for i, (y0, name) in enumerate(((34.3, 'UHF'), (23.7, 'LBAND'), (13.1, 'HF'))):
        r, u, q = 4420 + i * 10, 450 + i * 2, 450 + i * 2
        X = 136.0
        anchor(f'U{u + 1}', (X, y0), 90)
        anchor(f'U{u}', (X + 3.5, y0), 270)
        anchor(f'R{r + 1}', (X + 1.75, y0 + 3.03), 270)
        anchor(f'C{r + 1}', (X + 3.72, y0 + 2.83), 0)
        anchor(f'R{r + 2}', (X - 0.22, y0 + 2.83), 0)
        anchor(f'D{451 + i}', (X + 2.945, y0 + 5.92), 270)
        anchor(f'C{4411 + i * 2}', (X - 2.48, y0 + 0.5), 90)
        anchor(f'C{4410 + i * 2}', (X + 5.98, y0 - 1.1375), 90)
        row([(f'Q{q}', 0), (f'Q{q + 1}', 0)], X + 7.1, y0 + 1.55)
        row([(f'R{r + 3}', 90), (f'R{r + 4}', 90), (f'R{r + 5}', 90), (f'R{r + 6}', 90)], X + 7.1, y0 - 1.75)
        CHECK_PAIRS.extend([(f'C{4411 + i * 2}', f'U{u + 1}', '6'), (f'C{4410 + i * 2}', f'U{u}', '6')])
        sense(f'E4_DCS_{name}_SENSE', f'U{u + 1}', f'U{u}', f'R{r + 1}', f'C{r + 1}', f'R{r + 2}', f'D{451 + i}')
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


SENSE_W = 0.2


def sense(net, hi, lo, rtap, cfilt, rref, clamp):
    """Scripted SENSE copper of one detector channel (class DCSENSE: not autorouted, 0.30 mm to other nets)."""
    a4, b3 = pad(hi, 4), pad(lo, 3)
    r2, c1, q2, d3 = pad(rtap, 2), pad(cfilt, 1), pad(rref, 2), pad(clamp, 3)
    why = 'DC_CORE SENSE node (scripted, locked; guard: F.Cu GND pour at the DCSENSE clearance over the solid In1.Cu GND)'
    track(net, [a4, b3], SENSE_W, why)                         # IN- of the high and IN+ of the low comparator
    track(net, [(r2[0], a4[1]), r2], SENSE_W, why)              # up to the 23.2 k tap divider
    track(net, [(q2[0], r2[1]), (c1[0], r2[1])], SENSE_W, why)  # 49.9 k reference divider - 23.2 k - 10 nF filter
    track(net, [c1, d3], SENSE_W, why)                          # BAV199 clamp


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
                if [hx, hy] == BOND['at'] and t['net'] == BOND['net']:
                    continue  # the bond track enters the plated BOND-RF land
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


CLEAR = {'Default': 0.15, 'RF50': 0.2, 'DCTAP': 0.3, 'PWR1A': 0.15, 'DCSENSE': 0.3, 'SCRIPTED': 0.15}
# Project-only net classes (W2 PCB-RF-2; pcb/generated/netclasses.json keeps the graph classes): DCSENSE = the three
# detector SENSE nodes (scripted copper, 0.30 mm to other nets like DCTAP, so the GND pour guards them), SCRIPTED = GND
# and CHASSIS (all copper scripted: pad fan-outs, fences, pours, the bond track). Freerouting skips both and RF50.
PROJECT_ONLY = {'DCSENSE': ('E4_DCS_UHF_SENSE', 'E4_DCS_LBAND_SENSE', 'E4_DCS_HF_SENSE'), 'SCRIPTED': ('GND', 'CHASSIS')}
DC_KEEPOUT_MM = 5.0                  # bleeds stay this far outside the DC_CORE courtyard box (DC-01, DC-02)
BLEEDS = ['R4460', 'R4461', 'R4462', 'R4463', 'R4464', 'R4465', 'R4466', 'R4467', 'R4468', 'R4469', 'R4470', 'R4471']
TAPS = (('R4420', 'C4420'), ('R4430', 'C4430'), ('R4440', 'C4440'))  # 26.7 k DC tap and its first 100 pF (DC-01)


def net_classes(nets):
    nc = bg.read_json(NETCLASSES)
    out = {}
    for n in nets:
        cls = (nc['nets'].get(n) or {}).get('class')
        if cls in ('RF50', 'DCTAP', 'PWR1A'):
            out[n] = cls
    for cls, members in PROJECT_ONLY.items():
        for n in members:
            if n in nets:
                out[n] = cls
    for net, *_rest in COUPONS:  # coupon lines: board-only nets, RF50 geometry
        out[net] = 'RF50'
    return out


def project_text(classes):
    proj = json.loads(ENC_PROJECT.read_text(encoding='utf-8'))
    proj['meta']['filename'] = 'RF.kicad_pro'
    base = proj['net_settings']['classes'][0]
    base.update({'clearance': 0.15, 'track_width': 0.2})
    rows = [base]
    for prio, (name, width, clear) in enumerate((('RF50', 0.36, 0.2), ('DCTAP', 0.2, 0.3), ('PWR1A', 0.35, 0.15),
                                                 ('DCSENSE', 0.2, 0.3), ('SCRIPTED', 0.3, 0.15))):
        rows.append(dict(base, name=name, priority=prio, track_width=width, clearance=clear))
    proj['net_settings']['classes'] = rows
    # Pours: 0.20 mm to other nets (the RF50 CPWG gap; DCTAP keeps 0.30 through its class), thermal spokes that fit
    # 0.25 mm QFN pins. board_gen creates its zones with these project defaults (route run 42414473163: 0.3/0.5/0.5).
    proj['board']['design_settings']['defaults']['zones'] = {
        'min_clearance': 0.2, 'min_thickness': 0.25, 'thermal_relief_gap': 0.25, 'thermal_relief_spoke_width': 0.3}
    # min_thickness stays 0.25: 0.2 left twelve 0.004 mm pour necks (connection_width) in route run 42415959957.
    # Hole to hole: the JLC pad hole-to-hole floor 0.45 (via to via 0.2, netclasses.json fab_floor); 0.6/0.3 vias at
    # 0.15 mm clearance sit 0.45 mm apart, which the project value 0.5 refused in route run 42414473163.
    proj['board']['design_settings']['rules']['min_hole_to_hole'] = 0.45
    # One resolved spoke: a HMC7992 GND pin between two RF pins (0.25 mm pads, 0.5 mm pitch) can only take the outward
    # spoke; its return is the EPAD and the GND fan-out vias (13 starved_thermal errors in route run 42414473163).
    proj['board']['design_settings']['rules']['min_resolved_spokes'] = 1
    proj['net_settings']['netclass_patterns'] = [{'netclass': c, 'pattern': n} for n, c in sorted(classes.items())]
    return json.dumps(proj, indent=2, ensure_ascii=False) + '\n'


def spec_doc(template_nets, parts, enc):
    nc = bg.read_json(NETCLASSES)
    floor = nc['fab_floor']['jlc_4l_1oz']
    log = {k: v for k, v in COPPER_LOG.items() if not k.startswith('_')}
    coupon_spec = {k: v for k, v in COUPON.items() if not k.startswith('_')}
    coupon_spec = {'why': ('impedance coupon on a breakaway part of the RF panel (A-PCB-06 decision): two RF50 CPWG thru '
                           'lines, 50 and 25 mm board edge to board edge between Molex 73251-1153 edge SMAs (the '
                           'J409-J412 land), same stackup, lamination and etch as the board; TDR / S21 of the 25 mm '
                           'difference is a bench measurement (OPEN)'), **coupon_spec}
    only_refs = {'H5': 'BOND-RF plated contract hole (92, 40.5) on CHASSIS (bond_hole; NT401 ties it to GND)'}
    only_pins = {'H5': {'1': 'CHASSIS'}}
    for net, x0, x1, left, right, gnd in COUPONS:
        for ref in (left, right):
            only_refs[ref] = f'impedance coupon SMA of {net} ({x1 - x0:g} mm thru line), on the breakaway coupon outline'
            only_pins[ref] = {'CENTER': net, 'SHIELD': gnd}
    return {
        'schema': bg.SPEC_SCHEMA,
        'board_id': 'RF',
        'status': 'RF2_ROUTED_NOT_FOR_FABRICATION',
        'title': 'RF / detector board (RF_HMC, RF_HF, RF_INJECTOR, DC_CORE) 184 x 44.5 - routed CI model with impedance coupon',
        'note': ('W2 PCB-RF-1 placed every RF-domain ref and scripted the RF50 copper; W2 PCB-RF-2 adds the scripted GND '
                 'vias, the SENSE copper, the BOND-RF plated hole and the coupon and routes the rest with Freerouting. '
                 'Written by build/kicad/boards/RF/rf_layout.py (edit the layout there, then rerun it). Nothing here is '
                 'a fabrication release; bench gates stay OPEN.'),
        'contract': {'file': 'mechanical/generated/contract/boards.json', 'board': 'RF'},
        'contract_transform': {'origin': [100.0, 144.5], 'y': 'up',
                               'why': 'board_gen frame (contract (0, 0) at KiCad (100, 100 + 44.5)); the coupon outlines '
                                      'below the board would move an Edge.Cuts bounding-box origin'},
        'domains': DOMAINS,
        'partition': 'pcb/generated/partition.json',
        'layers': {
            'copper': 4, 'thickness_mm': 1.6,
            'source': ('contract stackup JLC04161H-7628, 4 layers, 1.6 mm (mechanical/generated/contract/boards.json '
                       'stackup; build/15); RF50 geometry from pcb/generated/netclasses.json (L1 over L2, h 0.2104 mm)'),
            'types': {'In1.Cu': 'power', 'In2.Cu': 'power'},
            'plan': {'F.Cu': 'all parts, RF50 CPWG (scripted, locked), signals, GND pour (coplanar ground)',
                     'In1.Cu': 'solid GND reference plane under RF50 (layer type power: the router puts only vias through it)',
                     'In2.Cu': 'second solid GND plane (layer type power)',
                     'B.Cu': 'signals, GND pour'}},
        'project': 'build/kicad/boards/RF/RF.kicad_pro',
        'rules_file': None,
        'rules_note': ('rules_file stays null (pcb/board_gen.py does not copy .kicad_dru files yet); the net classes '
                       'RF50 0.36/0.20, DCTAP 0.20/0.30 (project rule, not IPC-verified), PWR1A 0.35/0.15, the project '
                       'classes DCSENSE 0.20/0.30 and SCRIPTED 0.30/0.15 and the default 0.20/0.15 live in RF.kicad_pro '
                       '(graph class values from pcb/generated/netclasses.json). Project zone defaults (used by the '
                       'board_gen pours): clearance 0.20 (= RF50 CPWG gap), minimum width 0.25, thermal gap 0.25, spokes '
                       '0.30. min_hole_to_hole 0.45 = JLC pad hole-to-hole floor (via to via 0.2); the ENC value 0.5 '
                       'refused 0.6/0.3 vias at 0.15 mm clearance. min_resolved_spokes 1: a THT GND pin keeps a single '
                       'spoke where the pour reaches it from one side (SMD GND pads connect solid, tht_thermal pours). '
                       'RF_TAPER rule areas are not drawn: without a rules file KiCad enforces no class width, and '
                       'pcb/check_boards.py takes the HMC pin tapers from rf50_taper.'),
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
        'bond_hole': {**BOND, 'why': ('BOND-RF: the RF ground meets the chassis at one point, the M3 screw of contract hole '
                                      'H5; a plated hole with a land of the 7.0 mm keepout on every layer, NT401 just '
                                      'outside the keepout (parts DB NT-RF-CHASSIS; the other five holes stay NPTH)')},
        'board_only_refs': only_refs,
        'board_only_pins': only_pins,
        'coupons': [{'rect': [o[0], o[1], o[2] - o[0], o[3] - o[1]], 'rf50_nets': [c[0]], 'gnd_net': c[5],
                     'reason': f'impedance coupon {c[0]} on its own breakaway outline, ground net {c[5]}'}
                    for o, c in zip(COUPON['outlines'], COUPONS)],
        'groups': [],
        'rf50_taper': {ref: {'max_len_mm': TAPER_LEN, 'min_width_mm': TAPER_W,
                             'reason': ('HMC7992 QFN-16 pins are 0.25 mm wide at 0.5 mm pitch: the RF50 line enters each '
                                        'RF pin at pad width for 0.84 mm (pad half-length 0.4125 + 0.43), then widens to '
                                        '0.36 mm')}
                       for ref in ('U405', 'U406', 'U407')},
        'rf_checks': {
            'why': ('independent checks of the routed board (pcb/check_boards.py rf_nodes; the same limits as rf2_checks() '
                    'here, measured on RF.kicad_pcb): DC taps on their RF50 line and their first 100 pF next to the tap '
                    '(DC-01, <= 2 mm), the 12 bleeds outside the DC_CORE keepout (courtyards + 5 mm; DC-01, DC-02), the '
                    'SENSE copper not longer than the routed prototype (verification/pcb-prototype-review.json; DC-02)'),
            'taps': [{'ref': tap, 'pad': '1', 'max_mm': 2.0} for tap, _cap in TAPS],
            'tap_caps': [{'ref': cap, 'to': [tap, '2'], 'max_mm': 2.0} for tap, cap in TAPS],
            'keepout': {'domains': ['DC_CORE'], 'margin_mm': DC_KEEPOUT_MM, 'refs': BLEEDS},
            'sense': {'nets': list(PROJECT_ONLY['DCSENSE']), 'prototype': PROTOTYPE_REVIEW.relative_to(BASE).as_posix()}},
        'pre_route': {
            'tracks': TRACKS + GND_TRACKS,
            'vias': VIAS,
            'zones': [{'id': 'GND-L2', 'net': 'GND', 'layer': 'In1.Cu', 'outline': 'board', 'priority': 0,
                       'pad_connection': 'solid',
                       'why': 'solid L2 GND under the RF50 CPWG (power layer, a plane in the DSN)'},
                      {'id': 'GND-L3', 'net': 'GND', 'layer': 'In2.Cu', 'outline': 'board', 'priority': 0,
                       'pad_connection': 'solid', 'why': 'second GND plane (power layer)'}]},
        'post_route_zones': [
            {'id': 'GND-F', 'net': 'GND', 'layer': 'F.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'tht_thermal',
             'why': 'coplanar ground of the CPWG; SMD GND pads solid, THT pins with spokes'},
            {'id': 'GND-B', 'net': 'GND', 'layer': 'B.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'tht_thermal'}],
        'height_zones': enc['height_zones'],
        'router': {'tool': 'freerouting', 'max_passes': 40, 'threads': 1, 'job_timeout': '00:20:00', 'timeout_s': 1500,
                   'fanout': False, 'ignore_net_classes': ['RF50', 'DCSENSE', 'SCRIPTED'],
                   'why': ('RF50, the SENSE nodes, GND and CHASSIS are scripted and complete pad to pad, so the router '
                           'leaves them (locked copper that crosses a pad is no connection for it: route run 42416865216 '
                           'listed the HMC pin entries as unrouted); fan-out off: its escape stubs were necked down to '
                           '0.12 mm (route run 42416865216, track_width / connection_width)')},
        'drc_policy': enc['drc_policy'],
        'rf_copper': {
            'label': 'scripted copper of W2 PCB-RF-2 (rf_copper.py); counts are CI/model geometry',
            **log,
            'epad_vias_source': ('project choice: 2 x 2 vias 0.6/0.3 at +/-0.425 mm in the 1.7 mm HMC7992 exposed pad, one '
                                 'in the A407 pad; the ADI HMC7992 data sheet (https://www.analog.com/media/en/technical-'
                                 'documentation/data-sheets/hmc7992.pdf) was not readable 2026-11-07 (connection reset; the '
                                 'Farnell copy https://www.farnell.com/datasheets/2283884.pdf timed out), so its '
                                 'evaluation-board via pattern is TBD and the array is not claimed to follow it'),
            'open': ['solderable GND land and mask opening for a shield can over each HMC section: only the via ring '
                     'is drawn; the land waits for a can MPN (none chosen, A-PCB-06 decision)',
                     'via plugging / tenting of the exposed-pad vias (solder wicking) is an order-time fab option, not set here']},
        'coupon': coupon_spec,
        'decisions': [
            {'topic': 'Shield can over the HMC sections',
             'choice': 'no can fitted in this revision; a GND via ring per HMC section is drawn (rf_copper hmc_ring_vias), '
                       'the solderable can land waits for a can MPN',
             'reason': 'STACK.md names an optional shield wall or lid; a ring costs only copper and invents no MPN (A-PCB-06 decision)'},
            {'topic': 'Impedance coupon',
             'choice': 'breakaway coupon of the RF panel: two RF50 CPWG thru lines 50 and 25 mm (edge to edge) between '
                       'Molex 73251-1153 edge SMAs on two outlines below the board, in the same board file and fab set',
             'reason': ('same lamination and etch as the board (A-PCB-06 decision); two lengths give the per-length loss and '
                        'the launch by difference; board_gen draws the coupon after the SES import, so the router never sees it')},
            {'topic': 'Edge SMA side (J409-J412, J426)',
             'choice': 'top edge (y 44.5), beside the U.FL ports, instead of the bottom edge [100,184]',
             'reason': ('the 73251-1153 body reaches 9.5 mm beyond the board edge (footprint courtyard -14.29 to -4.76 mm '
                        'local), while RF.r0 is 0.4 mm from rfbay.wall.bottom (mechanical/generated/fit-report.md); '
                        'beyond the top edge the bay has 18.3 mm (bay inner height 62.7 from y 99.1; board top at '
                        'enclosure y 143.5). The V4L SMA ends sit at board x 81.6 (arrangement b), so J410/J411 at '
                        'x 65-123 keep the cables short. MODEL reasoning; MECH must model the SMA overhang (OPEN).')},
            {'topic': 'Board ends that the graph lacks',
             'choice': ('U.FL lands (KiCad 10.0.7 U.FL_Hirose_U.FL-R-SMT-1_Vertical, the land of GR-2 J423-J427) as '
                        'pilot placeholders PH401-PH406; the CHASSIS end is the plated BOND-RF hole H5'),
             'reason': 'design/** is outside PCB-RF-1/-2; the boundary audit reports them provisional until GR-4/SRC-2 add the refs'},
            {'topic': 'S03/S04 headers', 'choice': 'bottom edge x 120-171, openings to the edge',
             'reason': 'harness routes S03/S04 reach the RF bottom edge at board x 163.3 and 167.5 (mechanical/generated/harness-routes.json)'},
            {'topic': 'DC_CORE placement',
             'choice': ('x 132-152 in three channel blocks (UHF, LBAND, HF top to bottom), the reference and reference-good '
                        'blocks to the right; per block the two TLV3012 face each other (IN- / IN+) under the divider, '
                        'filter and clamp, so the SENSE node is short'),
             'reason': ('the prototype positions (generate_routed.py:25-44) span 59 x 67 mm for 2-layer routing and do not '
                        'fit the 44.5 mm board; the channel parts are kept together and the scripted SENSE copper stays '
                        'below the prototype SENSE length; the 12 bleeds stay at the ports, outside the DC_CORE keepout '
                        '(DC-01, DC-02)')},
            {'topic': 'BOND-RF hole',
             'choice': 'H5 plated, 3.2 mm hole with a 7.0 mm CHASSIS land on every layer and open mask; NT401 at its edge',
             'reason': 'one GND-CHASSIS tie at the screw that bonds the RF board to the chassis (parts DB NT-RF-CHASSIS)'},
            {'topic': 'Routing of the RF board',
             'choice': ('scripted and locked: RF50, GND (fan-outs, fences, rings, stitching, pours), the SENSE nodes and '
                        'CHASSIS; Freerouting 2.5.0 routes the rest on F.Cu and B.Cu only (In1/In2 are power layers)'),
             'reason': ('keeps the L2 reference solid under every RF50 line (no inner tracks), keeps the router from '
                        'necking down or re-routing scripted nets, and makes the RF-critical copper reproducible from the spec')},
            {'topic': 'SENSE guard',
             'choice': 'project class DCSENSE 0.20/0.30 for the three SENSE nodes: the F.Cu GND pour keeps 0.30 mm around '
                       'them over the solid In1.Cu GND (guard), like the DCTAP project rule',
             'reason': 'DC-02 asks for a clean low-leakage SENSE layout; 0.30 is the DCTAP project rule (not IPC-verified)'}],
    }


def fp_keepouts(text):
    """Keepout zones of a footprint (local mm, KiCad y down) that block vias or tracks: [[(x, y), ...]]."""
    tree = bg.sexpr(text)
    out = []
    for node in tree[1:]:
        if not (isinstance(node, list) and node and node[0] == 'zone'):
            continue
        ko = next((n for n in node if isinstance(n, list) and n and n[0] == 'keepout'), None)
        if ko is None:
            continue
        blocked = {n[0] for n in ko[1:] if isinstance(n, list) and len(n) > 1 and n[1] == 'not_allowed'}
        if not blocked & {'vias', 'tracks'}:
            continue
        poly = next((n for n in node if isinstance(n, list) and n and n[0] == 'polygon'), None)
        pts = next((n for n in poly if isinstance(n, list) and n and n[0] == 'pts'), None) if poly else None
        if pts:
            out.append([(float(x[1]), float(x[2])) for x in pts[1:] if isinstance(x, list) and x[0] == 'xy'])
    return out


def to_board(ref, pt):
    """A footprint-local point (KiCad, y down) on the board (board mm, y up), as bg.placed_geometry places pads."""
    a, g = ANCHORS[ref], GEO[ref]
    rot = float(a.get('rotation', 0))
    lx, ly = bg.turn_point(pt, rot)
    align = a.get('align', 'origin')
    if align == 'origin':
        ax, ay = 0.0, 0.0
    else:
        want = str(align['pad'] if 'pad' in align else align['pad_centroid'])
        pts = [bg.turn_point(p['at'], rot) for p in g['pads'] if str(p['number']) == want]
        ax, ay = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    bx, by = a['at']
    return (bx + lx - ax, by - (ly - ay))


def pad_items(placed, geos, anchors, nets_of):
    """Every copper pad: {ref, num, net, box, center, drill} (board mm); EPAD paste windows and NPTH pads left out."""
    out = []
    for ref, pl in placed.items():
        g, rot = geos[ref], anchors[ref]['rotation']
        for p in g['pads']:
            if p['type'] == 'np_thru_hole' or (not p['number'] and p['type'] == 'smd'):
                continue
            w, h = p['size']
            if int(round(rot / 90.0)) % 2:
                w, h = h, w
            at = {'at': pl['origin'], 'align': 'origin', 'rotation': rot, 'side': 'F'}
            c = bg.placed_geometry({'pads': [dict(p, number='X')], 'courtyard': None}, at)['pads']['X'][0]
            out.append({'ref': ref, 'num': str(p['number']), 'net': nets_of(ref, str(p['number'])),
                        'box': [c[0] - w / 2, c[1] - h / 2, c[0] + w / 2, c[1] + h / 2], 'center': (c[0], c[1]),
                        'drill': p['drill'][0] if p['type'] == 'thru_hole' and p['drill'] else 0.0, 'type': p['type']})
    return out


EPAD_NAMES = {'EPAD', 'EP'}
ESCAPES = [('C446', '1', 'BIAS_CH4')]
NO_FANOUT = {'J409', 'J410', 'J411', 'J412', 'J426',   # edge SMAs: their plated shield pins join every GND layer
             'NT401'}                                    # net tie: its copper bridge is no pad; the pour joins pad 1


def copper(contract, classes):
    """Pad entries, GND vias and the coupon (W2 PCB-RF-2); fills TRACKS, GND_TRACKS, VIAS, COUPON, COPPER_LOG."""
    def clear(net):
        return CLEAR.get(classes.get(net, 'Default'), 0.15)

    def is_rf50(net):
        return classes.get(net) == 'RF50'

    def nets_of(ref, num):
        if ref in PLACEHOLDERS:
            return PLACEHOLDERS[ref][0] if num == '1' else 'GND'
        return NET_OF.get((ref, num))
    pads = pad_items(PLACED, GEO, ANCHORS, nets_of)
    TRACKS[:] = rc.trim_pad_entries(TRACKS, pads, is_rf50, RF_W)
    W, H = contract['outline_mm'][2]
    ko = contract['hole_keepout_d'] / 2
    holes = [((x, y), ko) for x, y in contract['holes_mm'] if [x, y] != BOND['at']]
    keepouts = []
    nt = [p['box'] for p in pads if p['ref'] == 'NT401']  # the net-tie bridge (footprint copper, no net) between its pads
    keepouts.append([min(b[0] for b in nt) - 0.3, min(b[1] for b in nt) - 0.3, max(b[2] for b in nt) + 0.3, max(b[3] for b in nt) + 0.3])
    for ref in sorted(PLACED, key=bg.sort_ref):
        for poly in GEO[ref].get('keepouts', []):
            pts = [to_board(ref, p) for p in poly]
            keepouts.append([min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)])
    cu = rc.Copper([0.0, 0.0, W, H], pads, TRACKS, clear, holes, (tuple(BOND['at']), BOND['pad_mm'] / 2, BOND['net']), keepouts)
    log = collections.OrderedDict()
    by_ref = collections.defaultdict(list)
    for p in pads:
        by_ref[p['ref']].append(p)
    # 1. exposed pads and the QFN GND pins tied to them
    epads = [(p['ref'], p) for p in pads if p['num'] in EPAD_NAMES and p['net'] == 'GND']
    log['epad_vias'] = len(rc.epad_vias(cu, epads))
    stubs, no_stub = [], []
    for ref, ep in epads:
        for p in by_ref[ref]:
            if p['net'] == 'GND' and p['num'] not in EPAD_NAMES:
                t = rc.inward_stub(cu, p, ep, 0.25 if min(p['box'][2] - p['box'][0], p['box'][3] - p['box'][1]) >= 0.25 else 0.2)
                (stubs.append(t) if t else no_stub.append(f'{ref}.{p["num"]}'))
    GND_TRACKS.extend(stubs)
    log['qfn_gnd_pin_stubs'] = len(stubs)
    log['qfn_gnd_pins_on_the_pour'] = no_stub
    # 1b. escape vias of power pads boxed in by the RF50 fences (route run 42421969829 left BIAS_CH4 unrouted at A424)
    esc = []
    for ref, num, net in ESCAPES:
        p = next(q for q in pads if q['ref'] == ref and q['num'] == num)
        res = rc.fanout(cu, p, p['center'], 0.35, net, f'{net} escape of {ref}.{num} to B.Cu (scripted, locked)')
        if res is None:
            raise SystemExit(f'rf_layout: no escape via fits at {ref}.{num}')
        GND_TRACKS.append(res[0])
        esc.append(f'{ref}.{num} {net}')
    log['escape_vias'] = esc
    # 2. a fan-out via at every other SMD GND pad
    fan, nofan = 0, []
    for p in sorted(pads, key=lambda p: (bg.sort_ref(p['ref']), p['num'], p['center'])):
        if p['net'] != 'GND' or p['type'] != 'smd' or p['ref'] in NO_FANOUT or p['ref'] in dict(epads):
            continue
        box = PLACED[p['ref']]['box'] or p['box']
        res = rc.fanout(cu, p, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2))
        if res:
            GND_TRACKS.append(res[0])
            fan += 1
        else:
            nofan.append(f'{p["ref"]}.{p["num"]}')
    log['gnd_fanouts'] = fan
    log['gnd_pads_on_the_pour'] = nofan
    # 3. RF50 fences, 4. GND rings around the HMC7992 sections (optional can, no MPN), 5. stitching
    log['rf50_fence_vias'] = len(rc.fences(cu, TRACKS, is_rf50, RF_W))
    rings = 0
    for hmc, caps in (('U406', ('C406', 'C407', 'C408', 'C409', 'C410')), ('U407', ('C411', 'C414', 'C415', 'C416', 'C417')),
                      ('U405', ('C401', 'C402', 'C403', 'C404', 'C405'))):
        bx = [PLACED[r]['box'] for r in (hmc,) + caps]
        box = [min(b[0] for b in bx) - 0.9, min(b[1] for b in bx) - 0.9, max(b[2] for b in bx) + 0.9, max(b[3] for b in bx) + 0.9]
        rings += len(rc.ring(cu, box, why=f'GND ring around the {hmc} section (optional shield can, no can fitted)'))
    log['hmc_ring_vias'] = rings
    log['stitching_vias'] = len(rc.stitch(cu, [b['box'] for b in PLACED.values() if b['box']]))
    VIAS.extend(cu.via_list)
    gaps = rc.fence_gaps(VIAS, TRACKS, is_rf50, RF_W)
    log['fence_gaps_over_2mm'] = len(gaps)
    COPPER_LOG.update(log)
    COPPER_LOG['_gaps'] = gaps
    COUPON.update(coupon(classes, clear, is_rf50))


def coupon(classes, clear, is_rf50):
    """Two RF50 CPWG thru lines (50 and 25 mm edge to edge) between edge SMAs on outlines below the board."""
    manifest = bg.read_json(bg.MANIFEST)
    entry = next(f for f in manifest['footprints'] if f['footprint'] == SMA_FP)
    g = bg.footprint_geometry((BASE / entry['file']).read_text(encoding='utf-8'))
    y0, y1 = COUPON_Y
    yc = (y0 + y1) / 2
    outlines, fps, tracks, vias, zones, gaps = [], [], [], [], [], []
    for net, x0, x1, left, right, gnd in COUPONS:
        outlines.append([x0, y0, x1, y1])
        placed, anchors, geos = {}, {}, {}
        for ref, at, rot in ((left, (x0 + SMA_EDGE, yc), 0), (right, (x1 - SMA_EDGE, yc), 180)):
            a = {'at': [bg.r4(at[0]), bg.r4(at[1])], 'align': 'origin', 'rotation': rot, 'side': 'F'}
            anchors[ref], geos[ref] = a, g
            placed[ref] = bg.placed_geometry(g, a)
            fps.append({'ref': ref, 'footprint': SMA_FP, 'value': 'Molex 73251-1153 (coupon, hand-fitted for the bench)',
                        'pads': {'CENTER': net, 'SHIELD': gnd}, 'anchor': a})
        pads = pad_items(placed, geos, anchors, lambda r, n, net=net, gnd=gnd: net if n == 'CENTER' else gnd)
        c0 = next(p['center'] for p in pads if p['ref'] == left and p['num'] == 'CENTER')
        c1 = next(p['center'] for p in pads if p['ref'] == right and p['num'] == 'CENTER')
        line = [{'id': f'{net}-1', 'net': net, 'layer': 'F.Cu', 'width_mm': RF_W, 'path': [list(c0), list(c1)], 'locked': True,
                 'why': f'coupon RF50 CPWG thru line, {x1 - x0:g} mm board edge to board edge (scripted, locked)'}]
        line = rc.trim_pad_entries(line, pads, lambda n: True, RF_W)
        cu = rc.Copper([x0, y0, x1, y1], pads, line, clear)
        rc.fences(cu, line, lambda n: True, RF_W, why='coupon RF50 GND fence', net=gnd)
        gaps += rc.fence_gaps(cu.via_list, line, lambda n: True, RF_W)
        for v in cu.via_list:
            v['id'] = f'{net}-{v["id"]}'
        tracks += line
        vias += cu.via_list
        rect = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        for layer in ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'):
            zones.append({'id': f'{gnd}-{layer.split(".")[0]}', 'net': gnd, 'layer': layer, 'outline': rect,
                          'priority': 0, 'pad_connection': 'solid'})
    return {'outlines': outlines, 'footprints': fps, 'tracks': tracks, 'vias': vias, 'zones': zones, '_gaps': gaps}


def build():
    GEO.clear(); PLACED.clear(); ANCHORS.clear(); TRACKS.clear(); CHECK_PAIRS.clear(); NET_OF.clear()
    VIAS.clear(); GND_TRACKS.clear(); COPPER_LOG.clear(); COUPON.clear()
    graph = bg.load_graph()
    manifest = bg.read_json(bg.MANIFEST)
    fps = {f['footprint']: f for f in manifest['footprints']}
    partition = bg.read_json(BASE / 'pcb/generated/partition.json')
    refs = sorted((p['ref'] for p in partition['parts'] if p['board_candidate'] in DOMAINS and not p['dnp']), key=bg.sort_ref)
    domain = {p['ref']: p['board_candidate'] for p in partition['parts']}
    lib = bg.image_library_dir()
    for ref in refs:
        fp = graph[ref]['footprint']
        text = (BASE / fps[fp]['file']).read_text(encoding='utf-8')
        GEO[ref] = dict(bg.footprint_geometry(text), keepouts=fp_keepouts(text))
    for ref, (net, what, img) in PLACEHOLDERS.items():
        nick, name = img['footprint'].split(':')
        path = (lib / f'{nick}.pretty' / f'{name}.kicad_mod') if lib else None
        if path is None or not path.is_file():
            raise SystemExit(f'rf_layout: KiCad image footprint {img["footprint"]} not found (set KICAD10_FOOTPRINT_DIR)')
        if bg.sha256_file(path) != img['sha256']:
            raise SystemExit(f'rf_layout: {path} sha256 differs from the recorded {img["sha256"]}')
        text = path.read_text(encoding='utf-8')
        GEO[ref] = dict(bg.footprint_geometry(text), keepouts=fp_keepouts(text))
    NET_OF.clear()
    for ref in refs:
        for p in graph[ref]['pins']:
            if p.get('net'):
                NET_OF[(ref, str(p['number']))] = p['net']
    layout()
    split_at_pads()
    missing = sorted(set(GEO) - set(ANCHORS), key=bg.sort_ref)
    if missing:
        raise SystemExit(f'rf_layout: not placed: {missing}')
    nets = sorted({p['net'] for r in refs for p in graph[r]['pins'] if p.get('net')} |
                  {n for n, _w, _i in PLACEHOLDERS.values()} | {'GND'} | {c[0] for c in COUPONS} | {c[5] for c in COUPONS})
    classes = net_classes(nets)
    contract = bg.read_json(BASE / 'mechanical/generated/contract/boards.json')['boards']['RF']
    copper(contract, classes)
    parts = []
    for ref in refs:
        parts.append({'ref': ref, 'source': 'graph', 'anchor': ANCHORS[ref]})
    for ref, (net, what, img) in PLACEHOLDERS.items():
        parts.append({
            'ref': ref, 'source': 'pilot_placeholder', 'footprint': img['footprint'], 'footprint_library': 'kicad-image',
            'footprint_sha256': img['sha256'], 'footprint_sha256_source': img['source'],
            'value': f'{what} board end, placeholder', 'pins': {'1': net, '2': 'GND'},
            'pins_source': ('design/E4.json: the net reaches only off-board modules (boundary would be dangling); '
                            'pad 1 = centre / land, pad 2 = shield (GND)'),
            'replaced_by': 'GR-4 graph ref for this board end (cable assembly and length: SRC-2)',
            'pending': f'board end of {net} pending GR-4',
            'why_placeholder': (f'{what}: no board-side connector ref exists in design/E*.json, and design/** is outside '
                                'PCB-RF-1 and PCB-RF-2'),
            'anchor': ANCHORS[ref]})
    enc = bg.read_json(BASE / 'pcb/boards/ENC.json')
    problems = rf2_checks(classes, domain)
    spec = spec_doc(nets, parts, enc)
    contract, _stack = bg.load_contract(spec)
    template = bg.resolve(spec, graph, manifest)
    problems = checks(template, contract, classes) + problems
    return spec, project_text(classes), problems


def rf2_checks(classes, domain):
    """W2 PCB-RF-2 checks on the scripted geometry: fence pitch, SENSE length, bleeds, taps, the bond tie."""
    problems = []
    for net, a, b, side, gap in COPPER_LOG['_gaps'] + COUPON['_gaps']:
        problems.append(f'RF50 fence gap {gap} mm > 2.0 on {net} {a}->{b} side {side}')
    proto = collections.Counter()
    for s in bg.read_json(PROTOTYPE_REVIEW)['routing']:
        proto[s['net']] += s['length_mm']
    for net in sorted(n for n in classes if classes[n] == 'DCSENSE'):
        length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for t in TRACKS if t['net'] == net for a, b in zip(t['path'], t['path'][1:]))
        COPPER_LOG.setdefault('sense_length_mm', {})[net] = {'board': round(length, 3), 'prototype': round(proto[net], 3)}
        if not 0 < length <= proto[net] + 1e-9:
            problems.append(f'SENSE {net} copper {length:.3f} mm is not within the prototype {proto[net]:.3f} mm')
    dc = [PLACED[r]['box'] for r in PLACED if domain.get(r) == 'DC_CORE' and PLACED[r]['box']]
    keep = [min(b[0] for b in dc) - DC_KEEPOUT_MM, min(b[1] for b in dc) - DC_KEEPOUT_MM,
            max(b[2] for b in dc) + DC_KEEPOUT_MM, max(b[3] for b in dc) + DC_KEEPOUT_MM]
    COPPER_LOG['dc_core_keepout'] = [round(v, 3) for v in keep]
    for r in BLEEDS:
        if bg.rects_overlap(PLACED[r]['box'], keep):
            problems.append(f'bleed {r} inside the DC_CORE keepout {keep}')
    COPPER_LOG['bleed_to_dc_core_keepout_mm'] = round(min(rc.box_point(keep, ((PLACED[r]['box'][0] + PLACED[r]['box'][2]) / 2,
                                                                          (PLACED[r]['box'][1] + PLACED[r]['box'][3]) / 2))
                                                         for r in BLEEDS), 3)
    taps = {}
    for tap, cap in TAPS:
        net = NET_OF[(tap, '1')]
        box = next(b for r, n, _net, b in pad_boxes({tap: {'1': net}}) if r == tap and n == '1')
        d = min(rc.seg_box(a, b, box) for t in TRACKS if t['net'] == net for a, b in zip(t['path'], t['path'][1:]))
        dc = bg.box_circle_distance(PLACED[cap]['box'], pad(tap, 2))
        taps[tap] = {'rf_net': net, 'pad1_to_rf50_copper_mm': round(d, 3), cap + '_to_pad2_mm': round(dc, 3)}
        if d > 2.0 or dc > 2.0:
            problems.append(f'tap {tap} is {d:.2f} mm from {net} copper or {cap} {dc:.2f} mm from its pad 2 (limit 2.0)')
    COPPER_LOG['taps'] = taps
    return problems


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
