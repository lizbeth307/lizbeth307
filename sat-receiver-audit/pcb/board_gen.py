#!/usr/bin/env python3
"""Generate, route and check one SR-RX board from its spec pcb/boards/<BOARD>.json.

Modes (run from any directory):
  python3 pcb/board_gen.py --board ENC              --check (default): read-only. Re-runs KiCad DRC and the
                                                     audits on the committed board and fails unless they
                                                     reproduce build/kicad/boards/<B>/report.json.
  python3 pcb/board_gen.py --board ENC --route      places, lays the scripted locked copper, routes the rest
                                                     with the pinned Freerouting 2.5.0 JAR, imports the session,
                                                     pours, fills, runs DRC and writes the outputs.
  python3 pcb/board_gen.py --board ENC --inputs-only  standard library only: spec, contract and graph
                                                     projection against the committed report.
  python3 pcb/board_gen.py --list-boards            JSON list of board ids (CI matrix).

--check and --route need KiCad 10.0.7 (pcbnew Python module and kicad-cli, as in the kicad/kicad:10.0.7
image); everything else, and pcb/tests, uses the standard library only. Routing is a frozen output: CI
re-routes a board only when the subject (first line) of the head commit message carries the token
'[pcb-route <BOARD>]' and does not start with 'GENERATED:'.
Freerouting (GPL-3.0) and its Java runtime are fetched in CI by pinned SHA256 and never committed or bundled.
Results are CI/model results, never a hardware PASS.
"""
from __future__ import annotations

import argparse
import faulthandler
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

BASE = Path(__file__).resolve().parents[1]
# The git work tree around sat-receiver-audit (a checkout or a worktree): fetch-only tools stay outside all of it.
REPO_ROOT = next((d for d in (BASE, *BASE.parents) if (d / '.git').exists()), BASE)
SPEC_DIR = BASE / 'pcb/boards'
OUT_ROOT = BASE / 'build/kicad/boards'
GRAPHS = [BASE / f'design/E{i}.json' for i in range(1, 6)]
MANIFEST = BASE / 'build/kicad/footprints/manifest.json'
PARTS_DB = BASE / 'design/parts/parts.json'
KICAD_VERSION = '10.0.7'
SPEC_SCHEMA = 'srrx-board-spec-v1'
REPORT_SCHEMA = 'srrx-board-report-v1'
# Fixed pattern; the commit message is data and never reaches a shell.
ROUTE_TOKEN = re.compile(r'\[pcb-route ([A-Z][A-Z0-9_]*)\]')
# Contract fields that the board copper, the audits and connectors.json read (F10 'contract' projection).
# Other fields of the entry (name, dxf, mount text, area, thermal bonds, modules, later MECH additions)
# do not make a board stale; placements count only by origin, z_bottom and facing.
CONTRACT_FIELDS = ('outline_mm', 'cutouts_mm', 'holes_mm', 'hole_d', 'hole_keepout_d', 'max_component_height',
                   'edge_zones')
PLACEMENT_FIELDS = ('origin', 'z_bottom', 'facing')
# Optional spec keys (W2 PCB-PWRB): zone pad connection, copper layer type (a 'power' layer is a plane layer in the
# Specctra export, specctra_export.cpp :1124-1138 at 10.0.7, so Freerouting routes no traces on it).
ZONE_PAD_CONNECTIONS = {'thermal': 'ZONE_CONNECTION_THERMAL', 'solid': 'ZONE_CONNECTION_FULL',
                        'tht_thermal': 'ZONE_CONNECTION_THT_THERMAL', 'none': 'ZONE_CONNECTION_NONE'}
LAYER_TYPES = {'signal': 'LT_SIGNAL', 'power': 'LT_POWER', 'mixed': 'LT_MIXED'}

# Release v2.5.0 of https://github.com/freerouting/freerouting (published 2026-10-05, GPL-3.0; licence from
# gh api repos/freerouting/freerouting/license). Asset digests read from the GitHub release API
# (gh api repos/freerouting/freerouting/releases/tags/v2.5.0) on 2026-11-07.
# The release also ships a native GraalVM CLI (freerouting-cli-2.5.0-linux-x64.tar.gz, sha256
# 64a957a9ef2a2fbde6ab2001bb32800f5ba34f9fd15575e363512934b870d63a). The first CI probe (run 42388559634,
# 2026-11-07) showed that binary dying in its routing thread with GraalVM UnsupportedFeatureError
# 'SerializationConstructorAccessor class not found for ... ComponentOutline' and then waiting forever:
# its native-image metadata (src/main/resources/META-INF/native-image/reachability-metadata.json at
# v2.5.0) registers only DrillItem, Item, Pin, Trace and Via of board.model.items for serialization, so a
# DSN with component outlines, keepouts or planes fails. The same release's JAR runs on the JVM instead.
FREEROUTING = {
    'name': 'Freerouting',
    'version': '2.5.0',
    'licence': 'GPL-3.0',
    'url': 'https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-2.5.0.jar',
    'sha256': 'f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7',
    'size': 64599107,
    'file': 'freerouting-2.5.0.jar',
    # Headless entry point of the same sources (build.gradle at v2.5.0 :492; src/main/java/app/freerouting/cli/
    # FreeroutingCli.java disables the GUI, API and MCP servers).
    'main_class': 'app.freerouting.cli.FreeroutingCli',
    'requires': 'Java 25 (build.gradle at v2.5.0 :28-33)',
    'source_read': 'GitHub release API v2.5.0 asset digests, read 2026-11-07',
}
# Eclipse Temurin JRE 25.0.5+8 for linux x64 (GPL-2.0 with Classpath Exception, https://adoptium.net/docs/faq/
# read 2026-11-07). Digest from the Adoptium API (api.adoptium.net/v3/assets/latest/25/hotspot) and the GitHub
# release API (adoptium/temurin25-binaries tag jdk-25.0.5+8, published 2026-10-22), both read 2026-11-07.
TEMURIN_JRE = {
    'name': 'Eclipse Temurin JRE',
    'version': '25.0.5+8',
    'licence': 'GPL-2.0-with-classpath-exception',
    'url': 'https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.5%2B8/OpenJDK25U-jre_x64_linux_hotspot_25.0.5_8.tar.gz',
    'sha256': '6fac98f0c8202efc3135a9e9e42aa61963ec42d1c5cbb40caf231e7b14a24ef6',
    'size': 61736206,
    'source_read': 'Adoptium API and GitHub release API, read 2026-11-07',
}

# Every DRC check key of KiCad 10.0.7 (pcbnew/drc/drc_item.cpp at tag 10.0.7, read 2026-11-07).
# Each board project must give every one of them a reviewed severity: 'error', or 'warning' with a
# reason in the spec drc_policy. 'ignore' is refused, so DRC reports ignored_checks [].
DRC_KEYS = frozenset('''
annular_width assertion_failure clearance connection_width copper_edge_clearance copper_sliver
courtyards_overlap creepage diff_pair_gap_out_of_range diff_pair_uncoupled_length_too_long
drill_out_of_range duplicate_footprints extra_footprint footprint footprint_filters_mismatch
footprint_symbol_field_mismatch footprint_symbol_mismatch footprint_type_mismatch generic_error
generic_warning hole_clearance hole_to_hole holes_co_located invalid_outline isolated_copper
item_on_disabled_layer items_not_allowed length_out_of_range lib_footprint_issues lib_footprint_mismatch
malformed_courtyard microvia_drill_out_of_range mirrored_text_on_front_layer missing_courtyard
missing_footprint missing_tuning_profile net_conflict nonmirrored_text_on_back_layer npth_inside_courtyard
padstack padstack_invalid pth_inside_courtyard shorting_items silk_edge_clearance silk_over_copper
silk_overlap skew_out_of_range solder_mask_bridge starved_thermal text_height text_on_edge_cuts
text_thickness through_hole_pad_without_hole too_many_vias track_angle track_dangling
track_not_centered_on_via track_on_post_machined_layer track_segment_length track_width tracks_crossing
tuning_profile_track_geometries unconnected_items unresolved_variable via_dangling via_diameter
zones_intersect'''.split())

# What DRC 0 on a generated board does and does not show (A-PCB plan notes); copied into every report.
NOT_PROVED = [
    'that the schematic is right',
    'current capacity or temperature rise beyond the chosen class widths',
    'impedance, RF loss or isolation, EMC or signal integrity',
    'creepage beyond the encoded clearances',
    'that the enclosure fits (only outline and hole checks; heights are not checked here)',
    "that the fab's DFM accepts the board, or that CPL rotations are right",
    'that the land patterns match the purchased MPNs',
    'any function: hardware and bench gates stay OPEN',
]


class SpecError(SystemExit):
    """A spec, contract or graph inconsistency: the board cannot be generated."""

    def __init__(self, message):
        super().__init__('board_gen: ' + message)


# --- small helpers -----------------------------------------------------------------------------------

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def rel(path):
    return Path(path).resolve().relative_to(BASE).as_posix()


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data if isinstance(data, bytes) else data.encode('utf-8'))
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def r4(value):
    """Round a millimetre value for reports (KiCad stores nanometres)."""
    out = round(float(value), 4)
    return 0.0 if out == 0 else out


def sort_ref(ref):
    m = re.fullmatch(r'([^0-9]*)([0-9]+)(.*)', ref)
    return (m[1], int(m[2]), m[3]) if m else (ref, -1, '')


# --- commit token, Freerouting command ---------------------------------------------------------------

def route_requested(message, board):
    """True when the subject (first line) of the commit message carries '[pcb-route <board>]'.

    The body never counts, and neither does the subject of a 'GENERATED: ...' commit: a GENERATED
    commit that quotes the token of its route run is checked, not routed again.
    """
    lines = (message or '').splitlines()
    subject = lines[0].strip() if lines else ''
    if subject.startswith('GENERATED:'):
        return False
    return board in ROUTE_TOKEN.findall(subject)


def outside_repository(path):
    """True when path is outside the git work tree (fetch-only tools must never be inside it)."""
    path = Path(path).resolve()
    return path != REPO_ROOT and REPO_ROOT not in path.parents


def router_extra(router):
    """Optional Freerouting arguments of a spec router block (W2 PCB-PWRB; docs/settings.md and
    docs/command_line_arguments.md at v2.5.0): 'fanout': false turns the SMD fan-out pre-pass off
    (--router.fanout.enabled=false); 'ignore_net_classes' [names] are not autorouted (-inc), for nets whose
    copper is all scripted and locked (the router does not count locked copper that crosses a pad as a connection)."""
    extra = []
    if 'fanout' in router:
        if not isinstance(router['fanout'], bool):
            raise SpecError('router.fanout must be true or false')
        extra.append(f'--router.fanout.enabled={str(router["fanout"]).lower()}')
    names = router.get('ignore_net_classes') or []
    if names:
        if not all(isinstance(n, str) and re.fullmatch(r'[A-Za-z0-9_]+', n) for n in names):
            raise SpecError('router.ignore_net_classes must be net class names ([A-Za-z0-9_])')
        extra += ['-inc', ','.join(names)]
    return extra


def freerouting_command(java, jar, dsn, ses, max_passes, threads, user_dir, job_timeout, extra=()):
    """Headless Freerouting call: analytics off (-da), no GUI, optimizer on one thread (-mt), bounded job."""
    if int(max_passes) < 1 or int(threads) < 1:
        raise SpecError('router.max_passes and router.threads must be >= 1')
    if not re.fullmatch(r'\d{2}:\d{2}:\d{2}', str(job_timeout)):
        raise SpecError('router.job_timeout must be HH:MM:SS')
    # -mt alone left optimizer.max_threads at 3 in the first JAR run (log of run 42389363266), so the canonical
    # key is passed too; automatic neckdown off keeps every routed track at its net-class width.
    return [str(java), '-Djava.awt.headless=true', '-cp', str(jar), FREEROUTING['main_class'],
            '-de', str(dsn), '-do', str(ses), f'--router.autorouter.max_passes={int(max_passes)}', '-mt', str(int(threads)),
            f'--router.optimizer.max_threads={int(threads)}', '--router.automatic_neckdown=false',
            '-da', '--gui.enabled=false', f'--router.job_timeout={job_timeout}', '--logging.file.enabled=false',
            f'--user_data_path={user_dir}'] + [str(a) for a in extra]


def _download(item, dest):
    with urllib.request.urlopen(item['url'], timeout=300) as response:  # default urllib User-Agent
        data = response.read()
    digest = sha256_bytes(data)
    if digest != item['sha256']:
        raise SpecError(f'{item["name"]} download SHA256 mismatch: {digest} != {item["sha256"]}')
    print(f'{item["name"]} {item["version"]} sha256 match: {digest} ({len(data)} bytes)')
    path = dest / PurePosixPath(item['url']).name.replace('%2B', '+')
    path.write_bytes(data)
    return path


def fetch_freerouting(dest):
    """Download the pinned Freerouting JAR and Temurin JRE outside the work tree; verify both SHA256s.

    Fetch-only: nothing lands in the repository, the bundle or a CI artifact.
    """
    dest = Path(dest).resolve()
    if not outside_repository(dest):
        raise SpecError('Freerouting must be fetched outside the repository (fetch-only, never committed)')
    dest.mkdir(parents=True, exist_ok=True)
    jar = _download(FREEROUTING, dest)
    archive = _download(TEMURIN_JRE, dest)
    jre = dest / 'jre'
    if jre.exists():
        shutil.rmtree(jre)
    with tarfile.open(archive, 'r:gz') as tar:
        tar.extractall(jre, filter='data')
    java = java_in(dest)
    proc = run([java, '-version'], timeout=120)
    print((proc.stdout + proc.stderr).strip())
    print(f'Freerouting: {jar}; Java: {java}')
    return jar, java


def java_in(dest):
    found = sorted(Path(dest, 'jre').glob('*/bin/java'))
    if len(found) != 1:
        raise SpecError(f'no single JRE under {dest}/jre')
    return found[0]


# --- footprint text (.kicad_mod) ---------------------------------------------------------------------

def sexpr(text):
    """Parse a KiCad S-expression into nested lists of strings."""
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text)
    stack = [[]]
    for tok in tokens:
        if tok == '(':
            stack.append([])
        elif tok == ')':
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(tok[1:-1] if tok.startswith('"') else tok)
    if len(stack) != 1 or len(stack[0]) != 1:
        raise ValueError('unbalanced S-expression')
    return stack[0][0]


