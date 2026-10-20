#!/usr/bin/env python3
"""Read-only independent check of the unrouted detector-core placement board.

Uses only the Python standard library: no KiCad runtime, generator imports, or
generated placement-audit results. Run from any directory; paths default to this
checkout. A pass verifies placement-input fidelity, not fabrication readiness.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import uuid


def parse_sexpr(text):
    """Parse one complete KiCad S-expression without executing any input."""
    roots, stack = [], []
    i = 0
    while i < len(text):
        char = text[i]
        if char.isspace():
            i += 1
            continue
        if char == ';':
            newline = text.find('\n', i)
            i = len(text) if newline < 0 else newline + 1
            continue
        if char == '(':
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
            i += 1
            continue
        if char == ')':
            if not stack:
                raise ValueError('Unmatched closing parenthesis')
            stack.pop()
            i += 1
            continue
        if not stack:
            raise ValueError('Atom outside an S-expression')
        if char == '"':
            value = []
            i += 1
            while i < len(text) and text[i] != '"':
                char = text[i]
                if char == '\\':
                    i += 1
                    if i == len(text):
                        raise ValueError('Unterminated string escape')
                    char = {'n': '\n', 'r': '\r', 't': '\t'}.get(text[i], text[i])
                value.append(char)
                i += 1
            if i == len(text):
                raise ValueError('Unterminated quoted string')
            atom = ''.join(value)
            i += 1
        else:
            start = i
            while i < len(text) and not text[i].isspace() and text[i] not in '()':
                i += 1
            atom = text[start:i]
        stack[-1].append(atom)
    if stack or len(roots) != 1 or not roots[0]:
        raise ValueError('Expected one balanced, nonempty S-expression')
    return roots[0]


def children(node, key):
    return [item for item in node[1:]
            if isinstance(item, list) and item and item[0] == key]


def child(node, key):
    found = children(node, key)
    if len(found) > 1:
        raise ValueError(f'Duplicate {key} field')
    return found[0] if found else None


def walk(node):
    yield node
    for item in node:
        if isinstance(item, list):
            yield from walk(item)


def pad_net(pad):
    net = child(pad, 'net')
    if net is None:
        return ''
    if len(net) not in (2, 3):
        raise ValueError('Unrecognized pad net field')
    return net[-1]  # KiCad 10 name-only and older code/name forms.


def pad_geometry(pad):
    result = [tuple(pad[2:4])]
    for key in ('at', 'size', 'drill'):
        entry = child(pad, key)
        values = entry[1:] if entry else []
        normalized = []
        for value in values:
            try:
                normalized.append(float(value))
            except (ValueError, TypeError):
                normalized.append(value)
        # An omitted local pad rotation is zero.
        if key == 'at' and len(normalized) == 2:
            normalized.append(0.0)
        result.append(normalized)
    layers = child(pad, 'layers')
    result.append(sorted(layers[1:]) if layers else [])
    return result


def inspect_outline(board):
    edges = [n for n in board[1:] if isinstance(n, list)
             and child(n, 'layer') == ['layer', 'Edge.Cuts']]
    if not edges or any(n[0] != 'gr_line' for n in edges):
        raise ValueError('Candidate outline must consist of line segments')
    graph = defaultdict(list)
    segments = []
    for edge in edges:
        start = tuple(map(float, child(edge, 'start')[1:]))
        end = tuple(map(float, child(edge, 'end')[1:]))
        if len(start) != 2 or len(end) != 2 or start == end:
            raise ValueError('Invalid outline segment')
        graph[start].append(end)
        graph[end].append(start)
        segments.append((start, end))
    if any(len(neighbors) != 2 for neighbors in graph.values()):
        raise ValueError('Outline endpoints do not have degree two')
    first = next(iter(graph))
    order, previous, current = [], None, first
    while current not in order:
        order.append(current)
        neighbors = graph[current]
        following = neighbors[0] if neighbors[0] != previous else neighbors[1]
        previous, current = current, following
    if current != first or len(order) != len(graph):
        raise ValueError('Outline does not form a single closed loop')
    # This candidate is deliberately a rectangle; also reject bow-ties or
    # overlapping segments that a degree-only closure test would miss.
    xs, ys = {p[0] for p in graph}, {p[1] for p in graph}
    if (len(edges) != 4 or len(xs) != 2 or len(ys) != 2
            or set(graph) != {(x, y) for x in xs for y in ys}
            or any(a[0] != b[0] and a[1] != b[1] for a, b in segments)):
        raise ValueError('Expected the closed rectangular candidate outline')
    return dict(closed=True, segment_count=len(edges), vertices=order,
                width_mm=max(xs) - min(xs), height_mm=max(ys) - min(ys))


def compare(project, input_path, board_path, drc_path):
    captured = {}

    def read(path):
        path = path.resolve()
        if path not in captured:
            captured[path] = path.read_bytes()
        return captured[path]

    source = json.loads(read(input_path))
    board = parse_sexpr(read(board_path).decode('utf-8'))
    drc = json.loads(read(drc_path))
    if board[0] != 'kicad_pcb':
        raise ValueError('Board file is not a kicad_pcb expression')
    issues = []

    def check(condition, category, detail):
        if not condition:
            issues.append(dict(category=category, detail=detail))

    expected, expected_ids, components = {}, {}, {}
    for component in source['components']:
        ref = component['ref']
        check(ref not in components, 'duplicate_source_reference', ref)
        components[ref] = component
        expected_ids[ref] = component['placement_footprint']
        pins = {}
        for pin in component['pins']:
            number = str(pin['number'])
            check(number not in pins, 'duplicate_source_pin', f'{ref}.{number}')
            check(bool(pin.get('net')) != bool(pin.get('nc')),
                  'source_pin_net_xor_nc', f'{ref}.{number}')
            pins[number] = pin.get('net') or ''
        expected[ref] = pins
    check(source['part_count'] == len(expected), 'source_part_count', source['part_count'])

    actual, actual_ids, actual_pads = {}, {}, {}
    for footprint in children(board, 'footprint'):
        refs = [p[2] for p in children(footprint, 'property') if p[1] == 'Reference']
        if len(refs) != 1:
            issues.append(dict(category='board_reference', detail=refs))
            continue
        ref = refs[0]
        check(ref not in actual, 'duplicate_board_reference', ref)
        actual_ids[ref] = footprint[1]
        pads, pad_nodes = {}, {}
        for pad in children(footprint, 'pad'):
            number = pad[1]
            check(number not in pads, 'duplicate_board_pad', f'{ref}.{number}')
            pads[number] = pad_net(pad)
            pad_nodes[number] = pad
        actual[ref], actual_pads[ref] = pads, pad_nodes

    check(set(actual) == set(expected), 'component_set',
          dict(missing=sorted(set(expected) - set(actual)),
               extra=sorted(set(actual) - set(expected))))
    for ref, pins in expected.items():
        found = actual.get(ref, {})
        check(set(pins) == set(found), 'pad_set',
              dict(ref=ref, missing=sorted(set(pins) - set(found)),
                   extra=sorted(set(found) - set(pins))))
        for pin, net in pins.items():
            check(found.get(pin) == net, 'pad_net',
                  dict(ref=ref, pin=pin, expected=net, actual=found.get(pin)))
        check(actual_ids.get(ref) == expected_ids[ref], 'footprint_id',
              dict(ref=ref, expected=expected_ids[ref], actual=actual_ids.get(ref)))

    # Check the actual retained library candidates independently, including pad
    # geometry, rather than accepting a matching FPID string as sufficient.
    library_files = set()
    table = parse_sexpr(read(board_path.parent / 'fp-lib-table').decode('utf-8'))
    libraries = {child(entry, 'name')[1]: child(entry, 'uri')[1]
                 for entry in children(table, 'lib')}
    for ref, component in components.items():
        library_name, footprint_name = expected_ids[ref].split(':', 1)
        uri = libraries[library_name].replace('${KIPRJMOD}', str(board_path.parent.resolve()))
        check('${' not in uri, 'unresolved_library_uri', uri)
        library_dir = Path(uri)
        if not library_dir.is_absolute():
            library_dir = board_path.parent / library_dir
        path = library_dir / (footprint_name + '.kicad_mod')
        declared_file = component.get('placement_footprint_file')
        if declared_file:
            declared_path = Path(declared_file)
            if not declared_path.is_absolute():
                declared_path = project / declared_path
            check(declared_path.resolve() == path.resolve(), 'declared_library_path', ref)
        library = parse_sexpr(read(path).decode('utf-8'))
        library_files.add(path.resolve())
        check(library[0] == 'footprint'
              and library[1] == expected_ids[ref].split(':', 1)[-1],
              'library_candidate_id', dict(ref=ref, path=str(path)))
        pads = children(library, 'pad')
        numbers = [p[1] for p in pads]
        check(Counter(numbers) == Counter(expected[ref].keys()), 'library_candidate_pad_set', ref)
        for pad in pads:
            placed = actual_pads.get(ref, {}).get(pad[1])
            check(placed is not None and pad_geometry(placed) == pad_geometry(pad),
                  'library_candidate_pad_geometry', f'{ref}.{pad[1]}')

    connected = {(r, p, n) for r, pins in expected.items() for p, n in pins.items() if n}
    listed = [(node['ref'], str(node['pin']), net)
              for net, nodes in source['nets'].items() for node in nodes]
    check(len(listed) == len(set(listed)) and set(listed) == connected,
          'source_net_table', 'Component pins and redundant net table must agree')
    nc = sorted((r, p) for r, pins in expected.items() for p, n in pins.items() if not n)
    boundary = source['external_boundary']
    for interface in boundary:
        for node in interface['core_nodes']:
            check(actual.get(node['ref'], {}).get(str(node['pin'])) == interface['net'],
                  'boundary_net', dict(net=interface['net'], ref=node['ref'], pin=node['pin']))
    excluded = set(source['must_remain_at_RF_port'])
    check(not excluded & set(actual), 'excluded_RF_port_components', sorted(excluded & set(actual)))

    uuids = [n[1] for n in walk(board) if n and n[0] == 'uuid']
    check(len(uuids) == len(set(uuids)), 'duplicate_uuid',
          {key: count for key, count in Counter(uuids).items() if count > 1})
    for value in uuids:
        try:
            uuid.UUID(value)
        except ValueError:
            issues.append(dict(category='invalid_uuid', detail=value))
    routing = {key: len(children(board, key)) for key in ('segment', 'arc', 'via', 'zone')}
    check(not any(routing.values()), 'routed_copper_or_zones', routing)
    outline = inspect_outline(board)

    unconnected = drc['unconnected_items']
    expected_airwires = len(connected) - len(source['nets'])
    check(len(unconnected) == expected_airwires, 'raw_DRC_unconnected_count',
          dict(expected=expected_airwires, actual=len(unconnected)))
    check(all(item.get('type') == 'unconnected_items' and item.get('severity') == 'error'
              for item in unconnected), 'raw_DRC_unconnected_classification', 'Expected errors only')
    check(not drc['violations'], 'raw_DRC_other_violations', len(drc['violations']))
    check(not drc['schematic_parity'], 'raw_DRC_schematic_parity', len(drc['schematic_parity']))
    check(not drc['ignored_checks'], 'raw_DRC_ignored_checks', drc['ignored_checks'])
    check(set(drc['included_severities']) == {'error', 'warning', 'exclusion'},
          'raw_DRC_severity_filter', drc['included_severities'])
    # Check that raw DRC pad references belong to this exact board snapshot.
    pad_uuids = {child(pad, 'uuid')[1] for pads in actual_pads.values() for pad in pads.values()}
    for item in unconnected:
        for node in item['items']:
            check(node.get('uuid') in pad_uuids, 'raw_DRC_unknown_pad_uuid', node.get('uuid'))

    for path, data in captured.items():
        check(path.read_bytes() == data, 'snapshot_changed_during_check', str(path))

    def display(path):
        try:
            return str(path.resolve().relative_to(project.resolve()))
        except ValueError:
            return str(path)

    return dict(passed=not issues,
                methodology='Independent stdlib S-expression and JSON parsers; no generator or audit imports.',
                counts=dict(source_components=len(expected), board_components=len(actual),
                            source_pins=sum(map(len, expected.values())),
                            board_pads=sum(map(len, actual.values())), connected_pins=len(connected),
                            nets=len(source['nets']), nc_pads=len(nc), boundary_nets=len(boundary),
                            excluded_RF_port_references=len(excluded), unique_library_candidates=len(library_files),
                            uuids=len(uuids), unique_uuids=len(set(uuids))),
                nc_pads=[dict(ref=r, pin=p) for r, p in nc], routing=routing, outline=outline,
                raw_DRC=dict(version=drc.get('kicad_version'), date=drc.get('date'),
                             unconnected_items=len(unconnected), expected_unconnected_items=expected_airwires,
                             violations=len(drc['violations']), schematic_parity=len(drc['schematic_parity']),
                             ignored_checks=drc['ignored_checks'], included_severities=drc['included_severities'],
                             unconnected_severities=dict(Counter(i.get('severity') for i in unconnected))),
                sha256={display(p): hashlib.sha256(data).hexdigest()
                        for p, data in captured.items()}, issues=issues)


def main():
    project = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=project / 'pcb/generated/detector-core-input.json')
    parser.add_argument('--board', type=Path,
                        default=project / 'build/kicad/pcb-preparation/detector-core-placement.kicad_pcb')
    parser.add_argument('--drc', type=Path, default=project / 'build/kicad/pcb-preparation/drc-raw.json')
    args = parser.parse_args()
    try:
        result = compare(project, args.input, args.board, args.drc)
    except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
        result = dict(passed=False, issues=[dict(category='parse_or_schema_error', detail=str(error))])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
