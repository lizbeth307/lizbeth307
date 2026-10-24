#!/usr/bin/env python3
"""Independently inspect the routed DC_CORE prototype using only stdlib.

Prints JSON and exits nonzero on mismatch. No KiCad runtime or generator/audit
imports are used. All inputs are read-only. A pass does not approve fabrication,
external interconnects, proposed passive MPNs, or analog performance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import math
from pathlib import Path
import json
import sys
import uuid

sys.dont_write_bytecode = True
from independent_pcb_check import (child, children, inspect_outline,
                                   pad_geometry, pad_net, parse_sexpr, walk)


FROZEN_INPUT_SHA256 = '14a5d3988a0e6e33a5e7b7134292d833edd25feafd3629fe5a69fc78db302892'
FROZEN_STARTER_SHA256 = '25f586a5ec5ed50ef954a659732321277c03267a7f446fefc1e16512c8183ec6'
SENSE_NETS = ('E4_DCS_UHF_SENSE', 'E4_DCS_LBAND_SENSE', 'E4_DCS_HF_SENSE')
EPS = 1e-7


def field_point(node, key):
    return tuple(map(float, child(node, key)[1:3]))


def segment_point_distance(a, b, p):
    dx, dy = b[0] - a[0], b[1] - a[1]
    norm = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / norm)) if norm else 0.0
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def segment_distance(a, b, c, d):
    """Minimum distance between two closed segments; zero when they cross."""
    orient = lambda p, q, r: (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2, d3, d4 = orient(c, d, a), orient(c, d, b), orient(a, b, c), orient(a, b, d)
    if d1 * d2 < 0 and d3 * d4 < 0:
        return 0.0
    return min(segment_point_distance(a, b, c), segment_point_distance(a, b, d),
               segment_point_distance(c, d, a), segment_point_distance(c, d, b))


def boxes_meet(x, y):
    return x[0] <= y[2] and y[0] <= x[2] and x[1] <= y[3] and y[1] <= x[3]


def segment_box_distance(a, b, half_x, half_y):
    """Distance between a segment and an axis-aligned centered rectangle."""
    low, high = 0.0, 1.0
    for start, delta, extent in zip(a, (b[0] - a[0], b[1] - a[1]), (half_x, half_y)):
        if abs(delta) <= EPS:
            if abs(start) > extent:
                break
        else:
            t0, t1 = (-extent - start) / delta, (extent - start) / delta
            low, high = max(low, min(t0, t1)), min(high, max(t0, t1))
            if low > high:
                break
    else:
        if low <= high:
            return 0.0
    point_distance = lambda p: math.hypot(max(abs(p[0]) - half_x, 0.0),
                                          max(abs(p[1]) - half_y, 0.0))
    return min(point_distance(a), point_distance(b),
               *(segment_point_distance(a, b, (x, y))
                 for x in (-half_x, half_x) for y in (-half_y, half_y)))


def point_in_polygon(point, polygon):
    inside = False
    x, y = point
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y):
            crossing = (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]
            if x < crossing:
                inside = not inside
    return inside


def pad_shape(footprint, pad):
    origin = field_point(footprint, 'at')
    fp_at, at = child(footprint, 'at'), child(pad, 'at')
    angle = float(fp_at[3]) if len(fp_at) > 3 else 0.0
    theta = math.radians(angle)
    x, y = map(float, at[1:3])
    center = (origin[0] + x * math.cos(theta) + y * math.sin(theta),
              origin[1] - x * math.sin(theta) + y * math.cos(theta))
    # KiCad's serialized pad orientation is absolute board rotation.
    pad_angle = float(at[3]) if len(at) > 3 else 0.0
    sx, sy = map(float, child(pad, 'size')[1:3])
    shape = pad[3]
    if shape == 'roundrect':
        ratio = child(pad, 'roundrect_rratio')
        radius = min(sx, sy) * float(ratio[1]) if ratio else 0.0
    elif shape in ('oval', 'circle'):
        radius = min(sx, sy) / 2
    elif shape == 'rect':
        radius = 0.0
    else:
        raise ValueError(f'Unsupported NC pad shape: {shape}')
    return dict(center=center, angle=pad_angle, half_x=sx / 2 - radius,
                half_y=sy / 2 - radius, radius=radius,
                layers=child(pad, 'layers')[1:])


def local(point, shape):
    x, y = point[0] - shape['center'][0], point[1] - shape['center'][1]
    theta = math.radians(shape['angle'])
    return x * math.cos(theta) - y * math.sin(theta), x * math.sin(theta) + y * math.cos(theta)


def touches_pad(a, b, copper_radius, shape):
    distance = segment_box_distance(local(a, shape), local(b, shape), shape['half_x'], shape['half_y'])
    return distance <= copper_radius + shape['radius'] + EPS


def geometry_with_local_angle(pad, footprint_angle):
    signature = pad_geometry(pad)
    signature[1][2] = (signature[1][2] - footprint_angle) % 360
    ratio = child(pad, 'roundrect_rratio')
    signature.append(float(ratio[1]) if ratio else None)
    return signature


def compare(project, source_path, starter_path, board_path, drc_path, review_path=None):
    captured = {}

    def read(path):
        path = path.resolve()
        if path not in captured:
            captured[path] = path.read_bytes()
        return captured[path]

    digest = lambda data: hashlib.sha256(data).hexdigest()
    source_data, starter_data = read(source_path), read(starter_path)
    source = json.loads(source_data)
    starter = parse_sexpr(starter_data.decode())
    board = parse_sexpr(read(board_path).decode())
    drc = json.loads(read(drc_path))
    review = json.loads(read(review_path or project / 'verification/pcb-prototype-review.json'))
    issues = []

    def check(condition, category, detail):
        if not condition:
            issues.append(dict(category=category, detail=detail))

    # A clean DRC file counts only for the exact board the routing run checked.
    check(review.get('published_board') is True and review.get('board_sha256') == digest(read(board_path)),
          'DRC_board_binding', review.get('board_sha256'))
    check(review.get('drc', {}).get('raw_sha256') == digest(read(drc_path)),
          'DRC_report_binding', review.get('drc', {}).get('raw_sha256'))

    check(digest(source_data) == FROZEN_INPUT_SHA256, 'frozen_input_hash', digest(source_data))
    check(digest(starter_data) == FROZEN_STARTER_SHA256, 'frozen_starter_hash', digest(starter_data))
    check(board[0] == 'kicad_pcb' and starter[0] == 'kicad_pcb', 'board_expression', board[0])
    expected, components = {}, {}
    for comp in source['components']:
        ref = comp['ref']
        check(ref not in expected, 'duplicate_source_ref', ref)
        components[ref] = comp
        pins = {}
        for pin in comp['pins']:
            number = str(pin['number'])
            check(number not in pins, 'duplicate_source_pin', f'{ref}.{number}')
            check(bool(pin.get('net')) != bool(pin.get('nc')), 'source_net_xor_nc', f'{ref}.{number}')
            pins[number] = pin.get('net') or ''
        expected[ref] = pins
    actual, footprints, pad_nodes, nc_shapes, netted_shapes = {}, {}, {}, [], []
    for footprint in children(board, 'footprint'):
        refs = [p[2] for p in children(footprint, 'property') if p[1] == 'Reference']
        if len(refs) != 1:
            check(False, 'footprint_reference', refs)
            continue
        ref = refs[0]
        check(ref not in actual, 'duplicate_board_ref', ref)
        footprints[ref] = footprint
        actual[ref], pad_nodes[ref] = {}, {}
        for pad in children(footprint, 'pad'):
            number = pad[1]
            check(number not in actual[ref], 'duplicate_board_pad', f'{ref}.{number}')
            actual[ref][number], pad_nodes[ref][number] = pad_net(pad), pad
            if not pad_net(pad):
                nc_shapes.append((f'{ref}.{number}', pad_shape(footprint, pad)))
            else:
                netted_shapes.append((f'{ref}.{number}', pad_net(pad), pad_shape(footprint, pad)))
    check(set(actual) == set(expected), 'component_set',
          dict(missing=sorted(set(expected) - set(actual)), extra=sorted(set(actual) - set(expected))))
    for ref, pins in expected.items():
        found = actual.get(ref, {})
        check(set(found) == set(pins), 'pad_set', dict(ref=ref, expected=sorted(pins), actual=sorted(found)))
        for number, net in pins.items():
            check(found.get(number) == net, 'pad_net',
                  dict(ref=ref, pin=number, expected=net, actual=found.get(number)))
        if ref in footprints:
            check(footprints[ref][1] == components[ref]['placement_footprint'], 'footprint_id', ref)

    table_path = board_path.parent / 'fp-lib-table'
    table = parse_sexpr(read(table_path).decode())
    libraries = {child(lib, 'name')[1]: child(lib, 'uri')[1] for lib in children(table, 'lib')}
    candidate_paths = set()
    for ref, comp in components.items():
        library_name, name = comp['placement_footprint'].split(':', 1)
        uri = libraries[library_name].replace('${KIPRJMOD}', str(board_path.parent.resolve()))
        check('${' not in uri, 'unresolved_library_path', uri)
        directory = Path(uri)
        if not directory.is_absolute():
            directory = board_path.parent / directory
        path = directory / (name + '.kicad_mod')
        candidate_paths.add(path.resolve())
        candidate = parse_sexpr(read(path).decode())
        check(candidate[0:2] == ['footprint', name], 'candidate_identity', ref)
        pads = children(candidate, 'pad')
        check(Counter(p[1] for p in pads) == Counter(expected[ref].keys()), 'candidate_pads', ref)
        fp = footprints.get(ref)
        if fp is None:
            continue
        fp_at = child(fp, 'at')
        angle = float(fp_at[3]) if len(fp_at) > 3 else 0.0
        for pad in pads:
            placed = pad_nodes.get(ref, {}).get(pad[1])
            check(placed is not None and geometry_with_local_angle(placed, angle)
                  == geometry_with_local_angle(pad, 0.0), 'candidate_pad_geometry', f'{ref}.{pad[1]}')

    net_names = set(source['nets'])
    connected = {(r, p, n) for r, pins in expected.items() for p, n in pins.items() if n}
    listed = [(node['ref'], str(node['pin']), net)
              for net, nodes in source['nets'].items() for node in nodes]
    check(set(listed) == connected and len(listed) == len(set(listed)), 'source_net_table', 'pin/net equality')
    boundary_names = [entry['net'] for entry in source['external_boundary']]
    for entry in source['external_boundary']:
        for node in entry['core_nodes']:
            check(actual.get(node['ref'], {}).get(str(node['pin'])) == entry['net'], 'boundary_pad', node)
    excluded = set(source['must_remain_at_RF_port'])
    check(not excluded & set(actual), 'RF_port_exclusions', sorted(excluded & set(actual)))

    uuids = [node[1] for node in walk(board) if node and node[0] == 'uuid']
    check(len(uuids) == len(set(uuids)), 'duplicate_uuid',
          {key: count for key, count in Counter(uuids).items() if count > 1})
    for value in uuids:
        try:
            uuid.UUID(value)
        except ValueError:
            check(False, 'invalid_uuid', value)
    outline = inspect_outline(board)
    check(outline['width_mm'] == 125 and outline['height_mm'] == 115, 'candidate_outline_size', outline)
    routing = {kind: children(board, kind) for kind in ('segment', 'arc', 'via', 'zone')}
    check(bool(routing['segment']), 'missing_routing', 'Expected routed prototype copper')
    check(not routing['arc'], 'unsupported_copper_arcs', len(routing['arc']))
    sense = {net: dict(segment_count=0, total_track_length_mm=0.0, via_count=0,
                       layers=set(), points=[]) for net in SENSE_NETS}
    copper_overlaps, copper, shorts = [], [], []

    def add_copper(kind, net, layers, a, b, radius):
        box = (min(a[0], b[0]) - radius, min(a[1], b[1]) - radius, max(a[0], b[0]) + radius, max(a[1], b[1]) + radius)
        copper.append(dict(id=f'{kind}{len(copper)}@{a[0]:g},{a[1]:g}', net=net, layers=set(layers), a=a, b=b, r=radius, box=box))

    for segment in routing['segment']:
        net = pad_net(segment)
        check(net in net_names, 'unknown_track_net', net)
        a, b = field_point(segment, 'start'), field_point(segment, 'end')
        width = float(child(segment, 'width')[1])
        layer = child(segment, 'layer')[1]
        check(layer in ('F.Cu', 'B.Cu') and width > 0, 'invalid_track_geometry', dict(net=net, layer=layer, width=width))
        add_copper('segment', net, [layer], a, b, width / 2)
        if net in sense:
            metric = sense[net]
            metric['segment_count'] += 1
            metric['total_track_length_mm'] += math.dist(a, b)
            metric['layers'].add(layer)
            metric['points'].extend([a, b])
        for refpin, shape in nc_shapes:
            if (layer in shape['layers'] or '*.Cu' in shape['layers']) and touches_pad(a, b, width / 2, shape):
                copper_overlaps.append(dict(nc_pad=refpin, object='segment', net=net))
    for via in routing['via']:
        net, position = pad_net(via), field_point(via, 'at')
        check(net in net_names, 'unknown_via_net', net)
        size, drill = float(child(via, 'size')[1]), float(child(via, 'drill')[1])
        check(size > drill > 0, 'invalid_via_geometry', dict(net=net, size=size, drill=drill))
        add_copper('via', net, ('F.Cu', 'B.Cu'), position, position, size / 2)
        if net in sense:
            sense[net]['via_count'] += 1
        for refpin, shape in nc_shapes:
            if touches_pad(position, position, size / 2, shape):
                copper_overlaps.append(dict(nc_pad=refpin, object='via', net=net))

    filled_polygon_count = 0
    for zone in routing['zone']:
        check(pad_net(zone) == 'GND', 'non_GND_zone', pad_net(zone))
        layers = child(zone, 'layers') or child(zone, 'layer')
        check(layers is not None and set(layers[1:]) <= {'F.Cu', 'B.Cu'}, 'zone_layers', layers)
        filled = children(zone, 'filled_polygon')
        check(bool(filled), 'unfilled_GND_zone', 'No retained filled polygons')
        for polygon in filled:
            filled_polygon_count += 1
            layer = child(polygon, 'layer')[1]
            check(layer in ('F.Cu', 'B.Cu'), 'filled_polygon_layer', layer)
            points = [tuple(map(float, point[1:3])) for point in children(child(polygon, 'pts'), 'xy')]
            check(len(points) >= 3, 'invalid_filled_polygon', len(points))
            for refpin, shape in nc_shapes:
                if layer not in shape['layers'] and '*.Cu' not in shape['layers']:
                    continue
                if point_in_polygon(shape['center'], points) or any(
                        touches_pad(a, b, 0.0, shape) for a, b in zip(points, points[1:] + points[:1])):
                    copper_overlaps.append(dict(nc_pad=refpin, object='filled_GND_polygon', layer=layer))
            edges = [(a, b, (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])))
                     for a, b in zip(points, points[1:] + points[:1])]
            for item in copper:
                if item['net'] != pad_net(zone) and layer in item['layers'] and (point_in_polygon(item['a'], points) or any(
                        boxes_meet(item['box'], box) and segment_distance(item['a'], item['b'], a, b) <= item['r'] + EPS
                        for a, b, box in edges)):
                    shorts.append(dict(objects=[item['id'], 'filled_polygon'], nets=[item['net'], pad_net(zone)], layer=layer))
            for refpin, net, shape in netted_shapes:
                if net != pad_net(zone) and (layer in shape['layers'] or '*.Cu' in shape['layers']) and (
                        point_in_polygon(shape['center'], points)
                        or any(touches_pad(a, b, 0.0, shape) for a, b, _ in edges)):
                    shorts.append(dict(objects=[refpin, 'filled_polygon'], nets=[net, pad_net(zone)], layer=layer))
    check(bool(routing['zone']) and filled_polygon_count > 0, 'missing_filled_GND_zone', filled_polygon_count)
    check(not copper_overlaps, 'NC_pad_copper_overlap', copper_overlaps)
    # Independent short check: DRC is not trusted alone for contact between nets.
    for i, item in enumerate(copper):
        for other in copper[i + 1:]:
            if (item['net'] != other['net'] and item['layers'] & other['layers'] and boxes_meet(item['box'], other['box'])
                    and segment_distance(item['a'], item['b'], other['a'], other['b']) <= item['r'] + other['r'] + EPS):
                shorts.append(dict(objects=[item['id'], other['id']], nets=[item['net'], other['net']]))
        for refpin, net, shape in netted_shapes:
            reach = math.hypot(shape['half_x'], shape['half_y']) + shape['radius'] + item['r'] + EPS
            if (net != item['net'] and (item['layers'] & set(shape['layers']) or '*.Cu' in shape['layers'])
                    and segment_point_distance(item['a'], item['b'], shape['center']) <= reach
                    and touches_pad(item['a'], item['b'], item['r'], shape)):
                shorts.append(dict(objects=[item['id'], refpin], nets=[item['net'], net]))
    check(not shorts, 'inter_net_copper_contact', shorts[:20])
    for net, metric in sense.items():
        check(metric['segment_count'] > 0, 'unrouted_SENSE_net', net)
        check(metric['via_count'] == 0, 'SENSE_vias', dict(net=net, vias=metric['via_count']))
        points = metric.pop('points')
        metric['layers'] = sorted(metric['layers'])
        metric['total_track_length_mm'] = round(metric['total_track_length_mm'], 6)
        if points:
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            metric['bounding_box_mm'] = dict(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys),
                                             width=max(xs) - min(xs), height=max(ys) - min(ys))

    counts = dict(source_components=len(expected), board_components=len(actual),
                  source_pins=sum(map(len, expected.values())), board_pads=sum(map(len, actual.values())),
                  connected_pins=len(connected), nets=len(net_names), nc_pads=len(nc_shapes),
                  boundary_nets=len(boundary_names), RF_port_exclusions=len(excluded),
                  unique_library_candidates=len(candidate_paths), uuids=len(uuids), unique_uuids=len(set(uuids)),
                  **{kind: len(nodes) for kind, nodes in routing.items()}, filled_GND_polygons=filled_polygon_count)
    for key, expected_count in dict(source_components=71, board_components=71, source_pins=187,
                                     board_pads=187, connected_pins=180, nets=40, nc_pads=7,
                                     boundary_nets=8, RF_port_exclusions=18).items():
        check(counts[key] == expected_count, 'contract_count', dict(key=key, expected=expected_count, actual=counts[key]))
    for section in ('violations', 'unconnected_items', 'schematic_parity', 'ignored_checks'):
        check(isinstance(drc[section], list) and len(drc[section]) == 0, 'raw_DRC_' + section, drc[section])
    check(set(drc['included_severities']) == {'error', 'warning', 'exclusion'}, 'raw_DRC_severities', drc['included_severities'])
    check(drc['source'] == board_path.name, 'raw_DRC_source', drc['source'])
    for path, data in captured.items():
        check(path.read_bytes() == data, 'snapshot_changed', str(path))

    def display(path):
        try:
            return path.relative_to(project.resolve()).as_posix()
        except ValueError:
            return str(path)

    return dict(passed=not issues, issues=issues, counts=counts, boundary_net_names=boundary_names,
                methodology='Independent stdlib S-expression/JSON parsing, NC-pad and inter-net copper contact geometry, and DRC-to-board hash binding; no generator/audit imports.',
                scope='Prototype topology and retained copper/DRC checks; physical external interfaces and analog performance remain unqualified.',
                outline=outline, SENSE_routing=sense,
                SENSE_metric_note='Track centerline lengths and bounding boxes are measured, not TI layout limits or analog qualification.',
                raw_DRC=dict(version=drc.get('kicad_version'), date=drc.get('date'),
                             **{section: len(drc[section]) for section in ('violations', 'unconnected_items', 'schematic_parity', 'ignored_checks')},
                             included_severities=drc['included_severities']),
                sha256={display(path): digest(data) for path, data in captured.items()})


def main():
    project = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=project / 'pcb/generated/detector-core-input.json')
    parser.add_argument('--starter', type=Path, default=project / 'build/kicad/pcb-preparation/detector-core-placement.kicad_pcb')
    parser.add_argument('--board', type=Path, default=project / 'build/kicad/pcb-prototype/detector-core-routed-prototype.kicad_pcb')
    parser.add_argument('--drc', type=Path, default=project / 'build/kicad/pcb-prototype/drc-raw.json')
    parser.add_argument('--review', type=Path, default=project / 'verification/pcb-prototype-review.json',
                        help='Routing record binding the raw DRC report to the board SHA256')
    args = parser.parse_args()
    try:
        result = compare(project, args.input, args.starter, args.board, args.drc, args.review)
    except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
        result = dict(passed=False, issues=[dict(category='parse_or_schema_error', detail=str(error))])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
