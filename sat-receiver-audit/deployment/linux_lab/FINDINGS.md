# Linux lab — виправлення та передача ПЗ 0.3.1

> **23.10.2026:** нижче — стан і результати ARM64 run07 від 20.10.2026. Після нього змінено виконані джерела (зокрема `software/srrx`, тести, `deployment/module_lab`, `guest_smoke.py`), тому run07 — лише запис попереднього прогону; повторний ARM64 прогін ще потрібен. Поточні [модульні результати](../../verification/module-lab/MODULE-RESULTS.md) перегенеровано 23.10.2026 на хості x86_64 (750 refs / 64 збірки / 166 інтерфейсів; 40 PASS, 0 FAIL, 126 CONNECTION_MODEL_ONLY; 3737/3737 topology/fault scenarios). Поточна хостова регресія — 432 тести, 431 PASS, 1 SKIP ([звіт](../../verification/software-tests.json)).

Стан на 20.10.2026: production-виправлення нижче внесені, хостова регресія має **421 виявлений тест: 419 PASS, 2 SKIP**. [Машинний звіт](../../verification/software-tests.json) містить причини SKIP: відсутня справжня QNN HTP SDK library та заборонений у хостовому середовищі AF_UNIX socket для одного service-тесту. SKIP не зараховані як PASS.

**ARM64 run07: PASS, QEMU exit 0**, 1434.289 s. Ubuntu24.04.5 aarch64, kernel6.8.0-147-generic, systemd PID1. Усі вісім наборів завершені: **420 PASS / 1 SKIP із 421** регресій, **14** systemd scenarios, **9** PTY cases, **2** GUI failure cases, XCB/Xvfb, **5** native RX worker cases, **5** virtual-block storage cases та **6** module domains. Єдиний ARM64 SKIP — справжня QNN HTP SDK library відсутня. [Первинні результати](../../verification/linux-lab/README.md) імпортовані після штатного poweroff; `source-binding.json` зв'язує **86** виконуваних джерел із guest manifest. Попередні невдалі/перервані спроби збережені окремо в [linux-attempts](../../verification/linux-attempts/README.md).

Модульні результати run07 (ARM64): **754 refs / 64 збірки / 166 інтерфейсів**. Функціонально: **40 PASS, 0 FAIL, 126 CONNECTION_MODEL_ONLY**; окремо всі **166** interfaces мають CONNECTION_MODEL_PASS, виконано **3749/3749** topology/fault scenarios. XCB observer отримав **267** успішних samples, **0** transport misses; найбільший проміжок без sample — **0.574 s**. Це виміряна вибіркова перевірка, не твердження про безперервний стан між samples. Опис середовища й відтворення — [README](README.md); деталізація моделей — [module lab](../module_lab/README.md).

## Що виправлено у production-коді

### SerialLink: termios EIO має потрапляти до безпечної межі Engine

Після паузи Engine понад 100 ms викликає `discard_input()`, щоб старі UART-байти не стали свіжим статусом. При HUP Linux може повернути EIO із `tcflush()`. У використаному CPython `termios.error` не є `OSError`, тому старий exception міг оминути обробник транспортної відмови Engine. Помилка під час часткового налаштування UART також могла залишити відкритий FD.

[SerialLink](../../software/srrx/link.py) тепер перетворює `termios.error` на `OSError` зі збереженими errno і cause. `discard_input()` скидає frame decoder у `finally`, а конструктор закриває FD при будь-якій помилці налаштування, зберігаючи початковий тип cancellation. [Engine](../../software/srrx/engine.py) отримує помилку через свій чинний транспортний обробник: програмно знімає ARM, вимикає керовані виходи та залишає trip активним після відновлення трафіку.

Точні регресії у [test_serial_link.py](../../software/tests/test_serial_link.py):

