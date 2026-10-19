#!/usr/bin/env python3
"""Build editable, electrically connected KiCad sheets from reviewed design graphs.

The graph records physical contact numbers or explicitly labelled functional module
interfaces. It is the auditable source; generated drawings do not establish a PCB
layout or certify any of the hardware acceptance gates.
"""
from __future__ import annotations

import argparse
from collections import Counter, OrderedDict, defaultdict
from copy import deepcopy
from datetime import date
import json
import hashlib
import math
from pathlib import Path
import re
import textwrap
from uuid import NAMESPACE_URL, uuid5

BASE = Path(__file__).resolve().parents[1]
TYPES = set("input output bidirectional tri_state passive free unspecified power_in power_out open_collector open_emitter no_connect".split())
SIMPLE = {"resistor", "capacitor", "inductor", "fuse", "switch", "diode", "battery", "testpoint", "net_tie"}
WIDTH, HEIGHT = 594.0, 420.0
TOP, BOTTOM, LEFT, CELL_W, COLS = 30.48, 387.35, 10.16, 142.24, 4
ROOT_UUID = str(uuid5(NAMESPACE_URL, "sr-rx-v2/root/4653188"))


def uid(key):
    return str(uuid5(NAMESPACE_URL, "sr-rx-v2/completion/" + str(key)))


def q(s):
    return json.dumps(str(s), ensure_ascii=False)


def f(n):
    return f"{float(n):.4f}".rstrip("0").rstrip(".") or "0"


def effects(size=1.016, extra=""):
    return f"(effects (font (size {f(size)} {f(size)})) {extra})"


def prop(k, v, x=0, y=0, hidden=False, size=1.016):
    return f"(property {q(k)} {q(v)} (at {f(x)} {f(y)} 0) {effects(size, '(hide yes)' if hidden else '')})"


def line(a, b, width=0.254):
    return f"(polyline (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})) (stroke (width {f(width)}) (type default)) (fill (type none)))"


def rectangle(a, b):
    return f"(rectangle (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) (stroke (width 0.254) (type default)) (fill (type background)))"


def symbol_geometry(c):
    pins = c["pins"]
    if c.get("kind") == "power_flag":
        return 12.7, [(pins[0], 0, 0, 90)], False
    if c.get("kind") == "testpoint" and len(pins) == 1:
        return 15.24, [(pins[0], -2.54, 0, 0)], False
    simple = c.get("kind") in SIMPLE and len(pins) == 2
    if simple:
        coords = [(p, -10.16 if i == 0 else 10.16, 0, 0 if i == 0 else 180) for i, p in enumerate(pins)]
        return 20.32, coords, True
    half = math.ceil(len(pins) / 2)
    rows = max(half, len(pins) - half, 1)
    span = (rows - 1) * 2.54
    coords = []
    for i, p in enumerate(pins):
        side, row = (0, i) if i < half else (1, i - half)
        coords.append((p, -27.94 if side == 0 else 27.94, span / 2 - row * 2.54, 0 if side == 0 else 180))
    return span + 22.86, coords, False


