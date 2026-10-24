#!/usr/bin/env python3
"""Build editable, electrically connected KiCad sheets from reviewed design graphs.

The graph records physical contact numbers or explicitly labelled functional module
interfaces. It is the auditable source; generated drawings do not establish a PCB
layout or certify any of the hardware acceptance gates.

Drawing conventions (stack v2 brief, "Conventions: layout"):
* every functional group is one block on one page: its header once, its notes, then
  one or more rows; a group is never split across columns;
* a row runs left to right in signal order: ICs, modules, transistors and in-line
  series parts sit on the signal line; pull-ups and test points stand above it;
  shunt parts (decoupling, dividers, TVS, damping) hang below it with the ground
  symbol at the bottom;
* inside a row every net with two or more contacts is drawn with orthogonal wires
  found by a grid maze router, with junction dots at T joins; a contact that cannot
  be reached within a short detour keeps a label instead (no long wire runs);
* a row with fallback labels or wire crossings is laid out once more with a free grid
  line next to each bus contact between two boxes that face each other; that spread
  variant is kept only if it has fewer fallback labels, or as many and at most half
  the wire crossings (route_group), so a kept spread row can still have crossings;
* every drawn wire tree carries exactly one global label with the canonical net
  name. Local labels would be renamed "/<sheet>/<name>" by KiCad and change the
  exported netlist, so nets that stay inside their group use the small "passive"
  label shape and nets that leave the group the "bidirectional" one. Ground uses
  power symbols;
* a sheet does not end on a nearly empty page if wider notes save that page
  (layout_sheet); the manifest records each page's fill, note wrap cap, the wrap each
  note actually got (no wider than its group's drawing), fallback labels and wire
  crossings, and run_checks.py refuses sparse last pages and fallback labels.
The generator re-derives the connectivity of every page from the emitted geometry
(wire ends, pins, labels, ground symbols) and refuses to write a page whose drawn
connectivity differs from the design graph.
"""
from __future__ import annotations

import argparse
from collections import Counter, OrderedDict, defaultdict
import copy
import hashlib
import heapq
import json
import math
from pathlib import Path
import re
import sys
import textwrap
from uuid import NAMESPACE_URL, uuid5

BASE = Path(__file__).resolve().parents[1]
TYPES = set("input output bidirectional tri_state passive free unspecified power_in power_out open_collector open_emitter no_connect".split())
SIMPLE = {"resistor", "capacitor", "inductor", "fuse", "switch", "diode", "battery", "testpoint", "net_tie"}
WIDTH, HEIGHT = 594.0, 420.0
U = 2.54  # connection grid: every pin, wire and label anchor lies on it
ROOT_UUID = str(uuid5(NAMESPACE_URL, "sr-rx-v2/root/4653188"))
# Title block of every sheet (drawing convention of the project brief).
DESIGN_DATE, REVISION, COMPANY = "2026-10-23", "v2.1", "SR-RX-v2"
TITLE_COMMENTS = ("Теоретичний проєкт — перевірити на стенді", "Джерело: STACK.md v2",
                  "Не є комплектом для виробництва PCB; див. OPEN_ITEMS.md")
# Reference designators stay inside their sheet range. E4 also owns the
# documented 4400-4499 extension for the DC detectors (design/E4-review.md);
# E2 owns 2900-2999 for the E4-06 bias-branch blocking elements (design/E2-review.md).
REF_RANGES = {"E1": ((100, 199),), "E2": ((200, 299), (2900, 2999)), "E3": ((300, 399),),
              "E4": ((400, 499), (4400, 4499)), "E5": ((500, 599),)}
# KiCad's stroke font has no glyph for U+02BC (it renders as a box).
NO_GLYPH = {"ʼ": "MODIFIER LETTER APOSTROPHE (use an ASCII apostrophe)"}
PIN_NUMBER_SIZE = 0.889
PIN_NUMBER_CHAR_W = 0.82  # mm per character of a 0.889 mm pin number, measured on the KiCad 10 SVG export
CHAR_W = 0.92             # stroke-font advance per mm of text height (0.82/0.889 measured; 1.11/1.27 for Cyrillic)
REF_SIZE, VALUE_SIZE, PIN_TEXT, LABEL_SIZE, GROUP_SIZE = 1.27, 1.016, 0.889, 1.016, 1.524
# Visible notes (open items and drawing notes) placed next to the parts they concern.
NOTE_SIZE = 1.27
NOTE_CHARS = 110        # body wrap: up to ~1.11 mm per 1.27 mm character (measured on Cyrillic) -> <= 122 mm < NOTE_W
NOTE_HEAD_CHARS = 100   # the bold header is wider
NOTE_LINE = 2.1         # line pitch of 1.27 mm KiCad stroke text (measured 2.05 mm)
NOTE_PAD = 1.27
NOTE_GAP = 2.54
NOTE_W = 142.24 - 5.08
NOTE_CYR_MM = 1.11      # advance of one 1.27 mm Cyrillic character (measured): sizes the frame of a wider wrap
NOTE_WIDE_CHARS = (130, 150, 180)  # wider body wraps, tried narrowest first, when a sheet ends on a sparse page
SPARSE_LAST_PAGE = 0.20  # a sheet's last page below this share of the drawable area is sparse
NOTE_COLORS = {"open": "170 0 0 1", "option": "150 90 0 1", "note": "0 60 150 1"}
# Drawable area of the A2 sheet: inside the frame, below the page title and legend,
# with the title block corner (bottom right) kept free. The right edge stays one grid
# step inside the 582 mm inner frame line; it bounds the drawn extent of a block,
# which snapping its rows onto the grid can move right by up to one step.
AREA_X0, AREA_X1, AREA_Y0, AREA_Y1 = 12.7, 582.0 - U, 30.48, 403.86
TITLE_BLOCK_X, TITLE_BLOCK_Y = 459.74, 363.22
BLOCK_GAP = 7.62
ROW_MAX_U = 120          # chains share a row up to 305 mm, so that two blocks fit side by side
ROW_HARD_U = 205         # one signal chain is broken over rows only beyond 521 mm
ROW_GAP_U = 3
MARGIN_U = 12            # free grid units around a row for wires and labels
BEND_COST, CROSS_COST = 2, 6
DETOUR = (2.0, 16, 60)   # wire a contact if its path <= 2*Manhattan+16 and <= 60 units; otherwise label it
GROUND = "GND"


def uid(key):
    return str(uuid5(NAMESPACE_URL, "sr-rx-v2/completion/" + str(key)))


def q(s):
    return json.dumps(str(s), ensure_ascii=False)


def f(n):
    return f"{float(n):.4f}".rstrip("0").rstrip(".") or "0"


def fm(n):
    """A coordinate in mm, normalised so that -0 prints as 0."""
    s = f(round(float(n), 4))
    return "0" if s in ("-0", "") else s


def effects(size=1.016, extra=""):
    return f"(effects (font (size {f(size)} {f(size)})) {extra})"


def prop(k, v, x=0, y=0, hidden=False, size=1.016, justify=""):
    extra = ("(hide yes) " if hidden else "") + (f"(justify {justify})" if justify else "")
    return f"(property {q(k)} {q(v)} (at {fm(x)} {fm(y)} 0) {effects(size, extra.strip())})"


def tw(s, size):
    """Width estimate of KiCad stroke text (mm)."""
    return max((len(x) for x in str(s).split("\n")), default=0) * size * CHAR_W


def label_len(name):
    return tw(name, LABEL_SIZE) + 2.6 * LABEL_SIZE


def text(value, x, y, key, size=1.27, extra="(justify left top)"):
    return f"(text {q(value)} (at {fm(x)} {fm(y)} 0) {effects(size, extra)} (uuid {uid(key)}))"


# --------------------------------------------------------------------------------------
# Symbol graphics (library coordinates, y up). Passive and semiconductor bodies follow
# the stock KiCad 10 Device library (R, C, C_Polarized, L, Fuse, Battery, D, D_Zener,
# D_Schottky, LED, Q_NMOS, Q_PMOS); contacts sit on the 2.54 mm grid.

def _pts(pts):
    return " ".join(f"(xy {fm(x)} {fm(y)})" for x, y in pts)


def prim_sexpr(p):
    k = p[0]
    if k == "poly":
        return f"(polyline (pts {_pts(p[1])}) (stroke (width {f(p[2])}) (type default)) (fill (type {p[3]})))"
    if k == "rect":
        return f"(rectangle (start {fm(p[1][0])} {fm(p[1][1])}) (end {fm(p[2][0])} {fm(p[2][1])}) (stroke (width {f(p[3])}) (type default)) (fill (type {p[4]})))"
    if k == "circle":
        return f"(circle (center {fm(p[1][0])} {fm(p[1][1])}) (radius {f(p[2])}) (stroke (width {f(p[3])}) (type default)) (fill (type {p[4]})))"
    return f"(arc (start {fm(p[1][0])} {fm(p[1][1])}) (mid {fm(p[2][0])} {fm(p[2][1])}) (end {fm(p[3][0])} {fm(p[3][1])}) (stroke (width {f(p[4])}) (type default)) (fill (type none)))"


def rot(pt, a):
    x, y = pt
    return {0: (x, y), 90: (-y, x), 180: (-x, -y), 270: (y, -x)}[a % 360]


def transform(prims, a=0, mirror=False):
    def t(p):
        return rot((p[0], -p[1]) if mirror else p, a)
    out = []
    for p in prims:
        if p[0] == "poly":
            out.append(("poly", [t(x) for x in p[1]], p[2], p[3]))
        elif p[0] == "rect":
            out.append(("rect", t(p[1]), t(p[2]), p[3], p[4]))
        elif p[0] == "circle":
            out.append(("circle", t(p[1]), p[2], p[3], p[4]))
        else:
            out.append(("arc", t(p[1]), t(p[2]), t(p[3]), p[4]))
    return out


def L_(*pts, w=0.254, fill="none"):
    return ("poly", list(pts), w, fill)


GFX = {  # vertical, contact 1 on top
    "resistor": [("rect", (-1.016, 2.54), (1.016, -2.54), 0.254, "none")],
    "capacitor": [L_((-2.032, 0.762), (2.032, 0.762), w=0.508), L_((-2.032, -0.762), (2.032, -0.762), w=0.508)],
    "capacitor_pol": [("rect", (-2.286, 0.508), (2.286, 1.016), 0, "none"), L_((-1.778, 2.286), (-0.762, 2.286), w=0),
                      L_((-1.27, 2.794), (-1.27, 1.778), w=0), ("rect", (2.286, -0.508), (-2.286, -1.016), 0, "outline")],
    "inductor": [("arc", (0, 2.54), (0.6323, 1.905), (0, 1.27), 0), ("arc", (0, 1.27), (0.6323, 0.635), (0, 0), 0),
                 ("arc", (0, 0), (0.6323, -0.635), (0, -1.27), 0), ("arc", (0, -1.27), (0.6323, -1.905), (0, -2.54), 0)],
    "fuse": [("rect", (-0.762, -2.54), (0.762, 2.54), 0.254, "none"), L_((0, 2.54), (0, -2.54), w=0)],
    "battery": [("rect", (-2.286, 1.778), (2.286, 1.524), 0, "outline"), ("rect", (-2.286, -1.27), (2.286, -1.524), 0, "outline"),
                ("rect", (-1.524, 1.016), (1.524, 0.508), 0, "outline"), ("rect", (-1.524, -2.032), (1.524, -2.54), 0, "outline"),
                L_((0, 1.778), (0, 2.54), w=0), L_((0, 0), (0, 0.254), w=0), L_((0, -0.508), (0, -0.254), w=0),
                L_((0, -1.016), (0, -0.762), w=0), L_((0.762, 3.048), (1.778, 3.048)), L_((1.27, 3.556), (1.27, 2.54))],
    "switch": [("circle", (0, 2.032), 0.508, 0, "none"), ("circle", (0, -2.032), 0.508, 0, "none"), L_((0.254, -1.524), (1.778, 1.778))],
    "net_tie": [L_((0, 2.54), (0, -2.54), w=0.762)],
    "generic": [("rect", (-1.016, 2.54), (1.016, -2.54), 0.254, "none")],
}
PIN_LEN = {"resistor": 2.54, "capacitor": 4.318, "capacitor_pol": 4.064, "inductor": 2.54, "fuse": 2.54, "battery": 2.54,
           "switch": 2.54, "net_tie": 2.54, "generic": 2.54, "diode": 3.81}
DIODE_BODY = [L_((1.27, 0), (-1.27, 0), w=0), L_((1.27, 1.27), (1.27, -1.27), (-1.27, 0), (1.27, 1.27))]
DIODE_BAR = {  # horizontal, cathode on the left
    "plain": [L_((-1.27, 1.27), (-1.27, -1.27))],
    "zener": [L_((-1.27, -1.27), (-1.27, 1.27), (-0.762, 1.27))],
    "schottky": [L_((-1.905, 0.635), (-1.905, 1.27), (-1.27, 1.27), (-1.27, -1.27), (-0.635, -1.27), (-0.635, -0.635))],
    "led": [L_((-1.27, 1.27), (-1.27, -1.27)), L_((-3.048, -0.762), (-4.572, -2.286), (-3.81, -2.286), (-4.572, -2.286), (-4.572, -1.524), w=0),
            L_((-1.778, -0.762), (-3.302, -2.286), (-2.54, -2.286), (-3.302, -2.286), (-3.302, -1.524), w=0)],
}
Q_NMOS = [L_((0.254, 1.905), (0.254, -1.905)), L_((0.254, 0), (-2.54, 0), w=0), L_((0.762, 2.286), (0.762, 1.27)),
          L_((0.762, 0.508), (0.762, -0.508)), L_((0.762, -1.27), (0.762, -2.286)),
          L_((0.762, -1.778), (3.302, -1.778), (3.302, 1.778), (0.762, 1.778), w=0),
          L_((1.016, 0), (2.032, 0.381), (2.032, -0.381), (1.016, 0), w=0, fill="outline"),
          ("circle", (1.651, 0), 2.794, 0.254, "none"), L_((2.54, 2.54), (2.54, 1.778), w=0),
          ("circle", (2.54, 1.778), 0.254, 0, "outline"), ("circle", (2.54, -1.778), 0.254, 0, "outline"),
          L_((2.54, -2.54), (2.54, 0), (0.762, 0), w=0), L_((2.921, 0.381), (3.683, 0.381), w=0),
          L_((3.302, 0.381), (2.921, -0.254), (3.683, -0.254), (3.302, 0.381), w=0)]
