# Декодери: дозвільні профілі та фактична межа

Модуль `srrx.decoder_policy` реалізує виконуваний **офлайн WAV → PNG профіль цивільної погоди**. Наявність коду не означає встановлення зовнішнього декодера. У цьому комплекті немає прийнятого запису встановлення; запуск за замовчуванням недоступний. Апаратне приймання не виконано.

```sh
PYTHONPATH=software:. python3 -m srrx.decoder_policy status
PYTHONPATH=software:. python3 -m unittest discover -s software/tests -p test_decoder_policy.py -v
```

| Профіль | Стан і межа |
|---|---|
| `noaa-apt-weather` | Реалізований file-only runner для **noaa-apt 1.4.1**, вихід — лише погодне PNG і звіт фіксованої структури; потрібні прийняте встановлення та погоджений mono PCM16 WAV |
| `satdump-weather` | Залежить від прийнятого встановлення (v2.1): лише baseband LRPT Meteor-M, записаний `labrx.run_baseband`, декодується в екземплярі шаблону `srrx-satdump-decode@` (`srrx.satdump_pass`, `srrx.satdump_unit`), вихід — лише санітизовані PNG і звіт; без прийнятого запису встановлення (зараз) — `UNAVAILABLE_NO_ACCEPTED_INSTALLATION`. Збірка за `deployment/recipes/satdump` — збирач +lab (важкий job `sr-rx-packages`, запис збирання CI_BUILT_UNREVIEWED, не рецензія); шаблон запису — `installation_template` у `satdump.package-hook.json`, прийнятого запису в Git немає |
| `egc-safetynet` | Вимкнений. Окремий модуль `srrx.egc_gate` класифікує заголовки за правилами egc-gate на синтетичних пакетах (таблиця C2 за IMO MSC.1/Circ.1364/Rev.2: 00 лише з пріоритетом urgency/distress, 04, 13, 14, 24, 31, 34, 44; 0x73 відкидається; контрольна сума за SatDump `packets_structs.h` 1aedd60, надіслане 0 відкидається), але цей профіль його не імпортує і жодних байтів пакетів не читає; джерела прочитано 07.11.2026, проте не прорецензовано (`SOURCE_READ_UNREVIEWED`), тож усі `RELEASE_EVIDENCE` — `False`; вмикання — лише після рецензії таблиці C2 і алгоритму контрольної суми та змішаного запису ПОЛ-06 ([SCOPE-POLICY.md](SCOPE-POLICY.md)) |
| `dsc-safety` | Вимкнений до перевіреного парсера format/category і тестових векторів; жодні адреси/MMSI або payload не читаються |
| `amateur-digital` | Недоступний: конкретний decode-only профіль і версія CLI не кваліфіковані |
| `ais-public`, `adsb-public` | `ais-public` (W2 SW-AIS) залежить від прийнятого встановлення, як `satdump-weather`, але це оренда рушія, а не file-план цього модуля: `make_plan` відмовляє `DISABLED_FILE_PLAN_AIS_RUNS_ONLY_AS_LEASE_ENGINE` ще до доступу до будь-якого файла; AIS-catcher 0.70+lab1 (`deployment/recipes/ais-catcher`) працює лише в оренді `srrx-lease-aiscatcher@.service` (екземпляр `rtla`, `rtlb` або `hfplus`) з `-X off` (без нього v0.70 вмикає мережевий community feed) за фільтром `srrx.ais_filter`: судно публікується лише після статичного повідомлення 5, 19 або 24B з відомим типом судна, крім 35; пізній тип 35 вилучає судно й придушує MMSI до кінця оренди, пізній невідомий тип вилучає без придушення; про судна нічого не журналюється. Без запису встановлення (ELF, `ais_filter.py`, шаблон оренди й рецепт за SHA-256) — `UNAVAILABLE_NO_ACCEPTED_INSTALLATION`, із записом, що не проходить перевірку, — `UNAVAILABLE_INSTALLATION_NOT_QUALIFIED`, із прийнятим (`load_ais_installation()` як `ais_installation=`) — `LEASE_PRESET_ACCEPTED_RECEIVER_LEASE_REQUIRED_AT_RUN`; `engine_lease` labd цього запису ще не перевіряє, приймання на Q6A — OPEN. `adsb-public` (W2 SW-ADSB) залежить від прийнятого встановлення, як `satdump-weather`, але це оренда рушія, а не file-план цього модуля: `make_plan` відмовляє `DISABLED_AS_FILE_PLAN_READSB_LEASE_ONLY` ще до доступу до будь-якого файла; readsb 3.16.17+lab1 працює лише в оренді `srrx-lease-readsb@.service` (екземпляр `rtla` або `rtlb`; приймач ADS-B на LAB USB H3 зі STACK.md:825 ще не має псевдоніма `/dev/lab` і оренди — OPEN) за фільтром `srrx.adsb_filter` (dbFlags & 1/4/8 — за readsb і за власним читанням бази, військові діапазони ICAO, адреси не ICAO приховано; прихованих не показує, не рахує й не пише). Без прийнятого запису `/var/lib/srrx/adsb/acceptance.json` (aircraft.csv.gz з tar1090-db, не старший за 90 днів, і таблиця військових діапазонів `ranges.json`; обидва лише завантажуються вдома й не комітяться) — `UNAVAILABLE_NO_ACCEPTED_INSTALLATION`, із записом, що не проходить перевірку, — `UNAVAILABLE_INSTALLATION_NOT_QUALIFIED`, із прийнятим (`load_adsb_acceptance()` як `adsb_acceptance=`) — `LEASE_PRESET_ACCEPTED_FILTER_CHECKS_AT_START`. Приймання на Q6A — OPEN |