def footprint_geometry(text):
    """Pads and courtyard box of a .kicad_mod in footprint coordinates (KiCad, y down)."""
    tree = sexpr(text)
    pads, crtyd = [], []
    for node in tree[1:]:
        if not isinstance(node, list) or not node:
            continue
        if node[0] == 'pad':
            at = next(n for n in node if isinstance(n, list) and n[0] == 'at')
            size = next(n for n in node if isinstance(n, list) and n[0] == 'size')
            drill = next((n for n in node if isinstance(n, list) and n[0] == 'drill'), None)
            pads.append({'number': node[1], 'type': node[2], 'at': [float(at[1]), float(at[2])],
                         'size': [float(size[1]), float(size[2])],
                         # (drill (offset x y)) of an SMD pad (Pico castellations, W2 PCB-CTRL) has no size atom: skip sub-lists
                         'drill': [float(x) for x in drill[1:] if isinstance(x, str) and re.fullmatch(r'-?[\d.]+', x)]
                         if drill else []})
        elif node[0] in ('fp_line', 'fp_rect', 'fp_circle', 'fp_poly', 'fp_arc'):
            layer = next((n[1] for n in node if isinstance(n, list) and n[0] == 'layer'), '')
            if layer != 'F.CrtYd':
                continue
            pts = []

            def walk(n):
                if isinstance(n, list) and n and n[0] in ('start', 'end', 'xy', 'mid', 'center'):
                    pts.append((float(n[1]), float(n[2])))
                elif isinstance(n, list):
                    for m in n:
                        walk(m)
            walk(node)
            if node[0] == 'fp_circle':
                (cx, cy), (ex, ey) = pts[0], pts[1]
                r = math.hypot(ex - cx, ey - cy)
                pts = [(cx - r, cy - r), (cx + r, cy + r)]
            crtyd.extend(pts)
    box = None
    if crtyd:
        xs, ys = [p[0] for p in crtyd], [p[1] for p in crtyd]
        box = [min(xs), min(ys), max(xs), max(ys)]
    return {'pads': pads, 'courtyard': box}


def rotate_box(box, degrees):
    """Courtyard box after a KiCad rotation (multiple of 90 degrees, footprint coordinates)."""
    x0, y0, x1, y1 = box
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    turns = int(round(degrees / 90.0)) % 4
    if abs(degrees - 90 * round(degrees / 90.0)) > 1e-9:
        raise SpecError(f'only multiples of 90 degrees are packed, got {degrees}')
    for _ in range(turns):  # KiCad RotatePoint by +90: (x, y) -> (y, -x)
        corners = [(y, -x) for x, y in corners]
    xs, ys = [c[0] for c in corners], [c[1] for c in corners]
    return [min(xs), min(ys), max(xs), max(ys)]


# --- deterministic placement helpers ------------------------------------------------------------------

class PackError(SpecError):
    pass


def shelf_pack(items, region, gap=0.5):
    """Pack courtyard rectangles into region [x0, y0, x1, y1] (board mm, y up).

    items: [{'ref', 'w', 'h'}]. Order: taller first, then by reference (deterministic). Shelves fill
    left to right from the top edge of the region downwards. Returns {ref: (cx, cy)} centres.
    """
    x0, y0, x1, y1 = region
    if x1 <= x0 or y1 <= y0:
        raise PackError(f'empty region {region}')
    order = sorted(items, key=lambda it: (-round(it['h'], 6), sort_ref(it['ref'])))
    out, x, top, shelf_h = {}, x0, y1, 0.0
    for it in order:
        w, h = float(it['w']), float(it['h'])
        if w > x1 - x0 or h > y1 - y0:
            raise PackError(f'{it["ref"]} ({w} x {h}) does not fit region {region}')
        if x + w > x1 + 1e-9:
            top -= shelf_h + gap
            x, shelf_h = x0, 0.0
        if top - h < y0 - 1e-9:
            raise PackError(f'region {region} is full at {it["ref"]}')
        out[it['ref']] = (r4(x + w / 2), r4(top - h / 2))
        x += w + gap
        shelf_h = max(shelf_h, h)
    return out


def rects_overlap(a, b, gap=0.0):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])


def place_near(size, pin, body, placed, region, max_mm, gap=0.25):
    """Put a w x h part next to pin (x, y) outside body [x0, y0, x1, y1]; nearest free side first.

    Returns ((cx, cy), distance from the pin to the part's near edge). Raises PackError when no side
    within max_mm is free. Used for decoupling capacitors (pin-to-part distance <= 2 mm by default).
    """
    w, h = size
    px, py = pin
    # (side, part centre, distance from the pin to the part's near edge)
    candidates = [
        ('left', (body[0] - gap - w / 2, py), px - (body[0] - gap)),
        ('right', (body[2] + gap + w / 2, py), (body[2] + gap) - px),
        ('below', (px, body[1] - gap - h / 2), py - (body[1] - gap)),
        ('above', (px, body[3] + gap + h / 2), (body[3] + gap) - py),
    ]
    candidates.sort(key=lambda c: (abs(c[2]), c[0]))
    for _side, (cx, cy), dist in candidates:
        rect = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]
        if rect[0] < region[0] - 1e-9 or rect[1] < region[1] - 1e-9 or rect[2] > region[2] + 1e-9 or rect[3] > region[3] + 1e-9:
            continue
        if any(rects_overlap(rect, other, gap) for other in placed):
            continue
        if abs(dist) > max_mm + 1e-9:
            continue
        return (r4(cx), r4(cy)), r4(abs(dist))
    raise PackError(f'no free side within {max_mm} mm of pin {pin}')


def turn_point(point, degrees):
    """A footprint-local point (KiCad, y down) after a KiCad rotation by a multiple of 90 degrees."""
    if abs(degrees - 90 * round(degrees / 90.0)) > 1e-9:
        raise SpecError(f'only multiples of 90 degrees are packed, got {degrees}')
    x, y = point
    for _ in range(int(round(degrees / 90.0)) % 4):  # KiCad RotatePoint by +90: (x, y) -> (y, -x)
        x, y = y, -x
    return x, y


