#!/usr/bin/env python3
"""Assemble review, connection and component inventories from the reviewed graphs."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.append(str(BASE / "tools"))
from uk_text import drift_sentence, plural  # noqa: E402  (plural re-exported for earlier callers)


def md(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def read_optional(relative):
    path = BASE / relative
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_for(recorded, current):
    """True when a report's recorded SHA256 map equals the present bytes; None if that cannot be computed."""
    try:
        return recorded == current() if recorded else None
    except (OSError, ValueError, ImportError):
        return None


def evidence_note(current, subject):
    # A PASS recorded for other bytes is not evidence for the present tree.
    if current is None:
        return f" Відповідність поточним джерелам ({subject}) не перевірено."
    return "" if current else f" **Отримано для попередньої редакції джерел:** {subject} не підтверджує поточний код, потрібен новий запуск."


def electrical_pages(report, generated):
    """Pages of the generated schematic; the netlist must show as many sheets with parts
    (validate_project does not count the root index)."""
    pages = len(generated["pages"])
    if report.get("electrical_sheets") != pages:
        raise SystemExit(f"verification/validation.json electrical_sheets={report.get('electrical_sheets')} differs from "
                         f"{pages} pages in build/kicad/generation-manifest.json; rerun tools/run_checks.py")
    return pages


def lab_evidence(binding, base=BASE):
    """evidence_note of the ARM64 run, with the drift sentence the bundle notice repeats."""
    try:
        from finalize_linux_lab import binding_drift
        drift = drift_sentence(binding_drift(base, binding)) if binding.get("source_sha256") else None
    except (OSError, ValueError, KeyError, ImportError):
        drift = None
    if drift is None:
        return evidence_note(None, "ARM64 прогін")
    return evidence_note(False, "ARM64 прогін") + " Після прогону " + drift + "." if drift else ""


