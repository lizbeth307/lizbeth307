# Рецепти пакетів +lab і CI-збирач

Редакція 24.10.2026. Тут лежать рецепти, з яких CI збирає `.deb` пакети `+labN` для SR-RX-v2.1, і два інструменти збирача. Збирання — це доказ CI, а не рецензія збірки: жоден крок не ставить `REVIEWED`, не підписує випуск і не замінює стендові ворота. Апаратні ворота лишаються OPEN.

## Як працює збирач

Workflow `.github/workflows/sr-rx-packages.yml` (ручний запуск, вхід `lab_builds`, типово `rtlsdr,limesuiteng`) виконується на нативному arm64 (`ubuntu-24.04-arm`) і для кожного рецепта:

1. `deployment/fetch_sources.py fetch` потоково завантажує архів джерел із `deployment/sources.lock.json` і приймає його лише після збігу SHA-256 і розміру; `deploy.py verify-cache --sources-only` перевіряє кеш ще раз, а `fetch_sources.py tree` — що вміст архіву дорівнює дереву закріпленого коміту (`git_tree_sha1`).
2. `lab_build.py` (від root, лише на одноразовому CI-збирачі) створює **новий** chroot noble arm64 через `mmdebstrap --variant=buildd` зі знімка `snapshot.ubuntu.com`, дата якого записана в lock (`apt_snapshot.timestamp`, зараз `20261020T000000Z`). Підписи індексів apt перевіряються ключем з `apt_snapshot.keyring`. У chroot є лише набір buildd, `python3`, `git`, `cmake`, `pkgconf` і `build_depends` рецепта; кожен рецепт отримує власний chroot (build/07, розділ 2: окремий chroot на кожен пакет +lab).
3. Збирання запускається командою `unshare --net --mount --pid` → `chroot --userspec=1000:1000` з порожнім оточенням. У новому мережевому просторі немає жодного інтерфейсу, крім loopback; `build_recipe.py` спершу пробує з'єднатися із зовнішньою адресою і зупиняється, якщо з'єднання вдалося.
4. `build_recipe.py` розпаковує точний архів (з рецензованим патчем — через `vendor_patch.py`, який ще раз звіряє SHA-256 архіву й цільових файлів), виконує `cmake` з параметрами рецепта, перевіряє, що **кожну** опцію `option()`/`cmake_dependent_option()` upstream, яку обчислила ця конфігурація, рецепт задав явно (неперевірених значень за замовчуванням немає), збирає, розкладає файли за пакетами, виконує перевірки рецепта і пакує `.deb` через `dpkg-deb --root-owner-group` з часом `SOURCE_DATE_EPOCH` архіву.
5. З `repeat` (типово увімкнено) рецепт збирається вдруге в тих самих шляхах; `<id>.reproducibility.json` порівнює SHA-256 `.deb`. Друга незалежна машина-збирач лишається окремою перевіркою.
6. `deployment/repo/check_repo.py packages` звіряє кожен `.deb` із записом збірки, розпаковує його і порівнює дерево з маніфестом пакета; `deploy.verify_build` має відмовити, бо маніфест OPEN.
7. Пакети публікуються в тимчасовий репозиторій aptly, підписаний **тестовим** ключем, який існує лише в цьому job, і перевіряються `deploy.py verify-repo` та випадками підробки ([repo/README.md](../repo/README.md)).

Результати CI (артефакти з терміном 14 днів): `.deb`, `<пакет>.build-manifest.json` (схема `verify_build`, status OPEN), `<id>.build-record.json`, журнал збирання, список пакетів chroot (`<id>.chroot-packages.txt`, його SHA-256 є в записі збірки) і порівняння відтворюваності.

## Схема `recipe.json`

Ключі точні (`build_recipe.validate_recipe`, тести `deployment/tests/test_recipes.py`):