def placed_geometry(geo, anchor):
    """Courtyard box and pad centres (board mm, y up) of a footprint placed by an anchor.

    Mirrors place(): rotation, then a left-right flip for side B (KiCad FOOTPRINT::Flip mirrors x about
    the footprint position), then the align point (origin, one pad or a pad centroid) onto anchor 'at'.
    """
    rotation = float(anchor.get('rotation', 0))
    flip = anchor.get('side', 'F') == 'B'

    def local(pt):
        x, y = turn_point(pt, rotation)
        return (-x if flip else x), y
    pads = [(str(p['number']), local(p['at'])) for p in geo['pads']]
    align = anchor.get('align', 'origin')
    if align == 'origin':
        ax, ay = 0.0, 0.0
    else:
        want = str(align['pad'] if 'pad' in align else align['pad_centroid'])
        pts = [xy for num, xy in pads if num == want]
        if not pts:
            raise SpecError(f'anchor pad {want} not in footprint')
        ax, ay = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    bx, by = (float(v) for v in anchor['at'])

    def board(pt):
        return (r4(bx + pt[0] - ax), r4(by - (pt[1] - ay)))
    box = None
    if geo['courtyard']:
        x0, y0, x1, y1 = geo['courtyard']
        corners = [board(local(c)) for c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        box = [min(c[0] for c in corners), min(c[1] for c in corners), max(c[0] for c in corners),
               max(c[1] for c in corners)]
    out_pads = {}
    for num, xy in pads:
        if num:
            out_pads.setdefault(num, []).append(list(board(xy)))
    return {'origin': list(board((0.0, 0.0))), 'box': box, 'pads': out_pads}


def point_in_outline(point, outline, eps=1e-6):
    """Point inside the board outline polygon (board mm); points on an edge count as inside."""
    px, py = point
    inside = False
    for (x1, y1), (x2, y2) in zip(outline, outline[1:] + outline[:1]):
        cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
        if abs(cross) <= eps * max(1.0, math.hypot(x2 - x1, y2 - y1)) and \
                min(x1, x2) - eps <= px <= max(x1, x2) + eps and min(y1, y2) - eps <= py <= max(y1, y2) + eps:
            return True
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def cutout_boxes(contract):
    """Contract cutouts [x, y, w, h] (board mm, as pcb/check_boards.py reads them) as boxes [x0, y0, x1, y1]."""
    return [[float(x), float(y), float(x) + float(w), float(y) + float(h)]
            for x, y, w, h in (contract.get('cutouts_mm') or [])]


def place_groups(spec, template, geometry, hole_list, outline, cutouts=()):
    """Anchors for the parts that the spec's placement groups place (deterministic, standard library).

    geometry: {template ref: footprint_geometry()} for every template part. Anchored parts are fixed
    obstacles. Groups run in spec order. In each group the members without 'decouple' are shelf-packed
    into the region (courtyard boxes after rotation and side); then every decoupling member goes next to
    its pin ({ref, pad, max_mm}) with place_near, nearest free side first, at most max_mm from the pin.
    A placed courtyard box must not overlap another part on the same side, a contract cutout (cutouts:
    boxes [x0, y0, x1, y1], cutout_boxes()) or enter a hole keepout; a region must not overlap a cutout.
    Returns ({ref: anchor}, rows); rows carry the plan that the KiCad group audit checks.
    """
    placed = {}
    for part in template:
        if part.get('anchor'):
            placed[part['ref']] = {'side': part['anchor'].get('side', 'F'),
                                   **placed_geometry(geometry[part['ref']], part['anchor'])}
    anchors, rows = {}, []

    def put(group, member, side, rotation, centre, local_box, decouple=None, target=None):
        lcx, lcy = (local_box[0] + local_box[2]) / 2, (local_box[1] + local_box[3]) / 2
        anchor = {'at': [r4(centre[0] - lcx), r4(centre[1] + lcy)], 'align': 'origin', 'rotation': rotation,
                  'side': side}
        geo = placed_geometry(geometry[member['ref']], anchor)
        for ref, other in placed.items():
            if ref != target and other['side'] == side and other['box'] and rects_overlap(geo['box'], other['box']):
                raise PackError(f'group {group["id"]}: {member["ref"]} overlaps {ref}')
        for hole in hole_list:
            if box_circle_distance(geo['box'], hole['at']) < hole['keepout_d'] / 2:
                raise PackError(f'group {group["id"]}: {member["ref"]} enters the keepout of {hole["ref"]}')
        for cut in cutouts:
            if rects_overlap(geo['box'], cut):
                raise PackError(f'group {group["id"]}: {member["ref"]} overlaps the cutout {cut}')
        placed[member['ref']] = {'side': side, **geo}
        anchors[member['ref']] = anchor
        rows.append({'group': group['id'], 'ref': member['ref'], 'side': side, 'rotation': rotation,
                     'at': anchor['at'], 'courtyard_box': geo['box'], 'region': group['region'],
                     'decouple': decouple})

    for group in spec.get('groups', []):
        side = group.get('side', 'F')
        region = [float(v) for v in group['region']]
        corners = ((region[0], region[1]), (region[2], region[1]), (region[2], region[3]), (region[0], region[3]))
        if not all(point_in_outline(c, outline) for c in corners):
            raise SpecError(f'group {group["id"]}: region {region} is not inside the board outline')
        if any(rects_overlap(region, cut) for cut in cutouts):
            raise SpecError(f'group {group["id"]}: region {region} overlaps a contract cutout')
        local_boxes, items = {}, []
        for member in group['members']:
            geo = geometry[member['ref']]
            if not geo['courtyard']:
                raise SpecError(f'group {group["id"]}: {member["ref"]} footprint has no courtyard')
            box = rotate_box(geo['courtyard'], float(member.get('rotation', 0)))
            local_boxes[member['ref']] = [-box[2], box[1], -box[0], box[3]] if side == 'B' else box
            if 'decouple' not in member:
                b = local_boxes[member['ref']]
                items.append({'ref': member['ref'], 'w': b[2] - b[0], 'h': b[3] - b[1]})
        centres = shelf_pack(items, region, float(group.get('gap_mm', 0.5))) if items else {}
        members = {m['ref']: m for m in group['members']}
        for ref in sorted(centres, key=sort_ref):
            put(group, members[ref], side, float(members[ref].get('rotation', 0)), centres[ref], local_boxes[ref])
        for member in group['members']:
            dec = member.get('decouple')
            if not dec:
                continue
            target = placed.get(dec['ref'])
            if target is None or target['side'] != side:
                raise SpecError(f'group {group["id"]}: decoupling target {dec["ref"]} of {member["ref"]} is not '
                                f'placed on side {side} before it')
            pins = target['pads'].get(str(dec['pad']), [])
            if len(pins) != 1:
                raise SpecError(f'group {group["id"]}: {dec["ref"]} pad {dec["pad"]} must be exactly one pad')
            b = local_boxes[member['ref']]
            others = [o['box'] for r, o in placed.items() if r != dec['ref'] and o['side'] == side and o['box']]
            max_mm = float(dec.get('max_mm', 2.0))
            centre, dist = place_near((b[2] - b[0], b[3] - b[1]), tuple(pins[0]), target['box'], others, region,
                                      max_mm, float(group.get('decouple_gap_mm', 0.25)))
            put(group, member, side, float(member.get('rotation', 0)), centre, b,
                {'ref': dec['ref'], 'pad': str(dec['pad']), 'max_mm': max_mm, 'planned_distance_mm': dist},
                target=dec['ref'])
    return anchors, rows


# --- inputs: spec, contract, graph, footprints --------------------------------------------------------

def spec_path(board):
    return SPEC_DIR / f'{board}.json'


def list_boards():
    out = []
    for path in sorted(SPEC_DIR.glob('*.json')):
        spec = read_json(path)
        if spec.get('board_id') != path.stem:
            raise SpecError(f'{rel(path)}: board_id {spec.get("board_id")!r} must equal the file name')
        out.append(path.stem)
    return out


def load_graph():
    comps = {}
    for path in GRAPHS:
        sheet = read_json(path)
        for comp in sheet['components']:
            if comp['ref'] in comps:
                raise SpecError('duplicate graph ref ' + comp['ref'])
            comps[comp['ref']] = {**comp, '_sheet': sheet['sheet']}
    return comps


def net_nodes(graph):
    nodes = {}
    for ref, comp in graph.items():
        for pin in comp['pins']:
            if pin.get('net'):
                nodes.setdefault(pin['net'], []).append((ref, str(pin['number'])))
    return nodes


def parts_by_ref():
    db = read_json(PARTS_DB)
    return {r: p for p in db['parts'] for r in p['refs']}


def hosted_contacts(db):
    """Virtual contacts (mount 'virtual') and the board ref hosting each (parts DB 'host')."""
    out = {}
    for ref, part in db.items():
        host = part.get('host')
        if part.get('mount') == 'virtual' and isinstance(host, dict) and host.get(ref):
            out[ref] = host[ref]
    return out


def image_library_dir():
    for candidate in (os.environ.get('KICAD10_FOOTPRINT_DIR', ''), '/usr/share/kicad/footprints',
                      '/usr/local/share/kicad/footprints'):
        if candidate and Path(candidate, 'Resistor_SMD.pretty').is_dir():
            return Path(candidate)
    return None


def validate_groups(spec, board, refs):
    """Placement groups: {id, region [x0, y0, x1, y1] board mm, side F/B, gap_mm?, decouple_gap_mm?,
    members [{ref, rotation?, decouple?: {ref, pad, max_mm?}}]}. Returns {member ref: group id}.

    A member is a template graph part without an anchor, in one group only. A decoupling target must be
    an anchored part or a packed member of this or an earlier group, on the same side.
    """
    if not isinstance(spec['groups'], list):
        raise SpecError(f'{board}: groups must be a list')
    sides = {p['ref']: p['anchor'].get('side', 'F') for p in spec['parts'] if p.get('anchor')}
    grouped, ids = {}, set()
    for group in spec['groups']:
        gid = group.get('id')
        if not gid or gid in ids:
            raise SpecError(f'{board}: every group needs a unique id ({gid!r})')
        ids.add(gid)
        region = group.get('region', [])
        if len(region) != 4 or not all(isinstance(v, (int, float)) for v in region) or \
                region[2] <= region[0] or region[3] <= region[1]:
            raise SpecError(f'{board}: group {gid} region must be [x0, y0, x1, y1] with x1 > x0 and y1 > y0')
        side = group.get('side', 'F')
        if side not in ('F', 'B'):
            raise SpecError(f'{board}: group {gid} side must be F or B')
        members = group.get('members') or []
        if not members:
            raise SpecError(f'{board}: group {gid} has no members')
        for member in members:
            ref = member.get('ref')
            if ref not in refs:
                raise SpecError(f'{board}: group {gid} member {ref!r} is not a template ref')
            if ref in grouped:
                raise SpecError(f'{board}: {ref} is in groups {grouped[ref]} and {gid}')
            grouped[ref] = gid
            rotation = float(member.get('rotation', 0))
            if abs(rotation - 90 * round(rotation / 90.0)) > 1e-9:
                raise SpecError(f'{board}: group {gid} member {ref} rotation must be a multiple of 90')
        for member in members:
            if 'decouple' not in member:
                sides[member['ref']] = side
        for member in members:
            dec = member.get('decouple')
            if dec is None:
                continue
            if not isinstance(dec, dict) or dec.get('ref') == member['ref'] or 'pad' not in dec or \
                    float(dec.get('max_mm', 2.0)) <= 0:
                raise SpecError(f'{board}: group {gid} member {member["ref"]} decouple needs ref, pad and max_mm > 0')
            if sides.get(dec['ref']) != side:
                raise SpecError(f'{board}: group {gid}: decoupling target {dec["ref"]} of {member["ref"]} must be '
                                f'anchored or packed before it, on side {side}')
        for member in members:
            if 'decouple' in member:
                sides[member['ref']] = side
    return grouped


def validate_spec(spec, board):
    need = ('schema', 'board_id', 'status', 'contract', 'domains', 'layers', 'project', 'instances', 'parts',
            'holes', 'groups', 'pre_route', 'post_route_zones', 'router', 'drc_policy', 'fab_floor')
    missing = [k for k in need if k not in spec]
    if missing:
        raise SpecError(f'{board}: spec lacks {missing}')
    if spec['schema'] != SPEC_SCHEMA or spec['board_id'] != board:
        raise SpecError(f'{board}: schema must be {SPEC_SCHEMA} and board_id {board}')
    if spec['layers']['copper'] not in (2, 4):
        raise SpecError(f'{board}: copper layers must be 2 or 4')
    if spec.get('rules_file') is not None:
        raise SpecError(f'{board}: rules_file is set, but copying it into build/kicad/boards/{board}/{board}.kicad_dru '
                        '(and hashing it) is not implemented in board_gen yet; keep it null')
    refs = [p['ref'] for p in spec['parts']]
    if len(refs) != len(set(refs)):
        raise SpecError(f'{board}: duplicate template ref')
    grouped = validate_groups(spec, board, refs)
    inst = spec['instances']
    if not inst['list']:
        raise SpecError(f'{board}: at least one instance')
    nets = set(inst['template_nets'])
    for item in inst['list']:
        if set(item['nets']) != nets:
            raise SpecError(f'{board}: instance {item["id"]} must map exactly the template nets {sorted(nets)}')
        if len(set(item['nets'].values())) != len(item['nets']):
            raise SpecError(f'{board}: instance {item["id"]} maps two template nets onto one graph net')
        if set(item['refs']) != set(refs):
            raise SpecError(f'{board}: instance {item["id"]} must map every template ref')
        if not isinstance(item.get('qty'), int) or item['qty'] < 1:
            raise SpecError(f'{board}: instance {item["id"]} needs qty >= 1')
    for part in spec['parts']:
        if part['source'] not in ('graph', 'pilot_placeholder'):
            raise SpecError(f'{board}: part {part["ref"]} source must be graph or pilot_placeholder')
        for item in inst['list']:
            graph_ref = item['refs'][part['ref']]
            if (part['source'] == 'graph') != bool(graph_ref):
                raise SpecError(f'{board}: {item["id"]}.{part["ref"]}: graph parts need a ref, placeholders none')
        if part['source'] == 'pilot_placeholder':
            for key in ('footprint', 'footprint_library', 'footprint_sha256', 'value', 'pins', 'replaced_by', 'pending'):
                if key not in part:
                    raise SpecError(f'{board}: placeholder {part["ref"]} lacks {key}')
            if not str(part['pending']).strip():
                raise SpecError(f'{board}: placeholder {part["ref"]} needs a pending text (boundary audit status)')
            bad = sorted(set(part['pins'].values()) - nets)
            if bad:
                raise SpecError(f'{board}: placeholder {part["ref"]} uses unknown nets {bad}')
        if part['ref'] in grouped:
            if 'anchor' in part:
                raise SpecError(f'{board}: part {part["ref"]} is placed by group {grouped[part["ref"]]} and has an anchor')
            if part['source'] == 'pilot_placeholder':
                raise SpecError(f'{board}: placeholder {part["ref"]} needs an anchor, not a group')
            continue
        anchor = part.get('anchor')
        if not anchor or anchor.get('side', 'F') not in ('F', 'B') or len(anchor.get('at', [])) != 2:
            raise SpecError(f'{board}: part {part["ref"]} needs an anchor with at [x, y] and side F/B')
    for track in spec['pre_route'].get('tracks', []):
        if track['net'] not in nets or len(track['path']) < 2 or track['width_mm'] <= 0:
            raise SpecError(f'{board}: pre-route track {track.get("id")} is malformed')
    for zone in spec['post_route_zones'] + spec['pre_route'].get('zones', []):
        if zone['net'] not in nets:
            raise SpecError(f'{board}: zone {zone.get("id")} on unknown net {zone["net"]}')
        if zone.get('pad_connection', 'thermal') not in ZONE_PAD_CONNECTIONS:
            raise SpecError(f'{board}: zone {zone.get("id")} pad_connection must be one of {sorted(ZONE_PAD_CONNECTIONS)}')
    for via in spec['pre_route'].get('vias', []):
        at = via.get('at', [])
        if via.get('net') not in nets or len(at) != 2 or not all(isinstance(v, (int, float)) for v in at) or \
                not 0 < float(via.get('drill_mm', 0)) < float(via.get('diameter_mm', 0)):
            raise SpecError(f'{board}: pre-route via {via.get("id")} needs a template net, at [x, y] and '
                            '0 < drill_mm < diameter_mm')
    copper = [f'In{i}.Cu' for i in range(1, int(spec['layers']['copper']) - 1)] + ['F.Cu', 'B.Cu']
    router_extra(spec['router'])
    edge = spec.get('edge_keepout')
    if edge is not None and (not isinstance(edge, dict) or float(edge.get('width_mm', 0)) <= 0
                             or not set(edge.get('layers', [])) <= set(copper) or not edge.get('layers')
                             or not set(edge.get('blocks', [])) <= {'tracks', 'vias'} or not edge.get('blocks')):
        raise SpecError(f'{board}: edge_keepout needs width_mm > 0, copper layers and blocks (tracks, vias)')
    for layer, kind in (spec['layers'].get('types') or {}).items():
        if layer not in copper or kind not in LAYER_TYPES:
            raise SpecError(f'{board}: layers.types {layer!r}: {kind!r} must name a copper layer of the board and one '
                            f'of {sorted(LAYER_TYPES)}')
    for cls, layers in (spec['router'].get('class_layers') or {}).items():
        if not re.fullmatch(r'[A-Za-z0-9_]+', str(cls)) or not isinstance(layers, list) or not layers \
                or not set(layers) <= set(copper):
            raise SpecError(f'{board}: router.class_layers {cls}: {layers!r} must list copper layers of the board')
    reserved = spec['router'].get('class_layers_reserved')
    if reserved is not None and (not isinstance(reserved, list) or
                                 not set(reserved) <= set(spec['router'].get('class_layers') or {})):
        raise SpecError(f'{board}: router.class_layers_reserved must list classes of router.class_layers')
    if not isinstance(spec.get('audit_cutouts', False), bool):
        raise SpecError(f'{board}: audit_cutouts must be true or false')
    for key, reason in spec['drc_policy'].get('warning_checks', {}).items():
        if key not in DRC_KEYS or not reason.strip():
            raise SpecError(f'{board}: drc_policy warning {key!r} is not a KiCad 10.0.7 check or has no reason')
    validate_bond_and_coupon(spec, board, nets)


def validate_bond_and_coupon(spec, board, nets):
    """Optional spec keys of W2 PCB-RF-2 (standard library).

    bond_hole {at [x, y], net, pad_mm, why}: the contract hole at `at` becomes a plated hole with a pad_mm land on
    every copper layer, on a template net (the BOND-RF chassis bond); its keepout rule areas are left out, so only
    the land's own copper sits there (pcb/check_boards.py bond_hole: only the BOND-RF hole may be plated or netted).
    coupon {why, outlines [[x0, y0, x1, y1]] board mm outside the outline, footprints [{ref, footprint (manifest),
    value, pads {pad: template net}, anchor}], tracks, vias (pre_route forms), zones (post_route_zones form with an
    explicit outline)}: test-coupon copper drawn after the SES import, so the router never sees it; its footprints
    are board-only, excluded from the position files and the BOM.
    """
    bond = spec.get('bond_hole')
    if bond is not None:
        if not isinstance(bond, dict) or len(bond.get('at', [])) != 2 or bond.get('net') not in nets or \
                not float(bond.get('pad_mm', 0)) > 0 or not str(bond.get('why', '')).strip():
            raise SpecError(f'{board}: bond_hole needs at [x, y], a template net, pad_mm > 0 and why')
    coupon = spec.get('coupon')
    if coupon is None:
        return
    if not isinstance(coupon, dict) or not coupon.get('outlines') or not str(coupon.get('why', '')).strip():
        raise SpecError(f'{board}: coupon needs outlines and why')
    for box in coupon['outlines']:
        if len(box) != 4 or not (box[2] > box[0] and box[3] > box[1]):
            raise SpecError(f'{board}: coupon outline {box} must be [x0, y0, x1, y1] with x1 > x0, y1 > y0')
    refs = {p['ref'] for p in spec['parts']}
    for item in coupon.get('footprints', []):
        if item.get('ref') in refs or not item.get('footprint') or not isinstance(item.get('pads'), dict) or \
                not item.get('anchor') or len(item['anchor'].get('at', [])) != 2:
            raise SpecError(f'{board}: coupon footprint {item.get("ref")} needs a new ref, footprint, pads and anchor')
        bad = sorted(set(item['pads'].values()) - nets)
        if bad:
            raise SpecError(f'{board}: coupon footprint {item["ref"]} uses unknown nets {bad}')
    for item in coupon.get('tracks', []) + coupon.get('vias', []) + coupon.get('zones', []):
        if item.get('net') not in nets:
            raise SpecError(f'{board}: coupon item {item.get("id")} on unknown net {item.get("net")}')
    for zone in coupon.get('zones', []):
        if not isinstance(zone.get('outline'), list) or zone.get('pad_connection', 'thermal') not in ZONE_PAD_CONNECTIONS:
            raise SpecError(f'{board}: coupon zone {zone.get("id")} needs an explicit outline and a known pad_connection')


def load_contract(spec):
    contract = read_json(BASE / spec['contract']['file'])
    entry = contract['boards'].get(spec['contract']['board'])
    if entry is None:
        raise SpecError('contract has no board ' + spec['contract']['board'])
    return entry, contract.get('stackup', {})


def check_project(spec, project):
    """The committed .kicad_pro: every DRC key reviewed, warnings match the policy, rules above the fab floor."""
    sev = project['board']['design_settings']['rule_severities']
    problems = []
    unknown = sorted(set(sev) - DRC_KEYS)
    missing = sorted(DRC_KEYS - set(sev))
    if unknown or missing:
        problems.append(f'rule_severities: unknown {unknown}, missing {missing}')
    ignored = sorted(k for k, v in sev.items() if v == 'ignore')
    if ignored:
        problems.append(f'checks set to ignore: {ignored}')
    warn = sorted(k for k, v in sev.items() if v == 'warning')
    policy = sorted(spec['drc_policy'].get('warning_checks', {}))
    if warn != policy:
        problems.append(f'warning severities {warn} differ from the reviewed drc_policy {policy}')
    floor = spec['fab_floor']
    rules = project['board']['design_settings']['rules']
    classes = project['net_settings']['classes']
    pairs = [('min_track_width', rules.get('min_track_width'), floor['min_track_width']),
             ('min_clearance', rules.get('min_clearance'), floor['min_clearance']),
             ('min_through_hole_diameter', rules.get('min_through_hole_diameter'), floor['min_drill']),
             ('min_via_diameter', rules.get('min_via_diameter'), floor['min_via_diameter']),
             ('min_hole_to_hole', rules.get('min_hole_to_hole'), floor['min_hole_to_hole']),
             ('min_copper_edge_clearance', rules.get('min_copper_edge_clearance'), floor['min_copper_edge_clearance']),
             ('min_text_height', rules.get('min_text_height'), floor['min_text_height']),
             ('min_text_thickness', rules.get('min_text_thickness'), floor['min_text_thickness'])]
    for cls in classes:
        pairs += [(f'class {cls["name"]} track_width', cls['track_width'], floor['min_track_width']),
                  (f'class {cls["name"]} clearance', cls['clearance'], floor['min_clearance']),
                  (f'class {cls["name"]} via_drill', cls['via_drill'], floor['min_drill']),
                  (f'class {cls["name"]} via_diameter', cls['via_diameter'], floor['min_via_diameter'])]
    for name, value, minimum in pairs:
        if value is None or float(value) + 1e-9 < float(minimum):
            problems.append(f'{name} {value} is below the fab floor {minimum}')
    return problems


def resolve(spec, graph, manifest):
    """Template parts with neutral pad nets, checked for every instance against the graph.

    Graph parts take footprint, value and pin nets from design/E*.json; each instance maps template
    nets to graph nets. All instances must yield the same neutral pad nets (one design built N times).
    """
    fps = {f['footprint']: f for f in manifest['footprints']}
    inst = spec['instances']['list']
    template = []
    for part in spec['parts']:
        if part['source'] == 'pilot_placeholder':
            template.append({'ref': part['ref'], 'source': part['source'], 'fpid': part['footprint'],
                             'library': part['footprint_library'], 'file': None,
                             'sha256': part['footprint_sha256'], 'value': part['value'],
                             'pads': {str(k): v for k, v in sorted(part['pins'].items())},
                             'unused_pads': [], 'anchor': part['anchor'], 'pending': part.get('pending', '')})
            continue
        resolved = None
        for item in inst:
            gref = item['refs'][part['ref']]
            comp = graph.get(gref)
            if comp is None:
                raise SpecError(f'{item["id"]}: graph has no ref {gref}')
            fpid = comp.get('footprint', '')
            if fpid not in fps:
                raise SpecError(f'{gref}: footprint {fpid!r} is not in the portable manifest')
            inverse = {}
            for neutral, gnet in item['nets'].items():
                inverse.setdefault(gnet, []).append(neutral)
            pads = {}
            for pin in comp['pins']:
                num = str(pin['number'])
                if pin.get('nc'):
                    pads[num] = None
                    continue
                choices = inverse.get(pin['net'], [])
                if len(choices) != 1:
                    raise SpecError(f'{item["id"]}: {gref}.{num} net {pin["net"]} maps to {choices or "no"} template net')
                pads[num] = choices[0]
            missing = sorted(set(pads) - set(fps[fpid]['pads']))
            if missing:
                raise SpecError(f'{gref}: graph pins {missing} have no pad in {fpid}')
            here = {'fpid': fpid, 'value': comp['value'].strip(), 'pads': dict(sorted(pads.items()))}
            if resolved is None:
                resolved = here
            elif here != resolved:
                raise SpecError(f'{part["ref"]}: instances differ ({item["id"]} {here} vs {resolved}); '
                                'one template cannot serve both')
        fp = fps[resolved['fpid']]
        unused = sorted(set(fp['pads']) - set(resolved['pads']))
        template.append({'ref': part['ref'], 'source': 'graph', 'fpid': resolved['fpid'], 'library': 'project',
                         'file': fp['file'], 'sha256': fp['sha256'], 'value': resolved['value'],
                         'pads': resolved['pads'], 'unused_pads': unused, 'anchor': part.get('anchor')})
    return template


def domain_audit(spec, graph_partition):
    """Every graph ref of the board's domains is covered by an instance, and nothing else is."""
    want = {p['ref'] for p in graph_partition['parts'] if p['board_candidate'] in spec['domains'] and not p['dnp']}
    have = {item['refs'][p['ref']] for item in spec['instances']['list'] for p in spec['parts'] if p['source'] == 'graph'}
    return {'domains': spec['domains'], 'domain_refs': sorted(want, key=sort_ref),
            'missing': sorted(want - have, key=sort_ref), 'foreign': sorted(have - want, key=sort_ref),
            'passed': want == have}


def holes(spec, contract):
    out = []
    if spec['holes'].get('from_contract'):
        d, ko = float(contract['hole_d']), float(contract['hole_keepout_d'])
        for i, (x, y) in enumerate(contract['holes_mm'], 1):
            out.append({'ref': f'{spec["holes"]["ref_prefix"]}{i}', 'at': [float(x), float(y)], 'd': d, 'keepout_d': ko})
    floor = spec['fab_floor']['npth_min_diameter']
    for h in out:
        if h['d'] + 1e-9 < floor:
            raise SpecError(f'hole {h["ref"]} {h["d"]} mm is below the NPTH floor {floor}')
    bond = spec.get('bond_hole')
    if bond:  # the one plated, netted contract hole (W2 PCB-RF-2)
        hit = [h for h in out if math.hypot(h['at'][0] - float(bond['at'][0]), h['at'][1] - float(bond['at'][1])) < 1e-6]
        if len(hit) != 1:
            raise SpecError(f'bond_hole {bond["at"]} is not a contract hole')
        if not hit[0]['d'] < float(bond['pad_mm']) <= hit[0]['keepout_d'] + 1e-9:
            raise SpecError(f'bond_hole pad {bond["pad_mm"]} mm must exceed the hole and stay within its keepout')
        hit[0]['plated'] = {'net': bond['net'], 'pad_mm': float(bond['pad_mm'])}
    return out


def contract_projection(contract, stackup):
    """The contract fields a board depends on (CONTRACT_FIELDS, placements by PLACEMENT_FIELDS) and the stackup."""
    board = {k: contract.get(k) for k in CONTRACT_FIELDS}
    board['placements'] = {name: {k: entry.get(k) for k in PLACEMENT_FIELDS}
                           for name, entry in sorted((contract.get('placements') or {}).items())}
    return {'board': board, 'stackup': stackup}


def projection(spec, contract, stackup, template, graph, project_bytes):
    """Input projection (F10): what the routed copper and the audits depend on, not whole files."""
    instances = []
    for item in spec['instances']['list']:
        parts = []
        for part in template:
            gref = item['refs'][part['ref']]
            if gref:
                comp = graph[gref]
                parts.append({'ref': gref, 'value': comp['value'].strip(), 'footprint': comp.get('footprint', ''),
                              'pins': sorted([str(p['number']), p.get('net'), bool(p.get('nc'))] for p in comp['pins'])})
        instances.append({'id': item['id'], 'refs': item['refs'], 'nets': item['nets'], 'graph': parts})
    contract_part = contract_projection(contract, stackup)
    template_part = [{k: p[k] for k in ('ref', 'source', 'fpid', 'sha256', 'value', 'pads')} for p in template]
    parts = {'spec': sha256_bytes(canonical(spec)), 'contract': sha256_bytes(canonical(contract_part)),
             'project_rules': sha256_bytes(project_bytes), 'template': sha256_bytes(canonical(template_part)),
             'instances': sha256_bytes(canonical(instances))}
    return {'parts': parts, 'sha256': sha256_bytes(canonical(parts))}


def boundary_audit(spec, template, graph, db):
    """Every board net that has graph pins elsewhere must end on a connector pin of this board.

    'connector' = a graph connector ref on this board; 'provisional' = only a pilot placeholder pin
    carries it; 'dangling' = no pin of this board leaves it. Hosted virtual contacts (parts DB host)
    belong to their host part and are listed when their nets reach no host pad.
    """
    nodes = net_nodes(graph)
    hosts = hosted_contacts(db)
    result = []
    for item in spec['instances']['list']:
        on_board = {item['refs'][p['ref']] for p in template if p['source'] == 'graph'}
        hosted = sorted((c for c, h in hosts.items() if h in on_board), key=sort_ref)
        local = on_board | set(hosted)
        nets = []
        for neutral in sorted(spec['instances']['template_nets']):
            gnet = item['nets'][neutral]
            pads = [(p['ref'], num) for p in template for num, n in p['pads'].items() if n == neutral]
            external = sorted({ref for ref, _ in nodes.get(gnet, []) if ref not in local}, key=sort_ref)
            connector = [f'{r}.{n}' for r, n in pads for p in template if p['ref'] == r and p['source'] == 'graph'
                         and (graph[item['refs'][r]]['kind'] == 'connector' or item['refs'][r][:1] in 'JX')]
            placeholder = [f'{r}.{n}' for r, n in pads for p in template if p['ref'] == r and p['source'] == 'pilot_placeholder']
            bond = spec.get('bond_hole')
            if bond and bond['net'] == neutral and not connector:  # the plated bond hole and its screw end the net
                connector = [f'bond_hole {bond["at"]}']
            if not external:
                status = 'internal'
            elif connector:
                status = 'connector'
            elif placeholder:
                status = 'provisional'
            else:
                status = 'dangling'
            nets.append({'net': neutral, 'graph_net': gnet, 'board_pads': [f'{r}.{n}' for r, n in pads],
                         'external_refs': len(external), 'external_sample': external[:6], 'status': status})
        contacts = []
        for c in hosted:
            host = hosts[c]
            host_nets = {p.get('net') for p in graph[host]['pins'] if p.get('net')}
            loose = sorted({p['net'] for p in graph[c]['pins'] if p.get('net')} - host_nets)
            contacts.append({'contact': c, 'host': host, 'nets_not_on_host_pads': loose})
        dangling = [n['net'] for n in nets if n['status'] == 'dangling']
        # The placeholders that carry the provisional nets name what they wait for (spec 'pending').
        pending = sorted({p['pending'] or f'{p["ref"]} placeholder pending' for n in nets if n['status'] == 'provisional'
                          for p in template if p['source'] == 'pilot_placeholder'
                          and any(b.split('.', 1)[0] == p['ref'] for b in n['board_pads'])})
        status = ('fail: dangling ' + ', '.join(dangling) if dangling else
                  'provisional: ' + '; '.join(pending) if pending else 'pass')
        result.append({'instance': item['id'], 'status': status, 'nets': nets, 'hosted_contacts': contacts})
    return result


def drc_summary(raw, policy, project_severities):
    """Split KiCad DRC JSON into errors and reviewed warnings (F14).

    A warning whose check is not in the reviewed policy counts as an error; any ignored check,
    unconnected item or parity item is reported and fails the board.
    """
    items = []
    for section in ('violations', 'unconnected_items', 'schematic_parity'):
        for v in raw.get(section, []):
            items.append({'section': section, 'type': v.get('type', 'unknown'), 'severity': v.get('severity', ''),
                          'description': v.get('description', ''),
                          'items': [{'description': i.get('description', ''),
                                     'pos': [r4(i['pos']['x']), r4(i['pos']['y'])] if 'pos' in i else None}
                                    for i in v.get('items', [])]})
    items.sort(key=lambda v: (v['section'], v['type'], v['description'], json.dumps(v['items'], sort_keys=True)))
    errors = [v for v in items if v['section'] == 'violations' and (v['severity'] != 'warning' or v['type'] not in policy)]
    warnings = [{**v, 'reason': policy[v['type']]} for v in items
                if v['section'] == 'violations' and v['severity'] == 'warning' and v['type'] in policy]
    unconnected = [v for v in items if v['section'] == 'unconnected_items']
    parity = [v for v in items if v['section'] == 'schematic_parity']
    ignored = sorted(c.get('key', c.get('description', '')) if isinstance(c, dict) else str(c)
                     for c in raw.get('ignored_checks', []))
    by_type = {}
    for v in items:
        by_type.setdefault(v['type'], {'severity': v['severity'], 'count': 0})['count'] += 1
    passed = not errors and not unconnected and not parity and not ignored
    return {'errors': len(errors), 'warnings': len(warnings), 'unconnected': len(unconnected),
            'schematic_parity': len(parity), 'ignored_checks': ignored, 'by_type': dict(sorted(by_type.items())),
            'error_items': errors, 'warning_items': warnings, 'unconnected_items': unconnected,
            'severities_reviewed': {'errors': sorted(k for k, v in project_severities.items() if v == 'error'),
                                    'warnings': {k: policy[k] for k in sorted(policy)}},
            'kicad_version': raw.get('kicad_version', ''), 'coordinate_units': raw.get('coordinate_units', ''),
            'passed': passed}


def normalise_drc(raw):
    """Committed DRC JSON without the run date and absolute path, items in a fixed order.

    KiCad runs some DRC providers on several threads, so the marker order is not stable.
    """
    out = {k: v for k, v in raw.items() if k not in ('date', 'source')}
    out['source'] = 'see report.json board_file'
    for section in ('violations', 'unconnected_items', 'schematic_parity'):
        if isinstance(out.get(section), list):
            out[section] = sorted(out[section], key=lambda v: canonical(v))
    return out


def fp_lib_table(template):
    """Project footprint table of a board directory (build/kicad/boards/<B>)."""
    libs = {}
    for part in template:
        nick = part['fpid'].split(':', 1)[0]
        uri = ('${KIPRJMOD}/../../footprints/' + nick + '.pretty' if part['library'] == 'project'
               else '${KICAD10_FOOTPRINT_DIR}/' + nick + '.pretty')
        if libs.setdefault(nick, uri) != uri:
            raise SpecError(f'library {nick} is needed from both the project and the KiCad image')
    lines = ['(fp_lib_table', '  (version 7)']
    for nick, uri in sorted(libs.items()):
        descr = ('SR-RX project footprints (build/kicad/footprints)' if uri.startswith('${KIPRJMOD}')
                 else 'Official KiCad 10.0.7 library of the kicad/kicad:10.0.7 image (pilot placeholder)')
        lines.append(f'  (lib (name "{nick}")(type "KiCad")(uri "{uri}")(options "")(descr "{descr}"))')
    lines.append(')')
    return '\n'.join(lines) + '\n'


def npth_footprint(name, d):
    """Board-only NPTH mounting hole; its courtyard is the hole itself, the keepout is a rule area."""
    r = d / 2
    return f'''(footprint "{name}"
\t(version 20260206)
\t(generator "sr_rx_board_gen")
\t(generator_version "10.0")
\t(layer "F.Cu")
\t(descr "Non-plated mounting hole {d:g} mm from the mechanical contract; copper keepout is a board rule area")
\t(property "Reference" "H" (at 0 {-(r + 1.2):g} 0) (layer "F.SilkS") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
\t(property "Value" "{name}" (at 0 {r + 1.2:g} 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
\t(attr exclude_from_pos_files exclude_from_bom)
\t(fp_circle (center 0 0) (end {r:g} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
\t(fp_circle (center 0 0) (end {r:g} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "B.CrtYd"))
\t(pad "" np_thru_hole circle (at 0 0) (size {d:g} {d:g}) (drill {d:g}) (layers "*.Cu" "*.Mask"))
\t(embedded_fonts no)
)
'''


def edge_strip(a, b, w):
    """Rectangle of half-width w around the edge segment ab, extended by w at both ends (board mm)."""
    (x1, y1), (x2, y2) = a, b
    length = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    nx, ny = -uy * w, ux * w
    p, q = (x1 - ux * w, y1 - uy * w), (x2 + ux * w, y2 + uy * w)
    return [(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)]


def bond_footprint(name, d, pad):
    """Board-only plated mounting hole (spec bond_hole): a pad-diameter land on every copper layer, mask open."""
    r = d / 2
    return f'''(footprint "{name}"
\t(version 20260206)
\t(generator "sr_rx_board_gen")
\t(generator_version "10.0")
\t(layer "F.Cu")
\t(descr "Plated bond hole {d:g} mm with a {pad:g} mm land on every copper layer (spec bond_hole)")
\t(property "Reference" "H" (at 0 {-(pad / 2 + 1.2):g} 0) (layer "F.SilkS") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
\t(property "Value" "{name}" (at 0 {pad / 2 + 1.2:g} 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
\t(attr exclude_from_pos_files exclude_from_bom)
\t(fp_circle (center 0 0) (end {r:g} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
\t(fp_circle (center 0 0) (end {r:g} 0) (stroke (width 0.05) (type solid)) (fill no) (layer "B.CrtYd"))
\t(pad "1" thru_hole circle (at 0 0) (size {pad:g} {pad:g}) (drill {d:g}) (layers "*.Cu" "*.Mask"))
\t(embedded_fonts no)
)
'''


def circle_polygon(cx, cy, radius, n=48):
    """Polygon that contains the circle (circumscribed), board mm."""
    rr = radius / math.cos(math.pi / n)
    return [(cx + rr * math.cos(2 * math.pi * k / n), cy + rr * math.sin(2 * math.pi * k / n)) for k in range(n)]


def patch_dsn_class_layers(text, class_layers, reserved=()):
    """Restrict net classes to routing layers in a KiCad Specctra DSN: '(use_layer ...)' in each class circuit.

    W2 PCB-CTRL (optional spec key router.class_layers {class: [layers]}): KiCad 10.0.7 exports no per-class layer
    list; Freerouting 2.5.0 reads '(circuit (use_layer ...))' of a class (io/specctra/parser/Circuit.java and
    Network.createActiveTraceLayers at tag v2.5.0, read 2026-11-07). Refuses a class that the DSN does not carry,
    except a class named in reserved (optional spec key router.class_layers_reserved, W2 CTRL-5): a class kept in
    class_layers for later members that has no net on the board yet, so KiCad exports no class for it; it is skipped.
    """
    for name, layers in sorted((class_layers or {}).items()):
        pattern = re.compile(r'(\(class\s+' + re.escape(name) + r'\s[^()]*\(circuit)')
        found = len(pattern.findall(text))
        if found == 0 and name in reserved:
            continue
        if found != 1:
            raise SpecError(f'router.class_layers: the DSN has no single class {name}')
        text = pattern.sub(lambda m: m.group(1) + '\n        (use_layer ' + ' '.join(layers) + ')', text)
    return text


def dsn_probe(text):
    """What the KiCad 10.0.7 Specctra export carried (first-run probe, A-PCB-03 research items)."""
    classes = {}
    for m in re.finditer(r'\(class\s+"?([^\s")]+)"?(.*?)\(rule\s*(\(width\s+([\d.]+)\))?\s*(\(clearance\s+([\d.]+)\))?', text, re.S):
        classes[m.group(1)] = {'width': m.group(4), 'clearance': m.group(6)}
    unit = re.search(r'\(resolution\s+(\w+)\s+(\d+)\)', text)
    return {'resolution': f'{unit.group(1)} {unit.group(2)}' if unit else None,
            'wires_fix': len(re.findall(r'\(type\s+fix\)', text)),
            'wires_protect': len(re.findall(r'\(type\s+protect\)', text)),
            'keepouts': len(re.findall(r'\((?:keepout|via_keepout|wire_keepout)\b', text)),
            'planes': len(re.findall(r'\(plane\b', text)),
            'classes': classes}


# --- the KiCad side ----------------------------------------------------------------------------------

def pcbnew_module():
    try:
        import pcbnew  # noqa: F401  (KiCad 10.0.7 Python module)
    except ImportError as error:
        raise SystemExit('board_gen: KiCad pcbnew is required for --check/--route (kicad/kicad:10.0.7). ' + str(error))
    return pcbnew


class Frame:
    """Board mm (contract outline, y up, top view) <-> KiCad nm (y down)."""

    def __init__(self, pcb, outline):
        self.pcb = pcb
        self.ox = 100.0
        self.oy = 100.0 + max(p[1] for p in outline)

    def k(self, x, y):
        return self.pcb.VECTOR2I(self.pcb.FromMM(self.ox + x), self.pcb.FromMM(self.oy - y))

    def m(self, vec):
        return (r4(self.pcb.ToMM(vec.x) - self.ox), r4(self.oy - self.pcb.ToMM(vec.y)))


def flip_footprint(pcb, fp):
    if hasattr(pcb, 'FLIP_DIRECTION_LEFT_RIGHT'):
        fp.Flip(fp.GetPosition(), pcb.FLIP_DIRECTION_LEFT_RIGHT)
    else:
        fp.Flip(fp.GetPosition(), True)


def footprint_file(part):
    """The .kicad_mod of a template part (project library or KiCad image library), SHA256 checked."""
    nick, name = part['fpid'].split(':', 1)
    if part['library'] == 'project':
        path = BASE / part['file']
    else:
        lib = image_library_dir()
        if lib is None:
            raise SpecError('KiCad image footprint library not found (KICAD10_FOOTPRINT_DIR)')
        path = lib / f'{nick}.pretty' / f'{name}.kicad_mod'
    if not path.is_file():
        raise SpecError(f'footprint file missing: {path}')
    if sha256_file(path) != part['sha256']:
        raise SpecError(f'footprint {part["fpid"]} sha256 {sha256_file(path)} differs from the recorded {part["sha256"]}')
    return path


def group_plan(spec, contract, template):
    """Anchors and plan rows of the placement groups; nothing to read when the spec has none."""
    if not spec['groups']:
        return {}, []
    geometry = {p['ref']: footprint_geometry(footprint_file(p).read_text(encoding='utf-8')) for p in template}
    return place_groups(spec, template, geometry, holes(spec, contract), contract['outline_mm'], cutout_boxes(contract))


def load_footprint(pcb, part, temp):
    name = part['fpid'].split(':', 1)[1]
    path = footprint_file(part)
    fp = pcb.FootprintLoad(str(path.parent), name)
    if fp is None:
        raise SpecError('KiCad could not load ' + part['fpid'])
    return fp, path


def place(pcb, frame, fp, anchor):
    fp.SetPosition(pcb.VECTOR2I(0, 0))
    fp.SetOrientationDegrees(float(anchor.get('rotation', 0)))
    if anchor.get('side', 'F') == 'B':
        flip_footprint(pcb, fp)
    align = anchor.get('align', 'origin')
    if align == 'origin':
        point = fp.GetPosition()
    else:
        numbers = {align['pad']} if 'pad' in align else {align['pad_centroid']}
        pads = [p for p in fp.Pads() if str(p.GetNumber()) in numbers]
        if not pads:
            raise SpecError(f'anchor pad(s) {sorted(numbers)} not in footprint')
        xs = [p.GetPosition().x for p in pads]
        ys = [p.GetPosition().y for p in pads]
        point = pcb.VECTOR2I(int(round(sum(xs) / len(xs))), int(round(sum(ys) / len(ys))))
    target = frame.k(*anchor['at'])
    fp.SetPosition(pcb.VECTOR2I(fp.GetPosition().x + target.x - point.x, fp.GetPosition().y + target.y - point.y))


def add_polygon_zone(pcb, board, frame, points, layer, name):
    zone = pcb.ZONE(board)
    zone.SetLayer(layer)
    zone.SetZoneName(name)
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in points:
        v = frame.k(x, y)
        outline.Append(v.x, v.y)
    return zone


def build_board(pcb, spec, contract, template, temp):
    """Board with outline, footprints, holes, keepouts and scripted locked copper (no routing yet)."""
    board_id = spec['board_id']
    blank = pcb.BOARD()
    blank.SetCopperLayerCount(spec['layers']['copper'])
    path = Path(temp) / f'{board_id}.kicad_pcb'
    if not pcb.SaveBoard(str(path), blank, True):
        raise RuntimeError('SaveBoard failed (blank)')
    shutil.copyfile(BASE / spec['project'], Path(temp) / f'{board_id}.kicad_pro')
    (Path(temp) / 'fp-lib-table').write_text(fp_lib_table(template), encoding='utf-8')
    board = pcb.LoadBoard(str(path))  # loads the committed project rules and net classes
    board.SetCopperLayerCount(spec['layers']['copper'])
    for layer, kind in sorted((spec['layers'].get('types') or {}).items()):
        if not board.SetLayerType(board.GetLayerID(layer), getattr(pcb, LAYER_TYPES[kind])):
            raise SpecError(f'KiCad refused layer type {kind} for {layer}')
    block = pcb.TITLE_BLOCK()
    block.SetTitle(f'{board_id} - {spec["status"]}')
    block.SetComment(0, 'CI/model output of pcb/board_gen.py; not a fabrication release; bench gates OPEN.')
    board.SetTitleBlock(block)
    frame = Frame(pcb, contract['outline_mm'])
    nets = {}
    for code, name in enumerate(sorted(spec['instances']['template_nets']), 1):
        net = pcb.NETINFO_ITEM(board, name, code)
        board.Add(net)
        nets[name] = net
    outline = contract['outline_mm']
    for a, b in zip(outline, outline[1:] + outline[:1]):
        edge = pcb.PCB_SHAPE(board)
        edge.SetShape(pcb.SHAPE_T_SEGMENT)
        edge.SetLayer(pcb.Edge_Cuts)
        edge.SetStart(frame.k(*a))
        edge.SetEnd(frame.k(*b))
        edge.SetWidth(pcb.FromMM(0.05))
        board.Add(edge)
    for x0, y0, x1, y1 in cutout_boxes(contract):  # inner Edge.Cuts loops; the DSN export makes them keepouts
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for a, b in zip(corners, corners[1:] + corners[:1]):
            edge = pcb.PCB_SHAPE(board)
            edge.SetShape(pcb.SHAPE_T_SEGMENT)
            edge.SetLayer(pcb.Edge_Cuts)
            edge.SetStart(frame.k(*a))
            edge.SetEnd(frame.k(*b))
            edge.SetWidth(pcb.FromMM(0.05))
            board.Add(edge)
    group_anchors, _rows = group_plan(spec, contract, template)
    sources = []
    for part in template:
        fp, fpath = load_footprint(pcb, part, temp)
        fp.SetReference(part['ref'])
        fp.SetValue(part['value'])
        nick, name = part['fpid'].split(':', 1)
        fp.SetFPID(pcb.LIB_ID(nick, name))
        anchor = part['anchor'] or group_anchors[part['ref']]
        back = anchor.get('side', 'F') == 'B'
        if back:  # KiCad flips texts and pads through the parent board (FlipLayer): a parentless Flip crashed (W2 PCB-PWRB)
            board.Add(fp)
        place(pcb, frame, fp, anchor)
        ref_text = anchor.get('ref_text')
        if ref_text:  # legend position (board mm) when the footprint default lands on a hole or pad
            fp.Reference().SetPosition(frame.k(*ref_text['at']))
            if 'angle' in ref_text:
                fp.Reference().SetTextAngleDegrees(float(ref_text['angle']))
        seen = set()
        for pad in fp.Pads():
            num = str(pad.GetNumber())
            if not num:
                continue
            seen.add(num)
            neutral = part['pads'].get(num)
            if neutral:
                pad.SetNet(nets[neutral])
            else:
                pad.SetNetCode(0)
        if set(part['pads']) - seen:
            raise SpecError(f'{part["ref"]}: pads {sorted(set(part["pads"]) - seen)} missing in {part["fpid"]}')
        if not back:
            board.Add(fp)
        sources.append({'ref': part['ref'], 'footprint': part['fpid'],
                        'file': rel(fpath) if part['library'] == 'project' else f'kicad-image:{nick}.pretty/{name}.kicad_mod',
                        'sha256': part['sha256']})
    lib = Path(temp) / 'SR_RX_Board_Holes.pretty'
    lib.mkdir(exist_ok=True)
    layers = [board.GetLayerID(n) for n in spec['holes'].get('keepout_layers', [])]
    blocks = set(spec['holes'].get('keepout_blocks', []))
    for hole in holes(spec, contract):
        if hole.get('plated'):  # spec bond_hole: plated land on its net, no keepout rule areas (W2 PCB-RF-2)
            add_bond_hole(pcb, board, frame, lib, hole, nets)
            continue
        name = f'NPTH_{hole["d"]:g}mm'
        (lib / f'{name}.kicad_mod').write_text(npth_footprint(name, hole['d']), encoding='utf-8')
        fp = pcb.FootprintLoad(str(lib), name)
        fp.SetReference(hole['ref'])
        fp.SetFPID(pcb.LIB_ID('', name))  # empty nickname: board-only, skipped by library parity
        fp.SetPosition(frame.k(*hole['at']))
        board.Add(fp)
        for layer in layers:
            zone = add_polygon_zone(pcb, board, frame, circle_polygon(*hole['at'], hole['keepout_d'] / 2), layer,
                                    f'KO_{hole["ref"]}_{board.GetLayerName(layer)}')
            zone.SetIsRuleArea(True)
            zone.SetDoNotAllowTracks('tracks' in blocks)
            zone.SetDoNotAllowVias('vias' in blocks)
            zone.SetDoNotAllowZoneFills('zone_fills' in blocks)
            zone.SetDoNotAllowPads('pads' in blocks)
            zone.SetDoNotAllowFootprints('footprints' in blocks)
            board.Add(zone)
    edge = spec.get('edge_keepout')
    if edge:  # rule-area strips on every outline and cutout edge: the router keeps its copper off the edge clearance
        loops = [contract['outline_mm']] + [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)] for x0, y0, x1, y1 in cutout_boxes(contract)]
        for li, loop in enumerate(loops):
            for si, (a, b) in enumerate(zip(loop, loop[1:] + loop[:1])):
                for name in edge['layers']:
                    zone = add_polygon_zone(pcb, board, frame, edge_strip(a, b, float(edge['width_mm'])),
                                            board.GetLayerID(name), f'KO_EDGE_{li}_{si}_{name}')
                    zone.SetIsRuleArea(True)
                    zone.SetDoNotAllowTracks('tracks' in edge['blocks'])
                    zone.SetDoNotAllowVias('vias' in edge['blocks'])
                    zone.SetDoNotAllowZoneFills(False)
                    zone.SetDoNotAllowPads(False)
                    zone.SetDoNotAllowFootprints(False)
                    board.Add(zone)
    for track in spec['pre_route'].get('tracks', []):
        layer = board.GetLayerID(track['layer'])
        for a, b in zip(track['path'], track['path'][1:]):
            seg = pcb.PCB_TRACK(board)
            seg.SetStart(frame.k(*a))
            seg.SetEnd(frame.k(*b))
            seg.SetWidth(pcb.FromMM(track['width_mm']))
            seg.SetLayer(layer)
            seg.SetNet(nets[track['net']])
            seg.SetLocked(bool(track.get('locked', True)))
            board.Add(seg)
    for item in spec['pre_route'].get('vias', []):  # through vias (F.Cu to B.Cu), scripted and locked
        via = pcb.PCB_VIA(board)
        via.SetViaType(pcb.VIATYPE_THROUGH)
        via.SetPosition(frame.k(*item['at']))
        via.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
        via.SetWidth(pcb.FromMM(item['diameter_mm']))
        via.SetDrill(pcb.FromMM(item['drill_mm']))
        via.SetNet(nets[item['net']])
        via.SetLocked(bool(item.get('locked', True)))
        board.Add(via)
    for zone in spec['pre_route'].get('zones', []):
        add_copper_zone(pcb, board, frame, spec, contract, zone, nets)
    text = pcb.PCB_TEXT(board)
    text.SetText(f'{board_id} {spec["status"]}')
    text.SetPosition(frame.k(0, -2.0))
    text.SetTextSize(pcb.VECTOR2I(pcb.FromMM(1.0), pcb.FromMM(1.0)))
    text.SetTextThickness(pcb.FromMM(0.15))
    text.SetLayer(pcb.Cmts_User)
    board.Add(text)
    return board, frame, nets, sources


