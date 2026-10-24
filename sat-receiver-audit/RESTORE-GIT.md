# Відновлення Git-редакції SR-RX-v2.1

Репозиторій: `lizbeth307/lizbeth307`. Основна опублікована гілка редакції — `ccr-1537979d-cj7q9t`. Підсумкове дерево ревізії 23.10.2026 (злиття обох ліній роботи та узгодження) закомічено поверх `37c629e`, вершини цієї гілки після хмарної сесії Claude. Hash нової вершини тут не фіксується; його показує `git log`.

Гілки `codex/sr-rx-v2-completion` і `wip/review-fixes` злито в `ccr-1537979d-cj7q9t` і 24.10.2026 видалено з origin, тож їхні оригінальні hash (наприклад `87e1e90`, `20e4f06`) можуть бути недоступні в origin; копії ранніх комітів є в переписаній історії під іншими hash (див. «Історія»).

Новий checkout:

```bash
git clone --branch ccr-1537979d-cj7q9t https://github.com/lizbeth307/lizbeth307.git
cd lizbeth307/sat-receiver-audit
```

Наявний клон:

```bash
git fetch origin ccr-1537979d-cj7q9t
git switch ccr-1537979d-cj7q9t
git merge --ff-only origin/ccr-1537979d-cj7q9t
```

Якщо локальна `ccr-1537979d-cj7q9t` ще має історію до переписування 23.10.2026, `--ff-only` відмовить. Тоді спершу збережіть власні локальні коміти в окремій гілці, а потім виконайте `git switch -C ccr-1537979d-cj7q9t origin/ccr-1537979d-cj7q9t`. Клон, у якому лишилася `codex/sr-rx-v2-completion`, переходить на `ccr-1537979d-cj7q9t` тими самими командами; стару гілку видаляють, коли в ній немає власних неопублікованих комітів.

## Історія

- Базовий коміт редакції — `465318835e71eae326059f5f66e2b47232169556` (основа гілки `ccr-1537979d-cj7q9t` до переписування її історії 23.10.2026); у переписаній історії йому відповідає `4ffcc1d`. Спільний предок старої й переписаної історії — лише `master`.
- Коміти Codex — лише `05f0019`…`87e1e90` (у переписаній історії — `b19ad4f`…`0e2ed98`).
- Усю пізнішу роботу виконано в сесії Claude: злиття часткових аркушів Claude `e95fec4` (E1/E2/E5, намальовані поза `design/E*.json`) merge-комітом `20e4f06` без зміни дерева (у переписаній історії — `9063cfa` і `c0a57d7`), Linux/KiCad CI, виправлення findings, пункти плану A–D і докази CI. У переписаній історії коміти від `c0a57d7` до `ad623a2` мають у метаданих автора «Codex».
- 23.10.2026 хмарна сесія Claude переписала історію `ccr-1537979d-cj7q9t` (вилучила старі версії великого HTML і `handoff/handoff-bundle.zip` з проміжних комітів) і додала власні зміни: читабельні схеми, STACK.md знову як джерело істини, вилучення R102/R503/R507/R511, ворота E5-10, вимкнення Wi-Fi/BT, маску Cospas-Sarsat і відтворюваний `run_checks.py`.
- Обидві лінії злито триточковим злиттям із явною базою (копія коміту «deterministic pin order» у переписаній історії), узгоджено й закомічено поверх `37c629e`. Пізніші коміти інших гілок не входять у редакцію без нового злиття. Не замінюйте чужі нові зміни файлами ZIP або patch без порівняння.

## Офлайн-перенос

Повний ZIP дає вихідні файли без Git-історії; ZIP, patch, vendor-sources і offline kit — необов'язкові зовнішні файли, яких у репозиторії немає. Для офлайн-переносу історії використовуйте bundle, а не `git format-patch`:

```bash
git bundle create /tmp/SR-RX-v2.1.bundle ccr-1537979d-cj7q9t
git bundle verify /tmp/SR-RX-v2.1.bundle
git clone --branch ccr-1537979d-cj7q9t /tmp/SR-RX-v2.1.bundle lizbeth307
```

Bundle містить усю історію гілки й відображає лише закомічене, тому його будують після commit.

**Історична примітка.** До публікації ранній push повертав HTTP 403, і передача тимчасово йшла через `SR-RX-v2.1-git.patch.gz` (`git format-patch` від `465318835e…`). Цей шлях застарів: базовий коміт не входить у переписану історію `ccr-1537979d-cj7q9t`, а `format-patch` пропускає merge-коміти. Використовуйте clone або bundle.

Окремі перевірки з каталогу `sat-receiver-audit`:

```bash
python3 tools/run_checks.py --export
python3 verification/independent_netlist_check.py
python3 tools/run_tests_offline.py
python3 pcb/prepare.py --check
python3 verification/independent_pcb_check.py
python3 tools/build_firmware.py
```

Ті самі перевірки, відтворення CAD у KiCad 10.0.7 і module lab на x86_64/ARM64 виконує CI; ARM64 QEMU lab і перепакування запускаються вручну (`gh workflow run sr-rx-verify.yml --ref ccr-1537979d-cj7q9t -f linux_lab=true`, подробиці — у [HANDOFF](HANDOFF.md#ревізія-23102026-claude-перевірка-виправлення-ci-план)). Для перепакування після зміни джерел обов'язковий повний цикл [Linux FINDINGS](deployment/linux_lab/FINDINGS.md#відтворення-перевірки-та-пакування): актуальний inventory/source snapshots, host regression, новий Linux/module run і finalizer, документи, повторна host regression, ще раз документи, firmware, `python3 tools/build_bundle.py` та `python3 tools/check_bundle.py`. Старі Linux reports/source binding не підтверджують змінених джерел.

Потрібні KiCad 10 CLI, Python, Pandoc та залежності `tools/requirements.txt`. Для роботи зі схемами без генерації відкрийте `build/kicad/sr-rx-v2.kicad_pro`. Межа готовності й обов'язкові апаратні перевірки: [COMPLETION](COMPLETION.md) та [OPEN_ITEMS](OPEN_ITEMS.md). Гілка містить вихідні прошивки Pico/IMU, керувальне ПЗ, моделі модулів, Linux launcher, нерозведений PCB starter і внутрішній розведений прототип; фізичного приймання й готової виробничої PCB немає. Запуск і обмеження ПЗ: [software/README.md](software/README.md).