Q_PMOS = [L_((0.254, 1.905), (0.254, -1.905)), L_((0.254, 0), (-2.54, 0), w=0), L_((0.762, 2.286), (0.762, 1.27)),
          L_((0.762, 1.778), (3.302, 1.778), (3.302, -1.778), (0.762, -1.778), w=0), L_((0.762, 0.508), (0.762, -0.508)),
          L_((0.762, -1.27), (0.762, -2.286)), ("circle", (1.651, 0), 2.794, 0.254, "none"),
          L_((2.286, 0), (1.27, 0.381), (1.27, -0.381), (2.286, 0), w=0, fill="outline"), L_((2.54, 2.54), (2.54, 1.778), w=0),
          ("circle", (2.54, 1.778), 0.254, 0, "outline"), ("circle", (2.54, -1.778), 0.254, 0, "outline"),
          L_((2.54, -2.54), (2.54, 0), (0.762, 0), w=0), L_((2.921, -0.381), (3.683, -0.381), w=0),
          L_((3.302, -0.381), (2.921, 0.254), (3.683, 0.254), (3.302, -0.381), w=0)]
GND_GFX = [L_((0, 0), (0, -1.27), (1.27, -1.27), (0, -2.54), (-1.27, -1.27), (0, -1.27), w=0)]
GND_VARIANTS = {(0, 1): ("PWR_GND", 0), (0, -1): ("PWR_GND_UP", 180), (-1, 0): ("PWR_GND_LEFT", 270), (1, 0): ("PWR_GND_RIGHT", 90)}
ANGLE = {(-1, 0): 0, (1, 0): 180, (0, -1): 270, (0, 1): 90}


class Sym:
    """One symbol in schematic-relative coordinates (mm and grid units, y down)."""

    def __init__(self, comp, name):
        self.comp, self.name = comp, name
        self.prims, self.pins, self.boxes, self.texts = [], [], [], []
        self.ref = self.val = None          # (dx, dy, justify) in mm
        self.show_names = self.show_numbers = False
        self.name_offset = 0.508
        self.power = self.flag = False

    def add_pin(self, p, x, y, out, length):
        self.pins.append({"p": p, "x": x, "y": y, "out": out, "len": length})


def sym_name(c):
    return "C_" + re.sub(r"[^A-Za-z0-9_]", "_", c["ref"])


def is_nc(p):
    return bool(p.get("nc")) or p.get("type") == "no_connect"


def two_terminals(c):
    pins = c["pins"]
    if len(pins) == 2:
        return pins[0], pins[1], []
    main = [p for p in pins if p.get("net") or not (is_nc(p) or str(p.get("name", "")).upper() == "NC")]
    extra = [p for p in pins if p not in main]
    return main[0], main[1], extra


def cathode(p):
    return str(p.get("name", p["number"])).strip().upper().startswith("K")


def plus(p):
    return str(p.get("name", "")).strip() == "+" or str(p["number"]) == "+"


def diode_style(c):
    s = (c.get("value", "") + " " + c.get("description", "")).upper()
    if "LED" in s or "WP7113" in s:
        return "led"
    if any(k in s for k in ("SMBJ", "TVS", "ESD", "ZENER")):
        return "zener"
    if any(k in s for k in ("SS14", "BAT54", "PMEG", "SCHOTTKY")):
        return "schottky"
    return "plain"


def gfx_key(c, a, b):
    kind = c.get("kind")
    if kind == "capacitor":
        return "capacitor_pol" if plus(a) or plus(b) else "capacitor"
    return kind if kind in GFX else "generic"


def text_box(dx, dy, s, size, justify):
    w, h = tw(s, size), size * 1.3
    x0 = dx if "left" in justify else dx - w if "right" in justify else dx - w / 2
    return (x0, dy - h / 2, x0 + w, dy + h / 2)


def fields(sym, ref_at, val_at):
    """Visible reference/value: (dx, dy, justify) in mm; records their clearance boxes."""
    c = sym.comp
    sym.ref, sym.val = ref_at, val_at
    if ref_at:
        sym.texts.append(text_box(ref_at[0], ref_at[1], c["ref"], REF_SIZE, ref_at[2]))
    if val_at:
        sym.texts.append(text_box(val_at[0], val_at[1], c["value"], VALUE_SIZE, val_at[2]))


def build_two(c, first, second, extra, vertical):
    """Two-terminal part (R, C, L, fuse, diode, battery, switch, net tie): `first` on top/left."""
    sym = Sym(c, sym_name(c))
    if c.get("kind") == "diode":
        k_first = cathode(first)
        sym.prims = transform(DIODE_BODY + DIODE_BAR[diode_style(c)], (270 if k_first else 90) if vertical else (0 if k_first else 180))
        length = PIN_LEN["diode"]
    else:
        key = gfx_key(c, first, second)
        polar = key in ("capacitor_pol", "battery")
        pf = plus(first) if polar else True
        sym.prims = transform(GFX[key], (0 if pf else 180) if vertical else (90 if pf else 270))
        length = PIN_LEN[key]
    if vertical:
        sym.add_pin(first, 0, -2, (0, -1), length)
        sym.add_pin(second, 0, 2, (0, 1), length)
        for p in extra:
            sym.add_pin(p, -2, 0, (-1, 0), 3.81)
        sym.boxes.append((-2.4, -4.4, 2.4, 4.4))
        fields(sym, (2.286, -0.762, "left"), (2.286, 1.016, "left"))
    else:
        sym.add_pin(first, -2, 0, (-1, 0), length)
        sym.add_pin(second, 2, 0, (1, 0), length)
        for p in extra:
            sym.add_pin(p, 0, 2, (0, 1), 3.81)
        sym.boxes.append((-4.4, -2.4, 4.4, 2.4))
        if extra:
            fields(sym, (0, -4.826, ""), (0, -3.302, ""))
        else:
            fields(sym, (0, -3.302, ""), (0, 3.302, ""))
    return sym


def build_tp(c):
    sym = Sym(c, sym_name(c))
    sym.prims = [("circle", (0, 0), 0.762, 0.254, "none")]
    sym.add_pin(c["pins"][0], 0, 1, (0, 1), 1.778)
    sym.boxes.append((-1.3, -1.3, 1.3, 1.9))
    fields(sym, (1.778, -0.762, "left"), (1.778, 0.889, "left"))
    return sym


def build_flag(c):
    sym = Sym(c, sym_name(c))
    sym.flag = True
    sym.prims = [L_((0, 0), (0, 2.54)), L_((0, 2.54), (-1.27, 1.27)), L_((0, 2.54), (1.27, 1.27))]
    sym.add_pin(c["pins"][0], 0, 0, (0, 1), 0)
    sym.boxes.append((-1.6, -3.0, 1.6, -0.3))
    fields(sym, None, (1.778, -1.778, "left"))
    return sym


def build_fet(c, pmos):
    sym = Sym(c, sym_name(c))
    by = {str(p.get("name", "")).upper(): p for p in c["pins"]}
    top, bottom = (by["S"], by["D"]) if pmos else (by["D"], by["S"])
    sym.prims = transform(Q_PMOS, 0, mirror=True) if pmos else list(Q_NMOS)
    sym.add_pin(by["G"], -2, 0, (-1, 0), 2.54)
    sym.add_pin(top, 1, -2, (0, -1), 2.54)
    sym.add_pin(bottom, 1, 2, (0, 1), 2.54)
    sym.show_numbers = True
    sym.boxes.append((-4.4, -4.4, 4.7, 4.4))
    fields(sym, (5.334, -1.016, "left"), (5.334, 1.016, "left"))
    return sym


def build_dcc(c):
    """Common-cathode diode pair (BAT54C): anodes left/right, cathode up."""
    sym = Sym(c, sym_name(c))
    by = {str(p.get("name", "")).upper(): p for p in c["pins"]}
    k = next(p for n, p in by.items() if n.startswith("K"))
    sym.prims = [L_((-5.08, 0), (-3.81, 0), w=0), L_((-3.81, 1.27), (-3.81, -1.27), (-1.27, 0), (-3.81, 1.27)), L_((-1.27, 1.27), (-1.27, -1.27)),
                 L_((-1.27, 0), (1.27, 0), w=0), L_((1.27, 1.27), (1.27, -1.27)), L_((3.81, 1.27), (3.81, -1.27), (1.27, 0), (3.81, 1.27)),
                 L_((3.81, 0), (5.08, 0), w=0), ("circle", (0, 0), 0.254, 0, "outline")]
    sym.add_pin(by["A1"], -3, 0, (-1, 0), 2.54)
    sym.add_pin(by["A2"], 3, 0, (1, 0), 2.54)
    sym.add_pin(k, 0, -2, (0, -1), 5.08)
    sym.show_numbers = True
    sym.boxes.append((-6.9, -4.4, 6.9, 2.0))
    fields(sym, (0, 3.302, ""), (0, 4.826, ""))
    return sym


def build_dser(c):
    """Series diode pair (BAV199): K2 on top, the common node to the left, A1 at the bottom."""
    sym = Sym(c, sym_name(c))
    by = {str(p.get("name", "")).upper(): p for p in c["pins"]}
    sym.prims = [L_((-1.27, 3.81), (1.27, 3.81)), L_((-1.27, 1.27), (1.27, 1.27), (0, 3.81), (-1.27, 1.27)), L_((0, 1.27), (0, -1.27), w=0),
                 L_((-1.27, -1.27), (1.27, -1.27)), L_((-1.27, -3.81), (1.27, -3.81), (0, -1.27), (-1.27, -3.81)),
                 ("circle", (0, 0), 0.254, 0, "outline")]
    sym.add_pin(by["K2"], 0, -3, (0, -1), 3.81)
    sym.add_pin(by["K1_A2"], -2, 0, (-1, 0), 5.08)
    sym.add_pin(by["A1"], 0, 3, (0, 1), 3.81)
    sym.show_numbers = True
    sym.boxes.append((-4.4, -6.9, 2.0, 6.9))
    fields(sym, (2.54, -1.016, "left"), (2.54, 1.016, "left"))
    return sym


def pin_display(c):
    """Which pin texts a module/IC box shows, chosen so that no text overprints another:
    functional module ports whose number repeats the name show the name only."""
    pins = c["pins"]
    same = all(str(p["number"]) == str(p.get("name", p["number"])) for p in pins)
    return {"names": True, "numbers": not same}


def pin_length_u(c):
    """Long functional pin numbers (e.g. P1.7, HDMI_1) get a pin long enough to carry them."""
    if not pin_display(c)["numbers"]:
        return 1
    longest = max(len(str(p["number"])) for p in c["pins"])
    if longest <= 3:
        return 1
    return math.ceil((longest * PIN_NUMBER_CHAR_W + 1.27) / U)