def add_bond_hole(pcb, board, frame, lib, hole, nets):
    plated = hole['plated']
    name = f'PTH_BOND_{hole["d"]:g}mm_{plated["pad_mm"]:g}mm'
    (lib / f'{name}.kicad_mod').write_text(bond_footprint(name, hole['d'], plated['pad_mm']), encoding='utf-8')
    fp = pcb.FootprintLoad(str(lib), name)
    fp.SetReference(hole['ref'])
    fp.SetFPID(pcb.LIB_ID('', name))  # empty nickname: board-only, skipped by library parity
    fp.SetPosition(frame.k(*hole['at']))
    for pad in fp.Pads():
        pad.SetNet(nets[plated['net']])
    board.Add(fp)


def add_tracks_and_vias(pcb, board, frame, nets, tracks, vias):
    for track in tracks:
        layer = board.GetLayerID(track['layer'])
        for a, b in zip(track['path'], track['path'][1:]):
            seg = pcb.PCB_TRACK(board)
            seg.SetStart(frame.k(*a))
            seg.SetEnd(frame.k(*b))
            seg.SetWidth(pcb.FromMM(track['width_mm']))
            seg.SetLayer(layer)
            seg.SetNet(nets[track['net']])
            seg.SetLocked(bool(track.get('locked', True)))
            board.Add(seg)
    for item in vias:
        via = pcb.PCB_VIA(board)
        via.SetViaType(pcb.VIATYPE_THROUGH)
        via.SetPosition(frame.k(*item['at']))
        via.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
        via.SetWidth(pcb.FromMM(item['diameter_mm']))
        via.SetDrill(pcb.FromMM(item['drill_mm']))
        via.SetNet(nets[item['net']])
        via.SetLocked(bool(item.get('locked', True)))
        board.Add(via)