| Ключ | Зміст |
|---|---|
| `schema_version` | 1 |
| `component` | id з `sources.lock.json` із закріпленим архівом upstream (не пакет Ubuntu з `debian_source`) |
| `summary`, `notes` | опис і обґрунтування відхилень від upstream за замовчуванням |
| `source.patch` | `null` або лише `deployment/patches/<component>-rx-only.patch` |
| `build_depends` | назви пакетів noble для chroot |
| `cmake.configure` | argv, що починається з `cmake -S {src} -B {build}` |
| `cmake.options` | кожна опція upstream, значення `ON`/`OFF` |
| `cmake.variables` | інші змінні CMake; `FETCHCONTENT_FULLY_DISCONNECTED=ON` обов'язково |
| `build` | список argv; дозволені програми — лише `cmake`, `make`, `ninja`; URL і ввімкнення завантажень відхиляються |
| `install` | або `cmake_install: true`, або явний список `copy` з `{src}`/`{build}` у відносний шлях пакета |
| `packages` | `name`, `section`, `description`, `files` (glob), `depends` (`{version}` — версія з lock), `shlibs_depends` (`dpkg-shlibdeps`) |
| `drop` | файли, які свідомо не пакуються, кожен із причиною |
| `checks` | `soname`, `export_count`, `forbid_strings`, `forbid_paths`, `require_paths` |

Плейсхолдери: `{src}`, `{build}`, `{destdir}`, `{jobs}`. Кожен файл із `DESTDIR` має належати рівно одному пакету або бути в `drop`; невідомий файл зупиняє збирання. Назва пакета, яку забороняє `receive-only-policy.json` (наприклад `wsjtx`, `limesuiteng-cli`, `gr-limesuiteng`), відхиляється ще до збирання. Версія пакета завжди дорівнює `version` компонента в lock (`+labN` або `-0labN`).

## Чинні рецепти

| Рецепт | Пакети | Головне |
|---|---|---|
| `rtlsdr` | `librtlsdr2`, `librtlsdr-dev` 2.0.3-0+lab1 | патч RX-only, `ENABLE_ZEROCOPY=OFF`, `DETACH_KERNEL_DRIVER=ON`, лише ціль `rtlsdr`; перевірки SONAME `librtlsdr.so.2`, 37 експортів `rtlsdr_*`, відсутність тексту zero-copy, жодних `rtl_tcp`/`rtl_biast`/`rtl_eeprom` |
| `limesuiteng` | `liblimesuiteng`, `limesuiteng-soapysdr`, `limesuiteng-dev` 25.1.0+git37cb183+lab1 | патч, що відхиляє TX; опції `build-vendor.sh` збережено, кожну з 41 опції дерева задано явно; модулі ядра LA9310 — окремі компоненти DKMS |

Префікс пакетів — `/usr` і multiarch-каталог `aarch64-linux-gnu`, а не `/opt/srrx-vendor` кандидата `build-vendor.sh`: пакет `librtlsdr2` має замінити noble 2.0.1 там, де його завантажують споживачі. Пакування — `dpkg-deb` з рецепта, а не каталог `debian/` noble; перенесення того пакування лишається за рецензентом. Пакети `-dev` потрібні лише chroot-ам інших рецептів і в образ пристрою не входять.

## Межі

- CI-збирання доводить лише те, що рецензований патч компілюється й пакується на arm64 з закріпленими залежностями. `deploy.verify_build` і далі відхиляє будь-яку бібліотеку Lime, доки повний аудит native/raw TX не стане REVIEWED.
- Статус запису збірки — `CI_BUILT_UNREVIEWED`, перевірки — `CI_PASS`. Це не апаратний PASS і не рецензія.
- Інструменти хоста (`mmdebstrap`, `aptly`, `gpg`) беруться з apt раннера і не закріплені; закріплено вміст chroot. Їхні версії записуються в `host-tools.txt`.
- Для перевірки інтеграції CI розпаковує зібрані пакети в staged root (`deploy.py stage`) разом із `lab.pref` і записом apt і запускає `selftest.py offline --profile full` лише як звіт. Прогін 24.10.2026 (run 40113667357): RX-06 і RX-08 дають FAIL на модулі Soapy і бібліотеці Lime — саме так, як вимагає політика, доки Lime вимкнено; RX-16 приймає структуру `lab.pref`; решта рядків BLOCKED, бо SatDump, SDR++, SDRangel, OpenWebRX+, Gpredict, прошивок і записів пристрою ще немає.
- Новий рецепт (SatDump, SDR++, SDRangel та інші) додається як `deployment/recipes/<id>/recipe.json` за цією схемою; дерево `deployment/recipes/` прив'язане до доказів лабораторії Linux (`tools/finalize_linux_lab.py`), тож файли `debian/` без розширення теж не лишаються неприв'язаними.
