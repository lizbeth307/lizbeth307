#!/usr/bin/env python3
"""PWR-A SHRINK-2 planner spec (W2 PCB-PWRA-3): the two-sided PWR-A of the SHRINK-2 decision, standard library.

  python3 build/kicad/boards/PWR_A/make_spec.py           write PWR_A.spec-shrink2.json next to this file
  python3 build/kicad/boards/PWR_A/make_spec.py --check   fail unless PWR_A.spec-shrink2.json reproduces

The repository port of the scratch builder of the SHRINK-2 re-check (orchestrator decision of 11.11.2026; scratch
evidence, never committed). It reads, and never writes, the design: nothing here edits design/E*.json or the budget.
Inputs:
  PWR_A.spec-draft.json (this directory)       base: layers, project, rules, anchors, groups, scripted copper
  design/E1-E5 (board_gen.load_graph)          refs, footprints, MPNs and pin nets of the graph of record
  pcb/generated/partition.json                 PWR-A domain refs (pcb/prepare.py; follows partition.domain_override_pwr_a)
  pcb/partition-spec.json candidates.shrink2   planned changes (blocks w/d, footprints), pwr_a_bottom, h_trim
  pcb/partition_budget.py Evaluator.planned    status of every planned change against the graph of now ('pending' while
                                               every ref still has the value it replaces, 'in graph' once GR-5A/GR-5B
                                               changed it; part 2: the status is read live, not from
                                               pcb/partition-budget.json, which is older than the graph until AREA-2b)
  pcb/boards/PWR_B.json, pcb/generated/b2b-nets.json   the J209 anchor and the J208 -> J209 contact map
  mechanical/generated/contract/boards.json    thermal_bond zones (MECH-7 zones 3'/4'), bottom_side pockets PB1-PB13 and
                                               h_max, converter_zone_refs, the bottom edge row_end_max

Rules (SHRINK-2 options: F102 holder kept, C506 to PWR-B, 12 V dampers radial):
- A 'pending' change with reserved blocks drops its refs and adds its blocks as reserved areas at BLOCK_AT (zones
  3'/4' at the old module squares, F103 in the top strip); a 'pending' deletion drops its refs; a 'pending' footprint
  swap keeps the ref and records the planned footprint in planned_footprints (placement_study.py uses its courtyard).
  An 'in graph' change counts the graph: its refs and the new graph refs go to the draft group of their schematic
  group (SCHEMATIC_GROUP; W2 PCB-PWRA-3 part 2: the real converter parts replaced the blocks).
- Part 2 (GR-5A, GR-5B and MECH-7 in the lane): the power stages are anchored (POWER_ANCHORS, design choice): U107 +
  L102 in contract zone 3', U108 in zone 4' (contract converter_zone_refs), their input and output capacitors, the
  reverse-polarity FET Q102, the shared bulk C107 and the LAB5 filter L101 at F102.2; the critical copper is scripted
  (POWER_POURS, POWER_VIAS: solid pad connection, at least the BATT single-layer width 3.2 mm or PWR3A 1.85 mm) and each
  F.Cu or B.Cu pour is a planner keep-out of its side (reserved area kind 'copper', not a courtyard demand). Review fixes
  F1/F2 of W2 PCB-PWRA-3: the LM61460 input per SNVSBD5D (CIN_HF and CIN on both VIN/PGND pairs, VIN strap on In2.Cu),
  the SYS12 trunk across the spine (spine bridged on In2) to the SYS12 node (F201, Q201) and the LAB5 trunk (B.Cu and
  F.Cu) from L101.2 to L205.1 and the J208 LAB5 contacts; POWER_TRUNKS names the pads each net's scripted copper must
  join by itself. Every top region gives way to the F.Cu copper and the power anchors, every pocket to the B.Cu copper
  (subtract_rect).
- Refs of the planned PWR-B set (budget pwr_b_refs) leave PWR-A; since GR-5B the domain of pcb/generated/partition.json
  already puts the six 5 V dampers and C506 on PWR-B.
- The chip refs of pwr_a_bottom.refs go on the bottom side, in one bottom group per top group, packed into the plate
  pockets PB1-PB13 of the contract (bottom_side.keep_in_mm; MECH-7: every bottom courtyard inside one pocket), the
  nearest pocket first; placement_study.py adds the top THT pin fields + tht_margin and the through vias as obstacles.
- The bottom row J105-J112 follows the MECH-7 contract (bottom edge row_end_max): J109-J112 turned by 90 degrees and the
  row compacted towards x 0 in its order, 0.5 mm apart (BOTTOM_ROW).
- J208 (LSHM-150, graph ref since W2 B2B) is anchored so that its pad n lies under J209 pad map(n) (b2b-nets.json
  contacts), the B2B2 placeholder of the draft leaves.
- J113/J114/J115/J507 take FFC_PLACES only if the S02 FFC is in the graph (a PWR-A part with a Connector_FFC-FPC
  footprint, GR-5B); otherwise their wip/w2-pwra1 places (PWRA1_PLACES).
- Groups and new refs that no designed region names go to group NEW_UNASSIGNED (all top regions): the study lists them.
MODEL / planning input only: not a board of record, nothing here is a hardware result; bench gates stay OPEN.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]  # sat-receiver-audit
sys.path.insert(0, str(BASE / 'pcb'))
import board_gen as bg  # noqa: E402
import partition_budget as pbud  # noqa: E402

DRAFT = HERE / 'PWR_A.spec-draft.json'
OUT = HERE / 'PWR_A.spec-shrink2.json'
PARTITION = BASE / 'pcb/generated/partition.json'
PSPEC = BASE / 'pcb/partition-spec.json'
BUDGET = BASE / 'pcb/partition-budget.json'
PWR_B_SPEC = BASE / 'pcb/boards/PWR_B.json'
B2B_NETS = BASE / 'pcb/generated/b2b-nets.json'
CONTRACT = BASE / 'mechanical/generated/contract/boards.json'
CANDIDATE = 'shrink2'
B2B_PAIR = ('J208', 'J209')
FFC_PREFIX = 'Connector_FFC-FPC:'

# Lower-left corner [x, y] (board mm) of each reserved block of a *pending* planned change on the PWR-A top: design choice
# of the SHRINK-2 study (converters in zones 3'/4' at the old module squares; RPP and the F201 fuse beside CONV_SYS12;
# F103 in the top strip of the band). Width and depth come from pcb/partition-spec.json candidates.shrink2.planned.
BLOCK_AT = {'CONV_SYS12': [8.0, 40.0], 'RPP': [8.0, 55.0], 'FUSE_F201': [16.0, 55.0], 'CONV_LAB5': [8.0, 74.0],
            'FUSE_F103': [81.0, 31.0]}
# wip/w2-pwra1 80d92c28 places of the right-edge headers (no FFC), and the FFC places of the SHRINK-2 decision.
PWRA1_PLACES = {'J113': ([117.7, 14.15], 90), 'J114': ([124.5, 4.13], 90), 'J115': ([124.5, 15.29], 90),
                'J507': ([117.7, 2.75], 90)}
FFC_PLACES = {'J113': ([102.0, 2.75], 90), 'J114': ([108.77, 4.13], 90), 'J115': ([116.04, 4.13], 90),
              'J507': ([122.54, 2.75], 90)}
# W2 PWRJ-F2C probe (fallback F2-C, wip/w2-pwrj-f2c): with pcb/partition-spec.json partition.domain_override_pwr_c set,
# the E1 front end, the E5 IMU service group and their headers are on PWR-C. Design choices of the probe:
# - J106 (W-C1 LAB5 feed, GND + LAB5) stands in the bottom row at the freed J108 slot (row_end_max 92.5 of the MECH-7
#   contract), below the LAB5 contacts of J208; J107 (W-C1 E1_SW feed) keeps its row place, so the scripted E1_SW rise stays.
# - The PWR-A parts that keep a PWR-B cut-out stay at their PCB-PWRA-4 places (placement-study-shrink2.json of
#   00fdc9e8, origins align 'origin'), so the PWR-B placement around the remaining cut-outs stays legal; the J21 and DISP
#   test points TP201/TP213/TP202/TP214 leave the PWR-B bar at x 42-50 (review of the PWRB-R PLACE probe: 12.8-17.4 mm
#   per layer for 47 crossing nets) for the probe windows of the E1 test points that moved to PWR-C (TP107, TP108,
#   TP104, TP105), which PWR-B already keeps free.
F2C_PLACES = {'J106': ([73.85, 3.5], 90)}
F2C_PINS = {
    'C206': (37.8, 97.65, 90), 'C207': (31.1, 82.55, 0), 'C210': (9.95, 97.0, 0), 'C222': (30.75, 48.9, 0),
    'C254': (29.05, 22.15, 90), 'C262': (23.15, 13.2, 90), 'C265': (93.5, 6.35, 90), 'C273': (2.45, 31.4, 0),
    'C511': (108.65, 8.25, 0), 'C512': (101.75, 7.6, 0), 'L501': (24.9, 93.9, 0),
    'TP101': (11.65, 40.95, 0), 'TP102': (5.5, 100.95, 90), 'TP203': (11.51, 69.35, 90), 'TP204': (40.05, 43.75, 0),
    'TP205': (61.85, 11.45, 0), 'TP211': (4.01, 16.05, 90), 'TP212': (90.25, 33.55, 0), 'TP215': (7.01, 16.05, 90),
    'C219': (3.2, 51.35, 90), 'TP2903': (93.25, 33.55, 0), 'U216': (117.95, 22.05, 0), 'L203': (3.29, 43.81, 0),
    'TP201': (18.85, 74.93, 0),  # the TP107 slot
    'TP213': (21.85, 74.93, 0),  # the TP108 slot
    'TP202': (22.75, 54.15, 90),  # the TP104 slot
    'TP214': (19.45, 44.6, 90),  # the TP105 slot
}
GAP = 0.5  # mm, region edge to a fixed courtyard (the planner gap)
EDGE_INSET = 0.3  # mm, a planner region keeps this off the board outline (the draft regions start at 0.3)

# --- W2 PCB-PWRA-3 part 2: power stages and their scripted copper (design choice; board mm, y up, top side) ---
# Anchors of the power stages once their planned changes are in the graph: ref -> (x, y, rotation). U107 (LM61460, SW
# up) under L102 pad 1 (SRP1040VA on the SRP1038C land, pads vertical) in zone 3' [7, 39, 24, 63]; the output capacitors
# C123-C125 left of L102 and C126 right of it, pad 1 up in the SYS12 bar at L102 pad 2; U108 (TPSM63606, VIN up, VOUT
# down) in zone 4' [7, 73, 21, 87] with C130/C131 above it (pad 1 down in the E1_CONV_IN bar) and C133-C135 below it (pad 1
# up in the E1_LAB5_RAW bar towards F102.1); Q102 (DMT6007 of the LM74700 stage) at the foot of the E1_CONV_IN spine; C107
# (shared input bulk) between the zones; L101 (LAB5 filter) above F102.2.
# Review fix F1 (W2 PCB-PWRA-3): the LM61460 input as SNVSBD5D section 11 lays it out (read 2026-11-12, see
# POWER_FIX_SOURCE): one VIN/PGND pin pair per side, each with its high-frequency capacitor next to the pins (C122 at
# VIN2/PGND2 left, C121 at VIN1/PGND1 right; their schematic notes say so) and its bulk capacitor beyond it (C119 left,
# C120 right), pad 1 (E1_CONV_IN) at the VIN level and pad 2 (GND) at the PGND level; the two sides are joined by a VIN
# strap on an inner layer ("Use a wide VIN plane on a lower layer to connect both of the VIN pairs together", figure 11-2
# "VIN Strap on Inner Layer"): In2.Cu here, In1.Cu stays the solid GND plane under the IC.
# Review fix F2: C111 (E1_LAB5_FUSED input capacitor of the LAB5 filter) at the F102.2/L101.1 node, C112 (LAB5 output bulk)
# and F104 (LAB5_RLY PTC) at L101.2, L205 (LAB5 -> E2_LNA_IN filter of the LT3045 pair) left of U204 under the LAB5 trunk;
# two SYS12 branch heads at the SYS12 node right of the spine: F201 (J21 fuse) above, Q201 (AUX12 switch) below; the
# display filter L202 does not fit there (C113, R110 and the hole keep-out at (38, 56)) and stays with its group.
POWER_ANCHORS = {
    'U107': (16.0, 46.5, 90), 'L102': (16.0, 56.0, 90),
    'C119': (9.15, 48.2, 90), 'C122': (13.07, 47.525, 90), 'C121': (18.93, 47.525, 90), 'C120': (22.85, 48.2, 90),
    'C123': (2.0, 59.0, 270), 'C124': (5.4, 59.0, 270), 'C125': (8.8, 59.0, 270), 'C126': (22.95, 59.0, 270),
    'Q102': (26.5, 38.6, 90), 'C107': (19.0, 67.15, 180),
    'U108': (14.0, 80.0, 0), 'C130': (11.2, 86.475, 90), 'C131': (16.8, 86.475, 90),
    'C133': (9.2, 73.725, 270), 'C134': (12.6, 73.725, 270), 'C135': (16.0, 73.725, 270),
    'L101': (4.0, 88.0, 90), 'C111': (9.3, 80.05, 90), 'C112': (5.85, 94.9, 90), 'F104': (2.25, 99.25, 90),
    'L205': (39.91, 23.41, 270),
    'F201': (30.43, 64.9, 90), 'Q201': (30.53, 56.6, 180),
}
POWER_ANCHOR_CHANGES = ('U107-SYS12', 'RPP-SYS12', 'U108-LAB5')  # anchors apply once these are in the graph
BATT_W = 3.2  # mm, netclasses.json BATT outer_min_width_mm (single layer)
POWER_FIX_SOURCE = ('TI LM61460 data sheet SNVSBD5D (rev. D, July 2022) section 11.1 Layout Guidelines and figure 11-2 '
                    'Layout Example, https://www.ti.com/lit/ds/symlink/lm61460.pdf read 2026-11-12 (curl default '
                    'User-Agent, HTTP 200, sha256 2c8a0bf340c70aa3ac29e586146804d7651822e14bee0897f6415ee9e56be84d; '
                    'fetch-only, not committed)')


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def pour(net, outline, why, pin_entry=None, layer='F.Cu', branch=False):
    # branch: the pour feeds a side part (a capacitor, a PTC) and is not in the series path of its net (lab5_budget.py)
    return {'net': net, 'outline': outline, 'why': why, 'pin_entry': pin_entry, 'layer': layer, 'branch': branch}


# Scripted pours, priority 2, solid pad connection (W2 PCB-PWRA-2 probes 2-4: thermal spokes gave a 1.03 mm neck): id ->
# pour(net, outline, why[, pin_entry][, layer]). An F.Cu or B.Cu outline is a planner keep-out of its side (reserved area
# kind 'copper'); an In2.Cu outline is not (inner copper, no part can touch it). A pin_entry stem (a pour narrower than its
# class onto a fine pin) lies wholly within half the class width of those pins, where pcb/check_boards.py does not measure
# a pour neck; different-net pours on one layer keep >= 0.3 mm (placement_study POUR_GAP). B.Cu copper stays outside the
# thermal_bond zones (their L4 GND bond copper) by >= 0.3 mm; non-GND vias stay outside them too.
POWER_POURS = {
    'E1SW-RISE': pour('E1_SW', rect(15.85, 1.8, 19.45, 36.0),
                      'BATT 3.6 mm: J107.2 (battery feed after the main switch) up past U211 to the leg'),
    'E1SW-BAR': pour('E1_SW', rect(15.85, 32.8, 28.4, 36.0), 'BATT 3.2 mm: across to the source pins of Q102'),
    'E1SW-Q102': pour('E1_SW', rect(25.3, 36.0, 27.05, 37.45),
                      'stem onto Q102 S1-S3 (pins 0.42 mm, gate pad 0.215 mm away): within half the class width of the pins',
                      ['Q102.1', 'Q102.2', 'Q102.3']),
    'CONVIN-SPINE': pour('E1_CONV_IN', rect(24.8, 38.2, 28.2, 58.4),
                         '3.4 mm: Q102 drain (after the LM74700 stage) up the leg to U107 and to the SYS12 crossing (E1_CONV_IN '
                         'has no NET_CURRENT entry yet: scripted at the BATT width of E1_SW, W2 GR-5A review GR5A-03)'),
    'CONVIN-SPINE-UP': pour('E1_CONV_IN', rect(24.8, 62.55, 28.2, 86.6),
                            '3.4 mm: from the In2 bridge over the SYS12 crossing up to C107 and U108 (review fix F2)'),
    'CONVIN-BRIDGE': pour('E1_CONV_IN', rect(24.8, 55.4, 28.2, 65.55),
                          'In2.Cu 3.4 mm: the spine under the F.Cu SYS12 crossing (U108 input, about 1.2 A at 3.2 A LAB5: '
                          'MODEL), three vias on each side (review fix F2)', layer='In2.Cu'),
    'CONVIN-U107-R': pour('E1_CONV_IN', rect(21.5, 43.9, 28.2, 47.2),
                          '3.3 mm: spine to C120.1 (CIN1) (review fix F1)'),
    'CONVIN-U107-R-BAR': pour('E1_CONV_IN', rect(18.455, 46.15, 21.7, 47.2),
                              'C120.1 to C121.1 (CIN_HF1) along the VIN1 level, within half the class width of the two pads; '
                              'the RT/EN pins 6/7 escape below it (review fix F1)', ['C121.1', 'C120.1']),
    'CONVIN-U107-VIN1': pour('E1_CONV_IN', rect(17.55, 46.75, 18.7, 47.15),
                             'onto U107 VIN1 (pin 8, 1.0 x 0.4 mm) from C121.1 (review fix F1)', ['U107.8']),
    'CONVIN-U107-L': pour('E1_CONV_IN', rect(7.2, 38.1, 10.4, 47.2),
                          '3.2 mm: C119.1 (CIN2) down to the In2 strap vias below thermal_bond zone 3\' (review fix F1)'),
    'CONVIN-U107-L-BAR': pour('E1_CONV_IN', rect(10.2, 46.15, 13.545, 47.2),
                              'C119.1 to C122.1 (CIN_HF2) along the VIN2 level, within half the class width of the two pads; '
                              'the CBOOT/RBOOT pins 13/14 escape below it (review fix F1)', ['C119.1', 'C122.1']),
    'CONVIN-U107-VIN2': pour('E1_CONV_IN', rect(13.3, 46.75, 14.45, 47.15),
                             'onto U107 VIN2 (pin 12, 1.0 x 0.4 mm) from C122.1 (review fix F1)', ['U107.12']),
    'CONVIN-STRAP': pour('E1_CONV_IN', rect(7.2, 43.9, 28.2, 46.75),
                         'In2.Cu 2.85 mm VIN strap under U107: VIN2/CIN2 side to the spine (SNVSBD5D figure 11-2; review fix '
                         'F1)', layer='In2.Cu'),
    'CONVIN-STRAP-L': pour('E1_CONV_IN', rect(7.2, 38.1, 10.4, 46.75),
                           'In2.Cu 3.2 mm: the VIN strap down to its left vias below thermal_bond zone 3\' (non-GND vias stay '
                           'outside the bond zones; review fix F1)', layer='In2.Cu'),
    'CONVIN-C107': pour('E1_CONV_IN', rect(19.95, 65.55, 28.2, 68.75), '3.2 mm: spine to the shared bulk C107.1'),
    'CONVIN-U108': pour('E1_CONV_IN', rect(9.85, 83.4, 28.2, 86.6), '3.2 mm: spine to C130.1/C131.1 above U108'),
    'CONVIN-U108-VIN1': pour('E1_CONV_IN', rect(11.3, 81.9, 12.7, 83.4), 'onto U108 VIN1 (pad 1.4 mm)', ['U108.1']),
    'CONVIN-U108-VIN2': pour('E1_CONV_IN', rect(15.3, 81.9, 16.7, 83.4), 'onto U108 VIN2 (pad 1.4 mm)', ['U108.16']),
    'SYS12SW-PIN': pour('E1_SYS12_SW', rect(15.65, 46.3, 16.35, 49.3),
                        'over U107 SW (0.4 mm pin between the PGND pins): within half the class width of the pin', ['U107.10']),
    'SYS12SW-L102': pour('E1_SYS12_SW', rect(14.25, 49.3, 17.75, 53.3),
                         'BATT 3.5 mm: U107 SW to L102.1 (minimal SW copper)'),
    'SYS12-BAR': pour('SYS12', rect(0.6, 58.7, 24.5, 62.25), 'BATT 3.55 mm: L102.2 over the pads 1 of C123-C126'),
    'SYS12-CROSS': pour('SYS12', rect(24.0, 58.7, 32.6, 62.25),
                        'BATT 3.55 mm: across the spine gap (the spine runs on In2 there) to the SYS12 node right of the '
                        'spine: F201.1 (J21) and Q201.2 (AUX12) (review fix F2)'),
    'SYS12-Q201': pour('SYS12', rect(30.73, 57.5, 32.205, 58.9), 'onto Q201.2 (source) from the SYS12 node (review fix F2)',
                       ['Q201.2']),
    'LAB5RAW-F102': pour('E1_LAB5_RAW', rect(0.6, 67.6, 7.4, 76.8), 'BATT 6.8 mm: onto both THT pads of F102.1'),
    'LAB5RAW-BAR': pour('E1_LAB5_RAW', rect(0.6, 73.6, 17.6, 76.8), 'BATT 3.2 mm: U108 VOUT over C133-C135 to F102.1'),
    'LAB5RAW-VOUT1': pour('E1_LAB5_RAW', rect(11.3, 76.8, 12.7, 78.1), 'onto U108 VOUT1 (pad 1.4 mm)', ['U108.8']),
    'LAB5RAW-VOUT2': pour('E1_LAB5_RAW', rect(15.3, 76.8, 16.7, 78.1), 'onto U108 VOUT2 (pad 1.4 mm)', ['U108.9']),
    'LAB5FUSED': pour('E1_LAB5_FUSED', rect(0.6, 77.5, 7.4, 87.6), 'PWR3A 6.8 mm: F102.2 (both THT pads) to L101.1'),
    'LAB5FUSED-C111': pour('E1_LAB5_FUSED', rect(7.1, 77.4, 10.65, 79.4),
                           'PWR3A 2.0 mm: onto C111.1 at the F102.2/L101.1 node (review fix F2)', branch=True),
    'LAB5-L101': pour('LAB5', rect(0.6, 89.0, 7.4, 94.0),
                      'PWR3A 5.0 mm: L101.2 (the E1 LAB5 end) and C112.1, six vias to the B.Cu trunk (review fix F2)'),
    'LAB5-F104': pour('LAB5', rect(0.6, 93.6, 3.95, 97.675), 'PWR3A 3.35 mm: onto F104.1 (LAB5_RLY PTC) (review fix F2)',
                      branch=True),
    'LAB5-B-TOP': pour('LAB5', rect(0.6, 90.4, 26.5, 92.6),
                       'B.Cu PWR3A 2.2 mm: the LAB5 trunk from L101.2 across the leg above thermal_bond zone 4\' (review fix '
                       'F2)', layer='B.Cu'),
    'LAB5-B-SPINE': pour('LAB5', rect(24.3, 27.3, 26.5, 92.6),
                         'B.Cu PWR3A 2.2 mm: the LAB5 trunk down the leg under the F.Cu E1_CONV_IN spine, between zones '
                         '3\'/4\' and the right column (review fix F2)', layer='B.Cu'),
    'LAB5-B-BAND': pour('LAB5', rect(24.3, 27.3, 42.2, 29.5),
                        'B.Cu PWR3A 2.2 mm: along the band above thermal_bond zone 1 up to the hole at (46, 31) (review fix '
                        'F2)', layer='B.Cu'),
    'LAB5-RISE-L': pour('LAB5', rect(39.5, 25.0, 42.2, 29.5), 'PWR3A 2.7 mm: six vias up from the B.Cu trunk (review fix F2)'),
    'LAB5-DETOUR': pour('LAB5', rect(39.5, 25.0, 50.4, 27.2),
                        'PWR3A 2.2 mm: L205.1 (the LT3045 feed) and below the hole keep-out at (46, 31) (review fix F2)'),
    'LAB5-RISE-R': pour('LAB5', rect(49.5, 26.6, 52.4, 29.5), 'PWR3A 2.9 mm: six vias down to the B.Cu trunk (review fix F2)'),
    'LAB5-B-BAND-R': pour('LAB5', rect(49.5, 27.3, 82.8, 29.5),
                          'B.Cu PWR3A 2.2 mm: along the band above thermal_bond zones 1/2 to the J208 drop (review fix F2)',
                          layer='B.Cu'),
    'LAB5-DROP': pour('LAB5', rect(80.4, 13.4, 82.8, 29.5),
                      'PWR3A 2.4 mm: six vias up from the B.Cu trunk, down left of J208 (review fix F2)'),
    'LAB5-J208-BAR': pour('LAB5', rect(80.4, 13.4, 89.9, 15.5),
                          'PWR3A 2.1 mm: under the J208 bottom row to its four LAB5 contacts (path B to PWR-B; review fix F2)'),
    'LAB5-J208-2': pour('LAB5', rect(86.4, 15.3, 86.7, 16.4), 'onto J208.2 between the GND contacts', ['J208.2']),
    'LAB5-J208-6': pour('LAB5', rect(87.4, 15.3, 87.7, 16.4), 'onto J208.6 between the GND contacts', ['J208.6']),
    'LAB5-J208-10': pour('LAB5', rect(88.4, 15.3, 88.7, 16.4), 'onto J208.10 between the GND contacts', ['J208.10']),
    'LAB5-J208-14': pour('LAB5', rect(89.4, 15.3, 89.7, 16.4), 'onto J208.14 between the GND contacts', ['J208.14']),
    'GND-U107-L': pour('GND', rect(7.55, 47.5, 15.05, 49.0),
                       'U107 PGND2 to C122.2 and C119.2 and two vias to In1/In2/L4 (zone 3\'; review fix F1)'),
    'GND-C119': pour('GND', rect(7.55, 49.0, 10.75, 50.5), 'C119.2 (review fix F1)'),
    'GND-U107-R': pour('GND', rect(16.95, 47.5, 24.45, 49.0),
                       'U107 PGND1 to C121.2 and C120.2 and two vias to In1/In2/L4 (zone 3\'; review fix F1)'),
    'GND-C120': pour('GND', rect(21.25, 49.0, 24.45, 50.5), 'C120.2 (review fix F1)'),
    'GND-COUT-SYS12': pour('GND', rect(0.6, 55.6, 10.55, 58.15), 'pads 2 of C123-C125 and their vias'),
    'GND-COUT-C126': pour('GND', rect(21.6, 55.6, 24.3, 58.15), 'pad 2 of C126 and its via'),
    'GND-COUT-LAB5': pour('GND', rect(7.85, 70.75, 17.35, 72.9), 'pads 2 of C133-C135 and their vias'),
    'GND-CIN-U108': pour('GND', rect(9.85, 87.3, 18.15, 89.9), 'pads 2 of C130/C131 and their vias'),
    'GND-C111': pour('GND', rect(7.95, 80.95, 10.65, 83.05), 'C111.2 and its via (zone 4\'; review fix F2)'),
}
# Vias of the power stages, 0.6/0.3 like the TPS7A4701 EP vias: id -> (x, y[, net]); GND unless a net is given. GND: to the
# In1/In2 GND planes and the L4 bond copper of zones 3'/4' (heat to the plate). U108: one via in each PGND pad 17-20 (TI
# RDL0020A land pattern 4226416/B note 5: optional 0.2 mm vias in pads 17-20, recorded in tools/make_footprints.py
# rdl0020a(), W2 GR-5A; here the project via 0.6/0.3 in the 0.875 mm pad; via in pad: filled or plugged vias are an order
# option, OPEN). E1_CONV_IN: the In2 strap and bridge (review fix F1/F2). LAB5: F.Cu <-> B.Cu trunk transitions, six each
# (PWR3A vias_per_transition 5, advisory; review fix F2).
POWER_VIAS = {
    'U107-PGND-L1': (8.3, 48.2), 'U107-PGND-L2': (9.3, 48.2), 'U107-PGND-R1': (22.7, 48.2), 'U107-PGND-R2': (23.7, 48.2),
    'COUT-SYS12-1': (2.0, 56.1), 'COUT-SYS12-2': (5.4, 56.1), 'COUT-SYS12-3': (8.8, 56.1), 'COUT-C126': (22.95, 56.1),
    'COUT-LAB5-1': (9.2, 71.1), 'COUT-LAB5-2': (12.6, 71.1), 'COUT-LAB5-3': (16.0, 71.1),
    'CIN-U108-1': (11.2, 89.4), 'CIN-U108-2': (16.8, 89.4),
    'U108-PGND-17': (14.0, 81.6125), 'U108-PGND-18': (14.0, 80.5375), 'U108-PGND-19': (14.0, 79.4625),
    'U108-PGND-20': (14.0, 78.3875),
    'C111-GND': (9.3, 82.55),
    'STRAP-L1': (7.7, 38.4, 'E1_CONV_IN'), 'STRAP-L2': (8.65, 38.4, 'E1_CONV_IN'), 'STRAP-L3': (9.6, 38.4, 'E1_CONV_IN'),
    'STRAP-R1': (27.5, 44.4, 'E1_CONV_IN'), 'STRAP-R2': (27.5, 45.35, 'E1_CONV_IN'), 'STRAP-R3': (27.5, 46.3, 'E1_CONV_IN'),
    'BRIDGE-LO1': (27.5, 55.9, 'E1_CONV_IN'), 'BRIDGE-LO2': (27.5, 56.8, 'E1_CONV_IN'), 'BRIDGE-LO3': (27.5, 57.7, 'E1_CONV_IN'),
    'BRIDGE-UP1': (27.5, 63.25, 'E1_CONV_IN'), 'BRIDGE-UP2': (27.5, 64.15, 'E1_CONV_IN'),
    'BRIDGE-UP3': (27.5, 65.05, 'E1_CONV_IN'),
    **{f'LAB5-L101-{i + 1}': (1.3 + i, 91.75, 'LAB5') for i in range(6)},
    **{f'LAB5-RL-{i * 2 + j + 1}': (x, y, 'LAB5') for i, x in enumerate((39.9, 40.85, 41.8)) for j, y in enumerate((27.95, 28.95))},
    **{f'LAB5-RR-{i * 2 + j + 1}': (x, y, 'LAB5') for i, x in enumerate((50.0, 50.95, 51.9)) for j, y in enumerate((27.95, 28.95))},
    **{f'LAB5-DROP-{i * 2 + j + 1}': (x, y, 'LAB5') for i, x in enumerate((80.8, 81.6, 82.4)) for j, y in enumerate((27.95, 28.95))},
}
# Design data for the corridor pre-check of placement_study.py: pads of a BATT/PWR3A net that carry no power current
# (bias, feedback sense, gate pull-up), checked at the project default track width instead of the class width (the
# PWR_BRANCH* idea of pcb/generated/netclasses.json rule_areas; review fix F2).
POWER_BRANCH_PADS = {
    'SYS12': {'pads': ['U107.1', 'R124.1', 'C129.1', 'R221.1'],
              'why': 'U107 BIAS, the feedback divider top R124, the CFF C129 and the Q201 gate pull-up R221 (mA)'},
    'E1_CONV_IN': {'pads': ['R108.1'], 'why': 'top of the U107 EN divider R108 (uA)'},
    'E1_SYS12_SW': {'pads': ['C127.2'], 'why': 'the CBOOT capacitor C127 (gate-drive charge only)'},
}
# Pads that the scripted copper of each net joins by itself (placement_study.py scripted_copper_precheck.trunks checks
# it; review fixes F1/F2): the power path of every scripted net, end to end.
POWER_TRUNKS = {
    'E1_SW': ['J107.2', 'Q102.1', 'Q102.2', 'Q102.3'],
    'E1_CONV_IN': ['Q102.5', 'U107.8', 'U107.12', 'C119.1', 'C120.1', 'C121.1', 'C122.1', 'C107.1', 'C130.1', 'C131.1',
                   'U108.1', 'U108.16'],
    'E1_SYS12_SW': ['U107.10', 'L102.1'],
    'SYS12': ['L102.2', 'C123.1', 'C124.1', 'C125.1', 'C126.1', 'F201.1', 'Q201.2'],
    'E1_LAB5_RAW': ['U108.8', 'U108.9', 'C133.1', 'C134.1', 'C135.1', 'F102.1'],
    'E1_LAB5_FUSED': ['F102.2', 'C111.1', 'L101.1'],
    'LAB5': ['L101.2', 'C112.1', 'F104.1', 'L205.1', 'J208.2', 'J208.6', 'J208.10', 'J208.14'],
}

# Bottom row of the PWR-A bottom edge (MECH-7 contract edge_zones[0] row_end_max): the headers in their order along the
# edge; turned ones rotate by 90 degrees. Design choice (part 2): the PH headers J109, J111 and J112 turn; the 5-pin J110
# stays along the edge (turned it would reach 12.9 mm into bond zone 1 and deepen the PWR-B edge strip to 13.4 mm), and the
# row still ends inside the MECH-7 row_end_max (bottom_row.end_x_with_margin of the spec).
BOTTOM_ROW = ['J107', 'J111', 'J105', 'J109', 'J106', 'J110', 'J108', 'J112']
BOTTOM_ROW_TURNED = ['J109', 'J111', 'J112']
BOTTOM_ROW_START = 8.2  # x of the first courtyard (right of the H1 keepout), the draft value

# Top regions of the SHRINK-2 layout (free rectangles after the anchors, J208, the scripted copper and the hole keepouts;
# design choice). The band keeps the draft regions, re-cut around the E1_SW rise and the turned bottom row; the leg is
# re-cut around the power stages of part 2 (zones 3'/4', the E1_CONV_IN spine, the SYS12 and E1_LAB5_RAW bars).
TOP_REGIONS = {
    'BAND_LEFT': [0.3, 9.8, 9.3, 26.8], 'BAND_U211_LOW': [9.6, 7.0, 15.5, 13.3], 'BAND_U211_UP': [9.6, 19.8, 15.5, 26.8],
    'BAND_LNB': [19.75, 7.5, 42.6, 26.8],
    'BAND_LT_LOW': [43.0, 7.5, 49.4, 11.4], 'BAND_LT_HIGH': [43.0, 22.4, 49.4, 26.8],
    'BAND_LNA': [49.6, 7.0, 72.3, 26.4], 'BAND_BONI': [78.8, 11.2, 82.95, 26.4], 'BAND_U213_UP': [72.6, 19.8, 80.1, 26.4],
    'BAND_B2B_BELOW': [83.45, 11.2, 115.2, 14.9], 'BAND_B2B_ABOVE': [83.45, 22.1, 107.8, 26.4],
    'BAND_B2B_ABOVE_R': [107.9, 22.1, 115.0, 24.5],
    'BAND_BOTTOM_M': [90.1, 0.3, 99.3, 11.0], 'BAND_BOTTOM_R': [99.6, 0.3, 115.2, 11.0],
    'BAND_COL3_TOP': [115.5, 19.1, 121.0, 24.5], 'BAND_COL2_TOP': [121.53, 22.6, 128.3, 24.5],
    'BAND_TOP_LEFT': [0.3, 27.0, 15.5, 34.8], 'BAND_TOP_LEFT_R': [19.75, 27.0, 42.2, 32.5],
    'BAND_TOP_LEFT_R2': [28.7, 32.5, 42.2, 34.8],
    'BAND_TOP_MID': [50.0, 26.9, 66.0, 30.8], 'BAND_TOP_MID2': [89.0, 30.9, 107.8, 34.8],
    'BAND_TOP_MID3': [50.0, 30.9, 66.0, 34.8], 'BAND_TOP_MID4': [66.3, 26.9, 80.1, 34.8],
    'BAND_TOP_MID_R': [83.1, 26.9, 107.8, 30.8],
    'LEG_LEFT_LOW': [0.3, 35.2, 8.1, 55.3], 'LEG_SYS12_LOW': [8.4, 36.3, 24.3, 42.2], 'LEG_ENTRY': [8.4, 35.2, 15.5, 36.2],
    'LEG_Z3_L': [8.3, 49.5, 10.5, 55.3], 'LEG_Z3_R': [21.5, 49.5, 24.55, 55.4],
    'LEG_U107_L': [10.7, 42.3, 13.8, 45.85], 'LEG_U107_R': [18.2, 42.3, 21.2, 45.85],
    'LEG_MID_L': [0.3, 62.5, 7.5, 65.8], 'LEG_MID': [7.8, 62.5, 14.0, 70.6],
    'LEG_Z4_L': [7.8, 77.0, 10.85, 83.2], 'LEG_Z4_R': [17.6, 71.0, 24.5, 83.1],
    'LEG_RPP': [28.6, 35.2, 34.2, 41.2], 'LEG_RIGHT_LOW2': [34.4, 35.2, 41.8, 41.2],
    'LEG_RIGHT_LOW': [28.6, 41.4, 41.8, 52.3], 'LEG_SPINE_R': [28.6, 52.5, 34.2, 77.6],
    'LEG_RIGHT_MID': [28.6, 77.8, 41.8, 86.8], 'LEG_RIGHT_HIGH': [34.4, 87.0, 41.8, 102.3],
    'LEG_HFL': [18.4, 87.0, 34.2, 100.4], 'LEG_Z4_TOP': [7.8, 90.2, 18.2, 100.4],
    'LEG_LEFT_HIGH': [0.3, 91.8, 7.75, 102.2],
    'LEG_TOP': [7.8, 100.6, 34.3, 102.8], 'LEG_TOP_L': [7.8, 102.8, 15.3, 109.7], 'LEG_TOP_R': [26.5, 102.8, 34.3, 109.7],
}
# With the FFC the right column is free (J113/J114/J115/J507 on the bottom edge): the SHRINK-2 study region.
FFC_REGIONS = {'drop': ['BAND_BOTTOM_R', 'BAND_COL3_TOP', 'BAND_COL2_TOP'],
               'add': {'BAND_RIGHT_COL': [114.65, 11.5, 128.6, 24.8]}}
# Top group -> (region, alt_regions); groups run in this order (HFP first: L501 needs the leg slot). Part 2: the power-stage
# groups first (their regions are theirs alone), then the band's E2 low-noise groups (LNB, LNA4V5, Boni), then the
# SYS12-fed groups: J21 above and AUX12 below the SYS12 node right of the spine (review fix F2: F201 and Q201 sit at the
# node), DISP and LIME, then the E1 control groups.
TOP_GROUPS = [
    ('HFP', 'LEG_HFL', ['BAND_BOTTOM_R', 'BAND_BOTTOM_M']),
    ('RPP', 'LEG_RPP', ['LEG_RIGHT_LOW2', 'LEG_SYS12_LOW']),
    ('SYS12', 'LEG_SYS12_LOW', ['LEG_U107_L', 'LEG_U107_R', 'LEG_Z3_R', 'LEG_Z3_L', 'LEG_ENTRY']),
    ('LAB5_CTRL', 'LEG_Z4_R', ['LEG_Z4_L']),
    ('LNA4V5', 'BAND_LNA', ['BAND_LT_LOW', 'BAND_LT_HIGH']),
    ('LNB', 'BAND_LNB', ['BAND_U211_UP', 'BAND_U211_LOW', 'BAND_LEFT']),
    ('BONI', 'BAND_B2B_BELOW', ['BAND_U213_UP', 'BAND_BONI', 'BAND_B2B_ABOVE', 'BAND_BOTTOM_M', 'BAND_TOP_MID2',
                                'BAND_B2B_ABOVE_R']),
    ('J21', 'LEG_RIGHT_MID', ['LEG_RIGHT_HIGH', 'LEG_SPINE_R', 'LEG_RIGHT_LOW2']),
    ('AUX12', 'LEG_RIGHT_LOW', ['LEG_RIGHT_LOW2', 'BAND_TOP_MID3', 'BAND_TOP_LEFT']),
    ('E1_SERVICE', 'LEG_TOP_R', ['BAND_TOP_MID3', 'BAND_TOP_MID']),
    ('DISP', 'LEG_Z4_TOP', ['LEG_TOP', 'LEG_TOP_L', 'LEG_TOP_R']),
    ('LIME', 'LEG_LEFT_LOW', ['LEG_MID_L', 'LEG_MID']),
    ('LAB5', 'LEG_LEFT_HIGH', ['LEG_Z4_L', 'LEG_MID_L']),
    ('INA3221_2', 'LEG_RIGHT_HIGH', ['LEG_SPINE_R']),
    ('E5_SERVICE', 'LEG_MID', ['LEG_RIGHT_HIGH', 'LEG_MID_L']),
    ('E1_CTRL', 'BAND_TOP_LEFT_R', ['BAND_TOP_MID4', 'BAND_TOP_LEFT', 'BAND_TOP_LEFT_R2', 'BAND_TOP_MID3']),
    ('E1_USBPD', 'BAND_LEFT', ['BAND_TOP_LEFT']),

    ('E5_RTLA_LAB', 'LEG_RIGHT_HIGH', ['BAND_TOP_MID']),
    ('PWRB_RADIALS', 'LEG_TOP_L', ['LEG_TOP_R', 'LEG_TOP']),
]
# Part 2 (design choice): groups split out of their schematic group so that they sit at their stage: the LM74700 stage
# with the E1_SW bypasses beside Q102 (right of the spine foot), and the U108 feedback, RT and EN parts at U108's
# small-signal pins. Review fix F1: the U107 small-signal parts (SYS12 group: CBOOT/RBOOT, RT, FB, VCC) also get the
# pockets left and right of U107 below the VIN levels (LEG_U107_L/R), where the pins 13/14 and 6/7 escape.
SPLIT_GROUPS = {'RPP': ['U111', 'C136', 'C108', 'C110'], 'LAB5_CTRL': ['C132', 'R129', 'R130', 'R131', 'R132', 'R133']}
# Schematic group (sheet, group) -> draft group of a new graph ref (since the draft): GR-5A put the converter parts
# into E1 'SYS12' and 'LAB5' (the RPP stage U111/Q102/C136 is in 'SYS12').
SCHEMATIC_GROUP = {('E1', 'SYS12'): 'SYS12', ('E1', 'LAB5'): 'LAB5'}
TURN_WHATIF = ['J109', 'J110', 'J111', 'J112']  # PH headers turned by 90 degrees: bottom-edge need and PWR-B strip depth


def r4(v):
    return bg.r4(v)


def subtract_rect(reg, cut, keep_min=1.0):
    """reg minus cut as up to four rectangles (left, right, below, above; review fix F2), each at least keep_min mm wide
    and deep, the largest first; reg itself when they do not overlap."""
    if not bg.rects_overlap(reg, cut):
        return [reg]
    x0, y0, x1, y1 = reg
    pieces = [[x0, y0, cut[0], y1], [cut[2], y0, x1, y1], [max(x0, cut[0]), y0, min(x1, cut[2]), cut[1]],
              [max(x0, cut[0]), cut[3], min(x1, cut[2]), y1]]
    pieces = [q for q in pieces if q[2] - q[0] >= keep_min - 1e-9 and q[3] - q[1] >= keep_min - 1e-9]
    return [[r4(v) for v in q] for q in sorted(pieces, key=lambda q: -round((q[2] - q[0]) * (q[3] - q[1]), 6))]


def b2b_anchor(fp_geo, mate_anchor, pin_map):
    """Anchor of J208 (side F) that puts pad n under J209 pad pin_map[n] (J209 anchored on the PWR-B bottom)."""
    mate = bg.placed_geometry(fp_geo, mate_anchor)['pads']
    for rot in (0, 90, 180, 270):
        local = bg.placed_geometry(fp_geo, {'at': [0.0, 0.0], 'align': 'origin', 'rotation': rot, 'side': 'F'})['pads']
        p1 = local['1'][0]
        m1 = mate[pin_map['1']][0]
        dx, dy = m1[0] - p1[0], m1[1] - p1[1]
        if all(abs(local[n][0][0] + dx - mate[m][0][0]) < 1e-6 and abs(local[n][0][1] + dy - mate[m][0][1]) < 1e-6
               for n, m in pin_map.items()):
            return {'at': [r4(dx), r4(dy)], 'align': 'origin', 'rotation': rot, 'side': 'F'}
    raise SystemExit('make_spec: no rotation of J208 puts every contact under its J209 mate')


def edge_x(contract, y0, y1):
    """Right outline edge (x) of the PWR L over the rows y0..y1: the smallest x of an outline vertical edge spanning them."""
    pts = contract['outline_mm']
    xs = [ax for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1])
          if ax == bx and ax > 0 and min(ay, by) < y1 and max(ay, by) > y0]
    return min(xs)


def live_status(pspec):
    """{change id: status row} of candidates.shrink2.planned against the graph of now (pcb/partition_budget.py
    Evaluator.planned: the budget's own rule; a half-applied change stops it)."""
    ev = pbud.Evaluator(pbud.Design(pspec))
    _, rows, _ = ev.planned(pspec['candidates'][CANDIDATE])
    return {row['id']: row for row in rows}


def bottom_row_anchors(draft_by_ref, fp_geo_of, row_end_max, margin, keep=None):
    """Anchors of the bottom-edge row: each header keeps its courtyard bottom on the edge line of the draft and its order;
    the turned ones rotate by 90 degrees; the row is packed from BOTTOM_ROW_START with GAP between courtyards."""
    out, x = {}, BOTTOM_ROW_START
    for ref in [r for r in BOTTOM_ROW if r in draft_by_ref and (keep is None or (r in keep and r not in F2C_PLACES))]:
        # W2 PWRJ-F2C probe: headers that moved to PWR-C (pcb/partition-spec.json partition.domain_override_pwr_c) or
        # were deleted with S06/S07 (dnp) leave the row; the rest keep the draft order
        old = draft_by_ref[ref]['anchor']
        geo = fp_geo_of(ref)
        rot = (float(old.get('rotation', 0)) + (90 if ref in BOTTOM_ROW_TURNED else 0)) % 360
        rot = int(rot) if rot == int(rot) else rot
        probe = {**old, 'rotation': rot}
        box0 = bg.placed_geometry(geo, old)['box']
        box = bg.placed_geometry(geo, probe)['box']
        dx, dy = x - box[0], box0[1] - box[1]
        at = [r4(old['at'][0] + dx), r4(old['at'][1] + dy)]
        out[ref] = {**{k: v for k, v in old.items() if k != 'ref_text'}, 'at': at, 'rotation': rot}
        x = r4(box[2] + dx + GAP)
    end = r4(x - GAP + margin)
    if end > row_end_max + 1e-9:
        raise SystemExit(f'make_spec: the bottom row ends at x {end} (+ window margin) beyond row_end_max {row_end_max}')
    return out, end


def build():
    draft = bg.read_json(DRAFT)
    graph = bg.load_graph()
    manifest = bg.read_json(bg.MANIFEST)
    fps = {f['footprint']: f for f in manifest['footprints']}
    pspec = bg.read_json(PSPEC)
    budget = bg.read_json(BUDGET)
    cand = pspec['candidates'][CANDIDATE]
    bud = budget['candidates'][CANDIDATE]
    contract = bg.read_json(CONTRACT)['boards'][draft['contract']['board']]
    partition = bg.read_json(PARTITION)
    f2c = bool(pspec['partition'].get('domain_override_pwr_c'))  # W2 PWRJ-F2C probe
    domains = set(draft['domains'])
    domain_refs = sorted((p['ref'] for p in partition['parts'] if p['board_candidate'] in domains and not p['dnp']),
                         key=bg.sort_ref)
    draft_refs = {p['ref'] for p in draft['parts'] if p['source'] == 'graph'}

    def fp_geo_of(ref):
        return bg.footprint_geometry((BASE / fps[graph[ref]['footprint']]['file']).read_text(encoding='utf-8'))

    # --- planned changes: status from the graph of now (pcb/partition_budget.py rule), content from the spec ---
    status = live_status(pspec)
    changes = []
    drop, planned_fp, reserved = set(), {}, []
    for ch in cand['planned']['changes']:
        st = status[ch['id']]['status']
        to = ch['to']
        row = {'id': ch['id'], 'refs': ch['refs'], 'owner': ch.get('owner'), 'status': st}
        if 'merge_into' in to or ch['id'] == 'C506-3x':
            row['effect'] = 'PWR-B (not on PWR-A)'
        elif st == 'pending':
            if to.get('delete'):
                drop |= set(ch['refs'])
                row['effect'] = 'dropped (deleted by the change)'
            elif 'blocks' in to:
                drop |= set(ch['refs'])
                for b in to['blocks']:
                    x, y = BLOCK_AT[b['id']]
                    reserved.append({'id': b['id'], 'rect': [x, y, r4(x + b['w']), r4(y + b['d'])], 'side': 'F',
                                     'kind': 'block', 'h_mm': b['h'], 'stands_for': ch['refs'], 'change': ch['id'],
                                     'what': b['what'], 'source': b['src'],
                                     'position_source': 'design choice of the SHRINK-2 study (make_spec.py BLOCK_AT)'})
                row['effect'] = 'reserved blocks ' + ', '.join(b['id'] for b in to['blocks'])
            else:
                for r in ch['refs']:
                    if r in graph:
                        planned_fp[r] = {'footprint': to['footprint'], 'mpn': to.get('mpn'), 'change': ch['id'],
                                         'graph_footprint': graph[r]['footprint']}
                row['effect'] = f'planned footprint {to["footprint"]}'
        else:
            row['effect'] = 'in graph: the graph counts'
            if status[ch['id']].get('graph_refs'):
                row['graph_refs'] = status[ch['id']]['graph_refs']
        changes.append(row)
    for f in planned_fp:
        if planned_fp[f]['footprint'] not in fps:
            raise SystemExit(f'make_spec: planned footprint {planned_fp[f]["footprint"]} of {f} is not vendored')
    pwr_b = set(bud['pwr_b_refs'])
    power_live = all(status[c]['status'] == 'in graph' for c in POWER_ANCHOR_CHANGES)

    # --- the PWR-A ref set ---
    keep = [r for r in domain_refs if r not in drop and r not in pwr_b]
    keep_set = set(keep)
    for r in list(planned_fp):
        if r not in keep_set:
            planned_fp.pop(r)
    ffc = sorted(r for r in keep if graph[r].get('footprint', '').startswith(FFC_PREFIX))
    bottom_list = cand['pwr_a_bottom']['refs']
    bottom = [r for r in bottom_list if r in keep_set]
    bottom_missing = [r for r in bottom_list if r not in keep_set]
    bottom_set = set(bottom)

    # --- anchors ---
    by_ref = {p['ref']: p for p in draft['parts']}
    places = FFC_PLACES if ffc else PWRA1_PLACES
    parts, anchored = [], set()
    b2b_contacts = bg.read_json(B2B_NETS)['contacts']
    pin_map = {c['pwr_a_pin']: c['pwr_b_pin'] for c in b2b_contacts}
    spec_b = bg.read_json(PWR_B_SPEC)
    mate = next(p for p in spec_b['parts'] if p['ref'] == B2B_PAIR[1])
    edge0 = contract['edge_zones'][0]
    row_end_max = edge0.get('row_end_max')
    margin_w = pspec['parameters']['window_margin']
    row_anchors, row_end = (bottom_row_anchors(by_ref, fp_geo_of, row_end_max, margin_w, keep_set) if row_end_max is not None
                            else ({}, None))
    for ref in keep:
        old = by_ref.get(ref)
        if ref == B2B_PAIR[0]:
            anchor = b2b_anchor(fp_geo_of(ref), mate['anchor'], pin_map)
            parts.append({'ref': ref, 'source': 'graph', 'anchor': anchor,
                          'anchor_source': f'under PWR_B {B2B_PAIR[1]} (pcb/boards/PWR_B.json anchor {mate["anchor"]["at"]} '
                                           f'side {mate["anchor"]["side"]} rotation {mate["anchor"]["rotation"]}): pad n of '
                                           f'{ref} under {B2B_PAIR[1]} pad map(n) of pcb/generated/b2b-nets.json contacts '
                                           '(n odd -> n+1, n even -> n-1), computed by make_spec.py b2b_anchor'})
            anchored.add(ref)
            continue
        if power_live and ref in POWER_ANCHORS:
            x, y, rot = POWER_ANCHORS[ref]
            parts.append({'ref': ref, 'source': 'graph',
                          'anchor': {'at': [x, y], 'align': 'origin', 'rotation': rot, 'side': 'F'},
                          'anchor_source': 'W2 PCB-PWRA-3 part 2 power stage (make_spec.py POWER_ANCHORS, design choice): '
                                           + ('contract converter zone ' + next(z for z, rs in
                                              contract.get('converter_zone_refs', {}).items() if ref in rs)
                                              if any(ref in rs for rs in contract.get('converter_zone_refs', {}).values())
                                              else 'beside its converter, pads on the scripted copper')})
            anchored.add(ref)
            continue
        if f2c and ref in F2C_PLACES:
            at, rot = F2C_PLACES[ref]
            parts.append({**old, 'anchor': {'at': at, 'align': 'origin', 'rotation': rot, 'side': 'F'},
                          'anchor_source': 'W2 PWRJ-F2C probe: W-C1 LAB5 feed in the bottom row at the freed J108 slot (make_spec.py '
                                           'F2C_PLACES, design choice)'})
            anchored.add(ref)
            continue
        if f2c and ref in F2C_PINS and not (old and old.get('anchor')):
            x, y, rot = F2C_PINS[ref]
            parts.append({'ref': ref, 'source': 'graph',
                          'anchor': {'at': [x, y], 'align': 'origin', 'rotation': rot, 'side': 'F'},
                          'anchor_source': 'W2 PWRJ-F2C probe: PWR-B cut-out part kept at its PCB-PWRA-4 place, or a J21/DISP '
                                           'test point moved out of the PWR-B bar into a freed E1 probe window (make_spec.py '
                                           'F2C_PINS)'})
            anchored.add(ref)
            continue
        if ref in row_anchors:
            parts.append({**old, 'anchor': row_anchors[ref],
                          'anchor_source': ('bottom edge row of the MECH-7 contract (edge_zones[0] row_end_max '
                                            f'{row_end_max}): ' + ('turned by 90 degrees, ' if ref in BOTTOM_ROW_TURNED
                                                                   else '') + 'packed from x '
                                            f'{BOTTOM_ROW_START} in the draft order {", ".join(BOTTOM_ROW)}, 0.5 mm apart '
                                            '(make_spec.py bottom_row_anchors)')})
            anchored.add(ref)
            continue
        if old is None or not old.get('anchor'):
            parts.append({'ref': ref, 'source': 'graph'})
            continue
        if ref in ('U107', 'U108'):  # a Pololu square anchor never carries over: the converter is a block or POWER_ANCHORS
            parts.append({'ref': ref, 'source': 'graph'})
            continue
        part = {k: v for k, v in old.items()}
        if ref in places:
            at, rot = places[ref]
            part['anchor'] = {**old['anchor'], 'at': at, 'rotation': rot}
            part['anchor_source'] = ('SHRINK-2: the S02 FFC is in the graph, so this header moves to the PWR-A bottom edge '
                                     '(decision place)') if ffc else (
                'SHRINK-2 without the S02 FFC: the wip/w2-pwra1 80d92c28 place (second/third column of the right edge, '
                'the recorded deviation of W2 PCB-PWRA-1); J208 ends at x 114.15, so the column is free again')
            part['anchor'].pop('ref_text', None)
        parts.append(part)
        anchored.add(ref)

    # --- scripted copper of the power stages: planner keep-outs (kind copper; not a courtyard demand) ---
    copper_zones, copper_vias = [], []
    if power_live:
        pwr_a_nets = {pin['net'] for r in keep for pin in graph[r]['pins'] if pin.get('net')}
        for zid, item in POWER_POURS.items():
            net, outline, why, layer = item['net'], item['outline'], item['why'], item['layer']
            if net not in pwr_a_nets:
                raise SystemExit(f'make_spec: pour {zid} net {net} is not a PWR-A net')
            zone = {'id': zid, 'net': net, 'layer': layer, 'outline': outline, 'priority': 2, 'pad_connection': 'solid',
                    'why': why + ' (W2 PCB-PWRA-3, make_spec.py POWER_POURS; solid pad connection)'}
            if item['pin_entry']:
                zone['pin_entry'] = item['pin_entry']
            if item['branch']:
                zone['branch'] = True
            copper_zones.append(zone)
            if layer in ('F.Cu', 'B.Cu'):  # inner copper is no placement obstacle
                xs, ys = [p[0] for p in outline], [p[1] for p in outline]
                reserved.append({'id': 'CU_' + zid, 'rect': [min(xs), min(ys), max(xs), max(ys)],
                                 'side': 'F' if layer == 'F.Cu' else 'B', 'kind': 'copper',
                                 'what': f'scripted {net} pour on {layer} (planner keep-out, not a courtyard)',
                                 'source': 'make_spec.py POWER_POURS'})
        for vid, at in POWER_VIAS.items():
            net = at[2] if len(at) > 2 else 'GND'
            why = ('W2 PCB-PWRA-3 part 2 GND via of a power stage (make_spec.py POWER_VIAS): In1/In2 GND planes and the L4 '
                   'bond copper of zones 3\'/4\'' if net == 'GND' else
                   f'W2 PCB-PWRA-3 review fix {net} via (make_spec.py POWER_VIAS): ' +
                   ('In2.Cu VIN strap/bridge of the LM61460 input' if net == 'E1_CONV_IN' else 'F.Cu <-> B.Cu trunk transition'))
            copper_vias.append({'id': vid, 'net': net, 'at': [at[0], at[1]], 'diameter_mm': 0.6, 'drill_mm': 0.3,
                                'locked': True, 'why': why + '; size = the project via 0.6/0.3'})

    # --- groups ---
    grouped = set()
    draft_groups = {g['id']: g for g in draft['groups']}
    regions = dict(TOP_REGIONS)
    if ffc:
        for k in FFC_REGIONS['drop']:
            regions.pop(k)
        regions.update(FFC_REGIONS['add'])
    if power_live:
        # review fix F2: every top region gives way to the F.Cu scripted copper and the power-stage anchors (the planner
        # packs a region from its corner and does not step over an obstacle); a cut region keeps its name for its first
        # piece, the others get a letter
        cuts = [[min(p[0] for p in it['outline']), min(p[1] for p in it['outline']), max(p[0] for p in it['outline']),
                 max(p[1] for p in it['outline'])] for it in POWER_POURS.values() if it['layer'] == 'F.Cu']
        cuts += [bg.placed_geometry(fp_geo_of(r), next(p['anchor'] for p in parts if p['ref'] == r))['box']
                 for r in POWER_ANCHORS if r in anchored]
        for cut in cuts:
            nxt = {}
            for name, reg in regions.items():
                for i, piece in enumerate(subtract_rect(reg, cut, keep_min=1.5)):
                    nxt[name if i == 0 else f'{name}{chr(ord("a") + i)}'] = piece
            regions = nxt
    # new graph refs (since the draft) join the draft group of their schematic group
    new_refs = [r for r in keep if r not in draft_refs and r not in anchored]
    extra = {}
    for r in new_refs:
        gid = SCHEMATIC_GROUP.get((graph[r]['_sheet'], graph[r].get('group')))
        if gid:
            extra.setdefault(gid, []).append({'ref': r, 'rotation': 0})
    # bottom pockets of the contract (MECH-7): PB1-PB13, board mm [x0, y0, x1, y1]
    bs = contract.get('bottom_side') or {}
    pockets = {}
    for name, (x, y, w, h) in zip(bs.get('pockets', []), bs.get('keep_in_mm', [])):
        # a pocket that reaches the board edge gives way to EDGE_INSET (design value, as the draft regions): a bottom
        # chip keeps its copper off the outline
        pockets[name] = [r4(max(x, EDGE_INSET)), r4(max(y, EDGE_INSET)), r4(min(x + w, edge_x(contract, y, y + h) - EDGE_INSET)),
                         r4(min(y + h, max(py for _, py in contract['outline_mm']) - EDGE_INSET))]
    if not pockets:
        raise SystemExit('make_spec: the contract PWR bottom_side has no pockets (MECH-7)')
    # review fix F2: the B.Cu scripted copper (LAB5 trunk) cuts the pockets into bottom regions (the planner packs a
    # region from its corner and does not step over an obstacle); the contract pockets stay the pocket rule of the study
    bottom_regions = dict(pockets)
    if power_live:
        for zid, item in POWER_POURS.items():
            if item['layer'] != 'B.Cu':
                continue
            xs, ys = [p[0] for p in item['outline']], [p[1] for p in item['outline']]
            cut = [min(xs), min(ys), max(xs), max(ys)]
            nxt = {}
            for name, reg in bottom_regions.items():
                pieces = subtract_rect(reg, cut)
                for i, piece in enumerate(pieces):
                    nxt[name if i == 0 else f'{name}{chr(ord("a") + i)}'] = piece
            bottom_regions = nxt

    def nearest_pockets(region):
        cx, cy = (region[0] + region[2]) / 2, (region[1] + region[3]) / 2

        def dist(p):
            dx = max(p[0] - cx, 0, cx - p[2])
            dy = max(p[1] - cy, 0, cy - p[3])
            return math.hypot(dx, dy)
        return sorted(bottom_regions, key=lambda n: (round(dist(bottom_regions[n]), 6), n))

    groups, bottom_groups = [], []
    split = {r for refs in SPLIT_GROUPS.values() for r in refs}
    for gid, region, alts in TOP_GROUPS:
        g = draft_groups.get(gid)
        if gid in SPLIT_GROUPS:
            g = {'id': gid, 'gap_mm': 0.5, 'members': [{'ref': r, 'rotation': 0} for r in SPLIT_GROUPS[gid]]}
        elif g is None:
            continue
        else:
            g = {**g, 'members': [m for m in g['members'] if m['ref'] not in split]}
        members = list(g['members']) + [m for m in extra.get(gid, []) if m['ref'] not in split]
        top = [m for m in members if m['ref'] in keep_set and m['ref'] not in bottom_set and m['ref'] not in anchored]
        bot = [{'ref': m['ref'], 'rotation': 0} for m in members if m['ref'] in bottom_set]
        alts = [a for a in alts if a in regions]
        if region not in regions:
            if not alts:
                raise SystemExit(f'make_spec: group {gid} has neither its region {region} nor an alt region left')
            region, alts = alts[0], alts[1:]
        if top:
            groups.append({'id': gid, 'region': regions[region], 'region_name': region, 'alt_regions': alts,
                           'side': 'F', 'gap_mm': g.get('gap_mm', 0.5), 'members': top})
        if bot:
            order = nearest_pockets(regions[region])
            bottom_groups.append({'id': gid + '_BOT', 'region': bottom_regions[order[0]], 'region_name': order[0],
                                  'alt_regions': order[1:], 'side': 'B', 'gap_mm': g.get('gap_mm', 0.5), 'members': bot})
        grouped |= {m['ref'] for m in top} | {m['ref'] for m in bot}
    for gid in draft_groups:
        if gid not in {t[0] for t in TOP_GROUPS} - set(SPLIT_GROUPS):
            raise SystemExit(f'make_spec: draft group {gid} has no SHRINK-2 region (TOP_GROUPS)')
    rest = [r for r in keep if r not in grouped and r not in anchored]
    if rest:
        groups.append({'id': 'NEW_UNASSIGNED', 'region': regions['BAND_TOP_MID'], 'region_name': 'BAND_TOP_MID',
                       'alt_regions': [], 'side': 'F', 'gap_mm': 0.5,
                       'members': [{'ref': r, 'rotation': 0} for r in rest],
                       'why': 'graph refs that no designed SHRINK-2 region names (new since the draft): the study packs '
                              'them anywhere and lists them; a regeneration names their region'})
    # bottom: the thermal_bond zones are side-B obstacles (contract zones; the planned zones until MECH-7 lands)
    zones = [list(z) for z in contract['thermal_bond_mm']]
    planned_zones = cand['pwr_a_bottom'].get('thermal_bond_planned', {})
    zone_src = []
    for k, z in sorted(planned_zones.items()):
        i = int(k) - 1
        if zones[i] != list(z):
            zone_src.append(f'zone {k}: planned {z} (pcb/partition-spec.json candidates.shrink2.pwr_a_bottom.'
                            f'thermal_bond_planned; contract still {zones[i]}, MECH-7 pending)')
            zones[i] = list(z)
        else:
            zone_src.append(f'zone {k}: contract {z} (MECH-7 landed)')
    for i, (x, y, w, h) in enumerate(zones, 1):
        reserved.append({'id': f'BOND{i}', 'rect': [x, y, x + w, y + h], 'side': 'B', 'kind': 'thermal_bond',
                         'what': 'thermal_bond zone (Gelid pad on the plate): no bottom-side part',
                         'source': 'mechanical/generated/contract/boards.json PWR thermal_bond_mm' if i <= 2 else
                         '; '.join(s for s in zone_src if s.startswith(f'zone {i}:')) or 'contract'})

    # --- instances, nets, copper ---
    nets = set()
    for r in keep:
        nets |= {pin['net'] for pin in graph[r]['pins'] if pin.get('net') and not pin.get('nc')}
    pre = draft['pre_route']
    lab5_raw = 'E1_LAB5_RAW'  # the pour of the draft ran U108 VOUT -> F102.1; SHRINK-2 re-scripts it from the converter
    pre_route = {
        'tracks': [t for t in pre.get('tracks', []) if t['net'] in nets and t['net'] != lab5_raw],
        'vias': [v for v in pre.get('vias', []) if v['net'] in nets] + copper_vias,
        'zones': [z for z in pre.get('zones', []) if z['net'] in nets and z['net'] != lab5_raw] + copper_zones,
    }
    post = []
    for z in draft['post_route_zones']:
        zid = z['id']
        if zid in ('GND-BOND-3', 'GND-BOND-4'):
            x, y, w, h = zones[int(zid[-1]) - 1]
            z = {**z, 'outline': [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
                 'why': f'GND copper on L4 over thermal_bond zone {zid[-1]} (SHRINK-2 converter zone); mask on'}
        if z['net'] in nets:
            post.append(z)
    item = draft['instances']['list'][0]
    inst = {
        'template_nets': sorted(nets),
        'list': [{**{k: v for k, v in item.items() if k not in ('refs', 'nets', 'source')},
                  'refs': {r: r for r in keep}, 'nets': {n: n for n in sorted(nets)},
                  'source': 'identity map (graph refs and nets of the SHRINK-2 PWR-A set)'}],
    }
    for k, v in draft['instances'].items():
        if k not in ('template_nets', 'list'):
            inst[k] = v

    out = {}
    for k, v in draft.items():
        if k in ('split_nets', 'split_nets_note', 'b2b', 'reserved_area_mm2'):
            continue
        if k == 'status':
            v = 'DRAFT_SHRINK2_PLANNER_NOT_FOR_FABRICATION'
        elif k == 'title':
            v = 'PWR-A plate-bonded power board, two-sided SHRINK-2 layout - placement draft'
        elif k == 'note':
            v = ('W2 PCB-PWRA-3: generated by build/kicad/boards/PWR_A/make_spec.py from PWR_A.spec-draft.json, the graph, '
                 'pcb/partition-spec.json candidates.shrink2 and the MECH-7 contract (never hand-edited). Kept in '
                 'build/kicad/boards/PWR_A/, not in pcb/boards/: a placement draft with locked power-stage copper; the '
                 'board of record (routed to DRC 0, fab set) is W2 PCB-PWRA-4. placement_study.py --spec '
                 'PWR_A.spec-shrink2.json writes placement-study-shrink2.json.')
        elif k == 'parts':
            v = parts
        elif k == 'instances':
            v = inst
        elif k == 'groups':
            v = groups + bottom_groups
        elif k == 'regions':
            v = {'note': 'free rectangles of the SHRINK-2 layout (make_spec.py TOP_REGIONS, design choice) and the plate '
                         'pockets PB1-PB13 of the contract (bottom_side.keep_in_mm) as bottom regions; a group names its '
                         'preferred region and alt_regions (bottom: the nearest pocket first); board_gen reads only '
                         'group.region; placement_study.py uses rects for top groups and bottom_rects for bottom groups',
                 'rects': regions, 'bottom_rects': bottom_regions}
        elif k == 'reserved_areas':
            v = reserved
        elif k == 'pre_route':
            v = pre_route
        elif k == 'post_route_zones':
            v = post
        out[k] = v
    out['budget_candidate'] = CANDIDATE
    out['fallback_id'] = 'F2-C'
    out['reserved_area_mm2'] = [{'id': 'PWR_B_THT_KEEPOUTS', 'area_mm2_source':
                                 f'pcb/partition-budget.json candidates.{CANDIDATE}.pwr_a_keepouts_mm2',
                                 'what': 'rule H-TRIM (pcb/partition-spec.json keepouts.h_trim): the area under the PWR-B THT '
                                         'pin fields is a height zone (parts up to zone_h_max_mm), not a keepout'}]
    out['b2b'] = [{'ref': B2B_PAIR[0], 'mate_board': 'PWR_B', 'mate_ref': B2B_PAIR[1],
                   'pin_map': {k: pin_map[k] for k in sorted(pin_map, key=int)},
                   'pin_map_source': 'pcb/generated/b2b-nets.json contacts (pwr_a_pin -> pwr_b_pin)'}]
    out['planned_footprints'] = {r: planned_fp[r] for r in sorted(planned_fp, key=bg.sort_ref)}
    out['planned_changes'] = changes
    out['planned_status_source'] = ('pcb/partition_budget.py Evaluator.planned on the graph of now (live; '
                                    'pcb/partition-budget.json is regenerated by the AREA lineage)')
    out['two_sided'] = {
        'bottom_refs': bottom, 'bottom_refs_missing': bottom_missing,
        'tht_margin_mm': cand['pwr_a_bottom']['tht_margin'],
        # review fix F7: the room under PWR-A is the contract h_max once MECH-7 landed; the partition-spec value is the
        # superseded part-1 planning figure
        'h_room_mm': bs.get('h_max', cand['pwr_a_bottom']['h_room_mm']),
        'h_room_source': ('mechanical/generated/contract/boards.json PWR bottom_side h_max (MECH-7)' if 'h_max' in bs else
                          'pcb/partition-spec.json candidates.shrink2.pwr_a_bottom.h_room_mm (MECH-7 pending)'),
        'h_room_mm_planning_superseded': cand['pwr_a_bottom']['h_room_mm'] if 'h_max' in bs else None,
        'thermal_bond_zones': [[x, y, x + w, y + h] for x, y, w, h in zones], 'thermal_bond_zones_source': zone_src,
        'bottom_pockets': pockets, 'bottom_pockets_source': 'mechanical/generated/contract/boards.json PWR bottom_side '
                                                            'keep_in_mm (MECH-7, plate pockets PB1-PB13, board mm)',
        'rule': bs.get('rule') or cand['pwr_a_bottom']['rule'],
    }
    out['h_trim'] = {k: pspec['keepouts']['h_trim'][k] for k in ('protrusion_max_mm', 'zone_h_max_mm', 'clearance_mm')}
    out['ffc'] = {'adopted': bool(ffc), 'refs': ffc,
                  'rule': 'the S02 FFC counts as adopted when a PWR-A graph part has a Connector_FFC-FPC footprint (GR-5B); '
                          'then J113/J114/J115/J507 take the decision places on the bottom edge and exit_edges says so'}
    if ffc:
        out['exit_edges'] = {r: 'bottom' for r in FFC_PLACES}
    out['turn_whatif'] = [r for r in TURN_WHATIF if r not in row_anchors]
    if row_anchors:
        out['bottom_row'] = {'refs': BOTTOM_ROW, 'turned': BOTTOM_ROW_TURNED, 'start_x': BOTTOM_ROW_START,
                             'end_x_with_margin': row_end, 'row_end_max': row_end_max,
                             'rule': 'MECH-7 contract edge_zones[0] row_end_max: the courtyards of J105-J112 + window_margin '
                                     'end at x <= row_end_max, so that the PWR-A bottom edge under the PWR-B PH 9-pin span '
                                     '(PWR_B edge_zones[2]) stays free of PWR-A headers'}
    if power_live:
        out['power_stages'] = {
            'anchors': sorted(POWER_ANCHORS, key=bg.sort_ref),
            'converter_zone_refs': contract.get('converter_zone_refs'),
            'pours': sorted(POWER_POURS), 'vias': sorted(POWER_VIAS),
            'branch_pads': POWER_BRANCH_PADS,
            'trunks': POWER_TRUNKS,
            'u107_input_source': POWER_FIX_SOURCE,
            'note': 'W2 PCB-PWRA-3 (design choice; review fixes F1/F2): anchored power stages and their scripted copper. '
                    'Scripted: E1_SW from J107.2 to Q102; E1_CONV_IN from Q102 to both LM61460 VIN pins (each side with its '
                    'CIN_HF and CIN, joined by the In2 VIN strap), C107 and both TPSM63606 VIN pins; SYS12 from L102.2 '
                    'over COUT across the spine to the SYS12 node with F201.1, L202.1 and Q201.2; E1_LAB5_RAW from U108 '
                    'VOUT to F102.1; E1_LAB5_FUSED from F102.2 to C111.1 and L101.1; LAB5 from L101.2 to C112.1, F104.1, '
                    'L205.1 (the LT3045 feed) and the four J208 LAB5 contacts (F.Cu and B.Cu trunk). Left to the router '
                    '(PCB-PWRA-4; placement_study.py corridor pre-check): the U107/U108 small-signal pins (FB, RT, EN, '
                    'CBOOT, RBOOT, VCC, BIAS, PG) to their parts, the 0603 E1_CONV_IN bypass C132 at U108, the other '
                    'LAB5 loads (J104, J206.2, U503, U553, C552, C509, C223, R110), E2_LNA_IN from L205.2 to the LT3045 '
                    'IN pins and every branch net after F201, L202 and Q201',
        }
    # pcb/check_boards.py keys of a two-sided board: parts on both sides, bottom height limit = the room under PWR-A
    out['sides'] = ['top', 'bottom']
    out['max_height_bottom'] = bs.get('h_max', cand['pwr_a_bottom']['h_room_mm'])
    out['max_height_bottom_note'] = ('mechanical/generated/contract/boards.json PWR bottom_side h_max (MECH-7: shim gap 0.4 '
                                     '+ pocket depth 1.0 - polyimide film 0.07 - clearance 0.3); the heights of the bottom '
                                     'chip parts are not read (TBD per MPN), so check_boards lists them as unverified')
    out['generator'] = 'build/kicad/boards/PWR_A/make_spec.py'
    bg.validate_spec(out, 'PWR_A')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args(argv)
    text = json.dumps(build(), ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding='utf-8') != text:
            print('PWR_A.spec-shrink2.json is stale: rerun build/kicad/boards/PWR_A/make_spec.py')
            return 1
        print('PWR_A.spec-shrink2.json reproduces')
        return 0
    bg.atomic_write(OUT, text)
    doc = json.loads(text)
    print(f'{OUT.relative_to(BASE).as_posix()}: {len(doc["parts"])} parts, '
          f'{sum(1 for p in doc["parts"] if p.get("anchor"))} anchored, {len(doc["two_sided"]["bottom_refs"])} bottom, '
          f'{len(doc["reserved_areas"])} reserved areas, {len(doc["planned_footprints"])} planned footprints, '
          f'FFC {doc["ffc"]["adopted"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
