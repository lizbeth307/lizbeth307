# Розгортання SR-RX-v2.1: відтворюваний staging, випуск заблоковано

`deployment/` реалізує read-only doctor, перевірку джерел/кешу, патчування точних vendor-джерел у нову копію, rootfs staging, відтворюваний tar.gz та генерацію кандидатів BLS A/B. Скрипти не запускають apt, systemctl enable/start, udev reload, bootctl, прошивання, монтування чи розмітку диска. Усі фізичні ворота залишаються OPEN. Створений архів — кандидат для перевірки, а не прийнятий образ Q6A.

Чинні електричні вимоги — `design/E1.json`–`E5.json` і `build/12-revision-v2.1.md`; версії та обмеження сторонніх програм — `build/07-pz-vstanovlennia.md`. Старі команди зміни системи в build07 не виконуються цим пакетом.

## Команди, які вже працюють

З кореня репозиторію:

```sh
sh deployment/build.sh --check
sh deployment/test.sh
python3 deployment/deploy.py doctor > /tmp/srrx-doctor.json
python3 deployment/deploy.py stage --dest /tmp/srrx-stage
python3 deployment/deploy.py bundle --stage-dir /tmp/srrx-stage --output /tmp/srrx-stage.tar.gz
```

Doctor повертає код2 для невідповідного цільового середовища. На цьому x86_64 host це очікуваний BLOCKED, а не результат приймання Q6A. Він читає `/etc/os-release`, DT/DMI, dpkg і lsblk; з прив’язками — атрибути sysfs/udevadm. Він не сканує I²C, не відкриває SDR і не надсилає дані UART.

`--check` перевіряє синтаксис, source lock і фактичне застосування патчів у тимчасових копіях точних upstream-файлів. `test.sh` окремо перевіряє негативні сценарії й компілює витягнуті guard-умови Lime на host C++; це не повна збірка Lime SDK на arm64.

Staging потребує нового каталогу поза checkout і системними префіксами. Повторний запуск у той самий каталог відхиляється. `bundle` перевіряє точний `stage-files.json`, відхиляє сторонні/змінені файли, обнуляє час/owner у tar і час gzip; однакові staged bytes дають однаковий SHA256. Архів не має install/postinst-скриптів.

## Ціль і прив’язки пристроїв

Ціль: Radxa Dragon Q6A, aarch64, Radxa OS r2 Ubuntu noble, ядро `6.18.2-4-qcom`, BIOS260120. Вибір іншого ядра або дистрибутива потребує нової редакції й приймання. Номери `/dev/i2c-N` не вгадуються.

1. Зберегти копію `deployment/devices.template.json` поза репозиторієм.
2. На Q6A перевірити pinmux, aliases і відповідність кожної I²C-шини її OF node; заповнити **окремі** `ina228` та `control` paths/`of_fullname`.
3. Pico прив’язати або до спостереженого platform UART parent, або до USB VID/PID/повного серійного номера. У USB-режимі platform parent має бути null. Потрібен стабільний `/dev/lab/pico`.
4. RTL-A/B — лише LABRXA/LABRXB; HF+ — точний сирий USB serial, включно з `AIRSPYHF SN:`. EEPROM ці скрипти не змінюють. Фізичний запасний RTL-C не отримує доступу автоматично.
5. Lime `enabled=false`; сирий PCIe-шлях не видається. Зовнішній S-band вузол та TX навантаження визначає схема, а не udev.

```sh
python3 deployment/deploy.py udev --devices /path/to/observed-devices.json > /tmp/70-srrx-serial-bound.rules
python3 deployment/deploy.py doctor --devices /path/to/observed-devices.json > /tmp/srrx-q6a-doctor.json
python3 deployment/deploy.py stage --dest /tmp/srrx-q6a-stage --devices /path/to/observed-devices.json
```

Udev-правила — кандидат, який ще треба порівняти з `udevadm info` на справжньому Q6A. Шаблон із null не проходить перевірку. Правила не використовують wildcard serial, `0666` або `uaccess`; це не замінює майбутню оренду USB descriptor єдиним data-plane процесом. GNSS/PPS потребують окремого прийнятого overlay й прив’язок із build07; цей контролер їх автоматично не встановлює.

## Джерела й offline-відтворюваність

`deployment/sources.lock.json` зберігає30 компонентів початкового плану, точні версії/refs, підтверджені full commits та причини блокування. Для20 refs підтверджено офіційний repository API. `source_archive_sha256=null` означає, що байти повного архіву ще не отримані/не затверджені. SHA1 git commit/blob не підміняє SHA256 архіву. Жоден хеш із старого тексту не позначено перевіреним без первинного підтвердження.