def build_hub(c, left, right, bottom):
    """IC/module/connector box. `left`/`right` are per-row pin lists (None = empty row)."""
    sym = Sym(c, sym_name(c))
    show = pin_display(c)
    sym.show_names, sym.show_numbers = show["names"], show["numbers"]
    L = pin_length_u(c)
    rows = max(len(left), len(right), 1)

    def names(ps):
        return max((tw(p.get("name", p["number"]), PIN_TEXT) for p in ps if p), default=0)
    wl, wr, wb = names(left), names(right), names(bottom)
    W = max(4, math.ceil((wl + wr + 2 * 0.508 + 2.54) / U), len(bottom) + 1)
    H = max(rows + 1, math.ceil(((rows + 0.5) * U + wb + 1.3) / U)) if bottom else rows + 1
    sym.prims = [("rect", (0, 0), (W * U, -H * U), 0.254, "background")]
    for r, p in enumerate(left):
        if p:
            sym.add_pin(p, -L, r + 1, (-1, 0), L * U)
    for r, p in enumerate(right):
        if p:
            sym.add_pin(p, W + L, r + 1, (1, 0), L * U)
    start = max(1, (W - len(bottom) + 1) // 2)
    for k, p in enumerate(bottom):
        sym.add_pin(p, start + k, H + L, (0, 1), L * U)
    sym.W, sym.H, sym.L = W, H, L
    sym.boxes.append((-L * U + 0.6, -0.6, (W + L) * U - 0.6, (H + L) * U - 0.6))
    fields(sym, (0, -3.556, "left"), (0, -1.778, "left"))
    return sym


def ground_symbol(variant):
    name, a = variant
    sym = Sym({"ref": "#PWR", "value": GROUND, "description": "Ground power symbol", "status": "annotation", "notes": []}, name)
    sym.power = True
    sym.prims = transform(GND_GFX, a)
    return sym


def lib_symbol(sym, embedded=True):
    c = sym.comp
    full = ("sr_rx_v2_completed:" if embedded else "") + sym.name
    numbers = "" if sym.show_numbers else "(pin_numbers (hide yes)) "
    names = f"(pin_names (offset {f(sym.name_offset)}){'' if sym.show_names else ' (hide yes)'})"
    special = sym.flag or sym.power
    body = [f"(symbol {q(full)} {'(power) ' if special else ''}{numbers}{names} (exclude_from_sim no) (in_bom {'no' if special else 'yes'}) (on_board {'no' if special else 'yes'})"]
    if sym.power:
        body += [prop("Reference", "#PWR", 0, -6.35, True, 1.27), prop("Value", GROUND, 0, -3.81, True, 1.27),
                 prop("Footprint", "", hidden=True), prop("Datasheet", "", hidden=True), prop("Description", "Ground (GND) power symbol", hidden=True)]
        pins = [f"(pin power_in line (at 0 0 {ANGLE[{'PWR_GND': (0, 1), 'PWR_GND_UP': (0, -1), 'PWR_GND_LEFT': (-1, 0), 'PWR_GND_RIGHT': (1, 0)}[sym.name]]}) (length 0) (name \"\" {effects(1.27)}) (number \"1\" {effects(1.27)}))"]
    else:
        body += [prop("Reference", c["ref"], 0, 0), prop("Value", c["value"], 0, -2.54), prop("Footprint", c.get("footprint", ""), hidden=True),
                 prop("Datasheet", c.get("source", ""), hidden=True),
                 prop("Description", c.get("description", "") + " | " + c.get("status", "") + " | " + "; ".join(c.get("notes", [])), hidden=True)]
        pins = []
        for pin in sym.pins:
            p = pin["p"]
            lx, ly = pin["x"] * U, -pin["y"] * U
            pins.append(f"(pin {p.get('type', 'passive')} line (at {fm(lx)} {fm(ly)} {ANGLE[pin['out']]}) (length {f(pin['len'])}) "
                        f"(name {q(p.get('name', p['number']))} {effects(PIN_TEXT)}) (number {q(p['number'])} {effects(PIN_NUMBER_SIZE)}))")
    body += [f"(symbol {q(sym.name + '_0_1')} {' '.join(prim_sexpr(p) for p in sym.prims)})", f"(symbol {q(sym.name + '_1_1')} {' '.join(pins)}))"]
    return "\n".join(body)


# --------------------------------------------------------------------------------------
# Net context

class Context:
    def __init__(self, graphs):
        self.groups_of = defaultdict(set)
        self.types = defaultdict(set)
        flagged = set()
        for g in graphs:
            flagged |= {e["net"] for e in g.get("power_flags", [])}
            for c in g["components"]:
                if c.get("kind") == "power_flag":
                    continue  # ERC annotations do not change where a net is drawn
                for p in c["pins"]:
                    if p.get("net"):
                        self.groups_of[p["net"]].add((g["sheet"], c.get("group", "Інше")))
                        self.types[p["net"]].add(p.get("type", "passive"))
        self.rails = {n for n, t in self.types.items() if n != GROUND and (t & {"power_in", "power_out"} or n in flagged)}

    def global_rail(self, n):
        """A supply rail that leaves its group: drawn with labels, never used to order parts."""
        return n in self.rails and len(self.groups_of[n]) > 1

    def leaves_group(self, n, key):
        return self.groups_of[n] != {key}


# --------------------------------------------------------------------------------------
# Row placement

class Part:
    """A placed symbol: anchor (grid units, row coordinates)."""

    def __init__(self, sym, x, y, cluster=-1):
        self.sym, self.x, self.y, self.cluster = sym, x, y, cluster

    def pin_points(self):
        for pin in self.sym.pins:
            yield pin, (self.x + pin["x"], self.y + pin["y"])


class Item:
    """A part on the signal line: hub (IC/module/connector/relay), transistor, diode pair or series part."""

    def __init__(self, comp, style, index, ctx):
        self.comp, self.style, self.index = comp, style, index
        self.side = {}
        self.order = {}
        self.first = None
        if style == "two":
            a, b, extra = two_terminals(comp)
            self.ends, self.extra = [a, b], extra
        elif style == "fet":
            by = {str(p.get("name", "")).upper(): p for p in comp["pins"]}
            self.side = {by["G"]["number"]: "L", by["D"]["number"]: "R", by["S"]["number"]: "R"}
        elif style == "dcc":
            for p in comp["pins"]:
                n = str(p.get("name", "")).upper()
                self.side[p["number"]] = "L" if n == "A1" else "R" if n == "A2" else "T"
        elif style == "dser":
            for p in comp["pins"]:
                n = str(p.get("name", "")).upper()
                self.side[p["number"]] = "L" if n == "K1_A2" else "R"
        else:
            self.side = hub_sides(comp)

    def nets(self, side, ctx):
        """Nets on one side that order the signal line (no ground, no shared supply rails)."""
        if self.style == "two":
            ps = self.ends if self.first is None else [self.ends[0]] if side == "L" else [self.ends[1]]
        else:
            ps = [p for p in self.comp["pins"] if self.side.get(p["number"]) == side]
        return [p["net"] for p in ps if p.get("net") and p["net"] != GROUND and not ctx.global_rail(p["net"])]

    def orient_two(self, left_net):
        a, b = self.ends
        if left_net is not None and b.get("net") == left_net and a.get("net") != left_net:
            self.ends = [b, a]
        self.first = self.ends[0]

    def mirror(self):
        self.side = {k: {"L": "R", "R": "L"}.get(v, v) for k, v in self.side.items()}


def hub_sides(c):
    sides, signal = {}, []
    for p in c["pins"]:
        if p.get("net") == GROUND:
            sides[p["number"]] = "B"
        else:
            signal.append(p)
    half = len(signal) / 2
    connector = c.get("kind") == "connector" and len(signal) > 2
    for i, p in enumerate(signal):
        name = str(p.get("name", p["number"])).upper()
        t = p.get("type", "passive")
        if connector:
            s = "L" if i < half else "R"
        elif len(signal) == 1:
            s = "R"
        elif name.startswith(("OUT", "VOUT")):  # incl. OUTS, the output-sense input of LDOs
            s = "R"
        elif t in ("output", "open_collector", "open_emitter", "tri_state", "power_out"):
            s = "R"
        elif t in ("input", "power_in") and not name.startswith("USB"):
            s = "L"
        elif re.search(r"(^|[^A-Z])(OUT|VOUT)([^A-Z]|$)", name) or name.startswith("USB") or name in ("END_B", "RF", "K2", "PANEL", "BLOCK", "POD_5V", "SMA_OUT", "SMA_F_B", "SMA_B"):
            s = "R"
        elif re.search(r"(^|[^A-Z])(IN|VIN|ANT)([^A-Z]|$)", name) or name in ("END_A", "SMA_A", "SMA_F_A"):
            s = "L"
        else:
            s = "L" if i < half else "R"
        sides[p["number"]] = s
    return sides


class Col:
    """A vertical stack hanging below the signal line ('low') or standing above it ('up')."""

    def __init__(self, kind, parts, index):
        self.kind, self.parts, self.index = kind, parts, index  # parts: [(comp, first, second, extra)]

    @property
    def attach(self):
        if self.kind == "low":
            return self.parts[0][1].get("net")
        return self.parts[-1][2].get("net") if self.parts[-1][2] is not None else self.parts[-1][1].get("net")

    @property
    def taps(self):
        return [p[2].get("net") for p in self.parts[:-1]] if self.kind == "low" else []


def classify(c):
    kind, pins = c.get("kind"), c["pins"]
    if kind == "power_flag":
        return "flag"
    if kind == "testpoint" and len(pins) == 1:
        return "tp"
    names = {str(p.get("name", "")).upper() for p in pins}
    if kind in ("nfet", "pfet") and names == {"G", "S", "D"}:
        return "fet"
    if kind == "diode" and len(pins) == 3:
        if names == {"A1", "A2"} | {n for n in names if n.startswith("K")} and any(n.startswith("K") for n in names):
            return "dcc"
        if names == {"A1", "K1_A2", "K2"}:
            return "dser"
    if kind in SIMPLE and (len(pins) == 2 or (kind == "diode" and len(pins) == 3 and sum(1 for p in pins if p.get("net")) <= 2
                                             and any(is_nc(p) or str(p.get("name", "")).upper() == "NC" for p in pins))):
        return "two"
    return "hub"


def group_plan(comps, ctx, key):
    """Split a group into signal-line items, lower columns and upper items."""
    styles = {c["ref"]: classify(c) for c in comps}
    index = {c["ref"]: i for i, c in enumerate(comps)}
    twos = {c["ref"]: two_terminals(c) for c in comps if styles[c["ref"]] == "two"}
    role = {}
    for ref, (a, b, _) in twos.items():
        na, nb = a.get("net"), b.get("net")
        if GROUND in (na, nb):
            role[ref] = "shunt"
        elif (ctx.global_rail(na) and nb and not ctx.global_rail(nb) or ctx.global_rail(nb) and na and not ctx.global_rail(na)) \
                and next(c for c in comps if c["ref"] == ref).get("kind") == "resistor":
            role[ref] = "pull"
        else:
            role[ref] = "series"
    by_net = defaultdict(list)
    for ref, (a, b, _) in twos.items():
        for p in (a, b):
            if p.get("net"):
                by_net[p["net"]].append(ref)
    comp = {c["ref"]: c for c in comps}
    used, cols, upper = set(), [], []
    for c in comps:
        ref = c["ref"]
        if ref in used or role.get(ref) != "shunt":
            continue
        a, b, extra = twos[ref]
        top, bot = (b, a) if a.get("net") == GROUND else (a, b)
        stack = [(c, top, bot, extra)]
        used.add(ref)
        n = top.get("net")
        while n and n != GROUND:
            others = [r for r in by_net[n] if r != stack[0][0]["ref"]]
            # only R/C networks (dividers, snubbers, RC filters) stack into a column; inductors,
            # fuses, diodes and switches stay in-line on the signal line
            if len(others) != 1 or others[0] in used or role.get(others[0]) not in ("series", "pull") or comp[others[0]].get("kind") not in ("resistor", "capacitor"):
                break
            o = others[0]
            oa, ob, oextra = twos[o]
            otop, obot = (ob, oa) if oa.get("net") == n else (oa, ob)
            if otop.get("net") in (None, GROUND) or ctx.global_rail(n):
                break
            stack.insert(0, (comp[o], otop, obot, oextra))
            used.add(o)
            n = otop.get("net")
        cols.append(Col("low", stack, index[stack[0][0]["ref"]]))
    for c in comps:
        ref = c["ref"]
        if ref in used:
            continue
        if role.get(ref) == "pull":
            a, b, extra = twos[ref]
            top, bot = (a, b) if ctx.global_rail(a.get("net")) else (b, a)
            upper.append(Col("up", [(c, top, bot, extra)], index[ref]))
            used.add(ref)
        elif styles[ref] in ("tp", "flag"):
            upper.append(Col("up", [(c, c["pins"][0], None, [])], index[ref]))
            used.add(ref)
    items = [Item(c, styles[c["ref"]], index[c["ref"]], ctx) for c in comps if c["ref"] not in used]
    return items, cols, upper


def chain_order(items, ctx):
    """Order the signal-line items left to right by following nets from outputs to inputs."""
    # A part with one signal contact (a port connector, a load) that feeds another part's
    # output is a sink: its contact goes on the left so the chain reads source -> sink.
    for it in items:
        if it.style != "hub":
            continue
        sig = [p for p in it.comp["pins"] if it.side.get(p["number"]) in ("L", "R") and p.get("net")]
        if len(sig) != 1:
            continue
        n = sig[0]["net"]
        outs = sum(1 for o in items if o is not it and o.style == "hub" and n in o.nets("R", ctx))
        ins = sum(1 for o in items if o is not it and (n in o.nets("L", ctx) if o.style != "two" else False))
        if outs and not ins:
            it.side[sig[0]["number"]] = "L"
    users = defaultdict(list)
    for it in items:
        for n in sorted(set(it.nets("L", ctx) + it.nets("R", ctx)), key=str):
            users[n].append(it)
    used, chains = set(), []

    def can_enter(it, n):
        if it.style == "two":
            return n in [p.get("net") for p in it.ends]
        return n in it.nets("L", ctx) or (it.style == "hub" and n in it.nets("R", ctx))

    def walk(it, via, chain):
        used.add(id(it))
        if it.style == "two":
            it.orient_two(via if via is not None else start_net(it))
        elif via is not None and it.style == "hub" and via not in it.nets("L", ctx) and via in it.nets("R", ctx):
            it.mirror()
        chain.append(it)
        for n in it.nets("R", ctx):
            for nxt in users[n]:
                if id(nxt) not in used and can_enter(nxt, n):
                    walk(nxt, n, chain)

    def start_net(it):
        a, b = it.ends
        for p in (a, b):
            n = p.get("net")
            if n is None or ctx.global_rail(n) or not [o for o in users[n] if o is not it and id(o) not in used]:
                return n
        return a.get("net")

    def is_source(it):
        if it.style == "two":
            return any(p.get("net") is None or ctx.global_rail(p["net"]) or not [o for o in users[p["net"]] if o is not it and id(o) not in used]
                       for p in it.ends)
        for n in it.nets("L", ctx):
            if any(o is not it and id(o) not in used and (n in o.nets("R", ctx) or o.style == "two") for o in users[n]):
                return False
        return True

    while len(used) < len(items):
        rest = [it for it in items if id(it) not in used]
        start = next((it for it in rest if is_source(it)), rest[0])
        chain = []
        walk(start, None, chain)
        chains.append(chain)
    return chains


class Row:
    def __init__(self):
        self.parts, self.cols_low, self.cols_up = [], [], []
        self.links = []        # pre-wired column links (net, a, b)
        self.width = 0
        self.gap_nets = []     # nets of the signal line, routed first
        self.n_items = 0       # the first n_items parts sit on the signal line
        self.spread = 0        # hub sides laid out with a free grid line between contacts


def item_width(it, sym):
    if it.style == "hub":
        text = max(tw(it.comp["ref"], REF_SIZE), tw(it.comp["value"], VALUE_SIZE)) + 0.6
        return max(sym.W + 2 * sym.L, sym.L + math.ceil(text / U))
    if it.style == "two":
        need = max(tw(it.comp["ref"], REF_SIZE), tw(it.comp["value"], VALUE_SIZE)) + 1.0
        return max(4, 2 * math.ceil(need / U / 2))
    if it.style == "fet":
        return 2 + math.ceil((5.334 + max(tw(it.comp["ref"], REF_SIZE), tw(it.comp["value"], VALUE_SIZE)) + 0.6) / U)
    if it.style == "dcc":
        return max(6, math.ceil(tw(it.comp["value"], VALUE_SIZE) / U))
    return 2 + math.ceil((2.54 + max(tw(it.comp["ref"], REF_SIZE), tw(it.comp["value"], VALUE_SIZE))) / U)


def col_width(col):
    w = 0
    for comp, *_ in col.parts:
        w = max(w, 2.4 + max(tw(comp["ref"], REF_SIZE), tw(comp["value"], VALUE_SIZE)))
    return 1 + math.ceil(w / U) + 1


def item_pins(it):
    if it.style == "two":
        return [(p, "L" if i == 0 else "R") for i, p in enumerate(it.ends)]
    return [(p, it.side.get(p["number"], "L")) for p in it.comp["pins"]]


def attach_cols(seq, cols, ctx):
    """Assign every column to a zone of the row `seq`: returns {id(col): (zone, category, row_key)}."""
    gap = {}
    for k in range(len(seq) - 1):
        a, b = seq[k], seq[k + 1]
        right = a.nets("R", ctx)
        left = b.nets("L", ctx) if b.style != "two" else [p.get("net") for p in b.ends[:1]]
        common = [n for n in right if n in left]
        gap[k + 1] = common[0] if common else None
    gap_zone = {n: z for z, n in gap.items() if n}
    pinpos = defaultdict(list)
    for k, it in enumerate(seq):
        for p, s in item_pins(it):
            if p.get("net") and p["net"] != GROUND:
                pinpos[p["net"]].append((k, s, p))
    where = {}
    for col in cols:
        n = col.attach
        tapped = any(s in ("L", "R") for t in col.taps for k, s, p in pinpos.get(t, []))
        if n in gap_zone and not ctx.global_rail(n) and not tapped:
            where[id(col)] = (gap_zone[n], "gap", None)
            continue
        hit = None
        for t in col.taps:
            for k, s, p in pinpos.get(t, []):
                if s in ("L", "R"):
                    hit = (k, s, p)
                    break
            if hit:
                break
        if not hit:
            for k, s, p in pinpos.get(n, []):
                if s in ("L", "R"):
                    hit = (k, s, p)
                    break
        if hit:
            k, s, p = hit
            where[id(col)] = (k if s == "L" else k + 1, "B" if s == "L" else "A", (k, p["number"]))
        else:
            where[id(col)] = (None, "free", None)
    return where, gap


def face_neighbours(seq, ctx):
    """Contacts that connect two neighbouring boxes move to the sides that face each
    other (unless the same net also reaches the box on the far side)."""
    def nets(it):
        return {p.get("net") for p in it.comp["pins"] if p.get("net") and p["net"] != GROUND and not ctx.global_rail(p["net"])}
    for k in range(1, len(seq)):
        a, b = seq[k - 1], seq[k]
        if a.style != "hub" or b.style != "hub":
            continue
        shared = nets(a) & nets(b)
        before = nets(seq[k - 2]) if k >= 2 else set()
        after = nets(seq[k + 1]) if k + 1 < len(seq) else set()
        facing_a = {p.get("net") for p in a.comp["pins"] if a.side.get(p["number"]) == "R"}
        facing_b = {p.get("net") for p in b.comp["pins"] if b.side.get(p["number"]) == "L"}
        for p in a.comp["pins"]:
            n = p.get("net")
            if n in shared and a.side.get(p["number"]) == "L" and n not in before and n not in facing_a:
                a.side[p["number"]] = "R"
        for p in b.comp["pins"]:
            n = p.get("net")
            if n in shared and b.side.get(p["number"]) == "R" and n not in after and n not in facing_b:
                b.side[p["number"]] = "L"


def plan_row(seq, lows, ups, ctx, key, spread=False):
    """Pin order, symbols and zone widths of one row (nothing placed yet).

    With `spread`, a hub side that faces a neighbouring hub over two or more nets (a
    bus) gets one free grid line between its contacts, so that every bus wire can take
    its label right above it instead of across the other wires."""
    face_neighbours(seq, ctx)
    where, gap = attach_cols(seq, lows + ups, ctx)
    up_pins, down_pins = defaultdict(set), defaultdict(set)
    for col in lows + ups:
        z, cat, rk = where[id(col)]
        if rk:
            (up_pins if col.kind == "up" else down_pins)[rk[0]].add(rk[1])
    row_nets = Counter()
    for it in seq:
        for p, s in item_pins(it):
            if p.get("net"):
                row_nets[p["net"]] += 1
    for col in lows + ups:
        if where[id(col)][0] is not None:
            for comp, a, b, extra in col.parts:
                for p in (a, b):
                    if p is not None and p.get("net"):
                        row_nets[p["net"]] += 1
    syms, chainrow, right_rows = [], [], []

    def side_nets(it, side):
        return {p.get("net") for p, s in item_pins(it) if s == side and p.get("net") and p["net"] != GROUND}

    def bus(k, side):
        """Nets that one side of hub k shares with the facing hub, if they form a bus."""
        j = k - 1 if side == "L" else k + 1
        if not spread or not 0 <= j < len(seq) or seq[j].style != "hub":
            return set()
        shared = side_nets(seq[k], side) & side_nets(seq[j], "R" if side == "L" else "L")
        return shared if len(shared) > 1 else set()

    def spaced(pins, shared):
        """A free grid line on either side of every bus contact; other contacts stay packed."""
        out = []
        for p in pins:
            if out and (out[-1].get("net") in shared or p.get("net") in shared):
                out.append(None)
            out.append(p)
        return out
    spread_sides = 0
    for k, it in enumerate(seq):
        left_chain = gap.get(k)
        right_chain = gap.get(k + 1)
        prev_rows = right_rows[k - 1] if k else {}
        next_nets = side_nets(seq[k + 1], "L") if k + 1 < len(seq) and seq[k + 1].style != "two" else \
            ({p.get("net") for p in seq[k + 1].ends} if k + 1 < len(seq) else set())
        if it.style == "hub":
            per = {"L": [], "R": []}
            bottom = []
            for i, p in enumerate(it.comp["pins"]):
                s = it.side[p["number"]]
                if s == "B":
                    bottom.append(p)
                    continue
                n = p.get("net")
                chain = n is not None and n == (left_chain if s == "L" else right_chain)
                # signal-line neighbours first, in the neighbour's order, so that buses run straight
                adjacent = n in prev_rows if s == "L" else n in next_nets
                if p["number"] in up_pins[k]:
                    rank = (0, 0)
                elif chain:
                    rank = (1, 0)
                elif is_nc(p) or not n:
                    rank = (4, i)
                elif p["number"] in down_pins[k]:
                    rank = (3, i)
                elif adjacent:
                    rank = (2, prev_rows[n] if s == "L" else i)
                else:
                    rank = (2.5, i)
                per[s].append((rank, p, chain))
            for s in per:
                per[s].sort(key=lambda t: t[0])
            cl = next((i for i, t in enumerate(per["L"]) if t[2]), None)
            cr = next((i for i, t in enumerate(per["R"]) if t[2]), None)
            left, right = [t[1] for t in per["L"]], [t[1] for t in per["R"]]
            for s, shared in (("L", bus(k, "L")), ("R", bus(k, "R"))):
                if shared:
                    spread_sides += 1
                    if s == "L":
                        left = spaced(left, shared)
                        cl = None if cl is None else left.index(per["L"][cl][1])
                    else:
                        right = spaced(right, shared)
                        cr = None if cr is None else right.index(per["R"][cr][1])
            if cl is not None and cr is not None and cl != cr:
                if cl < cr:
                    left = [None] * (cr - cl) + left
                else:
                    right = [None] * (cl - cr) + right
            crow = max(cl or 0, cr or 0) if (cl is not None or cr is not None) else 0
            sym = build_hub(it.comp, left, right, bottom)
            syms.append(sym)
            chainrow.append(crow)
            right_rows.append({p.get("net"): r - crow for r, p in enumerate(right) if p and p.get("net")})
        elif it.style == "two":
            if it.first is None:
                it.orient_two(left_chain)
            syms.append(build_two(it.comp, it.ends[0], it.ends[1], it.extra, False))
            chainrow.append(0)
            right_rows.append({p.get("net"): 0 for p, sd in item_pins(it) if sd == "R" and p.get("net")})
        elif it.style == "fet":
            syms.append(build_fet(it.comp, it.comp.get("kind") == "pfet"))
            chainrow.append(0)
            right_rows.append({p.get("net"): 0 for p, sd in item_pins(it) if sd == "R" and p.get("net")})
        elif it.style == "dcc":
            syms.append(build_dcc(it.comp))
            chainrow.append(0)
            right_rows.append({p.get("net"): 0 for p, sd in item_pins(it) if sd == "R" and p.get("net")})
        else:
            syms.append(build_dser(it.comp))
            chainrow.append(0)
            right_rows.append({p.get("net"): 0 for p, sd in item_pins(it) if sd == "R" and p.get("net")})
    return where, gap, syms, chainrow, row_nets, spread_sides


def side_pin_rows(sym, x, y, side):
    """Pin rows (absolute y) of one side of a placed hub-like symbol."""
    out = {}
    for pin in sym.pins:
        if (side == "L" and pin["out"] == (-1, 0)) or (side == "R" and pin["out"] == (1, 0)):
            out[pin["p"]["number"]] = y + pin["y"]
    return out


def item_state(seq):
    """The pin sides and orientation that a layout changes, for restore_items()."""
    return [(it, dict(it.side), it.first, list(getattr(it, "ends", []))) for it in seq]


def restore_items(state):
    for it, side, first, ends in state:
        it.side, it.first = side, first
        if ends:
            it.ends = ends


def layout_row(seq, lows, ups, ctx, key, dry=False, free=True, spread=False):
    if dry:
        # a trial layout must not leave its pin-side changes behind
        saved = item_state(seq)
        try:
            return _layout_row(seq, lows, ups, ctx, key, True, free, spread)
        finally:
            restore_items(saved)
    return _layout_row(seq, lows, ups, ctx, key, False, free, spread)


def _layout_row(seq, lows, ups, ctx, key, dry, free, spread=False):
    where, gap, syms, chainrow, row_nets, spread_sides = plan_row(seq, lows, ups, ctx, key, spread)
    row = Row()
    row.spread = spread_sides
    zones = defaultdict(lambda: {"low": [], "up": []})
    free_low, free_up = [], []
    for col in lows + ups:
        z, cat, rk = where[id(col)]
        if z is None:
            if free:
                (free_low if col.kind == "low" else free_up).append(col)
        else:
            zones[z][col.kind].append((cat, rk, col))
    # single-contact pins on hub sides carry labels into the zone next to them
    def lbl_extent(k, side):
        if k < 0 or k >= len(seq):
            return 0
        it, w = seq[k], 0
        if it.style in ("two", "fet", "dcc", "dser"):
            ps = [(p, s) for p, s in item_pins(it) if s == side]
        else:
            ps = [(p, s) for p, s in item_pins(it) if s == side]
        for p, s in ps:
            n = p.get("net")
            if n and n != GROUND and row_nets[n] == 1:
                w = max(w, 1 + math.ceil(label_len(n) / U))
        return w
    x = 0
    ypos = []
    for k in range(len(seq) + 1):
        lblA = lbl_extent(k - 1, "R")
        lblB = lbl_extent(k, "L")
        z = zones.get(k, {"low": [], "up": []})
        # order: A's right-side columns (nearest A), gap columns, B's left-side columns (nearest B)
        rowsA = side_pin_rows(syms[k - 1], 0, 0, "R") if k > 0 else {}
        rowsB = side_pin_rows(syms[k], 0, 0, "L") if k < len(seq) else {}

        def keyf(entry, kind):
            cat, rk, col = entry
            if cat == "A":
                r = rowsA.get(rk[1], 0)
                return (0, -r if kind == "low" else r, col.index)
            if cat == "gap":
                return (1, 0, col.index)
            r = rowsB.get(rk[1], 0)
            return (2, r if kind == "low" else -r, col.index)
        lowseq = sorted(z["low"], key=lambda e: keyf(e, "low"))
        upseq = sorted(z["up"], key=lambda e: keyf(e, "up"))
        inner = x + lblA + 1
        wl = sum(col_width(e[2]) for e in lowseq)
        wu = sum(col_width(e[2]) for e in upseq)
        gapnet = gap.get(k)
        need = max(wl, wu, (math.ceil(label_len(gapnet) / U) + 3) if gapnet else 0, 3 if 0 < k < len(seq) else 1)
        if 0 < k < len(seq):
            # nets running between two neighbours need room for their labels in between
            shared = {p.get("net") for p, sd in item_pins(seq[k - 1]) if sd == "R"} & {p.get("net") for p, sd in item_pins(seq[k]) if sd == "L"}
            shared -= {None, GROUND}
            if len(shared) > 1:
                need = max(need, max(math.ceil(label_len(n) / U) for n in shared) + 2 + len(shared) // 2)
        for seqs, kind in ((lowseq, "low"), (upseq, "up")):
            cx = inner
            for cat, rk, col in seqs:
                anchor_row = None
                if cat == "A":
                    anchor_row = rowsA.get(rk[1])
                elif cat == "B":
                    anchor_row = rowsB.get(rk[1])
                col.place = (cx + 1, cat, anchor_row, k)
                cx += col_width(col)
        x = inner + need + 1 + lblB
        if k < len(seq):
            sym = syms[k]
            w = item_width(seq[k], sym)
            ypos.append((x, w))
            x += w
    # free columns at the end of the row (grouped by net)
    free_low.sort(key=lambda c: (str(c.attach), c.index))
    free_up.sort(key=lambda c: (str(c.attach), c.index))
    if free_low or free_up:
        x += 1
        cl = cu = x
        for col in free_low:
            col.place = (cl + 1, "free", None, None)
            cl += col_width(col)
        for col in free_up:
            col.place = (cu + 1, "free", None, None)
            cu += col_width(col)
        x = max(cl, cu) + 1
    row.width = x
    if dry:
        return row
    row.gap_nets = [gap[k] for k in sorted(gap) if gap[k]]
    row.n_items = len(seq)
    # place the signal-line items
    for k, it in enumerate(seq):
        x0, w = ypos[k]
        sym = syms[k]
        if it.style == "hub":
            part = Part(sym, x0 + sym.L, -(chainrow[k] + 1))
        elif it.style == "two":
            part = Part(sym, x0 + w // 2, 0)
        elif it.style == "fet":
            part = Part(sym, x0 + 2, 0)
        elif it.style == "dcc":
            part = Part(sym, x0 + max(3, w // 2), 0)
        else:
            part = Part(sym, x0 + 2, 0)
        part.cluster = k
        row.parts.append(part)
    # columns: hub-attached ones hang from their pin row, gap/free ones from the signal line
    pinrow = {}
    for part in row.parts:
        for pin, (px, py) in part.pin_points():
            pinrow[(part.sym.comp["ref"], pin["p"]["number"])] = py
    for col in lows + ups:
        cx, cat, arow, k = col.place
        rk = where[id(col)][2]
        # the signal-line item a column belongs to (supply rails are wired per item)
        cluster = rk[0] if rk else (k - 1 if cat == "gap" else -1)
        if rk:
            arow = pinrow[(seq[rk[0]].comp["ref"], rk[1])]
        if col.kind == "low":
            top = max(2, (arow + 2) if arow is not None else 2)
            for i, (comp, a, b, extra) in enumerate(col.parts):
                sym = build_two(comp, a, b, extra, True)
                row.parts.append(Part(sym, cx, top + 2 + 6 * i, cluster))
                if i:
                    row.links.append((a.get("net"), (cx, top + 6 * i - 2), (cx, top + 6 * i)))
            row.cols_low.append(col)
        else:
            bottom = min(-2, (arow - 2) if arow is not None else -2)
            comp, a, b, extra = col.parts[0]
            if b is None:
                sym = build_flag(comp) if comp.get("kind") == "power_flag" else build_tp(comp)
                row.parts.append(Part(sym, cx, bottom if sym.flag else bottom - 1, cluster))
            else:
                sym = build_two(comp, a, b, extra, True)
                row.parts.append(Part(sym, cx, bottom - 2, cluster))
            row.cols_up.append(col)
    return row


def build_group_rows(comps, ctx, key):
    items, lows, ups = group_plan(comps, ctx, key)
    chains = chain_order(items, ctx)
    rows_seq, cur = [], []
    for ch in chains:
        trial = cur + ch
        if cur and layout_row(trial, lows, ups, ctx, key, dry=True, free=False).width > ROW_MAX_U:
            rows_seq.append(cur)
            cur = list(ch)
        else:
            cur = trial
        # a single signal chain is only broken when it would not fit the page width
        while len(cur) > 1 and layout_row(cur, lows, ups, ctx, key, dry=True, free=False).width > ROW_HARD_U:
            cut = len(cur) - 1
            while cut > 1 and layout_row(cur[:cut], lows, ups, ctx, key, dry=True, free=False).width > ROW_HARD_U:
                cut -= 1
            rows_seq.append(cur[:cut])
            cur = cur[cut:]
    if cur or not rows_seq:
        rows_seq.append(cur)
    # each column belongs to the first row that shows a part it connects to
    remaining_low, remaining_up = list(lows), list(ups)
    assigned = []
    for seq in rows_seq:
        where, _ = attach_cols(seq, remaining_low + remaining_up, ctx)
        mine_low = [c for c in remaining_low if where[id(c)][0] is not None]
        mine_up = [c for c in remaining_up if where[id(c)][0] is not None]
        remaining_low = [c for c in remaining_low if c not in mine_low]
        remaining_up = [c for c in remaining_up if c not in mine_up]
        assigned.append([seq, mine_low, mine_up])
    # unattached columns join the last row while it stays narrow enough, else rows of their own
    free = sorted(remaining_low + remaining_up, key=lambda c: (str(c.attach), c.index))
    for col in free:
        seq, lo, up = assigned[-1]
        trial_lo, trial_up = (lo + [col], up) if col.kind == "low" else (lo, up + [col])
        if layout_row(seq, trial_lo, trial_up, ctx, key, dry=True).width <= ROW_MAX_U or (not seq and not lo and not up):
            assigned[-1] = [seq, trial_lo, trial_up]
        else:
            assigned.append([[], [col] if col.kind == "low" else [], [col] if col.kind == "up" else []])
    return [(seq, lo, up) for seq, lo, up in assigned if seq or lo or up]


def route_group(comps, ctx, key):
    """Lay out and route every row of one group: [(row, board, grounds, ncs, tbd)].

    A row whose labels needed a fallback spot or whose wires cross another net is laid
    out once more with its buses spread (see plan_row) and routed again. A spread bus
    is taller, so that variant is kept only for a clear gain: fewer fallback labels,
    or as many and at most half the crossings."""
    out = []
    for seq, lo, up in build_group_rows(comps, ctx, key):
        state = item_state(seq)
        row = layout_row(seq, lo, up, ctx, key)
        routed = (row,) + route_row(row, ctx, key)
        fallback, crossings = routed[1].fallback, routed[1].crossings()
        if fallback or crossings:
            restore_items(state)
            wide = layout_row(seq, lo, up, ctx, key, spread=True)
            if wide.spread:
                alt = (wide,) + route_row(wide, ctx, key)
                if alt[1].fallback < fallback or (alt[1].fallback == fallback and 2 * alt[1].crossings() <= crossings):
                    routed = alt
        out.append(routed)
    return out


# --------------------------------------------------------------------------------------
# Grid router

DIRS = ((1, 0), (0, 1), (-1, 0), (0, -1))
DIRI = {d: i for i, d in enumerate(DIRS)}


def ekey(p, d):
    x, y = p
    return ("h", x, y) if d == 0 else ("h", x - 1, y) if d == 2 else ("v", x, y) if d == 1 else ("v", x, y - 1)


class Board:
    def __init__(self):
        self.blocked, self.eblock = set(), set()
        self.hard, self.ehard = set(), set()   # symbol bodies and labels (text is "soft")
        self.edge, self.cell, self.node = {}, defaultdict(set), {}
        self.pin, self.pin_out, self.reserved = {}, {}, {}
        self.rects, self.labels, self.trees = [], [], defaultdict(list)
        self.bounds = None
        self.fallback = 0

    def block_rect(self, r, clear=0.4, keep=True, soft=False):
        x0, y0, x1, y1 = r[0] - clear, r[1] - clear, r[2] + clear, r[3] + clear
        if keep:
            self.rects.append((x0, y0, x1, y1))
        pts, edges = self.blocked, self.eblock
        i0, i1 = math.ceil(x0 / U - 1e-9), math.floor(x1 / U + 1e-9)
        j0, j1 = math.ceil(y0 / U - 1e-9), math.floor(y1 / U + 1e-9)
        new_p, new_e = [], []
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                new_p.append((i, j))
        for j in range(math.floor(y0 / U), math.ceil(y1 / U)):
            if (j + 1) * U > y0 and j * U < y1:
                for i in range(i0, i1 + 1):
                    new_e.append(("v", i, j))
        for i in range(math.floor(x0 / U), math.ceil(x1 / U)):
            if (i + 1) * U > x0 and i * U < x1:
                for j in range(j0, j1 + 1):
                    new_e.append(("h", i, j))
        pts.update(new_p)
        edges.update(new_e)
        if not soft:
            self.hard.update(new_p)
            self.ehard.update(new_e)

    def inside(self, p):
        x0, y0, x1, y1 = self.bounds
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1

    def own_dirs(self, net, p):
        return [d for d in range(4) if self.edge.get(ekey(p, d)) == net]

    def foreign(self, net, p):
        return any(n != net for n in self.cell.get(p, ()))

    def commit(self, net, path):
        for a, b in zip(path, path[1:]):
            self.edge[ekey(a, DIRI[(b[0] - a[0], b[1] - a[1])])] = net
        for p in path:
            self.cell[p].add(net)
        self.node[path[0]] = net
        self.node[path[-1]] = net
        for i in range(1, len(path) - 1):
            if (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]) != (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]):
                self.node[path[i]] = net

    def joinable(self, net, p):
        return p not in self.pin and not self.foreign(net, p) and len(self.own_dirs(net, p)) <= 2

    def crossings(self):
        """Grid points where a wire of one net runs straight across a wire of another
        (drawn without a junction, so not connected, but easy to misread)."""
        n = 0
        for (k, x, y), net in self.edge.items():
            if k == "h" and self.edge.get(("h", x - 1, y)) == net:
                other = self.edge.get(("v", x, y))
                n += other is not None and other != net and self.edge.get(("v", x, y - 1)) == other
        return n

    def astar(self, net, src, targets, pin_targets, cap, limit=60000):
        pts = list(targets) + list(pin_targets)
        bx0, by0 = min(p[0] for p in pts), min(p[1] for p in pts)
        bx1, by1 = max(p[0] for p in pts), max(p[1] for p in pts)

        def h(p):
            return max(bx0 - p[0], 0, p[0] - bx1) + max(by0 - p[1], 0, p[1] - by1)
        sdir = self.pin_out[src]
        heap = [(h(src), 0, 0, src, -1, False)]
        best, parent, count = {(src, -1): 0}, {}, 0
        while heap:
            _, g, _, p, d, goal = heapq.heappop(heap)
            if goal:
                path, s = [p], (p, d)
                while s in parent:
                    s = parent[s]
                    path.append(s[0])
                return path[::-1]
            if best.get((p, d), 1e9) < g:
                continue
            count += 1
            if count > limit:
                return None
            here_foreign = p != src and self.foreign(net, p)
            for nd in range(4):
                if d == -1:
                    if nd != sdir:
                        continue
                elif nd == (d + 2) % 4 or (nd != d and here_foreign):
                    continue
                qp = (p[0] + DIRS[nd][0], p[1] + DIRS[nd][1])
                if not self.inside(qp):
                    continue
                e = ekey(p, nd)
                if e in self.eblock or e in self.edge or qp in self.blocked:
                    continue
                ng = g + 1 + (BEND_COST if d != -1 and nd != d else 0)
                if qp in self.pin:
                    if qp in pin_targets and nd == (pin_targets[qp] + 2) % 4 and ng <= cap:
                        parent[(qp, nd)] = (p, d)
                        heapq.heappush(heap, (ng, ng, len(parent), qp, nd, True))
                    continue
                owner = self.node.get(qp) or self.reserved.get(qp)
                if owner is not None and owner != net:
                    continue
                cq = self.cell.get(qp, ())
                if net in cq:
                    if qp in targets and ng <= cap:
                        parent[(qp, nd)] = (p, d)
                        heapq.heappush(heap, (ng, ng, len(parent), qp, nd, True))
                    continue
                if any(n != net for n in cq):
                    ng += CROSS_COST
                if ng + h(qp) > cap or ng >= best.get((qp, nd), 1e9):
                    continue
                best[(qp, nd)] = ng
                parent[(qp, nd)] = (p, d)
                heapq.heappush(heap, (ng + h(qp), ng, len(parent), qp, nd, False))
        return None

    def route_net(self, net, terms, primary=(), isolate=False):
        """Connect the contacts of one net into as few trees as short detours allow.

        Contacts on the signal line (`primary`) are joined first, so that the line is
        drawn straight and the hanging parts join it with short drops. With `isolate`
        the contacts form their own trees (a supply rail is wired per item)."""
        trees = [] if isolate else self.trees[net]
        todo = sorted(t for t in terms if not any(t in tr for tr in self.trees[net]))
        first = [t for t in todo if t in primary]
        rest = [t for t in todo if t not in primary]
        if not trees and todo:
            start = (first or rest).pop(0)
            trees.append({start})
        for pending in (first, rest):
            self._grow(net, trees, pending)
        if isolate:
            self.trees[net].extend(trees)

    def _grow(self, net, trees, pending):
        pending = list(pending)
        while pending:
            def dist(t):
                return min(abs(t[0] - p[0]) + abs(t[1] - p[1]) for tr in trees for p in tr)
            t = min(pending, key=lambda t: (dist(t), t))
            pending.remove(t)
            targets, pin_targets = set(), {}
            for tr in trees:
                wired = [p for p in tr if self.own_dirs(net, p)]
                if wired:
                    targets |= {p for p in tr if self.joinable(net, p)}
                else:
                    for p in tr:
                        pin_targets[p] = self.pin_out[p]
            if not targets and not pin_targets:
                trees.append({t})
                continue
            manh = min(abs(t[0] - p[0]) + abs(t[1] - p[1]) for p in list(targets) + list(pin_targets))
            cap = min(DETOUR[2], DETOUR[0] * manh + DETOUR[1])
            path = self.astar(net, t, targets, pin_targets, cap)
            if not path:
                trees.append({t})
                continue
            self.commit(net, path)
            end = path[-1]
            tree = next(tr for tr in trees if end in tr)
            tree.update(path)

    def label_spot(self, net, tree, length, pin=None, long=False, vertical=False, overlap=False, wires=False):
        """Best anchor for one label of `net` on `tree`: (score, anchor, stub points, direction).

        By default the label is horizontal, at most three grid steps from the tree and
        clear of every symbol, text and wire. `long` allows stubs up to eight steps,
        `vertical` vertical labels, `overlap` a label body over text and `wires` a body
        over crossing wires. The anchor and the stub are always electrically clear: no
        other net, contact or node is touched."""
        K = math.ceil((length + 0.6) / U)
        best = None
        cands = [pin] if pin is not None else sorted(tree)
        top = 9 if long else 4
        stubs = range(1, top) if pin is not None else range(0, top)
        for p in cands:
            if pin is None and (p in self.pin or self.foreign(net, p) or len(self.own_dirs(net, p)) > 2):
                continue
            own = self.own_dirs(net, p)
            sds = [self.pin_out[p]] if pin is not None else [d for d in (3, 0, 2, 1) if d not in own]
            for sd in sds:
                for s in stubs:
                    if s == 0 and len(own) == 0:
                        continue
                    stub, ok, cur = [], True, p
                    for _ in range(s):
                        e = ekey(cur, sd)
                        nxt = (cur[0] + DIRS[sd][0], cur[1] + DIRS[sd][1])
                        if e in self.eblock or e in self.edge or nxt in self.blocked or nxt in self.pin or self.cell.get(nxt) or nxt in self.node or \
                                self.reserved.get(nxt, net) != net or not self.inside(nxt):
                            ok = False
                            break
                        stub.append(nxt)
                        cur = nxt
                    if not ok:
                        break
                    a = cur
                    if s == 0:
                        lds = [sd] if DIRS[sd][1] == 0 or vertical else []
                    elif DIRS[sd][1] == 0:
                        lds = [sd]
                    else:
                        lds = [0, 2] + ([sd] if vertical else [])
                    for ld in lds:
                        dx, dy = DIRS[ld]
                        if s == 0 and ld in own:
                            continue
                        free = True
                        for k in range(1, K + 1):
                            pt = (a[0] + dx * k, a[1] + dy * k)
                            if pt in self.pin or pt in self.node or not self.inside(pt) or self.reserved.get(pt, net) != net or pt in self.hard or \
                                    (not wires and self.cell.get(pt)) or (wires and any(e2 in self.edge for e2 in (ekey(pt, ld), ekey(pt, (ld + 2) % 4)))) or \
                                    (not overlap and (pt in self.blocked or ekey((a[0] + dx * (k - 1), a[1] + dy * (k - 1)), ld) in self.eblock)):
                                free = False
                                break
                        if not free:
                            continue
                        if dy == 0:
                            x0, x1 = sorted((a[0] * U, a[0] * U + dx * length))
                            box = (x0, a[1] * U - 0.95, x1, a[1] * U + 0.95)
                        else:
                            y0, y1 = sorted((a[1] * U, a[1] * U + dy * length))
                            box = (a[0] * U - 0.95, y0, a[0] * U + 0.95, y1)
                        if not overlap and any(box[0] < r[2] and box[2] > r[0] and box[1] < r[3] and box[3] > r[1] for r in self.rects):
                            continue
                        junction = s > 0 and pin is None
                        score = 2 * s + (0 if sd == 3 else 0.5 if DIRS[sd][1] == 0 else 1.5) + (1 if junction else 0) + (3 if dy else 0)
                        cand = (score, p[1], p[0], ld, sd, s)
                        if best is None or cand < best[0]:
                            best = (cand, a, [p] + stub, ld)
        return best

    def escape_spot(self, net, tree, length, pin=None, strict=True, limit=20000):
        """Search outwards from the tree along free grid lines (crossing other wires only
        at right angles) for the nearest point where a horizontal label fits; the path
        becomes the label stub. `strict` keeps path and label clear of text as well."""
        K = math.ceil((length + 0.6) / U)
        stop_p, stop_e = (self.blocked, self.eblock) if strict else (self.hard, self.ehard)
        starts = []
        if pin is not None:
            starts.append((pin, [self.pin_out[pin]]))
        else:
            for p in sorted(tree):
                if p not in self.pin and not self.foreign(net, p) and len(self.own_dirs(net, p)) <= 2:
                    starts.append((p, [d for d in range(4) if d not in self.own_dirs(net, p)]))
        heap, parent, best, count = [], {}, {}, 0
        for p, dirs in starts:
            for d in dirs:
                heapq.heappush(heap, (0, len(parent) + len(heap), p, d, -1, True))
        while heap:
            g, _, p, d, pdir, first = heapq.heappop(heap)
            count += 1
            if count > limit:
                return None
            qp = (p[0] + DIRS[d][0], p[1] + DIRS[d][1])
            e = ekey(p, d)
            if e in stop_e or e in self.edge or qp in stop_p or qp in self.pin or not self.inside(qp):
                continue
            if (self.node.get(qp) or self.reserved.get(qp) or net) != net or self.node.get(qp) == net:
                continue
            if best.get((qp, d), 1e9) <= g:
                continue
            best[(qp, d)] = g
            parent[(qp, d)] = (p, pdir, first)
            crossing = bool(self.cell.get(qp))
            if not crossing:
                for ld in (0, 2):
                    dx = DIRS[ld][0]
                    if ld == (d + 2) % 4:
                        continue
                    ok = True
                    for k in range(1, K + 1):
                        pt = (qp[0] + dx * k, qp[1])
                        if pt in self.pin or pt in self.node or self.cell.get(pt) or pt in stop_p or not self.inside(pt) or self.reserved.get(pt, net) != net:
                            ok = False
                            break
                    if ok and strict:
                        x0, x1 = sorted((qp[0] * U, qp[0] * U + dx * length))
                        ok = not any(x0 < r[2] and x1 > r[0] and qp[1] * U - 0.95 < r[3] and qp[1] * U + 0.95 > r[1] for r in self.rects)
                    if ok:
                        path, st = [qp], (qp, d)
                        while True:
                            pp, pd, pf = parent[st]
                            path.append(pp)
                            if pf:
                                break
                            st = (pp, pd)
                        return (None, qp, path[::-1], ld)
            for nd in range(4):
                if nd == (d + 2) % 4 or (crossing and nd != d):
                    continue
                heapq.heappush(heap, (g + 1 + (BEND_COST if nd != d else 0) + (CROSS_COST if crossing else 0), len(parent) + len(heap), qp, nd, d, False))
        return None

    def along_spot(self, net, tree, length):
        """A label laid along a straight run of its own horizontal wire (used inside dense
        buses, where any other spot would put the label body over a different net)."""
        K = math.ceil((length + 0.6) / U)
        for p in sorted(tree, key=lambda t: (t[1], t[0])):
            if p in self.pin or self.foreign(net, p) or sorted(self.own_dirs(net, p)) != [0, 2]:
                continue
            for ld in (0, 2):
                dx = DIRS[ld][0]
                run = [(p[0] + dx * k, p[1]) for k in range(1, K + 1)]
                if all(q2 not in self.pin and q2 not in self.node and self.cell.get(q2) == {net} and
                       sorted(self.own_dirs(net, q2)) == [0, 2] and q2 not in self.hard for q2 in run):
                    return (None, p, [p], ld)
        return None

    def place_label(self, net, tree, shape, pin=None):
        length = label_len(net)
        attempts = [lambda: self.label_spot(net, tree, length, pin),
                    lambda: self.label_spot(net, tree, length, pin, long=True, vertical=True),
                    lambda: self.escape_spot(net, tree, length, pin),
                    lambda: self.label_spot(net, tree, length, pin, long=True, vertical=True, overlap=True),
                    lambda: self.escape_spot(net, tree, length, pin, strict=False),
                    lambda: None if pin is not None else self.along_spot(net, tree, length),
                    lambda: self.label_spot(net, tree, length, pin, long=True, vertical=True, overlap=True, wires=True)]
        spot = None
        for level, attempt in enumerate(attempts):
            spot = attempt()
            if spot is not None:
                break
        if spot is None:
            # Boxed in by other wires: anchor the label on the contact (or tree point)
            # itself. Only the anchor connects in KiCad, so this stays electrically
            # exact; the label body may overprint a neighbouring wire.
            p = pin if pin is not None else min(tree, key=lambda t: (self.foreign(net, t), t in self.pin, t[1], t[0]))
            d = self.pin_out.get(p, 0)
            ld = d if DIRS[d][1] == 0 else 0
            spot, level = (None, p, [p], ld), len(attempts)
        if level >= 3:
            self.fallback += 1
        _, a, stub, ld = spot
        if len(stub) > 1:
            self.commit(net, stub)
            tree.update(stub)
        self.node[a] = net
        dx, dy = DIRS[ld]
        if dy == 0:
            x0, x1 = sorted((a[0] * U, a[0] * U + dx * length))
            self.block_rect((x0 + (0.3 if dx > 0 else 0), a[1] * U - 0.95, x1 - (0.3 if dx < 0 else 0), a[1] * U + 0.95), clear=0.2)
        else:
            y0, y1 = sorted((a[1] * U, a[1] * U + dy * length))
            self.block_rect((a[0] * U - 0.95, y0 + (0.3 if dy > 0 else 0), a[0] * U + 0.95, y1 - (0.3 if dy < 0 else 0)), clear=0.2)
        self.labels.append((net, a, ld, shape))

    def segments(self, net):
        own = defaultdict(list)
        for e, n in self.edge.items():
            if n != net:
                continue
            k, x, y = e
            a, b = ((x, y), (x + 1, y)) if k == "h" else ((x, y), (x, y + 1))
            own[a].append(b)
            own[b].append(a)
        anchors = {a for n, a, _, _ in self.labels if n == net}

        def is_node(p):
            nb = own[p]
            if len(nb) != 2 or p in self.pin or p in anchors:
                return True
            return (nb[0][0] - p[0], nb[0][1] - p[1]) != (p[0] - nb[1][0], p[1] - nb[1][1])
        segs, seen = [], set()
        for p in sorted(own):
            if not is_node(p):
                continue
            for nb in sorted(own[p]):
                if (p, nb) in seen:
                    continue
                d = (nb[0] - p[0], nb[1] - p[1])
                cur = nb
                seen.add((p, nb))
                seen.add((nb, p))
                while not is_node(cur):
                    nxt = (cur[0] + d[0], cur[1] + d[1])
                    seen.add((cur, nxt))
                    seen.add((nxt, cur))
                    cur = nxt
                segs.append((p, cur))
        return segs


def route_row(row, ctx, key):
    """Pins, obstacles, ground symbols, wires and labels of one row (grid units)."""
    b = Board()
    terms = defaultdict(list)
    grounds, ncs, tbd = [], [], []
    xs, ys = [], []
    for part in row.parts:
        sym = part.sym
        for r in sym.boxes + sym.texts:
            xs += [part.x * U + r[0], part.x * U + r[2]]
            ys += [part.y * U + r[1], part.y * U + r[3]]
        for pin, pt in part.pin_points():
            xs.append(pt[0] * U)
            ys.append(pt[1] * U)
    b.bounds = (math.floor(min(xs) / U) - MARGIN_U, math.floor(min(ys) / U) - MARGIN_U,
                math.ceil(max(xs) / U) + MARGIN_U, math.ceil(max(ys) / U) + MARGIN_U)
    for part in row.parts:
        sym = part.sym
        for r in sym.boxes:
            b.block_rect((part.x * U + r[0], part.y * U + r[1], part.x * U + r[2], part.y * U + r[3]), clear=0.3)
        for r in sym.texts:
            b.block_rect((part.x * U + r[0], part.y * U + r[1], part.x * U + r[2], part.y * U + r[3]), clear=0.3, soft=True)
        bottom_gnd = []
        for pin, pt in part.pin_points():
            p = pin["p"]
            net = p.get("net")
            if pt in b.pin:
                raise ValueError(f"{key}: two contacts at one point {pt} ({sym.comp['ref']}.{p['number']})")
            b.pin[pt] = net
            b.pin_out[pt] = DIRI[pin["out"]]
            if is_nc(p):
                ncs.append(pt)
            elif not net:
                tbd.append((pt, pin["out"]))
            elif net == GROUND:
                if pin["out"] == (0, 1) and len(sym.pins) > 3:
                    bottom_gnd.append(pt)
                else:
                    grounds.append((pt, pin["out"]))
            else:
                terms[net].append(pt)
        if len(bottom_gnd) == 1:
            grounds.append((bottom_gnd[0], (0, 1)))
        elif bottom_gnd:
            # several ground contacts on the bottom edge share one ground symbol
            bottom_gnd.sort()
            y = bottom_gnd[0][1] + 1
            for pt in bottom_gnd:
                b.commit(GROUND, [pt, (pt[0], y)])
            b.commit(GROUND, [(x, y) for x in range(bottom_gnd[0][0], bottom_gnd[-1][0] + 1)])
            mid = bottom_gnd[len(bottom_gnd) // 2]
            grounds.append(((mid[0], y), (0, 1)))
    # every contact keeps its first grid step outwards for its own net
    escape = Counter()
    for net, pts in terms.items():
        for pt in pts:
            d = DIRS[b.pin_out[pt]]
            escape[(pt[0] + d[0], pt[1] + d[1])] += 1
    for net, pts in terms.items():
        for pt in pts:
            d = DIRS[b.pin_out[pt]]
            q2 = (pt[0] + d[0], pt[1] + d[1])
            if escape[q2] == 1 and q2 not in b.pin:
                b.reserved[q2] = net
    for pt, out in grounds:
        dx, dy = out
        px, py = pt[0] * U, pt[1] * U
        if dx == 0:
            b.block_rect((px - 1.6, min(py + dy * 0.3, py + dy * 2.9), px + 1.6, max(py + dy * 0.3, py + dy * 2.9)), clear=0.1)
        else:
            b.block_rect((min(px + dx * 0.3, px + dx * 2.9), py - 1.6, max(px + dx * 0.3, px + dx * 2.9), py + 1.6), clear=0.1)
        b.node[pt] = GROUND
    for pt in ncs:
        b.node[pt] = "<NC>"
    for pt, out in tbd:
        b.node[pt] = "<TBD>"
        b.block_rect((pt[0] * U + out[0] * 1.3 - 2.6, pt[1] * U - 2.2, pt[0] * U + out[0] * 1.3 + 2.6, pt[1] * U - 0.8), clear=0.1)
    for net, a, c in row.links:
        mid = (a[0], a[1] + 1)
        b.commit(net, [a, mid, c])
        b.reserved[mid] = net  # other wires may not cross a column between its parts
        b.trees[net].append({a, mid, c})
    shape = {n: ("bidirectional" if ctx.leaves_group(n, key) else "passive") for n in terms}
    # single-contact nets: label at the contact first (they claim the space next to their pin)
    singles = sorted(n for n, ts in terms.items() if len(ts) == 1 and not b.trees[n])
    for n in singles:
        tree = {terms[n][0]}
        b.trees[n].append(tree)
        b.place_label(n, tree, shape[n], pin=terms[n][0])
    primary = {pt for part in row.parts[:row.n_items] for pin, pt in part.pin_points()}
    multi = [n for n in terms if n not in singles]
    gaps = [n for n in row.gap_nets if n in multi]
    multi.sort(key=lambda n: (n not in gaps, gaps.index(n) if n in gaps else 0,
                              (max(p[0] for p in terms[n]) - min(p[0] for p in terms[n])) + (max(p[1] for p in terms[n]) - min(p[1] for p in terms[n])), n))
    cluster = {pt: part.cluster for part in row.parts for pin, pt in part.pin_points()}
    owner = {pt: i for i, part in enumerate(row.parts) for pin, pt in part.pin_points()}
    solo = []
    for n in multi:
        # A box with one net on two different sides (a pass-through) is wired on the side
        # that faces the rest of the net; its far-side contacts carry their own labels.
        by_part = defaultdict(list)
        for t in terms[n]:
            by_part[owner[t]].append(t)
        for i, ts in sorted(by_part.items()):
            if len({b.pin_out[t] for t in ts}) < 2:
                continue
            others = [t for t in terms[n] if owner[t] != i]
            if others:
                cx = sum(t[0] for t in others) / len(others)
                cy = sum(t[1] for t in others) / len(others)
                keep = max(sorted({b.pin_out[t] for t in ts}), key=lambda d: sum(DIRS[d][0] * (cx - t[0]) + DIRS[d][1] * (cy - t[1]) for t in ts))
            else:
                keep = Counter(b.pin_out[t] for t in ts).most_common(1)[0][0]
            solo += [(n, t) for t in ts if b.pin_out[t] != keep]
    away = {t for n, t in solo}
    for n in multi:
        ts = [t for t in terms[n] if t not in away]
        if ctx.global_rail(n):
            for c in sorted({cluster[t] for t in ts}):
                b.route_net(n, [t for t in ts if cluster[t] == c], primary, isolate=True)
        else:
            b.route_net(n, ts, primary)
    for n, t in solo:
        b.trees[n].append({t})
    for n in sorted(multi):
        for tree in b.trees[n]:
            wired = any(b.own_dirs(n, p) for p in tree)
            if wired:
                b.place_label(n, tree, shape[n])
            else:
                (pt,) = tuple(tree)
                b.place_label(n, tree, shape[n], pin=pt)
    return b, grounds, ncs, tbd


# --------------------------------------------------------------------------------------
# Blocks, pages and emission

def flow_order(graph):
    """Components grouped as drawn: by group, then as listed."""
    groups = OrderedDict()
    for c in graph["components"]:
        groups.setdefault(c.get("group", "Інше"), []).append(c)
    return groups


def sheet_notes(graph):
    """Visible notes of one sheet (header and paragraphs, unwrapped), keyed by the first
    of their parts in drawing order.

    Every open item (blocking or not) and every drawing note must name the STACK
    section and the parts it concerns; it is placed once, at the top of the row that
    shows the first of those parts, so it lands on the page that shows them.
    """
    order = {c["ref"]: i for i, c in enumerate(c for comps in flow_order(graph).values() for c in comps)}
    entries = []
    for it in graph.get("open_items", []):
        status = "OPEN, блокує випуск" if it.get("blocking") else "умова опції, не блокує випуск"
        body = [it["description"], "Ворота (стенд): " + it.get("resolve", "")]
        entries.append((it, "open" if it.get("blocking") else "option", f"{it['id']} — {status} — STACK {it.get('stack', '')}", body))
    for note in graph.get("drawing_notes", []):
        entries.append((note, "note", f"{note['id']} — примітка — STACK {note.get('stack', '')}", [note.get("text", "")]))
    anchored, errors = defaultdict(list), []
    for item, kind, head, body in entries:
        if not str(item.get("stack", "")).strip():
            errors.append(f"{graph['sheet']} {item['id']}: no STACK section")
        refs = item.get("refs") or []
        unknown = [r for r in refs if r not in order]
        if not refs or unknown:
            errors.append(f"{graph['sheet']} {item['id']}: refs missing or not on this sheet: {unknown or refs}")
            continue
        anchor = min(refs, key=order.get)
        anchored[anchor].append({"id": item["id"], "kind": kind, "head": head, "body": body})
    if errors:
        raise ValueError("\n".join(errors))
    return anchored


def note_width(chars):
    """Frame width of a note wrapped at `chars` body characters (NOTE_W at the standard wrap)."""
    return max(NOTE_W, U * math.ceil((chars * NOTE_CYR_MM + 2 * NOTE_PAD) / U))


def wrap_note(note, chars=NOTE_CHARS):
    """Header and body lines of one note wrapped at `chars` body characters, with its frame size."""
    lines = []
    for para in note["body"]:
        lines += textwrap.wrap(para, width=chars, break_long_words=False, break_on_hyphens=False) or [""]
    # the bold header is wider: same ratio as at the standard wrap
    heads = textwrap.wrap(note["head"], width=chars * NOTE_HEAD_CHARS // NOTE_CHARS, break_long_words=False, break_on_hyphens=False)
    height = U * math.ceil((2 * NOTE_PAD + NOTE_LINE * (len(heads) + len(lines))) / U)
    return {"id": note["id"], "kind": note["kind"], "head": heads, "lines": lines, "height": height, "w": note_width(chars),
            "chars": chars}


def note_block(note, x, y, key):
    color = NOTE_COLORS[note["kind"]]
    x0, x1, y1 = x + 2.54, x + 2.54 + note["w"], y + note["height"]
    head = f"(text {q(chr(10).join(note['head']))} (exclude_from_sim no) (at {fm(x0 + NOTE_PAD)} {fm(y + NOTE_PAD)} 0) (effects (font (size {f(NOTE_SIZE)} {f(NOTE_SIZE)}) (bold yes) (color {color})) (justify left top)) (uuid {uid(key + '/head')}))"
    body = text("\n".join(note["lines"]), x0 + NOTE_PAD, y + NOTE_PAD + NOTE_LINE * len(note["head"]), key + "/body", NOTE_SIZE)
    frame = f"(rectangle (start {fm(x0)} {fm(y)}) (end {fm(x1)} {fm(y1)}) (stroke (width 0.254) (type dash) (color {color})) (fill (type none)) (uuid {uid(key + '/frame')}))"
    return "\n".join([frame, head, body])


class RowDraw:
    """A routed row with its bounding box (mm, row coordinates)."""

    def __init__(self, row, board, grounds, ncs, tbd):
        self.row, self.board, self.grounds, self.ncs, self.tbd = row, board, grounds, ncs, tbd
        xs, ys = [], []
        for r in board.rects:
            xs += [r[0], r[2]]
            ys += [r[1], r[3]]
        for e in board.edge:
            k, x, y = e
            xs += [x * U, (x + (k == "h")) * U]
            ys += [y * U, (y + (k == "v")) * U]
        self.box = (min(xs), min(ys), max(xs), max(ys))
        self.refs = [p.sym.comp["ref"] for p in row.parts]
        self.notes = []


def route_groups(graph, ctx):
    """Every functional group of one sheet, laid out and routed once: [(group, [RowDraw])]."""
    return [(group, [RowDraw(*routed) for routed in route_group(comps, ctx, (graph["sheet"], group))])
            for group, comps in flow_order(graph).items()]


def make_blocks(groups, notes, chars=NOTE_CHARS):
    """One block per functional group, split only if taller than a page.

    The routed rows are shared; each call gets its own row views with the notes
    wrapped at up to `chars` body characters, as far as the group's drawing is wide
    enough to hold the frame, and at NOTE_CHARS otherwise."""
    blocks = []
    for group, routed in groups:
        width = max(rd.box[2] - rd.box[0] for rd in routed)
        fit = max(c for c in range(NOTE_CHARS, max(chars, NOTE_CHARS) + 1) if c == NOTE_CHARS or note_width(c) + U <= width)
        rows = []
        for rd in routed:
            view = copy.copy(rd)
            view.notes = [wrap_note(n, fit) for ref in rd.refs for n in notes.get(ref, [])]
            rows.append(view)
        # split into page-sized blocks
        cur, h, part = [], 0.0, 0
        limit = AREA_Y1 - AREA_Y0 - 2 * U
        for rd in rows:
            rh = row_height(rd)
            if cur and h + rh > limit:
                blocks.append(Block(group, cur, part))
                cur, h, part = [], 0.0, part + 1
            cur.append(rd)
            h += rh
        blocks.append(Block(group, cur, part))
    return blocks


def row_height(rd):
    """Vertical space of one row in its block: notes, drawing, gap and grid rounding."""
    return sum(n["height"] + NOTE_GAP for n in rd.notes) + (rd.box[3] - rd.box[1]) + (ROW_GAP_U + 1) * U


class Block:
    def __init__(self, group, rows, part):
        self.group, self.rows, self.part = group, rows, part
        self.title = group if part == 0 else group + " (продовження)"
        w = max([tw(self.title, GROUP_SIZE) + U] + [rd.box[2] - rd.box[0] for rd in rows] +
                [n["w"] + U for rd in rows for n in rd.notes])
        self.w, self.h = w, 2 * U + sum(row_height(rd) for rd in rows)

    def right(self, x):
        """Drawn right edge with the left edge at grid position x: emit snaps each row's
        origin onto the grid, which moves the row right by less than one grid step."""
        return max([x + self.w] + [math.ceil((x - rd.box[0]) / U - 1e-9) * U + rd.box[2] for rd in self.rows])

    def fill(self):
        return self.w * self.h / ((AREA_X1 - AREA_X0) * (AREA_Y1 - AREA_Y0))


def page_fill(page):
    """Share of the drawable area that the blocks of one page take."""
    return sum(b.fill() for b, _, _ in page)


def layout_sheet(groups, notes):
    """Pages of one sheet ([(block, x, y)] each) and the note wrap they use.

    When the last page would stay sparse (a few blocks that are harder to find than on
    a fuller page), the notes are wrapped wider, as far as each group's drawing allows,
    and the narrowest such wrap that saves a page is kept."""
    pages = pack_pages(make_blocks(groups, notes))
    if len(pages) > 1 and page_fill(pages[-1]) < SPARSE_LAST_PAGE:
        for chars in NOTE_WIDE_CHARS:
            wide = pack_pages(make_blocks(groups, notes, chars))
            if len(wide) < len(pages):
                return wide, chars
    return pages, NOTE_CHARS


def pack_pages(blocks):
    """Pages of group blocks: in drawing order unless placing the larger blocks first
    saves a page (a nearly empty last page is harder to read than a reordered sheet)."""
    in_order = pack_first_fit(blocks)
    big_first = pack_first_fit(sorted(blocks, key=lambda b: (-b.h * b.w, blocks.index(b))))
    return big_first if len(big_first) < len(in_order) else in_order


def pack_first_fit(blocks):
    """Place group blocks in order, each on the first page that has room, at the highest
    (then leftmost) free spot; a block that fits nowhere starts a new page."""
    def free(placed, x, y, b):
        x1, y1 = b.right(x), y + b.h
        if x1 > AREA_X1 or y1 > AREA_Y1 or (x1 > TITLE_BLOCK_X and y1 > TITLE_BLOCK_Y):
            return False
        x1 = x + b.w
        return all(x1 + BLOCK_GAP <= px or px + pb.w + BLOCK_GAP <= x or y1 + BLOCK_GAP <= py or py + pb.h + BLOCK_GAP <= y
                   for pb, px, py in placed)

    def spot(placed, b):
        step = 3 * U
        xs = sorted({AREA_X0 + step * i for i in range(int((AREA_X1 - AREA_X0) / step))} |
                    {U * math.ceil((px + pb.w + BLOCK_GAP) / U) for pb, px, py in placed})
        ys = sorted({AREA_Y0 + step * i for i in range(int((AREA_Y1 - AREA_Y0) / step))} |
                    {U * math.ceil((py + pb.h + BLOCK_GAP) / U) for pb, px, py in placed})
        for y in ys:
            for x in xs:
                if free(placed, x, y, b):
                    return x, y
        return None
    pages = []
    for b in blocks:
        if b.h > AREA_Y1 - AREA_Y0 or b.right(AREA_X0) > AREA_X1:
            raise ValueError(f"group block {b.title!r} is larger than a page: {b.w:.0f} x {b.h:.0f} mm")
        # first page with room (a continuation never goes before its group's earlier part)
        first = max((i for i, pg in enumerate(pages) for pb, _, _ in pg if pb.group == b.group and pb.part < b.part), default=0)
        for page in pages[first:]:
            pos = spot(page, b)
            if pos is not None:
                page.append((b, pos[0], pos[1]))
                break
        else:
            pages.append([(b, AREA_X0, AREA_Y0)])
    return pages


def emit_row(rd, ox, oy, path, stem, counters, used_syms, out, stats, checks):
    """S-expressions of one routed row placed with its grid origin at (ox, oy) grid units."""
    b = rd.board
    for part in rd.row.parts:
        sym = part.sym
        c = sym.comp
        used_syms[sym.name] = sym
        X, Y = (part.x + ox) * U, (part.y + oy) * U
        key = stem + "/" + c["ref"]
        flag = sym.flag
        body = [f"(symbol (lib_id {q('sr_rx_v2_completed:' + sym.name)}) (at {fm(X)} {fm(Y)} 0) (unit 1) (exclude_from_sim no) (in_bom {'no' if flag else 'yes'}) (on_board {'no' if flag else 'yes'}) (dnp {'yes' if c.get('dnp') else 'no'}) (uuid {uid(key)})"]
        rx = sym.ref
        vx = sym.val
        body.append(prop("Reference", c["ref"], X + (rx[0] if rx else 0), Y + (rx[1] if rx else 0), rx is None, REF_SIZE, rx[2] if rx else ""))
        body.append(prop("Value", c["value"], X + vx[0], Y + vx[1], False, VALUE_SIZE, vx[2]))
        body += [prop("Footprint", c.get("footprint", ""), X, Y, True), prop("Datasheet", c.get("source", ""), X, Y, True),
                 prop("Description", c.get("description", ""), X, Y, True), prop("ReviewStatus", c.get("status", "TBD"), X, Y, True)]
        body += [f"(pin {q(p['number'])} (uuid {uid(key + '/pin/' + str(p['number']))}))" for p in c["pins"]]
        body += [f"(instances (project \"sr-rx-v2\" (path {q(path)} (reference {q(c['ref'])}) (unit 1)))))"]
        out.append("\n".join(body))
        for pin, (px, py) in part.pin_points():
            checks["pins"].append(((round((px + ox) * U, 3), round((py + oy) * U, 3)), pin["p"].get("net"), c["ref"], pin["p"]["number"]))
    for pt, outd in rd.grounds:
        name, a = GND_VARIANTS[outd]
        used_syms[name] = ground_symbol((name, a))
        counters["pwr"] += 1
        ref = f"#PWR{counters['pwr']:04d}"
        X, Y = (pt[0] + ox) * U, (pt[1] + oy) * U
        key = f"{stem}/gnd/{pt[0]}/{pt[1]}/{rd.refs[0]}"
        out.append(f"(symbol (lib_id {q('sr_rx_v2_completed:' + name)}) (at {fm(X)} {fm(Y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid {uid(key)}) "
                   f"{prop('Reference', ref, X, Y, True, 1.27)} {prop('Value', GROUND, X, Y + 3.81, True, 1.27)} {prop('Footprint', '', X, Y, True)} {prop('Datasheet', '', X, Y, True)} "
                   f"{prop('Description', 'Ground (GND) power symbol', X, Y, True)} (pin \"1\" (uuid {uid(key + '/pin')})) "
                   f"(instances (project \"sr-rx-v2\" (path {q(path)} (reference {q(ref)}) (unit 1)))))")
        stats["ground_symbols"] += 1
        checks["power"].append(((round(X, 3), round(Y, 3)), GROUND))
    for pt in rd.ncs:
        X, Y = (pt[0] + ox) * U, (pt[1] + oy) * U
        out.append(f"(no_connect (at {fm(X)} {fm(Y)}) (uuid {uid(f'{stem}/nc/{pt[0]}/{pt[1]}/{rd.refs[0]}')}))")
    for pt, outd in rd.tbd:
        X, Y = (pt[0] + ox) * U, (pt[1] + oy) * U
        out.append(text("TBD", X + outd[0] * 1.27 - (2.54 if outd[0] < 0 else 0), Y - 1.27, f"{stem}/tbd/{pt[0]}/{pt[1]}/{rd.refs[0]}", 0.889))
    nets = sorted({n for n in b.edge.values()})
    for net in nets:
        segs = b.segments(net)
        ends = Counter()
        for a, c in segs:
            A = ((a[0] + ox) * U, (a[1] + oy) * U)
            C = ((c[0] + ox) * U, (c[1] + oy) * U)
            out.append(f"(wire (pts (xy {fm(A[0])} {fm(A[1])}) (xy {fm(C[0])} {fm(C[1])})) (stroke (width 0) (type default)) (uuid {uid(f'{stem}/{rd.refs[0]}/w/{net}/{a}/{c}')}))")
            checks["wires"].append(((round(A[0], 3), round(A[1], 3)), (round(C[0], 3), round(C[1], 3))))
            ends[a] += 1
            ends[c] += 1
            stats["wires"] += 1
        for p, n in sorted(ends.items()):
            if n + (1 if p in b.pin else 0) >= 3:
                X, Y = (p[0] + ox) * U, (p[1] + oy) * U
                out.append(f"(junction (at {fm(X)} {fm(Y)}) (diameter 0) (color 0 0 0 0) (uuid {uid(f'{stem}/{rd.refs[0]}/j/{net}/{p}')}))")
                stats["junctions"] += 1
    for net, a, ld, shape in sorted(b.labels, key=lambda t: (t[0], t[1])):
        X, Y = (a[0] + ox) * U, (a[1] + oy) * U
        angle, just = {0: (0, "left"), 2: (180, "right"), 3: (90, "left"), 1: (270, "right")}[ld]
        key = f"{stem}/{rd.refs[0]}/l/{net}/{a}"
        out.append(f"(global_label {q(net)} (shape {shape}) (at {fm(X)} {fm(Y)} {angle}) {effects(LABEL_SIZE, f'(justify {just})')} (uuid {uid(key)}) {prop('Intersheetrefs', '${INTERSHEET_REFS}', X, Y, True)})")
        stats["global_labels"] += 1
        checks["labels"].append(((round(X, 3), round(Y, 3)), net))
    stats["fallback_labels"] += b.fallback
    stats["wire_crossings"] += b.crossings()


def check_page(stem, checks):
    """Re-derive connectivity from the emitted geometry; every drawn tree must be one design net."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)
    pts = defaultdict(list)
    for pt, net, ref, num in checks["pins"]:
        pts[pt].append(("pin", net, f"{ref}.{num}"))
    for pt, name in checks["labels"]:
        pts[pt].append(("name", name, "label"))
    for pt, name in checks["power"]:
        pts[pt].append(("name", name, "power"))
    for a, c in checks["wires"]:
        union(("p", a), ("p", c))
        pts.setdefault(a, [])
        pts.setdefault(c, [])
    for pt in pts:
        find(("p", pt))
    # a contact, label or wire end lying inside another wire is ambiguous: refuse it
    horiz, vert = defaultdict(list), defaultdict(list)
    for a, c in checks["wires"]:
        if a[1] == c[1]:
            horiz[a[1]].append((min(a[0], c[0]), max(a[0], c[0])))
        else:
            vert[a[0]].append((min(a[1], c[1]), max(a[1], c[1])))
    errors = []
    for pt in pts:
        for lo, hi in horiz.get(pt[1], ()):
            if lo < pt[0] < hi:
                errors.append(f"{stem}: point {pt} {pts[pt]} lies inside a horizontal wire {lo}..{hi}")
        for lo, hi in vert.get(pt[0], ()):
            if lo < pt[1] < hi:
                errors.append(f"{stem}: point {pt} {pts[pt]} lies inside a vertical wire {lo}..{hi}")
    comps = defaultdict(lambda: {"pins": [], "names": set(), "nets": set()})
    for pt, items in pts.items():
        root = find(("p", pt))
        for kind, val, what in items:
            if kind == "pin":
                comps[root]["pins"].append(what)
                comps[root]["nets"].add(val)
            else:
                comps[root]["names"].add(val)
    for root, cmp in comps.items():
        nets = cmp["nets"]
        if None in nets:
            if len(cmp["pins"]) > 1 or cmp["names"]:
                errors.append(f"{stem}: unconnected contact {cmp['pins']} touches {sorted(cmp['names'])}")
            continue
        if not cmp["pins"] and not cmp["names"]:
            continue
        if len(nets) > 1 or len(cmp["names"]) != 1 or (nets and nets != cmp["names"]):
            errors.append(f"{stem}: drawn tree joins nets {sorted(nets)} under names {sorted(cmp['names'])} ({cmp['pins'][:6]})")
    if errors:
        raise ValueError("\n".join(errors[:40]))


def header(document_uuid, title, code, page_size="A2"):
    comments = " ".join(f"(comment {i} {q(v)})" for i, v in enumerate((code,) + TITLE_COMMENTS, 1))
    return f'''(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0")
 (uuid {document_uuid}) (paper {q(page_size)})
 (title_block (title {q(title)}) (date {q(DESIGN_DATE)}) (rev {q(REVISION)})
 (company {q(COMPANY)}) {comments})
'''


def check_glyphs(text_out, where):
    for ch, why in NO_GLYPH.items():
        if ch in text_out:
            raise ValueError(f"{where}: contains U+{ord(ch):04X} {why}")


def validate(graphs):
    refs, errors, nodes = {}, [], defaultdict(list)
    for g in graphs:
        for c in g["components"]:
            ref = c["ref"]
            if ref in refs:
                errors.append(f"duplicate reference {ref}: {refs[ref]} and {g['sheet']}")
            refs[ref] = g["sheet"]
            number = re.search(r"(\d+)$", ref)
            if not ref.startswith("#") and not (number and any(lo <= int(number.group(1)) <= hi for lo, hi in REF_RANGES.get(g["sheet"], ()))):
                errors.append(f"reference {ref} outside the {g['sheet']} range {REF_RANGES.get(g['sheet'])}")
            numbers = [str(p["number"]) for p in c["pins"]]
            if len(numbers) != len(set(numbers)):
                errors.append(f"duplicate physical contact in {ref}")
            for p in c["pins"]:
                if p.get("type", "passive") not in TYPES:
                    errors.append(f"invalid electrical type {ref}.{p['number']}")
                # place_component draws a no-connect marker and drops the label for either form.
                if (p.get("nc") or p.get("type") == "no_connect") and p.get("net"):
                    errors.append(f"NC/no_connect contact connected to a net: {ref}.{p['number']}")
                if p.get("net"):
                    nodes[p["net"]].append({"ref": ref, "pin": str(p["number"]), "sheet": g["sheet"], "type": p.get("type", "passive")})
    if errors:
        raise ValueError("\n".join(errors))
    return refs, nodes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design-dir", type=Path, default=BASE / "design")
    ap.add_argument("--output", type=Path, default=BASE / "build/kicad")
    args = ap.parse_args()
    graphs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(args.design_dir.glob("E[1-5].json"))]
    if not graphs:
        raise SystemExit("No reviewed E1..E5 design graphs found")
    # Explicit supply declarations only, after passive components or at documented
    # external supply boundaries. Never infer these from ERC failures.
    flag_nets = set()
    for graph in graphs:
        for i, entry in enumerate(graph.get("power_flags", []), 1):
            if entry["net"] in flag_nets:
                continue
            flag_nets.add(entry["net"])
            graph["components"].append({"ref": f"#FLG{graph['sheet'][1:]}{i:02d}", "value": "PWR_FLAG", "kind": "power_flag", "group": "Позначення фізичних джерел живлення (ERC)", "source": entry.get("source", ""), "description": entry.get("reason", ""), "status": "annotation", "pins": [{"number": "1", "name": "pwr", "type": "power_out", "net": entry["net"]}]})
    refs, nets = validate(graphs)
    ctx = Context(graphs)
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    pages = []
    all_syms = {}
    stats = Counter()
    counters = Counter()
    legend = ("Дроти з'єднують контакти всередині функціональної групи; кожне дерево дротів має одну глобальну мітку з канонічною назвою мережі "
              "(рамка-стрілка — мережа виходить за межі групи, пряма рамка — мережа лише цієї групи). Однакові мітки з'єднані на всіх аркушах; земля — символ GND. "
              "Рамки OPEN — незакриті ворота з design/E#.json (повний реєстр: OPEN_ITEMS.md); «TBD» у значенні — STACK номіналу не задає, показано стартове значення до стенду.")
    sparse = []
    for graph in graphs:
        sheet = graph["sheet"]
        layouts, note_chars = layout_sheet(route_groups(graph, ctx), sheet_notes(graph))
        if len(layouts) > 1 and page_fill(layouts[-1]) < SPARSE_LAST_PAGE:
            sparse.append(sheet + "_" + str(len(layouts)).zfill(2))
        for n, layout in enumerate(layouts, 1):
            stem = sheet if n == 1 else sheet + "_" + str(n).zfill(2)
            instance = uid("instance/" + stem)
            doc_uuid = uid("document/" + stem)
            path = "/" + ROOT_UUID + "/" + instance
            title = f"{sheet} - {graph['title']} ({n}/{len(layouts)})"
            used, body, page_stats = {}, [], Counter()
            checks = {"pins": [], "labels": [], "power": [], "wires": []}
            comps, notes_here, wraps = 0, [], {}
            for block, bx, by in layout:
                body.append(text(block.title, bx, by, f"{stem}/group/{block.group}/{block.part}", GROUP_SIZE))
                y = by + 2 * U
                for i, rd in enumerate(block.rows):
                    for note in rd.notes:
                        body.append(note_block(note, bx - U, y, stem + "/note/" + note["id"]))
                        notes_here.append(note["id"])
                        wraps[note["id"]] = note["chars"]
                        y += note["height"] + NOTE_GAP
                    ox = math.ceil((bx - rd.box[0]) / U - 1e-9)
                    oy = math.ceil((y - rd.box[1]) / U - 1e-9)
                    emit_row(rd, ox, oy, path, stem, counters, used, body, page_stats, checks)
                    comps += sum(1 for p in rd.row.parts)
                    y = (oy * U + rd.box[3]) + ROW_GAP_U * U
            check_page(stem, checks)
            all_syms.update(used)
            content = [header(doc_uuid, title, f"{COMPANY}-{sheet}"), "(lib_symbols", "\n".join(lib_symbol(used[k]) for k in sorted(used)), ")"]
            content += [text(title, 15.24, 15.24, stem + "/title", 2.032), text(legend, 15.24, 22.86, stem + "/legend", 1.016)]
            content += body
            content.append(")\n")
            sch = "\n".join(content)
            check_glyphs(sch, stem)
            (out / (stem + ".kicad_sch")).write_text(sch, encoding="utf-8", newline="\n")
            stats.update(page_stats)
            pages.append({"stem": stem, "instance": instance, "title": title, "components": comps, "sheet": sheet,
                          # the sheet's wrap cap; each note gets at most what its group's drawing is wide enough for
                          "notes": notes_here, "note_wrap_cap": note_chars, "note_wrap_chars": wraps, "fill": round(page_fill(layout), 3),
                          "drawing": dict(sorted(page_stats.items()))})
    placed = Counter(note for p in pages for note in p["notes"])
    declared = [x["id"] for g in graphs for x in g.get("open_items", []) + g.get("drawing_notes", [])]
    if sorted(placed.elements()) != sorted(declared):
        raise ValueError(f"notes not placed exactly once: placed={dict(placed)}, declared={declared}")
    (out / "sr_rx_v2_completed.kicad_sym").write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n' + "\n".join(lib_symbol(all_syms[k], embedded=False) for k in sorted(all_syms)) + "\n)\n", encoding="utf-8", newline="\n")
    # The overview indexes every actual electrical page, retaining E1..E5 naming.
    root = [header(ROOT_UUID, "SR-RX-v2 - зміст електричної схеми", f"{COMPANY} — зміст E1–E5", "A2"), "(lib_symbols)", text("SR-RX-v2: приймач і портативна радіолабораторія", 15.24, 15.24, "root/title", 3.048), text("Лише прийом в ефірі. Інженерна редакція від 4653188. Статус і незакриті ворота: ../../COMPLETION.md та ../../OPEN_ITEMS.md.", 15.24, 25.4, "root/status", 1.524)]
    for i, p in enumerate(pages):
        col, row = i % 4, i // 4
        x, y = 15.24 + col * 142.24, 43.18 + row * 38.1
        title = p["title"].split(" - ", 1)[-1]
        title = "\n".join(textwrap.wrap(title, width=45))
        root.append(f'''(sheet (at {fm(x)} {fm(y)}) (size 129.54 27.94)
 (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {p['instance']})
 {prop('Sheetname', p['stem'], x + 64.77, y + 4.445)}
 {prop('Sheetfile', p['stem'] + '.kicad_sch', x + 64.77, y + 20.32)}
 (instances (project "sr-rx-v2" (path {q('/' + ROOT_UUID)} (page {q(str(i + 2))})))))''')
        root.append(text(title, x + 5.08, y + 8.89, "root/index/" + p["stem"], 1.016))
    root.append('(sheet_instances (path "/" (page "1")))\n)\n')
    if math.ceil(len(pages) / 4) * 38.1 + 38.1 > 380:
        raise ValueError("Overview page overflow: split required")
    check_glyphs("\n".join(root), "sr-rx-v2")
    (out / "sr-rx-v2.kicad_sch").write_text("\n".join(root), encoding="utf-8", newline="\n")
    # A page that the current graphs no longer produce must not linger beside the live set.
    live = {p["stem"] + ".kicad_sch" for p in pages}
    for stale in out.glob("E*.kicad_sch"):
        if re.fullmatch(r"E[1-5](_\d\d)?\.kicad_sch", stale.name) and stale.name not in live:
            stale.unlink()
    # ... nor its SVG export from an earlier run (run_checks.py --export rewrites the live ones)
    for stale in (out / "svg").glob("sr-rx-v2-E*.svg"):
        m = re.fullmatch(r"sr-rx-v2-(E[1-5](_\d\d)?)\.svg", stale.name)
        if m and m.group(1) + ".kicad_sch" not in live:
            stale.unlink()
    table = '(sym_lib_table (version 7)\n'
    for name in ["sr_rx_v2_pwr", "sr_rx_v2_sig", "sr_rx_v2_completed"]:
        table += f' (lib (name "{name}")(type "KiCad")(uri "${{KIPRJMOD}}/{name}.kicad_sym")(options "")(descr "SR-RX-v2"))\n'
    (out / "sym-lib-table").write_text(table + ")\n", encoding="utf-8", newline="\n")
    project_file = out / "sr-rx-v2.kicad_pro"
    project = json.loads(project_file.read_text(encoding="utf-8")) if project_file.exists() else {}
    project.setdefault("meta", {}).update({"filename": "sr-rx-v2.kicad_pro", "version": 3})
    project["sheets"] = [[ROOT_UUID, "Root"]] + [[uid("document/" + p["stem"]), p["stem"]] for p in pages]
    project_file.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    physical_nets = {k: [v for v in vs if not v["ref"].startswith("#")] for k, vs in nets.items()}
    manifest = {"base_commit": "465318835e71eae326059f5f66e2b47232169556", "root_uuid": ROOT_UUID, "pages": pages, "components": sum(not r.startswith('#') for r in refs), "supply_annotations": len(flag_nets), "connected_contacts": sum(map(len, physical_nets.values())), "nets": len(nets), "drawing": dict(sorted(stats.items())), "sparse_last_pages": sparse, "single_contact_nets": {k: v for k, v in physical_nets.items() if len(v) == 1}, "open_items": [dict(item, sheet=g["sheet"]) for g in graphs for item in g.get("open_items", [])], "drawing_notes": [dict(item, sheet=g["sheet"]) for g in graphs for item in g.get("drawing_notes", [])], "title_block": {"date": DESIGN_DATE, "rev": REVISION, "comments": [COMPANY + "-E<n>", *TITLE_COMMENTS]}}
    manifest["source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.design_dir.glob("E[1-5].json"))}
    (out / "generation-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (out / "expected-netlist.json").write_text(json.dumps(physical_nets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in manifest.items() if k not in {"single_contact_nets", "open_items", "drawing_notes", "pages"}}, ensure_ascii=False))
    print(f"Electrical pages: {len(pages)}; explicit open items: {len(manifest['open_items'])}; drawing notes: {len(manifest['drawing_notes'])}; all placed on their pages")
    # Readability, not connectivity: the pages are written, run_checks.py refuses them.
    if sparse or stats["fallback_labels"]:
        print(f"WARNING: sparse last pages {sparse}; fallback labels {stats['fallback_labels']}", file=sys.stderr)


if __name__ == "__main__":
    main()