def add_coupon(pcb, board, frame, spec, contract, nets):
    """Test-coupon outlines, footprints and copper (spec coupon), drawn after the SES import (W2 PCB-RF-2)."""
    coupon = spec.get('coupon')
    if not coupon:
        return []
    for x0, y0, x1, y1 in coupon['outlines']:
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for a, b in zip(corners, corners[1:] + corners[:1]):
            edge = pcb.PCB_SHAPE(board)
            edge.SetShape(pcb.SHAPE_T_SEGMENT)
            edge.SetLayer(pcb.Edge_Cuts)
            edge.SetStart(frame.k(*a))
            edge.SetEnd(frame.k(*b))
            edge.SetWidth(pcb.FromMM(0.05))
            board.Add(edge)
    fps = {f['footprint']: f for f in read_json(MANIFEST)['footprints']}
    sources = []
    for item in coupon.get('footprints', []):
        entry = fps.get(item['footprint'])
        if entry is None:
            raise SpecError(f'coupon footprint {item["footprint"]} is not in the portable manifest')
        part = {'fpid': item['footprint'], 'library': 'project', 'file': entry['file'], 'sha256': entry['sha256']}
        fp, fpath = load_footprint(pcb, part, None)
        fp.SetReference(item['ref'])
        fp.SetValue(item['value'])
        nick, name = item['footprint'].split(':', 1)
        fp.SetFPID(pcb.LIB_ID(nick, name))
        board.Add(fp)
        place(pcb, frame, fp, item['anchor'])
        for pad in fp.Pads():
            net = item['pads'].get(str(pad.GetNumber()))
            if net:
                pad.SetNet(nets[net])
            else:
                pad.SetNetCode(0)
        flags = 0
        for name_ in ('FP_EXCLUDE_FROM_POS_FILES', 'FP_EXCLUDE_FROM_BOM', 'FP_BOARD_ONLY'):
            flags |= int(getattr(pcb, name_, 0))
        fp.SetAttributes(fp.GetAttributes() | flags)
        sources.append({'ref': item['ref'], 'footprint': item['footprint'], 'file': rel(fpath), 'sha256': entry['sha256']})
    add_tracks_and_vias(pcb, board, frame, nets, coupon.get('tracks', []), coupon.get('vias', []))
    for zone in coupon.get('zones', []):
        add_copper_zone(pcb, board, frame, spec, contract, zone, nets)
    return sources


