# Приймальний процес labrx

Реалізовано потік **джерело → RAM → FFT → обов'язкова маска → спектр/огляд**. Синтетичний вхід працює без SDR. Фізичні bindings використовують офіційні C API librtlsdr та libairspyhf; відкриття відбувається лише за явним унікальним serial. Це Python/NumPy реалізація для спектральної обробки, а не підтверджений C++ тракт 56 MS/s. Пропускну здатність Q6A, паралельний LRPT/HRPT та приймання Lime тут не заявлено.

## Запуск

З кореня проєкту, Python3.11+ і NumPy:

```sh
PYTHONPATH=software:. python3 -m srrx.labrx --simulate --center-hz 100000000 --sample-rate 1024000 --frames 10 --output /tmp/srrx/latest.json --survey /tmp/srrx/survey.jsonl
```

`--frames 0` працює до Ctrl-C. `latest.json` атомарно замінюється; JSONL містить лише маскований спектр. Усі синтетичні результати мають `source=SIMULATION`. Усі частоти задаються в Hz, sample rate — комплексних відліків за секунду. Наявність RF-сигналу не є доказом класу або публічності його вмісту.

Маски [SPECTRUM](SPECTRUM.md) застосовуються також до вигаданого або завантаженого кадру перед записом/навчанням. Звичайний `run_capture` не має IQ/audio recorder і raw-sample UDP/TCP export; EEPROM write і bias-ON API немає взагалі. Голосові позначки зберігають лише спектр. Жодних координат передавачів чи їхніх ідентифікаторів не записується. Єдиний записувач IQ — обмежений запис baseband проходів Meteor-M LRPT за рішенням власника v2.1 (блок поправок v2.1 у [STACK.md](../STACK.md)); його описано нижче в розділі «Запис baseband LRPT (v2.1)». Джерело вікон — операція labd `plan_passes` (ізольований `srrx-passes@.service`) і `srrx.passes.baseband_windows`: рівно AOS–LOS повних проходів алоу-лістованих цілей ролі `LRPT` і жодного вікна без перевіреного UTC (`UTC_NOT_VERIFIED`); поки джерела перевіреного UTC в labd немає, вікон немає ([LOCATION](LOCATION.md)). Роль `LRPT` — лише мітка з алоу-листа оператора, попередній фільтр без NORAD id у коді; набір «лише Meteor-M N2-3/N2-4», поля AOS−60 s … LOS+60 s і межу 20 хв на файл перевіряє вже сам записувач (`srrx.satdump_pass.select_windows`, `srrx.baseband.window`).

## Запис на знімний накопичувач

Для такого запису треба явно ввімкнути `StorageGuard`: **обидва** параметри `--storage-root` і `--storage-device`. Root має бути вже наявною точною точкою монтування, а device — перевіреним оператором block device саме змонтованого тому, наприклад `/dev/disk/by-uuid/…`. UUID реального T7 невідомий і в проєкті не призначений. Якщо змонтовано розділ, прив'язка має вказувати його, а не весь диск. Приклад після перевірки й монтування оператором:

```sh
PYTHONPATH=software:. python3 -m srrx.labrx --simulate --frames 10 --storage-root /media/T7 --storage-device /dev/disk/by-uuid/REPLACE_WITH_VERIFIED_UUID --output latest.json --survey survey.jsonl
```

`REPLACE_WITH_VERIFIED_UUID` — обов'язкова заміна на фактичний перевірений UUID, не готова конфігурація пристрою. У guarded mode відносні output/survey шляхи відраховуються від `--storage-root`; абсолютні мають лишатися всередині нього. Усі батьківські каталоги вже повинні існувати. Guard не створює відсутній mountpoint чи каталоги, не переходить через symlink або сторонній вкладений mount і не підставляє root filesystem після втрати диска. Без цих параметрів лишається звичайний локальний запис зі створенням parent directories; його не можна використовувати як доказ захищеного запису на T7.

Guard звіряє явний block device, `st_dev`, Linux mount ID з `mountinfo`/`fdinfo` та закріплений directory fd. Втрата, переміщення або підміна mount/bind mount, заміна шляху, read-only стан чи помилка запису, зокрема ENOSPC, назавжди відкликає цей екземпляр guard. Автоматичного відновлення немає: після усунення причини потрібні нова явна прив'язка та запуск capture. Відмова під час уже відкритого guarded capture проходить через cleanup: RX worker закривається й до labd надсилається OFF належної гілки приймача. Це не команда вимкнути живлення T7.

