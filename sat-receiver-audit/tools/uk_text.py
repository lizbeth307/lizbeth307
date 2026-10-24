"""Ukrainian wording shared by the document generators in tools/ (not bound to any run).

deployment/module_lab/run.py keeps its own copy of plural(): the module report's
model_sha256 hashes only deployment/module_lab/*.py, and importing this file would let
the rendered module results depend on a file that hash does not cover.
"""


def plural(n, one, few, many):
    """'n noun' in the Ukrainian form: 1/21 one, 2-4/22-24 few, 0/5-20/11-14 many; a non-integer takes many.

    After a preposition that governs the genitive ("із", "з") pass the genitive forms,
    e.g. plural(n, "тесту", "тестів", "тестів")."""
    tail, tens = (n % 10, n % 100) if type(n) is int else (0, 0)
    return f"{n} {one if tail == 1 and tens != 11 else few if 2 <= tail <= 4 and not 12 <= tens <= 14 else many}"


def drift_sentence(drift):
    """How far the tree moved from an imported ARM64 run (finalize_linux_lab.binding_drift).

    COMPLETION.md and the bundle notice print exactly this sentence; "" when nothing moved."""
    if not (drift["changed"] or drift["missing"] or drift["added"] or drift["module_rebound"]):
        return ""
    text = (f"з {plural(drift['bound'], 'прив’язаного виконуваного файлу', 'прив’язаних виконуваних файлів', 'прив’язаних виконуваних файлів')} "
            f"змінено {len(drift['changed'])}, вилучено {len(drift['missing'])}; "
            f"додано {plural(len(drift['added']), 'новий файл', 'нові файли', 'нових файлів')}")
    return text + ("; звіт модулів замінено після прив’язки" if drift["module_rebound"] else "")
