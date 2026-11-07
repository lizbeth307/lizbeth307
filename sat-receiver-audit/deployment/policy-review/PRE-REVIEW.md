# РЕЦ-01: досьє попередньої рецензії `receive-only-policy.json` (не рецензія)

Редакція 07.11.2026 (хвиля 2, пакет SYS-HOST). Це робочий матеріал для людини-рецензента рядка РЕЦ-01 ([build/09](../../build/09-testy.md), §19). Досьє підготував агент ШІ. Воно **не є записом рецензії**: статусу політики не змінює, `selftest.py --policy-review` його не читає, і в ньому навмисно немає JSON, який прийняв би `selftest.load_review`. Політика лишається DRAFT, а звіт selftest — не вищим за BLOCKED (`POLICY_NOT_REVIEWED`).

Рішення ([build/15](../../build/15-rishennia-komplektu.md), «Рецензія політики receive-only (W2 SYS-HOST)»): агент може готувати таке досьє, але ніколи не ставить статус REVIEWED і не пише запис рецензії. Причини: (1) потрібних входів ще немає: рецензованих збірок +lab SatDump, SDR++, SDRangel, OpenWebRX+ і Gpredict (група E у HANDOFF) і матриці Phase 0; (2) політику написали ті самі делеговані агенти, тож це була б самоперевірка; (3) build/09 (РЕЦ-01) залишає REVIEWED лише рецензентові. Схема запису допускає чесний рядок ролі рецензента, але вигадати відсутні входи вона не дозволяє.

## Прив'язка

Досьє описує байти політики на базі хвилі 2 (коміт `72ee71b`): `deployment/receive-only-policy.json`, SHA-256 `a1ed869b136cfb02815b7e99b17e87ed76fbab70122c76578ea150ff3b31b2da`, статус DRAFT, 9 приміток (індекси 0–8); `deployment/sources.lock.json`, SHA-256 `2ca1b262b16938742170f389167a728029f0cf7c81a2d734f5a5bf5d83b098c7`. Пакети хвилі 2 додають до політики компоненти (embloader, SDR++, SDRangel, readsb, AIS-catcher, WSJT, Gpredict), тож перед рецензією SHA-256 треба порахувати знову, а для кожної нової чи зміненої примітки — дописати розділ за тим самим зразком.

## Примітки 0–8

### Примітка 0 — імена файлів плагінів і модулів

- **Зараз.** Алоу-листи `components.sdrangel.allow_plugins`, `components.sdrpp.allow_plugins`, `components.satdump.allow_plugins` і `allow_pipelines`, `components.soapy.allow_plugins` (`librtlsdrSupport`, `libairspyhfSupport`) виведено з назв опцій збирання build/07 (рядки 370–430). Для SatDump схему імен файлів узято з рецепта `deployment/recipes/satdump/recipe.json` (статус PENDING_BUILDER: перевірено офлайн, ще не зібрано). CI-збирач +lab зібрав лише `rtlsdr` і `limesuiteng` (прогін sr-rx-packages 42366505294, 07.11.2026); жодного плагіна SDRangel, SDR++, SatDump чи модуля Soapy ще не зібрано.
- **Бракує.** Рецензовані збірки +lab SatDump, SDR++, SDRangel і модулів SoapyRTLSDR/SoapyAirspyHF: `.deb`, записи збірки й `<пакет>.build-manifest.json` зі статусом REVIEWED.
- **Перевірка рецензента.** Для кожного пакета взяти перелік файлів із рецензованого маніфесту збірки (або `dpkg-deb -c <пакет>.deb`) і виписати всі файли в `plugin_dirs` компонента. Кожен зібраний плагін має бути в `allow_plugins` (для SDRangel рядок RX-02 вимагає рівності множин). Кожен запис `allow_plugins`, якого немає в збірці, рецензент прибирає або пояснює. Жодне ім'я не містить токенів `deny_tokens`. Потім `selftest.py offline --profile full` на staged-корені з цими пакетами (як крок «Staged root with the publishable lab packages through selftest --profile full» у `sr-rx-packages.yml`): рядки RX-02, RX-03, RX-04 і RX-06 без FAIL.

### Примітка 1 — ключі налаштувань OpenWebRX+, Gpredict і SatDump

