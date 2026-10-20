#!/usr/bin/env python3
"""Run independent module models and show exact coverage against the schematics."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DOMAINS = {"power": "power_scenarios.py", "mcu": "mcu_scenarios.py",
           "radio": "radio_modules.py", "location": "location_scenarios.py", "io": "io_scenarios.py",
           "connectivity": "connectivity.py"}
MCU_REFS = {"bno085_spi_shtp": ["U314"], "external_imu_uart": ["U309", "U305"],
            "pico_adc_ntc_battery": ["U305"], "pico_gpio_supervisor": ["U305", "Q306", "BZ301"],
            "pico_fan_tach": ["U305", "FAN301", "FAN302"], "pico_watchdog_clock": ["U305"],
            "pico_uart": ["U305"], "pi4io9555_keys": ["U306"],
            "pico_encoders": ["ENC301", "ENC302"], "veml7700": ["U308"]}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = path.with_suffix(".tmp")
    stage.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    stage.replace(path)


def success(status):
    return isinstance(status, str) and (status == "PASS" or status.startswith("EMULATION_PASS"))


def record_refs(record):
    values = record.get("design_refs", record.get("refs", []))
    if isinstance(values, str):
        values = [values]
    refs = set()
    for value in values:
        refs.update(re.findall(r"(?<![A-Z0-9])(?:ENC|FAN|BZ|[A-Z]{1,3})[0-9]{3,4}(?![A-Z0-9])", str(value)))
    ident = record.get("id", record.get("module_id", record.get("module", "")))
    refs.update(re.findall(r"(?<![A-Z0-9])(?:ENC|FAN|BZ|[A-Z]{1,3})[0-9]{3,4}(?![A-Z0-9])", str(ident)))
    refs.update(MCU_REFS.get(ident, []))
    return refs


def normalized_record(domain, record, parent):
    ident = str(record.get("id", record.get("module_id", record.get("module", "unnamed"))))
    status = record.get("status", "UNSUPPORTED")
    case_ids = record.get("case_ids", [])
    if "status" not in record and case_ids:
        cases = {x.get("id", x.get("case", x.get("name"))): x for x in parent.get("cases", [])}
        if all(x in cases for x in case_ids):
            status = "EMULATION_PASS" if all(success(cases[x].get("status")) for x in case_ids) else "EMULATION_FAIL"
    default_level = {"mcu": "firmware_module_model", "power": "production_driver_register_model"}.get(domain, "protocol_model")
    level = record.get("coverage_level", record.get("model_level", default_level))
    return {"domain": domain, "id": ident, "refs": sorted(record_refs(record)),
            "status": status, "coverage_level": level, "physical_verified": False,
            "pinout": record.get("pinout"),
            "scenario_count": record.get("case_count", len(record.get("scenarios", record.get("cases", case_ids)))),
            "limitations": record.get("limitations", record.get("limitation", record.get("reason",
                record.get("unsupported", record.get("limits", parent.get("limitations",
                    parent.get("limits", parent.get("unsupported", []))))))))}


def coverage(project, inventory, domains):
    known = {}
    graph_hashes = {}
    for relative, record in inventory["source_snapshots"].items():
        path = project / relative
        if path.stat().st_size != record["bytes"] or sha(path) != record["sha256"]:
            raise ValueError("Inventory source snapshot is stale: " + relative)
    for path in sorted((project / "design").glob("E[1-5].json")):
        graph_hashes[str(path.relative_to(project))] = sha(path)
        for item in read(path)["components"]:
            if item["ref"] in known:
                raise ValueError("Duplicate graph component ref")
            known[item["ref"]] = item
    assigned = [ref for group in inventory["assemblies"] for ref in group["refs"]]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(known):
        raise ValueError("Inventory does not partition the exact current schematic refs")
    models = [normalized_record(name, m, result.get("report", {})) for name, result in domains.items()
              for m in result.get("report", {}).get("modules", [])]
    rows = []
    for interface in inventory["subinterfaces"]:
        ref = interface["ref"]
        if ref not in known:
            raise ValueError("Unknown inventory reference: " + ref)
        if interface["source_pins"] != known[ref]["pins"] or interface["value"] != known[ref]["value"]:
            raise ValueError("Inventory module pins/value differ from graph: " + ref)
        matching = [x for x in models if ref in x["refs"]]
        exercised = [x for x in matching if success(x["status"])]
        failures = [x for x in matching if x["status"] in {"FAIL", "EMULATION_FAIL"}]
        gaps = [x for x in matching if "UNSUPPORTED" in x["status"] and not success(x["status"])]
        connection = [x for x in matching if x["coverage_level"] == "connection_net_model"]
        status = "EMULATION_FAIL" if failures else "EMULATION_PASS" if exercised else "CONNECTION_MODEL_ONLY"
        rows.append({"id": interface["module_id"], "ref": ref, "value": interface["value"],
            "interface_family": interface["interface_family"], "assembly": interface["parent_assembly"],
            "source_status": interface["source_status"], "pinout_gate": interface["pinout_gate"],
            "source_description": interface["source_description"], "source_notes": interface["source_notes"],
            "status": status, "models": matching, "exercised_model_count": len(exercised),
            "connection_status": ("FAIL" if any(x["status"] == "CONNECTION_MODEL_FAIL" for x in connection)
                else "PASS" if connection and all(x["status"] == "CONNECTION_MODEL_PASS" for x in connection) else "NOT_CHECKED"),
            "unmodeled_records": gaps, "constraints": interface["coverage_constraints"],
            "pinout_status": interface["pinout_status"], "pins": interface["source_pins"],
            "physical_status": "NOT_TESTED", "hardware_qualified": False})
    groups = []
    for group in inventory["assemblies"]:
        matches = [x for x in rows if x["ref"] in group["refs"]]
        groups.append({"id": group["module_id"], "sheet": group["sheet"], "name": group["source_group"],
            "refs": group["refs"], "component_count": group["component_count"],
            "interfaces_exercised": sum(x["status"] == "EMULATION_PASS" for x in matches),
            "interface_count": len(matches), "physical_status": "NOT_TESTED",
            "coverage_constraints": group["coverage_constraints"]})
    return {"graph_sha256": graph_hashes, "component_count": len(known), "assembly_count": len(groups),
            "interface_count": len(rows), "assemblies": groups, "interfaces": rows, "model_records": models,
            "catalogue_only_entities": inventory["catalogue_only_entities"],
            "counts": {status: sum(x["status"] == status for x in rows)
                       for status in ("EMULATION_PASS", "EMULATION_FAIL", "CONNECTION_MODEL_ONLY")}}


def render(report, output):
    rows = report["coverage"]["interfaces"]
    labels = {"EMULATION_PASS": "Драйвер / модель: PASS", "EMULATION_FAIL": "Помилка перевірки",
              "CONNECTION_MODEL_ONLY": "Лише з’єднання / не реалізовано"}
    lines = ["# Перевірка підключення модулів SR-RX", "", 
        "Це результати програмних моделей, а не дозвіл підключати залізо. Усі фізичні модулі мають стан NOT_TESTED.", "",
        f"Виконання наборів: **{report['execution_status']}**. Реєстр охоплює {report['coverage']['component_count']} елементи, "
        f"{report['coverage']['assembly_count']} вузли та {len(rows)} деталізованих інтерфейсів.", "",
        "PASS означає виконані сценарії конкретного драйвера або моделі. Відсутність реального USB/kernel, аналогового RF, "
        "калібрування, живлення або механіки залишається явно записаною в JSON та окремих звітах.", "",
        "| Модуль | Позначення | Інтерфейс | З’єднання | Драйвер / функція | Ворота / статус джерела |", "|---|---|---|---|---|---|"]
    for row in rows:
        gate = row["pinout_gate"] or ""
        cells = [row["value"], row["ref"], str(row["interface_family"]), row["connection_status"], labels[row["status"]], str(gate) + " / " + row["source_status"]]
        lines.append("| " + " | ".join(x.replace("|", "\\|").replace("\n", " ") for x in cells) + " |")
    catalogue = report["coverage"]["catalogue_only_entities"]
    lines += ["", "## Каталожні та заводські вузли", "",
        "Ці сутності не мають окремого схемного символу/повної розпіновки в E1–E5. Їхні vendor interfaces залишаються NOT_TESTED; перевірка файлової системи або пов'язаного ref не підтверджує внутрішній контролер.", "",
        "| Сутність | Інтерфейс | Межа | Результат |", "|---|---|---|---|"]
    for entity in catalogue:
        cells = [entity["name"], entity["interface"], entity["scope"], "CATALOGUE_ONLY / NOT_TESTED"]
        lines.append("| " + " | ".join(x.replace("|", "\\|").replace("\n", " ") for x in cells) + " |")
    (output / "MODULE-RESULTS.md").write_text("\n".join(lines) + "\n")
    data = json.dumps(report, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c")
    catalogue_html = '<details><summary>Каталожні та заводські вузли: ' + str(len(catalogue)) + ' · NOT_TESTED</summary><p>Окремі vendor interfaces цих сутностей не емульовані. Перевірка пов’язаного ref або файлової системи не підтверджує внутрішній контролер.</p>'
    for entity in catalogue:
        catalogue_html += '<details><summary>' + html.escape(entity["name"]) + ' · NOT_TESTED</summary><pre>' + html.escape(json.dumps(entity, ensure_ascii=False, indent=2)) + '</pre></details>'
    catalogue_html += '</details>'
    page = '''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SR-RX — підключення модулів</title><style>
body{font:16px/1.5 system-ui;margin:0;background:#111923;color:#e7edf4}main{max-width:1500px;margin:auto;padding:24px}h1{font-size:1.7rem}
input,select{font:inherit;padding:9px;margin:5px;background:#202e3d;color:inherit;border:1px solid #586c83;border-radius:5px}
table{width:100%;border-collapse:collapse;font-size:.9rem}td,th{padding:10px;border:1px solid #3b4d60;text-align:left;vertical-align:top}th{background:#202e3d}
.notice{border-left:4px solid #ddb35a;padding:14px;background:#30291d}.pass{color:#8be4bd}.fail{color:#ff8f94}.partial{color:#efcc82}small{color:#aabbcc}summary{cursor:pointer}pre{white-space:pre-wrap;max-width:70vw}.wrap{overflow:auto}
</style><main><h1>Підключення кожного модуля</h1><p class="notice">Статус стосується програмної емуляції. Фізичне залізо не перевірено. PASS конкретного драйвера не підтверджує всі функції модуля.</p>
<p id="counts"></p><input id="search" placeholder="Назва, позначення або інтерфейс"><select id="filter"><option value="">Усі результати</option><option value="EMULATION_PASS">Перевірені моделі</option><option value="EMULATION_FAIL">Помилки</option><option value="CONNECTION_MODEL_ONLY">Прогалини / лише з’єднання</option></select>
<div class="wrap"><table><thead><tr><th>Модуль</th><th>Інтерфейс</th><th>З’єднання</th><th>Драйвер / функція</th><th>Сценарії та межі</th></tr></thead><tbody id="rows"></tbody></table></div>
<h2>Набори перевірок</h2><pre id="domains"></pre>'''+catalogue_html+'''</main><script type="application/json" id="data">'''+data+'''</script><script>
const report=JSON.parse(document.getElementById('data').textContent),all=report.coverage.interfaces;
const names={EMULATION_PASS:'PASS моделі',EMULATION_FAIL:'Помилка',CONNECTION_MODEL_ONLY:'Лише з’єднання / не реалізовано'};
document.getElementById('counts').textContent=report.coverage.component_count+' елементи · '+report.coverage.assembly_count+' вузли · '+all.length+' інтерфейсів · з’єднання PASS: '+all.filter(x=>x.connection_status==='PASS').length+' · перевірені функціональні моделі: '+report.coverage.counts.EMULATION_PASS+' · виконання: '+report.execution_status;
document.getElementById('domains').textContent=JSON.stringify(Object.fromEntries(Object.entries(report.domains).map(([k,v])=>[k,{exit_code:v.exit_code,status:v.report?.status,error:v.error}])),null,2);
function draw(){const search=document.getElementById('search').value.toLowerCase(),filter=document.getElementById('filter').value,body=document.getElementById('rows');body.replaceChildren();
for(const row of all){if(filter&&row.status!==filter)continue;if(search&&!JSON.stringify([row.value,row.ref,row.interface_family,row.pinout_gate,row.source_status,row.source_notes,row.models]).toLowerCase().includes(search))continue;
const badge=row.pinout_gate?' · Ворота: '+(typeof row.pinout_gate==='string'?row.pinout_gate:JSON.stringify(row.pinout_gate)):'';
const tr=document.createElement('tr');for(const text of [row.ref+' · '+row.value,typeof row.interface_family==='string'?row.interface_family:JSON.stringify(row.interface_family),row.connection_status+badge,names[row.status]]){const td=document.createElement('td');td.textContent=text;tr.append(td);}tr.children[3].className=row.status==='EMULATION_PASS'?'pass':row.status==='EMULATION_FAIL'?'fail':'partial';
const td=document.createElement('td'),details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent=row.models.length+' моделей · фізично НЕ ПЕРЕВІРЕНО';pre.textContent=JSON.stringify({source_status:row.source_status,gate:row.pinout_gate,source_description:row.source_description,source_notes:row.source_notes,models:row.models,constraints:row.constraints,pinout:row.pinout_status,pins:row.pins},null,2);details.append(summary,pre);td.append(details);tr.append(td);body.append(tr);}}
document.getElementById('search').addEventListener('input',draw);document.getElementById('filter').addEventListener('change',draw);draw();
</script></html>'''
    (output / "module-results.html").write_text(page)


def run(args):
    project, output = args.project.resolve(strict=True), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Use a new empty result directory")
    inventory = read(HERE / "inventory.json")
    domains = {}
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join([str(project / "software"), str(project), environment.get("PYTHONPATH", "")])
    environment.update(QT_QPA_PLATFORM="offscreen", ORT_DISABLE_TELEMETRY="1",
                       OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    for name, filename in DOMAINS.items():
        started = time.monotonic()
        path = output / (name + ".json")
        command = [sys.executable, str(HERE / filename), "--project", str(project), "--output", str(path)]
        with (output / (name + ".log")).open("wb") as log:
            try:
                proc = subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=600)
                report = read(path) if path.exists() else {}
                domains[name] = {"exit_code": proc.returncode, "elapsed_s": round(time.monotonic()-started, 3), "report": report}
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                domains[name] = {"exit_code": -1, "error": str(error)[:1000], "report": {}}
        print(name, domains[name]["exit_code"], domains[name]["report"].get("status", "NO_REPORT"), flush=True)
    cov = coverage(project, inventory, domains)
    ok = all(x["exit_code"] == 0 and (success(x["report"].get("status")) or
             x["report"].get("status") == "CONNECTION_MODEL_PASS") for x in domains.values()) and cov["counts"]["EMULATION_FAIL"] == 0
    report = {"schema_version": 1, "execution_status": "PASS" if ok else "FAIL",
        "status": "EMULATION_PASS_WITH_GAPS" if ok else "EMULATION_FAIL",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"architecture": platform.machine(), "kernel": platform.release(), "python": platform.python_version()},
        "physical_tests_performed": False, "hardware_qualified": False,
        "inventory_sha256": sha(HERE / "inventory.json"),
        "model_sha256": {p.name: sha(p) for p in sorted(HERE.glob("*.py"))},
        "domains": domains, "coverage": cov}
    write(output / "report.json", report)
    render(report, output)
    print(json.dumps({"status": report["status"], "counts": cov["counts"], "report": str(output / "report.json")}, ensure_ascii=False))
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--render-report", type=Path)
    args = parser.parse_args()
    if args.render_report:
        args.output.mkdir(parents=True, exist_ok=True)
        render(read(args.render_report), args.output)
        return 0
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