def main():
    graphs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((BASE / "design").glob("E[1-5].json"))]
    report = json.loads((BASE / "verification/validation.json").read_text(encoding="utf-8"))
    generated = json.loads((BASE / "build/kicad/generation-manifest.json").read_text(encoding="utf-8"))
    software = read_optional("verification/software-tests.json")
    linux = read_optional("verification/linux-lab/report.json")
    guest = read_optional("verification/linux-lab/software-tests.json")
    binding = read_optional("verification/linux-lab/source-binding.json")
    modules = read_optional("verification/module-lab/report.json")
    sys.path[:0] = [str(BASE / "software"), str(BASE / "tools")]

    def module_sources():
        lab = BASE / "deployment/module_lab"
        return {"inventory": sha(lab / "inventory.json"), "models": {p.name: sha(p) for p in sorted(lab.glob("*.py"))},
                "graphs": {name: sha(BASE / name) for name in modules["coverage"]["graph_sha256"]}}
    if modules:
        coverage, connect = modules["coverage"], modules.get("domains", {}).get("connectivity", {}).get("report", {})
        counts, connect_counts = coverage.get("counts", {}), connect.get("summary", {})
        recorded = {"inventory": modules.get("inventory_sha256"), "models": modules.get("model_sha256"), "graphs": coverage.get("graph_sha256")}
        module_note = (f"Емуляція модулів: виконання **{modules['execution_status']}**, загальний статус **{modules.get('status', 'NOT_RUN')}**, "
                       f"{plural(coverage['component_count'], 'елемент', 'елементи', 'елементів')}, {plural(coverage['assembly_count'], 'вузол', 'вузли', 'вузлів')}, "
                       f"{plural(coverage['interface_count'], 'інтерфейс', 'інтерфейси', 'інтерфейсів')}. "
                       f"Функціональні моделі покрили {plural(counts.get('EMULATION_PASS', 0), 'інтерфейс', 'інтерфейси', 'інтерфейсів')} ({counts.get('EMULATION_FAIL', 0)} FAIL); "
                       f"{plural(counts.get('CONNECTION_MODEL_ONLY', 0), 'інтерфейс має', 'інтерфейси мають', 'інтерфейсів мають')} лише модель з'єднань, і їхні функції залишаються непідтвердженими. "
                       f"Модель з'єднань: **{connect.get('status', 'NOT_RUN')}**, {plural(connect_counts.get('cases', 0), 'topology/fault сценарій', 'topology/fault сценарії', 'topology/fault сценаріїв')}, {connect_counts.get('failed', 0)} FAIL."
                       + evidence_note(current_for(recorded, module_sources), "модульний прогін")
                       + " [Таблиця](verification/module-lab/MODULE-RESULTS.md).")
    else:
        module_note = "Результати модулів зберігаються окремо; сам інвентар не доводить успішну емуляцію."
    items = [dict(x, sheet=g["sheet"]) for g in graphs for x in g.get("open_items", [])]
    blockers = [x for x in items if x.get("blocking")]
    lines = ["# Ворота приймання SR-RX-v2.1", "", "Жоден стендовий тест не виконано. `OPEN` не означає, що виявлено несправність конкретного екземпляра: це умова, без підтвердження якої його не можна приймати чи підключати. Стан апаратного випуску — **BLOCKED**.", "", "Основні інструкції українською наведено в аудитах [E1](design/E1-review.md), [E2](design/E2-review.md), [E3](design/E3-review.md), [E4](design/E4-review.md), [E5](design/E5-review.md) та [таблицях монтажу](design/E5-connection-guide.md). Нижче — повний реєстр ідентифікаторів із машинного контракту.", ""]
    for item in items:
        lines += [f"## {item['id']} — {'OPEN / блокує випуск' if item.get('blocking') else 'умова окремої опції'}", "", md(item["description"]), "", "**Умова закриття:** " + md(item.get("resolve", "")), ""]
    lines += ["## Додаткова калібровка аварійного ADC", "", "Дільник E1 100 kΩ / 20 kΩ з допуском 1% та LM4040C30 0.5% не дають точного батарейного порога без калібровки. Початкова похибка біля 13.05 V може становити приблизно ±0.28 V. Перед штатним запуском потрібні дві опорні напруги, запис scale/offset із серійним номером пристрою та перевірка відсічки 13.05±0.1 V за кімнатної і підвищеної температури. Немає чинної калібровки — штатний режим заборонений.", "", "## Правило звітності", "", "Синтаксично валідний KiCad, збіг переліків з'єднань і навіть ERC без помилок не закривають ці ворота. Заборонено записувати PASS без виміряних даних, умов тесту, приладу й дати."]
    (BASE / "OPEN_ITEMS.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    rows = []
    for g in graphs:
        for c in g["components"]:
            rows.append([g["sheet"], c["ref"], c["value"], c.get("kind", ""), c.get("status", ""), "DNP" if c.get("dnp") else "", c.get("footprint", ""),
                         c.get("manufacturer", ""), c.get("mpn", ""), c.get("lcsc", ""), c.get("source", ""), "; ".join(c.get("notes", []))])
    with (BASE / "build/11-schematic-bom.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        w.writerow(["Аркуш", "Позначення", "Деталь / номінал", "Тип", "Статус", "Не монтувати", "Посадкове місце", "Виробник", "MPN", "LCSC", "Джерело", "Примітки"])
        w.writerows(rows)
    # This inventory is not added to the old purchasing BOM: on-module parts may
    # already be supplied with a commercial assembly.
    (BASE / "build/11-schematic-bom.md").write_text("""# Перелік елементів електричної схеми v2.1

[11-schematic-bom.csv](11-schematic-bom.csv) формується з перевірених графів E1–E5. Це перелік позначених на схемі елементів, а не готовий кошик покупок. Частина резисторів, мікросхем і роз'ємів уже входить до готових модулів; повторно замовляти їх автоматично не можна.

Колонка DNP означає «не монтувати». `design` — обране в цій редакції проєктне рішення; `verified` — перевірена документація, а не результат стенду. Порожнє посадкове місце не дозволяє виготовляти PCB.

Посадкове місце, виробник, MPN і код LCSC записує в графи `tools/build_parts.py` з бази деталей [design/parts/parts.json](../design/parts/parts.json); там же — альтернативи, причини одного джерела й позиції TBD. Закупівельний перелік v2.1 за цією базою — [10-zakupivlia.md](10-zakupivlia.md) і [10-zakupivlia.csv](10-zakupivlia.csv).

Початковий кошторис [10-bom.md](10-bom.md) і [10-bom.csv](10-bom.csv) залишається оцінкою редакції v2 від 18.10.2026. Він не є підтвердженою ціною оновлених схем. Заміни перетворювача, додаткові захисти, детектори, пасиви та конструктивні зміни мають бути включені в остаточний кошик за конкретними MPN і кількостями, без подвійного обліку деталей модулів. Непідтверджені ціни не прирівняно до нуля.

Джерела і розрахунки змін: [E1](../design/E1-review.md), [E2](../design/E2-review.md), [E3](../design/E3-review.md), [E4](../design/E4-review.md), [E5](../design/E5-review.md).
""", encoding="utf-8", newline="\n")
    # Explicitly conservative reference contract. It is data for the future
    # firmware implementation, not a service that writes GPIOs.
    controls = {}
    for g in graphs:
        for c in g["components"]:
            for p in c["pins"]:
                net = p.get("net", "")
                if net.startswith(("EN_", "SW_")) or net in {"K1_ON", "K2_ON", "PICO_DISP_EN", "CHG_INHIBIT"}:
                    controls.setdefault(net, []).append({"ref": c["ref"], "pin": str(p["number"]), "type": p.get("type", "")})
    readiness = {
        "schema_version": 1,
        "hardware_readiness": False,
        "production_release": False,
        "custom_firmware_implemented_and_tested": False,
        "custom_firmware_source_implemented": True,
        "host_regression_status": software.get("host_regression_status", "NOT_RUN"),
        "host_tests_passed": software.get("passed", 0),
        "host_tests_skipped": len(software.get("skipped", [])),
        "firmware_flashed_and_hardware_qualified": False,
        "software_components": {name: {"source_present": (BASE / path).is_file(),
            "physical_qualification": False} for name, path in {
                "supervised_control": "software/srrx/engine.py",
                "rx_fft": "software/srrx/labrx.py",
                "touch_menu": "software/srrx/hmi.py",
                "gnss": "software/srrx/location.py",
                "spectrum_training": "software/srrx/learning.py",
                "onnx_export": "software/srrx/model_export.py",
                "physical_hmi": "firmware/pico/hmi.py",
                "deployment": "deployment/deploy.py"}.items()},
        "battery_adc_calibration_valid": False,
        "gate_results": {i["id"]: "OPEN" for i in blockers},
        "startup_output_requests": {n: (1 if n == "CHG_INHIBIT" else 0) for n in sorted(controls)},
        "control_contacts": controls,
        "rules": [
            "Це специфікація станів, не реалізований GPIO-драйвер і не доказ виконання їх прошивкою.",
            "До апаратного приймання усі bias enables заблоковані незалежно від логічного рівня непідключеного DC-sense.",
            "Підтягнутий HIGH від відсутнього датчика не є доказом безпечного DC.",
            "Preflight DC-free вимірюється лише при вимкненому власному bias; після увімкнення bias застосовуються визначені для нього струмові й напругові вікна.",
            "Pico GP17 через Q306 апаратно утримує спільний RESET трьох MCP при Pico boot/reset. Реалізована прошивка тримає RESET при heartbeat fault; release тільки після свіжого explicit ARM. Safe OLAT (CHG_INHIBIT=1, решта0) перед IODIR. Фізичний час і рівні не кваліфіковані; повна втрата живлення Pico не покривається цим FET.",
            "Штатний режим без чинної двоточкової калібровки батарейного ADC заборонений.",
            "При SJ1 на Adafruit INA228 VBUS вимірює VIN+ до шунта; V_N = VBUS - VSHUNT з правильним знаком струму.",
            "Стан реле K1=1,K2=1 заборонено. HMC A/B=00 вибирає RF1 PARK.",
            "Сервісна зарядка через ISDT/raw balance вимкнена до E1-02; main OFF і запобіжник не доводять ізоляцію B0/P−.",
        ],
    }
    (BASE / "design/readiness-contract.json").write_text(json.dumps(readiness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    errors = report.get("erc_errors", [])
    status = "без помилок" if not errors else plural(len(errors), "помилка", "помилки", "помилок") + "; див. сирий звіт і пояснення"
    erc = json.loads((BASE / "verification/erc.json").read_text(encoding="utf-8"))
    pcb = json.loads((BASE / "verification/pcb-review.json").read_text(encoding="utf-8"))
    host_failed = len(software.get("failures", [])) + len(software.get("errors", []))
    host_status = "" if software.get("host_regression_status") == "PASS" else f", **{software.get('host_regression_status', 'NOT_RUN')}: {host_failed} FAIL/ERROR**"

    def host_sources():
        from srrx.commissioning import project_hashes
        graphs, sources = project_hashes(BASE)
        return {**graphs, **sources}
    # Read after the readiness contract above is written: it is one of the bound graphs.
    host_note = evidence_note(current_for(software and {**software.get("graph_sha256", {}), **software.get("source_sha256", {})}, host_sources),
                              "звіт `verification/software-tests.json`")
    # Also after the contract write: the ARM64 binding covers design/readiness-contract.json (TOOL-07).
    if linux:
        host, suites = linux.get("host", {}), Counter(linux.get("suites", {}).values())
        guest_tests = (f" Регресії в guest: **{guest.get('passed', 0)} PASS**, **{len(guest.get('skipped', []))} SKIP** із {guest.get('tests_discovered', 0)}; "
                       "пропуски не зараховані як PASS.") if guest else ""
        linux_note = (f"Фактичний ARM64 Linux/systemd прогін: **{linux.get('status', 'NOT_RUN')}**, QEMU exit {host.get('qemu_exit_code', '?')}, {host.get('elapsed_s', '?')} s; "
                      + plural(sum(suites.values()), "набір", "набори", "наборів") + ": " + ", ".join(f"{n} {s}" for s, n in sorted(suites.items())) + "." + guest_tests
                      + lab_evidence(binding)
                      + " Окремий звіт і журнали: [Linux lab](verification/linux-lab/README.md).")
    else:
        linux_note = "ARM64 Linux lab підготовлено; фактичні результати потрібно читати в окремому звіті після запуску."
    pages = electrical_pages(report, generated)
    ignored = report.get("erc_ignored_checks", [])
    ignored_note = (" KiCad за замовчуванням не виконує перевірок " + ", ".join(f"`{name}`" for name in ignored)
                    + "; їх перелічено в `erc_ignored_checks`, тож «без помилок» стосується лише виконаних правил.") if ignored else ""
    drawings = sorted(p.name for p in (BASE / "build").glob("0[1-9]-*.svg"))
    placement = [name for name in drawings if name.startswith("05-roztashuvannia-")]
    completion = f"""# SR-RX-v2.1 — передача перевіреного інженерного комплекту

Редакція від 24.10.2026. Вихідний репозиторій: [lizbeth307/lizbeth307](https://github.com/lizbeth307/lizbeth307), основна опублікована гілка `ccr-1537979d-cj7q9t` (`git clone --branch ccr-1537979d-cj7q9t https://github.com/lizbeth307/lizbeth307.git`, [відновлення](RESTORE-GIT.md)). Гілки `codex/sr-rx-v2-completion` і `wip/review-fixes` злито в `ccr-1537979d-cj7q9t` і 24.10.2026 видалено з origin. Базовий коміт редакції — `465318835e71eae326059f5f66e2b47232169556` (основа гілки `ccr-1537979d-cj7q9t` до переписування її історії 23.10.2026). Коміти Codex — лише `05f0019`…`87e1e90`; пізнішу роботу виконано в сесії Claude: злиття часткових аркушів Claude `e95fec4` (E1/E2/E5, намальовані поза `design/E*.json`) без зміни дерева, тож збережено згенерований набір, що проходить ERC; далі Linux/KiCad CI, виправлення findings, пункти плану A–D і докази CI. Того ж дня хмарна сесія Claude переписала історію гілки `ccr-1537979d-cj7q9t` і додала читабельні схеми, STACK.md знову як джерело істини, вилучення R102/R503/R507/R511, ворота E5-10, вимкнення Wi-Fi/BT, маску Cospas-Sarsat і відтворюваний `run_checks.py`. Обидві лінії злито, узгоджений результат закомічено поверх `ccr-1537979d-cj7q9t`; CAD і PCB перегенеровано з об'єднаних джерел, а ARM64 Linux run для них пройшов 24.10.2026 (GitHub run 40043380590, **PASS**). Того ж дня внесено етап 2 і рішення власника v2.1 (номінали SYS12, LT3045, RILM і UVLO J21, захист ±30 V, політика baseband/IQ); ARM64 run цієї редакції — GitHub run 40099774142, **PASS**. Зведення ревізій 23–24.10.2026, CI і відкриті пункти — у [HANDOFF](HANDOFF.md).

## Що фактично передано від Claude

У Git були вимоги, STACK, інструкції, журнали аудиту, чернетки SVG і 36 бібліотечних символів. У базовому коміті всі E1–E5 були порожніми файлами по 210 байтів. Завантажений HTML побайтово збігався з файлом Git і не містив бібліотек. Повідомлення про процес креслення не означало, що його результат було збережено.

## Результат цієї редакції

- Заповнено всі п'ять розділів схеми. Для читабельності вони розбиті на {plural(pages, 'електричну сторінку', 'електричні сторінки', 'електричних сторінок')} і кореневий зміст.
- На схемах {plural(report['physical_components'], 'позначений елемент', 'позначені елементи', 'позначених елементів')}; {plural(report['connected_physical_contacts'], 'підключений фізичний/явно функціональний контакт', 'підключені фізичні/явно функціональні контакти', 'підключених фізичних/явно функціональних контактів')} у {plural(report['named_nets'], 'іменованій мережі', 'іменованих мережах', 'іменованих мережах')}. Повний експорт KiCad зіставлено з графами: **{report['graph_netlist_comparison']}**.
- Збережено початкові бібліотеки, додано самодостатню бібліотеку елементів нових схем, відносні таблиці бібліотек, підтверджені стандартні посадкові місця й джерела.
- ERC виконано справжнім KiCad {erc.get("kicad_version", "?")}: **{status}**. [Сирий ERC](verification/erc.json) не відфільтровано.{ignored_note} [Незалежна звірка](verification/validation.json) містить точні лічильники й SHA256 файлів.
- [PDF](build/kicad/sr-rx-v2.pdf), SVG, XML-netlist, [перелік елементів](build/11-schematic-bom.csv), [таблиці монтажу](design/E5-connection-guide.md) і відтворювані генератори входять у комплект.

## Матеріальні виправлення

Звірено нумерацію контактів Q6A J2/J5/J21 за схемою Radxa v1.21 (не виміряно), нумерацію Adafruit CH334F, повні pinouts мікросхем і NC, розподіл MCP, ізоляцію HDMI, драйвери реле та PARK, живлення IMU, допуски ILIM/OVLO, паралельні LT3045, фільтри живлення й запас струму LAB5. Проєктні призначення джгутів позначені як нові рішення; їх не видано за фабричну розпіновку невідомої плати.

Окремо усунено помилку двох паралельних навантажень HF+ у PARK. Для сервісної зарядки виявлено непідтверджений шлях B0/P−; цей режим заблоковано до підтвердження топології, а не оголошено захищеним.

## Межа завершення

Це інженерна схема та пакет перевірок. **Пристрій не зібрано, стендові результати відсутні, виробничий випуск заблоковано.** У реєстрі {plural(len(blockers), 'блокувальна умова', 'блокувальні умови', 'блокувальних умов')}, багато з яких стосуються одного приймального тесту або ревізії плати. Не можна перетворювати їх на PASS за результатом програмної перевірки.

Початковий `sr-rx-v2.kicad_pcb` є порожнім шаблоном. Gerber, виробнича PCB та підтверджені механічні файли виготовлення не заявлені. Наявні SVG-креслення v2 ({plural(len(drawings), 'файл', 'файли', 'файлів')}, з них {plural(len(placement), 'ескіз', 'ескізи', 'ескізів')} розміщення/механіки `05-roztashuvannia-*`) — теоретичні ескізи, які мають бути звірені з новими розмірами деталей. Додано [PCB-підготовку](build/13-pcb-preparation.md), нерозведений starter DC_CORE ({plural(pcb["components"], 'компонент', 'компоненти', 'компонентів')}/{plural(pcb["source_pins"], 'контакт', 'контакти', 'контактів')}, verification/pcb-review.json) та окремий [прототип внутрішнього розведення](build/kicad/pcb-prototype/README.md). Його точний raw DRC і незалежна звірка містяться у verification/pcb-prototype-review.json. Навіть нуль внутрішніх DRC findings не визначає зовнішні роз'єми, MPN, корпус або фізичну точність детектора.

Реалізовано [керування й меню](software/README.md), Pico Supervisor, RP2040-Zero/BNO085, UART/CRC, I²C-монітори, інтерлоки, калібрування, приймальні записи та systemd units. Додано [RX/FFT](software/RX.md), [GNSS](software/LOCATION.md), [читач GNSS UART і RESET](software/GNSS-UART.md), [спектральне навчання](software/LEARNING.md), [touch-консоль](software/HMI.md), [декодерні адаптери](software/DECODERS.md), [політики меж labd](software/SCOPE-POLICY.md) та [staging встановлення з офлайн-самоперевіркою](software/DEPLOYMENT.md). Хостові перевірки: **{software.get("passed", 0)} PASS**, **{len(software.get("skipped", []))} SKIP** із {software.get("tests_discovered", 0)}{host_status}; причини SKIP — у `verification/software-tests.json`, пропуски не зараховані як PASS.{host_note} Фізичне встановлення/прошивання не виконано. Сервіс перевіряється справжніми процесами; GUI — справжнім Qt. Обмеження Unix socket хоста відокремлено від перевірок у Linux guest.

## Перевірка без фізичної плати

Додано відтворюване [ARM64 Linux середовище](deployment/linux_lab/README.md), [моделі модулів](deployment/module_lab/README.md) і прив'язку запису до конкретного змонтованого диска через StorageGuard. {linux_note}

{module_note} Моделі з'єднань використовують незалежний експорт KiCad; навмисні обриви, замикання та підключення NC не є фізичними вимірюваннями. Реальні USB/PCIe/HDMI, RF, BMS, калібрування, тактування Q6A та фізичний T7 залишаються відкритими.

Повний C++ data plane 56 MS/s/Lime, весь початковий каталог декодерів, апаратний HTP/QAIRT та встановлений A/B образ не оголошено завершеними. Experimental vendor patches і вихідні генератори мають пройти native/API та стендове приймання; EGC/DSC вимкнені без перевірених pre-payload parsers. [readiness-contract.json](design/readiness-contract.json) фіксує межу; його дані самі не керують GPIO.

Ціни v2 від 18.10 залишено як історичну оцінку. Нові схеми мають окремий BOM-аудит; їх не названо підтвердженим кошторисом покупок.

## Як продовжити без втрати контексту

Редакцію отримують з опублікованої гілки `ccr-1537979d-cj7q9t` ([RESTORE-GIT](RESTORE-GIT.md)); хостову регресію, CAD і module lab на кожному push виконує CI workflow «SR-RX verification», а ARM64 Linux lab запускається вручну ([HANDOFF](HANDOFF.md)).

1. Відкрити `build/kicad/sr-rx-v2.kicad_pro` у KiCad 10; коренева схема індексує всі сторінки.
2. Прочитати [актуальні ворота](OPEN_ITEMS.md) та відповідні `design/E#-review.md` до купівлі, модифікації чи підключення заліза.
3. Звіряти монтаж за [E5 connection guide](design/E5-connection-guide.md), а вимоги безпеки — за [STACK](STACK.md) (джерело істини; поправки v2.1 зафіксовано на його початку).
4. Записувати фактичні результати приймання окремо з приладами, датою, умовами й ревізіями. Після зміни графа повторити генерацію, ERC і звірку netlist.

Жорсткі правила з USER_REQUIREMENTS збережено: лише прийом в ефірі, без приватного змісту/військових трактів, без рамок/тарілок, місце з GNSS. Схема передбачає термінування Lime TX; експериментальний source patch закриває перевірені високорівневі TX entry points. Повного native/raw-register аудиту та фізичного підтвердження немає, тому Lime runtime залишається заблокованим.
"""
    (BASE / "COMPLETION.md").write_text(completion, encoding="utf-8", newline="\n")
    print(f"Wrote component inventory, readiness contract and {len(blockers)} blocking gate records")


if __name__ == "__main__":
    main()
