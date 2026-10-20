#!/usr/bin/env python3
"""Mutate every declared connection, using KiCad XML as a separate oracle.

Level: connection_net_model only. A terminal is attached to an ideal named net;
component internals, voltage/current, contact resistance and physical connector
numbering are not inferred. DNP declarations and unresolved pinouts stay so.
This module imports no schematic generator or production functional model.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

LEVEL = "connection_net_model"
PASS = "CONNECTION_MODEL_PASS"
FAIL = "CONNECTION_MODEL_FAIL"


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def endpoint(key):
    return {"ref": key[0], "pin": key[1]}


class ConnectionNetModel:
    """Mutable wire attachments and explicit shorts; no implicit pin bridges."""
    def __init__(self, connections, all_pins):
        self.attachments = dict(connections)
        self.all_pins = frozenset(all_pins)
        self.nets = frozenset(connections.values())
        self.shorts = set()

    def attach(self, key, net):
        check(key in self.all_pins and net in self.nets, "unknown endpoint/net cannot be invented")
        self.attachments[key] = net

    def disconnect(self, key):
        check(key in self.all_pins, "unknown endpoint")
        return self.attachments.pop(key, None)

    def short(self, first, second):
        check(first in self.nets and second in self.nets and first != second, "short needs two distinct declared nets")
        pair = tuple(sorted((first, second)))
        self.shorts.add(pair)
        return pair

    def net_component(self, net):
        visited, pending = set(), [net]
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            for first, second in self.shorts:
                if first == current and second not in visited:
                    pending.append(second)
                elif second == current and first not in visited:
                    pending.append(first)
        return visited

    def connected_endpoints(self, key):
        """Actual dynamic peers, derived from current edges rather than oracle."""
        if key not in self.attachments:
            return []
        component = self.net_component(self.attachments[key])
        return sorted(other for other, net in self.attachments.items() if other != key and net in component)

    def validate(self, oracle, intentional_nc, selected=None):
        selected = set(oracle) | set(intentional_nc) if selected is None else set(selected)
        faults = []
        for key in sorted(selected):
            actual = self.attachments.get(key)
            if key in intentional_nc:
                if actual is not None:
                    faults.append({"kind": "NC_UNEXPECTED_CONNECTION", **endpoint(key), "actual_net": actual})
                continue
            if key not in oracle:
                faults.append({"kind": "UNDECLARED_ENDPOINT", **endpoint(key)})
                continue
            expected = oracle[key]
            if actual is None:
                faults.append({"kind": "OPEN_CONNECTION", **endpoint(key), "expected_net": expected})
                continue
            observed_nets = self.net_component(actual)
            if expected not in observed_nets:
                faults.append({"kind": "WRONG_NET", **endpoint(key), "expected_net": expected, "actual_net": actual})
            if len(observed_nets) > 1:
                faults.append({"kind": "CROSS_NET_SHORT", **endpoint(key), "expected_net": expected,
                               "merged_nets": sorted(observed_nets)})
        return faults


def read_graphs(project):
    components, pins, connected, nc, snapshots = {}, {}, {}, set(), {}
    for path in sorted((project / "design").glob("E[1-5].json")):
        snapshots[str(path.relative_to(project))] = sha(path)
        doc = json.loads(path.read_text())
        for comp in doc["components"]:
            ref = comp["ref"]
            check(ref not in components, "duplicate graph reference " + ref)
            components[ref] = {**comp, "sheet": path.stem}
            for pin in comp["pins"]:
                key = ref, str(pin["number"])
                check(key not in pins, "duplicate graph pin " + str(key))
                check(bool(pin.get("net")) != bool(pin.get("nc")), "pin must declare net xor NC: " + str(key))
                pins[key] = pin
                if pin.get("net"):
                    connected[key] = pin["net"]
                else:
                    nc.add(key)
    check(len(snapshots) == 5, "five current source graph sheets are required")
    return components, pins, connected, nc, snapshots


def read_kicad_oracle(path):
    check(path.is_file(), "independent KiCad XML is missing: verification/netlist.xml")
    doc = ET.parse(path).getroot()
    check(doc.tag == "export" and doc.findtext("./design/tool", "").startswith("Eeschema "), "oracle is not a KiCad XML export")
    components, connected, nc, nodes = {}, {}, set(), set()
    for comp in doc.findall("./components/comp"):
        ref = comp.attrib["ref"]
        check(ref not in components, "duplicate XML reference " + ref)
        components[ref] = comp.findtext("value", "")
    for net in doc.findall("./nets/net"):
        name = net.attrib["name"]
        for node in net.findall("node"):
            key = node.attrib["ref"], node.attrib["pin"]
            check(key not in nodes, "XML pin belongs to multiple nets: " + str(key))
            nodes.add(key)
            is_nc = "no_connect" in node.attrib.get("pintype", "").split("+")
            if name.startswith("unconnected-"):
                check(is_nc and len(net.findall("node")) == 1, "unconnected XML net lacks explicit singleton no-connect marker")
                nc.add(key)
            else:
                check(not is_nc, "XML NC pin is attached to a canonical net")
                connected[key] = name
    return components, connected, nc, {"tool": doc.findtext("./design/tool"), "sha256": sha(path),
        "xml_pin_nodes": len(nodes), "canonical_nets": len(set(connected.values())), "nc_nodes": len(nc),
        "methodology": "Separate stdlib XML parser; no import of graph generator, existing netlist checker, register models or production drivers.",
        "boundary": "KiCad export is an independent serialization/extraction check of the schematic, not independent evidence that its intended wiring is electrically correct."}


def physical_pinout(interface, component):
    declared = interface.get("pinout_status", "NOT_RECORDED") if interface else "not_catalogued_as_separate_interface"
    if declared == "source_numbered_pin_map" or declared.startswith("manufacturer_"):
        numbering = "DECLARED_NUMBERS_NOT_PHYSICALLY_VERIFIED"
    elif declared == "project_harness_assignment_not_factory_pinout":
        numbering = "PROJECT_ASSIGNED_VENDOR_MAPPING_UNQUALIFIED"
    else:
        numbering = "FUNCTIONAL_TERMINALS_PHYSICAL_MAPPING_UNKNOWN"
    gate = interface.get("pinout_gate") if interface else None
    tbd = component.get("status", "").upper() == "TBD" or bool(re.search(r"\bTBD\b", json.dumps(component, ensure_ascii=False), re.I))
    return {"source_pinout_status": declared, "physical_numbering_status": numbering, "pinout_gate": gate,
            "source_TBD_preserved": tbd, "physical_verified": False,
            "dnp": bool(component.get("dnp")), "functional_pin_identifiers_unchanged": True}


def _run(project):
    inventory_path = project / "deployment/module_lab/inventory.json"
    inventory = json.loads(inventory_path.read_text())
    components, pins, graph_connections, graph_nc, snapshots = read_graphs(project)
    xml_components, oracle, nc, oracle_meta = read_kicad_oracle(project / "verification/netlist.xml")
    check(set(components) == set(xml_components), "XML and graph component references differ")
    check(all(comp["value"].strip() == xml_components[ref].strip() for ref, comp in components.items()), "XML component value differs from graph")
    check(graph_connections == oracle and graph_nc == nc, "XML and graph pin/net/NC declarations differ")
    check(set(pins) == set(oracle) | nc, "XML does not cover every graph contact")
    for name, value in snapshots.items():
        check(inventory["source_snapshots"][name]["sha256"] == value, "inventory graph snapshot is stale: " + name)
    assigned = [ref for assembly in inventory["assemblies"] for ref in assembly["refs"]]
    check(len(assigned) == len(set(assigned)) and set(assigned) == set(components), "assemblies do not partition every reference exactly once")
    check(len(inventory["subinterfaces"]) == len({entry["ref"] for entry in inventory["subinterfaces"]}), "duplicate interface reference")
    interface_by_ref = {entry["ref"]: entry for entry in inventory["subinterfaces"]}
    for ref, interface in interface_by_ref.items():
        check(ref in components, "inventory interface not in graph")
        expected = {str(p["number"]): (p.get("net"), bool(p.get("nc"))) for p in components[ref]["pins"]}
        observed = {str(p["number"]): (p.get("net"), bool(p.get("nc"))) for p in interface["source_pins"]}
        check(expected == observed, "inventory interface pins differ: " + ref)
    model = ConnectionNetModel(graph_connections, pins)
    cases, case_refs = [], defaultdict(list)
    counts = defaultdict(int)
    def record(ident, category, refs, evidence):
        cases.append({"id": ident, "category": category, "status": PASS, "refs": sorted(set(refs)), **evidence})
        counts[category] += 1
        for ref in set(refs):
            case_refs[ref].append(ident)

    # Literal miniature topology checks validator behavior independently of the
    # project input. These intentionally bad states must be judged faulty.
    literal = {("X", "1"): "NET_A", ("Y", "1"): "NET_A", ("Y", "2"): "NET_B"}
    literal_nc = {("Z", "NC")}
    probe = ConnectionNetModel(literal, set(literal) | literal_nc)
    check(not probe.validate(literal, literal_nc), "validator rejects healthy literal fixture")
    probe.disconnect(("X", "1"))
    check(probe.validate(literal, literal_nc)[0]["kind"] == "OPEN_CONNECTION", "validator misses literal open")
    probe.attach(("X", "1"), "NET_B")
    check(probe.validate(literal, literal_nc)[0]["kind"] == "WRONG_NET", "validator misses literal wrong wire")
    probe.attach(("X", "1"), "NET_A")
    check(not probe.connected_endpoints(("Z", "NC")), "intentional NC must have no dynamic peers")
    probe.attach(("Z", "NC"), "NET_A")
    check(any(x["kind"] == "NC_UNEXPECTED_CONNECTION" for x in probe.validate(literal, literal_nc)), "validator confuses NC with open")
    probe.disconnect(("Z", "NC")); probe.short("NET_A", "NET_B")
    check(any(x["kind"] == "CROSS_NET_SHORT" for x in probe.validate(literal, literal_nc)), "validator misses transitive short")
    record("validator-literal-negative-controls", "validator_negative_controls", [],
           {"injected_fault_verdicts": ["OPEN_CONNECTION", "WRONG_NET", "NC_UNEXPECTED_CONNECTION", "CROSS_NET_SHORT"]})
    check(not model.validate(oracle, nc), "baseline dynamic graph differs from XML")
    record("independent-xml-baseline", "independent_baseline", components, {"xml_match": True})

    by_ref, by_net = defaultdict(list), defaultdict(list)
    for key, net in oracle.items():
        by_ref[key[0]].append(key)
        by_net[net].append(key)
    for key in nc:
        by_ref[key[0]].append(key)

    # Every connected endpoint is individually detached from an otherwise healthy
    # graph, independently detected against XML, then reattached to recover.
    for key, expected_net in sorted(oracle.items()):
        old = model.disconnect(key)
        faults = model.validate(oracle, nc, [key])
        check(len(faults) == 1 and faults[0]["kind"] == "OPEN_CONNECTION", "individual disconnect escaped detection: " + str(key))
        check(not model.connected_endpoints(key), "a disconnected pin retained peers")
        model.attach(key, old)
        check(not model.validate(oracle, nc, [key]), "reattachment did not recover baseline")
        peers = model.connected_endpoints(key)
        check(len(peers) == len(by_net[expected_net])-1, "dynamic connected endpoint membership differs")
        record("open:" + key[0] + ":" + key[1], "individual_connected_pin_open", [key[0]],
               {"endpoint": endpoint(key), "expected_net": expected_net, "fault_verdict": faults[0]["kind"],
                "restored_peer_count": len(peers), "restored": True})

    all_nets = sorted(by_net)
    for key in sorted(nc):
        check(key not in model.attachments and not model.validate(oracle, nc, [key]), "intentional NC incorrectly classified as an open")
        record("nc:" + key[0] + ":" + key[1], "intentional_nc_distinguished", [key[0]],
               {"endpoint": endpoint(key), "actual_attachment": None, "verdict": "INTENTIONAL_NC_NOT_OPEN"})
        model.attach(key, all_nets[0])
        faults = model.validate(oracle, nc, [key])
        check(len(faults) == 1 and faults[0]["kind"] == "NC_UNEXPECTED_CONNECTION", "NC accidental attachment not detected")
        model.disconnect(key)
        record("nc-short:" + key[0] + ":" + key[1], "nc_accidental_connection", [key[0]],
               {"endpoint": endpoint(key), "injected_net": all_nets[0], "fault_verdict": faults[0]["kind"], "restored": True})

    # A rotating pair exercises every distinct canonical net. These are explicit
    # ideal-wire faults, not an assertion that the hardware can sense every short.
    for index, first in enumerate(all_nets):
        second = all_nets[(index+1) % len(all_nets)]
        pair = model.short(first, second)
        selected = by_net[first] + by_net[second]
        faults = model.validate(oracle, nc, selected)
        check(len(faults) == len(selected) and all(x["kind"] == "CROSS_NET_SHORT" for x in faults), "cross-net fault escaped detection")
        check(set(model.connected_endpoints(selected[0])) == set(selected)-{selected[0]}, "short did not dynamically join endpoint sets")
        model.shorts.remove(pair)
        check(not model.validate(oracle, nc, selected), "short removal did not recover baseline")
        record("net-short:" + first + ":" + second, "cross_net_short", [key[0] for key in selected],
               {"injected_nets": [first, second], "fault_verdict": "CROSS_NET_SHORT", "affected_endpoint_count": len(selected), "restored": True})

    component_rows = []
    for ref, component in sorted(components.items()):
        connected_keys = sorted(key for key in by_ref[ref] if key in oracle)
        disconnected = {key: model.disconnect(key) for key in connected_keys}
        faults = model.validate(oracle, nc, by_ref[ref])
        check(len(faults) == len(connected_keys) and all(x["kind"] == "OPEN_CONNECTION" for x in faults), "whole-component unplug escaped detection: " + ref)
        for key, net in disconnected.items(): model.attach(key, net)
        check(not model.validate(oracle, nc, by_ref[ref]), "whole-component reconnect failed: " + ref)
        record("unplug-ref:" + ref, "whole_component_unplug", [ref],
               {"connected_pins_removed": len(connected_keys), "opens_detected": len(faults), "restored": True})
        connected_details = [{"pin": key[1], "name": pins[key].get("name"), "net": model.attachments[key],
                              "dynamic_peer_count": len(model.connected_endpoints(key))} for key in connected_keys]
        component_rows.append({"id": component["sheet"] + "/" + ref, "refs": [ref], "status": PASS,
            "coverage_level": LEVEL, "functional_status": "UNCHANGED_NOT_ASSESSED", "hardware_qualified": False,
            "declared_schematic_population": "DNP" if component.get("dnp") else "DESIGN_DECLARATION_ONLY",
            "connected_pins": connected_details, "intentional_nc_pins": sorted(key[1] for key in by_ref[ref] if key in nc),
            "pinout": physical_pinout(interface_by_ref.get(ref), component)})

    assembly_rows = []
    for assembly in inventory["assemblies"]:
        selected = sorted(key for ref in assembly["refs"] for key in by_ref[ref] if key in oracle)
        disconnected = {key: model.disconnect(key) for key in selected}
        faults = model.validate(oracle, nc, selected)
        check(len(faults) == len(selected), "assembly unplug missed endpoints")
        for key, net in disconnected.items(): model.attach(key, net)
        check(not model.validate(oracle, nc, selected), "assembly reconnect failed")
        ident = "unplug-assembly:" + assembly["module_id"]
        record(ident, "whole_assembly_unplug", assembly["refs"], {"opens_detected": len(faults), "restored": True})
        assembly_rows.append({"id": assembly["module_id"], "refs": assembly["refs"], "status": PASS,
            "coverage_level": LEVEL, "functional_status": "UNCHANGED_NOT_ASSESSED", "connected_pin_count": len(selected),
            "case_id": ident, "hardware_qualified": False})

    modules = []
    row_by_ref = {row["refs"][0]: row for row in component_rows}
    for interface in inventory["subinterfaces"]:
        ref = interface["ref"]
        row = row_by_ref[ref]
        ids = case_refs[ref]
        modules.append({"id": interface["module_id"], "refs": [ref], "ref": ref, "status": PASS,
            "coverage_level": LEVEL, "functional_status": "UNCHANGED_NOT_ASSESSED", "hardware_qualified": False,
            "assembly": interface["parent_assembly"], "value": interface["value"], "pinout": row["pinout"],
            "connected_pins": row["connected_pins"], "intentional_nc_pins": row["intentional_nc_pins"],
            "case_count": len(ids), "case_ids": ids,
            "limitations": ["Only named schematic connection/fault topology is exercised; functional model coverage is unchanged.",
                            "Unknown/TBD physical mapping and hardware gates remain unresolved."]})
    for row in component_rows:
        row["case_count"] = len(case_refs[row["refs"][0]])
    check(not model.validate(oracle, nc) and not model.shorts, "mutations were not completely restored")
    scope = inventory["scope"]
    check((len(components), len(pins), len(oracle), len(nc), len(by_net), len(assembly_rows), len(modules)) ==
          (scope["graph_components"], scope["graph_pins"], scope["graph_connected_pins"], scope["graph_nc_pins"],
           scope["canonical_nets"], scope["top_level_circuit_assemblies"], scope["detailed_subinterfaces"]), "inventory count contract differs")
    return {"schema_version": 1, "status": PASS, "coverage_level": LEVEL, "functional_status": "UNCHANGED_NOT_ASSESSED",
        "hardware_qualified": False, "physical_tests_performed": False, "source_graphs_changed": False,
        "summary": {"components": len(components), "declared_pins": len(pins), "connected_pins": len(oracle),
                    "intentional_nc_pins": len(nc), "canonical_nets": len(by_net), "assemblies": len(assembly_rows),
                    "interfaces": len(modules), "cases": len(cases), "failed": 0, "cases_by_category": dict(sorted(counts.items())),
                    "physical_or_TBD_interfaces_preserved": sum(m["pinout"]["source_TBD_preserved"] or
                        m["pinout"]["physical_numbering_status"] != "DECLARED_NUMBERS_NOT_PHYSICALLY_VERIFIED" for m in modules)},
        "independent_netlist": oracle_meta, "modules": modules, "components": component_rows, "assemblies": assembly_rows,
        "dynamic_nets": [{"net": name, "endpoints": [endpoint(key) for key, attached in sorted(model.attachments.items())
            if attached in model.net_component(name)]} for name in sorted(model.nets)],
        "cases": cases, "source_sha256": {**snapshots, "deployment/module_lab/inventory.json": sha(inventory_path),
            "verification/netlist.xml": oracle_meta["sha256"], "deployment/module_lab/connectivity.py": sha(Path(__file__))},
        "limits": ["CONNECTION_MODEL_PASS is not functional EMULATION_PASS or hardware acceptance.",
                   "Fault detection means comparison by this virtual topology observer. It does not mean a real instrument or firmware can electrically detect every open or short.",
                   "Ideal nets do not propagate through resistors, capacitors, diodes, switches, ICs or module internals. Their electrical behavior remains outside this layer.",
                   "An NC declaration means no external schematic wire; internal module coupling/isolation is unknown unless separately modeled.",
                   "DNP components are tested as schematic declarations only. J102 remains DNP/service-only with E1-02 OPEN; its modeled net attachment is no permission to connect a charger.",
                   "Functional names, project harness assignments, numbered pins and verified physical pinouts are distinct. No unknown/TBD connector number is invented.",
                   "KiCad XML and source graphs share the schematic design origin: agreement proves serialization consistency, not independent circuit-design correctness."]}


def run(project):
    try:
        return _run(Path(project).resolve())
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        return {"schema_version": 1, "status": FAIL, "coverage_level": LEVEL,
                "functional_status": "UNCHANGED_NOT_ASSESSED", "hardware_qualified": False,
                "physical_tests_performed": False, "error": type(error).__name__ + ": " + str(error), "modules": [], "cases": []}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = run(args.project)
    encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    else:
        print(encoded, end="")
    return 0 if report["status"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
