#!/usr/bin/env python3
"""Import a stopped, successful guest's reports and bind its executed sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

PROJECT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve(strict=True)
    report = read(work / "report.json")
    if (report.get("status") != "PASS" or report["host"]["qemu_exit_code"] != 0
            or report["environment"]["architecture"] != "aarch64"
            or report["hardware_qualified"] is not False or report["physical_tests_performed"] is not False):
        raise SystemExit("Only a successful stopped ARM64 simulation run may be imported")
    entries = read(work / "results/project-manifest.json")
    executed = {}
    prefixes = ("software/", "firmware/", "deployment/linux_lab/", "deployment/module_lab/")
    for entry in entries:
        relative = entry["path"]
        if (relative.startswith(prefixes) and Path(relative).suffix in {".py", ".sh", ".service"}
                and relative != "deployment/linux_lab/build_kit.py"):
            path = PROJECT / relative
            if not path.is_file() or sha(path) != entry["sha256"]:
                raise SystemExit("Executed source changed after guest preparation: " + relative)
            executed[relative] = entry["sha256"]
    if len(executed) < 50:
        raise SystemExit("Incomplete executed-source manifest")
    module_report = read(work / "results/module-lab/report.json")
    if module_report["execution_status"] != "PASS" or module_report["environment"]["architecture"] != "aarch64":
        raise SystemExit("Missing successful ARM64 per-module execution")
    destination = PROJECT / "verification/linux-lab"
    modules = PROJECT / "verification/module-lab"
    if destination.exists() or modules.exists():
        raise SystemExit("Import only into new verification directories; archive an earlier run first")
    destination.mkdir()
    for path in sorted((work / "results").rglob("*")):
        relative = path.relative_to(work / "results")
        if not path.is_file() or relative.parts[0] in {"lost+found", "module-lab"}:
            continue
        if path.suffix not in {".json", ".txt", ".log", ".png"}:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    shutil.copytree(work / "results/module-lab", modules)
    for name in ("report.json", "run.json", "console.log", "debugfs.log"):
        shutil.copyfile(work / name, destination / name)
    binding = {"schema_version": 1, "source_sha256": executed,
               "guest_source_manifest_sha256": sha(work / "results/project-manifest.json"),
               "module_report_sha256": sha(modules / "report.json"),
               "linux_report_sha256": sha(destination / "report.json"),
               "scope": "Exact Python, shell and service files present in this executed guest payload; no physical qualification"}
    (destination / "source-binding.json").write_text(json.dumps(binding, indent=2) + "\n")
    units = read(destination / "software-tests.json")
    storage = read(destination / "storage-smoke.json")
    connect = module_report["domains"]["connectivity"]["report"]
    text = f"""# ARM64 Linux — фактичний результат

Загальний стан **{report['status']}**. Справжній ARM64 Linux `{report['environment']['kernel']}`, systemd як PID1, QEMU TCG/Cortex-A76, 4 vCPU/3 GiB. Мережевих карт, USB passthrough та спільних каталогів хоста немає; loopback використовується локальними GPSD fixtures. ОС Ubuntu24.04 з generic kernel, а не цільовий Q6A образ/ядро.

| Набір | Фактичний стан |
|---|---|
"""
    text += "\n".join(f"| `{name}` | {status} |" for name, status in report["suites"].items())
    text += f"""

Регресії: **{units['passed']} PASS**, **{len(units['skipped'])} SKIP** із {units['tests_discovered']} тестів. Причини пропусків наведені в `software-tests.json`; пропуски не зараховані як PASS. System smoke перевіряє справжні systemd sandbox/restart/peer UID і відмову запускати hardware service з OPEN/missing records. PTY, Qt offscreen, XCB/Xvfb і native RX worker lifecycle виконуються реальними процесами.

Storage smoke: **{len(storage['cases'])} PASS** на окремому віртуальному ext4 block device. Перевірено запис маскованого спектра, неправильний пристрій, підміну mount ID, ENOSPC і втрату mount без запису на rootfs. Це не Samsung T7/USB або перевірка фізичного відключення живлення.

[Таблиця модулів](../module-lab/MODULE-RESULTS.md) та автономний `../module-lab/module-results.html` відокремлюють програмні драйвери від моделі з'єднань. Повний `../module-lab/report.json` зберігає всі сценарії та обмеження. Модель з'єднань: `{connect['status']}`; її точні лічильники — в `../module-lab/connectivity.json`.

`run.json` записує походження OS/dependency cache, зокрема попередній перерваний прогін, якщо використано кеш. Журнал файлової системи відновлює саме Linux guest; усі поточні вихідні файли замінено, перевірено SHA256, пакет перевстановлено, усі набори виконано повторно. Це не прогін із чистого базового образу. `source-binding.json` і `project-manifest.json` дозволяють звірити реально виконаний код. Годинник задається з host preparation timestamp; це не GNSS/PPS/RTC qualification.

{len(read(PROJECT / 'design/readiness-contract.json')['gate_results'])} апаратних воріт залишаються OPEN. Фізичне залізо, аналогові RF/живлення, BMS, калібрування, Q6A peripheral pinmux, повний Lime/56MS/s/HTP та виробничий випуск не прийняті.
"""
    (destination / "README.md").write_text(text)
    print(json.dumps({"status": "IMPORTED", "bound_sources": len(executed), "linux": str(destination), "modules": str(modules)}))


if __name__ == "__main__":
    main()