def lib_symbol(c, embedded=True):
    name = "C_" + re.sub(r"[^A-Za-z0-9_]", "_", c["ref"])
    height, coords, simple = symbol_geometry(c)
    parts = []
    flag = c.get("kind") == "power_flag"
    if flag:
        parts = [line((0, 0), (0, 2.54)), line((0, 2.54), (-1.27, 1.27)), line((0, 2.54), (1.27, 1.27))]
    elif c.get("kind") == "testpoint" and len(c["pins"]) == 1:
        parts = ['(circle (center 0 0) (radius 1.27) (stroke (width 0.254) (type default)) (fill (type none)))']
    elif simple:
        kind = c.get("kind")
        if kind == "capacitor":
            parts = [line((-1.27, 3.81), (-1.27, -3.81)), line((1.27, 3.81), (1.27, -3.81)), line((-7.62, 0), (-1.27, 0)), line((1.27, 0), (7.62, 0))]
        elif kind == "resistor":
            parts = [rectangle((-5.08, 1.27), (5.08, -1.27)), line((-7.62, 0), (-5.08, 0)), line((5.08, 0), (7.62, 0))]
        elif kind == "switch":
            parts = [line((-7.62, 0), (-3.81, 0)), line((-3.81, 0), (3.81, 3.81)), line((3.81, 0), (7.62, 0))]
        elif kind == "battery":
            parts = [line((-1.27, 3.81), (-1.27, -3.81)), line((1.27, 1.905), (1.27, -1.905)), line((-7.62, 0), (-1.27, 0)), line((1.27, 0), (7.62, 0))]
        else:
            parts = [rectangle((-5.08, 2.54), (5.08, -2.54)), line((-7.62, 0), (-5.08, 0)), line((5.08, 0), (7.62, 0))]
    else:
        span = height - 22.86
        parts = [rectangle((-25.4, span / 2 + 2.54), (25.4, -span / 2 - 2.54))]
    pins = []
    for p, x, y, angle in coords:
        typ = p.get("type", "passive")
        name_text = p.get("name", p["number"])
        pins.append(f"(pin {typ} line (at {f(x)} {f(y)} {angle}) (length {0 if flag else 2.54}) (name {q(name_text)} {effects(0.889)}) (number {q(p['number'])} {effects(0.889)}))")
    full = "sr_rx_v2_completed:" + name if embedded else name
    body = [f"(symbol {q(full)} {'(power)' if flag else ''} (pin_names (offset 0.508)) (exclude_from_sim no) (in_bom {'no' if flag else 'yes'}) (on_board {'no' if flag else 'yes'})"]
    body.extend([prop("Reference", c["ref"], 0, height / 2), prop("Value", c["value"], 0, height / 2 - 2.54), prop("Footprint", c.get("footprint", ""), hidden=True), prop("Datasheet", c.get("source", ""), hidden=True), prop("Description", c.get("description", "") + " | " + c.get("status", "") + " | " + "; ".join(c.get("notes", [])), hidden=True)])
    body += [f"(symbol {q(name + '_0_1')} {' '.join(parts)})", f"(symbol {q(name + '_1_1')} {' '.join(pins)}))"]
    return "\n".join(body), name


def text(value, x, y, key, size=1.27, extra="(justify left top)"):
    return f"(text {q(value)} (at {f(x)} {f(y)} 0) {effects(size, extra)} (uuid {uid(key)}))"


def wire(a, b, key):
    return f"(wire (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})) (stroke (width 0) (type default)) (uuid {uid(key)}))"


def label(name, x, y, side, key):
    # A left-side label points right towards its wire; the right-side one points left.
    angle = 180 if side == "left" else 0
    just = "(justify right)" if side == "left" else "(justify left)"
    return f"(global_label {q(name)} (shape bidirectional) (at {f(x)} {f(y)} {angle}) {effects(0.889, just)} (uuid {uid(key)}) {prop('Intersheetrefs', '${INTERSHEET_REFS}', x, y, True)})"


def place_component(c, x, y, path, key):
    h, coords, simple = symbol_geometry(c)
    center_y = y + h / 2 + 1.27
    _, name = lib_symbol(c)
    flag = c.get("kind") == "power_flag"
    body = [f"(symbol (lib_id {q('sr_rx_v2_completed:' + name)}) (at {f(x)} {f(center_y)} 0) (unit 1) (exclude_from_sim no) (in_bom {'no' if flag else 'yes'}) (on_board {'no' if flag else 'yes'}) (dnp {'yes' if c.get('dnp') else 'no'}) (uuid {uid(key)})"]
    # Keep the value readable, including its full exact value as a multiline field.
    shown = "\n".join(textwrap.wrap(c["value"], width=52, break_long_words=False))
    body += [prop("Reference", c["ref"], x, y + 1.27, size=1.27), prop("Value", shown, x, y + 4.445, size=1.016), prop("Footprint", c.get("footprint", ""), x, y, True), prop("Datasheet", c.get("source", ""), x, y, True), prop("Description", c.get("description", ""), x, y, True), prop("ReviewStatus", c.get("status", "TBD"), x, y, True)]
    body += [f"(pin {q(p['number'])} (uuid {uid(key + '/pin/' + str(p['number']))}))" for p in c["pins"]]
    body += [f"(instances (project \"sr-rx-v2\" (path {q(path)} (reference {q(c['ref'])}) (unit 1)))))"]
    for p, px, py, angle in coords:
        anchor = (x + px, center_y - py)
        pk = key + "/pin/" + str(p["number"])
        if p.get("nc") or p.get("type") == "no_connect":
            body.append(f"(no_connect (at {f(anchor[0])} {f(anchor[1])}) (uuid {uid(pk + '/nc')}))")
        elif p.get("net"):
            end = (anchor[0] - 2.54 if px < 0 else anchor[0] + 2.54, anchor[1])
            body += [wire(anchor, end, pk + "/wire"), label(p["net"], *end, "left" if px < 0 else "right", pk + "/label")]
        else:
            # Intentionally exposed unknown terminal: do not hide it with an NC marker.
            body.append(text("TBD", anchor[0] - 2.54 if px < 0 else anchor[0] + 2.54, anchor[1] - 1.27, pk + "/unresolved", 0.889))
    return "\n".join(body)


