# ARM64 Linux lab без фізичної Q6A

Це окрема Ubuntu 24.04 ARM64 VM з власним Linux-ядром і systemd, запущена QEMU TCG на `virt-8.2`. Вона не використовує KVM, host mounts, host USB/UART/I²C або мережеву карту. Зв’язок усередині VM — справжні Unix sockets, PTY і окремі процеси Linux. Контрольовані навантаження та Pico залишаються моделями SIMULATION.

Опис нижче визначає середовище та команди відтворення. Факт успішного ARM64 виконання, лічильники й результати окремих сценаріїв підтверджує лише `report.json` конкретного run-каталогу; готовий launcher сам по собі не є результатом тесту.

Ціль Q6A використовує інше ядро/DT/драйвери. Generic ARM64 guest перевіряє ABI, встановлення, процеси та системну інтеграцію. Він не підтверджує GPIO, ADC, фізичний watchdog, RF, HTP, нагрів, швидкість 56 MS/s чи час реакції реальної плати. Жодного приймального PASS для пристрою не створюється.

## Відтворення на Linux

Потрібні Python 3, `curl`, `gpgv`, довірені Ubuntu cloud-image та archive keyrings (`ubuntu-cloudimage-keyring.gpg` і `ubuntu-archive-keyring.gpg`), `dpkg-deb`, `tar`, `mke2fs` та `debugfs`. Не запускати `guest_bootstrap.sh` безпосередньо: його місце — лише всередині цієї VM. QEMU, qemu-img і genisoimage — тільки wrappers `bin/` одного каталогу, створеного `fetch_tools.py` (або `tools/` автономного комплекту): `host.py prepare` відхиляє системні QEMU та будь-який інший файл, бо лише ці wrappers запускають locked ld.so з `--inhibit-cache`, без host `ld.so.cache`; фактичні завантаження під час прогону аудит перевіряє тільки для `qemu-system-aarch64` (див. нижче). Launcher не встановлює пакети й не змінює служби хоста.

Із кореня повного проєкту:

```sh
python3 deployment/linux_lab/fetch_tools.py --dest /tmp/srrx-qemu-tools
python3 deployment/linux_lab/fetch_assets.py --dest /tmp/srrx-arm64-assets
python3 deployment/linux_lab/host.py prepare \
  --assets /tmp/srrx-arm64-assets --work /tmp/srrx-arm64-run \
  --qemu /tmp/srrx-qemu-tools/bin/qemu-system-aarch64 \
  --qemu-img /tmp/srrx-qemu-tools/bin/qemu-img \
  --genisoimage /tmp/srrx-qemu-tools/bin/genisoimage
python3 deployment/linux_lab/host.py run --work /tmp/srrx-arm64-run
```

