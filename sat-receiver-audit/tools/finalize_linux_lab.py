#!/usr/bin/env python3
"""Import a stopped, successful guest's reports and bind its executed sources."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
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
BOUND_SUFFIXES = {".py", ".sh", ".service", ".json", ".toml", ".patch", ".c", ".h", ".cpp", ".hpp", ".cmake", ".in"}
# Build recipes (debian/ files have no suffix), the lab repository layout and native sources; the
# system files the guest tests hash, read or run (DT overlays, DKMS tree, EDID, image initramfs and
# kernel-install scripts) and the software configuration examples and locks.
BOUND_TREES = ("deployment/upstream-fixtures/", "deployment/patches/", "deployment/recipes/", "deployment/repo/",
               "software/labrx-native/", "deployment/system/", "deployment/image/files/", "software/config/")
BOUND_NAMES = {"CMakeLists.txt"}
# The guest compares the readiness contract's gate_results with the staged template (guest_smoke.py).
# It is a sink of host evidence (test counts); never bind verification/software-tests.json itself.
# firmware/mpremote-requirements.txt: the mpremote pin test_flash_mcu.py checks; the wheel lock the
# guest bootstrap installs from and compares with its payload (guest_bootstrap.sh).
BOUND_EXTRA = {"tools/check_software.py", "tools/run_tests_offline.py", "design/readiness-contract.json",
               "firmware/mpremote-requirements.txt", "deployment/linux_lab/wheelhouse-requirements.txt"}
CONTRACT = "design/readiness-contract.json"
UNBOUND = ("deployment/linux_lab/build_kit.py", "firmware/dist/")
ATTEMPTS = "verification/linux-attempts"
# GitHub run ids of imports archived before finalize wrote github-run.json next to each import. Both are
# named by commit 51f8a4c on origin/wip/stage3-int ("GENERATED: ARM64 QEMU Linux lab run 42355259865
# evidence": the lab patch of run 42355259865, which archived the previous import, run 40099774142, as
# run10); run10 itself was imported by be8fd84 ("Stage 2 evidence: ARM64 lab PASS (CI run 40099774142)").
KNOWN_RUN_IDS = {"run10": "40099774142", "run11": "42355259865"}
RUN_DIR = re.compile(r"run(\d+)")
# An archived README's module links: '../module-lab/<file>' was right next to verification/module-lab,
# the archive keeps that tree in runNN/module-lab. A bare '`../module-lab/`' mention is prose, not a link.
MODULE_LINK = re.compile(r"(\]\(|`)\.\./module-lab/(?=[^\s)`])")
INTRO = re.compile(r"Ці запуски не підтверджують поточну редакцію: [^.\n]*\.")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def bound(relative):
    if relative.startswith(UNBOUND) or any(p in {"__pycache__", ".git", "tmp", "qa"} for p in relative.split("/")):
        return False
    return (relative in BOUND_EXTRA or relative.startswith(BOUND_TREES)
            or (relative.startswith(BOUND_PREFIXES) and (PurePosixPath(relative).suffix in BOUND_SUFFIXES
                                                         or PurePosixPath(relative).name in BOUND_NAMES)))


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


def importable(report):
    """Only a successful stopped ARM64 simulation whose QEMU mapped nothing outside its locked tools."""
    if (report.get("status") != "PASS" or report["host"]["qemu_exit_code"] != 0
            or report["environment"]["architecture"] != "aarch64"
            or report["hardware_qualified"] is not False or report["physical_tests_performed"] is not False):
        raise SystemExit("Only a successful stopped ARM64 simulation run may be imported")
    audit = report["host"].get("loader_audit")
    if (type(audit) is not dict or audit.get("status") != "PASS" or audit.get("outside_tools_root") != []
            or type(audit.get("objects")) is not int or audit["objects"] < 1 or type(audit.get("dlopened")) is not list):
        raise SystemExit("QEMU loader audit is missing, vacuous or saw objects outside the locked tools root")
    return report


def bind_executed(entries, project):
    """Bound files of the guest's project manifest: each still has the executed bytes, none was added."""
    executed = {}
    for entry in entries:
        relative = entry["path"]
        if bound(relative):
            path = project / relative
            if not path.is_file() or path.is_symlink() or sha(path) != entry["sha256"]:
                raise SystemExit("Executed source changed after guest preparation: " + relative)
            executed[relative] = entry["sha256"]
    if len(executed) < 50:
        raise SystemExit("Incomplete executed-source manifest")
    added = sorted(bound_sources(project) - set(executed))
    if added:
        raise SystemExit("Source added after guest preparation: " + ", ".join(added[:12]))
    return executed