def paginate(graph):
    groups = OrderedDict()
    for c in graph["components"]:
        groups.setdefault(c.get("group", "Інше"), []).append(c)
    pages, page, col, y = [], [], 0, TOP
    for group, comps in groups.items():
        new_group = True
        for c in comps:
            h, _, _ = symbol_geometry(c)
            need = h + (8.89 if new_group else 1.27)
            limit = 355.6 if col == COLS - 1 else BOTTOM
            if y + need > limit:
                col += 1
                y = TOP
                new_group = True
                if col >= COLS:
                    pages.append(page)
                    page, col = [], 0
            if new_group:
                page.append(("group", group, LEFT + col * CELL_W, y))
                y += 8.89
                new_group = False
            page.append(("component", c, LEFT + col * CELL_W + CELL_W / 2, y))
            y += h + 1.27
        y += 5.08
    if page:
        pages.append(page)
    return pages


def header(document_uuid, title, page_size="A2"):
    block_title = re.sub(r"^E4 - .* (\(\d+/\d+\))$", r"E4 - РЧ-тракт і DC-захист \1", title)
    return f'''(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0")
 (uuid {document_uuid}) (paper {q(page_size)})
 (title_block (title {q(block_title)}) (date "2026-10-19") (rev "v2.1-review")
 (company "SR-RX-v2") (comment 1 "Теоретична схема - перевірити на стенді")
 (comment 2 "Не є комплектом для виробництва PCB; див. OPEN_ITEMS.md"))
'''