Працює один writer, а mount/output directories мають бути доступні для запису лише довіреному процесу. Advisory lock не захищає від іншого writer, який його ігнорує, або привілейованих змін mount namespace. Запис іде через `dirfd`/`O_NOFOLLOW` та staging file з atomic replace. Попередній файл зберігається при помилці **до commit**; помилка directory fsync після replace вже не гарантує збереження попередніх байтів чи стійкість при втраті живлення.

Guarded JSONL append до наявного файла дописує лише новий рядок у той самий перевірений inode (вартість O(рядка), без копії всього файла) і після помилки write/fsync обрізає файл до попередніх повних рядків. Новий файл створюється через staging і atomic replace. Втрата живлення під час append може лишити один обірваний останній рядок; наступний append до такого файла відмовляє й відкликає guard. Ліміт файла — **64 MiB**, автоматичного rollover немає. Рядок спектра має приблизно 34–38 KB при `--fft-size 1024` (близько 1900 кадрів на файл) і 560–600 KB при 16384 (близько 115 кадрів); за частоти кадрів RX це хвилини або секунди. До межі слід завершити capture й явно обрати новий файл. Досягнення межі дає помилку та відкликає guard.

Перед sync/unmount/вимкненням живлення оператор має завершити capture і закрити guard, який утримує directory fd тому. Сам guard не монтує, не форматує, не виконує unmount і не керує EN_T7. Фізичний T7, USB3/UAS, поведінка при USB removal, тривалий запис і порядок sync/unmount/power-off залишаються непідтвердженими; програмні fixture-перевірки цього не замінюють.

## Фізичний шлях

Спершу треба завершити справжнє приймання з [software/README](README.md). `labrx --hardware` самостійно повторно перевіряє весь acceptance, потім зв'язує driver record із його hashed artifacts. Приклад фізичного запуску після приймання:

```sh
PYTHONPATH=software:. python3 -m srrx.labrx --hardware --acceptance /etc/srrx/acceptance.json --driver-record /opt/srrx/evidence/rtl-driver.json --socket /run/srrx/control.sock --center-hz 100000000 --sample-rate 1024000 --frames 100 --output /data/products/latest.json
```

Driver record має точні поля `v=1`, `backend` (`rtl` або `airspyhf`), `branch` (`RTLA`/`RTLB` або `HFP`), `serial`, `library_path`, `library_sha256`, `rx_only_reviewed=true`, `bias_disabled_verified=true`, `dependencies_reviewed=true`. Сам JSON мусить бути локальним файлом усередині проєкту й фігурувати як `{path,sha256}` у доказах прийнятого gate. Шаблон [rtl-driver.template.json](config/rtl-driver.template.json) навмисно неприйнятний. Прив'язка — лише до RX gate своєї гілки (review finding RX-10), бо саме його вимір струму й пускового струму виконано з цією збіркою драйвера:

| `branch` | gate | refs |
|---|---|---|
| `RTLA` | `E5-04` | R501 |
| `HFP` | `E5-04` | R509 |
| `RTLB` | `E2-03` | U210 |

Той самий record у доказах іншого gate, зокрема `E1-01`, відхиляється. `RTLA` і `HFP` ділять `E5-04`, їх розрізняє поле `branch` самого record. Record читається один раз: розбираються саме ті байти, що хешовані.

