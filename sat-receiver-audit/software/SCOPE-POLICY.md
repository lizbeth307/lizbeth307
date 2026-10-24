# Політики меж labd: маска TDF, ДХ-сигнали часу, стоп Artemis, egc-gate, алоу-лист NORAD

Модулі `srrx.scope_policy` і `srrx.egc_gate` реалізують правила з STACK.md (рядки 120, 121, 125, 631, 873, 880), build/07-pz-vstanovlennia.md (розділ 21, політики labd) і build/09-testy.md (ПОЛ-06, ПОЛ-09, П-12). `srrx.artemis_convert` (artemis-db v74 → дзеркало) і `srrx.norad_allowlist` (алоу-лист NORAD) готують для них дані на домашній базі. Усі чотири модулі — лише стандартна бібліотека, без мережі, без доступу до приймача чи файлів поза явно переданими шляхами. Кожне правило може лише **додати позначку або відмову**; маски `srrx.spectrum` не послаблюються. Тести працюють на синтетичних даних: це не доказ роботи на ефірі, не перевірка справжнього файла artemis-db v74 (її роблять вибіркові перевірки оператора, див. нижче) і не прийняття egc-gate.

```sh
PYTHONPATH=software python3 -m unittest discover -s software/tests -p 'test_scope_policy.py' -v
PYTHONPATH=software python3 -m unittest discover -s software/tests -p 'test_egc_gate.py' -v
PYTHONPATH=software python3 -m unittest discover -s software/tests -p 'test_artemis_convert.py' -v
PYTHONPATH=software python3 -m unittest discover -s software/tests -p 'test_norad_allowlist.py' -v
```

## Маска TDF 162 kHz (вівторок 06:00–12:00 UTC)

Джерело: STACK.md:121, :609–610, :1600; П-12 (09-testy.md:318). Вторинне джерело називає вівторок 08:00–12:00 без часового поясу, тому маска — об'єднання прочитань, 06:00–12:00 UTC, доки журнали П-12 не дадуть реальне вікно.

Консервативні рішення (у STACK не уточнено):

- Це **маска якості даних**, а не «no data»: TDF не має приватного вмісту, а П-12 мусить записувати амплітуду саме в цьому вікні, щоб його звузити. Відліки у вікні зберігаються, але мають позначку `TDF_MAINTENANCE`, не входять у базову лінію SID і похідні продукти та ніколи не стають результатом декодування часу (`tdf_sample_use()`).
- Правило застосовується, коли смуга торкається 162.000 kHz ± 1 kHz (захисний проміжок не задано в STACK; ±1 kHz — консервативний вибір). Від'ємні частоти комплексної базової смуги перевіряються дзеркально, як у `spectrum`.
- Вікно напіввідкрите: вівторок [06:00, 12:00) UTC. 05:59:59 — `OUT`, 06:00:00 — `IN_WINDOW`, 11:59:59 — `IN_WINDOW`, 12:00:00 — `OUT`.
- Вікно розширюється з обох боків на невизначеність годинника `clock_uncertainty_s(days) = 120 s + 100 ppm × дні з останньої схваленої синхронізації` (формула STACK.md:880).
- Неперевірений час (`utc_uncertainty_s=None` або невідомий час відліку) дає `UNKNOWN_UTC`, який споживачі трактують точно як `IN_WINDOW`.
- Звужувати вікно можна **лише** записом, перевіреним людиною: root-owned файлом без group/world write у root-owned каталогах (`load_tdf_window()`). Розширювати (`TdfWindow.widened()`) можна завжди. Автоматичного навчання вікна немає; конструктор `TdfWindow` відмовляє у звуженні без перевіреного запису.

Запис звуження (приклад структури, не чинний запис):

```json
{
  "v": 1,
  "kind": "srrx_tdf_maintenance_window",
  "weekday": "TUE",
  "start_utc": "07:00",
  "end_utc": "11:00",
  "basis": "reviewed_p12_amplitude_log",
  "evidence_id": "p12/als162-amplitude-4-tuesdays"
}
```

API: `tdf_window_status(span_lo_hz, span_hi_hz, t_start_utc, t_end_utc, utc_uncertainty_s, *, window=None)` → `IN_WINDOW` | `OUT` | `UNKNOWN_UTC`. Смуга без 162 kHz завжди `OUT` (позначка не застосовується). Час — aware `datetime` або POSIX-секунди; naive `datetime` відхиляється.

