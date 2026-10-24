#!/usr/bin/env python3
"""Import a stopped, successful guest's reports and bind its executed sources."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
# Shared wording; appended, so a module loaded by file path cannot shadow anything else.
if str(PROJECT / "tools") not in sys.path:
    sys.path.append(str(PROJECT / "tools"))
from uk_text import plural  # noqa: E402
# Everything the guest executes or consumes as test input: service/deploy code,
# locks, patches and byte-exact upstream fixtures, plus the guest test runner.
BOUND_PREFIXES = ("software/", "firmware/", "deployment/")
BOUND_SUFFIXES = {".py", ".sh", ".service", ".json", ".toml", ".patch"}
BOUND_TREES = ("deployment/upstream-fixtures/", "deployment/patches/")
BOUND_EXTRA = {"tools/check_software.py", "tools/run_tests_offline.py"}
UNBOUND = ("deployment/linux_lab/build_kit.py", "firmware/dist/")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def bound(relative):
    if relative.startswith(UNBOUND) or any(p in {"__pycache__", ".git", "tmp", "qa"} for p in relative.split("/")):
        return False
    return (relative in BOUND_EXTRA or relative.startswith(BOUND_TREES)
            or (relative.startswith(BOUND_PREFIXES) and PurePosixPath(relative).suffix in BOUND_SUFFIXES))


def bound_sources(project):
    """Current in-scope project files; build_bundle requires all of them bound."""
    return {p.relative_to(project).as_posix() for p in project.rglob("*")
            if p.is_file() and not p.is_symlink() and bound(p.relative_to(project).as_posix())}


def binding_drift(project, binding):
    """How the tree moved from an imported run's source-binding.json: bound files changed
    or missing, in-scope files it does not cover, and whether the module report was
    replaced. build_bundle and build_documents both count stale records with this."""
    recorded = binding["source_sha256"]
    missing = sorted(r for r in recorded if not (project / r).is_file())
    changed = sorted(r for r, h in recorded.items() if r not in missing and sha(project / r) != h)
    report = project / "verification/module-lab/report.json"
    return {"bound": len(recorded), "changed": changed, "missing": missing,
            "added": sorted(bound_sources(project) - set(recorded)),
            "module_rebound": not report.is_file() or sha(report) != binding.get("module_report_sha256")}


def regular_tree(root):
    """Guest-written results: reject links/special files before anything is read or copied.

    debugfs rdump re-applies guest modes; an unlistable directory fails closed
    instead of being skipped by os.walk, and the root itself is lstat'ed first."""
    def unreadable(error):
        raise SystemExit("Unreadable guest results: " + str(error))
    def regular(path):
        mode = os.lstat(path).st_mode
        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise SystemExit("Guest results contain a symlink or special file: " + str(path))
    regular(root)
    for directory, dirs, files in os.walk(root, onerror=unreadable):
        for name in dirs + files:
            regular(os.path.join(directory, name))


