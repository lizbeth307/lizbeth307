#!/usr/bin/env python3
"""Refresh only the schematic-derived fields of inventory.json from design/E1-E5.json.

Rewritten: copied component pins/value/kind/status/description/notes/source,
assembly groups, nets, passive parameters and sheet open items, the net/NC
lists, graph counts and the source_snapshots bytes/SHA256. The assembly
partition, interface selection, model boundaries, gates and coverage fields
are hand-maintained and never written; a changed ref set, or a ref that would
change sheet, group split or passive/interface class, is refused for review.
--check writes nothing and exits 1 when inventory.json is stale.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
INVENTORY = HERE / "inventory.json"
SHEETS = ("E1", "E2", "E3", "E4", "E5")
# Circuit passives are parameters of their assembly; the other kinds are interfaces.
PARAMETER_KINDS = frozenset({"resistor", "capacitor", "inductor", "diode", "nfet", "pfet", "fuse", "testpoint", "net_tie"})
INTERFACE_KINDS = frozenset({"module", "ic", "connector", "switch", "battery", "relay"})
# Graph-derived keys; every other key of these records must come out byte-identical.
ASSEMBLY_KEYS = {"source_group", "component_count", "named_nets", "passive_parameters", "sources", "sheet_hardware_gates"}
INTERFACE_KEYS = {"value", "source_kind", "source_status", "source_pins", "sources", "source_description", "source_notes"}
TOP_KEYS = {"source_snapshots", "scope", "assemblies", "subinterfaces", "reference_to_assembly",
            "canonical_net_connections", "explicit_unconnected_pins", "validation"}
SCOPE_KEYS = {"graph_components", "graph_pins", "graph_sheets", "source_kind_module_count",
              "graph_connected_pins", "graph_nc_pins", "canonical_nets", "cross_assembly_nets"}


class RefreshError(ValueError):
    pass


def check(condition, message):
    if not condition:
        raise RefreshError(message)


def strict_json(text):
    def pairs(items):
        out = {}
        for key, value in items:
            check(key not in out, "duplicate JSON key " + key)
            out[key] = value
        return out
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(RefreshError("nonfinite JSON")))


def encode(inventory):
    return json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"


def regular(project, relative):
    path = project / relative
    check(not Path(relative).is_absolute() and ".." not in Path(relative).parts, "unsafe snapshot path " + relative)
    check(not path.is_symlink() and path.is_file() and path.resolve().is_relative_to(project.resolve()),
          "snapshot is not a regular project file: " + relative)
    return path


def snapshot(path):
    with open(path, "rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    return {"sha256": digest, "bytes": path.stat().st_size}


def read_graphs(project):
    sheets, comps = {}, {}
    for sheet in SHEETS:
        doc = strict_json(regular(project, "design/" + sheet + ".json").read_text(encoding="utf-8"))
        sheets[sheet] = doc
        for comp in doc["components"]:
            check(comp["ref"] not in comps, "duplicate graph ref " + comp["ref"])
            check(comp["kind"] in PARAMETER_KINDS | INTERFACE_KINDS, "unclassified graph kind " + comp["kind"] + " for " + comp["ref"])
            for pin in comp["pins"]:
                check(type(pin["number"]) is str and bool(pin.get("net")) != bool(pin.get("nc")),
                      "pin must declare a string number and net xor NC: " + comp["ref"])
            comps[comp["ref"]] = (sheet, comp)
    return sheets, comps


def refresh(project, inventory):
    """Return (refreshed copy, changed field paths); refuse structural changes."""
    project = Path(project).resolve(strict=True)
    sheets, comps = read_graphs(project)
    new = copy.deepcopy(inventory)
    assigned = [ref for group in inventory["assemblies"] for ref in group["refs"]]
    added, removed = sorted(set(comps) - set(assigned)), sorted(set(assigned) - set(comps))
    check(not added and not removed and len(assigned) == len(set(assigned)),
          "schematic ref set changed (added " + ",".join(added[:12]) + "; removed " + ",".join(removed[:12])
          + "); the assembly partition and models are hand-maintained: update them first")
    owner = {ref: group["module_id"] for group in inventory["assemblies"] for ref in group["refs"]}
    interfaces = {entry["ref"] for entry in inventory["subinterfaces"]}
    check(len(interfaces) == len(inventory["subinterfaces"]), "duplicate interface ref")
    moved = sorted(ref for ref, (_, comp) in comps.items() if (comp["kind"] in INTERFACE_KINDS) != (ref in interfaces))
    check(not moved, "parameter/interface class changed for " + ",".join(moved[:12]) + "; review subinterfaces by hand")
    for relative in new["source_snapshots"]:
        new["source_snapshots"][relative] = snapshot(regular(project, relative))
    for group in new["assemblies"]:
        refs = group["refs"]
        check({comps[ref][0] for ref in refs} == {group["sheet"]}, "assembly " + group["module_id"] + " no longer lies on sheet " + group["sheet"])
        names = {comps[ref][1]["group"] for ref in refs}
        check(len(names) == 1, "assembly " + group["module_id"] + " now spans graph groups " + ", ".join(sorted(names)))
        group["source_group"] = names.pop()
        group["component_count"] = len(refs)
        group["named_nets"] = sorted({pin["net"] for ref in refs for pin in comps[ref][1]["pins"] if pin.get("net")})
        group["passive_parameters"] = [{"ref": ref, "kind": comps[ref][1]["kind"], "value": comps[ref][1]["value"],
                                        "status": comps[ref][1]["status"]} for ref in refs if ref not in interfaces]
        design = group["sources"][0]
        check(set(design) == {"path", "group"} and design["path"] == "design/" + group["sheet"] + ".json", "unexpected assembly graph source")
        design["group"] = group["source_group"]
        group["sheet_hardware_gates"] = [{"id": item["id"], "description": item["description"], "blocking": item["blocking"]}
                                         for item in sheets[group["sheet"]]["open_items"]]
    for entry in new["subinterfaces"]:
        sheet, comp = comps[entry["ref"]]
        check(entry["module_id"] == sheet + "/" + entry["ref"] and entry["parent_assembly"] == owner[entry["ref"]],
              "interface " + entry["ref"] + " moved sheet or assembly")
        nets = {pin["net"] for pin in comp["pins"] if pin.get("net")}
        stale = [net for net in entry["interface_signals"] if net not in nets]
        check(not stale, "hand-selected interface_signals of " + entry["ref"] + " name nets it no longer has: " + ", ".join(stale))
        entry.update(value=comp["value"], source_kind=comp["kind"], source_status=comp["status"], source_pins=comp["pins"],
                     source_description=comp.get("description", ""), source_notes=comp.get("notes", []))
        design = entry["sources"][0]
        check(set(design) == {"path", "ref", "component_source"} and design["path"] == "design/" + sheet + ".json"
              and design["ref"] == entry["ref"], "unexpected interface graph source")
        design["component_source"] = comp["source"]
    new["reference_to_assembly"] = owner  # partition order, as recorded
    nets, unconnected = {}, []
    for ref, (sheet, comp) in comps.items():
        for pin in comp["pins"]:
            row = {"sheet": sheet, "ref": ref, "pin": pin["number"], "name": pin["name"], "electrical_type": pin["type"], "assembly": owner[ref]}
            if pin.get("net"):
                nets.setdefault(pin["net"], []).append(row)
            else:
                unconnected.append(row)
    new["canonical_net_connections"] = []
    for name in sorted(nets):
        owners = sorted({row["assembly"] for row in nets[name]})
        new["canonical_net_connections"].append({"net": name, "pins": nets[name], "assemblies": owners, "cross_assembly": len(owners) > 1})
    new["explicit_unconnected_pins"] = unconnected
    connected = sum(len(rows) for rows in nets.values())
    new["scope"].update(graph_components=len(comps), graph_pins=connected + len(unconnected),
                        graph_sheets={sheet: len(doc["components"]) for sheet, doc in sheets.items()},
                        source_kind_module_count=sum(comp["kind"] == "module" for _, comp in comps.values()),
                        graph_connected_pins=connected, graph_nc_pins=len(unconnected), canonical_nets=len(nets),
                        cross_assembly_nets=sum(row["cross_assembly"] for row in new["canonical_net_connections"]))
    counts = {"refs_assigned_once": len(comps), "connected_pin_net_triples_exact": connected,
              "NCpins_exact": len(unconnected), "subinterface_pin_arrays_exact": len(interfaces)}
    validation = {}
    for key, value in new["validation"].items():
        match = re.fullmatch(r"all[0-9]+(.+)", key)
        if match and match.group(1) in counts:
            key = "all" + str(counts[match.group(1)]) + match.group(1)
        validation[key] = value
    check(len(validation) == len(new["validation"]), "validation keys collide")
    validation["source_snapshot_hashes_unchanged"] = True
    new["validation"] = validation
    return new, guard(inventory, new)


def guard(old, new):
    """Changed field paths; anything outside the graph-derived set is a bug, never written."""
    changed = []
    check(list(old) == list(new), "top-level keys changed")
    for key in old:
        if old[key] != new[key]:
            check(key in TOP_KEYS, "refused to touch hand-maintained field " + key)
            if key not in ("assemblies", "subinterfaces", "scope"):
                changed.append(key)
    check(all(old["scope"][k] == new["scope"][k] for k in old["scope"] if k not in SCOPE_KEYS) and list(old["scope"]) == list(new["scope"]),
          "refused to touch hand-maintained scope fields")
    changed += ["scope." + k for k in old["scope"] if old["scope"][k] != new["scope"][k]]
    for name, allowed in (("assemblies", ASSEMBLY_KEYS), ("subinterfaces", INTERFACE_KEYS)):
        check(len(old[name]) == len(new[name]), name + " count changed")
        for before, after in zip(old[name], new[name]):
            check(list(before) == list(after), name + " record keys changed")
            for key in before:
                if before[key] != after[key]:
                    check(key in allowed, "refused to touch hand-maintained " + name + "." + key)
                    changed.append(name + "[" + str(before.get("module_id")) + "]." + key)
            if name == "assemblies":
                check(before["sources"][1:] == after["sources"][1:], "refused to touch hand-maintained assembly sources")
            else:
                check(before["sources"][1:] == after["sources"][1:], "refused to touch hand-maintained interface sources")
    return changed


def write(path, text):
    fd, name = tempfile.mkstemp(prefix=".inventory-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--inventory", type=Path, default=INVENTORY)
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if inventory.json is stale")
    args = parser.parse_args(argv)
    try:
        current = args.inventory.read_bytes().decode("utf-8")  # exact bytes: CRLF or reformatting is stale too
        new, changed = refresh(args.project, strict_json(current))
    except (OSError, KeyError, TypeError, ValueError) as error:
        print("REFUSED: " + type(error).__name__ + ": " + str(error), file=sys.stderr)
        return 2
    text = encode(new)
    stale = text != current
    if stale and not args.check:
        write(args.inventory, text)
    print(json.dumps({"status": ("STALE" if args.check else "REFRESHED") if stale else "CURRENT",
                      "changed_fields": len(changed), "fields": changed[:40]}, ensure_ascii=False, indent=2))
    return 1 if stale and args.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