`library_path` — абсолютний канонічний шлях до справжнього файла, без жодного symlink-компонента: версійна `librtlsdr.so.2.<версія>`, встановлена від root у `/opt/srrx-vendor/lib`, або `/usr/lib/aarch64-linux-gnu/libairspyhf.so.<версія>`. `deployment/build-vendor.sh` лише стейджить RTL-бібліотеку в `NEW_WORKDIR/rootfs/opt/srrx-vendor/lib` від непривілейованого builder (від root скрипт не запускається), тож staged-файл належить builder; копія зі збереженням власника (`cp -a`, `rsync -a`) дасть бібліотеку, яку labrx відхилить. Оператор встановлює саме версійний файл від root, наприклад `install -d -o root -g root -m 0755 /opt/srrx-vendor/lib`, потім `install -o root -g root -m 0644 NEW_WORKDIR/rootfs/opt/srrx-vendor/lib/librtlsdr.so.2.<версія> /opt/srrx-vendor/lib/`, і лише після цього обчислює `library_sha256` з установленого файла. Soname-symlink (наприклад `librtlsdr.so.2`) і шляхи `/lib/...` (на merged /usr `/lib` — symlink) відхиляються. Ця сама примітка стосується заповнення шаблону. Файл має належати root, бути regular file без group/world write і без setuid/setgid; кожен батьківський каталог — каталог root без group/world write (sticky дозволено), як у decoder_policy і scope_policy. Інакше capture відмовляє ще до відкриття бібліотеки. CLI-прапорця чи змінної середовища, які розширили б набір довірених UID, немає; інший набір у коді передають лише component tests. Worker відкриває бібліотеку з `O_NOFOLLOW`, хешує байти з цього descriptor і виконує dlopen того самого inode через `/proc/self/fd`, тож перейменування в каталозі між хешем і завантаженням не підмінить байти. Перед open worker повторює перевірку власника/режиму за lstat (FIFO чи пристрій не відкривається), а після open — за fstat descriptor: це має бути той самий inode, який може змінити лише root, тож його байти не переписати на місці між хешем і mmap. Дайджест зв'язує байти; він не доводить справність ELF, залежностей, V4-підтримки або фізичне вимкнення bias. Залежності DT_NEEDED (наприклад libusb) та `LD_LIBRARY_PATH`/`LD_PRELOAD` середовища оператора цією перевіркою не охоплені.

Для HF+ driver-record serial — рівно **16 hex digits**, які передаються до `airspyhf_open_sn` як uint64. Повний USB descriptor `AIRSPYHF SN:…` використовується окремо в udev/devices config; копіювати префікс у driver record не можна.

Процес лише спостерігає за `labd`: живий прийнятий Pico, ACTIVE, налаштований MCP, armed policy і ввімкнена конкретна VBUS-гілка обов'язкові. Оренду створює оператор у меню/`labctl hold`, а не RX-процес. Зміна Pico session, відмова control service, втрата дозволу/живлення або відсутність свіжого блока припиняє потік. Запуск worker (spawn, імпорт NumPy, відкриття драйвера) обмежено 10 s, які відлічуються від `process.start()`, а не від першого `read()`: пізній перший `read()` додаткового часу не отримує. Лише після сигналу готовності діє межа свіжості 1 s на кожен блок. Виміряний час від spawn до сигналу готовності JSON-результат labrx містить як `worker_startup_s` (`null` у симуляції). Стан labd перевіряється приблизно кожні 50 ms, зокрема й під час запуску. Повторне відкриття після відмови потребує явного запуску.