## ДХ-сигнали часу, SID і RBU (STACK.md:121)

- `radio_clock_mode(station)`: декодування Radio Clock дозволене лише для DCF77, MSF, TDF, WWVB, JJY40; JJY60 — лише амплітуда; RBU (66.666 kHz) — `RBU_BLOCKED`; будь-яка інша станція — відмова.
- `decoded_time_usable(station, tdf_status)`: декодований час TDF у вікні обслуговування (або при неперевіреному UTC) не є результатом.
- `sid_target(station, band_lo_hz, band_hi_hz)`: SID — лише амплітуда цивільних ДХ-несучих (DCF77, MSF, WWVB, JJY 40/60, TDF). Відмова для смуги, що торкається 3–30 kHz (`SID_VLF_3_30_KHZ_REFUSED`), RBU ± 1 kHz, неперелічених станцій і смуги, яка не містить своєї несучої. Маска |f| < 30 kHz у збережених даних лишається обов'язком labrx/spectrum.

## Стоп Artemis

Джерело: STACK.md:85, :125, :517, :631, :873, :2183; ПОЛ-09 (09-testy.md:77). Ідентифікація — лише artemis-db v74 у labd, без GUI Artemis.

Правила `scope_check(span_lo_hz, span_hi_hz, db=None)`:

| Причина | Коли |
|---|---|
| `CATEGORY` | категорія запису містить Military, Radar або Numbers Stations (без урахування регістру й роздільників). Категорії «Government» у базі немає, тому її в наборі нема |
| `DENY_REGEX` | будь-яке текстове поле запису (назва, опис, категорії, модуляція, режим, місце) містить military, navy, air force, NATO, STANAG, MIL-STD, Link-11/16, ALE 4G/WALE, jammer (також jamming), OTH, intelligence |
| `UNTAGGED_MASKED` | запис без жодної категорії має діапазон у замаскованій смузі (fail closed) |
| `MASKED_BAND` | сама вибрана смуга торкається замаскованої смуги — навіть без бази |

Консервативні відповіді на неуточнене в STACK:

1. Враховується **кожен** запис бази, діапазон якого перетинає вибрану смугу (дотик краю теж); один стоп-запис зупиняє всю смугу.
2. Deny-regex: NFKC, casefold, заміна кириличних/грецьких двійників латиницею, видалення всіх роздільників («Link 16», «Link-16», «Link16» однакові), пошук підрядка. Хибні збіги («OTH» в «other») прийнято: fail closed. Інші підміни символів (наприклад, цифра замість літери) не охоплені — залишковий ризик.
3. Замасковані смуги — об'єднання `spectrum.MASKED_BANDS_HZ` і смуг STACK: 3–30 kHz, 225–400 MHz, 1544.0–1545.0 MHz (STACK.md:873) і Cospas-Sarsat 406.0–406.1 MHz (STACK.md:600, :626). Маску spectrum 1530–1660 MHz (суворішу за STACK) не змінено: для цього потрібне окреме перевірене рішення. Смуга налаштування, що торкається будь-якої з них, зупиняється **цілком** (`MASKED_BAND`), а не лише в окремих бінах: маскування бінів — шар `srrx.spectrum`. Тому захоплення радіозондів тримають `center + rate/2 < 406.0 MHz` (скан 400.0–405.9 MHz, STACK.md:600).
4. Після стопу показується лише `"out of scope"`; `identify` — `WITHHELD`; результат не повторює смугу. Записи «Trunked Radio» показуються лише як безіменна зайнятість `{"occupancy": "anonymous"}`.
5. База відсутня, не прийнята або з невідповідним SHA256 — `identify: UNAVAILABLE`, ніколи не «in scope»; стоп замаскованої смуги діє й тоді. Результат без стопу ніколи не містить слів «in scope».

`ScopeLatch(db)` — засувка сеансу: `permits(op, span)` для `mark`, `record`, `label`, `decode`, `export` дає `False` для невідомої операції, недійсної смуги, смуги, що торкається засувки, або смуги, яку `scope_check` зупиняє зараз (вона теж засувається). Засувка тримається, доки приймач не перелаштовано геть (`retune()` до смуги, яка її не торкається); `stop()` додає засувку оператора. Кожна нова засувка викликає зареєстровані `register_abort()`-обробники: запис, що перетинається, переривається, а тимчасовий вихід відкидається (атомарна публікація, як у `decoder_policy.execute`). **Уже опубліковані файли не видаляються** — це потребує явного рішення оператора, і автоматично не робиться. Пам'ять обмежена: понад 64 засувки зливаються в одну охопну смугу (fail closed).