- `test_discard_eio_preserves_errno_cause_and_drops_partial_frame`;
- `test_constructor_closes_fd_at_each_termios_failure_boundary`;
- `test_constructor_cancellation_still_closes_without_reclassifying`;
- `test_delayed_engine_tick_flush_eio_latches_all_outputs_off`.

[pty_smoke.py](pty_smoke.py) окремо працює зі справжніми Linux PTY/termios та переносною моделлю Supervisor. Це не перевірка електричного UART6, GP17/Q306 або фізичного watchdog. Опис `tcflush` — у [Python termios](https://docs.python.org/3/library/termios.html).

### RX worker: раптовий EOF має бути чистою помилкою захоплення

Після смерті native worker `Pipe.poll()` може показати готовність, а `recv_bytes()` — підняти `EOFError`. Раніше цей тип міг вийти за публічну межу помилок CLI. [WorkerSource.read](../../software/srrx/labrx.py) тепер повертає `OSError("RX worker pipe closed before a complete block")` із початковим EOF як cause. Чинний `run_capture()` закриває source і в `finally` запитує OFF RX-гілки; CLI завершується контрольованою відмовою без запису неповного спектра.

Регресія [test_receivers.py](../../software/tests/test_receivers.py) — `test_actual_pipe_eof_is_clean_oserror_after_capture_cleanup_and_cli_refusal`: використовується справжній закритий multiprocessing pipe, перевіряються його закриття, OFF request, відсутність файлів і відсутність traceback у CLI. Електричне виконання OFF цим не доведене.

### RX privacy: одного RLIMIT_CORE=0 недостатньо

Linux ігнорує `RLIMIT_CORE` для core dump, переданого через pipe зовнішньому collector: це прямо описано в [Linux core(5)](https://man7.org/linux/man-pages/man5/core.5.html). Тому лише нульовий ліміт не обґрунтовує твердження, що crash dump із RAM/IQ неможливий.

[_disable_worker_core_dumps](../../software/srrx/labrx.py) встановлює `RLIMIT_CORE=(0,0)`, викликає `PR_SET_DUMPABLE=0` і вимагає підтвердження `PR_GET_DUMPABLE==0`. Будь-яка відмова зупиняє RX. У hardware capture parent проходить цю перевірку **до ControlGuard і створення source**, бо parent теж тримає IQ/FFT buffers. Його dumpability не відновлюється після cleanup: звільнена пам'ять може зберігати samples. Child перевіряє захист перед завантаженням драйвера й повторно після його ініціалізації, до першого read. Simulation не змінює dumpability parent. Семантика Linux — [PR_SET_DUMPABLE](https://man7.org/linux/man-pages/man2/pr_set_dumpable.2const.html).

Цільовий хостовий набір [test_receivers.py](../../software/tests/test_receivers.py) має **21 PASS**; це Receiver/Capture/WorkerCorePrivacy тести, не 21 окреме фізичне випробування. Ключові перевірки:

- `test_worker_privacy_guard_precedes_driver_load_and_first_read`;
- `test_preload_privacy_failure_never_opens_driver`;
- `test_post_init_privacy_failure_closes_driver_without_reading`;
- `test_parent_privacy_failure_never_observes_control_opens_source_or_writes_output`;
- `test_real_capture_parent_is_nondumpable_before_source_and_remains_so_after_cleanup`;
- `test_failed_set_failed_get_and_still_dumpable_all_refuse`.

[rx_worker_smoke.py](rx_worker_smoke.py) компілює незалежний native ABI fixture і запускає справжній WorkerSource process. Хостовий [звіт](../../verification/host-native/rx-worker-smoke.json) має **5 PASS**: `driver_error`, `hang_ignoring_sigterm`, `crash_sigsegv`, `invalid_odd_short_read`, `valid_even_short_read`. Для `crash_sigsegv` фактичний exit code — **−11 (SIGSEGV)**, публічна помилка — `OSError`, worker закрито, OFF request спостережено, до native read підтверджені нульові core limit і dumpable. Це запуск x86_64 Linux, не ARM64 або фізичний SDR. Його sandbox не надав `/proc/sys/kernel/core_pattern`: стан системного collector на хості не вгадується. Захист спирається на підтверджені process attributes, а не лише відсутність файла `core` у робочій папці. У run04 цей самий harness також пройшов усі 5 сценаріїв на ARM64, з `crash_sigsegv` exit −11 та перевіреними process attributes, хоча загальний run04 був FAIL через окремий system smoke. Повтор run05 теж підтвердив цей набір; фінальний run07 завершив його з PASS.

### StorageGuard: явна прив'язка до змінного носія

Новий opt-in [StorageGuard](../../software/srrx/storage.py) підключено до [labrx](../../software/srrx/labrx.py) і [spectrum persistence](../../software/srrx/spectrum.py). CLI приймає пару `--storage-root`/`--storage-device`: наявний точний mountpoint і явно вказаний block device. Guard звіряє `/proc/self/mountinfo`, FD `mnt_id`, `st_dev`, inode каталогу та identity пристрою; підміна mount із тим самим `st_dev` теж відкликає поточну сесію. Нові output parent directories не створюються. Після втрати/підміни/помилки сесія відкликається назавжди; повернення носія потребує нового явного guard. Автоматичного запису на rootfs немає.

Запис використовує pinned dirfd, `O_NOFOLLOW`, staging, перевірку identity перед replace і atomic bounded copy+append для JSONL. ENOSPC або втрата mount **до commit** залишають попередній файл незмінним. Перша filesystem-помилка зберігає початковий `OSError`/errno; наступні звернення дають `StorageRevoked`. Це не гарантія проти зникнення живлення після commit, privileged mount manipulation або стороннього процесу, який має право змінювати той самий output directory. Guard сам не форматує, не монтує й не вмикає живлення носія. Linux metadata — [proc filesystem](https://www.kernel.org/doc/html/latest/filesystems/proc.html).

Точні регресії у [test_storage.py](../../software/tests/test_storage.py): `test_mount_id_replacement_same_st_dev_is_rejected`, `test_partial_enospc_preserves_previous_atomic_and_jsonl_files`, `test_mount_loss_after_staging_before_commit_preserves_previous_file`, `test_parent_symlink_swap_after_staging_is_rejected`, `test_capture_storage_loss_closes_source_and_requests_branch_off`.

[storage_smoke.py](storage_smoke.py) перевіряє реальний Linux mount, bind replacement, ENOSPC і lazy unmount на окремому 64 MiB virtual ext4 block `SRRXT7` усередині dedicated guest. Він не відкриває host storage і не підтверджує Samsung T7 USB firmware, ресурс або throughput. Run04 фактично пройшов усі 5 storage-сценаріїв, хоча його загальний статус був FAIL через окремий system smoke. Повтор run05 теж підтвердив цей набір; фінальний run07 завершив його з PASS.

## Що було виправленням harness, а не production-помилкою

| Спостереження | Виправлення перевірки та збережена вимога |
|---|---|
| PNG encoding/перший Qt layout міг сам спричинити прострочений UI heartbeat до запланованого SIGSTOP | [gui_smoke.py](gui_smoke.py) робить screenshots лише disarmed/SAFE; потім очікує природний heartbeat реального window worker і свіжий service poll, лише наступною timer-дією ARM. Час heartbeat вручну не переписується, production lease не послаблено. |
| XCB process уже стартував, але його вікно ще не відображене або перший frame порожній | [xcb_smoke.py](xcb_smoke.py) шукає mapped вікно за фактичним spawned CLI PID через `_NET_WM_PID` і повторює screenshot до обмеженого deadline з тими самими вимогами до зображення. Сам факт sleep/process start не зараховується як готовність. |
| System smoke створював новий Python process для кожного RPC; під TCG зайве навантаження спричинило коректний GPIO-stale trip до shutdown RPC | [guest_smoke.py](guest_smoke.py) використовує один persistent helper під перевіреним labclient UID/group, але новий справжній AF_UNIX connection для кожного запиту. Pipes/socket мають розмірні та часові межі, helper гарантовано reaped; mutating requests не replay. Lease scenario вимагає саме `owner lease expired`, а shutdown записує конкретну фазу відмови. Production 250 ms GPIO freshness і решта timers збережені. |
| PTY fixture покладався на readable/фіксовану паузу та надсилав HELLO лише раз на session | [pty_smoke.py](pty_smoke.py) спостерігає повну kernel queue через FIONREAD, підтверджує прийняття останнього frame перед replay baseline та поточну TRIPPED session перед recovery. Peer повторює HELLO кожні1000ms у SAFE/TRIPPED/OFF, як firmware; дев’ятий сценарій навмисно втрачає перший HELLO і перевіряє resync без ARM. Real clock, production timers і HUP лишилися чинними; failures мають структурний trace. Mutation once-only HELLO справді відмовила, але точну причину старого run05 timeout без trace не приписуємо заднім числом. |
| Один read-only Unix status запит XCB observer перевищив1s під час холодного Qt startup | [xcb_smoke.py](xcb_smoke.py) повторює лише визначені transport misses в межах чинного загального deadline дочірнього процесу. Unsafe/rejected/malformed відповіді та permission/missing socket одразу FAIL; initial/final і post-child successful probes обов’язкові. Report показує кількість успішних samples, timeouts і gaps; пропущена відповідь не підтверджує readiness або безперервно безпечний стан. |
| ENOSPC scenario спочатку очікував `StorageRevoked` на першій помилці запису | [storage_smoke.py](storage_smoke.py) перевіряє справжній початковий `OSError` з errno ENOSPC, незмінність попереднього запису і permanent revocation; `StorageRevoked` очікується на наступному зверненні. Production contract не змінено заради PASS. |

## Переносимість автономного комплекту

Під час перевірки розпакованого комплекту в іншому каталозі launcher виявив відсутній порожній directory target для `tools/root/usr/share/misc/magic → ../file/magic`. Початковий host-only builder включав файли, symlinks та їхні parent directories, але губив порожні каталоги. `build_kit.py` тепер записує runtime directories в manifest, включає їх до tar та звіряє точну множину/режим каталогів. Launcher перевіряє їх до symlink resolution. Це виправлення пакування; воно не змінює виконані guest/model джерела або результати run07. Переносимість підтверджується окремими `--verify-only` і `--prepare-only`, а не повторним завантаженням VM.

## Незмінні межі

Усі **37 апаратних воріт OPEN** (з 23.10.2026 додано E5-10 — W1-2 WIFI_PWR_EN), hardware release **BLOCKED**. Generic ARM64 Linux VM не є Q6A kernel/DT/driver image. Фізичні UART/I²C/GPIO, RF/аналогові тракти, заряд/BMS, температура/калібрування, реальні touch/HDMI/USB і фізичний OFF ще не прийняті. Повний Lime SDK/backend, гарантований тракт 56 MS/s, кваліфікований QNN HTP, весь каталог декодерів та затверджений цільовий системний образ залишаються прогалинами. Наявність пакета MicroPython source не означає UF2/runtime build або прошитий пристрій. Вихідний Git remote раніше повернув HTTP 403; пізніше редакцію опубліковано (див. [RESTORE-GIT](../../RESTORE-GIT.md)).

Connectivity `CONNECTION_MODEL_PASS` означає виконані topology/fault scenarios проти KiCad XML. Він не перетворює непокритий драйвер на `EMULATION_PASS`, не закриває DNP/TBD gates і не підтверджує фізичні pinouts. Відкриті умови J102/E1-02, IP2368/E1-01, Wisecoco/E3-02/E5-01 та DC polarity/DC block Boni мають залишатися у видимих row details звітів.

## Відтворення перевірки та пакування

Команди нижче виконуються з кореня `sat-receiver-audit` і описують відтворення. Поточний run07 завершено та імпортовано; наступне виконання потребує нового work-каталогу. Пакувальник і незалежний validator відхиляють неактуальні hashes та неповний ZIP.

1. Для нового запуску дочекатися завершення VM. Перевірити його `report.json`: загальний PASS, `qemu_exit_code=0`, архітектура aarch64, усі очікувані suites, `physical_tests_performed=false`, `hardware_qualified=false`. Не імпортувати проміжні логи як PASS. Поточний run07 має саме ці terminal значення.
2. Імпортувати execution evidence і source binding. `finalize_linux_lab.py` вимагає нових `verification/linux-lab` та `verification/module-lab` каталогів; якщо існують старі результати, спершу окремо зберегти їх, не змішувати прогони.

```sh
python3 tools/finalize_linux_lab.py --work /tmp/srrx-linux-lab-run07
python3 tools/build_documents.py
python3 tools/build_firmware.py
python3 tools/build_bundle.py
python3 -B tools/check_bundle.py
```

`build_bundle.py` вимагає актуальних host regression, Linux/module PASS, точних hashes виконаних Python/shell/service джерел, module inventory/models/графів і CAD verification. Виправлення production/model Python після підготовки guest потребує нового виконання guest; не переписувати source binding вручну. Якщо змінено джерела хостових перевірок або readiness contract, повторити `python3 tools/run_tests_offline.py` перед bundle. Якщо змінено схеми, спочатку повторити CAD export/перевірки за [KiCad README](../../build/kicad/README.md).

Виняток для середовища без ARM64 lab: якщо виконаний код змінено, а новий guest-прогін неможливий, `build_bundle.py` пакує лише тоді, коли сам проєкт позначає `verification/linux-lab/project-manifest.json` як `RECORD_OF_EARLIER_RUN` (а README Linux-результату має відповідне попередження). Тоді HTML показує окреме попередження «лише запис попереднього прогону» з кількістю змінених виконаних файлів і архітектурою поточного module-lab прогону. Решта перевірок (host regression, module inventory/models/графи, CAD) залишаються суворими; source binding вручну не переписується.

3. Переглянути `git status --short`, додати лише призначені до передачі джерела/звіти, виконати `git diff --cached --check` та створити локальний commit. Після нього сформувати патч усіх локальних комітів від точної Claude-бази:

```sh
git format-patch --stdout 465318835e71eae326059f5f66e2b47232169556..HEAD | gzip -n > /tmp/SR-RX-v2.1-git.patch.gz
gzip -t /tmp/SR-RX-v2.1-git.patch.gz
```

Patch відображає лише commits до HEAD, тому його не будувати до commit поточних змін. Інструкція застосування — [RESTORE-GIT](../../RESTORE-GIT.md). Відмова remote push не заважає віддати ZIP і patch, але не є успішною публікацією.

4. Після фінального ZIP створити offline kit. Наведені assets/tools — поточні локальні caches; на іншому хості їхні шляхи слід замінити. `--output` має бути новим `.tar.zst` поза checkout, а його parent directory має вже існувати.

```sh
python3 deployment/linux_lab/build_kit.py \
  --assets /workspace/scratch/63085b43f730/linux-lab-assets \
  --tools /workspace/scratch/63085b43f730/linux-lab-tools \
  --project-zip SR-RX-v2-project.zip \
  --output /tmp/SR-RX-Linux-Lab.tar.zst
```

Builder звіряє signed/locked inputs та кожний archive payload hash. Його PASS означає цілісність kit; він **не завантажує guest**. Після розпакування використовуйте `launch.py --verify-only`, потім новий workspace для `--prepare-only` або повного запуску. Kit не містить попередній writable overlay як runnable input і стартує з pinned base image; це окрема перевірка від cached run07. Фінально звірити manifest/CRC архівів, додати checksums і передати project ZIP/HTML, Git patch та offline kit із фактичними verification reports.