C driver працює в окремому дочірньому процесі; його USB read не блокує перевірку labd. Блоки не пишуться на диск, черги обмежені. Процес capture/FFT до дозволу живлення та дочірній worker до завантаження драйвера вимагають `RLIMIT_CORE=0` і Linux `PR_SET_DUMPABLE=0` із перевіркою `PR_GET_DUMPABLE=0`; worker повторює перевірку після конструктора драйвера. Відсутня підтверджена заборона дампів — capture відхиляється. Захист зберігається після cleanup, доки процес може містити залишки IQ у heap. Самого `RLIMIT_CORE=0` недостатньо для систем із piped core collector; див. [core(5)](https://man7.org/linux/man-pages/man5/core.5.html). При завершенні worker закривається, до labd надсилається OFF вибраної VBUS-гілки навіть після помилки конструктора/cleanup. Це стосується також SIGTERM/SIGHUP/SIGINT (kill, systemd stop, обрив SSH, Ctrl-C): обробник запускає той самий cleanup, код виходу 128+номер сигналу. Після першого сигналу наступні ігнорують; перший сигнал, що надійшов уже під час cleanup (закриття worker або запит OFF), не перериває його, а лише дає йому завершитися. Попередження в stderr не може зламати cleanup, навіть якщо термінал уже зник після обриву SSH. Відповідь labd на OFF перевіряється; непідтверджений OFF друкує попередження в stderr, `branch_off_confirmed=false` і код виходу 3. Worker спершу отримує до 0.5 s на штатний вихід із rtlsdr_close/airspyhf_stop+close, потім SIGTERM, потім SIGKILL. Убитий процес не доводить фізичний USB timing; це предмет стендового тесту. Захист від swap забезпечує окрема конфігурація системи, а не Python.

Батьківський процес за кожну ітерацію забирає все, що вже чекає в pipe, і залишає лише найновіші суміжні samples (не менше 16384). Якщо RAM-черга HF+ (64 блоки) заповнена через повільного споживача, callback відкидає новий transfer, а не backlog; наступний блок, що потрапив у чергу, позначається як розрив. Блоки з черги забирає лише `read()`, а прапорець розриву змінює лише callback-потік, тому блок, позначений суміжним, ніколи не йде після відкинутого. Ціна — затримка: після паузи споживача worker спершу вичитує старіший backlog (до 64 transfers), а не найновіші samples. Відкинутий у батьківському процесі backlog або позначений розрив очищують FFT history, тому FFT ніколи не з'єднує несуміжні блоки. USB `dropped_samples` HF+ лишається фатальною помилкою. Послідовні RTL `read_sync` блоки (8192 samples) не доведено суміжними: кожен FFT RTL рахується з одного блока, а `--fft-size` понад 8192 для RTL відхиляється до спостереження labd.

RTL налаштовується з direct sampling OFF, bias OFF, tuner AGC і digital AGC OFF; bias ON не викликається. Серійні номери мають бути унікальними; індекс 0 як fallback заборонений. HF+ використовує live supported-rate list та штатну калібровку бібліотеки без додаткової ppm-компенсації. У версії1.6.8 bias API немає; при наявності пізнішого API викликається тільки OFF. Відповідність плати й відсутність небажаного живлення все одно має бути виміряна.

Lime залишається заблокованим у runtime. Експериментальний source patch у deployment не є доказом повного аудиту всіх TX/raw-register шляхів або приймання на Micro M.2; приймальні програми не можуть відкрити його через цей backend. SatDump/live decoder transport та весь початковий каталог декодерів ще не інтегровані в цей спектральний процес.

Первинні ABI: [Osmocom rtl-sdr.h](https://github.com/osmocom/rtl-sdr/blob/master/include/rtl-sdr.h), [AirspyHF header](https://github.com/airspy/airspyhf/blob/master/libairspyhf/src/airspyhf.h), [AirspyHF1.6.8 implementation](https://github.com/airspy/airspyhf/blob/1.6.8/libairspyhf/src/airspyhf.c). Довідкові URL не є supply-chain pin; точні перевірені ревізії та hashes містяться в deployment.

## Стендовий вимір запуску worker

Холодне відкриття драйвера на справжній Q6A з RTL-SDR V4 і HF+ ще не виміряно, а `labrx --hardware` до повного приймання цього зробити не може. Для стенду є [rx_startup_bench.py](../deployment/linux_lab/rx_startup_bench.py) (review finding RX-02b). Він не запускає labd, не виконує ARM і не вмикає жодної гілки: приймач живиться від зовнішнього стендового USB hub, а не через EN. Скрипт будує record лише в пам'яті з аргументів `--backend`, `--branch`, `--serial`, `--library-path`, `--library-sha256`, `--center-hz`, `--sample-rate`, перевіряє бібліотеку тим самим production-правилом власника/режиму й дайджесту та N разів запускає production `WorkerSource` з явно позначеним no-op guard: один блок у RAM, потім close. На stdout виводиться лише JSON: `ready_after_s` кожного запуску, min/p50/max, kernel/arch, `physical_gate: OPEN`, `raw_iq_persisted: false`. Файлів, IQ, спектра чи `__pycache__` скрипт не пише: bytecode вимкнено ще до імпорту srrx, також для spawn worker (`PYTHONDONTWRITEBYTECODE=1`), тож у hash-перевіреному дереві `/opt/srrx` не з'являються невідомі файли.

```sh
PYTHONPATH=software python3 deployment/linux_lab/rx_startup_bench.py --backend rtl --branch RTLA --serial REPLACE_WITH_SERIAL --library-path /opt/srrx-vendor/lib/librtlsdr.so.2.REPLACE_WITH_VERSION --library-sha256 REPLACE_WITH_SHA256 --condition cold --runs 1
```

Для кожного приймача (RTL-A, RTL-B, HF+) потрібні 20 холодних запусків, кожен перший після повного вимкнення живлення приймача (`--condition cold --runs 1`), і 20 теплих (`--condition warm --runs 20`). Запропонований критерій — max холодного `ready_after_s` не більше 5.0 s, тобто щонайменше вдвічі менше за 10 s; поле `within_proposed_cold_limit` лише інформує. Якщо критерій не виконано, власник вирішує, чи збільшити `STARTUP_TIMEOUT_S` (bound-зміна, потрібен новий lab-прогін), чи шукати причину. JSON-журнали зберігаються як докази RX gate приймача: `E5-04` для RTL-A і HF+, `E2-03` для RTL-B. Gate лишається OPEN, доки не пройдено всю його процедуру. Живлення приймача лишається поза SR-RX; дотримуйтеся застережень E5-06 щодо зворотного живлення.

## Запис baseband LRPT (v2.1)

Рішення власника 24.10.2026 (STACK.md:977, [поправки v2.1](../build/12-revision-v2.1.md), [рішення 6](../build/15-rishennia-komplektu.md)) дозволяє на пристрої лише вузький запис проходів **Meteor-M N2-3/N2-4 LRPT**. Його реалізують `labrx.run_baseband`, `srrx.baseband` і `srrx.satdump_pass`. Це модель і хостові тести на синтетичному IQ (`software/tests/test_baseband.py`, `test_satdump_pass.py`), а не стендовий чи ефірний результат.

Ланцюг для кожного блоку RTL 1.024 MS/s:

1. `srrx.voice_mask.VoiceExcisor`: статичні маски голосу, голосові смуги поза вікнами, смуги без даних; єдина активна смуга — вікно каналу.
2. Канальний фільтр `ChannelDecimator`: FIR Кайзера (≈349 відводів), який overlap-save застосовує як точну лінійну згортку. Смуга пропускання — Rs·1.6/2 + Доплер (7 km/s, ≈3.2 kHz), загородження починається з краю вікна Rs·1.6/2 + Доплер + 20 kHz (≈±81/±87 kHz для 72k/80k). Загасання ≤−100 dB поза вікном і нерівномірність ≤0.01 dB розраховуються й перевіряються під час створення фільтра; інакше відмова `CHANNEL_FILTER_SPEC_NOT_MET`. Тон поза вікном амплітудою до 0 dBFS дає в ci16 нулі (тест). Перші ≈1.3 ms (перехідний процес обох фільтрів) відкидаються.
3. Децимація на 4 → 256 kS/s, потім SigMF v1.2.6 `ci16_le` зі значенням round(x·32767): це обернення читача cs16 у SatDump 1aedd60 (`volk_16i_s32f_convert_32f(..., 32767)`).

Межі:

- **Вікно.** Повний прохід цілі з прийнятого алоу-листа (`norad_allowlist.load_accepted`) з роллю `LRPT` і перевіреною назвою Meteor-M N2-3 або N2-4. Інші цілі з роллю LRPT лише рахуються й ніколи не записуються. Вікно — AOS−60 s … LOS+60 s, ≤20 хв на файл. Центр 137.1/137.9/137.9125 MHz і Rs 72k/80k задає оператор; код не вгадує, який супутник на якій частоті. Відліки до початку вікна відкидаються, кінець вікна закриває файл.
- **Час.** Перевірений UTC потрібен на старті й на кожному блоці: на залізі це поле `utc_verified` у статусі labd. Його ще немає, тож апаратний запуск сьогодні завжди відмовляє `UTC_NOT_VERIFIED` (fail closed); у симуляції стан UTC передає викликач.
- **Межі сеансу.** `ScopeLatch.permits('record')` перевіряється на кожному блоці; будь-який стоп переривач обробляє через abort callback.
- **Сховище.** Лише `<StorageGuard root>/raw/baseband-lrpt` з перевірками guard на кожному кроці (`StorageGuard.open_directory`, dirfd, `O_NOFOLLOW`, `O_EXCL`). Межа класу — 1.5 GiB у ковзній квоті сирих 30 GiB на `<root>/raw`. Старт відмовляє (`CLASS_CAP_1_5_GIB`, `RAW_QUOTA_30_GIB`, `STORAGE_FREE_SPACE`), якщо запланований розмір ×1.1 не вміщається. Запланований розмір наперед виділяється і ніколи не перевищується (`RESERVED_SIZE`). Одночасно працює один записувач (flock).
- **Видалення.** Стоп, помилка, втрата guard або UTC, стоп меж сеансу чи сигнал видаляють частковий файл. Після кожної спроби декодування (успішної чи ні) `satdump_pass.run_decode` видаляє запис. `BasebandStore.sweep()` (перед кожним записом і в `srrx-baseband-sweep.timer` кожні 15 хв) видаляє незавершене, невалідне, сторонні файли, записи віком ≥24 h і записи з датою в майбутньому (>1 h). Рядок tmpfiles `24h` — лише другий шар.
- **Без експорту.** Немає закріплення, меню, RPC, CLI-копії чи USB. CLI `srrx.baseband` має лише `sweep` і `usage`. Каталог 2750 `labd:srrx-bb`, файли 0640; читає їх лише unit декодування (додаткова група `srrx-bb`).

Живий шлях: `--live-port P` (або `live_port=`) надсилає **ті самі** збережені відліки як cf32 little-endian на фіксовану адресу `127.0.0.1:P`, ≤8188 комплексних відліків на датаграму (8192 × 8 B = 65 536 B > 65 507 B; net_source 1aedd60 читає одну датаграму в буфер 8192 × 8 B). Неблокувальний сокет: помилки лише рахуються й ніколи не зупиняють запис. Unit SatDump для живого режиму (`srrx.satdump_pass.live_command`: `live_argv` і `unit_properties("live")`, RuntimeMaxSec = вікно + 120 s; запускається до `run_baseband(..., live_port=P)`): `satdump legacy live <id> <out> --source net_source --mode udp --port P ...`, IPAddressDeny=any + IPAddressAllow=localhost, бо net_source 1aedd60 прив'язується до INADDR_ANY. Patch 0003 рецепта прив'язує його до 127.0.0.1 як другий шар.

Декодування (`srrx.satdump_pass.run_decode`, профіль `satdump-weather` у [DECODERS](DECODERS.md)): transient `systemd-run` від користувача `srrx-satdump`, порожній root-owned WorkingDirectory, приватний HOME, `/data` — порожній tmpfs з одним baseband лише для читання, PrivateNetwork=yes. Спершу обмежена перевірка `--help`, потім `satdump pipeline <id> baseband <файл> <out> --samplerate=256000 --baseband_format=cs16`. Unit падає на «CALCEPH ERROR», публікуються лише санітизовані PNG і звіт фіксованої структури.

Запуск оператором (з прийнятим алоу-листом, планом і прив'язкою сховища; поки labd не публікує `utc_verified`, команда відмовляє):

```sh
PYTHONPATH=software:. python3 -m srrx.labrx --hardware --acceptance /etc/srrx/acceptance.json --driver-record /opt/srrx/evidence/rtl-driver.json \
  --socket /run/srrx/control.sock --storage-root /data --storage-device /dev/disk/by-uuid/REPLACE_WITH_VERIFIED_UUID \
  --baseband-plan /var/lib/srrx/plans/<id>.json --orbit-allowlist /etc/srrx/orbit-allowlist.json \
  --orbit-allowlist-record /etc/srrx/orbit-allowlist.acceptance.json --center-hz 137900000 --symbol-rate 72000 [--live-port 8877]
PYTHONPATH=software:. python3 -m srrx.satdump_pass decode --recording lrpt-<16 hex> --installation /etc/srrx/satdump-installation.json \
  --products /data/products/satdump --storage-root /data --storage-device /dev/disk/by-uuid/REPLACE_WITH_VERIFIED_UUID
```

Відкрито: labd не планує запис і декодування за розкладом (інтеграція з рушієм і правило polkit для transient units). Немає джерела перевіреного UTC. `deploy.stage` ще не розкладає `satdump_pass.staged_files()` (tmpfiles, sweep unit/timer); користувачів `srrx-satdump` і групи `srrx-bb` не створено. Не передано TLE/OMM у SatDump (BUILDER `omm-csv`). Збирача пакета SatDump і перевірок `builder_checks` рецепта ще немає. Немає HRPT/AHRPT наживо (потрібен нативний labrx). Python-записувач на RTL читає блоки `read_sync`, не доведені як безперервні: стики рахуються як `srrx:unproven_joins`, пропуски — як `srrx:gaps`. Бюджет CPU на Q6A, справжній прохід і рядок RX-04-live (лише localhost на пристрої) — стенд і пристрій.