def lineage_text(base):
    """README sentence for run.json's base_overlay: OS cache lineage only, never a clean-image claim."""
    if base is None:
        return "Прогін почато з незмінного locked Ubuntu image без OS cache (`base_overlay: null` у `run.json`)."
    chain = base["backing_chain"]
    return (f"`run.json` записує походження OS cache: попередній прогін `previous_status` {base['previous_status']}, "
            f"`previous_qemu_exit_code` {base['previous_qemu_exit_code']} і `backing_chain` із SHA256 кожного з {plural(len(chain), 'шару', 'шарів', 'шарів')}; "
            "нижній шар — locked Ubuntu image. Журнал файлової системи відновлює саме Linux guest. Це не прогін із чистого базового образу.")


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
    # debugfs rdump recreates guest symlinks on the host; never follow one.
    regular_tree(work / "results")
    entries = read(work / "results/project-manifest.json")
    executed = {}
    for entry in entries:
        relative = entry["path"]
        if bound(relative):
            path = PROJECT / relative
            if not path.is_file() or path.is_symlink() or sha(path) != entry["sha256"]:
                raise SystemExit("Executed source changed after guest preparation: " + relative)
            executed[relative] = entry["sha256"]
    if len(executed) < 50:
        raise SystemExit("Incomplete executed-source manifest")
    added = sorted(bound_sources(PROJECT) - set(executed))
    if added:
        raise SystemExit("Source added after guest preparation: " + ", ".join(added[:12]))
    module_report = read(work / "results/module-lab/report.json")
    if module_report["execution_status"] != "PASS" or module_report["environment"]["architecture"] != "aarch64":
        raise SystemExit("Missing successful ARM64 per-module execution")
    # The README states that locked dependencies were reinstalled; require the guest's own proof.
    dependencies = read(work / "results/dependency-verification.json")
    if dependencies.get("status") != "PASS" or dependencies.get("cached_dependency_state_trusted") is not False:
        raise SystemExit("Missing locked dependency reinstall verification")
    lineage = read(work / "run.json").get("base_overlay")
    locked = {x["name"]: x["sha256"] for x in read(PROJECT / "deployment/linux_lab/assets.lock.json")["ubuntu_assets"]}
    if lineage is not None and lineage["backing_chain"][-1]["sha256"] != locked["ubuntu-24.04-server-cloudimg-arm64.img"]:
        raise SystemExit("OS cache lineage does not end at the locked Ubuntu image")
    # Publish no guest-authored page/script: it must equal the bound renderer's output.
    spec = importlib.util.spec_from_file_location("srrx_module_lab_run", PROJECT / "deployment/module_lab/run.py")
    lab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lab)
    with tempfile.TemporaryDirectory(prefix="srrx-module-render-") as tmp:
        lab.render(module_report, Path(tmp))
        for name in ("module-results.html", "MODULE-RESULTS.md"):
            if (Path(tmp) / name).read_bytes() != (work / "results/module-lab" / name).read_bytes():
                raise SystemExit("Guest module page differs from the host render of its report: " + name)
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
        shutil.copyfile(path, target, follow_symlinks=False)
    shutil.copytree(work / "results/module-lab", modules, symlinks=True)
    for name in ("report.json", "run.json", "console.log", "debugfs.log"):
        shutil.copyfile(work / name, destination / name)
    regular_tree(destination)
    regular_tree(modules)
    binding = {"schema_version": 1, "source_sha256": executed,
               "guest_source_manifest_sha256": sha(work / "results/project-manifest.json"),
               "module_report_sha256": sha(modules / "report.json"),
               "linux_report_sha256": sha(destination / "report.json"),
               "scope": "Exact code, locks, patches and upstream fixtures present in this executed guest payload, plus its test runner; no physical qualification"}
    (destination / "source-binding.json").write_text(json.dumps(binding, indent=2) + "\n", encoding="utf-8", newline="\n")
    units = read(destination / "software-tests.json")
    storage = read(destination / "storage-smoke.json")
    connect = module_report["domains"]["connectivity"]["report"]
    origin = lineage_text(lineage)
    text = f"""# ARM64 Linux — фактичний результат

Загальний стан **{report['status']}**. Справжній ARM64 Linux `{report['environment']['kernel']}`, systemd як PID1, QEMU TCG/Cortex-A76, 4 vCPU/3 GiB. Мережевих карт, USB passthrough та спільних каталогів хоста немає; loopback використовується локальними GPSD fixtures. ОС Ubuntu 24.04 з generic kernel, а не цільовий Q6A образ/ядро.

| Набір | Фактичний стан |
|---|---|
"""
    text += "\n".join(f"| `{name}` | {status} |" for name, status in report["suites"].items())
    text += f"""

Регресії: **{units['passed']} PASS**, **{len(units['skipped'])} SKIP** із {plural(units['tests_discovered'], 'тесту', 'тестів', 'тестів')}. Причини пропусків наведені в `software-tests.json`; пропуски не зараховані як PASS. System smoke перевіряє справжні systemd sandbox/restart/peer UID і відмову запускати hardware service з OPEN/missing records. PTY, Qt offscreen, XCB/Xvfb і native RX worker lifecycle виконуються реальними процесами.

Storage smoke: **{len(storage['cases'])} PASS** на окремому віртуальному ext4 block device. Перевірено запис маскованого спектра, неправильний пристрій, підміну mount ID, ENOSPC і втрату mount без запису на rootfs. Це не Samsung T7/USB або перевірка фізичного відключення живлення.

[Таблиця модулів](../module-lab/MODULE-RESULTS.md) та автономний `../module-lab/module-results.html` відокремлюють програмні драйвери від моделі з'єднань. Повний `../module-lab/report.json` зберігає всі сценарії та обмеження. Модель з'єднань: `{connect['status']}`; її точні лічильники — в `../module-lab/connectivity.json`.

{origin} Усі locked DEB і wheels перевстановлено з hash-перевіреного payload, а `dependency-verification.json` підтверджує, що встановлені версії точно збігаються з обома lock. Усі поточні вихідні файли замінено й перевірено за SHA256, пакет перевстановлено, усі набори виконано повторно. `source-binding.json` і `project-manifest.json` дозволяють звірити реально виконаний код. Годинник задається з host preparation timestamp; це не GNSS/PPS/RTC qualification.

Апаратні ворота, що лишаються OPEN: {len(read(PROJECT / 'design/readiness-contract.json')['gate_results'])}. Фізичне залізо, аналогові RF/живлення, BMS, калібрування, Q6A peripheral pinmux, повний Lime/56MS/s/HTP та виробничий випуск не прийняті.
"""
    (destination / "README.md").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "IMPORTED", "bound_sources": len(executed), "linux": str(destination), "modules": str(modules)}))


if __name__ == "__main__":
    main()