Ці самі кроки з тими самими locked tools/assets виконує ручний CI-job `linux-lab` workflow «SR-RX verification» на GitHub-hosted Linux x86_64 (`gh workflow run sr-rx-verify.yml --ref ccr-1537979d-cj7q9t -f linux_lab=true`); він переносить попередній імпорт у `verification/linux-attempts/<archive_as>` (`archive_as` необов'язковий: без нього — наступний вільний `runNN`), викликає finalizer і віддає `lab-evidence.patch` артефактом, нічого не комітячи. Перед підготовкою guest job доводить хостові докази до нерухомої точки, а після finalizer перебудовує й перевіряє документи та bundle ([FINDINGS](FINDINGS.md#відтворення-перевірки-та-пакування)). Кожна підготовка потребує нового run-каталогу; його абсолютний шлях не може містити пробілів або ком. Assets можна повторно використати: download helper перевіряє locked SHA256/size. `host.py prepare` перевіряє підпис `SHA256SUMS` і те, що locked hashes Ubuntu image, kernel та initrd справді містяться в підписаних `SHA256SUMS`; `wheelhouse-requirements.txt`/`wheelhouse-manifest.json` у assets мають байтово збігатися з lock проєкту, а в payload потрапляє саме lock проєкту. Wheelhouse містить лише CPython 3.12/aarch64 або pure-Python wheels, з exact PyPI hashes; інсталяція в guest — `--no-index --require-hashes --force-reinstall` у новоствореному venv. Архів джерел записує власника root, guest розпаковує його без збереження host UID/прав, тож дерево `/opt/srrx` належить root. Після poweroff host відхиляє symlink або спеціальні файли в `results/` до читання `summary.json`. Базовий образ, tools і пакети є тестовим lock, а не повним прийнятим образом Radxa OS.

Ізоляцію самого QEMU від бібліотек хоста перевіряють двічі. Статично: `fetch_tools.py` і ще раз `host.py prepare` проганяють locked `ld.so --inhibit-cache --list` не лише для трьох програм, а й для кожного розпакованого модуля `usr/lib/x86_64-linux-gnu/qemu/*.so`, які QEMU завантажує через dlopen із `QEMU_MODULE_DIR`; бібліотека поза locked root, `not found` чи порожній каталог модулів зупиняють підготовку. Ubuntu QEMU 8.2 із module upgrades шукає відсутній модуль ще й у `/var/run/qemu/Debian_1_8.2.2+ds-0ubuntu1`; якщо такий каталог на хості є, prepare відмовляє. `run.json` (`qemu_runtime`) записує SHA256 closure трьох програм (`program_libraries_sha256`), кількість модулів і SHA256 їхнього closure (`closure_sha256`). Під час прогону: `host.py run` задає `SRRX_LOADER_AUDIT`, і wrapper вмикає `LD_DEBUG=files,libs` лише для locked ld.so (glibc 2.39), якому передає керування через `exec`, а не для host `/bin/sh` чи `dirname`. Після зупинки host розбирає журнали `loader-audit/qemu.<pid>`: кожен відображений об'єкт, зокрема завантажені через dlopen NSS/gconv/plugins, має лежати в locked tools root, інакше `run` повертає 1; журнал без самого `qemu-system-aarch64` вважається порожнім доказом і теж відхиляється. Підсумок — `qemu-loaded-objects.json` і `report.json` → `host.loader_audit`; finalizer імпортує лише прогін із чистим, непорожнім аудитом. Аудит охоплює лише процес `qemu-system-aarch64` з `host.py run`: `qemu-img` і `genisoimage`, які в prepare створюють overlay та ISO, перевірено тільки статично, а вміст payload guest однаково звіряє за SHA256 з `payload-manifest.json`. Для цього командного рядка (`-display none`, `-nodefaults`, `-nic none`, вбудовані virtio-blk-pci і TCG) очікуваний перелік dlopen порожній; статична перевірка покриває майбутні зміни `-device`/`-display`.

Прив'язка джерел (`source-binding.json`) охоплює також `design/readiness-contract.json`: guest звіряє його `gate_results` зі staged шаблоном, а finalizer вимагає, щоб `system-smoke.json` записав той самий SHA256 контракту і щоб кожен інший прив'язаний файл цього запису збігався з прив'язкою (`smoke_attests`). Контракт є приймачем хостових лічильників тестів і не містить жодного поля, похідного від прив'язки чи стану Linux lab, тож циклу hash не виникає; сам `verification/software-tests.json` не прив'язується.

VM має 4 vCPU Cortex-A76, 3 GiB RAM і 10 GiB sparse qcow2 overlay над незмінним базовим образом. Seed/payload ISO доступні тільки для читання. Результати пишуться в окремий 128 MiB virtual disk; після poweroff launcher читає їх через debugfs. Ще один 64 MiB ext4 virtual block із міткою `SRRXT7` призначений лише для storage-сценаріїв: це не емуляція Samsung USB/T7 firmware. У work-каталозі зберігаються `console.log`, `run.json`, `report.json`, `loader-audit/`, `qemu-loaded-objects.json`, `results/` та overlay VM. Запуск за замовчуванням обмежений 30 хвилинами (`host.py run --timeout` задає секунди); host не виконує guest `poweroff`. Прогін із `--base-overlay` перевстановлює всі locked DEB і wheels під TCG і триває приблизно як чистий, тому для нього задавайте `--timeout 3600`, як launcher комплекту; перевищення ліміту дає помилку без PASS.

За потреби `host.py prepare` приймає `--base-overlay /tmp/previous-run/guest.qcow2` від попереднього завершеного, вимкненого ARM64 lab guest. Це повторне використання OS, а не запуск із чистого образу. Поруч із overlay потрібен попередній `report.json` зі статусом PASS або FAIL (summary записано) і `qemu_exit_code=0`; ABORTED/перервані прогони відхиляються. `run.json` записує SHA256 попереднього звіту, його статус і код QEMU, а також увесь backing chain (`qemu-img info --backing-chain`) із SHA256 кожного шару; нижній шар має збігатися із locked Ubuntu image. Cloud-init instance-id щоразу новий, тому runcmd не пропускається. Не переміщуйте й не змінюйте backing image, доки новий overlay від нього залежить. Кешованим залежностям guest не довіряє: усі locked DEB перевстановлюються без `--skip-same-version`, venv створюється заново з `--force-reinstall` усіх wheels, а `dependency-verification.json` підтверджує, що встановлені версії точно збігаються з обома lock. Перед smoke-наборами в цьому позначеному guest фіксовані lab-шляхи unit-файлів (`srrx.service`, увесь `srrx.service.d`, simulation unit) і п’ять записів `/etc/srrx` видаляються безумовно, хоч би ким їх створено; захист guest_smoke від перезапису ловить лише стан, створений уже після bootstrap. Поточне дерево джерел щоразу пакується заново з manifests, встановлюється замість попереднього й перевіряється за розмірами/SHA256; усі поточні набори тестів виконуються повторно. Старі результати не зараховуються до нового запуску.

## Що запускається

- Повний unittest набір із NumPy, справжнім Qt offscreen і ONNX Runtime на ARM64. Test harness перед import вимикає ORT telemetry та забороняє Internet sockets свого процесу; локальні Unix sockets дозволені. Підсумок guest приймає лише задокументовані SKIP поза locked wheelhouse (відсутні QNN HTP SDK library та PyMuPDF), кожен не більше одного разу; будь-який інший SKIP, зокрема NumPy/Qt/ONNX/compiler, робить загальний стан FAIL.
- `guest_smoke.py`: системні сценарії — installed entrypoints з іншої робочої папки, staging/hash checks, обмежене очікування device units (`systemd_device_wait_bounded`: drop-ins, згенеровані `deploy.py`, на тимчасових unit-файлах із вузлом `/dev/lab/srrxabsent`, якого немає; timeout 3 s, перезапуски не доходять до `start-limit-hit`; назви звірено із `systemd-escape`), systemd hardening, відмова production unit без записів/із OPEN записами (саме exit 2 release guard, а не 216/GROUP: bootstrap створює системну групу `srrx-pico` без членів, labclient до неї не входить), kernel peer UID, lease/fault/link-loss/shutdown і crash/restart. Fault, link-loss і lease вимагають точної першої причини trip (`active-low fault: FAULT_LNA1`, `pico_status_timeout`, `owner lease expired`). Simulation unit лишається SAFE для GUI. Фактичну кількість беріть зі звіту виконання.
- `pty_smoke.py`: справжній termios 115200, фрагментація, CRC/oversize, replay/session, HUP, bounded TX і explicit recovery. Peer відправляє кадри за `TelemetrySchedule` із `firmware/pico/main.py` (STATUS при зміні стану або кожні 200 ms, HELLO кожні 1000 ms у SAFE/TRIPPED/OFF); HUP-сценарій записує фактичну причину trip і приймає лише транспортний OSError або 500 ms status deadline.
- `gui_smoke.py`: реальне Qt-вікно від окремого unprivileged UID, SIGSTOP/SIGCONT/SIGKILL, точна причина lease expiry, OFF/reset і відсутність auto-ARM; PNG та JSON.
- `xcb_smoke.py`: справжній Qt XCB backend через локальний Xvfb без TCP listener, production меню та live Unix IPC від unprivileged UID; окремі PNG/JSON. Це Linux X11-перевірка, фізичний HDMI/display/touch залишаються неперевіреними.
- `rx_worker_smoke.py`: справжні native ARM64 C fixtures без USB/network, окремий WorkerSource process, error/hang/crash/short-read, bounded cleanup. Failure-сценарії проходять лише з публічною помилкою `OSError`/`ValueError`/`RuntimeError` (hang — саме `TimeoutError`). Guard навмисно підмінений локальним component fixture; це не доказ physical acceptance або повного live-control guard.
- `storage_smoke.py`: справжній guest-only ext4 block, production recording CLI у `--simulate`, device identity/mount ID, ENOSPC зі збереженням попереднього запису і втрата mount без переходу на root filesystem. Фізичні USB, T7 firmware та power sequencing не перевіряються.
- `module_lab/run.py`: шість окремих domain processes, звірка актуальних source snapshots та pins/value, функціональні моделі й окремі connectivity fault-сценарії. JSON/HTML/Markdown та журнали зберігаються в `results/module-lab/`.

Симуляційна служба ніколи не вмикає hardware backend. Справжній `srrx.service` перевіряється лише негативно; відсутні/OPEN записи не перетворюються на accepted. Capture parent і RX worker до доступу до приймача встановлюють нульовий RLIMIT_CORE та перевірений PR_SET_DUMPABLE=0; це також блокує piped core collector. Raw IQ не записується. Знімки offscreen не доводять роботу фізичного дисплея або touch.

## Окрема перевірка кожного модуля

[Module lab](../module_lab/README.md) зіставляє незалежні Power/MCU/Radio/Location/I/O моделі з поточними схемними refs; шостий набір Connectivity окремо перевіряє динамічну модель nets проти KiCad XML та внесені opens/shorts/NC faults. Звірка охоплює 750 refs і 166 деталізованих інтерфейсів, а функціональне покриття обліковується окремо. Таблиця показує як виконані сценарії, так і `UNSUPPORTED` функції та інтерфейси без функціональної моделі. Наявність 750 refs у реєстрі не означає 750 реалізованих функціональних емуляторів.

У підготовленому guest із повним деревом `/opt/srrx` і його venv команду можна виконати окремо:

```sh
PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen \
  /opt/srrx/venv/bin/python3 /opt/srrx/deployment/module_lab/run.py \
  --project /opt/srrx --output /tmp/srrx-module-run-001
```

Каталог результатів має бути новим/порожнім. На виході — `report.json`, `module-results.html`, `MODULE-RESULTS.md`, шість domain JSON і журнали. Цю саму команду можна виконати у власному Linux-середовищі із залежностями за інструкцією module lab; архітектура фактичного запуску записується у звіт і не підміняється ARM64. Runner обмежує кожний domain process 600 s і відхиляє застарілі сім source snapshots або невідповідні pins/value в inventory.

Загальний `EMULATION_PASS_WITH_GAPS` означає успішне виконання записаних наборів, **разом із відкритими прогалинами**. Для окремого ref `EMULATION_PASS` підтверджує лише пов'язані успішні функціональні моделі; решта функцій може бути `UNSUPPORTED`. `CONNECTION_MODEL_PASS` підтверджує тільки записані топологічні перевірки й не підвищує функціональний `CONNECTION_MODEL_ONLY` до `EMULATION_PASS`. Окреме JSON-поле `connection_status` показує результат з'єднань. `EMULATION_FAIL`/`FAIL` або domain `CONNECTION_MODEL_FAIL` — помилка перевірки чи запуску. Всі фізичні модулі залишаються `NOT_TESTED`, `hardware_qualified=false`.

GPSD API тут представляє незалежний сервер на 127.0.0.1, а не встановлений справжній gpsd. Це реальні локальні TCP sockets без NIC чи інтернету; відповідний набір запускається окремим процесом **поза** `run_tests_offline.py`, чий seccomp filter забороняє AF_INET/AF_INET6. LC76G NMEA й UTC-reference сценарії використовують синтетичні координати/час. MCU register models не виконують інструкцій RP2040, USB descriptor fixtures не емулюють kernel USB, а native SDR ABI fixtures не емулюють RF або заводську прошивку.

## Автономний комплект

`SR-RX-Linux-Lab.tar.zst` містить перевірені image/kernel/initrd, tools, guest DEB/wheels, повний ZIP проєкту й launcher. Розпакувати на Linux x86_64 зі збереженням executable bits і symlinks, потім із каталогу комплекту:

```sh
python3 launch.py --verify-only
python3 launch.py --prepare-only --work /tmp/srrx-offline-prepare
python3 launch.py --work /tmp/srrx-offline-run
```

Кожен `--work` має бути новим каталогом поза комплектом, без пробілів і ком. Потрібні Python 3.10+, `gpgv`, `mke2fs`, `debugfs` та `/bin/sh`; інсталяція пакетів і завантаження з мережі не виконуються. Комплект починає з незмінного базового образу; архівний run07 явно записав OS/dependency cache попередніх VM і його DEB/wheels не перевстановлював; пізніші прогони (CI run 40016984543 — з чистого образу, `base_overlay: null`) і cached-прогони перевстановлюють і перевіряють locked залежності. `--verify-only` підтверджує цілісність, `--prepare-only` — підготовку, а фактичне виконання підтверджує тільки звіт завершеної VM. Стандартний ліміт launcher — 3600 s. [Виправлення, результати й повна процедура перепакування](FINDINGS.md).

## Первинні джерела

- [QEMU ARM system emulation](https://www.qemu.org/docs/master/system/target-arm.html)
- [QEMU virt platform](https://www.qemu.org/docs/master/system/arm/virt.html)
- [Ubuntu 24.04 signed image release 20261017](https://cloud-images.ubuntu.com/releases/noble/release-20261017/)
- Exact Ubuntu/PyPI URLs, SHA256 та provenance — у сусідніх lock/manifest файлах.
