#!/usr/bin/env python3
"""Write the project footprint library SR_RX_Custom.pretty and fetch official KiCad footprints.

Run from any directory:
  python tools/make_footprints.py            # (re)write SR_RX_Custom.pretty + provenance
  python tools/make_footprints.py --check    # fail if a written file differs
  python tools/make_footprints.py --fetch    # network: fetch missing official footprints

SR_RX_Custom holds two kinds of footprints:
* "custom": drawn here from the manufacturer land pattern named in PROVENANCE (page and
  drawing quoted there). Only numbers printed in that drawing are used.
* "derived": an unmodified-geometry copy of a vendored official KiCad 10.0.7 footprint whose
  pad numbers are renamed to the logical pin numbers of the design graph (A/K, EP, CENTER...).
Official footprints are fetched byte-for-byte from the KiCad library tag 10.0.7 on GitLab;
their SHA256 values are recorded by tools/build_parts.py in footprints/manifest.json.
Nothing here is a fabrication release: every footprint still needs layout review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBDIR = ROOT / 'build/kicad/footprints'
CUSTOM = LIBDIR / 'SR_RX_Custom.pretty'
KICAD_TAG = '10.0.7'
KICAD_RAW = 'https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/' + KICAD_TAG + '/'


def fmt(v: float) -> str:
    s = f'{v:.4f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def xy(x, y):
    return f'(at {fmt(x)} {fmt(y)})'


class FP:
    """Minimal KiCad 10 footprint writer (no uuids; KiCad assigns them on load)."""

    def __init__(self, name, descr, tags, smd=True):
        self.name, self.descr, self.tags, self.is_smd = name, descr, tags, smd
        self.items, self.pads = [], []

    def line(self, x1, y1, x2, y2, layer, w):
        self.items.append(f'\t(fp_line\n\t\t(start {fmt(x1)} {fmt(y1)})\n\t\t(end {fmt(x2)} {fmt(y2)})\n\t\t(stroke\n\t\t\t(width {fmt(w)})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "{layer}")\n\t)')

    def rect(self, x1, y1, x2, y2, layer, w):
        self.items.append(f'\t(fp_rect\n\t\t(start {fmt(x1)} {fmt(y1)})\n\t\t(end {fmt(x2)} {fmt(y2)})\n\t\t(stroke\n\t\t\t(width {fmt(w)})\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "{layer}")\n\t)')

    def circle(self, cx, cy, r, layer, w):
        self.items.append(f'\t(fp_circle\n\t\t(center {fmt(cx)} {fmt(cy)})\n\t\t(end {fmt(cx + r)} {fmt(cy)})\n\t\t(stroke\n\t\t\t(width {fmt(w)})\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "{layer}")\n\t)')

    def text(self, s, x, y, layer, size=1.0):
        self.items.append(f'\t(fp_text user "{s}"\n\t\t{xy(x, y)}\n\t\t(layer "{layer}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {fmt(size)} {fmt(size)})\n\t\t\t\t(thickness {fmt(size * 0.15)})\n\t\t\t)\n\t\t)\n\t)')

    def smd(self, num, x, y, w, h, shape='roundrect', paste=True):
        layers = '"F.Cu" "F.Mask" "F.Paste"' if paste else '"F.Cu" "F.Mask"'
        extra = '\n\t\t(roundrect_rratio 0.25)' if shape == 'roundrect' else ''
        self.pads.append(f'\t(pad "{num}" smd {shape}\n\t\t{xy(x, y)}\n\t\t(size {fmt(w)} {fmt(h)})\n\t\t(layers {layers}){extra}\n\t)')

    def paste(self, x, y, w, h):
        self.pads.append(f'\t(pad "" smd roundrect\n\t\t{xy(x, y)}\n\t\t(size {fmt(w)} {fmt(h)})\n\t\t(layers "F.Paste")\n\t\t(roundrect_rratio 0.25)\n\t)')

    def poly_pad(self, num, ax, ay, pts, aw, ah):
        """Custom SMD pad: anchor rectangle aw x ah at (ax, ay) plus a polygon (absolute coords)."""
        rel = ' '.join(f'(xy {fmt(px - ax)} {fmt(py - ay)})' for px, py in pts)
        self.pads.append(f'\t(pad "{num}" smd custom\n\t\t{xy(ax, ay)}\n\t\t(size {fmt(aw)} {fmt(ah)})\n\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n\t\t(options\n\t\t\t(clearance outline)\n\t\t\t(anchor rect)\n\t\t)\n\t\t(primitives\n\t\t\t(gr_poly\n\t\t\t\t(pts\n\t\t\t\t\t{rel}\n\t\t\t\t)\n\t\t\t\t(width 0)\n\t\t\t\t(fill yes)\n\t\t\t)\n\t\t)\n\t)')

    def tht(self, num, x, y, size, drill, shape='circle', drill_oval=None):
        sx, sy = (size, size) if not isinstance(size, tuple) else size
        d = f'(drill oval {fmt(drill_oval[0])} {fmt(drill_oval[1])})' if drill_oval else f'(drill {fmt(drill)})'
        self.pads.append(f'\t(pad "{num}" thru_hole {shape}\n\t\t{xy(x, y)}\n\t\t(size {fmt(sx)} {fmt(sy)})\n\t\t{d}\n\t\t(layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n\t)')

    def render(self, ref_y, val_y):
        head = [f'(footprint "{self.name}"', '\t(version 20260206)', '\t(generator "sr_rx_make_footprints")', '\t(generator_version "10.0")', '\t(layer "F.Cu")',
                f'\t(descr "{self.descr}")', f'\t(tags "{self.tags}")']
        for prop, value, y, layer, hide in (('Reference', 'REF**', ref_y, 'F.SilkS', False), ('Value', self.name, val_y, 'F.Fab', False),
                                            ('Datasheet', '', 0, 'F.Fab', True), ('Description', '', 0, 'F.Fab', True)):
            h = '\n\t\t(hide yes)' if hide else ''
            head.append(f'\t(property "{prop}" "{value}"\n\t\t(at 0 {fmt(y)} 0)\n\t\t(layer "{layer}"){h}\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)')
        head.append('\t(attr smd)' if self.is_smd else '\t(attr through_hole)')
        return '\n'.join(head + self.items + [f'\t(fp_text user "${{REFERENCE}}"\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 0.5 0.5)\n\t\t\t\t(thickness 0.08)\n\t\t\t)\n\t\t)\n\t)'] + self.pads + ['\t(embedded_fonts no)', ')']) + '\n'


def box(fp, bx, by, cx, cy, pad=0.25):
    """Fab body outline bx*by and a courtyard around body and pads (cx, cy half extents)."""
    fp.rect(-bx / 2, -by / 2, bx / 2, by / 2, 'F.Fab', 0.1)
    ex, ey = max(bx / 2, cx) + pad, max(by / 2, cy) + pad
    fp.rect(-ex, -ey, ex, ey, 'F.CrtYd', 0.05)
    return ex, ey


def qfn(name, descr, n_side, pitch, pad_l, pad_w, row, body, ep, ep_name, ep_paste):
    """TI-style quad no-lead: pin 1 top of the left side, counter-clockwise."""
    fp = FP(name, descr, 'QFN VQFN TI land pattern')
    half = (n_side - 1) * pitch / 2
    num = 1
    for i in range(n_side):  # left, top->bottom
        fp.smd(num, -row, -half + i * pitch, pad_l, pad_w); num += 1
    for i in range(n_side):  # bottom, left->right
        fp.smd(num, -half + i * pitch, row, pad_w, pad_l); num += 1
    for i in range(n_side):  # right, bottom->top
        fp.smd(num, row, half - i * pitch, pad_l, pad_w); num += 1
    for i in range(n_side):  # top, right->left
        fp.smd(num, half - i * pitch, -row, pad_w, pad_l); num += 1
    fp.smd(ep_name, 0, 0, ep, ep, shape='rect', paste=False)
    n, size = ep_paste
    step = ep / n
    for ix in range(n):
        for iy in range(n):
            fp.paste(-ep / 2 + step * (ix + 0.5), -ep / 2 + step * (iy + 0.5), size, size)
    ex, ey = box(fp, body, body, row + pad_l / 2, row + pad_l / 2)
    c = body / 2 + 0.11
    fp.line(-c, -c + 0.6, -c, -c, 'F.SilkS', 0.12); fp.line(-c, -c, -c + 0.6, -c, 'F.SilkS', 0.12)
    fp.line(c, c - 0.6, c, c, 'F.SilkS', 0.12); fp.line(c, c, c - 0.6, c, 'F.SilkS', 0.12)
    fp.line(c, -c + 0.6, c, -c, 'F.SilkS', 0.12); fp.line(c, -c, c - 0.6, -c, 'F.SilkS', 0.12)
    fp.circle(-row - pad_l / 2 - 0.35, -half, 0.12, 'F.SilkS', 0.12)
    return fp.render(-ey - 0.8, ey + 0.8)


def rpw0010a():
    """TI RPW0010A VQFN-HR (TPS25947xx), land pattern example 4225183/A."""
    fp = FP('TI_RPW0010A_VQFN-HR-10_2x2mm_P0.5mm', 'TI RPW0010A VQFN-HR 10 pin 2x2 mm; TI land pattern example 4225183/A (TPS25947 datasheet SLVSFC9, page 73)', 'VQFN-HR RPW0010A TPS25947')
    for num, sx, sy in (('1', -1, -1), ('4', -1, 1), ('7', 1, 1), ('10', 1, -1)):
        # 0.6 x 0.3 pad at (+-0.9, +-0.7) joined to a 0.25 wide leg reaching the package edge (+-1.2)
        ax, ay = 0.9 * sx, 0.7 * sy
        x_out, x_in, x_leg = 1.2 * sx, 0.6 * sx, 0.85 * sx
        y_in, y_mid, y_edge = 0.55 * sy, 0.85 * sy, 1.2 * sy
        pts = [(x_out, y_in), (x_out, y_mid), (x_leg, y_mid), (x_leg, y_edge), (x_in, y_edge), (x_in, y_in)]
        fp.poly_pad(num, ax, ay, pts, 0.3, 0.3)
    for num, x, y in (('2', -0.9, -0.225), ('3', -0.9, 0.225), ('8', 0.9, 0.225), ('9', 0.9, -0.225)):
        fp.smd(num, x, y, 0.6, 0.25, shape='rect')
    fp.smd('5', -0.25, 0, 0.3, 2.4, shape='rect')
    fp.smd('6', 0.25, 0, 0.3, 2.4, shape='rect')
    ex, ey = box(fp, 2.0, 2.0, 1.2, 1.2)
    fp.circle(-1.45, -0.7, 0.1, 'F.SilkS', 0.12)
    return fp.render(-ey - 0.8, ey + 0.8)


def dda0008():
    """TI DDA (R-PDSO-G8) PowerPAD SO-8, land pattern data 4208951-6/D (TPS2596 datasheet pages 45-46)."""
    fp = FP('TI_DDA0008_HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.4x3.1mm', 'TI DDA PowerPAD SO-8; pads 0.5x2.2 at 1.27 pitch, rows 5.75 apart, exposed pad opening 3.10x2.40 (TI land pattern 4208951-6/D)', 'HSOP-8 DDA PowerPAD TPS25963')
    for i in range(4):
        fp.smd(str(i + 1), -2.875, -1.905 + i * 1.27, 2.2, 0.5)
        fp.smd(str(8 - i), 2.875, -1.905 + i * 1.27, 2.2, 0.5)
    fp.smd('EP', 0, 0, 2.4, 3.1, shape='rect')
    ex, ey = box(fp, 3.9, 4.9, 2.875 + 1.1, 2.45)
    fp.line(-2.06, -2.56, 2.06, -2.56, 'F.SilkS', 0.12); fp.line(-2.06, 2.56, 2.06, 2.56, 'F.SilkS', 0.12)
    fp.circle(-4.25, -1.905, 0.12, 'F.SilkS', 0.12)
    return fp.render(-ey - 0.8, ey + 0.8)


def mc1630():
    """Mini-Circuits MC1630 (YAT-xA+), case style 98-MC rev H 'PCB Land Pattern'."""
    fp = FP('MiniCircuits_MC1630_MCLP-6-1EP_2x2mm_P0.65mm', 'Mini-Circuits case MC1630 suggested land pattern (98-MC Rev H): pads 0.30x0.80, pitch 0.65, rows 2.70 outside, EP 1.25x0.65 (index chamfer omitted); layout PL-586', 'Mini-Circuits MC1630 YAT-10A+')
    for i, x in enumerate((-0.65, 0, 0.65)):
        fp.smd(str(i + 1), x, 0.95, 0.30, 0.80, shape='rect')
        fp.smd(str(6 - i), x, -0.95, 0.30, 0.80, shape='rect')
    fp.smd('EP', 0, 0, 1.25, 0.65, shape='rect')
    ex, ey = box(fp, 2.0, 2.0, 1.0, 1.35)
    fp.circle(-1.25, 1.25, 0.1, 'F.SilkS', 0.12)
    return fp.render(-ey - 0.8, ey + 0.8)


def gu1604():
    """Mini-Circuits GU1604 (TCBT-2R5G+), case style GU Rev W 'PCB Land Pattern'."""
    fp = FP('MiniCircuits_GU1604_3.81x3.81mm', 'Mini-Circuits case GU1604 suggested land pattern (GU1604 Rev W): pads 0.76x1.27, columns 2.54, rows 4.06 outside; keep the area under the base via masked (note 3); layout PL-146', 'Mini-Circuits GU1604 TCBT-2R5G+')
    for num, x, y in (('1', -1.27, -1.395), ('2', 1.27, -1.395), ('3', 1.27, 1.395), ('4', -1.27, 1.395)):
        fp.smd(num, x, y, 0.76, 1.27, shape='rect')
    ex, ey = box(fp, 3.81, 3.81, 1.65, 2.03)
    fp.circle(-2.2, -2.2, 0.12, 'F.SilkS', 0.12)
    return fp.render(-ey - 0.8, ey + 0.8)


def g6k_rf_s():
    """Omron G6K-2F-RF-S, 'Mounting Dimensions (Top View)' in en-g6k_2f_rf.pdf page 4."""
    fp = FP('Relay_DPDT_Omron_G6K-2F-RF-S', 'Omron G6K-2F-RF-S board space-saving RF relay, mounting dimensions (top view) en-g6k_2f_rf.pdf p.4: terminals 0.8x1.8 at 0/3.2/5.4/7.6 mm, rows 7.0 apart; ground pads 1.0x2.1 and 1.8x2.1 at -1.2/1.6/8.8 mm, rows 7.5 apart; all six ground pads are the case ground', 'relay Omron G6K RF')
    cols = (-3.8, -0.6, 1.6, 3.8)
    for i, x in enumerate(cols):
        fp.smd(str(i + 1), x, 3.5, 0.8, 1.8, shape='rect')
        fp.smd(str(8 - i), x, -3.5, 0.8, 1.8, shape='rect')
    for name, y in (('G1', -3.75), ('G2', 3.75)):
        fp.smd(name, -5.0, y, 1.0, 2.1, shape='rect')
        fp.smd(name, -2.2, y, 1.8, 2.1, shape='rect')
        fp.smd(name, 5.0, y, 1.0, 2.1, shape='rect')
    ex, ey = box(fp, 10.3, 6.9, 5.5, 4.8)
    fp.circle(-3.8, 5.1, 0.15, 'F.SilkS', 0.12)
    fp.text('1', -3.8, 6.0, 'F.Fab', 0.6)
    return fp.render(-ey - 0.8, ey + 0.8)


def tl3145():
    """E-Switch TL3145, 'Recommended PCB Layout' (TL3145 datasheet 4.2.2024 page 2)."""
    fp = FP('SW_E-Switch_TL3145_6.45x6.45mm', 'E-Switch TL3145 sealed SMT tact switch, recommended PCB layout: pads 2.0x1.4 at +-2.5/+-2.0 mm; switch pins 1+2 (top) and 3+4 (bottom) are paired, pads named 1 and 2 after the graph switch contacts', 'switch tactile TL3145')
    for x in (-2.5, 2.5):
        fp.smd('1', x, -2.0, 2.0, 1.4, shape='rect')
        fp.smd('2', x, 2.0, 2.0, 1.4, shape='rect')
    ex, ey = box(fp, 6.45, 6.45, 3.5, 2.7)
    fp.circle(0, 0, 1.5, 'F.Fab', 0.1)
    fp.rect(-3.33, -3.33, 3.33, 3.33, 'F.SilkS', 0.12)
    return fp.render(-ey - 0.8, ey + 0.8)


def pec11r_s():
    """Bourns PEC11R-4xxxF-Sxxxx PCB layout (PEC11R datasheet page 2), drawn in EC11E orientation."""
    fp = FP('RotaryEncoder_Bourns_PEC11R-4xxxF-Sxxxx', 'Bourns PEC11R-4xxxF-Sxxxx vertical encoder with switch, PCB layout: A/C/B at 2.5 mm pitch, switch 1/2 at 5.0 mm, 7.5 mm and 7.0 mm from the mounting-slot line; slots 1.8+0.2 x 2.6+0.2, 13.2 mm outside; holes 1.0+0.1', 'encoder Bourns PEC11R', smd=False)
    fp.tht('A', 0, 0, 2.0, 1.1, shape='rect')
    fp.tht('C', 0, 2.5, 2.0, 1.1)
    fp.tht('B', 0, 5.0, 2.0, 1.1)
    fp.tht('S1', 14.5, 0, 2.0, 1.1)
    fp.tht('S2', 14.5, 5.0, 2.0, 1.1)
    for y in (2.5 - 5.7, 2.5 + 5.7):
        fp.tht('MP', 7.5, y, (3.6, 2.6), None, shape='oval', drill_oval=(2.7, 1.9))
    # body 13.4 (along A->switch) x 12.5, centred on the shaft at (7.5, 2.5)
    fp.rect(0.8, 2.5 - 6.25, 14.2, 2.5 + 6.25, 'F.Fab', 0.1)
    fp.rect(-1.25, 2.5 - 7.5, 15.75, 2.5 + 7.5, 'F.CrtYd', 0.05)
    fp.rect(0.69, 2.5 - 6.36, 14.31, 2.5 + 6.36, 'F.SilkS', 0.12)
    fp.circle(7.5, 2.5, 3.0, 'F.Fab', 0.1)
    return fp.render(2.5 - 8.3, 2.5 + 8.3)


def cpt1207():
    """Same Sky CPT-1207-3TH, recommended PCB layout (datasheet 07/22/2025 page 2)."""
    fp = FP('Buzzer_SameSky_CPT-1207-3TH_D12.5mm_P5.0mm', 'Same Sky CPT-1207-3TH piezo, recommended PCB layout (top view): 2 pads D2.5, holes D1.0, 5.0 mm apart; body D12.5. The bottom view of the same drawing also marks D0.8 features 7.5 mm apart: verify the pin pitch on the first received part before PCB release', 'buzzer piezo CPT-1207', smd=False)
    fp.tht('+', 0, 0, 2.5, 1.0, shape='rect')
    fp.tht('-', 0, 5.0, 2.5, 1.0)
    fp.circle(0, 2.5, 6.25, 'F.Fab', 0.1)
    fp.circle(0, 2.5, 6.37, 'F.SilkS', 0.12)
    fp.circle(0, 2.5, 6.5, 'F.CrtYd', 0.05)
    fp.text('+', -1.8, 0, 'F.SilkS', 1.0)
    return fp.render(2.5 - 7.3, 2.5 + 7.3)


CUSTOM_BUILDERS = {
    'TI_RPW0010A_VQFN-HR-10_2x2mm_P0.5mm': rpw0010a,
    'TI_RGW0020A_VQFN-20-1EP_5x5mm_P0.65mm_EP3.15x3.15mm': lambda: qfn(
        'TI_RGW0020A_VQFN-20-1EP_5x5mm_P0.65mm_EP3.15x3.15mm', 'TI RGW0020A VQFN 20 pin 5x5 mm; TI land pattern example 4219039/A: pads 0.75x0.31, rows 4.65 apart, pitch 0.65, thermal pad 3.15 (TPS7A47 datasheet page 30); paste 4x1.37 per TI stencil example',
        5, 0.65, 0.75, 0.31, 2.325, 5.0, 3.15, 'EP', (2, 1.37)),
    'TI_RGV0016A_VQFN-16-1EP_4x4mm_P0.65mm_EP2.16x2.16mm': lambda: qfn(
        'TI_RGV0016A_VQFN-16-1EP_4x4mm_P0.65mm_EP2.16x2.16mm', 'TI RGV0016A VQFN 16 pin 4x4 mm; TI land pattern example 4219037/A: pads 0.75x0.305, rows 3.65 apart, pitch 0.65, thermal pad 2.16 (INA3221 datasheet page 48); paste 4x0.96 per TI stencil example',
        4, 0.65, 0.75, 0.305, 1.825, 4.0, 2.16, 'EP', (2, 0.96)),
    'TI_DDA0008_HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.4x3.1mm': dda0008,
    'MiniCircuits_MC1630_MCLP-6-1EP_2x2mm_P0.65mm': mc1630,
    'MiniCircuits_GU1604_3.81x3.81mm': gu1604,
    'Relay_DPDT_Omron_G6K-2F-RF-S': g6k_rf_s,
    'SW_E-Switch_TL3145_6.45x6.45mm': tl3145,
    'RotaryEncoder_Bourns_PEC11R-4xxxF-Sxxxx': pec11r_s,
    'Buzzer_SameSky_CPT-1207-3TH_D12.5mm_P5.0mm': cpt1207,
}

# name -> (official source 'Lib:Name', pad renames, note)
DERIVED = {
    'D_SMB_KA': ('Diode_SMD:D_SMB', {'1': 'K', '2': 'A'}, 'graph diode pins are named A/K'),
    'LED_D5.0mm_KA': ('LED_THT:LED_D5.0mm', {'1': 'K', '2': 'A'}, 'graph LED pins are named A/K'),
    'SMA_Molex_73251-1153_EdgeMount_Horizontal_CS': ('Connector_Coaxial:SMA_Molex_73251-1153_EdgeMount_Horizontal', {'1': 'CENTER', '2': 'SHIELD'}, 'graph coax ports are named CENTER/SHIELD'),
    'RaspberryPi_Pico_SMD_SWD': ('Module:RaspberryPi_Pico_SMD', {'D1': 'SWCLK', 'D2': 'SWD_GND', 'D3': 'SWDIO'}, 'debug pads named as the graph pins; order SWCLK/GND/SWDIO from Pico-R3-A4-Pinout.pdf'),
    'QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm_EPAD': ('Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm', {'17': 'EPAD'}, 'HMC7992LP3DE exposed pad named EPAD; ADI outline not read (analog.com unreachable 24.10.2026): exposed-pad size must be checked against the HMC7992 package drawing before PCB release'),
}

PROVENANCE = {
    'TI_RPW0010A_VQFN-HR-10_2x2mm_P0.5mm': {'kind': 'custom', 'source': 'https://www.ti.com/lit/ds/symlink/tps25947.pdf', 'drawing': 'RPW0010A land pattern example 4225183/A (page 73)', 'read': '2026-10-24'},
    'TI_RGW0020A_VQFN-20-1EP_5x5mm_P0.65mm_EP3.15x3.15mm': {'kind': 'custom', 'source': 'https://www.ti.com/lit/ds/symlink/tps7a47.pdf', 'drawing': 'RGW0020A 4219039/A (pages 29-31)', 'read': '2026-10-24'},
    'TI_RGV0016A_VQFN-16-1EP_4x4mm_P0.65mm_EP2.16x2.16mm': {'kind': 'custom', 'source': 'https://www.ti.com/lit/ds/symlink/ina3221.pdf', 'drawing': 'RGV0016A 4219037/A (pages 47-49)', 'read': '2026-10-24'},
    'TI_DDA0008_HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.4x3.1mm': {'kind': 'custom', 'source': 'https://www.ti.com/lit/ds/symlink/tps2596.pdf', 'drawing': 'DDA (R-PDSO-G8) 4206322-6/L and 4208951-6/D (pages 45-46)', 'read': '2026-10-24'},
    'MiniCircuits_MC1630_MCLP-6-1EP_2x2mm_P0.65mm': {'kind': 'custom', 'source': 'https://www.minicircuits.com/case_style/MC1630.pdf', 'drawing': 'Case style MC1630 PCB land pattern (98-MC Rev H); layout https://www.minicircuits.com/pcb/98-pl586.pdf', 'read': '2026-10-24'},
    'MiniCircuits_GU1604_3.81x3.81mm': {'kind': 'custom', 'source': 'https://www.minicircuits.com/case_style/GU1604.pdf', 'drawing': 'Case style GU1604 PCB land pattern (Rev W 02 JUL 24); layout https://www.minicircuits.com/pcb/98-pl146.pdf', 'read': '2026-10-24'},
    'Relay_DPDT_Omron_G6K-2F-RF-S': {'kind': 'custom', 'source': 'https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6k_2f_rf.pdf', 'drawing': 'G6K-2F-RF-S Mounting Dimensions (Top View), page 4', 'read': '2026-10-24'},
    'SW_E-Switch_TL3145_6.45x6.45mm': {'kind': 'custom', 'source': 'https://configured-product-images.s3.amazonaws.com/Datasheets/TL3145.pdf', 'drawing': 'Recommended PCB Layout, page 2 (datasheet 4.2.2024)', 'read': '2026-10-24'},
    'RotaryEncoder_Bourns_PEC11R-4xxxF-Sxxxx': {'kind': 'custom', 'source': 'https://www.bourns.com/docs/Product-Datasheets/PEC11R.pdf', 'drawing': 'PEC11R-4xxxF-Sxxxx PCB layout, page 2', 'read': '2026-10-24'},
    'Buzzer_SameSky_CPT-1207-3TH_D12.5mm_P5.0mm': {'kind': 'custom', 'source': 'https://www.sameskydevices.com/product/resource/cpt-1207-3th.pdf', 'drawing': 'Recommended PCB Layout (Top View), page 2 (07/22/2025)', 'read': '2026-10-24'},
}


def official_path(ident):
    lib, name = ident.split(':', 1)
    return LIBDIR / f'{lib}.pretty' / f'{name}.kicad_mod'


def derive(name, source, renames):
    text = official_path(source).read_text(encoding='utf-8')
    src_name = source.split(':', 1)[1]
    if not text.startswith(f'(footprint "{src_name}"'):
        raise SystemExit(f'Unexpected source header: {source}')
    text = text.replace(f'(footprint "{src_name}"', f'(footprint "{name}"', 1)
    text = re.sub(r'\(property "Value" "' + re.escape(src_name) + '"', f'(property "Value" "{name}"', text, count=1)
    digest = hashlib.sha256(official_path(source).read_bytes()).hexdigest()
    note = f'Derived from KiCad {KICAD_TAG} {source} (sha256 {digest[:16]}); only pad numbers renamed: ' + ', '.join(f'{a}->{b}' for a, b in renames.items())
    text = re.sub(r'\(descr "([^"]*)"\)', lambda m: f'(descr "{note}. Original: {m.group(1)}")', text, count=1)
    for old, new in renames.items():
        text, n = re.subn(r'\(pad "' + re.escape(old) + r'" ', f'(pad "{new}" ', text)
        if not n:
            raise SystemExit(f'{name}: source has no pad {old}')
    return text


def outputs():
    files = {}
    for name, build in CUSTOM_BUILDERS.items():
        files[f'{name}.kicad_mod'] = build()
    for name, (source, renames, _note) in DERIVED.items():
        files[f'{name}.kicad_mod'] = derive(name, source, renames)
    prov = {name: dict(PROVENANCE[name]) for name in CUSTOM_BUILDERS}
    for name, (source, renames, note) in DERIVED.items():
        prov[name] = {'kind': 'derived', 'source': f'KiCad {KICAD_TAG} {source}', 'source_sha256': hashlib.sha256(official_path(source).read_bytes()).hexdigest(),
                      'pad_renames': renames, 'note': note}
    files['provenance.json'] = json.dumps(prov, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    return files


def wanted_official():
    db = json.loads((ROOT / 'design/parts/parts.json').read_text(encoding='utf-8'))
    names = {p['footprint'] for p in db['parts'] if p.get('footprint') and not p['footprint'].startswith('SR_RX_Custom:')}
    names |= {src for src, _r, _n in DERIVED.values()}
    return sorted(names)


def fetch():
    for ident in wanted_official():
        dst = official_path(ident)
        if dst.exists():
            continue
        lib, name = ident.split(':', 1)
        url = KICAD_RAW + urllib.parse.quote(f'{lib}.pretty/{name}.kicad_mod')
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'sr-rx-make-footprints'}), timeout=60) as r:
            data = r.read()
        if not data.startswith(f'(footprint "{name}"'.encode()):
            raise SystemExit(f'Not a KiCad footprint: {url}')
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        print('fetched', ident, hashlib.sha256(data).hexdigest())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--fetch', action='store_true', help='network: fetch missing official KiCad footprints first')
    args = ap.parse_args()
    if args.fetch:
        fetch()
    files = outputs()
    if args.check:
        stale = [n for n, t in files.items() if not (CUSTOM / n).is_file() or (CUSTOM / n).read_text(encoding='utf-8') != t]
        extra = sorted(p.name for p in CUSTOM.glob('*') if p.name not in files)
        if stale or extra:
            raise SystemExit('SR_RX_Custom is stale: ' + ', '.join(stale + [f'unexpected {e}' for e in extra]))
        print(f'SR_RX_Custom.pretty: {len(files) - 1} footprints current')
        return
    CUSTOM.mkdir(parents=True, exist_ok=True)
    for n, t in files.items():
        (CUSTOM / n).write_text(t, encoding='utf-8', newline='\n')
    print(f'wrote {len(files) - 1} footprints to {CUSTOM.relative_to(ROOT).as_posix()}')


if __name__ == '__main__':
    sys.exit(main())