Первинні release asset metadata підтвердили SHA256 для Radxa r2 UFS4096 image та п’яти kernel/meta-deb активів6.18.2-4. Фактичних великих binary downloads у цій сесії не було: `verify-cache` має перевірити отримані байти й розмір. Повний список — lock, разом із точними URL й шляхами кешу.

```sh
python3 deployment/deploy.py verify-cache --cache /srv/srrx-cache
# Вузька перевірка одного source-компонента теж вимагає всіх core image/kernel bytes:
python3 deployment/deploy.py verify-cache --cache /srv/srrx-cache --component rtlsdr
# Перевірка вже отриманих source bytes без заяви про наявність core image/deb:
python3 deployment/deploy.py verify-cache --cache /path/to/srrx-upstream-cache --sources-only --component rtlsdr --component limesuiteng
```

Повний cache check зараз BLOCKED:11 source archive SHA256 залишаються null; деякі refs/пакування не закріплені. Для19 повних pinned tarballs реально отримано bytes і записано SHA256/size/URL; серед них Lime, RTL, HF+, SatDump, SDR++, Soapy, gr-satellites та декодери. SDRangel перевищив128MiB acquisition cap і залишається null; великого base image download не було. `slowrx-daemon` за наведеним у STACK репозиторієм/комітом повернув primary404 і вимкнений. Virgo3.8.9 за перевіреними варіантами tag також не підтверджено. URL джерел LA9310/UART та QAIRT не вгадуються — у lock вони null до перевірки. Вимоги Python/wheelhouse, FastRPC/firmware Phase0 і build toolchain зафіксовано в `deployment/dependencies.json`; відсутні точні транзитивні версії/хеші залишені OPEN.

Підготовка offline release на окремому arm64 builder:

1. Отримати лише зафіксовані image/deb/source refs з їхніх первинних джерел, разом з licenses, git submodules та історією потрібних cherry-picks. Не використовувати `latest`.
2. Зберегти довірений Ubuntu/Radxa keyring і його fingerprint, підписані InRelease/Release, Packages/Sources індекси та всі транзитивні `.deb`; перевірити `gpgv` і кожний hash з підписаного індексу. Ключ довіряють через окремо перевірений fingerprint, а не через файл із того самого неперевіреного архіву.
3. Записати реально отримані SHA256/size в нову reviewed редакцію lock. Не переносити припущені хеші. Для Python — окремі CPython3.12/aarch64 wheelhouse й повний `--require-hashes` lock, включно з транзитивними пакетами; GNU Radio/numpy не підтягувати довільним pip upgrade.
4. Для кожного +lab рецепта — власний sbuild/chroot, pinned compiler/CMake/dependencies, локальне дзеркало без мережевого fallback, `SOURCE_DATE_EPOCH` від коміту. SDK/DKMS/NPU прошивки — лише після Phase0 matrix, без змішування наборів. Цей репозиторій ще не містить повної підписаної apt-публікації або всіх build recipes.
5. Двічі зібрати в незалежних chroot, порівняти результат; пояснити різниці, якщо binary reproducibility не досягнута. Створити SBOM/file allowlist, source/build logs та signed aptly snapshot; приватний ключ не класти в пристрій чи репозиторій.
6. Перевірити cache відключеним від мережі, зібрати candidate rootfs, перевірити exact file list і negative TX tests. Hash забезпечує цілісність, а не правдивість журналу вимірювань чи автентичність автора.

Окремий файл `SR-RX-vendor-sources.zip`, переданий поруч з основним комплектом, містить ці19 перевірених архівів і їхній manifest. Розпакувати його у власний cache root, щоб отримати `sources/`. Це джерела залежностей, а не встановлений образ, wheelhouse або повний офлайн-реліз.


## Реальні vendor-патчі та їхня межа

```sh
sh deployment/build-vendor.sh --check
python3 deployment/vendor_patch.py --component limesuiteng --source /path/to/clean-pinned-LimeSuiteNG --output /tmp/lime-patched
# Повний отриманий архів теж підтримується: перевірка SHA256/size, bounded safe extraction, target/post hashes.
python3 deployment/vendor_patch.py --component limesuiteng --archive /path/to/srrx-upstream-cache/sources/limesuiteng.tar.gz --output /tmp/lime-from-archive
# На ізольованому builder з уже встановленими pinned залежностями:
sh deployment/build-vendor.sh limesuiteng /path/to/clean-pinned-LimeSuiteNG /tmp/lime-build-candidate
sh deployment/build-vendor.sh rtlsdr /path/to/clean-pinned-rtl-sdr /tmp/rtl-build-candidate
```

