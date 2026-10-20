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

Перевірки й пакування з каталогу `sat-receiver-audit`:

```bash
python3 tools/run_checks.py --export
python3 verification/independent_netlist_check.py
python3 tools/check_software.py
python3 pcb/prepare.py --check
python3 verification/independent_pcb_check.py
python3 tools/build_firmware.py
python3 tools/build_bundle.py
```

Потрібні KiCad 10 CLI, Python, Pandoc та залежності `tools/requirements.txt`. Для роботи зі схемами без генерації відкрийте `build/kicad/sr-rx-v2.kicad_pro`. Межа готовності й обов'язкові апаратні перевірки: [COMPLETION](COMPLETION.md) та [OPEN_ITEMS](OPEN_ITEMS.md). Патч містить вихідні прошивки Pico/IMU, керувальне ПЗ та нерозведений PCB starter; фізичного приймання й готової виробничої PCB немає. Запуск і обмеження ПЗ: [software/README.md](software/README.md).
