#!/usr/bin/env python3
"""Produce an offline project HTML with an embedded, non-recursive source archive."""
import base64
from datetime import datetime
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
from lxml import html, etree
import fitz

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


def section_id(path):
    return "file-" + re.sub(r"[^a-zA-Z0-9_-]", "-", str(path))


def markdown(path):
    p = BASE / path
    rendered = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none"], input=p.read_text(), text=True, capture_output=True, check=True).stdout
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
        if str(rel) in INCLUDED:
            a.set("href", "#" + section_id(rel))
        elif str(rel) == "build/kicad/sr-rx-v2.pdf":
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
        if p.suffix.lower() in {".html", ".zip", ".png", ".pyc", ".kicad_prl", ".lck", ".tmp"} or "__pycache__" in rel.parts:
            continue
        if any(part in {"tmp", ".git", "qa"} for part in rel.parts):
            continue
        data = p.read_bytes()
        paths.append((rel, data))
        manifest.append({"path": str(rel), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    # Store no archive inside itself, and no temporary workstation state.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, data in paths:
            z.writestr("SR-RX-v2/" + str(rel), data)
        z.writestr("SR-RX-v2/ARCHIVE-MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    payload = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as check:
        assert check.testzip() is None, "Archive CRC validation failed"
    atomic_write(target, payload)
    return target, manifest


CORE = [
    ("Стан та результати перевірок", "COMPLETION.md"),
    ("Пріоритетні поправки v2.1", "build/12-revision-v2.1.md"),
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


def main():
    verification = json.loads((BASE / "verification/validation.json").read_text())
    if verification["graph_netlist_comparison"] != "PASS" or verification["erc_counts"]:
        raise SystemExit("Package only after graph comparison and the full ERC pass")
    pdf = BASE / "build/kicad/sr-rx-v2.pdf"
    if not pdf.read_bytes().rstrip().endswith(b"%%EOF"):
        raise SystemExit("PDF is incomplete; regenerate it before packaging")
    source_zip, manifest = archive()
    generated = json.loads((BASE / "build/kicad/generation-manifest.json").read_text())
    nav = [f'<li><a href="#{section_id(p)}">{escape_html.escape(title)}</a></li>' for title, p in CORE]
    sections = []
    for title, p in CORE:
        if (BASE / p).exists():
            sections.append(f'<section id="{section_id(p)}"><div class="eyebrow">{escape_html.escape(p)}</div>{markdown(p)}</section>')
    pdf_link = f'<a class="button" id="download-pdf" download="sr-rx-v2.pdf" href="{data_uri(pdf,"application/pdf")}">Завантажити PDF схем</a>'
    zip_link = f'<a class="button" id="source-archive" download="SR-RX-v2-project.zip" href="{data_uri(source_zip,"application/zip")}">Завантажити весь проєкт ZIP</a>'
    gallery = []
    overlay = BASE / "build/12-revision-v2.1.svg"
    if overlay.exists():
        gallery.append(f'<details><summary>Зміни габаритів і зовнішній S-band вузол v2.1</summary><img loading="lazy" alt="Механічні поправки v2.1; ескіз, не виробниче креслення" src="{data_uri(overlay,"image/svg+xml")}"></details>')
    # Light previews keep this single file practical on a phone. The PDF and ZIP
    # retain the full vector originals; thumbnails are not fabrication drawings.
    with fitz.open(pdf) as pdf_doc:
        pages = [{"stem": "sr-rx-v2", "title": "Зміст електричної схеми"}] + generated["pages"]
        assert len(pdf_doc) == len(pages), "PDF page count differs from generated project"
        for i, p in enumerate(pages):
            page = pdf_doc[i]
            pix = page.get_pixmap(matrix=fitz.Matrix(1000 / page.rect.width, 1000 / page.rect.width), alpha=False)
            preview = 'data:image/png;base64,' + base64.b64encode(pix.tobytes('png')).decode('ascii')
            gallery.append(f'<details><summary>{escape_html.escape(p["title"])}</summary><p class="muted">Це зменшений огляд. Для читання контактів і масштабування завантажте векторний PDF; SVG є в ZIP.</p><img loading="lazy" alt="{escape_html.escape(p["title"])}" src="{preview}"></details>')
    doc = '''<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SR-RX-v2.1 — проєкт і перевірки</title><style>
:root{color-scheme:light dark;--bg:#fcfcfa;--fg:#182331;--muted:#5b6672;--line:#d7dee4;--paper:#fff;--accent:#1c5c78;--warn:#fff3d9;--warnfg:#543c09}
@media(prefers-color-scheme:dark){:root{--bg:#111820;--fg:#e4eaf0;--muted:#a2afbd;--line:#334252;--paper:#1b2530;--accent:#80c7e7;--warn:#392e18;--warnfg:#f9df9c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 system-ui,sans-serif}a{color:var(--accent)}nav{position:fixed;width:270px;padding:24px 20px;inset:0 auto 0 0;overflow:auto;border-right:1px solid var(--line)}nav ol{padding-left:20px}nav li{margin:6px 0}main{margin-left:270px;max-width:1280px;padding:32px 40px;overflow-wrap:anywhere}h1{font-size:1.8rem;line-height:1.2}h2{margin-top:1.6em;font-size:1.3rem}h3{font-size:1.08rem}.eyebrow,.muted{color:var(--muted);font-size:.85rem}.eyebrow{text-transform:none;letter-spacing:.03em}section{padding:28px 0;border-top:2px solid var(--line);margin-top:28px}.notice{padding:16px 20px;border-left:4px solid #bd8b28;background:var(--warn);color:var(--warnfg);margin:20px 0}.button{display:inline-block;border:1px solid var(--accent);border-radius:7px;padding:10px 16px;text-decoration:none;margin:5px 8px 5px 0;font-weight:600}table{display:block;max-width:100%;overflow-x:auto;border-collapse:collapse;font-size:.86rem}td,th{border:1px solid var(--line);padding:7px 10px;vertical-align:top;min-width:80px}th{background:var(--paper)}pre{white-space:pre-wrap;overflow-x:auto;padding:14px;background:var(--paper);border:1px solid var(--line);border-radius:6px;font-size:.83rem}code{font-family:ui-monospace,monospace;font-size:.9em}details{padding:12px;border:1px solid var(--line);margin:12px 0;border-radius:6px}summary{cursor:pointer;font-weight:650}img{display:block;width:100%;height:auto;background:#fff;margin-top:12px}blockquote{margin-left:0;padding-left:16px;border-left:3px solid var(--line)}@media(max-width:900px){nav{position:static;width:auto;border:0;border-bottom:1px solid var(--line)}nav ol{columns:2;font-size:.88rem}main{margin:0;padding:20px 16px}}@media print{nav,.button{display:none}main{margin:0;max-width:none;padding:0}details{break-inside:avoid}section{break-before:page}}
</style></head><body><nav><b>SR-RX-v2.1</b><p class="muted">19 жовтня 2026<br>Редагована схема · документація · аудит</p><ol>'''+"".join(nav)+'''<li><a href="#schematics">Огляд схем</a></li><li><a href="#downloads">Вбудовані файли</a></li></ol></nav><main><div class="eyebrow">Інженерна редакція від коміту 4653188</div><h1>Супутниковий приймач і портативна радіолабораторія</h1><p>В ефірі — лише прийом. Автономне ядро Radxa Dragon Q6A, RTL-SDR, HF+ та Lime.</p><div class="notice"><b>Стендове приймання не виконано.</b> Цей комплект містить відновлені й перевірені програмно схеми та конкретні умови їх апаратного приймання. Він не є дозволом на виготовлення PCB або підключення неперевіреного акумуляторного вузла.</div>'''+pdf_link+zip_link+"".join(sections)+'''<section id="schematics"><h1>Огляд електричних схем KiCad</h1><p>Усі сторінки експортовано з редагованого проєкту. З'єднання через однакові глобальні мітки перевірено порівнянням із XML-netlist.</p>'''+"".join(gallery)+'''</section><section id="downloads"><h1>Вбудовані файли</h1><p>Кнопки на початку документа працюють без інтернету. ZIP містить усі доступні вихідні документи, первинні журнали аудиту, графи, KiCad, SVG, PDF, BOM, перевірки та генератори. HTML не вкладено в ZIP, щоб уникнути рекурсії.</p><p class="muted">У ZIP '''+str(len(manifest))+''' файлів. Контрольні суми наведені у вкладеному ARCHIVE-MANIFEST.json. Початковий Git збережено історією комітів.</p></section></main></body></html>'''
    out = BASE / "SR-RX-v2-ves-proekt.html"
    # Verify every data attachment byte-for-byte, and fail on broken internal links.
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
        assert base64.b64decode(node.get("href").split(",", 1)[1]) == original.read_bytes()
    atomic_write(out, ('<!doctype html>\n' + etree.tostring(tree, encoding="unicode", method="html")).encode())
    print(json.dumps({"html_bytes": out.stat().st_size, "archive_bytes": source_zip.stat().st_size, "archive_files": len(manifest), "legacy_heading_links_repaired": len(missing)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