Скрипт перевіряє повний HEAD, чистий checkout включно з ignored build files, recursive submodule status і SHA256 кожного target file, копіює джерела в нове місце, застосовує patch та перевіряє очікувані post hashes. Для archive input перевіряється весь SHA256/size і pinned root, без потреби в `.git`. Вихідні дані не змінюються. CMake/build/install виконуються непривілейованим користувачем через окремий user+network namespace (`unshare --user --map-root-user --net`) без мережевого fallback; якщо namespaces недоступні — STOP. `FETCHCONTENT_FULLY_DISCONNECTED=ON` додатково вимикає FetchContent downloads; відсутня залежність означає помилку, а не установлення apt. `DESTDIR` Lime і ручне копіювання лише RTL shared library пишуть у candidate workdir. Сценарій відхиляє build від host root; ізольований builder/chroot залишається передумовою.

Lime37cb183: TX `setupStream` відхиляється до allocation/configuration; `writeStream` не містить compiled TX body; Micro native Configure/StreamCreate відхиляють TX; UploadTxWaveform вимкнений, Calibrate(Tx) відхиляється. Вимкнено CLI/GUI/Amarisoft/GNU Radio/HDSDR. Патч застосувався до точних офіційних файлів, guard-тести пройшли. **Повний SDK не доведено receive-only:** raw register/SPI/I²C/inherited APIs і внутрішні калібрування потребують окремого аудиту; arm64 build, TXEN0x0020 після configure/calibrate, firmware й кондуктивний leakage test не виконані. `verify-build` явно відхиляє Lime runtime library. RX56MHz hardware path не перевірений; backend залишається вимкненим. Наявність50Ω навантаження не робить software audit завершеним.

RTL797f814: GPIO0 ON завжди повертає EPERM; GPIO5 та OFF працюють як раніше; best-effort GPIO0 OFF додано в open/close; SOVERSION2 відновлено за первинним7ebcb041 diff. Рецепт використовує `ENABLE_ZEROCOPY=OFF`, `DETACH_KERNEL_DRIVER=ON`, перевіряє SONAME,37 exports і відсутність zero-copy text. Усі executable tools, включно з rtl_tcp/rtl_eeprom/rtl_biast, не встановлюються цим вузьким рецептом. **Свідоме суворіше обмеження:** labd token bridge для GPIO0 ще немає; антени використовують зовнішні захищені інжектори схеми. API тест OFF/перемикання V4L і EEPROM default-off лишаються апаратними воротами.

AirspyHF: у підтверджених1.6.8 source/header немає bias-tee API; типова noble1.6.8-4build1 із SONAME1 не замінена upstream make install. Патч для неіснуючої функції не вигадувався. Опційний Airspy Mini й нові AirspyHF API не отримують автоматичного дозволу. Підтверджені джерела/хеші/ліцензії описані в `deployment/UPSTREAM-REVIEW.md`.

## Перевірка candidate і системні служби

```sh
python3 deployment/deploy.py verify-build --prefix /path/to/candidate-prefix --manifest /path/to/reviewed-build-manifest.json
python3 deployment/deploy.py release-guard --devices /path/to/observed-devices.json --acceptance /path/to/accepted-unit.json --release /path/to/reviewed-release.json --build-manifest /path/to/reviewed-build-manifest.json --cache /srv/srrx-cache
```

Build manifest починається OPEN, не генерує PASS. Після незалежного source audit/negative tests reviewer фіксує exact SHA256 кожного файла й `.so`, докази та `REVIEWED`. Невідомий файл, відомий TX plugin/tool чи недозволена Lime library викликає BLOCKED. Це перевірка reviewed allowlist та відомих заборон; універсального доведення відсутності TX через пошук назв немає. Системні `.so` драйверів додатково зв’язує приймальний manifest/receiver guard власного ПЗ; скан одного prefix не охоплює весь rootfs.

Candidate містить існуючі `srrx.service`/`srrx-poweroff.service`, drop-ins з `ExecStartPre` release guard, шаблони без приймання і, лише за явним config, devices.env/udev candidate. Немає `.wants` symlinks чи автоматичної активації. `srrx-poweroff` може викликати вимкнення ОС лише після свідомого запуску qualified release; під час staging він не працює.