- **Зараз.** `components.openwebrx.locked_settings` (вісім ключів), `components.gpredict.tle_update` (секція `TLE`, ключ `AUTO_UPDATE_FREQ`, значення `0`) і `components.satdump.required_settings` (`kepler_update_interval` = `Never`) узято з build/07 (рядки 386, 431, 508). Агент звірив імена з джерелами закріплених комітів `sources.lock.json` (raw.githubusercontent.com, прочитано 07.11.2026); це попередня звірка, а не рецензія:
  - OpenWebRX+ `luarvique/openwebrx` `f2a8feca`, `owrx/config/defaults.py`: усі вісім ключів є (рядки 360, 361, 363, 409, 413, 418, 447, 489). Типові значення `allow_audio_recording=True` і `allow_chat=True` суперечать політиці, тож `settings.json` пакета має їх перевизначати; решта шість за замовчуванням уже такі, як вимагає політика.
  - Gpredict `csete/gpredict` `1d80049b`: `src/sat-cfg.c:211` — секція `TLE`, ключ `AUTO_UPDATE_FREQ`, типове значення 2 (щотижня); `src/tle-update.h:40` — `TLE_AUTO_UPDATE_NEVER = 0`. `src/radio-conf.h:37` — `RIG_TYPE_RX = 0` (це `rx_only_radio_type` політики).
  - SatDump `SatDump/SatDump` `1aedd602`, `satdump_cfg.json:235-247`: `kepler_update_interval` — параметр типу `options` зі значенням за замовчуванням `1 day` і варіантом `Never`. Отже без зміни конфігурації в пакеті RX-04 дасть FAIL `kepler_update_not_never`; рецепт має постачати `Never`.
- **Бракує.** Рецензовані збірки OpenWebRX+, Gpredict і SatDump та конфігурації, які вони справді встановлюють.
- **Перевірка рецензента.** Повторити звірку вище на тих самих комітах (не на гілці main) і для кожного ключа знайти місце в коді, де його читають, а не лише значення за замовчуванням. Ім'я, тип і значення, що вимикає мережеву функцію, мають збігатися з політикою. Ключ, якого в коді немає, — помилка політики: виправити ключ, а не зняти перевірку. Рядки RX-04, RX-05 і RX-10 на staged-корені із цими пакетами — без FAIL.

### Примітка 2 — модулі SDR++ поза переліком ON

- **Зараз.** Перелік ON build/07 (рядок 406) називає лише джерела (`SOAPY_SOURCE`, `RTL_SDR`, `AIRSPYHF`, `NETWORK_SOURCE`, `FILE_SOURCE`) і `RIGCTL_SERVER` (localhost:4532). Тому інші модулі SDR++ у `components.sdrpp.allow_plugins` не внесено, а рядок RX-03 («ON list only») їх не дозволяє. У `CMakeLists.txt` коміту `8c9f5ee8` (AlexandreRouma/SDRPlusPlus, прочитано 07.11.2026, рядки 12–68) за замовчуванням увімкнено ще, зокрема, `OPT_BUILD_RADIO` (основний демодулятор AM/FM/SSB), `OPT_BUILD_AUDIO_SINK`, `OPT_BUILD_FREQUENCY_MANAGER`, `OPT_BUILD_SCANNER`, `OPT_BUILD_METEOR_DEMODULATOR`, а також модулі з `deny_tokens` (`OPT_BUILD_NETWORK_SINK`, `OPT_BUILD_IQ_EXPORTER`, `OPT_BUILD_RECORDER`, `OPT_BUILD_PAGER_DECODER`, `OPT_BUILD_RIGCTL_CLIENT`, `OPT_BUILD_DISCORD_PRESENCE`). Без радіо й аудіо-виходу SDR++ не демодулює, тож рішення потрібне ще до збирання.
- **Бракує.** Рецензована збірка SDR++ коміту `8c9f5ee8` (build/07, рядок 405) і рішення рецензента щодо кожного модуля, увімкненого за замовчуванням.
- **Перевірка рецензента.** Перелічити всі модулі, які встановлює збірка. Для кожного типового модуля, без якого SDR++ не приймає (наприклад, демодулятор і аудіо-вихід), записати рішення: дозволити (додати в `allow_plugins` з посиланням на джерело) або вимкнути опцією збирання в рецепті. Модуль, що передає дані назовні чи записує IQ (`network_sink`, `recorder`, `iq_exporter`), лишається в `deny_tokens`. RX-03 на staged-корені — без FAIL.

### Примітка 3 — записи `pin_only`