def add_copper_zone(pcb, board, frame, spec, contract, zone, nets):
    points = contract['outline_mm'] if zone.get('outline', 'board') == 'board' else zone['outline']
    item = add_polygon_zone(pcb, board, frame, points, board.GetLayerID(zone['layer']), zone['id'])
    item.SetNet(nets[zone['net']])
    item.SetAssignedPriority(int(zone.get('priority', 0)))
    if 'pad_connection' in zone:
        item.SetPadConnection(getattr(pcb, ZONE_PAD_CONNECTIONS[zone['pad_connection']]))
    board.Add(item)
    return item


def via_centre_stubs(pcb, board):
    """Join router track ends that end inside a via, off its centre, to the centre with a short stub (W2 PCB-RF-2).

    KiCad 10.0.7 reports track_not_centered_on_via for a via layer where tracks end inside the via but none ends on
    its centre (pcbnew/drc/drc_test_provider_connectivity.cpp at 10.0.7: layerHasCenteredTrack). Freerouting joined a
    scripted locked via 0.135 mm off its centre (route run 42423540033). For each such via layer one stub of the
    track's width runs from that end to the centre, inside the via copper; no track is moved (moving the end tilted
    long tracks into clearance errors, route run 42424111495). Returns [{net, layer, end, centre}] in KiCad mm.
    """
    tracks = [t for t in board.GetTracks() if t.Type() == pcb.PCB_TRACE_T]
    added = []
    for via in [v for v in board.GetTracks() if v.Type() == pcb.PCB_VIA_T]:
        c = via.GetPosition()
        cx, cy = int(c.x), int(c.y)
        layers = {}
        for track in tracks:
            if track.GetNetCode() != via.GetNetCode() or not via.IsOnLayer(track.GetLayer()):
                continue
            for pt in (track.GetStart(), track.GetEnd()):
                x, y = int(pt.x), int(pt.y)
                entry = layers.setdefault(track.GetLayer(), {'centred': False, 'off': None})
                if (x, y) == (cx, cy):
                    entry['centred'] = True
                elif entry['off'] is None and via.HitTest(pcb.VECTOR2I(x, y)):
                    entry['off'] = (x, y, track.GetWidth())
        for layer, entry in sorted(layers.items()):
            if entry['centred'] or entry['off'] is None:
                continue
            x, y, width = entry['off']
            stub = pcb.PCB_TRACK(board)
            stub.SetStart(pcb.VECTOR2I(x, y))
            stub.SetEnd(pcb.VECTOR2I(cx, cy))
            stub.SetWidth(width)
            stub.SetLayer(layer)
            stub.SetNetCode(via.GetNetCode())
            board.Add(stub)
            added.append({'net': via.GetNetname(), 'layer': board.GetLayerName(layer),
                          'end': [r4(pcb.ToMM(x)), r4(pcb.ToMM(y))], 'centre': [r4(pcb.ToMM(cx)), r4(pcb.ToMM(cy))]})
    return sorted(added, key=lambda m: (m['net'], m['layer'], m['end']))


def count_locked(board):
    return sum(1 for t in board.GetTracks() if t.IsLocked())


def shown_arg(arg):
    """A command argument for logs: file names instead of runner paths."""
    arg = str(arg)
    if arg.startswith('--user_data_path='):
        return '--user_data_path=<temp>'
    return Path(arg).name if '/' in arg or '\\' in arg else arg


def run(cmd, timeout=900, cwd=None):
    proc = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=timeout, cwd=cwd,
                          stdin=subprocess.DEVNULL)
    return proc


def run_logged(cmd, log_path, timeout, cwd):
    """Run with stdout and stderr streamed to a file; returns the exit code, or None after a timeout."""
    with open(log_path, 'wb') as log:
        proc = subprocess.Popen([str(c) for c in cmd], stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, cwd=cwd)
        try:
            return proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return None


def kicad_cli():
    cli = shutil.which('kicad-cli')
    if not cli:
        raise SystemExit('board_gen: kicad-cli not found (kicad/kicad:10.0.7)')
    return cli


def run_drc(board_path, out_json, save):
    cmd = [kicad_cli(), 'pcb', 'drc', '--format', 'json', '--severity-all', '--all-track-errors', '--units', 'mm',
           '--refill-zones']
    if save:
        cmd.append('--save-board')
    cmd += ['--output', str(out_json), str(board_path)]
    proc = run(cmd, timeout=600)
    if proc.returncode != 0 or not Path(out_json).is_file():
        raise SystemExit('board_gen: KiCad DRC did not complete:\n' + proc.stdout + proc.stderr)
    return read_json(out_json), [Path(c).name if i == 0 else c for i, c in enumerate(cmd[:-3])]


def board_facts(pcb, board, frame):
    """Everything the audits and the report need, read back from the saved board."""
    fps = []
    for fp in sorted(board.GetFootprints(), key=lambda f: sort_ref(f.GetReference())):
        pads = []
        for pad in fp.Pads():
            box = pad.GetBoundingBox()
            lo = frame.m(pcb.VECTOR2I(box.GetLeft(), box.GetBottom()))
            hi = frame.m(pcb.VECTOR2I(box.GetRight(), box.GetTop()))
            size = pad.GetSize(pcb.F_Cu) if pad.GetAttribute() != pcb.PAD_ATTRIB_NPTH else pad.GetDrillSize()
            drill = pad.GetDrillSize()
            pads.append({'number': str(pad.GetNumber()), 'net': pad.GetNetname() or None, 'at': list(frame.m(pad.GetPosition())),
                         'box': [lo[0], lo[1], hi[0], hi[1]], 'tht': pad.HasHole() if hasattr(pad, 'HasHole') else drill.x > 0,
                         'npth': pad.GetAttribute() == pcb.PAD_ATTRIB_NPTH,
                         'annular_mm': r4(min(pcb.ToMM(size.x) - pcb.ToMM(drill.x), pcb.ToMM(size.y) - pcb.ToMM(drill.y)) / 2)
                         if drill.x > 0 and pad.GetAttribute() != pcb.PAD_ATTRIB_NPTH else None})
        pads.sort(key=lambda p: (sort_ref(p['number']) if p['number'] else ('', -1, ''), p['at']))
        layers = {}
        for item in fp.GraphicalItems():
            if item.Type() != pcb.PCB_SHAPE_T:  # body and courtyard outlines only, not texts
                continue
            name = board.GetLayerName(item.GetLayer())
            if name in ('F.Fab', 'B.Fab', 'F.Courtyard', 'B.Courtyard', 'F.CrtYd', 'B.CrtYd'):
                b = item.GetBoundingBox()
                lo = frame.m(pcb.VECTOR2I(b.GetLeft(), b.GetBottom()))
                hi = frame.m(pcb.VECTOR2I(b.GetRight(), b.GetTop()))
                key = 'fab' if 'Fab' in name else 'courtyard'
                cur = layers.get(key)
                layers[key] = [lo[0], lo[1], hi[0], hi[1]] if cur is None else [min(cur[0], lo[0]), min(cur[1], lo[1]),
                                                                                  max(cur[2], hi[0]), max(cur[3], hi[1])]
        fpid = fp.GetFPID()
        fps.append({'ref': fp.GetReference(), 'fpid': f'{fpid.GetLibNickname()}:{fpid.GetLibItemName()}'.lstrip(':'),
                    'value': fp.GetValue(), 'side': 'B' if fp.GetLayer() == pcb.B_Cu else 'F',
                    'rotation': r4(fp.GetOrientationDegrees()), 'at': list(frame.m(fp.GetPosition())),
                    'pads': pads, 'courtyard_box': layers.get('courtyard'), 'fab_box': layers.get('fab')})
    tracks = {'segments': 0, 'vias': 0, 'locked': 0, 'by_layer': {}, 'widths_mm': []}
    widths = set()
    for t in board.GetTracks():
        if t.Type() == pcb.PCB_VIA_T:
            tracks['vias'] += 1
        else:
            tracks['segments'] += 1
            layer = board.GetLayerName(t.GetLayer())
            tracks['by_layer'][layer] = tracks['by_layer'].get(layer, 0) + 1
            widths.add(r4(pcb.ToMM(t.GetWidth())))
        tracks['locked'] += bool(t.IsLocked())
    tracks['by_layer'] = dict(sorted(tracks['by_layer'].items()))
    tracks['widths_mm'] = sorted(widths)
    zones = []
    for z in board.Zones():
        zones.append({'name': z.GetZoneName(), 'rule_area': bool(z.GetIsRuleArea()), 'net': z.GetNetname() or None,
                      'layer': board.GetLayerName(z.GetLayer()), 'filled': bool(z.IsFilled()),
                      'locked': bool(z.IsLocked())})
    zones.sort(key=lambda z: (z['rule_area'], z['name']))
    return {'footprints': fps, 'tracks': tracks, 'zones': zones, 'copper_layers': board.GetCopperLayerCount()}


