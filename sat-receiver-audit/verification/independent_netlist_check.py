#!/usr/bin/env python3
"""Independently compare KiCad's XML netlist with the reviewed sheet graphs.

Uses only Python's standard library and does not import the project generator or
validator. Run from any directory. Defaults are relative to this script's repo.
Power flags are explicit annotations and are excluded from hardware node counts.
The check does not establish PCB correctness or close hardware acceptance gates.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(project, netfile, working=None):
    design = project / 'design'
    expected = {}
    nc = set()
    values = {}
    flags = {}
    graphs = {}
    schema_errors = []
    working_diffs = []
    dnp = []
    pin_count = 0
    top_level_power_flags = []
    for path in sorted(design.glob('E[1-5].json')):
        graphs[path.name] = sha256(path)
        if working is not None and path.read_bytes() != (working / path.name).read_bytes():
            working_diffs.append(path.name)
        doc = json.loads(path.read_text())
        top_level_power_flags.extend(dict(sheet=doc['sheet'], **item) for item in doc.get('power_flags', []))
        for comp in doc['components']:
            ref = comp['ref']
            if ref in values or ref in flags:
                schema_errors.append(f'Duplicate component reference: {ref}')
            nums = [pin['number'] for pin in comp['pins']]
            for num, count in Counter(nums).items():
                if count != 1:
                    schema_errors.append(f'Duplicate pin number: {ref}.{num}')
            if comp.get('kind') == 'power_flag':
                flags[ref] = [pin.get('net') for pin in comp['pins']]
                continue
            values[ref] = comp['value']
            if comp.get('dnp'):
                dnp.append(ref)
            for pin in comp['pins']:
                pin_count += 1
                key = (ref, pin['number'])
                if bool(pin.get('net')) == bool(pin.get('nc')):
                    schema_errors.append(f'Pin must have net xor nc: {ref}.{pin["number"]}')
                if pin.get('net'):
                    expected[key] = pin['net']
                elif pin.get('nc'):
                    nc.add(key)

    root = ET.parse(netfile).getroot()
    actual = {}
    duplicates = []
    components = {}
    for comp in root.findall('./components/comp'):
        ref = comp.attrib['ref']
        if ref in components:
            schema_errors.append(f'Duplicate XML component reference: {ref}')
        components[ref] = comp.findtext('value')
    for net in root.findall('./nets/net'):
        for node in net.findall('node'):
            key = (node.attrib['ref'], node.attrib['pin'])
            if key in actual:
                duplicates.append({'ref': key[0], 'pin': key[1],
                                   'nets': [actual[key], net.attrib['name']]})
            actual[key] = net.attrib['name']
    missing = [{'ref': r, 'pin': p, 'expected': name}
               for (r, p), name in expected.items() if (r, p) not in actual]
    wrong = [{'ref': r, 'pin': p, 'expected': name, 'actual': actual[(r, p)]}
             for (r, p), name in expected.items()
             if (r, p) in actual and actual[(r, p)] != name]
    extras = [{'ref': r, 'pin': p, 'actual': name}
              for (r, p), name in actual.items()
              if (r, p) not in expected and (r, p) not in nc and r not in flags]
    nc_connected = [{'ref': r, 'pin': p, 'actual': actual[(r, p)]}
                    for r, p in sorted(nc)
                    if (r, p) in actual and not actual[(r, p)].startswith('unconnected-')]
    missing_comps = sorted(set(values) - set(components))
    extra_comps = sorted(set(components) - set(values) - set(flags))
    value_changes = [{'ref': r, 'expected': value, 'actual': components[r]}
                     for r, value in values.items()
                     if r in components and components[r].strip() != value.strip()]
    whitespace_normalizations = [{'ref': r, 'graph_value': value, 'xml_value': components[r]}
                                 for r, value in values.items() if r in components
                                 and components[r] != value
                                 and components[r].strip() == value.strip()]
    raw_pack_on_gnd = [{'ref': r, 'pin': p, 'actual': name}
                       for (r, p), name in actual.items()
                       if name == 'GND' and 'Daly' in values.get(r, '') and p in ('B0', 'B-')]
    checks = dict(schema_errors=schema_errors, working_graph_differences=working_diffs,
                  missing_connected_pins=missing, wrong_net_assignments=wrong,
                  extra_connected_pins=extras, duplicate_node_assignments=duplicates,
                  nc_pins_unexpectedly_connected=nc_connected,
                  missing_hardware_components=missing_comps,
                  extra_hardware_components=extra_comps,
                  component_value_mismatches=value_changes,
                  raw_pack_negative_on_GND=raw_pack_on_gnd)
    return dict(passed=not any(checks.values()),
                methodology='Independent stdlib JSON and XML parsers; no generator/validator imports.',
                graph_sha256=graphs, netlist_sha256=sha256(netfile),
                counts=dict(hardware_components=len(values),
                            hardware_pin_declarations=pin_count,
                            connected_hardware_pins=len(expected),
                            connected_hardware_nets=len(set(expected.values())),
                            declared_nc_pins=len(nc),
                            xml_hardware_components=len(components),
                            xml_pin_nodes=len(actual),
                            xml_nets=len(root.findall('./nets/net')),
                            explicit_power_flags=len(flags) + len(top_level_power_flags)),
                dnp_components=dnp, power_flag_components=flags,
                power_flag_annotations=top_level_power_flags,
                value_whitespace_normalizations=whitespace_normalizations, checks=checks)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--netlist', type=Path, help='Default: PROJECT/verification/netlist.xml')
    ap.add_argument('--working-design', type=Path,
                    help='Optional extra graph directory; require byte-identical staged graphs')
    ap.add_argument('--report', type=Path,
                    help='Default: PROJECT/verification/independent-netlist-review.json')
    args = ap.parse_args()
    project = args.project_root.resolve()
    netfile = args.netlist or project / 'verification/netlist.xml'
    output = args.report or project / 'verification/independent-netlist-review.json'
    result = compare(project, netfile, args.working_design)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'counts': result['counts'],
                      'failure_counts': {k: len(v) for k, v in result['checks'].items()},
                      'report': str(output)}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