- **Зараз.** Чотирнадцять записів `pin_only` (`qcom-fastrpc*`, `qairt-*`, `libqnn*`, `libsnpe*`, `qnn-tools`, `snpe-tools`, `qcom-adreno*`, `dragonwing-defaults`, `firmware-qcom-audioreach`, `firmware-qcom-soc`, `linux-firmware-qualcomm-misc`, `hexagon-dsp-binaries*`, `firmware-qcom-dsp`, `embloader`) — apt-піни −1 зі STACK.md:892 і build/07 (рядок 132) без заборонених версій. Встановлений пакет дає BLOCKED `pinned_package_present_unreviewed`; у корені A еталонного образу саме так і є (рядок RX-01a, ОБР-03).
- **Бракує.** Матриця Phase 0 (FastRPC 1.0.4-1 чи 1.0.7-3, прошивка DSP 0.2.29 чи 0.2.42; build/09 §11) — стендовий результат на Q6A.
- **Перевірка рецензента.** Після Phase 0 для кожного запису додати `version_rule` з точними версіями, які пройшли матрицю (`allow_only`), і посилання на запис Phase 0. Тоді RX-01a на корені A дає PASS для цих пакетів, а будь-яка інша версія — FAIL. Без Phase 0 запис лишається BLOCKED.

### Примітка 4 — ключі SDR++ `directSampling` і `biasT`

- **Зараз.** `engine_config_rules`: ключі режиму прямої дискретизації `directsamplingmode` і `directsampling` мають бути 0, будь-який ключ bias заборонено навіть зі значенням false (STACK.md:888). Джерело коміту `8c9f5ee8` (`source_modules/rtl_sdr_source/src/main.cpp`, AlexandreRouma/SDRPlusPlus, прочитано 07.11.2026) пише й читає саме `devices.<назва>.directSampling` (рядки 203, 224–225, 419) і `devices.<назва>.biasT` (рядки 205, 232–233); `directSamplingMode` — лише ім'я змінної в коді. Це звірка джерела, а не збірки.
- **Бракує.** Рецензована збірка SDR++ `8c9f5ee8` і конфігурація, яку вона створює під час першого запуску.
- **Перевірка рецензента.** Повторити звірку джерела; на збірці запустити SDR++ з порожнім каталогом конфігурації (без пристрою) і порівняти записаний JSON з `engine_config_rules`. Модуль пише `biasT` у конфігурацію щойно створює запис нового пристрою (рядки 200–205) і коли оператор перемикає bias у GUI (рядок 480), тож рецензент вирішує, як пакет уникає цього ключа (патч модуля чи конфігурація без запису), бо RX-01c забороняє ключ bias навіть зі значенням false. RX-01c на корені з цією конфігурацією: PASS, коли режим 0 і ключа bias немає; FAIL — на копії з `biasT: false`.

### Примітка 5 — `IPAddressDeny=any` в юнітах оренди

- **Зараз.** Рядок RX-12 вимагає від юніта оренди `IPAddressDeny=any` поряд з `IPAddressAllow=localhost`. Підстава: systemd.resource-control(5) systemd v255 (github.com/systemd/systemd, тег v255, прочитано 07.11.2026) застосовує правила по черзі — адреса з `IPAddressAllow=` дозволена, інакше адреса з `IPAddressDeny=` заборонена, інакше дозволена; отже сам `IPAddressAllow=` нічого не обмежує. Юнітів оренди в репозиторії ще немає (`system_files.tmpfiles`: каталоги оренд — OPEN для пакета юнітів оренди).
- **Бракує.** Юніти оренди (пакет SW-LEASE хвилі 2) і рядок DEVICE RX-12-runtime на Q6A.
- **Перевірка рецензента.** Прочитати ту саму сторінку man для версії systemd цільового образу (255.4-1ubuntu8.12, факти образу) і переконатися, що порядок правил не змінився. Кожен юніт оренди на staged-корені — RX-12 PASS. На Q6A: з процесу оренди з'єднання на не-localhost адресу відхиляється (RX-12-runtime).

### Примітка 6 — порядок каталогів системних юнітів

- **Зараз.** `units.system_unit_paths`: `etc/systemd/system.control`, `etc/systemd/system`, `etc/systemd/system.attached`, `usr/local/lib/systemd/system`, `usr/lib/systemd/system`, `lib/systemd/system`. Це постійна частина шляху пошуку з systemd.unit(5) v255 (розділ «System Unit Search Path», той самий тег); каталоги `/run` (`system.control`, `transient`, `generator*`, `system`, `system.attached`) — стан роботи, і офлайн їх не інвентаризують.
- **Бракує.** Нічого з групи E; потрібна лише звірка на корені цільового образу.
- **Перевірка рецензента.** На завантаженому корені образу (QEMU-модель або Q6A, systemd 255) виконати `systemd-analyze unit-paths` і порівняти з переліком політики без `/run`. На noble з об'єднаним `/usr` каталог `lib` очікувано є посиланням на `usr/lib`, і тоді `lib/systemd/system` збігається з `usr/lib/systemd/system`; рецензент підтверджує це на образі або прибирає зайвий запис. Те, що офлайн-результат охоплює лише постійну конфігурацію, лишається приміткою; на пристрої це закриває RX-12-runtime.