def smoke_attests(smoke_sha256, executed):
    """system-smoke.json records what the guest read: the contract and every bound file in that record
    must carry the executed bytes. Unbound inputs it also records (design/E3.json) are not judged."""
    if type(smoke_sha256) is not dict or CONTRACT not in smoke_sha256:
        raise SystemExit("Guest smoke did not record the bound readiness contract: " + CONTRACT)
    wrong = sorted(name for name, value in smoke_sha256.items() if bound(name) and executed.get(name) != value)
    if wrong:
        raise SystemExit("Guest smoke did not read the bound sources: " + ", ".join(wrong[:12]))
    return smoke_sha256


def lineage_text(base):
    """README sentence for run.json's base_overlay: OS cache lineage only, never a clean-image claim."""
    if base is None:
        return "Прогін почато з незмінного locked Ubuntu image без OS cache (`base_overlay: null` у `run.json`)."
    chain = base["backing_chain"]
    return (f"`run.json` записує походження OS cache: попередній прогін `previous_status` {base['previous_status']}, "
            f"`previous_qemu_exit_code` {base['previous_qemu_exit_code']} і `backing_chain` із SHA256 кожного з {plural(len(chain), 'шару', 'шарів', 'шарів')}; "
            "нижній шар — locked Ubuntu image. Журнал файлової системи відновлює саме Linux guest. Це не прогін із чистого базового образу.")


def console_filtered(report, console):
    """The imported console.log is the file host.py filtered for addresses and then hashed."""
    record = report["host"].get("console_redactions")
    if type(record) is not dict or type(record.get("count")) is not int or record["count"] < 0:
        raise SystemExit("console.log was not filtered for addresses before hashing (host.py run)")
    if sha(console) != report["host"].get("console_sha256"):
        raise SystemExit("console.log differs from the console_sha256 the host recorded")
    return record