def box_circle_distance(box, center):
    x0, y0, x1, y1 = box
    cx, cy = center
    dx = max(x0 - cx, 0.0, cx - x1)
    dy = max(y0 - cy, 0.0, cy - y1)
    return math.hypot(dx, dy)


def source_pad_audit(facts, spec, template, graph):
    """Per instance: each graph pin is on its pad with the mapped net; no other numbered pad carries a net."""
    by_ref = {f['ref']: f for f in facts['footprints']}
    out = []
    for item in spec['instances']['list']:
        errors = []
        for part in template:
            fp = by_ref.get(part['ref'])
            if fp is None:
                errors.append({'kind': 'missing_footprint', 'ref': part['ref']})
                continue
            if fp['fpid'] != part['fpid']:
                errors.append({'kind': 'footprint_id', 'ref': part['ref'], 'expected': part['fpid'], 'observed': fp['fpid']})
            pads = {}
            for p in fp['pads']:
                if p['number']:
                    pads.setdefault(p['number'], []).append(p['net'])
            if part['source'] == 'graph':
                gref = item['refs'][part['ref']]
                comp = graph[gref]
                if fp['value'].strip() != comp['value'].strip():
                    errors.append({'kind': 'value', 'ref': gref})
                wanted = {}
                for pin in comp['pins']:
                    wanted[str(pin['number'])] = None if pin.get('nc') else pin['net']
            else:
                gref = None
                wanted = {num: item['nets'][n] for num, n in part['pads'].items()}
            inverse = {v: k for k, v in item['nets'].items()}
            for num, gnet in wanted.items():
                observed = pads.get(num)
                expect = inverse.get(gnet) if gnet else None
                if not observed or any(n != expect for n in observed):
                    errors.append({'kind': 'pad_net', 'ref': gref or part['ref'], 'pad': num, 'expected': gnet,
                                   'observed': observed})
            for num, nets in sorted(pads.items()):
                if num not in wanted and any(nets):
                    errors.append({'kind': 'extra_netted_pad', 'ref': gref or part['ref'], 'pad': num, 'observed': nets})
        out.append({'instance': item['id'], 'errors': errors, 'passed': not errors})
    return out


def keepout_audit(facts, hole_list, template):
    """Copper pads stay out of the hole keepouts; courtyard and body (F.Fab) intrusions are reported."""
    refs = {p['ref'] for p in template}
    rows, errors = [], []
    for hole in hole_list:
        r = hole['keepout_d'] / 2
        for fp in facts['footprints']:
            if fp['ref'] not in refs:
                continue
            pad_gap = min((box_circle_distance(p['box'], hole['at']) for p in fp['pads'] if not p['npth']), default=None)
            row = {'hole': hole['ref'], 'ref': fp['ref'], 'keepout_radius': r4(r),
                   'pad_distance': r4(pad_gap) if pad_gap is not None else None,
                   'courtyard_distance': r4(box_circle_distance(fp['courtyard_box'], hole['at'])) if fp['courtyard_box'] else None,
                   'body_distance': r4(box_circle_distance(fp['fab_box'], hole['at'])) if fp['fab_box'] else None}
            row['courtyard_intrudes'] = row['courtyard_distance'] is not None and row['courtyard_distance'] < r
            row['body_intrudes'] = row['body_distance'] is not None and row['body_distance'] < r
            if pad_gap is not None and pad_gap < r:
                errors.append({'kind': 'pad_in_keepout', 'hole': hole['ref'], 'ref': fp['ref']})
            if row['body_intrudes']:
                errors.append({'kind': 'body_in_keepout', 'hole': hole['ref'], 'ref': fp['ref']})
            rows.append(row)
    return {'rows': rows, 'errors': errors, 'passed': not errors,
            'note': 'Keepout = copper rule area (tracks, vias, fills) on the listed layers. A courtyard box '
                    'intrusion is reported, not failed, when pads and the F.Fab body clear the keepout.'}


def group_audit(facts, rows):
    """Group-placed parts on the saved board: at the planned anchor, courtyard inside the region,
    decoupling part within max_mm of its pin (pin pad centre to the courtyard box)."""
    by_ref = {f['ref']: f for f in facts['footprints']}
    tol = 0.05  # KiCad courtyard boxes include half the 0.05 mm courtyard line
    out, errors = [], []
    for row in rows:
        fp = by_ref.get(row['ref'])
        if fp is None:
            errors.append({'kind': 'missing_footprint', 'group': row['group'], 'ref': row['ref']})
            continue
        region, box, plan = row['region'], fp['courtyard_box'], row['courtyard_box']
        entry = {'group': row['group'], 'ref': row['ref'], 'planned_at': row['at'], 'observed_at': fp['at'],
                 'side': fp['side'], 'rotation': fp['rotation'], 'planned_courtyard_box': plan, 'courtyard_box': box}
        # The courtyard box, not KiCad's orientation number, is compared: a B-side flip changes the number.
        if fp['side'] != row['side'] or math.hypot(fp['at'][0] - row['at'][0], fp['at'][1] - row['at'][1]) > 1e-3 or \
                not box or any(abs(a - b) > tol for a, b in zip(box, plan)):
            errors.append({'kind': 'not_at_plan', 'group': row['group'], 'ref': row['ref']})
        entry['in_region'] = bool(box) and (box[0] >= region[0] - tol and box[1] >= region[1] - tol
                                            and box[2] <= region[2] + tol and box[3] <= region[3] + tol)
        if not entry['in_region']:
            errors.append({'kind': 'outside_region', 'group': row['group'], 'ref': row['ref']})
        dec = row['decouple']
        if dec:
            pins = [p['at'] for p in by_ref.get(dec['ref'], {}).get('pads', []) if p['number'] == dec['pad']]
            dist = r4(box_circle_distance(box, pins[0])) if pins and box else None
            entry['decouple'] = {**dec, 'distance_mm': dist,
                                 'within': dist is not None and dist <= dec['max_mm'] + 1e-3}
            if not entry['decouple']['within']:
                errors.append({'kind': 'decoupling_too_far', 'group': row['group'], 'ref': row['ref']})
        out.append(entry)
    return {'rows': out, 'errors': errors, 'passed': not errors}


def cutout_audit(facts, contract, template):
    """No pad, courtyard box or F.Fab body box of a template part inside a contract cutout (spec audit_cutouts, W2 PCB-CTRL).

    Boxes are axis-aligned bounding boxes, so the audit is conservative; touching the cutout edge passes."""
    cuts = cutout_boxes(contract)
    refs = {p['ref'] for p in template}
    errors = []
    for fp in facts['footprints']:
        if fp['ref'] not in refs:
            continue
        for cut in cuts:
            for what, box in (('courtyard', fp['courtyard_box']), ('body', fp['fab_box'])):
                if box and rects_overlap(box, cut, -1e-3):
                    errors.append({'kind': f'{what}_in_cutout', 'ref': fp['ref'], 'cutout': cut, 'box': box})
            if any(rects_overlap(p['box'], cut, -1e-3) for p in fp['pads']):
                errors.append({'kind': 'pad_in_cutout', 'ref': fp['ref'], 'cutout': cut})
    return {'cutouts': cuts, 'errors': errors, 'passed': not errors,
            'note': 'axis-aligned courtyard, F.Fab and pad boxes against the contract cutouts (edge contact allowed)'}


def annular_audit(facts, template, floor):
    refs = {p['ref'] for p in template}
    low = [{'ref': f['ref'], 'pad': p['number'], 'annular_mm': p['annular_mm']} for f in facts['footprints']
           if f['ref'] in refs for p in f['pads'] if p['annular_mm'] is not None and p['annular_mm'] + 1e-9 < floor]
    return {'floor_mm': floor, 'below_floor': low, 'passed': not low}


def connectors_doc(spec, contract, template, facts):
    by_ref = {f['ref']: f for f in facts['footprints']}
    out = []
    for item in spec['instances']['list']:
        place_key = item.get('placement', 'default')
        placement = contract.get('placements', {}).get(place_key)
        conns = []
        for part in template:
            gref = item['refs'][part['ref']]
            is_conn = part['source'] == 'pilot_placeholder' or (gref and gref[:1] in 'JX')
            if not is_conn:
                continue
            fp = by_ref[part['ref']]
            pins = [{'pad': p['number'], 'net': item['nets'].get(p['net']) if p['net'] else None, 'at': p['at']}
                    for p in fp['pads'] if p['number']]
            entry = {'template_ref': part['ref'], 'ref': gref, 'kind': part['source'], 'footprint': part['fpid'],
                     'side': fp['side'], 'rotation': fp['rotation'], 'at': fp['at'], 'pins': pins}
            if placement:
                ox, oy = placement['origin']
                entry['enclosure_xy'] = [r4(ox + fp['at'][0]), r4(oy + fp['at'][1])]
                for pin in pins:
                    pin['enclosure_xy'] = [r4(ox + pin['at'][0]), r4(oy + pin['at'][1])]
            if part['source'] == 'pilot_placeholder':
                entry['replaced_by'] = next(p['replaced_by'] for p in spec['parts'] if p['ref'] == part['ref'])
            conns.append(entry)
        out.append({'instance': item['id'], 'placement': place_key,
                    'board_origin_enclosure_mm': placement['origin'] if placement else None,
                    'z_bottom': placement.get('z_bottom') if placement else None,
                    'facing': placement.get('facing') if placement else None, 'connectors': conns})
    return {'schema': 'srrx-board-connectors-v1', 'board_id': spec['board_id'], 'status': spec['status'],
            'coordinates': 'board mm: contract outline origin, y up, top view; enclosure_xy = contract placement '
                           'origin + board xy (outline axes parallel to the enclosure, as mechanical/srrx_mech/cad.py:171)',
            'instances': out}


def build_report(spec, contract, stackup, template, proj, facts, drc, audits, board_path, project_rel):
    source_pad = audits['source_pad']
    boundary = audits['boundary']
    result = {
        'drc_errors': drc['errors'], 'drc_unconnected': drc['unconnected'], 'drc_warnings': drc['warnings'],
        'ignored_checks': drc['ignored_checks'],
        'source_pad_audit_errors': {a['instance']: len(a['errors']) for a in source_pad},
        'boundary_audit': sorted({b['status'] for b in boundary}),
        'domain_audit': audits['domain']['passed'], 'keepout_audit': audits['keepout']['passed'],
        'annular_audit': audits['annular']['passed'], 'locked_copper_kept': audits['locked']['kept'],
        'group_audit': audits['groups']['passed'],
    }
    if 'cutouts' in audits:  # only specs with audit_cutouts carry this key (ENC and PWR_B reports stay unchanged)
        result['cutout_audit'] = audits['cutouts']['passed']
    passed = (drc['passed'] and all(a['passed'] for a in source_pad) and audits['domain']['passed']
              and audits['keepout']['passed'] and audits['annular']['passed'] and audits['locked']['kept']
              and audits['groups']['passed'] and audits.get('cutouts', {'passed': True})['passed']
              and not any(b['status'].startswith('fail') for b in boundary))
    return {
        'schema': REPORT_SCHEMA, 'board_id': spec['board_id'], 'status': spec['status'],
        'label': 'CI/model result of pcb/board_gen.py in kicad/kicad:10.0.7; not a hardware PASS; bench gates OPEN',
        'passed': passed, 'result': result,
        'inputs': proj, 'board_file': rel(board_path), 'board_sha256': sha256_file(board_path),
        'project_file': project_rel, 'fp_lib_table_sha256': sha256_file(board_path.parent / 'fp-lib-table'),
        'layers': spec['layers'], 'stackup_contract': stackup,
        'outline_mm': contract['outline_mm'],
        **({'cutouts_mm': contract['cutouts_mm']} if contract.get('cutouts_mm') else {}),
        'holes': holes(spec, contract),
        'instances': [{'id': i['id'], 'placement': i.get('placement'), 'qty': i['qty'], 'refs': i['refs'], 'nets': i['nets']}
                      for i in spec['instances']['list']],
        'build_quantity': {'instances': sum(i['qty'] for i in spec['instances']['list']),
                           'spares': spec['instances'].get('spares', 0),
                           'total': sum(i['qty'] for i in spec['instances']['list']) + spec['instances'].get('spares', 0)},
        'template': [{k: p[k] for k in ('ref', 'source', 'fpid', 'library', 'file', 'sha256', 'value', 'pads', 'unused_pads')}
                     for p in template],
        'placeholders': [{'ref': p['ref'], 'footprint': p['footprint'], 'replaced_by': p['replaced_by'],
                          'pending': p['pending'], 'pins_source': p.get('pins_source', ''),
                          'why': p.get('why_placeholder', '')}
                         for p in spec['parts'] if p['source'] == 'pilot_placeholder'],
        'placement': [{k: f[k] for k in ('ref', 'fpid', 'side', 'rotation', 'at', 'courtyard_box', 'fab_box')}
                      for f in facts['footprints']],
        'pads': {f['ref']: [{k: p[k] for k in ('number', 'net', 'at')} for p in f['pads']] for f in facts['footprints']},
        'copper': {'tracks': facts['tracks'], 'zones': facts['zones'], 'copper_layers': facts['copper_layers']},
        'drc': drc, 'audits': audits,
        'router': {k: FREEROUTING[k] for k in ('name', 'version', 'licence', 'url', 'sha256', 'main_class')}
        | {'runtime': f'{TEMURIN_JRE["name"]} {TEMURIN_JRE["version"]} (sha256 {TEMURIN_JRE["sha256"]})',
           'max_passes': spec['router']['max_passes'], 'threads': spec['router']['threads'],
           'job_timeout': spec['router']['job_timeout'], 'fetch': 'CI only, never committed or uploaded'},
        'heights': spec.get('height_zones', []),
        'does_not_prove': NOT_PROVED,
    }