### Примітка 7 — правило `require_lab_build`

- **Зараз.** `deploy.LAB_BUILD` приймає версію, що закінчується на `+labN` або на `-0labN` (N ≥ 1), і те саме правило застосовують `deploy.py doctor` і selftest RX-01a (`deploy.version_forbidden`). `publish.sh` приймає лише файли `*+lab[1-9]*_arm64.deb` і `*-0lab[1-9]*_arm64.deb`. У lock gr-satellites має версію `5.10.0~git20260922-0lab1`, рецепт rtlsdr — `2.0.3-0+lab1`.
- **Бракує.** Версії всіх рецензованих збірок групи E.
- **Перевірка рецензента.** Для кожного запису збірки звірити поле версії з правилом (закінчення `+labN` чи `-0labN`) і з версією в lock; перевірити, що жоден пакет noble з тією самою назвою не проходить правило (наприклад, `2.0.1-2build1` без `+lab` — FAIL). Тести `deployment/tests` на `version_forbidden` мають покривати обидві форми.

### Примітка 8 — запасна збірка librtlsdr2

- **Зараз.** `librtlsdr2` має `allow_only` = `2.0.3-0+lab1` (build/07, рядок 86); запасна збірка `2.0.1-2build1+lab1` (build/07, рядок 262) не дозволена. CI зібрав `2.0.3-0+lab1` за рецептом `rtlsdr` (прогін sr-rx-packages 42366505294, CI-модель).
- **Бракує.** Рецензований запис збірки `rtlsdr` (статус REVIEWED, аудит джерел і TX negative tests) і рішення, чи потрібна запасна збірка взагалі.
- **Перевірка рецензента.** Звірити SHA-256 `.deb` з рецензованим записом збірки й lock. Якщо рецензент вирішить дозволити запасну збірку, — додати її версію в `allow_only` лише разом з окремим рецептом і записом збірки; інакше примітку закрити рішенням «лише 2.0.3-0+lab1». RX-01a і RX-09 на корені з пакетом — PASS.

## Решта РЕЦ-01 (поза примітками)

build/09 (РЕЦ-01) вимагає ще: компоненти readsb, AIS-catcher і WSJT у політиці (пакети SW-ADSB, SW-AIS, SW-WSJT хвилі 2); `version_rule` для записів `pin_only` (примітка 3); звірку меж голосових смуг DRAFT `VOICE_BANDS_HZ` (`software/srrx/voice_mask.py`) і відкриті питання розділу про маску голосу в [SPECTRUM.md](../../software/SPECTRUM.md). Для кожного з них потрібне те саме: джерело, прочитане рецензентом, і рішення, записане в політиці.

## Як рецензент оформлює запис

Запис рецензії — окремий файл JSON поза цим каталогом. `selftest.load_review` прив'язує його до точних байтів політики й lock, які прочитав selftest (`policy_sha256` запису порівнюється з SHA-256 прочитаного файла політики, `deployment/selftest.py`, `load_review`), тож будь-яка зміна політики після запису, зокрема сам статус REVIEWED, робить запис `NOT_BOUND`. Тому порядок такий:

1. Рецензент вносить у `deployment/receive-only-policy.json` усі правки й ставить у ній `status` REVIEWED. Це остання зміна політики перед записом.
2. Рахує SHA-256 саме цих байтів політики і `deployment/sources.lock.json` (`sha256sum`) і пише запис з полями, які задає `load_review`: `schema_version` 1; `status` REVIEWED; `policy_sha256` і `source_lock_sha256` — ці два SHA-256; `reviewer` — ім'я або роль без адреси e-mail (до 128 символів, без `@`); `reviewed_on` — дата YYYY-MM-DD; `builds` — непорожній перелік рецензованих результатів збірки з унікальними назвами і SHA-256; `notes` — рівно одна непорожня відповідь на кожен індекс приміток політики.
3. Запускає `python3 deployment/selftest.py offline … --policy-review <запис>`. Очікування: `policy_status` = REVIEWED, `policy_review.status` = BOUND і в `blockers` немає жодного `POLICY_*` (`POLICY_NOT_REVIEWED`, `POLICY_REVIEW_RECORD_NOT_BOUND`, `POLICY_REVIEW_RECORD_MISSING`).

Будь-яка пізніша зміна політики чи lock потребує нового запису за тими самими кроками. Ні агент, ні CI цих кроків не виконують.
