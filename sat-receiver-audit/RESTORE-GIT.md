# Відновлення Git-редакції SR-RX-v2.1

База: `lizbeth307/lizbeth307`, гілка `ccr-1537979d-cj7q9t`, коміт `465318835e71eae326059f5f66e2b47232169556`. Зміни підготовлено в окремій гілці `codex/sr-rx-v2-completion`. Запис через підключений GitHub повернув HTTP 403; успішного push цієї редакції не було.

Повний ZIP дає вихідні файли без Git-історії. Окремий `SR-RX-v2.1-git.patch.gz` зберігає локальні коміти і застосовується до зазначеної бази:

```bash
git clone --branch ccr-1537979d-cj7q9t https://github.com/lizbeth307/lizbeth307.git
cd lizbeth307
git switch -c codex/sr-rx-v2-completion
gzip -dc /шлях/до/SR-RX-v2.1-git.patch.gz | git am
```

Якщо гілка Claude вже просунулась, спочатку застосуйте патч до окремої гілки від точного базового коміту; не замінюйте нові чужі зміни файлами ZIP без порівняння. Push цієї редакції заблокований доступом підключеної інтеграції.

Окремі перевірки з каталогу `sat-receiver-audit`:

```bash
python3 tools/run_checks.py --export
python3 verification/independent_netlist_check.py
python3 tools/run_tests_offline.py
python3 pcb/prepare.py --check
python3 verification/independent_pcb_check.py
python3 tools/build_firmware.py
```

Для перепакування після зміни джерел обов'язковий повний цикл [Linux FINDINGS](deployment/linux_lab/FINDINGS.md): актуальний inventory/source snapshots, host regression, новий Linux/module run і finalizer, документи/firmware, `python3 tools/build_bundle.py` та `python3 tools/check_bundle.py`. Старі Linux reports/source binding не підтверджують змінених джерел.

Потрібні KiCad 10 CLI, Python, Pandoc та залежності `tools/requirements.txt`. Для роботи зі схемами без генерації відкрийте `build/kicad/sr-rx-v2.kicad_pro`. Межа готовності й обов'язкові апаратні перевірки: [COMPLETION](COMPLETION.md) та [OPEN_ITEMS](OPEN_ITEMS.md). Патч містить вихідні прошивки Pico/IMU, керувальне ПЗ, моделі модулів, Linux launcher, нерозведений PCB starter і внутрішній розведений прототип; фізичного приймання й готової виробничої PCB немає. Запуск і обмеження ПЗ: [software/README.md](software/README.md).