def audit_board(pcb, spec, contract, stackup, template, graph, db, proj, board_path, drc_raw, project):
    board = pcb.LoadBoard(str(board_path))
    frame = Frame(pcb, contract['outline_mm'])
    facts = board_facts(pcb, board, frame)
    policy = spec['drc_policy'].get('warning_checks', {})
    drc = drc_summary(drc_raw, policy, project['board']['design_settings']['rule_severities'])
    partition = read_json(BASE / spec['partition'])
    hole_list = holes(spec, contract)
    want_locked = (sum(len(t['path']) - 1 for t in spec['pre_route'].get('tracks', []) if t.get('locked', True))
                   + sum(1 for v in spec['pre_route'].get('vias', []) if v.get('locked', True)))
    audits = {
        'domain': domain_audit(spec, partition),
        'source_pad': source_pad_audit(facts, spec, template, graph),
        'boundary': boundary_audit(spec, template, graph, db),
        'keepout': keepout_audit(facts, hole_list, template),
        'annular': annular_audit(facts, template, spec['fab_floor']['pth_annular_min']),
        'groups': group_audit(facts, group_plan(spec, contract, template)[1]),
        'locked': {'scripted_segments': want_locked, 'locked_on_board': facts['tracks']['locked'],
                   'kept': facts['tracks']['locked'] >= want_locked,
                   'note': 'SES import before/after counts and the DSN probe are in route-log.json'},
    }
    if spec.get('audit_cutouts'):
        audits['cutouts'] = cutout_audit(facts, contract, template)
    report = build_report(spec, contract, stackup, template, proj, facts, drc, audits, board_path, spec['project'])
    return report, connectors_doc(spec, contract, template, facts)


def prepare_inputs(board):
    spec = read_json(spec_path(board))
    validate_spec(spec, board)
    contract, stackup = load_contract(spec)
    graph = load_graph()
    db = parts_by_ref()
    template = resolve(spec, graph, read_json(MANIFEST))
    project_path = BASE / spec['project']
    if not project_path.is_file():
        raise SpecError(f'committed project file missing: {spec["project"]}')
    project_bytes = project_path.read_bytes()
    project = json.loads(project_bytes)
    problems = check_project(spec, project)
    if problems:
        raise SpecError(f'{rel(project_path)}: ' + '; '.join(problems))
    proj = projection(spec, contract, stackup, template, graph, project_bytes)
    return spec, contract, stackup, graph, db, template, project, proj


def inputs_only(board):
    spec, contract, stackup, graph, db, template, project, proj = prepare_inputs(board)
    out = OUT_ROOT / board
    report_path = out / 'report.json'
    partition = read_json(BASE / spec['partition'])
    summary = {'board': board, 'inputs_sha256': proj['sha256'], 'domain_audit': domain_audit(spec, partition)['passed'],
               'boundary': [b['status'] for b in boundary_audit(spec, template, graph, db)]}
    if not report_path.is_file():
        summary['committed'] = 'no report yet: route with [pcb-route %s]' % board
        print(dump(summary), end='')
        return 1
    committed = read_json(report_path)['inputs']
    stale = sorted(k for k in proj['parts'] if committed['parts'].get(k) != proj['parts'][k])
    summary['stale_parts'] = stale
    print(dump(summary), end='')
    return 1 if stale or committed['sha256'] != proj['sha256'] else 0


def write_outputs(out, report, connectors, drc_raw):
    atomic_write(out / 'report.json', dump(report))
    atomic_write(out / 'connectors.json', dump(connectors))
    atomic_write(out / 'drc.json', dump(normalise_drc(drc_raw)))


def previews(board_path, out):
    cli = kicad_cli()
    done = []
    for name, layers in (('top', 'F.Cu,F.Silkscreen,F.Fab,Edge.Cuts'), ('bottom', 'B.Cu,B.Silkscreen,Edge.Cuts')):
        target = out / f'{board_path.stem}-{name}.svg'
        with tempfile.TemporaryDirectory(prefix='sr-rx-svg-') as temp:
            svg = Path(temp) / 'board.svg'
            proc = run([cli, 'pcb', 'export', 'svg', '--mode-single', '--black-and-white', '--layers', layers,
                        '--page-size-mode', '2', '--exclude-drawing-sheet', '--output', svg, board_path], timeout=300)
            if proc.returncode or not svg.is_file():
                raise SystemExit('board_gen: SVG export failed:\n' + proc.stdout + proc.stderr)
            atomic_write(target, svg.read_bytes())
        done.append(rel(target))
    return done


def route(board, freerouting):
    pcb = pcbnew_module()
    if not str(pcb.Version()).startswith(KICAD_VERSION):
        raise SystemExit(f'board_gen: KiCad {pcb.Version()} found, {KICAD_VERSION} required')
    spec, contract, stackup, graph, db, template, project, proj = prepare_inputs(board)
    tools = Path(freerouting).resolve()
    if not outside_repository(tools):
        raise SpecError('the Freerouting tools must live outside the repository')
    jar, java = tools / FREEROUTING['file'], java_in(tools)
    if sha256_file(jar) != FREEROUTING['sha256']:
        raise SpecError('Freerouting JAR SHA256 mismatch: fetch it again with --fetch-freerouting')
    out = OUT_ROOT / board
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f'sr-rx-{board}-') as temp:
        temp = Path(temp)
        board_obj, frame, nets, sources = build_board(pcb, spec, contract, template, temp)
        staged = temp / f'{board}.kicad_pcb'
        if not pcb.SaveBoard(str(staged), board_obj, True):
            raise RuntimeError('SaveBoard failed (placed)')
        locked_before = count_locked(board_obj)
        dsn, ses = temp / f'{board}.dsn', temp / f'{board}.ses'
        if not pcb.ExportSpecctraDSN(board_obj, str(dsn)) or not dsn.is_file():
            raise SystemExit('board_gen: Specctra DSN export failed')
        if spec['router'].get('class_layers'):  # per-class routing layers (W2 PCB-CTRL: power classes on the outer layers)
            dsn.write_text(patch_dsn_class_layers(dsn.read_text(encoding='utf-8'), spec['router']['class_layers'],
                                                  spec['router'].get('class_layers_reserved', ())), encoding='utf-8')
        probe = dsn_probe(dsn.read_text(encoding='utf-8', errors='replace'))
        cmd = freerouting_command(java, jar, dsn, ses, spec['router']['max_passes'], spec['router']['threads'],
                                  temp / 'fr-user', spec['router']['job_timeout'], router_extra(spec['router']))
        shown_cmd = [shown_arg(c) for c in cmd]
        print('Freerouting command:', ' '.join(shown_cmd), flush=True)
        art = os.environ.get('SR_RX_PCB_ARTIFACTS')
        if art:  # the DSN is our design data; keep it for review even if routing fails
            Path(art).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(dsn, Path(art) / dsn.name)
        proc = run_logged(cmd, temp / 'freerouting.log', int(spec['router'].get('timeout_s', 900)), temp)
        log = re.sub(r'\x1b\[[0-9;]*m', '', (temp / 'freerouting.log').read_text(encoding='utf-8', errors='replace'))
        if art:
            atomic_write(Path(art) / 'freerouting.log', log)
        if proc is None:
            raise SystemExit(f'board_gen: Freerouting timed out after {spec["router"].get("timeout_s", 900)} s:\n{log[-6000:]}')
        if proc != 0 or not ses.is_file():
            raise SystemExit(f'board_gen: Freerouting failed ({proc}):\n{log[-6000:]}')
        if not pcb.ImportSpecctraSES(board_obj, str(ses)):
            raise SystemExit('board_gen: Specctra SES import failed')
        locked_after = count_locked(board_obj)
        if locked_after < locked_before:
            raise SystemExit(f'board_gen: SES import dropped locked copper ({locked_before} -> {locked_after}); '
                             'use keepouts plus post-route copper for this board')
        stubs = via_centre_stubs(pcb, board_obj)  # track_not_centered_on_via
        sources += add_coupon(pcb, board_obj, frame, spec, contract, nets)
        for zone in spec['post_route_zones']:
            add_copper_zone(pcb, board_obj, frame, spec, contract, zone, nets)
        board_path = out / f'{board}.kicad_pcb'
        atomic_write(out / 'fp-lib-table', fp_lib_table(template))
        if not pcb.SaveBoard(str(staged), board_obj, True):
            raise RuntimeError('SaveBoard failed (routed)')
        atomic_write(board_path, staged.read_bytes())
        drc_raw, drc_cmd = run_drc(board_path, temp / 'drc.json', save=True)
        report, connectors = audit_board(pcb, spec, contract, stackup, template, graph, db, proj, board_path,
                                         drc_raw, project)
        write_outputs(out, report, connectors, drc_raw)
        shown = previews(board_path, out)
        route_log = {
            'schema': 'srrx-board-route-log-v1', 'board_id': board,
            'label': 'Frozen route provenance (CI run); --check does not re-route',
            'tool': {k: FREEROUTING[k] for k in ('name', 'version', 'licence', 'url', 'sha256', 'main_class', 'source_read')},
            'runtime': {k: TEMURIN_JRE[k] for k in ('name', 'version', 'licence', 'url', 'sha256', 'source_read')},
            'command': shown_cmd,
            'exit_code': proc, 'log_tail': log.strip().splitlines()[-40:],
            'dsn_sha256': sha256_file(dsn), 'ses_sha256': sha256_file(ses), 'dsn_probe': probe,
            'locked_segments': {'before_ses_import': locked_before, 'after_ses_import': locked_after},
            'via_centre_stubs': stubs,
            'drc_command': drc_cmd, 'board_sha256': sha256_file(board_path), 'previews': shown,
            'footprint_sources': sources, 'kicad_version': str(pcb.Version()),
            'github': {k: os.environ.get(v, '') for k, v in (('run_id', 'GITHUB_RUN_ID'), ('sha', 'GITHUB_SHA'),
                                                               ('ref', 'GITHUB_REF'))},
        }
        atomic_write(out / 'route-log.json', dump(route_log))
        # The DSN and SES are design data (not Freerouting code): kept as artifacts for review, not committed.
        if art:
            shutil.copyfile(ses, Path(art) / ses.name)
    summary = {k: report['result'][k] for k in report['result']}
    print(dump({'board': board, 'passed': report['passed'], **summary}), end='')
    return 0 if report['passed'] else 1


def check(board):
    pcb = pcbnew_module()
    if not str(pcb.Version()).startswith(KICAD_VERSION):
        raise SystemExit(f'board_gen: KiCad {pcb.Version()} found, {KICAD_VERSION} required')
    spec, contract, stackup, graph, db, template, project, proj = prepare_inputs(board)
    out = OUT_ROOT / board
    board_path = out / f'{board}.kicad_pcb'
    report_path = out / 'report.json'
    if not board_path.is_file() or not report_path.is_file():
        raise SystemExit(f'board_gen: {board} has no committed board/report: route it with [pcb-route {board}]')
    committed = read_json(report_path)
    problems = []
    if committed['inputs']['sha256'] != proj['sha256']:
        stale = sorted(k for k in proj['parts'] if committed['inputs']['parts'].get(k) != proj['parts'][k])
        problems.append(f'inputs changed ({", ".join(stale)}): re-route with [pcb-route {board}]')
    if committed['board_sha256'] != sha256_file(board_path):
        problems.append('board file differs from report.json board_sha256')
    if (out / 'fp-lib-table').read_text(encoding='utf-8') != fp_lib_table(template):
        problems.append('fp-lib-table is stale')
    route_log = read_json(out / 'route-log.json') if (out / 'route-log.json').is_file() else {}
    if route_log.get('board_sha256') != sha256_file(board_path):
        problems.append('route-log.json does not belong to the committed board')
    with tempfile.TemporaryDirectory(prefix=f'sr-rx-check-{board}-') as temp:
        drc_raw, _ = run_drc(board_path, Path(temp) / 'drc.json', save=False)
    report, connectors = audit_board(pcb, spec, contract, stackup, template, graph, db, proj, board_path, drc_raw,
                                     project)
    for name, fresh in (('report.json', dump(report)), ('connectors.json', dump(connectors)),
                        ('drc.json', dump(normalise_drc(drc_raw)))):
        path = out / name
        if not path.is_file() or path.read_text(encoding='utf-8') != fresh:
            old = read_json(path) if path.is_file() else {}
            new = json.loads(fresh)
            keys = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
            problems.append(f'{name} does not reproduce (keys {keys})')
    if not report['passed']:
        problems.append('board does not pass: ' + json.dumps(report['result'], ensure_ascii=False))
    print(dump({'board': board, 'passed': report['passed'], **report['result'], 'problems': problems}), end='')
    return 1 if problems else 0


def main(argv=None):
    faulthandler.enable()  # a crash inside pcbnew prints the Python stack (CI log) instead of a bare segfault
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--board')
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='read-only check of the committed board (default)')
    mode.add_argument('--route', action='store_true', help='place, route, pour, DRC and write the outputs')
    mode.add_argument('--inputs-only', action='store_true', help='standard-library projection check')
    mode.add_argument('--list-boards', action='store_true')
    mode.add_argument('--mode-from-commit', action='store_true',
                      help="print 'route' if $SR_RX_HEAD_COMMIT_MESSAGE carries [pcb-route BOARD], else 'check'")
    mode.add_argument('--fetch-freerouting', metavar='DIR', help='download and verify the pinned Freerouting JAR and JRE')
    ap.add_argument('--freerouting', help='directory filled by --fetch-freerouting (JAR and JRE)')
    args = ap.parse_args(argv)
    if args.list_boards:
        print(json.dumps(list_boards()))
        return 0
    if args.fetch_freerouting:
        fetch_freerouting(args.fetch_freerouting)
        return 0
    if not args.board or not re.fullmatch(r'[A-Z][A-Z0-9_]*', args.board):
        ap.error('--board BOARD (upper-case id of pcb/boards/<BOARD>.json) is required')
    if not spec_path(args.board).is_file():
        ap.error(f'no spec {rel(spec_path(args.board))}')
    if args.mode_from_commit:
        print('route' if route_requested(os.environ.get('SR_RX_HEAD_COMMIT_MESSAGE', ''), args.board) else 'check')
        return 0
    if args.inputs_only:
        return inputs_only(args.board)
    if args.route:
        if not args.freerouting:
            ap.error('--route needs --freerouting PATH')
        return route(args.board, args.freerouting)
    return check(args.board)


if __name__ == '__main__':
    sys.exit(main())