`ScopeLatch` не потокобезпечна. Для фонової задачі `detached_copy()` дає копію з тією самою базою (ArtemisDB після завантаження не змінюється) і тими самими засувками, але без abort-обробників (`register_abort` на копії відмовляє, `DETACHED_COPY`); копія належить одному потоку. Новий стоп, знайдений копією, засувається лише в ній. `adopt(copy)` викликає власник у своєму потоці: кожен такий стоп засувається в оригіналі з тими самими abort-обробниками й рядком журналу, `ABORT_CALLBACK_FAILED` піднімається після засування всіх стопів, повторний `adopt` нічого не додає, чужа копія чи звичайна засувка — `DETACHED_COPY_INVALID`. `adopt` повертає `True`, якщо після створення копії оригінал не отримав жодної нової засувки (лічильник `latch_generation`; звільнення через `retune()` його не змінює, бо лише розширює дозвіл, а результат, обчислений проти суворіших засувок, лишається fail closed).

Журнал: `stop_log_line(utc)` і `ScopeLatch.drain_log()` дають рівно `2026-10-20T08:00:00Z out of scope` — без частоти, місця, пеленга чи тексту запису.

### Формат бази і запис прийняття

`ArtemisDB.load(path, accepted_sha256)` читає файл один раз (до 64 MiB), обчислює SHA256 саме цих байтів і порівнює з прийнятим; аналізуються ті самі байти, тож підміни між перевіркою і читанням немає. Модуль ніколи не завантажує базу з мережі. `detect_format()` розпізнає:

- SQLite (`SQLite format 3\0`) — власний файл artemis-db. labd його **ніколи не розбирає**: навіть із прийнятим SHA256 база отримує `UNAVAILABLE_FORMAT_UNVERIFIED_SQLITE` і нічого не ідентифікує. Схему v74 перевіряє й перетворює на дзеркало лише `srrx.artemis_convert` (нижче).
- нормалізоване дзеркало `srrx_artemis_mirror_v1` (JSON) — єдиний прийнятий формат:

```json
{
  "v": 1,
  "kind": "srrx_artemis_mirror",
  "source": "artemis-db",
  "db_version": "v74",
  "entries": [
    {"name": "ПРИКЛАД", "categories": ["Broadcast"], "ranges_hz": [[100000000, 100200000]],
     "description": "необов'язково", "modulation": "необов'язково", "mode": "необов'язково", "location": "необов'язково"}
  ]
}
```

Поля записів суворі: невідомі ключі, NaN, дублікати ключів, boolean замість числа, `lo > hi`, від'ємні частоти, понад 32 діапазони або 32 категорії, понад 20 000 записів чи 100 000 діапазонів — `UNAVAILABLE_SCHEMA`. Порожній список категорій означає запис без тегу.

Запис прийняття — root-owned JSON (ті самі вимоги до власника й каталогів, що в `decoder_policy`), `ArtemisDB.load_accepted(path, record_path)`:

```json
{
  "v": 1,
  "kind": "srrx_artemis_acceptance",
  "db": "artemis-db",
  "db_version": "v74",
  "format": "srrx_artemis_mirror_v1",
  "sha256": "ЛОКАЛЬНО_ОБЧИСЛЕНИЙ_64_HEX_SHA256",
  "evidence_id": "admin/artemis-db-v74-mirror-001"
}
```

Без прийнятого дзеркала база в labd лишається `UNAVAILABLE`, а діє лише стоп замаскованих смуг.

### Перетворювач artemis-db v74 → дзеркало

`python3 -m srrx.artemis_convert` (stdlib `sqlite3`, без мережі) перетворює `data.sqlite` з архіву випуску Artemis-DB v74 на `srrx_artemis_mirror_v1`. Схему взято з `models/model.py` і `7.create_sqlite.py` репозиторію AresValley/Artemis-DB на коміті e54d5c3 («Preparing release v74», 18.07.2026; Peewee 4.1.1 за `uv.lock`, типові імена таблиць), звірено 24.10.2026. Випуск v74 — вкладення `v74.tar` (302 172 160 байт; GitHub показує digest `sha256:4ef66d5e0eddbc5430cc102f84de0489efd40b979bc6b78abdf259999d09d052`, станом на 24.10.2026). Архів містить і медіа; конвертеру потрібен лише `data.sqlite`. Ліцензію вмісту, похідного від SigID, не перевірено, а в README Artemis-DB названо лише GPL-3 самого Artemis: дзеркало лишається локальним, не публікується і не комітиться.