Опційний `srrx-menu.service` кладеться **окремо в `usr/lib/systemd/user/`**, не до системних служб. Його не вмикають автоматично. Labd користується `/usr/bin/python3` і stdlib; touch GUI потребує ізольованого `/opt/srrx/venv` із NumPy/PySide6. Широкі extras bounds у pyproject не є locked wheelhouse: для випуску зафіксувати exact compatible wheels, транзитивні залежності, build tools і SHA256 на CPython3.12/aarch64. Не змішувати GUI venv з GNU Radio/numpy системного пакування або NPU venv.

На цільовій машині **після** перевірки signed offline package/wheel cache й приймання, вручну reviewable план:

```sh
# Ці інсталяційні команди є планом; staging їх не запускає.
python3 -m venv /opt/srrx/venv
/opt/srrx/venv/bin/python3 -m pip install --no-index --find-links=/srv/srrx-cache/wheels --require-hashes -r /path/to/reviewed-hmi-requirements.lock
/opt/srrx/venv/bin/python3 -m pip install --no-index --no-build-isolation --no-deps '/opt/srrx/software[hmi]'
```

Перший hashed lock має вже містити NumPy/PySide6 і всі залежності, а також зафіксовані setuptools/build prerequisites для локального project build. Другий крок встановлює перевірене дерево `/opt/srrx/software[hmi]` без мережі чи resolver-заміни залежностей. Unit використовує `/usr/bin/env /opt/srrx/venv/bin/python3`; до створення/аудиту venv user menu не запускається. Доступ до controller socket і hardware readiness лишаються політикою labd. Наповнення venv змінює reviewed file list: фінальний build manifest формують після цього кроку.

План встановлення після всіх приймань: offline signed package repository → перевірка Release/Packages і package hashes → зупинений контролер і підтверджений Pico safe/reset → вручну reviewed install candidate в неактивний слот → окремо локальні unit acceptance/devices/release records із належними власником/правами → повторні doctor/release guard і bench rollback tests → лише тоді контрольоване enable/start. Ці дії потребують реального Q6A й не виконуються цими скриптами. Приймання не копіюється з шаблону й не запозичується з іншого hardware_unit_id/Pico serial. Групи labd/lab, /run права й least-privilege policy перевіряють перед запуском; udev candidate сам користувачів не створює.

Під час MCP reset CHG_INHIBIT плаває: апаратна зарядка за KSD/NTC може працювати при вимкненій Q6A. Лише після safe initialization контролер задає CHG_INHIBIT=1. Software deployment не обіцяє утримувати заборону зарядки в reset.

## A/B і відновлення — тільки кандидати

```sh
python3 deployment/deploy.py stage-ab --config /path/to/observed-ab-config.json --dest /tmp/srrx-ab-candidate
```

`deployment/ab.template.json` має null для PARTUUID/kernel/initrd/merged-DTB paths і не проходить перевірку. Після заповнення generator створить stable current-slot entry, `+3` trial для іншого слота та rescue entry, з явними linux/initrd/devicetree; поточний default не змінюється. Це **не інсталятор завантажувача**. Type#1/EFI-stub/initramfs/DTB firmware й фактичний rollback потребують bench test; жодний конфіг не слід переносити в ESP до перевірки шляхів і rescue medium.

Початковий план UFS: native4K, ESP1GiB, rootA/rootB по22GiB, решта /data. Перед операціями з розміткою/BIOS — два однакових повних SPI32MiB dumps, recovery media, зафіксовані UEFI/pinmux/base cmdline, перевірка4K geometry і резервна копія. Образ UFS4096 відрізняється від512. Ні ці параметри, ні generator не дозволяють автоматичне repartition/flash. У build07 збережено RouteB fallback; його write-back механізм теж не впроваджено цим пакетом.

## Що конкретно залишається до повного образу

| Частина | Стан |
|---|---|
| Controller staging, doctor, templates, deterministic bundle, patch application/guard tests | Реалізовано; host tests |
| Q6A image/kernel release digests | Первинні metadata підтверджені; bytes/cache ще перевірити |
|19 із30 повних source archives отримано/хешовано;11 ще unresolved, transitive apt/wheelhouse/toolchain lock | Offline full suite залишається BLOCKED |
| Повні +lab privacy/build recipes SDRangel/SatDump/OpenWebRX/readsb/AIS та їхні fixtures | План build07; не підмінені generic name scan |
| Lime native/raw TX audit, SDK arm64,56MHz/RAM/thermal/PCIe/firmware | OPEN, runtime disabled |
| Phase0 FastRPC/QAIRT/firmware/DKMS/EDID/PPS, A/B rollback, physical installation | OPEN |
|36 фізичних blocking gates і двоточкова ADC/branch калібровка | Жодного PASS не створено |
