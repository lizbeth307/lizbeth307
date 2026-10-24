# Linux lab — виправлення та передача ПЗ 0.3.1

> **Ревізія 23.10.2026.** Після run07 змінено production-код, моделі модулів, harness і графи (виправлення findings, пункти плану A–D, злиття гілки `ccr-1537979d-cj7q9t`; див. [HANDOFF](../../HANDOFF.md#ревізія-23102026-claude-перевірка-виправлення-ci-план)). Тому run07 нижче — історичний доказ для джерел 20.10.2026; його первинні результати перенесено без змін до [linux-attempts/run07](../../verification/linux-attempts/run07/). Наступний ARM64 run виконано 23.10.2026 у CI (workflow «SR-RX verification», тоді з `-f linux_lab=true -f archive_as=run07`, GitHub run 40016984543) для джерел до злиття з `ccr-1537979d-cj7q9t`: **PASS**, QEMU exit 0; його звіт і прив'язка джерел імпортовано в [verification/linux-lab](../../verification/linux-lab/README.md), модулі — у [verification/module-lab](../../verification/module-lab/MODULE-RESULTS.md). Після злиття змінено виконувані джерела й графи, тому той імпорт перенесено в [linux-attempts/run08](../../verification/linux-attempts/run08/), а чинний ARM64 run для об'єднаних джерел виконано 24.10.2026 (GitHub run 40043380590): **PASS**, QEMU exit 0 ([звіт](../../verification/linux-lab/README.md)). Наступний запуск: `gh workflow run sr-rx-verify.yml --ref ccr-1537979d-cj7q9t -f linux_lab=true`; без `archive_as` job переносить попередній імпорт у наступний вільний `verification/linux-attempts/runNN`. Лічильники нижче, що стосуються run07, описують джерела 20.10.2026.

Стан на 20.10.2026: production-виправлення нижче внесені, хостова регресія має **421 виявлений тест: 419 PASS, 2 SKIP**. Тодішній машинний звіт (`verification/software-tests.json` редакції 20.10.2026, є в історії Git) містив причини SKIP: відсутня справжня QNN HTP SDK library та заборонений у хостовому середовищі AF_UNIX socket для одного service-тесту. SKIP не зараховані як PASS.

**ARM64 run07: PASS, QEMU exit 0**, 1434.289 s. Ubuntu24.04.5 aarch64, kernel6.8.0-147-generic, systemd PID1. Усі вісім наборів завершені: **420 PASS / 1 SKIP із 421** регресій, **14** systemd scenarios, **9** PTY cases, **2** GUI failure cases, XCB/Xvfb, **5** native RX worker cases, **5** virtual-block storage cases та **6** module domains. Єдиний ARM64 SKIP — справжня QNN HTP SDK library відсутня. [Первинні результати](../../verification/linux-attempts/run07/README.md) імпортовані після штатного poweroff; `source-binding.json` зв'язує **86** виконуваних джерел із guest manifest. Попередні невдалі/перервані спроби збережені окремо в [linux-attempts](../../verification/linux-attempts/README.md).

[Модульні результати](../../verification/linux-attempts/run07/module-lab/MODULE-RESULTS.md): **754 refs / 64 збірки / 166 інтерфейсів**. Функціонально в run07: **40 PASS, 0 FAIL, 126 CONNECTION_MODEL_ONLY**. Після run07 fixture self-tests (`FILESYSTEM_FIXTURE`) і не виконані інтерфейси більше не зараховуються як `EMULATION_PASS`, тому чинний звіт (CI run 40043380590, 750 refs) дає **34 `EMULATION_PASS`, 0 FAIL, 132 `CONNECTION_MODEL_ONLY`** ([таблиця](../../verification/module-lab/MODULE-RESULTS.md)). Окремо всі **166** interfaces мають CONNECTION_MODEL_PASS, виконано **3749/3749** topology/fault scenarios. XCB observer отримав **267** успішних samples, **0** transport misses; найбільший проміжок без sample — **0.574 s**. Це виміряна вибіркова перевірка, не твердження про безперервний стан між samples. Опис середовища й відтворення — [README](README.md); деталізація моделей — [module lab](../module_lab/README.md).

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

Запис використовує pinned dirfd, `O_NOFOLLOW`, staging, перевірку identity перед replace. Існуючий JSONL дописується лише новим рядком у той самий перевірений inode (`O_APPEND` через `/proc/self/fd`), помилка write/fsync обрізає файл до попередніх повних рядків, обірваний останній рядок після втрати живлення не продовжується; новий файл — staging+atomic replace. ENOSPC або втрата mount **до commit** залишають попередній файл незмінним. Перша filesystem-помилка зберігає початковий `OSError`/errno; наступні звернення дають `StorageRevoked`. Це не гарантія проти зникнення живлення після commit, privileged mount manipulation або стороннього процесу, який має право змінювати той самий output directory. Guard сам не форматує, не монтує й не вмикає живлення носія. Linux metadata — [proc filesystem](https://www.kernel.org/doc/html/latest/filesystems/proc.html).

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

## Посилення harness після run07 (виконано в ARM64 run08 і чинному run)

Ці зміни внесено після run07; в ARM64 guest їх виконано в CI run 40016984543 (run08, джерела до злиття) і в чинному CI run 40043380590. Результати run07 вони не змінюють і не підтверджують. Production timers, freshness deadlines і safety guards не послаблені.

- Кешований overlay більше не означає неперевірені залежності: guest перевстановлює всі locked DEB (без `--skip-same-version`), заново створює venv і примусово проводить кожний wheel через `--require-hashes`; `dependency-verification.json` порівнює встановлені версії з обома lock і входить до загального PASS. Run07 фактично використав кешовані DEB/wheels попередніх VM.
- Host приймає overlay лише від прогону з записаним summary і `qemu_exit_code=0`, записує backing chain із SHA256 кожного шару та генерує новий cloud-init instance-id. Поле `previous_clean_shutdown` прибрано: воно не мало доказів.
- `explicit_arm_and_fault` і `link_loss_latched` вимагають точної першої причини trip, як уже вимагав lease-сценарій; PTY HUP записує фактичну причину; RX failure-сценарії відхиляють будь-який тип помилки поза публічною межею CLI.
- PTY peer відправляє STATUS/HELLO за `TelemetrySchedule` прошивки (200 ms / 1000 ms) замість 75 ms. Це зменшує запас fixture до реального: host stall понад приблизно 300 ms із TCIFLUSH може коректно спричинити `pico_status_timeout`. Таку відмову слід аналізувати (діагностика містить `max_pump_loop_gap_ms`), а не послаблювати 500 ms deadline.
- Підсумок guest приймає лише задокументовані SKIP (QNN HTP SDK, PyMuPDF поза wheelhouse), кожен один раз; `host_regression_status=PASS` з іншими SKIP більше не дає PASS. Host відхиляє symlink/спеціальні файли в результатах guest і робочі шляхи з пробілами; архів джерел належить root.
- Host і finalize обходять результати guest через `os.walk` з `onerror`: каталог без права читання (debugfs відновлює режими guest) зупиняє імпорт, а не пропускається; корінь перевіряється `lstat` першим. Finalize також вимагає `dependency-verification.json` зі статусом PASS.
- `srrx.service` тепер має `SupplementaryGroups=i2c dialout srrx-pico`: bootstrap створює системну групу `srrx-pico` без членів, `guest_smoke` вимагає її наявність і відсутність labclient. OPEN-записи мають завершити саме release guard кодом 2: перевірка `status=2` більше не збігається з `status=216` (GROUP), коли група відсутня і guard не запускався.
- HF+ module fixture моделює відставання споживача без фатальної помилки: 64 блоки заповнюють чергу, 65-й transfer відкидається, а наступний блок у черзі позначається `discontinuity`. PTY lost-HELLO звіт записує кількість повторів HELLO до ресинхронізації, тож 2000/3000 ms не читаються як відхилення інтервалу прошивки.

## Посилення harness для наступного ARM64 run (LAB-17, TOOL-07, DEP-11)

Ці зміни внесено після CI run 40043380590 і в імпортованому ARM64 прогоні ще не виконано; підтвердить їх лише наступний `linux_lab=true` run.

- LAB-17: модулі QEMU, які завантажуються через dlopen, більше не лишаються поза перевіркою. `fetch_tools.py` і `host.py prepare` перевіряють DT_NEEDED closure трьох програм і кожного `usr/lib/x86_64-linux-gnu/qemu/*.so` locked `ld.so --inhibit-cache --list`; порожній каталог модулів, `not found` або бібліотека хоста зупиняють підготовку, виправлення — лише додати пакет до lock або явно записати карантин, ніколи не пропуск. Prepare приймає тільки wrappers `fetch_tools.py` одного tools-каталогу й відмовляє, якщо на хості є `/var/run/qemu/Debian_1_8.2.2+ds-0ubuntu1` (Ubuntu QEMU шукає там відсутні модулі). `host.py run` вмикає через wrapper `LD_DEBUG=files,libs` для locked ld.so і вимагає, щоб усі фактично відображені об'єкти, зокрема NSS/gconv/plugins, лежали в tools root (`qemu-loaded-objects.json`, `host.loader_audit`); finalizer імпортує лише чистий і непорожній аудит. Цей аудит охоплює тільки процес QEMU; `qemu-img` і `genisoimage` у prepare перевірено статично.
- TOOL-07: `design/readiness-contract.json` входить до `source-binding.json` напряму, а не лише через шаблон приймання; `system-smoke.json` записує його SHA256, і finalizer (`smoke_attests`) вимагає, щоб він і кожен інший прив'язаний файл цього запису збігалися з прив'язкою.
- DEP-11: guest-крок `systemd_device_wait_bounded` застосовує drop-ins, згенеровані `deploy.py`, до тимчасових unit-файлів із вузлом, якого немає: oneshot стартує після timeout 3 s, а `Restart=on-failure` з `ExecStartPre=/bin/false` за 15 s не доходить до `start-limit-hit`. Назви device units звірено із `systemd-escape`. Сам `srrx.service` у guest цим кроком не запускається.

## Переносимість автономного комплекту

Під час перевірки розпакованого комплекту в іншому каталозі launcher виявив відсутній порожній directory target для `tools/root/usr/share/misc/magic → ../file/magic`. Початковий host-only builder включав файли, symlinks та їхні parent directories, але губив порожні каталоги. `build_kit.py` тепер записує runtime directories в manifest, включає їх до tar та звіряє точну множину/режим каталогів. Launcher перевіряє їх до symlink resolution. Це виправлення пакування; воно не змінює виконані guest/model джерела або результати run07. Переносимість підтверджується окремими `--verify-only` і `--prepare-only`, а не повторним завантаженням VM.

## Незмінні межі

Усі **37 апаратних воріт OPEN** (з 23.10.2026 додано E5-10 — W1-2 WIFI_PWR_EN), hardware release **BLOCKED**. Generic ARM64 Linux VM не є Q6A kernel/DT/driver image. Фізичні UART/I²C/GPIO, RF/аналогові тракти, заряд/BMS, температура/калібрування, реальні touch/HDMI/USB і фізичний OFF ще не прийняті. Повний Lime SDK/backend, гарантований тракт 56 MS/s, кваліфікований QNN HTP, весь каталог декодерів та затверджений цільовий системний образ залишаються прогалинами. Наявність пакета MicroPython source не означає UF2/runtime build або прошитий пристрій. Ранній push повертав HTTP 403; згодом гілку `codex/sr-rx-v2-completion` опубліковано в origin (див. [RESTORE-GIT](../../RESTORE-GIT.md)).

Connectivity `CONNECTION_MODEL_PASS` означає виконані topology/fault scenarios проти KiCad XML. Він не перетворює непокритий драйвер на `EMULATION_PASS`, не закриває DNP/TBD gates і не підтверджує фізичні pinouts. Відкриті умови J102/E1-02, IP2368/E1-01, Wisecoco/E3-02/E5-01 та DC polarity/DC block Boni мають залишатися у видимих row details звітів.

## Відтворення перевірки та пакування

Команди нижче виконуються з кореня `sat-receiver-audit` і описують відтворення. Run07, CI run 40016984543 (run08 в архіві спроб) і чинний CI run 40043380590 завершено та імпортовано; наступне виконання потребує нового work-каталогу. CI-job `linux-lab` виконує описаний нижче порядок повністю, але нічого не комітить: його `lab-evidence.patch` переглядають і застосовують окремо. Пакувальник і незалежний validator відхиляють неактуальні hashes та неповний ZIP.

1. Для нового запуску дочекатися завершення VM. Перевірити його `report.json`: загальний PASS, `qemu_exit_code=0`, архітектура aarch64, усі очікувані suites, `physical_tests_performed=false`, `hardware_qualified=false`. Не імпортувати проміжні логи як PASS. Імпортований CI run 40016984543 має саме ці terminal значення (для джерел до злиття).
2. Імпортувати execution evidence і source binding. `finalize_linux_lab.py` вимагає нових `verification/linux-lab` та `verification/module-lab` каталогів; якщо існують старі результати, спершу окремо зберегти їх, не змішувати прогони.

Спершу, ще до `host.py prepare`, хостові докази доводять до нерухомої точки. `design/readiness-contract.json` містить лічильники host regression (`host_tests_passed`, `host_tests_skipped`) і водночас входить до hash цієї регресії (`commissioning.GRAPH_PATHS`) та до `software/config/acceptance.template.json`, який як `software/**/*.json` входить до виконаних guest джерел (`finalize_linux_lab.bound`). Сам контракт тепер прив'язаний і напряму (`BOUND_EXTRA`), бо guest звіряє його `gate_results` зі staged шаблоном; цикл не виникає, доки контракт не містить полів, похідних від `source-binding.json` чи стану Linux lab (це закріплює тест його набору ключів), а `verification/software-tests.json` не прив'язується:

```sh
python3 tools/run_tests_offline.py
python3 tools/build_documents.py     # записує лічильники в контракт
python3 tools/run_tests_offline.py   # прив'язує регресію до нового контракту
python3 tools/build_documents.py     # контракт уже не змінюється; COMPLETION бачить актуальну регресію
PYTHONPATH=software:. python3 -m srrx.provision template --output software/config/acceptance.template.json
PYTHONPATH=software:. python3 -m srrx.demo --output verification/software-simulation.json
python3 tools/render_hmi_views.py --output verification/hmi-views
python3 tools/build_firmware.py
```

Якщо останній `build_documents.py` знову змінив контракт (регресія в іншому середовищі дала інші SKIP), пару «регресія → `build_documents.py`» повторюють, доки контракт не перестане змінюватися. Лише потім готують і запускають guest. Після нього:

```sh
python3 tools/finalize_linux_lab.py --work /tmp/srrx-linux-lab-runNN
python3 tools/build_documents.py     # контракт і шаблон мають лишитися побайтово тими самими
python3 tools/build_bundle.py
python3 -B tools/check_bundle.py
```

CI-job зберігає копії контракту й шаблону перед підготовкою guest і після finalizer звіряє їх через `cmp`; розбіжність зупиняє job до пакування. Шаблон і контракт після підготовки guest не перегенеровують: будь-яка зміна кожного з них дає «Linux execution result is stale».

`build_bundle.py` вимагає актуальних host regression, Linux/module PASS, точних hashes виконаних Python/shell/service джерел, module inventory/models/графів і CAD verification. Виправлення production/model Python після підготовки guest потребує нового виконання guest; не переписувати source binding вручну. Якщо змінено джерела хостових перевірок або readiness contract, перед bundle повторити `python3 tools/run_tests_offline.py`, а після нього `python3 tools/build_documents.py`. Якщо змінено схеми, спочатку повторити CAD export/перевірки за [KiCad README](../../build/kicad/README.md).

Виняток для середовища без ARM64 lab: якщо виконаний код змінено, а новий guest-прогін неможливий, `build_bundle.py` пакує лише тоді, коли сам проєкт позначає `verification/linux-lab/project-manifest.json` як `RECORD_OF_EARLIER_RUN` (а README Linux-результату має відповідне попередження). Тоді HTML показує окреме попередження «лише запис попереднього прогону» з кількістю змінених виконаних файлів і архітектурою поточного module-lab прогону. Решта перевірок (host regression, module inventory/models/графи, CAD) залишаються суворими; source binding вручну не переписується.

3. Переглянути `git status --short`, додати лише призначені до передачі джерела/звіти, виконати `git diff --cached --check`, створити commit і опублікувати гілку `ccr-1537979d-cj7q9t` в origin. Ця опублікована гілка є основним способом передачі; ZIP/bundle — додаткові. Гілки `codex/sr-rx-v2-completion` і `wip/review-fixes` застаріли: їхній вміст злито в `ccr-1537979d-cj7q9t`, тож їх можна видалити; історію комітів (Codex — `05f0019`…`87e1e90`, далі — сесії Claude) описано в [HANDOFF](../../HANDOFF.md#ревізія-23102026-claude-перевірка-виправлення-ci-план). Для офлайн-переносу історії використовувати bundle, а не `git format-patch`, який пропускає merge-коміти:

```sh
git bundle create /tmp/SR-RX-v2.1.bundle ccr-1537979d-cj7q9t
git bundle verify /tmp/SR-RX-v2.1.bundle
```

Bundle відображає лише закомічене, тому його не будувати до commit поточних змін. Інструкції відновлення, зокрема `git clone --branch ccr-1537979d-cj7q9t` з bundle, — [RESTORE-GIT](../../RESTORE-GIT.md).

4. Після фінального ZIP створити offline kit. Усі вхідні каталоги створюють скрипти репозиторію: `fetch_tools.py` (locked host DEB, розпакований `root/`, wrappers `bin/`, `host-packages.lock.json`) і `fetch_assets.py` (image/kernel/initrd, підписаний `ubuntu-24.04-server-cloudimg-arm64.manifest`, wheels, guest DEB). `--tools`/`--dest` мають бути новими каталогами поза checkout; `--output` — новим `.tar.zst` поза checkout, а його parent directory має вже існувати. Builder потребує `gpgv`, `zstd`, `dpkg-deb` і `tar`.

```sh
python3 deployment/linux_lab/fetch_tools.py --dest /tmp/srrx-qemu-tools
python3 deployment/linux_lab/fetch_assets.py --dest /tmp/srrx-arm64-assets
python3 deployment/linux_lab/build_kit.py \
  --assets /tmp/srrx-arm64-assets \
  --tools /tmp/srrx-qemu-tools \
  --project-zip SR-RX-v2-project.zip \
  --output /tmp/SR-RX-Linux-Lab.tar.zst
```

Builder звіряє signed/locked inputs та кожний archive payload hash. `tools/root` має точно збігатися з новим розпакуванням hash-locked host DEB у порядку lock (файли, SHA256, executable bit, symlink targets), а `tools/bin` — із wrappers `fetch_tools.py`; самодекларовані JSON-маніфести більше не приймаються як provenance. Wrappers запускають locked `ld.so` з `--inhibit-cache`, а `fetch_tools.py` перевіряє через `ld.so --list`, що жодна DT_NEEDED бібліотека QEMU/genisoimage не береться з хоста. Його PASS означає цілісність kit; він **не завантажує guest**. Після розпакування використовуйте `launch.py --verify-only`, потім новий workspace для `--prepare-only` або повного запуску. Kit не містить попередній writable overlay як runnable input і стартує з pinned base image; це окрема перевірка від cached run07. Фінально звірити manifest/CRC архівів, додати checksums і передати опубліковану гілку, а за потреби project ZIP/HTML, Git bundle та offline kit із фактичними verification reports.