EGC/DSC не замінені фільтром уже декодованого тексту. Відмова відбувається за назвою профілю **до відкриття джерела чи метаданих**. Немає заяви про виконаний SafetyNET/DSC gate: юніт-тести `egc_gate` на синтетичних пакетах профіль не вмикають, і окремий тест перевіряє, що `availability()` далі повертає `DISABLED_NO_VERIFIED_HEADER_PARSER_AND_TEST_VECTORS`. Непідтверджені протокольні поля не вигадані.

## Межі сеансу (стоп Artemis і маски)

`make_plan(..., scope=None)` і `execute(..., scope=None)` приймають засувку сеансу `scope_policy.ScopeLatch` ([SCOPE-POLICY.md](SCOPE-POLICY.md)). Перевіряється вся смуга метеосупутників 137–138 MHz: стоп замаскованої смуги діє завжди, передана засувка додає стоп Artemis. Перевірка `decode` виконується після схеми метаданих, але **до** будь-якого доступу до запису встановлення чи файла джерела; перевірка `export` — безпосередньо перед атомарним перейменуванням результату, тож стоп під час роботи декодера залишає лише видалений тимчасовий каталог. Відмова — `OUT_OF_SCOPE` без частоти; інший об'єкт замість засувки — `SCOPE_LATCH_REQUIRED`. Без засувки поведінка CLI не змінилася. Уже опубліковані результати автоматично не видаляються.

## Перевірена зовнішня команда

Джерела перевірено 20.10.2026:

- [Офіційна інструкція noaa-apt](https://noaa-apt.mbernardi.com.ar/usage.html) описує `input.wav -o output.png`, `--map no`, `--rotate no`, `--quiet`; IQ без FM-демодуляції не підтримується.
- [Офіційний release v1.4.1](https://github.com/martinber/noaa-apt/releases/tag/v1.4.1) вказує commit **48a9eb8321f722634aafd1f9dcf4d80e9bfe274d**; [зміна версії в цьому коміті](https://github.com/martinber/noaa-apt/commit/48a9eb8321f722634aafd1f9dcf4d80e9bfe274d) встановлює 1.4.1.
- Перевірено [парсер аргументів саме цього коміту](https://github.com/martinber/noaa-apt/blob/48a9eb8321f722634aafd1f9dcf4d80e9bfe274d/src/config.rs) і [режими запуску](https://github.com/martinber/noaa-apt/blob/48a9eb8321f722634aafd1f9dcf4d80e9bfe274d/src/main.rs). `--version` у цій версії **безумовно виконує перевірку оновлень через мережу**, тому runner його не запускає. Натомість bounded `--help` перевіряє потрібний інтерфейс; точна версія прив'язується прийнятим source commit і SHA256 бінарника.

Команда завжди створюється всередині модуля:

```text
/прийнятий/шлях/noaa-apt /тимчасовий/input.wav -o /тимчасовий/output.png --map no --rotate no --quiet
```

Job не може додати аргументи, оточення, pipeline, URL, SDR-пристрій, gain, bias, TX, shell або output sink. `shell=False`; executable — абсолютний ELF `noaa-apt`, root-owned, без group/world write, з точним SHA256. Усі батьківські каталоги executable і запису встановлення теж мають належати root без group/world write (world-writable дозволено лише зі sticky bit), бо runner повторно хешує файл і запускає його за шляхом: інакше процес без прав root може перейменуванням підмінити бінарник між перевіркою та `execve`. Скрипти й PATH lookup не приймаються. Не запускаються SatDump live/record, TX-capable GUI або довільний декодер.

Санітарний звіт і plan manifest містять лише фіксовані поля, hash, розміри й символічні аргументи. Шляхи джерела, evidence text, stdout/stderr і декодовані текстові повідомлення до звіту не потрапляють. Decode stdout/stderr відразу спрямовані в `/dev/null`; лише bounded `--help` тимчасово читається в пам'яті. Тайм-аут декодування 0.05–300 s; окрема перевірка `--help` має до 3 s. При завершенні/тайм-ауті закривається вся створена process group.

Це політика запуску довіреного декодера, **не OS sandbox для недовіреного виконуваного файла**. Прийнятий ELF та його походження мають бути перевірені адміністратором. Модуль не підтверджує сам факт походження бінарника лише за написаним у JSON source commit. Зміна SHA256 скасовує прийняття; інша версія відхиляється. Відсутні root-owned записи не створюються автоматично.

## Метадані погодженого джерела

`labrx` не зобов'язаний записувати IQ, щоб працював цей профіль: потрібен окремо погоджений **FM-демодульований погодний WAV** або погоджений публічний архів. Цей модуль не виконує IQ-демодуляцію, не вмикає запис IQ і не відкриває SDR. NOAA APT профіль також придатний для історичних записів; тут немає обіцянки, що певний супутник зараз передає.

Приклад структури, який треба заповнити фактичним SHA256 і evidence ID:

```json
{
  "v": 1,
  "sha256": "ACTUAL_64_LOWERCASE_HEX_SHA256",
  "purpose": "public_civil_weather",
  "satellite": "NOAA-19",
  "origin": "approved_public_archive",
  "evidence_id": "archive/acceptance-001",
  "voice_present": false,
  "private_payload": false,
  "military": false,
  "emitter_geolocation": false,
  "iq_retained": false,
  "format": "wav_pcm_s16le_mono"
}
```

Допустимі джерела: `approved_labrx_audio` або `approved_public_archive`; супутники — NOAA-15/18/19. Невідомі поля заборонені. Кожне з п'яти заборонних полів мусить бути саме boolean `false`, а не `0`, рядок або null. Mono PCM16 WAV перевіряється реально, включно з довжиною sample data, 8–192 kHz і межею 256 MiB. SHA256 перевіряється перед запуском і повторно для окремого тимчасового snapshot.

Ці поля — **запис прийняття від довіреного джерела/оператора, не автоматичне розпізнавання вмісту сигналу**. Підписати приватний чи голосовий запис словом «погода» недостатньо для прийняття в системі. Не передавайте приймальні записи неперевіреним клієнтам для самостійного редагування; daemon не надає RPC, що обминає це правило. Захист voice/no-IQ і military band mask на вході залишається обов'язком приймального data plane.

## Прийняте встановлення та запуск

Запис встановлення — локальний root-owned JSON без group/world write у каталогах із тим самим правилом. Його готує адміністратор після перевірки пакета/збірки, а не завдання декодування:

```json
{
  "v": 1,
  "tool_id": "noaa-apt",
  "version": "1.4.1",
  "source_commit": "48a9eb8321f722634aafd1f9dcf4d80e9bfe274d",
  "executable": "/opt/noaa-apt/noaa-apt",
  "sha256": "ACTUAL_64_LOWERCASE_HEX_SHA256",
  "evidence_id": "admin/reproducible-build-and-package-verification-001"
}
```

Приклад не є чинним приймальним записом. Реальний vendor binary тут не встановлено й end-to-end погодне зображення зовнішнім декодером не отримано.

```sh
PYTHONPATH=software:. python3 -m srrx.decoder_policy plan \
  --preset noaa-apt-weather --source /дані/погодний.wav \
  --metadata /дані/погодний.metadata.json \
  --installation /etc/srrx/noaa-apt.accepted.json

PYTHONPATH=software:. python3 -m srrx.decoder_policy run \
  --preset noaa-apt-weather --source /дані/погодний.wav \
  --metadata /дані/погодний.metadata.json \
  --installation /etc/srrx/noaa-apt.accepted.json \
  --output-directory /результати/новий-сеанс --timeout-s 60
```

Батьківська папка результату має існувати; папка нового сеансу — ще ні. Публікуються лише `weather.png` і `report.json`. PNG перевіряється на структуру/CRC/розміри, ancillary text/EXIF chunks видаляються, решта тимчасових файлів декодера не передається. Це не оцінка правильності метеорологічного зображення. Тести використовують синтетичний PNG та підміну vendor boundary; окремі process tests справді запускають bounded дочірній процес. Вони не видаються за встановлений або випробуваний noaa-apt на Q6A.

## Профіль `satdump-weather` (v2.1, baseband LRPT)

Профіль більше не вимкнений, але його доступність залежить від прийнятого встановлення: без root-owned запису встановлення `availability()` повертає `UNAVAILABLE_NO_ACCEPTED_INSTALLATION`. Рядок самоперевірки RX-S1 приймає офлайн для `satdump-weather` лише `DISABLED_*` або `UNAVAILABLE_*`; для решти профілів із `decoder_gated_presets` — лише `DISABLED_*`. Меж прийому профіль не змінює: SatDump не відкриває SDR. Вхід — лише запис `labrx.run_baseband` за політикою v2.1 ([RX.md](RX.md), розділ «Запис baseband LRPT (v2.1)»).

- **Запис встановлення** (`load_satdump_installation`, root-owned, ≤8 KiB) прив'язує за SHA256 ELF `satdump`, `/usr/lib/libsatdump_core.so` (у ньому більша частина SatDump: модулі конвеєрів, DSP, завантажувач плагінів), точний набір плагінів у `/usr/lib/satdump/plugins`, рівно п'ять файлів у `/usr/share/satdump/resources/pipelines`, дайджест усього дерева `/usr/share/satdump/resources` (`satdump_tree_digest`: SHA256 списку «sha256  відносний шлях» усіх звичайних файлів; symlink чи спеціальний файл — відмова) і пакетний `satdump_cfg.json` з `kepler_update_interval` = «Never». Ім'я файлу плагіна — `lib<каталог upstream>.so`, не похідне від назви опції: на 1aedd60 `PLUGIN_FY2` збирає `plugins/fengyun2_support` (`add_library(fengyun2_support SHARED)`, його CMakeLists.txt:6), тож набір — libmeteor_support, libnoaa_metop_support, libaws_support, libelektro_arktika_support, libxrit_support, libfengyun2_support і libnet_source_support (`.so`). Також запис фіксує версію `2.0.0~alpha+git20260929+lab1`, коміт 1aedd60 і SHA256 рецепта; цей SHA256 звіряється з розгорнутим `/opt/srrx/deployment/recipes/satdump/recipe.json` (`SATDUMP_RECIPE_DIGEST_CHANGED`), тож будь-яка зміна рецепта потребує нового запису зі збирача. Зайвий або відсутній файл — `SATDUMP_FILE_SET_NOT_ALLOWLISTED`; змінений — `SATDUMP_FILE_DIGEST_CHANGED`, `SATDUMP_CORE_DIGEST_CHANGED` або `SATDUMP_RESOURCES_DIGEST_CHANGED`. Поля дайджестів для запису друкує `check_recipe.py package --manifest` (`record_digests`). Перевірка повторюється перед кожним запуском і після `--help`. Каталоги взято з розкладки встановлення 1aedd60: `resources/pipelines` під `share/satdump`, плагіни в `${CMAKE_INSTALL_LIBDIR}/satdump/plugins`. Рецепт задає `CMAKE_INSTALL_LIBDIR=lib`; `receive-only-policy.json` тепер охоплює і цю розкладку.
- **План** (`satdump_plan`): метадані мають точно пройти `srrx.baseband.validate_metadata` (ci16 256 kS/s, Meteor-M N2-3/N2-4, `srrx:export` і `srrx:pinned` = false, UTC перевірено), конвеєр — лише `meteor_m2-x_lrpt` (72k) або `meteor_m2-x_lrpt_80k` (80k). Стоп меж сеансу перевіряється для всієї смуги 137–138 MHz до доступу до встановлення. Шаблон argv: `${ACCEPTED_SATDUMP} pipeline <id> baseband ${APPROVED_BASEBAND} ${OUTPUT_DIR} --samplerate=256000 --baseband_format=cs16`.
- **Запуск** — лише `srrx.satdump_pass.run_decode`. Unit, обмежене читання виводу й видалення baseband після кожної спроби описано в RX.md. `decoder_policy.make_plan` і CLI цього модуля для `satdump-weather` відмовляють (`SATDUMP_PRESET_IS_SATDUMP_PLAN`).
- **Публікація** (`satdump_publish`): з вихідного дерева SatDump беруться лише PNG (≤64, разом ≤256 MiB, кожен ≤64 MiB і ≤40 Мпікс, у порядку шляхів). PNG понад межі або зіпсований пропускається, а не скасовує прохід; звіт рахує їх у `images_skipped_over_limit` і `images_skipped_invalid`. Скільки й яких PNG дає декодування LRPT на 1aedd60, ще не виміряно (фікстура BUILDER). `input_iq_deleted_after_decode` у звіті — те, що викликач справді зробив: `run_decode` спершу видаляє baseband і лише потім публікує. Symlink і спеціальні файли не відкриваються, тексти й EXIF вилучаються. CADU, soft-символи, `products.cbor`, `dataset.json` і журнали лишаються в робочому каталозі, а `run_decode` його видаляє. Стоп меж сеансу перед атомарним перейменуванням не залишає опублікованого результату.

Збірка й перевірки CI (W2 SW-SATDUMP). SatDump збирає збирач +lab (`deployment/recipes/satdump`, схема 2, патчі 0001–0005, важкий job `sr-rx-packages`, двічі в тих самих шляхах); запис збирання CI_BUILT_UNREVIEWED — доказ CI, не рецензія. `runtime_check.py` рецепта на зібраному пакеті в новому chroot без мережі перевіряє: `plugin-set` (`satdump pipeline meteor_m2-x_lrpt --help` відкриває рівно сім плагінів, довідка містить маркери проби `satdump_pass`), `ldd` (RUNPATH лише `/usr/lib/satdump/plugins`, нічого «not found», жодної SDR/USB/аудіо-бібліотеки), `no-connect` (у всіх запусках жодного сокета іншої родини, ніж AF_UNIX, і жодного connect/sendto/sendmsg/bind поза AF_UNIX — як `RestrictAddressFamilies=AF_UNIX` unit декодування), `cli-forms` (`--samplerate=256000` і `--samplerate 256000` на 2 s шуму cs16) і `planted-pipelines-json` (підкладені в усі місця пошуку 1aedd60 файли: `pipelines.json`, `settings.json` і копію `satdump_cfg.json` бінарник читає з робочого каталогу, а `pipelines.json`/`settings.json` — з HOME/.config/satdump, це позитивні контролі; у формі unit — порожній робочий каталог і приватний порожній HOME — жодного з них, хоча сама перевірка стоїть у каталозі й HOME з підкладеними файлами) — модель CI, номери прогонів додає крок доказів. Patch 0005 прибирає завантаження IERS, яке 1aedd60 планує при кожному старті. `omm-csv`: порядок 17 стовпців `srrx.orbits.satdump_csv` збігається з читачем 1aedd60 (`ccsdsOmmToKepler`, хостовий тест), але читач ділить рядок за «,» без лапок, тож рядок з комою в OBJECT_NAME відкидає — OPEN для `srrx.orbits`. Не виконано: декодування фікстури LRPT і `lrpt-cadu-cut` — BLOCKED_NO_LICENSED_FIXTURE (немає запису з зазначеною ліцензією; потрібен стендовий запис власника); `live-localhost` і справжній прохід на Q6A — пристрій.
