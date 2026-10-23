#!/usr/bin/env python3
"""Produce an offline project HTML with an embedded, non-recursive source archive."""
import base64
import hashlib
import html as escape_html
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
import os
import zipfile
import sys

BASE = Path(__file__).resolve().parents[1]


def atomic_write(path, data):
    fd, name = tempfile.mkstemp(prefix="sr-rx-stage-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report(relative):
    return json.loads((BASE / relative).read_text(encoding="utf-8"))


def section_id(path):
    return "file-" + re.sub(r"[^a-zA-Z0-9_-]", "-", str(path))


def markdown(path):
    from lxml import html, etree
    p = BASE / path
    rendered = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none"], input=p.read_text(encoding="utf-8"), encoding="utf-8", capture_output=True, check=True).stdout
    fragment = html.fragment_fromstring(rendered, create_parent="div")
    prefix = section_id(path)
    for node in fragment.xpath('.//*[@id]'):
        node.set("id", prefix + "--" + node.get("id"))
    for a in fragment.xpath('.//a[@href]'):
        href = a.get("href")
        if href.startswith(("https:", "http:", "mailto:", "data:")):
            continue
        if href.startswith("#"):
            a.set("href", "#" + prefix + "--" + href[1:])
            continue
        target = href.split("#", 1)[0]
        resolved = (p.parent / target).resolve()
        try:
            rel = resolved.relative_to(BASE)
        except ValueError:
            a.set("href", "#source-archive")
            continue
        if rel.as_posix() in INCLUDED:
            a.set("href", "#" + section_id(rel))
        elif rel.as_posix() == "build/kicad/sr-rx-v2.pdf":
            a.set("href", "#download-pdf")
        else:
            a.set("href", "#source-archive")
    # The offline document never loads scripts or remote media from source text.
    for node in fragment.xpath('.//script|.//iframe|.//object'):
        node.drop_tree()
    return "".join(etree.tostring(c, encoding="unicode", method="html") for c in fragment)


def data_uri(path, mime):
    return "data:" + mime + ";base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def archive():
    target = BASE / "SR-RX-v2-project.zip"
    manifest = []
    paths = []
    for p in sorted(BASE.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(BASE)
        if ((p.suffix.lower() == ".html" and rel.as_posix() != "verification/module-lab/module-results.html") or p.suffix.lower() in {".pyc", ".kicad_prl", ".lck", ".tmp"} or (p.suffix.lower() == ".png" and rel.parts[:2] not in {( "verification", "hmi-views"), ("verification", "linux-lab")}) or (p.suffix.lower() == ".zip" and rel.parts[:2] != ("firmware", "dist")) or "__pycache__" in rel.parts):
            continue
        if any(part in {"tmp", ".git", "qa", ".ruff_cache", ".pytest_cache", ".mypy_cache", ".venv", "venv"} for part in rel.parts):
            continue
        data = p.read_bytes()
        paths.append((rel, data))
        manifest.append({"path": rel.as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    # Store no archive inside itself, and no temporary workstation state.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, data in paths:
            entry = zipfile.ZipInfo("SR-RX-v2/" + rel.as_posix(), date_time=(2026, 10, 20, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            entry.create_system = 3  # Unix mode bits; identical archive bytes on every host
            z.writestr(entry, data, compresslevel=9)
        entry = zipfile.ZipInfo("SR-RX-v2/ARCHIVE-MANIFEST.json", date_time=(2026, 10, 20, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        entry.create_system = 3
        z.writestr(entry, json.dumps(manifest, ensure_ascii=False, indent=2), compresslevel=9)
    payload = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as check:
        if check.testzip() is not None:
            raise SystemExit("Archive CRC validation failed")
    atomic_write(target, payload)
    return target, manifest


CORE = [
    ("Стан та результати перевірок", "COMPLETION.md"),
    ("Емуляція кожного модуля", "verification/module-lab/MODULE-RESULTS.md"),
    ("Стенд моделей модулів", "deployment/module_lab/README.md"),
    ("ARM64 Linux середовище", "deployment/linux_lab/README.md"),
    ("Результати Linux", "verification/linux-lab/README.md"),
    ("Поправки v2.1 (записані в STACK.md)", "build/12-revision-v2.1.md"),
    ("Виконуване керування 20.10", "software/README.md"),
    ("Приймальний процес", "software/RX.md"),
    ("Touch-меню", "software/HMI.md"),
    ("GNSS і джерело координат", "software/LOCATION.md"),
    ("Спектр і маски", "software/SPECTRUM.md"),
    ("Навчання на спектрі", "software/LEARNING.md"),
    ("Експорт моделі", "software/MODEL-EXPORT.md"),
    ("Декодерні адаптери", "software/DECODERS.md"),
    ("Встановлення", "software/DEPLOYMENT.md"),
    ("Апаратні HMI-входи", "software/PERIPHERALS.md"),
    ("Наскрізна перевірка консолі", "software/CONSOLE-REVIEW.md"),
    ("Огляд інтеграції ПЗ", "software/INTEGRATION-REVIEW.md"),
    ("Прошивка Pico", "firmware/pico/README.md"),
    ("Прошивка зовнішньої IMU", "firmware/imu/README.md"),
    ("PCB-підготовка", "build/13-pcb-preparation.md"),
    ("Внутрішнє розведення прототипу", "build/kicad/pcb-prototype/README.md"),
    ("Поточний стан ПЗ і PCB", "build/14-control-software.md"),
    ("Ворота приймання", "OPEN_ITEMS.md"),
    ("Вимоги", "USER_REQUIREMENTS.md"),
    ("STACK — головний документ", "STACK.md"),
    ("Пакет збирання", "build/README.md"),
    ("Живлення", "build/02-zhyvlennia.md"),
    ("РЧ-тракт", "build/03-rf-trakt.md"),
    ("Піни й шини", "build/04-pidkliuchennia-pinout.md"),
    ("Точні таблиці монтажу v2.1", "design/E5-connection-guide.md"),
    ("Механіка", "build/05-mekhanika.md"),
    ("Антени", "build/06-anteny.md"),
    ("План ПЗ", "build/07-pz-vstanovlennia.md"),
    ("Збирання", "build/08-zbyrannia.md"),
    ("Приймальні тести", "build/09-testy.md"),
    ("Початковий кошторис v2", "build/10-bom.md"),
    ("BOM схем v2.1", "build/11-schematic-bom.md"),
    ("Аудит E1", "design/E1-review.md"),
    ("Аудит E2", "design/E2-review.md"),
    ("Аудит E3", "design/E3-review.md"),
    ("Аудит E4", "design/E4-review.md"),
    ("Аудит E5", "design/E5-review.md"),
    ("Незалежна перевірка зарядки/BMS", "design/charger-bms-review.md"),
]
INCLUDED = {p for _, p in CORE}


def release_gates(base):
    """Every pre-archive gate: current, bound and passing reports, else SystemExit."""
    from srrx.commissioning import project_hashes
    from finalize_linux_lab import bound_sources
    report = lambda relative: json.loads((base / relative).read_text(encoding="utf-8"))
    software = report("verification/software-tests.json")
    graphs, sources = project_hashes(base)
    if (software.get("host_regression_status") != "PASS" or software.get("graph_sha256") != graphs
            or software.get("source_sha256") != sources
            or software.get("test_environment", {}).get("internet_sockets_denied") is not True):
        raise SystemExit("Package only after current-source software regression PASS with Internet sockets denied; report is stale or failed")
    module_report = report("verification/module-lab/report.json")
    linux_report = report("verification/linux-lab/report.json")
    if module_report.get("execution_status") != "PASS" or linux_report.get("status") != "PASS":
        raise SystemExit("Package only after Linux and module-lab PASS")
    lab_binding = report("verification/linux-lab/source-binding.json")
    stale = [relative for relative, expected in lab_binding["source_sha256"].items()
             if not (base / relative).is_file() or hashlib.sha256((base / relative).read_bytes()).hexdigest() != expected]
    unbound = sorted(bound_sources(base) - set(lab_binding["source_sha256"]))
    if hashlib.sha256((base / "verification/linux-lab/report.json").read_bytes()).hexdigest() != lab_binding["linux_report_sha256"]:
        raise SystemExit("Linux/module report binding changed: verification/linux-lab/report.json")
    module_rebound = hashlib.sha256((base / "verification/module-lab/report.json").read_bytes()).hexdigest() != lab_binding["module_report_sha256"]
    # A stale ARM64 result may be packaged only when the project itself marks it as
    # a record of an earlier run; the HTML then says so next to the main notice.
    record_path = base / "verification/linux-lab/project-manifest.json"
    record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.is_file() else {}
    earlier_record = isinstance(record, dict) and record.get("record_status") == "RECORD_OF_EARLIER_RUN"
    linux_notice = ""
    if stale or unbound or module_rebound:
        if not earlier_record:
            hint = "; rerun the ARM64 lab, or mark verification/linux-lab as RECORD_OF_EARLIER_RUN"
            if stale:
                raise SystemExit("Linux execution result is stale: " + stale[0] + hint)
            if unbound:
                raise SystemExit("Linux execution result does not cover current sources: " + ", ".join(unbound[:12]) + hint)
            raise SystemExit("Linux/module report binding changed: verification/module-lab/report.json" + hint)
        environment = module_report.get("environment", {})
        changed = len(stale) + len(unbound)
        linux_notice = ('<div class="notice"><b>ARM64 Linux lab — лише запис попереднього прогону.</b> '
                        f'Після нього змінено або додано {changed} виконуваних файлів (прив’язано {len(lab_binding["source_sha256"])}), тож його PASS не переноситься на цю редакцію; '
                        'повторний ARM64 прогін не виконано. Емуляцію модулів перегенеровано на '
                        f'{escape_html.escape(str(environment.get("architecture", "?")))} '
                        f'({escape_html.escape(str(module_report.get("created_at_utc", ""))[:10])}), не в ARM64 guest.</div>')
    models = base / "deployment/module_lab"
    if module_report["inventory_sha256"] != hashlib.sha256((models / "inventory.json").read_bytes()).hexdigest():
        raise SystemExit("Module inventory result is stale")
    if module_report["model_sha256"] != {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(models.glob("*.py"))}:
        raise SystemExit("Module models changed after their run")
    for relative, expected in module_report["coverage"]["graph_sha256"].items():
        if hashlib.sha256((base / relative).read_bytes()).hexdigest() != expected:
            raise SystemExit("Module graph result is stale: " + relative)
    verification = report("verification/validation.json")
    if verification["graph_netlist_comparison"] != "PASS" or verification["erc_counts"]:
        raise SystemExit("Package only after graph comparison and ERC with no reported violations")
    schematics = {p.relative_to(base).as_posix(): sha(p) for p in sorted((base / "build/kicad").glob("*.kicad_sch"))}
    if verification["sha256"] != schematics:
        raise SystemExit("CAD verification is stale: validated schematics differ from build/kicad")
    inputs = {r["file"]: r["sha256"] for r in verification.get("input_files", [])}
    if set(inputs) != {"verification/erc.json", "verification/netlist.xml"} or any(sha(base / f) != h for f, h in inputs.items()):
        raise SystemExit("CAD verification is not bound to the current ERC/netlist; rerun tools/run_checks.py")
    # Every shipped CAD/PCB PASS report must be bound to the files it checked.
    design = {p.relative_to(base).as_posix(): sha(p) for p in sorted((base / "design").glob("E[1-5].json"))}
    invariants = report("verification/electrical-invariants.json")
    if invariants.get("status") != "PASS" or invariants.get("input_sha256") != design:
        raise SystemExit("Electrical invariant report is stale or failed; rerun tools/run_checks.py")
    independent = report("verification/independent-netlist-review.json")
    if (independent.get("passed") is not True or independent.get("netlist_sha256") != sha(base / "verification/netlist.xml")
            or independent.get("graph_sha256") != {Path(f).name: h for f, h in design.items()}):
        raise SystemExit("Independent netlist review is stale or failed; rerun tools/run_checks.py")
    detector = subprocess.run([sys.executable, "-X", "utf8", str(base / "design/E4-detector-analysis.py"), "--json"], cwd=base, encoding="utf-8", capture_output=True, check=True).stdout
    if {k: v for k, v in json.loads(detector).items() if k != "design_file"} != {k: v for k, v in report("verification/dc-detector-analysis.json").items() if k != "design_file"}:
        raise SystemExit("DC-detector analysis report is stale; rerun tools/run_checks.py")
    starter = report("verification/pcb-review.json")
    if (starter.get("passed") is not True or starter["board_sha256"] != sha(base / starter["board_file"])
            or starter["input_sha256"] != sha(base / starter["input_file"]) or starter["drc"]["raw_sha256"] != sha(base / starter["drc"]["raw_file"])):
        raise SystemExit("PCB placement review is stale or failed; rerun pcb/generate_layout.py")
    routed_board = base / "build/kicad/pcb-prototype/detector-core-routed-prototype.kicad_pcb"
    proto = report("verification/pcb-prototype-review.json")
    drc = proto.get("drc", {})
    if (proto.get("status") != "ROUTED_INTERNAL_PROTOTYPE_NOT_FOR_FABRICATION" or proto.get("published_board") is not True
            or proto.get("board_sha256") != sha(routed_board) or drc.get("raw_sha256") != sha(base / "build/kicad/pcb-prototype/drc-raw.json")
            or drc.get("exit_code") != 0 or any(drc["sections"].values()) or drc["ignored_checks"] or proto["source_pad_audit"]["passed"] is not True):
        raise SystemExit("Routed prototype review is stale or not clean; rerun pcb/generate_routed.py")
    if subprocess.run([sys.executable, str(base / "tools/build_firmware.py"), "--check"], cwd=base).returncode:
        raise SystemExit("Firmware packages are stale; rerun tools/build_firmware.py")
    pdf = base / "build/kicad/sr-rx-v2.pdf"
    if not pdf.read_bytes().rstrip().endswith(b"%%EOF"):
        raise SystemExit("PDF is incomplete; regenerate it before packaging")
    # The PDF has no hash of its own in validation.json; its export record binds it.
    export = report("verification/pdf-export.json")
    if export.get("pdf") != {"file": "build/kicad/sr-rx-v2.pdf", "sha256": sha(pdf)} or export.get("kicad_sch_sha256") != schematics:
        raise SystemExit("Schematic PDF is not the export of the current verified schematics; run tools/run_checks.py --export")
    missing_core = [p for _, p in CORE if not (base / p).is_file()]
    if missing_core:
        raise SystemExit("Missing CORE documents: " + ", ".join(missing_core))
    return {"starter": starter, "proto": proto, "pdf": pdf, "linux_notice": linux_notice}


def main():
    sys.path[:0] = [str(BASE / "software"), str(BASE / "tools")]
    gates = release_gates(BASE)
    starter, proto, pdf, linux_notice = gates["starter"], gates["proto"], gates["pdf"], gates["linux_notice"]
    drc = proto["drc"]
    from lxml import html, etree
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf  # PyMuPDF < 1.24.3 only has the legacy name
    source_zip, manifest = archive()
    generated = report("build/kicad/generation-manifest.json")
    nav = [f'<li><a href="#{section_id(p)}">{escape_html.escape(title)}</a></li>' for title, p in CORE]
    sections = []
    for title, p in CORE:
        sections.append(f'<section id="{section_id(p)}"><div class="eyebrow">{escape_html.escape(p)}</div>{markdown(p)}</section>')
    pdf_link = f'<a class="button" id="download-pdf" download="sr-rx-v2.pdf" href="{data_uri(pdf,"application/pdf")}">Завантажити PDF схем</a>'
    zip_link = f'<a class="button" id="source-archive" download="SR-RX-v2-project.zip" href="{data_uri(source_zip,"application/zip")}">Завантажити весь проєкт ZIP</a>'
    gallery = []
    for filename, title in [("01-overview.png", "Меню: стан системи"), ("03-spectrum.png", "Меню: спектр"), ("05-teach-classify.png", "Меню: навчання")]:
        preview = BASE / "verification/hmi-views" / filename
        if preview.exists():
            gallery.append(f'<details><summary>{title} — справжній Qt, SIMULATION</summary><img loading="lazy" alt="{title}" src="{data_uri(preview,"image/png")}"></details>')
    overlay = BASE / "build/12-revision-v2.1.svg"
    if overlay.exists():
        gallery.append(f'<details><summary>Зміни габаритів і зовнішній S-band вузол v2.1</summary><img loading="lazy" alt="Механічні поправки v2.1; ескіз, не виробниче креслення" src="{data_uri(overlay,"image/svg+xml")}"></details>')
    placement = BASE / "build/kicad/pcb-preparation/detector-core-placement.svg"
    if placement.exists():
        gallery.append(f'<details><summary>DC_CORE: {starter["components"]} компонент, нерозведений PCB starter</summary><p class="muted">{starter["source_pins"]} контактів зіставлені зі схемою. Трас немає, DRC містить непідключення. Цей макет не призначений для виготовлення.</p><img loading="lazy" alt="DC_CORE unrouted placement candidate" src="{data_uri(placement,"image/svg+xml")}"></details>')
    routed = BASE / "build/kicad/pcb-prototype/detector-core-routed-prototype.svg"
    if routed.exists():
        gallery.append(f'<details><summary>DC_CORE: внутрішній розведений прототип, raw DRC{sum(drc["sections"].values())}</summary><p class="muted">{proto["source_pad_audit"]["parts"]} компонент,{proto["source_pad_audit"]["pins"]} контактів. Зовнішні інтерфейси/MPN/механіка й фізична кваліфікація відкриті; НЕ ДЛЯ ВИГОТОВЛЕННЯ.</p><img loading="lazy" alt="Internal routed prototype; not for fabrication" src="{data_uri(routed,"image/svg+xml")}"></details>')
    # Light previews keep this single file practical on a phone. The PDF and ZIP
    # retain the full vector originals; thumbnails are not fabrication drawings.
    with pymupdf.open(pdf) as pdf_doc:
        pages = [{"stem": "sr-rx-v2", "title": "Зміст електричної схеми"}] + generated["pages"]
        if len(pdf_doc) != len(pages):
            raise SystemExit("PDF page count differs from generated project")
        for i, p in enumerate(pages):
            page = pdf_doc[i]
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2000 / page.rect.width, 2000 / page.rect.width), alpha=False)
            preview = 'data:image/png;base64,' + base64.b64encode(pix.tobytes('png')).decode('ascii')
            gallery.append(f'<details><summary>{escape_html.escape(p["title"])}</summary><p class="muted">Це зменшений огляд. Для читання контактів і масштабування завантажте векторний PDF; SVG є в ZIP.</p><img loading="lazy" alt="{escape_html.escape(p["title"])}" src="{preview}"></details>')
    doc = '''<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SR-RX-v2.1 — проєкт і перевірки</title><style>
:root{color-scheme:light dark;--bg:#fcfcfa;--fg:#182331;--muted:#5b6672;--line:#d7dee4;--paper:#fff;--accent:#1c5c78;--warn:#fff3d9;--warnfg:#543c09}
@media(prefers-color-scheme:dark){:root{--bg:#111820;--fg:#e4eaf0;--muted:#a2afbd;--line:#334252;--paper:#1b2530;--accent:#80c7e7;--warn:#392e18;--warnfg:#f9df9c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 system-ui,sans-serif}a{color:var(--accent)}nav{position:fixed;width:270px;padding:24px 20px;inset:0 auto 0 0;overflow:auto;border-right:1px solid var(--line)}nav ol{padding-left:20px}nav li{margin:6px 0}main{margin-left:270px;max-width:1280px;padding:32px 40px;overflow-wrap:anywhere}h1{font-size:1.8rem;line-height:1.2}h2{margin-top:1.6em;font-size:1.3rem}h3{font-size:1.08rem}.eyebrow,.muted{color:var(--muted);font-size:.85rem}.eyebrow{text-transform:none;letter-spacing:.03em}section{padding:28px 0;border-top:2px solid var(--line);margin-top:28px}.notice{padding:16px 20px;border-left:4px solid #bd8b28;background:var(--warn);color:var(--warnfg);margin:20px 0}.button{display:inline-block;border:1px solid var(--accent);border-radius:7px;padding:10px 16px;text-decoration:none;margin:5px 8px 5px 0;font-weight:600}table{display:block;max-width:100%;overflow-x:auto;border-collapse:collapse;font-size:.86rem}td,th{border:1px solid var(--line);padding:7px 10px;vertical-align:top;min-width:80px}th{background:var(--paper)}pre{white-space:pre-wrap;overflow-x:auto;padding:14px;background:var(--paper);border:1px solid var(--line);border-radius:6px;font-size:.83rem}code{font-family:ui-monospace,monospace;font-size:.9em}details{padding:12px;border:1px solid var(--line);margin:12px 0;border-radius:6px}summary{cursor:pointer;font-weight:650}img{display:block;width:100%;height:auto;background:#fff;margin-top:12px}blockquote{margin-left:0;padding-left:16px;border-left:3px solid var(--line)}@media(max-width:900px){nav{position:static;width:auto;border:0;border-bottom:1px solid var(--line)}nav ol{columns:2;font-size:.88rem}main{margin:0;padding:20px 16px}}@media print{nav,.button{display:none}main{margin:0;max-width:none;padding:0}details{break-inside:avoid}section{break-before:page}}
</style></head><body><nav><b>SR-RX-v2.1</b><p class="muted">оновлено 23 жовтня 2026<br>Редагована схема · документація · аудит</p><ol>'''+"".join(nav)+'''<li><a href="#schematics">Огляд схем</a></li><li><a href="#downloads">Вбудовані файли</a></li></ol></nav><main><div class="eyebrow">Інженерна редакція від коміту 4653188</div><h1>Супутниковий приймач і портативна радіолабораторія</h1><p>В ефірі — лише прийом. Автономне ядро Radxa Dragon Q6A, RTL-SDR, HF+ та Lime.</p><div class="notice"><b>Стендове приймання не виконано.</b> Цей комплект містить відновлені й перевірені програмно схеми та конкретні умови їх апаратного приймання. Він не є дозволом на виготовлення PCB або підключення неперевіреного акумуляторного вузла.</div>'''+linux_notice+pdf_link+zip_link+"".join(sections)+'''<section id="schematics"><h1>Огляд електричних схем KiCad</h1><p>Усі сторінки експортовано з редагованого проєкту. З'єднання (дроти, вузли й глобальні мітки) перевірено порівнянням XML-netlist із графами design/E*.json.</p>'''+"".join(gallery)+'''</section><section id="downloads"><h1>Вбудовані файли</h1><p>Кнопки на початку документа працюють без інтернету. ZIP містить усі доступні вихідні документи, первинні журнали аудиту, графи, KiCad, SVG, PDF, BOM, перевірки та генератори. Головний HTML не вкладено в ZIP, щоб уникнути рекурсії; окремий автономний звіт модулів міститься в verification/module-lab/module-results.html.</p><p class="muted">У ZIP '''+str(len(manifest))+''' файлів. Контрольні суми наведені у вкладеному ARCHIVE-MANIFEST.json. Початковий Git збережено історією комітів.</p></section></main></body></html>'''
    out = BASE / "SR-RX-v2-ves-proekt.html"
    # Verify every data attachment byte-for-byte. Missing CORE documents fail
    # above; stale legacy heading anchors are rerouted below, never left dead.
    # Embedded archives legitimately exceed libxml's default 10MB attribute
    # limit. Parse our own generated document without silently truncating them.
    tree = html.fromstring(doc, parser=html.HTMLParser(huge_tree=True))
    ids = {e.get("id") for e in tree.xpath('//*[@id]')}
    missing = sorted({a.get("href")[1:] for a in tree.xpath('//a[starts-with(@href,"#")]') if a.get("href")[1:] not in ids})
    # The historic Markdown contains several stale heading anchors. Route any such
    # reference to its document section instead of publishing a dead anchor.
    for a in tree.xpath('//a[starts-with(@href,"#")]'):
        target = a.get("href")[1:]
        if target not in ids:
            base_id = target.split("--", 1)[0]
            a.set("href", "#" + (base_id if base_id in ids else "source-archive"))
    for link, original in [("download-pdf", pdf), ("source-archive", source_zip)]:
        node = tree.xpath('//*[@id=$id]', id=link)[0]
        if base64.b64decode(node.get("href").split(",", 1)[1]) != original.read_bytes():
            raise SystemExit("Embedded attachment differs from its file: " + link)
    atomic_write(out, ('<!doctype html>\n' + etree.tostring(tree, encoding="unicode", method="html")).encode())
    print(json.dumps({"html_bytes": out.stat().st_size, "archive_bytes": source_zip.stat().st_size, "archive_files": len(manifest), "legacy_heading_links_repaired": len(missing),
                      "schematic_pages": len(pages), "linux_lab": "RECORD_OF_EARLIER_RUN" if linux_notice else "CURRENT"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