def github_run(destination, environ):
    """github-run.json names the workflow run that imported this result, so its archive can cite it.
    Written only inside GitHub Actions (GITHUB_RUN_ID and GITHUB_SHA set); a local import writes none."""
    run_id, commit = environ.get("GITHUB_RUN_ID"), environ.get("GITHUB_SHA")
    if not run_id or not commit:
        return None
    if not re.fullmatch(r"[0-9]+", run_id) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("Malformed GITHUB_RUN_ID or GITHUB_SHA")
    record = {"schema_version": 1, "run_id": run_id, "sha": commit,
              "source": "GITHUB_RUN_ID and GITHUB_SHA of the workflow run that imported this ARM64 lab result"}
    (destination / "github-run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    return record


def archive_links(attempts):
    """In each archived runNN/README.md whose runNN/module-lab exists, point '../module-lab/' links at
    'module-lab/'. Nothing else changes; a second pass finds nothing to rewrite."""
    changed = []
    for readme in sorted(attempts.glob("run*/README.md")):
        if not RUN_DIR.fullmatch(readme.parent.name) or not (readme.parent / "module-lab").is_dir():
            continue
        text = readme.read_bytes().decode("utf-8")
        fixed = MODULE_LINK.sub(r"\1module-lab/", text)
        if fixed != text:
            readme.write_bytes(fixed.encode("utf-8"))
            changed.append(readme.parent.name)
    return changed


def run_dirs(attempts):
    return sorted((d for d in attempts.iterdir() if d.is_dir() and RUN_DIR.fullmatch(d.name)),
                  key=lambda d: int(RUN_DIR.fullmatch(d.name).group(1)))


def run_status(run):
    for name in ("report.json", "attempt.json"):
        if (run / name).is_file():
            return read(run / name).get("status")
    return None


def run_bullet(run):
    """Index bullet of an archived import, from its own records; statuses are copied, never rewritten."""
    report = read(run / "report.json") if (run / "report.json").is_file() else {}
    host = report.get("host", {})
    record = read(run / "github-run.json") if (run / "github-run.json").is_file() else {}
    run_id = record.get("run_id") or KNOWN_RUN_IDS.get(run.name)
    facts = ["GitHub run " + run_id if run_id else "GitHub run не записано"]
    smoke = run / "system-smoke.json"
    started = read(smoke).get("started_at", "") if smoke.is_file() else ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T.*", started):
        facts[0] += ", " + ".".join(reversed(started[:10].split("-")))
    if "qemu_exit_code" in host and "elapsed_s" in host:
        facts.append(f"QEMU exit {host['qemu_exit_code']}, {host['elapsed_s']} s")
    status = run_status(run) or "без report.json"
    moved = "разом із `module-lab/` " if (run / "module-lab").is_dir() else ""
    return (f"- {run.name}: **{status}** ({'; '.join(facts)}). Пункт записав `tools/finalize_linux_lab.py` під час "
            f"наступного імпорту: первинні результати {moved}перенесено сюди без переписування статусів; цей результат "
            "стосується тодішніх джерел і не переноситься на поточне дерево, чинний прогін — у ../linux-lab/.")


def run_ranges(names):
    numbers = sorted(int(RUN_DIR.fullmatch(n).group(1)) for n in names)
    groups = []
    for number in numbers:
        if groups and number == groups[-1][-1] + 1:
            groups[-1].append(number)
        else:
            groups.append([number])
    width = max(len(RUN_DIR.fullmatch(n).group(1)) for n in names)
    def name(number):
        return f"run{number:0{width}d}"
    # Three or more consecutive runs read as a range (run03–run06); shorter runs are listed one by one.
    parts = [p for g in groups for p in ([name(g[0]) + "–" + name(g[-1])] if len(g) > 2 else [name(n) for n in g])]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " і " + parts[-1]


def attempt_index(attempts):
    """README of the archive: one bullet per runNN (missing ones appended after the last bullet, existing
    ones kept verbatim) and the intro status sentence regenerated from the runs' recorded statuses."""
    readme = attempts / "README.md"
    lines = readme.read_bytes().decode("utf-8").split("\n")
    runs = run_dirs(attempts)
    listed = {m.group(1) for m in (re.match(r"- (run\d+):", line) for line in lines) if m}
    added = [run.name for run in runs if run.name not in listed]
    bullets = [i for i, line in enumerate(lines) if re.match(r"- run\d+:", line)]
    at = bullets[-1] + 1 if bullets else len(lines)
    for run in reversed([r for r in runs if r.name in added]):
        lines[at:at] = ["", run_bullet(run)]
    statuses = {run.name: run_status(run) for run in runs}
    passed = [n for n, s in statuses.items() if s == "PASS"]
    failed = [n for n, s in statuses.items() if s != "PASS"]
    kinds = "/".join(dict.fromkeys(statuses[n] or "без звіту" for n in failed))
    said = ([f"{run_ranges(failed)} завершились {kinds}"] if failed else []) + \
           ([f"{run_ranges(passed)} пройшли для попередніх джерел"] if passed else [])
    sentence = "Ці запуски не підтверджують поточну редакцію: " + ", ".join(said) + "."
    text = "\n".join(lines)
    if said and INTRO.search(text):
        text = INTRO.sub(lambda _: sentence, text, count=1)
    readme.write_bytes(text.encode("utf-8"))
    return {"added": added, "intro": sentence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve(strict=True)
    report = importable(read(work / "report.json"))
    redactions = console_filtered(report, work / "console.log")
    # debugfs rdump recreates guest symlinks on the host; never follow one.
    regular_tree(work / "results")
    executed = bind_executed(read(work / "results/project-manifest.json"), PROJECT)
    # The guest smoke records what it read: the bound contract bytes must be the ones it compared.
    smoke_attests(read(work / "results/system-smoke.json").get("source_sha256"), executed)
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
    for name in ("report.json", "run.json", "console.log", "debugfs.log", "qemu-loaded-objects.json"):
        shutil.copyfile(work / name, destination / name)
    regular_tree(destination)
    regular_tree(modules)
    binding = {"schema_version": 1, "source_sha256": executed,
               "guest_source_manifest_sha256": sha(work / "results/project-manifest.json"),
               "module_report_sha256": sha(modules / "report.json"),
               "linux_report_sha256": sha(destination / "report.json"),
               "scope": "Exact code, locks, patches, upstream fixtures and the readiness contract read by this executed guest payload, plus its test runner; no physical qualification"}
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

Аудит завантажувача QEMU на хості (`qemu-loaded-objects.json`, locked ld.so з `LD_DEBUG=files,libs`): відображених об'єктів — {report['host']['loader_audit']['objects']}, через dlopen — {len(report['host']['loader_audit']['dlopened'])}, поза locked tools root — 0. Модулі QEMU і їхні бібліотеки додатково перевірено статично (`run.json`, `qemu_runtime`).

{origin} Усі locked DEB і wheels перевстановлено з hash-перевіреного payload, а `dependency-verification.json` підтверджує, що встановлені версії точно збігаються з обома lock. Усі поточні вихідні файли замінено й перевірено за SHA256, пакет перевстановлено, усі набори виконано повторно. `source-binding.json` і `project-manifest.json` дозволяють звірити реально виконаний код. Годинник задається з host preparation timestamp; це не GNSS/PPS/RTC qualification.

Апаратні ворота, що лишаються OPEN: {len(read(PROJECT / 'design/readiness-contract.json')['gate_results'])}. Фізичне залізо, аналогові RF/живлення, BMS, калібрування, Q6A peripheral pinmux, повний Lime/56MS/s/HTP та виробничий випуск не прийняті.
"""
    (destination / "README.md").write_text(text, encoding="utf-8", newline="\n")
    github = github_run(destination, os.environ)
    # The workflow has just moved the previous import into the archive: fix its links, index every run.
    attempts = PROJECT / ATTEMPTS
    links = archive_links(attempts)
    index = attempt_index(attempts)
    print(json.dumps({"status": "IMPORTED", "bound_sources": len(executed), "linux": str(destination), "modules": str(modules),
                      "console_redactions": redactions["count"], "github_run": github and github["run_id"],
                      "archive_links_rewritten": links, "archive_bullets_added": index["added"]}))


if __name__ == "__main__":
    main()