Перевірки джерела. Будь-яке відхилення — відмова всього файла зі стабільним кодом (`ConvertRefused`; без вмісту файла, щонайбільше назва таблиці чи номер аргументу):

1. Звичайний файл (lstat; symlink, FIFO, пристрій — `NOT_REGULAR_FILE`) до 256 MiB із заголовком `SQLite format 3\0` у форматі rollback journal (байти 18/19 = 1; WAL — `SQLITE_JOURNAL_MODE`). SHA256, inode, розмір і mtime знімаються до й після читання; зміна — `SOURCE_CHANGED`.
2. Відкриття `file:…?mode=ro&immutable=1`. Authorizer дозволяє лише читання, `typeof()` і перелічені pragma: без ATTACH, запису й розширень. Також `SQLITE_DBCONFIG_DEFENSIVE`, `trusted_schema=OFF`, тригери й view вимкнено (Python 3.12+). Біля джерела не з'являється жоден файл (`-journal`, `-wal`, `-shm`).
3. `PRAGMA integrity_check` дає рівно `ok` (`SQLITE_INTEGRITY`; пошкоджені сторінки — `SQLITE_UNREADABLE`).
4. Точний набір таблиць, стовпців (ім'я, оголошений тип, NOT NULL, default, первинний ключ, без прихованих чи генерованих стовпців) і зовнішніх ключів (`SCHEMA_TABLES`, `SCHEMA_COLUMNS:<таблиця>`, `SCHEMA_FOREIGN_KEYS:<таблиця>`):

| Таблиця | Стовпці | Зовнішні ключі |
|---|---|---|
| `info` | DATE TEXT, EDITABLE INTEGER, NAME TEXT, VERSION INTEGER (без первинного ключа) | — |
| `signals` | SIG_ID INTEGER NOT NULL PK, DESCRIPTION TEXT, NAME TEXT, URL TEXT, SINCE_VERSION INTEGER | — |
| `acf` | ACF_ID PK, DESCRIPTION TEXT, SIG_ID INTEGER, VALUE REAL | SIG_ID → signals |
| `bandwidth`, `frequency` | BAND_ID / FREQ_ID PK, DESCRIPTION TEXT, SIG_ID INTEGER, VALUE INTEGER | SIG_ID → signals |
| `categorylabel` | CLB_ID PK, VALUE TEXT | — |
| `category` | CAT_ID PK, CLB_ID INTEGER, SIG_ID INTEGER | CLB_ID → categorylabel, SIG_ID → signals |
| `documents` | DOC_ID PK, DESCRIPTION TEXT, EXTENSION TEXT, NAME TEXT, PREVIEW INTEGER, SIG_ID INTEGER, TYPE TEXT | SIG_ID → signals |
| `location`, `mode`, `modulation` | LOC_ID / MOD_ID / MDL_ID PK, DESCRIPTION TEXT, SIG_ID INTEGER, VALUE TEXT | SIG_ID → signals |

PK — `INTEGER NOT NULL PRIMARY KEY`, решта стовпців допускає NULL; дії ключів `NO ACTION`. Індекси дозволені лише на цих таблицях. View, тригери, віртуальні таблиці, `sqlite_stat*` чи будь-яка інша таблиця — відмова (`SCHEMA_OBJECTS`, `SCHEMA_TABLE_KIND`, `SCHEMA_TABLES`). Рядок `info` рівно один: NAME `SigID`, VERSION — ціле 74 (`INFO_ROWS`, `INFO_NAME`, `INFO_VERSION`; v73 і майбутня v75 теж відмова, доки їхню схему не перевірено так само).

Правила значень:

- `frequency.VALUE` — збережене ціле 1…10¹² (Hz), `bandwidth.VALUE` — ціле 0…10¹². Текст, дробове число чи NULL — відмова (`FREQUENCY_VALUE`, `BANDWIDTH_VALUE`), бо так можуть ховатися інші одиниці. `acf.VALUE` не використовується, але має бути числом або NULL.
- Кожен дочірній рядок і кожна категорія посилаються на наявний сигнал і мітку (`ORPHAN_ROW:<таблиця>`, `CATEGORY_REFERENCE`). Мітка — текст до 128 символів, не більше 32 категорій на сигнал. Назва сигналу — непорожній текст (`SIGNAL_NAME`). Інші текстові стовпці — текст або NULL (`TEXT_TYPE:<таблиця>`).
- Одиниці підтверджує оператор: щонайменше 3 різні вибіркові перевірки `--expect "НАЗВА=HZ"` відомих цивільних записів. Кожна має бути точною частотною точкою рівно одного сигналу (`SPOT_CHECKS_REQUIRED`, `SPOT_CHECK_NAME:<n>`, `SPOT_CHECK_FREQUENCY:<n>`). У вихідних JSON v74 (`static/<pageid>/signal.json` на e54d5c3) значення — цілі Hz: DCF77 — 77500, MSF — 60000, «Automatic Identification System (AIS)» — 161975000, «Automatic Dependent Surveillance-Broadcast (ADS-B)» — 1090000000. Це рекомендовані перевірки; файл у kHz чи MHz їх не пройде.

Діапазони сигналу (консервативно: SigID зберігає точки без рядків діапазонів, а дві точки можуть бути межами смуги):

- h = ⌈max(B)/2⌉; обвідна [min(F) − h, max(F) + h] плюс кожна точка [f − h, f + h], усе в межах 0…10¹². Без смуги (немає рядків або max(B) = 0) — лише обвідна. Понад 32 діапазони — лише обвідна, яка й так покриває всі точки (лічильник `envelope_only`).
- Сигнал без частоти не перетинає жодної смуги: він рахується в `signals_without_frequency` і в дзеркало не потрапляє.
- **Наслідок.** Обвідна військових записів із точками на краях КХ зупиняє весь проміжок між ними. У вихідних даних v74 STANAG 4285 (Military) має точки 1.89 і 22.7 MHz, а 4G ALE/WALE (Military) — 3 і 30 MHz, тож із прийнятою базою кожна смуга приблизно між 1.888 і 30.0015 MHz дає стоп `CATEGORY`. Це свідомий надмірний стоп (fail closed). Звузити його (наприклад, лише точки для записів із понад двома точками чи рецензовані діапазони) — окреме рішення власника; у коді такого режиму немає.

Тексти. Категорії — `category → categorylabel.VALUE`. Опис — опис сигналу плюс описи його рядків acf, bandwidth і frequency. Модуляція, режим і місце — їхні VALUE і DESCRIPTION через «; ». Поля обрізаються до меж дзеркала (назва — 256 символів, опис — 16 384, решта — 1 024). Якщо обрізання прибрало deny-термін, опис починається з `[srrx: <термін>] `. Потім `scope_policy` (той самий код, що в labd) повторно перевіряє кожен запис, тож стоп не змінюється (`deny_markers` у звіті). Рядки `documents` і URL не копіюються.

Вихід — три нові файли; наявний файл ніколи не замінюється (`OUTPUT_EXISTS`):

- `artemis-mirror.json` — детермінований JSON (відсортовані ключі й записи, UTF-8) у межах ArtemisDB (≤ 20 000 записів, ≤ 32 діапазони на запис, ≤ 100 000 діапазонів, ≤ 64 MiB). Перед поверненням дзеркало завантажується через `ArtemisDB.load`.
- `artemis-acceptance.template.json` — шаблон запису прийняття з локально обчисленим SHA256 дзеркала. `evidence_id` — заповнювач `REVIEW REQUIRED: …`; `load_artemis_acceptance` відхиляє його, доки людина не впише справжній ідентифікатор.
- `artemis-conversion-report.json` — SHA256 і розмір джерела, Info, лічильники, вибіркові перевірки, SHA256 дзеркала; шляхів немає.

Процедура (домашня база або пристрій; мережа для перетворення не потрібна):

```sh
sha256sum v74.tar                        # звірити з digest випуску v74
tar -tf v74.tar | grep data.sqlite       # шлях усередині архіву
tar -xf v74.tar <шлях>/data.sqlite
PYTHONPATH=software python3 -m srrx.artemis_convert --sqlite <шлях>/data.sqlite --output-dir artemis-out \
  --expect "DCF77=77500" --expect "MSF=60000" \
  --expect "Automatic Identification System (AIS)=161975000" \
  --expect "Automatic Dependent Surveillance-Broadcast (ADS-B)=1090000000"
```

Рецензент переглядає звіт (`signals`, `entries`, `signals_without_frequency`, `deny_markers`, `truncated_fields`), вибірково звіряє кілька записів Military, Radar і Numbers Stations із SigID і копіює шаблон у запис прийняття з власним `evidence_id` (наприклад, `admin/artemis-db-v74-mirror-001`). Встановлення:

```sh
sudo install -o root -g root -m 0644 artemis-out/artemis-mirror.json /var/lib/srrx/artemis-mirror.json
sudo install -o root -g root -m 0644 artemis-acceptance.json /etc/srrx/artemis-acceptance.json
python3 -m srrx.hmi --artemis-db /var/lib/srrx/artemis-mirror.json --artemis-acceptance /etc/srrx/artemis-acceptance.json
```

Усі батьківські каталоги запису мають бути root-owned без group/world write. Якщо справжній `data.sqlite` дає `SCHEMA_*`, порівняйте `PRAGMA table_xinfo` і `PRAGMA foreign_key_list` з таблицею вище. Схему змінюють лише окремим перевіреним рішенням разом із тестом. Справжній файл v74 у проєкті не зберігається, тож його перетворення — крок домашньої бази (build/09-testy.md, розділ 17: ПОЛ-09a — CI, ПОЛ-09b — удома).

## egc-gate (Inmarsat-C EGC SafetyNET)

Джерело: STACK.md:85, :120, :873, :1335, :1501; ПОЛ-06 (09-testy.md:74). Профіль `egc-safetynet` у `decoder_policy` **лишається DISABLED**; `egc_gate.gate_status()` завжди починається з `DISABLED`. `RELEASE_EVIDENCE` (таблиця C2 International SafetyNET Services Manual, змішаний запис ПОЛ-06, перевірений алгоритм контрольної суми) — усі `False`. Проходження синтетичних юніт-тестів профіль не вмикає; це перевіряє окремий тест. `decoder_policy` не імпортує `egc_gate`.

Реалізовано:

1. `classify(packet)` читає лише байти 0–3 (0–5 для початку multiframe): клас із байта 0 (`0xxxxxxx` short — ніколи не EGC; `10xxxxxx` medium, довжина `pkt[1]+2`; `11xxxxxx` long, довжина `pkt[1..2]+3`), тип `byte0 & 0x3F`, EGC — 0x30/0x31/0x32 (сирі 0xB0–0xB2 і 0xF0–0xF2).
2. Сервісний код на зсуві 2 (medium) або 3 (long), а не жорстко `pkt[2]`.
3. Приймаються лише SafetyNET {0x04, 0x13, 0x14, 0x24, 0x31, 0x34, 0x44, 0x73}; System {0x00, 0x11, 0x23, 0x33}, FleetNET {0x02, 0x72} і решта 242 коди відкидаються (усього 248 не-SafetyNET кодів).
4. Рішення для multiframe — на першому фрагменті; внутрішній дескриптор на byte 2; його заголовок і сервісний код мають повністю лежати в першому фрагменті.
5. Контрольна сума обчислюється лише для прийнятих пакетів; відкинутий пакет не перевіряється і не копіюється (тест-шпигун фіксує, що читаються лише окремі байти заголовка).
6. `EgcAssembler` тримає не більше одного відкритого повідомлення (до 16 KiB, до 32 фрагментів), будь-який інший пакет відкидає незавершене повідомлення з обнуленням буфера.
7. `NcsWatchdog(n_frames)` зупиняє демодуляцію після N кадрів поспіль без заголовка NCS; зупинка засувкова. N — обов'язковий параметр (визначає тест egc-gate на змішаному записі; тут не вигадано).
8. `scope_policy.demod_allowed(center_hz, bw_hz)` — лише кандидати NCS 1537.0–1543.9 MHz, нічого від 1544.0 MHz. Це необхідна, а не достатня умова: `scope_check` і далі зупиняє 1530–1660 MHz маскою spectrum.

Припущення, які треба звірити з SatDump `packets_structs.h` на коміті 1aedd60 (URL у STACK.md:1955) до будь-якого вмикання: довжина long — big-endian; 0x3D — початок, 0x3E — продовження, обидва лише medium (0xBD/0xBE), long-форма 0xFD/0xFE відкидається; фрагмент — 2 байти заголовка, дані, 2 байти суми; продовження без прийнятого початку відкидається; відкинутий початок відкидає наступні продовження до нового початку.

Алгоритм контрольної суми Inmarsat-C у джерелах проєкту відсутній, тому він **лише ін'єктується** (`checksum_ok(packet, algorithm)`, `EgcAssembler(checksum)`); без нього нічого не перевіряється й не пропускається. Тести використовують навмисно іграшкову суму байтів, позначену як фікстура. Декодер кадрів SatDump `module_stdc_decoder`, перевірка таблиці C2 і змішаний запис ПОЛ-06 — відкриті.

## Алоу-лист NORAD для орбіт

Джерело: STACK.md:141, :192, :873, :884; формат `srrx_orbit_allowlist` і ролі — `srrx.orbits` ([LOCATION.md](LOCATION.md#orbit-elements-and-pass-prediction)). NORAD id не пишуться ні в код, ні в репозиторій: `srrx.norad_allowlist` бере їх із локальної копії SATCAT на домашній базі, а людина перевіряє звіт.

Запит — `software/config/orbit-targets.json`. Кожна ціль STACK задана точними `OBJECT_NAME` і `LAUNCH_DATE` із SATCAT, роллю `srrx.orbits.ROLES` і назвою для показу (ключ `norad_id` у запиті — відмова). Назви й дати звірено з CelesTrak SATCAT 24.10.2026:

| Ціль STACK | SATCAT OBJECT_NAME | LAUNCH_DATE | Роль |
|---|---|---|---|
| Meteor-M N2-3 | METEOR-M2 3 | 2023-06-27 | LRPT |
| Meteor-M N2-4 | METEOR-M2 4 | 2024-02-29 | LRPT |
| MetOp-B, MetOp-C | METOP-B, METOP-C | 2012-09-17, 2018-11-07 | OTHER |
| AWS | ARCTIC WEATHER SATELLITE | 2024-08-16 | OTHER |
| Elektro-L2, L3, L5 | ELEKTRO-L 2, ELEKTRO-L 3, ELEKTRO-L 5 | 2015-12-11, 2019-12-24, 2026-02-12 | GEO |
| FY-2H | FENGYUN 2H | 2018-06-05 | GEO |
| МКС (437.550, 437.800 MHz SSTV, 437.825 MHz) | ISS (ZARYA) | 1998-11-20 | ISS |
| QO-100 | ES'HAIL 2 | 2018-11-15 | QO100 |

Правила; будь-який сумнів — відмова всієї збірки (`AllowlistRefused`, код із номером цілі):

- Рівно один об'єкт SATCAT із такою назвою і датою запуску (`SATCAT_NO_MATCH`, `SATCAT_AMBIGUOUS`). Копії того самого рядка з кількох файлів рахуються один раз; розбіжні копії — відмова. Тип `PAY` (`SATCAT_NOT_PAYLOAD`), без DECAY_DATE і не статус `D` (`SATCAT_DECAYED`), COSPAR `YYYY-NNNA`, NORAD 1…999999 (`SATCAT_ROW`). 6-значні номери дозволені; `srrx.passes` пропускає номери понад 339999 із причиною.
- Для кожного id потрібен набір елементів GP: правила `srrx.orbits.parse_omm`, найновіша епоха з усіх файлів. Його `OBJECT_ID` має збігатися з COSPAR із SATCAT (`GP_MISSING`, `GP_OBJECT_ID_MISMATCH`, `GP_CONTRADICTION`, `GP_SCHEMA`).
- Результат приймає `srrx.orbits.allowlist` (≤ 256 цілей, не більше однієї QO100); запит перевіряється так само (`TARGETS_QO100`, `TARGET_DUPLICATE`).

Процедура (домашня база; інструмент нічого не завантажує, URL — лише текст для оператора):

```sh
# 1. SATCAT: повний https://celestrak.org/pub/satcat.csv або записи за назвою
#    https://celestrak.org/satcat/records.php?NAME=METEOR-M2&FORMAT=CSV (--satcat можна повторювати)
PYTHONPATH=software python3 -m srrx.norad_allowlist resolve \
  --targets software/config/orbit-targets.json --satcat satcat.csv
# 2. GP для кожного id за його gp_query (gp.php?CATNR=<id>&FORMAT=json); група weather не містить
#    AWS, Elektro-L3 і Elektro-L5
PYTHONPATH=software python3 -m srrx.norad_allowlist build --targets software/config/orbit-targets.json \
  --satcat satcat.csv --gp gp-1.json --gp gp-2.json --output-dir orbit-out
# 3. Рецензія orbit-allowlist.report.json; шаблон -> запис прийняття з власним evidence_id
sudo install -o root -g root -m 0644 orbit-out/orbit-allowlist.json /etc/srrx/orbit-allowlist.json
sudo install -o root -g root -m 0644 orbit-allowlist.acceptance.json /etc/srrx/orbit-allowlist.acceptance.json
python3 -m srrx.norad_allowlist check --allowlist /etc/srrx/orbit-allowlist.json \
  --record /etc/srrx/orbit-allowlist.acceptance.json
```

`build` створює три нові файли: `orbit-allowlist.json` (детермінований, цілі за NORAD id), `orbit-allowlist.acceptance.template.json` (SHA256 і заповнювач `evidence_id`, який відхиляється до рецензії) і `orbit-allowlist.report.json` (знайдені рядки SATCAT, ім'я та епоха GP, SHA256 вхідних файлів; без шляхів). `load_accepted(allowlist, record)` читає root-owned запис (ті самі вимоги, що в `decoder_policy`), а алоу-лист — один раз, звіряє SHA256 і повертає відображення `srrx.orbits`. Склад цілей і ролі змінюють лише в `orbit-targets.json` з повторною збіркою й рецензією. Новий запуск (наприклад, Meteor-M N2-5) — нова ціль, а не правка id. Тести — ПОЛ-16 (build/09-testy.md, розділ 17).

## Споживачі

- `learning.annotate(..., scope=None)`: стоп замаскованої смуги на смузі box застосовується завжди; передана `ScopeLatch` додає стоп Artemis (`label`). `learning.train(..., scope=None)` вимагає дозволу `label` для смуги кожної навчальної анотації, `learning.infer(..., scope=None)` для зупиненої смуги не дає мітки. Помилка не містить частоти.
- `decoder_policy.make_plan(..., scope=None)` і `execute(..., scope=None)`: перевірка всієї смуги 137–138 MHz (`decode`) до будь-якого доступу до встановлення чи джерела; повторна перевірка (`export`) перед атомарною публікацією — стоп під час запуску не залишає результату.
- `labrx.run_capture(..., scope=None)`: передана `ScopeLatch` перелаштовується на смугу налаштування ще до доступу до labd чи приймача і має дозволяти `record` перед кожним кадром, який записується в `output`/`survey`. Інакше — `ValueError("out of scope")` без частоти, і нічого більше не записується; стоп під час прогону проходить звичайний cleanup із закриттям джерела й запитом OFF.
- HMI: `create_window(..., scope_latch=None)` бере одну засувку на сесію (за замовчуванням `ScopeLatch()` без бази; `python -m srrx.hmi --artemis-db … --artemis-acceptance …` передає `ScopeLatch(ArtemisDB.load_accepted(...))`). Засувка перелаштовується при старті захоплення й на кожному показаному кадрі, перериває роботу приймача через `register_abort`, показує лише «out of scope» (без частоти, смуги чи графіка) і передається в `annotate`, `train` та `infer`. Ці дії виконуються фоновою задачею з `detached_copy()`; смуги box для анотації та класифікації GUI thread перевіряє ще до старту (засувка й переривання SIM capture одразу). Стоп, який знайшло лише фонове навчання (наприклад, Artemis-збіг для анотації з попереднього сеансу без бази), засувається, а SIM capture, що перетинається, переривається, коли задача завершилася, скасована чи відхилена — не посеред задачі. Якщо за час задачі засувка сеансу отримала новий стоп, результат відкидається. Якщо вікно закрито під час такої задачі, її рядок журналу втрачається.
- Ще не підключено: CLI `python -m srrx.labrx` не створює `ScopeLatch` (діють лише маски `srrx.spectrum`); позначка TDF (`tdf_sample_use()`) не має споживача, бо журналу SID у коді ще немає; `model_export` засувку не перевіряє; приймач HMI поки лише `ReceiverSimulation`; служба labd засувки сесії не тримає.
- Алоу-лист NORAD: `srrx.passes` (`--allowlist`) поки читає його через `orbits.load_allowlist` без запису прийняття; `norad_allowlist.load_accepted()` готовий для labd і планувальника проходів, але ще ними не викликається. Імпортер SatNOGS з алоу-листом (NORAD, частота ±10 kHz, режим; STACK.md:873, :1501) не реалізовано. Перетворення artemis-db запускається вручну: labd дзеркало не будує й не оновлює.