def validate(graphs):
    refs, errors, nodes = {}, [], defaultdict(list)
    for g in graphs:
        for c in g["components"]:
            ref = c["ref"]
            if ref in refs:
                errors.append(f"duplicate reference {ref}: {refs[ref]} and {g['sheet']}")
            refs[ref] = g["sheet"]
            numbers = [str(p["number"]) for p in c["pins"]]
            if len(numbers) != len(set(numbers)):
                errors.append(f"duplicate physical contact in {ref}")
            for p in c["pins"]:
                if p.get("type", "passive") not in TYPES:
                    errors.append(f"invalid electrical type {ref}.{p['number']}")
                if p.get("nc") and p.get("net"):
                    errors.append(f"NC connected to a net: {ref}.{p['number']}")
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
    graphs = [json.loads(p.read_text()) for p in sorted(args.design_dir.glob("E[1-5].json"))]
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
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    all_symbols = [lib_symbol(c, embedded=False)[0] for g in graphs for c in g["components"]]
    (out / "sr_rx_v2_completed.kicad_sym").write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n' + "\n".join(all_symbols) + "\n)\n")
    pages = []
    for graph in graphs:
        layouts = paginate(graph)
        for n, layout in enumerate(layouts, 1):
            sheet = graph["sheet"]
            stem = sheet if n == 1 else sheet + "_" + str(n).zfill(2)
            instance = uid("instance/" + stem)
            doc_uuid = uid("document/" + stem)
            path = "/" + ROOT_UUID + "/" + instance
            comps = [item[1] for item in layout if item[0] == "component"]
            title = f"{sheet} - {graph['title']} ({n}/{len(layouts)})"
            content = [header(doc_uuid, title), "(lib_symbols", "\n".join(lib_symbol(c)[0] for c in comps), ")"]
            content += [text(title, 15.24, 15.24, stem + "/title", 2.032), text("Мережі з однаковими глобальними мітками електрично з'єднані на всіх аркушах. Фізичні/функціональні контакти: див. design/ і OPEN_ITEMS.md.", 15.24, 22.86, stem + "/legend", 1.016)]
            for i, (kind, item, x, y) in enumerate(layout):
                if kind == "group":
                    content.append(text(item, x, y, stem + "/group/" + str(i), 1.524))
                else:
                    content.append(place_component(item, x, y, path, stem + "/" + item["ref"]))
            content.append(")\n")
            (out / (stem + ".kicad_sch")).write_text("\n".join(content))
            pages.append({"stem": stem, "instance": instance, "title": title, "components": len(comps), "sheet": sheet})
    # The overview indexes every actual electrical page, retaining E1..E5 naming.
    root = [header(ROOT_UUID, "SR-RX-v2 - зміст електричної схеми", "A2"), "(lib_symbols)", text("SR-RX-v2: приймач і портативна радіолабораторія", 15.24, 15.24, "root/title", 3.048), text("Лише прийом в ефірі. Інженерна редакція від 4653188. Статус і незакриті ворота: ../../COMPLETION.md та ../../OPEN_ITEMS.md.", 15.24, 25.4, "root/status", 1.524)]
    for i, p in enumerate(pages):
        col, row = i % 4, i // 4
        x, y = 15.24 + col * 142.24, 43.18 + row * 38.1
        title = p["title"].split(" - ", 1)[-1]
        title = "\n".join(textwrap.wrap(title, width=45))
        root.append(f'''(sheet (at {f(x)} {f(y)}) (size 129.54 27.94)
 (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {p['instance']})
 {prop('Sheetname', p['stem'], x + 64.77, y + 4.445)}
 {prop('Sheetfile', p['stem'] + '.kicad_sch', x + 64.77, y + 20.32)}
 (instances (project "sr-rx-v2" (path {q('/' + ROOT_UUID)} (page {q(str(i + 2))})))))''')
        root.append(text(title, x + 5.08, y + 8.89, "root/index/" + p["stem"], 1.016))
    root.append('(sheet_instances (path "/" (page "1")))\n)\n')
    if math.ceil(len(pages) / 4) * 38.1 + 38.1 > 380:
        raise ValueError("Overview page overflow: split required")
    (out / "sr-rx-v2.kicad_sch").write_text("\n".join(root))
    table = '(sym_lib_table (version 7)\n'
    for name in ["sr_rx_v2_pwr", "sr_rx_v2_sig", "sr_rx_v2_completed"]:
        table += f' (lib (name "{name}")(type "KiCad")(uri "${{KIPRJMOD}}/{name}.kicad_sym")(options "")(descr "SR-RX-v2"))\n'
    (out / "sym-lib-table").write_text(table + ")\n")
    project_file = out / "sr-rx-v2.kicad_pro"
    project = json.loads(project_file.read_text()) if project_file.exists() else {}
    project.setdefault("meta", {}).update({"filename": "sr-rx-v2.kicad_pro", "version": 3})
    project["sheets"] = [[ROOT_UUID, "Root"]] + [[uid("document/" + p["stem"]), p["stem"]] for p in pages]
    project_file.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n")
    physical_nets = {k: [v for v in vs if not v["ref"].startswith("#")] for k, vs in nets.items()}
    manifest = {"base_commit": "465318835e71eae326059f5f66e2b47232169556", "root_uuid": ROOT_UUID, "pages": pages, "components": sum(not r.startswith('#') for r in refs), "supply_annotations": len(flag_nets), "connected_contacts": sum(map(len, physical_nets.values())), "nets": len(nets), "single_contact_nets": {k: v for k, v in physical_nets.items() if len(v) == 1}, "open_items": [dict(item, sheet=g["sheet"]) for g in graphs for item in g.get("open_items", [])]}
    manifest["source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.design_dir.glob("E[1-5].json"))}
    (out / "generation-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (out / "expected-netlist.json").write_text(json.dumps(physical_nets, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k not in {"single_contact_nets", "open_items", "pages"}}, ensure_ascii=False))
    print(f"Electrical pages: {len(pages)}; explicit open items: {len(manifest['open_items'])}")


if __name__ == "__main__":
    main()
