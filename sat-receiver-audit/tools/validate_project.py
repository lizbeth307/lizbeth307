#!/usr/bin/env python3
"""Compare the KiCad-exported electrical netlist against reviewed design graphs.

This is independent of drawing layout. It catches missing components, changed
physical contacts, accidentally merged nets, dangling wires, and NC-pin shorts.
Raw ERC findings are retained; hardware acceptance is never inferred from ERC.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, default=BASE)
    args = ap.parse_args()
    base = args.project
    graphs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((base / "design").glob("E[1-5].json"))]
    expected, refs, nc, unassigned, dnp = {}, {}, set(), set(), set()
    nodes_to_net = {}
    errors = []
    for g in graphs:
        for c in g["components"]:
            if c["ref"] in refs:
                errors.append("Duplicate reference " + c["ref"])
            refs[c["ref"]] = c
            if c.get("dnp"):
                dnp.add(c["ref"])
            for p in c["pins"]:
                node = (c["ref"], str(p["number"]))
                if (p.get("nc") or p.get("type") == "no_connect") and p.get("net"):
                    errors.append(f"NC/no_connect contact has net {p['net']}: {node}")
                if p.get("nc") or p.get("type") == "no_connect":
                    nc.add(node)
                elif not p.get("net"):
                    unassigned.add(node)
                else:
                    net = p["net"]
                    expected.setdefault(net, set()).add(node)
                    if node in nodes_to_net:
                        errors.append(f"Contact assigned more than once: {node}")
                    nodes_to_net[node] = net
    # Hash exactly the bytes compared, so validation.json names its ERC/netlist inputs.
    inputs = {name: (base / name).read_bytes() for name in ("verification/erc.json", "verification/netlist.xml")}
    root = ET.fromstring(inputs["verification/netlist.xml"])
    actual_refs = {c.get("ref") for c in root.findall("./components/comp") if not c.get("ref", "").startswith("#")}
    if actual_refs != set(refs):
        errors.append(f"Component mismatch: missing={sorted(set(refs)-actual_refs)}, extra={sorted(actual_refs-set(refs))}")
    actual = {}
    nc_exported = set()
    for net in root.findall("./nets/net"):
        nodes = {(n.get("ref"), n.get("pin")) for n in net.findall("node") if not n.get("ref", "").startswith("#")}
        if not nodes:
            continue
        name = net.get("name")
        if name in expected:
            actual[name] = nodes
        elif len(nodes) == 1 and nodes <= nc | unassigned:
            nc_exported |= nodes
        else:
            errors.append(f"Unexpected exported net {name}: {sorted(nodes)}")
    for name, nodes in expected.items():
        if actual.get(name) != nodes:
            errors.append(f"Net mismatch {name}: missing={sorted(nodes-actual.get(name,set()))}, extra={sorted(actual.get(name,set())-nodes)}")
    for name, nodes in actual.items():
        if nodes & nc:
            errors.append(f"NC pin attached to named net {name}: {sorted(nodes & nc)}")
    if unassigned:
        errors.append(f"Unassigned contacts without explicit NC: {sorted(unassigned)}")
    erc = json.loads(inputs["verification/erc.json"].decode("utf-8"))
    violations = [dict(v, sheet=s["path"]) for s in erc["sheets"] for v in s["violations"]]
    erc_counts = Counter((v["severity"], v["type"]) for v in violations)
    report = {
        "graph_netlist_comparison": "PASS" if not errors else "FAIL",
        "electrical_sheets": len(root.findall("./design/sheet")),
        "physical_components": len(refs),
        "connected_physical_contacts": sum(map(len, expected.values())),
        "named_nets": len(expected),
        "explicit_nc_contacts": len(nc),
        "dnp_components": sorted(dnp),
        "erc_counts": {severity+":"+kind: n for (severity, kind), n in sorted(erc_counts.items())},
        "erc_ignored_checks": sorted(c["key"] for c in erc.get("ignored_checks", [])),
        "erc_errors": [v for v in violations if v["severity"] == "error"],
        "comparison_errors": errors,
        "hardware_acceptance": "NOT_PERFORMED",
        "production_release": False,
        "reason": "Structural checks and ERC do not close manufacturer-revision, charging, RF, thermal, PCB-layout, or physical acceptance gates.",
        "sha256": {p.relative_to(base).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((base / "build/kicad").glob("*.kicad_sch"))},
        "input_files": [{"file": name, "sha256": hashlib.sha256(data).hexdigest()} for name, data in inputs.items()],
    }
    (base / "verification/validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"sha256", "erc_errors", "dnp_components", "input_files"}}, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
