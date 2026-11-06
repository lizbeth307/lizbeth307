# LC76G: UART-читач NMEA та обмежений імпульс RESET

Цей документ описує програмні шари для приймача Quectel LC76G (Waveshare 24370, U304): `srrx.gnss_uart` — читач NMEA з UART6 лише на прийом (альтернатива gpsd, див. нижче); операцію `gnss_reset` у `SafetyPolicy` служби labd — один обмежений імпульс RESET_N через MCP23017 #4; і ланцюг часу й місця навколо імпульсу — служби `srrx-locationd` (єдиний читач позиції), `srrx-timegate` (лише `chronyc selectopts PPS ±noselect`), `srrx-gnss-config` (налаштування з читанням назад) та оркестрацію в labd (`srrx.gnss_orchestrator`). Код і тести реалізовано. **На зібраному Q6A, справжньому UART6 чи схемі скидання їх не запускали.** Модульні тести працюють на справжніх Linux PTY, тимчасовому фальшивому sysfs і `SimHardware`; це SIMULATION/EMULATION, а не апаратний PASS.

Жоден із шарів не вмикає передавач, живлення антени чи DC на антенному вході й не розбирає приватний вміст. Читач, імпульс, `srrx-locationd`, `srrx-timegate` і оркестрація приймачу нічого не надсилають; у UART пише лише `srrx-gnss-config` — рівно речення allowlist build/07 §18 (`srrx.lc76g.ALLOWLIST`) і лише тоді, коли читання назад не збігається. Позиція береться лише з власного GNSS-фіксу; таблиць міст немає, а тестові дані — одна безіменна синтетична точка lat/lon.

**Робочий ланцюг часу й місця за STACK — gpsd → chrony** (STACK.md:124, :879; build/07 §18): `gpsd -n -b -s 115200` читає `/dev/lab/gnss` і нічого не пише в приймач, chrony бере NMEA від gpsd через SHM і PPS з `/dev/pps-gnss`, а споживачі позиції читають або gpsd через `GpsdClient` (меню HMI), або знімки служби `srrx-locationd` ([LOCATION](LOCATION.md)). Сирий читач `srrx.gnss_uart` — лише альтернатива для конфігурації без gpsd; обидва режими взаємовиключні, UART читає лише одна сторона. Оркестрацію навколо RESET (PPS-ворота chrony, налаштування з читанням назад, повторний вибір PPS) описано в розділі [«Ланцюг часу й місця»](#ланцюг-часу-й-місця-srrx-locationd-srrx-timegate-srrx-gnss-config-і-оркестрація-labd).

## Підключення (з графа схеми та build-документів)

| Що | Значення | Джерело |
|---|---|---|
| UART | UART6, хедер 16/18, `alias serial1 = …/serial@998000`, рівень 3.3 V | build/04-pidkliuchennia-pinout.md:37, :76, :201; build/07-pz-vstanovlennia.md:203 |
| Ланцюги | U304 P1.3 TXD → `UART6_RX`, P1.4 RXD ← `UART6_TX` | design/E3.json, U304 |
| Швидкість | 115200 8N1 (`GPSD_OPTIONS="-n -b -s 115200"`) | build/07-pz-vstanovlennia.md:461; 09-testy.md:55 (W-04) |
| Вузол | udev `KERNELS=="998000.serial"` → `/dev/lab/gnss`; ніколи жорстко `ttyHS1` (номер залежить від порядку probe) | build/04:37; build/07:475 |
| PPS | хедер 7, GPIO96, pps-gpio → `/dev/pps-gnss`; власник — chrony | build/04:33, :203; build/07:465-470 |
| RESET | MCP23017 #4 (0x23, U303) GPA1 → `E3_GNSS_RESET_GATE` → затвор 2N7002 Q301, стік на `E3_GNSS_RESET_N`; R326 100k тримає затвор низько; high = скидання, 0 = неактивний | design/E3.json U303/Q301/R326; build/04:144 |
| Вимога Quectel | RESET_N низько ≥100 ms, зовнішня підтяжка заборонена | design/E3.json, примітки U304 |
| Власник лінії RESET | labd | build/07:525 |

## Читач `srrx.gnss_uart`

Модуль використовує лише стандартну бібліотеку (`os`, `termios`, `fcntl`, `select`, `stat`, `re`, `errno`) і не має відносних імпортів, тож module lab завантажує саме цей файл.

```python
from srrx.gnss_uart import open_lc76g, NmeaUartReader
from srrx.location import LocationTracker

tracker = LocationTracker()
fd = open_lc76g()                      # лише /dev/lab/gnss, KERNELS=="998000.serial"
reader = NmeaUartReader(fd, tracker)   # читач володіє fd
accepted = reader.poll(now_ms)         # з наявного 20 ms select-циклу; перший виклик лише робить flush
reader.status()                        # state, bytes_received, flushes, last_byte_ms, error, reset_candidate
reader.close()                         # явне закриття; повторного відкриття немає
```

### Прив'язка `open_lc76g` / `bind_lc76g`

- Шлях за замовчуванням — рівно `/dev/lab/gnss`; інший шлях можливий лише явним аргументом (так роблять тести). Шлях має бути udev-псевдонімом (symlink). Ім'я ядра `/dev/tty*` відхиляється (`GNSS_PATH_NOT_ALIAS`); сканування `/dev` і запасного шляху немає.
- `realpath` мусить бути символьним пристроєм (`GNSS_NOT_CHAR_DEVICE`). `realpath(<sysfs>/class/tty/<ім'я>/device)` мусить містити сегмент шляху `998000.serial` (`GNSS_PARENT_MISMATCH`), як doctor перевіряє батьківський пристрій Pico. Номер у `<sysfs>/class/tty/<ім'я>/dev` мусить дорівнювати `st_rdev` вузла (`GNSS_SYSFS_DEV_MISMATCH`). Після відкриття `fstat` має повернути той самий `st_rdev` (`GNSS_DEVICE_CHANGED`).
- Відкриття: `O_RDONLY|O_NOCTTY|O_NONBLOCK|O_CLOEXEC`, далі `flock(LOCK_EX|LOCK_NB)` і `ioctl(TIOCEXCL)` до будь-якої зміни termios чи flush, як `srrx.link` для Pico. Root/CAP_SYS_ADMIN обходить `TIOCEXCL`.
- `configure_raw_115200(fd)`: `iflag=oflag=lflag=0`, `cflag=CS8|CREAD|CLOCAL` (без PARENB/CSTOPB/CRTSCTS/HUPCL), `ispeed=ospeed=B115200`, `VMIN=VTIME=0`, `tcsetattr(TCSANOW)`, тоді зворотне читання `tcgetattr`. Розбіжність дає `GNSS_TERMIOS_MISMATCH`; лише після збігу виконується `tcflush(TCIFLUSH)`. За будь-якої помилки дескриптор закривається; `termios.error` перетворюється на `OSError`.

### `NmeaUartReader.poll(now_ms)`

- Дескриптор має бути `O_RDONLY` і неблокувальним, інакше `GNSS_UART_FD_MODE`. Модуль не містить жодного шляху запису: не надсилає PAIR/PQTM-речень, оновлень прошивки чи команд скидання.
- Межа: щонайбільше 8 читань по 2048 байт (16 KiB) за виклик. Кожен шматок — окремий виклик `LocationTracker.ingest_nmea`, тож рядки від 16 байт укладаються в ліміт 128 рядків трекера; коротше сміття спрацьовує як `NMEA_BATCH_LIMIT` (fail closed). 115200 baud у 8N1 — це 11520 B/s (близько 11.25 KiB/s).
- Затримка хоста: якщо між викликами минуло понад 500 ms (або час пішов назад), читач робить `tcflush(TCIFLUSH)` і `tracker.invalidate("nmea", "NMEA_HOST_STALL")` (`NMEA_MONOTONIC_TIME_REVERSED`), як Engine відкидає UART-вхід Pico після розриву тіку. Після flush і на старті байти до першого `$` до трекера не потрапляють. Тому незавершений до затримки рядок трекер лише відкидає (`NMEA_RESYNC`), а нові байти ніколи його не «дописують». Інакше старе речення отримало б новий час прийому.
- Перший `poll()` теж вважається початком затримки: він завжди робить `tcflush(TCIFLUSH)`, хоч би коли його викликали після `open_lc76g()`. Байти, що накопичилися відтоді, не мають часу прийому, тож до трекера вони не потрапляють. Інвалідації цей flush не робить, бо читач ще нічого не передав. Тому перший виклик варто зробити одразу після створення читача; module lab так і робить.
- Тиша: без жодного байта 2 s — одноразово `invalidate("nmea", "NMEA_UART_SILENT")`, стан `QUIET`; від 10 s — `SILENT`, тобто лише кандидат на скидання. Автоматичного скидання чи ескалації немає. Затримка самого хоста не вважається тишею приймача: відлік тиші починається заново, але й прийомом це не вважається. До першого справжнього байта після flush стан лишається `STARTING`, а не `RECEIVING`. `last_byte_ms` у `status()` — час останнього справжнього байта, а не перезапуску відліку.
- Втрата: `POLLHUP/POLLERR/POLLNVAL` від `select.poll` або `EIO/ENXIO/ENODEV/EBADF` під час читання закривають дескриптор (окрім EBADF/POLLNVAL, коли номер уже може належати іншому файлу), викликають `invalidate("nmea", "NMEA_UART_LOST")` і ставлять `disconnected=True`. Інші помилки вводу-виводу дають `NMEA_UART_IO_ERROR`. Повторного відкриття немає: новий `open_lc76g()` і новий читач — явне рішення оператора чи служби. Порожнє читання за `VMIN=VTIME=0` означає лише «немає даних»; зависання tty видно тільки через poll.
- Стани: `STARTING` (жодного байта від початкового flush чи flush після затримки), `RECEIVING`, `QUIET`, `SILENT`, `DISCONNECTED`. Потоків і sleep немає; час — монотонні цілі мілісекунди того самого годинника, що й у трекера.
- Системні виклики `os.open`, `os.read`, `os.close` і `termios.tcgetattr` модуль бере через власні псевдоніми (`_os_open`, `_os_read`, `_os_close`, `_tcgetattr`). Тести підміняють ці імена, а не глобальні функції `os`, тож потоки інших тестів у тому самому процесі не перехоплюються.

### Режими та межі обсягу

- Режим gpsd (`gpsd -b`, без записів у приймач, STACK.md:879) — робочий; сирий режим цього читача — альтернатива без gpsd. Вони взаємовиключні **за конфігурацією**: UART читає лише одна сторона. `flock`/`TIOCEXCL` зупиняють інших непривілейованих відкривачів, але не root. У сирому режимі gpsd не повинен мати `/dev/lab/gnss` у `DEVICES`; `srrx-locationd` у сирому режимі відмовляє стартувати, якщо це не так або gpsd активний, а doctor перевіряє те саме за файлами (розділ «Розгортання» нижче).
- Читач інтегровано не в labd, а в окрему службу `srrx-locationd` (labd лишається лише AF_UNIX і єдиним власником I²C). Керування gpsd/chrony, PPS-ворота (`chronyc selectopts PPS ±noselect`, build/07:484) і окремий інструмент налаштування з allowlist build/07:485-498 з читанням назад реалізовано нижче; ніколи `$PAIR007`, `$PAIR752`, `$PAIR753` (build/07:500).
- Ворота публікації позиції належать шару-споживачу, а не читачу. Ворота PPS (3D і ≥6 супутників без прапорця глушіння, build/07:503) рахує `srrx-locationd` (`qualified_fix`); перший фікс для наведення (3D, ≥8 супутників, у межах 50 m протягом 5 хв) — `srrx.geo_look.FirstFixGate`; окремого підтвердження стрибка понад 100 km (рядок «служба місця» STACK.md) немає: трекер відкидає лише стрибки, швидші за 100 m + 100 m/s × час між фіксами.

## udev-правило `/dev/lab/gnss`

`deploy.stage` разом із явними прив'язками пристроїв записує окремий файл `etc/udev/rules.d/71-srrx-gnss.rules`. Той самий кандидат друкує `python3 deployment/deploy.py udev-gnss`:

```text
SUBSYSTEM=="tty", KERNELS=="998000.serial", GROUP="srrx-gnss", MODE="0640", ENV{ID_MM_DEVICE_IGNORE}="1", SYMLINK+="lab/gnss", TAG+="systemd"
```

- `998000.serial` — фіксований UART6 плати, а не запис `devices.json`, тому точна схема `devices.json` (`schema_version` 1) не змінюється.
- `0640`: група лише читає, інші не мають доступу. `srrx-gnss` — системна група без login-членів, бо NMEA розкриває місцезнаходження. Її створюють до встановлення правила: `groupadd --system srrx-gnss`. Відсутня група **не** дає fail closed: невідому `GROUP` udev пропускає, і вузол може зберегти групу стандартних правил (`50-udev-default.rules` дає `dialout` для `ttyHS*`), тож NMEA змогли б читати члени `dialout`. Фактичного власника й режим перевіряють `stat -L /dev/lab/gnss` на Q6A (RUNTIME_ONLY). У сирому режимі групу `srrx-gnss` отримує лише `srrx-locationd` через згенерований drop-in `srrx-locationd.service.d/40-gnss-mode.conf` (`SupplementaryGroups=srrx-gnss`); labd її не має в жодному режимі, а udev-кандидат сам групу не створює ([DEPLOYMENT](DEPLOYMENT.md)).
- ModemManager не надсилає AT-проби (`ID_MM_DEVICE_IGNORE`).
- RUNTIME_ONLY на Q6A: `udevadm info`, справжній `ls -l /dev/lab/gnss`, права вузла після старту gpsd (gpsd під root перед скиданням привілеїв може змінювати права пристрою — перевірити `stat`) і те, що gpsd після скидання привілеїв повторно відкриває `/dev/lab/gnss` після втрати UART, 20 перезавантажень `ttyHS1 → 998000.serial` (09-testy.md:55, W-04).

## Імпульс RESET у labd

`SafetyPolicy` — єдиний власник I²C. Нова іменована операція:

```python
policy.command("gnss_reset", {"width_ms": 200}, now_ms)   # або None/{} -> 200 ms
engine.request({"op": "gnss_reset", "value": {"width_ms": 200}, "_owner": "uid:1000"})
```

```bash
# Поки `labctl hold --arm` того самого користувача тримає оренду:
PYTHONPATH=software:. python3 -m srrx.cli gnss_reset --width-ms 200
```

Сирий запис ланцюга `E3_GNSS_RESET_GATE` і далі відхиляється загальним whitelist (`raw GPIO is forbidden`), як у озброєному, так і в неозброєному стані.

### Передумови

| Перевірка | Де | Відмова |
|---|---|---|
| Власна чинна оренда того, хто запитує (немає оренди — немає власника) | Engine | `gnss_reset requires the caller's own valid lease` |
| Engine `configured`, ARM не очікує підтвердження | Engine | `… configured MCP outputs and no pending arm` |
| Свіжий статус Pico (≤500 ms), `mcp_reset == False` | Engine | `… fresh Pico status with MCP RESET released` |
| `policy.fault is None` | Policy | `fault latched: …` |
| Чинна оренда | Policy | `valid owner lease required` |
| `width_ms` — ціле (не bool) 100..500, за замовчуванням 200; інших ключів немає | Policy | `GNSS_RESET_WIDTH` |
| `hardware.initialized`, без засувки помилки адаптера | Policy | `GNSS_RESET_HARDWARE` |
| Імпульс не триває, лінія низька | Policy | `GNSS_RESET_IN_PROGRESS` |
| ≥30 s від **відпускання** попереднього імпульсу (холодний TTFF 28 s, 09-testy.md:179) | Policy | `GNSS_RESET_SPACING` |
| ≤3 імпульси за ковзні 15 хв | Policy | `GNSS_RESET_RATE_LIMIT` |

Імпульс нічого не живить, тому сам об'єкт `SafetyPolicy` дозволяє його і в неозброєному стані. **Через labd/labctl імпульс можливий лише в озброєному, налаштованому сеансі** (Pico ACTIVE). `Engine.configured` встановлює лише ARM-потік (CONFIGURING), кожен trip його скидає, а ARM, що очікує підтвердження, відхиляється. Тому `labctl hold --arm` — обов'язкова умова, а не лише приклад. Імпульс не перезапускається й не ескалюється автоматично.

### Часові межі

- Assert: запис `E3_GNSS_RESET_GATE=True`. `tick()` знімає імпульс на першому тіку ≥ start + width; Engine тікає кожні 20 ms. Якщо Pico-статус застарів, Engine все одно викликає `policy.tick`, поки імпульс триває.
- Жорсткий дедлайн 1000 ms: пізніший тік одразу знімає імпульс і записує `GNSS_RESET_OVERRUN`. Довше утримання RESET_N нічого не живить, тому це не trip.
- Невдалий запис зняття → `trip()` → `all_off()`. Якщо `all_off()` повернувся без помилки на ініціалізованому, відкритому адаптері, `LinuxHardware` записав і прочитав назад OLAT та IODIR кожного MCP. Тоді відпускання доведено: стан `IDLE`, `GNSS_RESET_DEASSERT_FAILED`, `release_ms` — момент цього запису.
- Програмний образ виходів не є доказом. `LinuxHardware.all_off()` спершу скидає образ до безпечного і лише потім кидає «Safe outputs not confirmed», тож після будь-якої спроби образ показує низький затвор. Тому стан визначає результат безпечного запису, а не образ. Якщо `all_off()` не підтверджено (`SAFE_UNCONFIRMED`) або адаптер не ініціалізовано чи вже закрито (тоді `all_off()` без помилки, але нічого не пише — наприклад, після невдалої повторної ініціалізації), стан стає `RELEASE_UNCONFIRMED`, `release_ms` і `last_width_ms` лишаються `None`, а `last_error` — `GNSS_RESET_RELEASE_UNCONFIRMED`. Так само для невдалого assert, для trip чи disarm посеред імпульсу і для засувки адаптера (`LinuxHardware._fail`), яку policy помічає лише на тіку. Повторних спроб запису немає. Нові імпульси заблоковано засувкою помилки й самим станом. Після Pico MCP RESET (outputs high-Z, R326) і нової ініціалізації `clear_fault` з успішним `all_off` переводить стан у `IDLE`. `release_ms` тоді — момент цього доказу, від нього відлічуються 30 s, а `last_width_ms` лишається невідомим (`None`).
- Trip, disarm, `clear_fault` або нова ініціалізація MCP посеред імпульсу відпускають лінію (`GNSS_RESET_ABORTED`), якщо безпечний запис підтверджено; інтервал 30 s відлічується від цього моменту.
- Невдалий запис assert зараховується до ліміту 3 за 15 хв: запис OLAT міг дійти до MCP раніше, ніж збій читання назад. Якщо `all_off()` потім підтверджено, стан `IDLE` з `GNSS_RESET_ASSERT_FAILED`.
- Якщо labd загине посеред імпульсу: тайм-аут HB Pico → MCP RESET через Q306 → виходи high-Z → R326 відпускає скидання. Це спроєктовано, але не кваліфіковано (OPEN_ITEMS.md, E3-08).

### Статус

`policy.status()["gnss_reset"]` (також у `engine.status()["policy"]`):

| Поле | Значення |
|---|---|
| `state` | `IDLE`, `ASSERTED`, `RELEASE_UNCONFIRMED` (`ASSERTING` існує лише всередині запису assert і назовні не видно) |
| `last_ms`, `width_ms`, `release_due_ms` | Початок останнього імпульсу, запитана ширина, плановий момент зняття (лише в `ASSERTED`) |
| `release_ms`, `last_width_ms` | Момент доведеного (прочитаного назад) відпускання і ширина за тіками; `None`, поки відпускання не доведено. Після відновлення з `RELEASE_UNCONFIRMED` `release_ms` — момент доказу, а ширина лишається `None` |
| `pulses_15min` | Початки, зокрема невдалі спроби assert, у ковзному 15-хвилинному вікні |
| `last_error` | Наслідок останнього імпульсу: `None`, `GNSS_RESET_OVERRUN`, `GNSS_RESET_ABORTED`, `GNSS_RESET_DEASSERT_FAILED`, `GNSS_RESET_ASSERT_FAILED`, `GNSS_RESET_RELEASE_UNCONFIRMED` (лишається й після відновлення як історія імпульсу); новий імпульс його скидає |

### Консервативні рішення там, де специфікація неоднозначна

- Інтервал 30 s відлічується від відпускання, а не від початку попереднього імпульсу (довший інтервал).
- «Пізно» до 1000 ms включно — лише зняття; `OVERRUN` — строго після 1000 ms.
- Engine вимагає власної чинної оренди того, хто запитує, а не лише «ніхто інший не володіє», і відмовляє, поки ARM очікує підтвердження.
- Стан `RELEASE_UNCONFIRMED` замість удаваного `IDLE`, коли програма не може довести низький рівень затвора. Доказом є лише запис із читанням назад (зняття, `all_off`, безпечна ініціалізація), а не програмний образ виходів.
- Невдалий assert зараховується до ліміту імпульсів.
- Перший `poll()` читача завжди робить flush; після затримки хоста стан `STARTING`, доки не надійде справжній байт.

### Служба місця навколо імпульсу

Перед імпульсом служба, що тримає трекер (`srrx-locationd`), отримує `invalidate GNSS_RESET`; chrony переводить PPS у `+noselect` (build/07:484); RTC і останній добрий фікс позначаються застарілими. Після імпульсу: дочекатися першого валідного речення, зупинити gpsd, повторно надіслати налаштування з allowlist і прочитати їх назад, знову запустити gpsd. PPS стає вибірним лише після читання назад і воріт 3D ≥6 зі свіжим звітом глушіння «добре» (build/07:500, :503), а після прапорця глушіння — лише після нового холодного перезапуску (build/07:484). Коли labd запущено з `--gnss gpsd` або `--gnss raw`, саме так працює `gnss_reset`: запит лише приймається (`ACCEPTED`), а імпульс з тими самими перевірками того самого власника оренди дає тік labd після підтвердженого `PPS_NOSELECT` ([нижче](#оркестрація-в-labd-srrxgnss_orchestrator)). З `--gnss off` (типово для ручного запуску) `gnss_reset` — простий імпульс, як описано вище.

## Ланцюг часу й місця: srrx-locationd, srrx-timegate, srrx-gnss-config і оркестрація labd

Код і хостові тести реалізовано (справжні Linux PTY і AF_UNIX-сокети, фальшиві ефекти, симульований Engine). У QEMU guest і на Q6A ці служби не запускали; усе нижче — SIMULATION/EMULATION, а не апаратний PASS. labd лишається лише AF_UNIX і єдиним власником I²C: UART, gpsd і сокет chrony він сам не відкриває.

| Частина | Unit, користувач | Що може | Інтерфейс |
|---|---|---|---|
| `srrx.locationd` | `srrx-locationd.service`, `srrx-loc`; група `srrx-gnss` лише в сирому режимі | єдиний читач позиції: `GpsdClient` до loopback gpsd або `NmeaUartReader` на `/dev/lab/gnss` | `/run/srrx-loc/location.sock` |
| `srrx.timegate` | `srrx-timegate.service`, `_chrony` | лише `chronyc selectopts PPS ±noselect` і `reselect` | `/run/srrx-timegate/timegate.sock` |
| `srrx.gnss_config` | `srrx-gnss-config.service`, root, oneshot | зупинити читача, прочитати налаштування назад, записати allowlist лише при розбіжності, запустити читача | `/run/srrx-gnss-config/result.json` |
| `srrx.gnss_orchestrator` | усередині labd (`srrx.service`, `labd`) | план кроків навколо `gnss_reset`; імпульс — лише через `SafetyPolicy` | неблокувальні AF_UNIX-запити й `systemctl start` через polkit |

Кожна служба має власний `RuntimeDirectory`. `/run/srrx` — каталог labd (`labd:labd 0750`), systemd видаляє його разом із зупинкою labd, і інша служба не може створити в ньому сокет; тому сокет місця — `/run/srrx-loc/location.sock`, а не `/run/srrx/location.sock`.

### srrx-locationd

- Режим — `--gnss ${SRRX_GNSS}` з `/etc/srrx/devices.env`: `gpsd`, `raw` або `off` (служба одразу завершується з кодом 0 і нічого не читає).
- **gpsd**: `JammingGpsdClient` — той самий `GpsdClient` ([LOCATION](LOCATION.md)), але з `?WATCH={"enable":true,"json":true,"raw":1};`, щоб gpsd додав сирі NMEA-рядки приймача. Рядки, що починаються з `{`, без змін ідуть у `GpsdJSONDecoder` (ті самі межі й лічильник помилок), рядки з `$` — лише в монітор глушіння, решта відкидається. `GpsdClient` сам не перепідключається: після розриву служба створює новий клієнт не частіше ніж раз на 5 s. Статичний unit дозволяє лише `AF_UNIX` і `IPAddressDeny=any`; drop-in gpsd-режиму додає `AF_INET AF_INET6` і `IPAddressAllow=localhost`. Якщо процес має групу `srrx-gnss`, старт відхиляється (`LOCATIOND_GNSS_GROUP_IN_GPSD_MODE`).
- **raw**: до відкриття UART — `DEVICES` з `/etc/default/gpsd` (також за `realpath`) не містить `/dev/lab/gnss` (`LOCATIOND_GPSD_CONFIGURED_FOR_UART`), а `systemctl is-active --quiet` для `gpsd.service` і `gpsd.socket` повертає 3 (LSB «не працює»: inactive, failed або такого unit немає). Код 0 — відмова `LOCATIOND_GPSD_ACTIVE`; будь-який інший код (1 — немає з'єднання з шиною чи доступу, 4 — стан невідомий) і недоступний або завислий (>10 s) `systemctl` — відмова `LOCATIOND_GPSD_STATE_UNKNOWN` (fail closed). Далі `open_lc76g()` і `NmeaUartReader`, якому `TeeTracker` передає ті самі байти трекеру й монітору глушіння. Втрата UART завершує процес з кодом 3; нове відкриття дає `Restart=on-failure` (`RestartSec=5`) — явне рішення служби, як вимагає читач. Drop-in сирого режиму: `SupplementaryGroups=srrx-gnss`, `Wants=`/`After=dev-lab-gnss.device`, `Conflicts=gpsd.service gpsd.socket`.
- **Сирий режим дає лише позицію, а не час.** gpsd зупинено, тож `refclock SHM 0 refid NMEA` із build/07 §18 (його живить лише gpsd) не отримує зразків, а `refclock PPS … lock NMEA` без них відкидає кожен імпульс. Тому labd у сирому режимі PPS не обирає взагалі: плани закінчуються станом `POSITION_ONLY` з попередженням `RAW_MODE_NO_NMEA_SHM`, а chrony лишається без GNSS-дисциплінування.
- Протокол сокета: один рядок JSON запиту (≤512 байт), один рядок відповіді, закриття; ≤8 клієнтів, кожен ≤2 s.

| Запит | Хто | Відповідь |
|---|---|---|
| `{"op":"snapshot"}` | UID `labd` або член групи `labd` (оператори консолі, які й так бачать позицію в HMI) | `{"ok":true,"data":{…}}` |
| `{"op":"invalidate","reason":"GNSS_RESET"}` | лише UID `labd` | обидва джерела трекера (`gpsd`, `nmea`) недійсні з цією причиною |
| будь-що інше | — | `LOCATIOND_UNKNOWN_REQUEST`, `LOCATIOND_REQUEST`, `LOCATIOND_REQUEST_JSON`, `LOCATIOND_PEER_REFUSED` |

- Авторизація — облікові дані ядра (`SO_PEERCRED`), як у labd; сторонній UID закривається ще до читання. Сокет `0666` у каталозі `0755`, у який може писати лише служба: файлова група вимагала б, щоб `srrx-loc` сам був у групі `labd`, а з нею мав би доступ і до `/run/srrx/control.sock`.
- Знімок: `schema_version` (1), `mode`, `location` (рівно `LocationTracker.status()`), `qualified_fix`, `jamming` (`active`, `status`, `source`, `error`, `reports`, `age_ms`), `reader` (стан `NmeaUartReader` або `connected`/`watching`/`error`/`connects` клієнта gpsd), `resets` (кількість `GNSS_RESET`), `last_invalidate`.
- `qualified_fix` — ворота PPS (build/07:503): живий свіжий фікс (≤3 s), `mode == 3`, відома кількість супутників ≥6 і немає прапорця глушіння. Після `invalidate` останній добрий фікс лишається доступним лише як `source: last_good` з `reason: GNSS_RESET` (застарілий), доки те саме джерело не дасть новий прийнятий фікс.
- Глушіння (build/07:484, :498): `$PAIRSPF,<статус>` і `$PQTMJAMMINGSTATUS,1,<статус>`; статус ≥2 — глушіння. Некоректний статус або версія повідомлення не 1 теж вважаються глушінням (fail closed); речення з хибною контрольною сумою вердикту не дає. Прапорець тримається 60 s після останнього такого звіту, а годинник назад його не старить. Положення полів узято з build/07 і специфікації протоколу Quectel v1.5; на справжній прошивці LC76G їх ще не звіряли.
- Позиція є лише в знімку на локальному сокеті: журнал, файл і мережа її не отримують, коди помилок координат не містять.

### srrx-timegate

- Працює як `_chrony`: chronyc 4.5 приймає `selectopts` лише через Unix-сокет chronyd, тобто від root або користувача chrony. labd таких прав не має й не отримує.
- Рівно два запити, кожен — один рядок ≤32 байти: `PPS_SELECT` → `chronyc -n -h /run/chrony/chronyd.sock selectopts PPS -noselect`, потім `chronyc -n -h /run/chrony/chronyd.sock reselect`; `PPS_NOSELECT` — те саме з `+noselect` (build/07:484). Аргументів із запиту немає, shell немає, оточення лише `PATH` і `LC_ALL=C`, кожен виклик ≤5 s. `-h` указує Unix-сокет, тож chronyc не переходить на UDP 127.0.0.1. Невдалий `selectopts` не запускає `reselect`.
- Обслуговується лише UID labd (`SO_PEERCRED`); інших закривають до читання. Відповідь: `{"ok":true,"command":"PPS_SELECT"}` або код (`TIMEGATE_PEER_REFUSED`, `TIMEGATE_UNKNOWN_COMMAND`, `TIMEGATE_REQUEST_FRAMING`, `TIMEGATE_CHRONYC_SELECTOPTS_EXIT`, `…_RESELECT_TIMEOUT`, `…_EXEC`).
- Unit: `PrivateNetwork=yes`, `RestrictAddressFamilies=AF_UNIX`, `CapabilityBoundingSet=`, `ReadWritePaths=-/run/chrony` (chronyc створює там власний клієнтський сокет).
- За build/07 §18 обидва refclock мають `noselect`: без timegate PPS ніколи не обирається, а NMEA (SHM) лишається `noselect` завжди й служить лише для `lock NMEA`. Отже `PPS_NOSELECT` зупиняє дисциплінування, а chrony тримає годинник за останньою оцінкою. SHM NMEA живить лише gpsd, тож у сирому режимі цей ланцюг не працює (див. «srrx-locationd»).
- Перезапуск chronyd повертає PPS до `noselect` із chrony.conf. Ні timegate, ні labd цього не бачать: PPS знову обирає лише наступний план labd (`gnss_config`, `gnss_reset` або перезапуск labd). Це безпечний бік (PPS не дисциплінує), але `pps_gate_open` у статусі labd тоді не означає, що chrony використовує PPS ([нижче](#оркестрація-в-labd-srrxgnss_orchestrator)).

### srrx-gnss-config

Root oneshot без `[Install]`; його запускає лише labd (polkit). Кроки:

1. зупинити єдиного читача UART: `gpsd.socket` і `gpsd.service` (режим gpsd) або `srrx-locationd.service` (сирий режим); приймач записують лише тоді, коли його ніхто не читає (build/07:485);
2. відкрити `/dev/lab/gnss` як `O_RDWR` з тією самою прив'язкою, що й `open_lc76g` (псевдонім, батько `998000.serial`, `dev` = `st_rdev`), `flock` (зайнято → `GNSS_CONFIG_UART_BUSY`) і `TIOCEXCL`, raw 115200 з читанням назад;
3. дочекатися першого речення з правильною контрольною сумою, ≤40 s (після RESET приймач спершу завантажується);
4. `$PQTMVERNO`, потім читання назад PPS, DGPS і SBAS;
5. лише при розбіжності — записи й збереження, потім друге читання назад;
6. закрити UART, знову запустити читача (і після невдачі), атомарно записати `result.json`.

| Ключ | Речення | Очікувана відповідь | Коли |
|---|---|---|---|
| `version` | `$PQTMVERNO*58` | `$PQTMVERNO,<версія>,…` | щоразу |
| `pps_read` | `$PQTMCFGPPS,R,1*6A` | `$PQTMCFGPPS,OK,1,1,100,3,0,0` | щоразу, читання назад |
| `dgps_read` | `$PAIR401*3F` | `$PAIR001,401,0`, потім `$PAIR401,2` | щоразу, читання назад |
| `sbas_read` | `$PAIR411*3E` | `$PAIR001,411,0`, потім `$PAIR411,1` | щоразу, читання назад |
| `pps_write` | `$PQTMCFGPPS,W,1,1,100,3,0,0*70` | `$PQTMCFGPPS,OK` | лише при розбіжності |
| `save_pqtm` | `$PQTMSAVEPAR*5A` | `$PQTMSAVEPAR,OK` | лише при розбіжності |
| `jamming_detect` | `$PAIR391,1*2C` | `$PAIR001,391,0` | лише при розбіжності |
| `sbas_enable` | `$PAIR410,1*22` | `$PAIR001,410,0` | лише при розбіжності |
| `dgps_sbas` | `$PAIR400,2*20` | `$PAIR001,400,0` | лише при розбіжності |
| `save_pair` | `$PAIR513*3D` | `$PAIR001,513,0` | лише при розбіжності |
| `jamming_rate` | `$PQTMCFGMSGRATE,W,PQTMJAMMINGSTATUS,1,1*11` і ще раз `$PQTMSAVEPAR*5A` | `$PQTMCFGMSGRATE,OK` | лише з `--jamming-status-message` («опційно», build/07:498) |

- `$PAIR001,<id>,1` означає «ще виконується» (чекати далі), будь-який інший ненульовий результат — відмова (`LC76G_PAIR_RESULT_<n>`), `…,ERROR,…` — `LC76G_REPLY_ERROR`, інші поля — `LC76G_REPLY_MISMATCH`. Кожна відповідь ≤1.5 s; сторонні NMEA-рядки між командою й відповіддю пропускаються (≤400). Положення полів відповідей узято з тієї самої специфікації й на прошивці LC76G ще не звірені.
- Тест перераховує всі 12 контрольних сум (11 речень allowlist і `$PAIR006*3C`, якого інструмент не надсилає: холодний старт дає імпульс RESET) і звіряє їх з build/07 §18 так само, як було зроблено 24.10.2026.
- Шлях запису в UART один: псевдонім `_uart_write`, який викликає лише `Port.send` після перевірки allowlist. `$PAIR007`, `$PAIR752` і `$PAIR753` відхиляються за назвою (`GNSS_CONFIG_FORBIDDEN_SENTENCE`), будь-що інше — allowlist (`GNSS_CONFIG_NOT_ALLOWLISTED`); стаціонарний режим і оновлення прошивки поза allowlist надіслати неможливо.
- `result.json` (`0644`, атомарна заміна, без координат): `ok`, `error`, `readback_match`, `wrote`, `version`, `readback`, `sent`, `reader_restarted`, `started_boottime_ms`, `finished_boottime_ms` (CLOCK_BOOTTIME), `mode`. Старий результат видаляється на початку кожного запуску. Код виходу 0 лише при збігу читання назад; невдалий повторний запуск читача — `GNSS_CONFIG_READER_START_FAILED`.
- Межі часу: кожен виклик `systemctl stop|start` ≤15 s (`SYSTEMCTL_TIMEOUT_S`), перше речення ≤40 s, щонайбільше 15 речень по ≤1 s запису й ≤1.5 s відповіді — разом близько 108 s, менше за `TimeoutStartSec=120`. SIGTERM під час кроків 1-5 (після `TimeoutStartSec` або ручний `systemctl stop srrx-gnss-config`) завершує їх кодом `GNSS_CONFIG_TERMINATED`, а крок 6 усе одно виконується: читач запускається знову, `result.json` записується. Повторний SIGTERM під час цього лише записується; SIGKILL настає не раніше ніж через `TimeoutStopSec=30`.
- Unit: `PrivateNetwork=yes`, `RestrictAddressFamilies=AF_UNIX` (лише для `systemctl`), `CapabilityBoundingSet=CAP_DAC_OVERRIDE`, `TimeoutStartSec=120`, `TimeoutStopSec=30`, `RuntimeDirectoryPreserve=yes` (результат переживає завершення oneshot).

### Оркестрація в labd (`srrx.gnss_orchestrator`)

`srrx.service` запускає labd з `--gnss ${SRRX_GNSS}`; з `off` оркестрації немає. Стан-машина чиста: ефекти (`invalidate`, `pps`, `snapshot`, `config`) повертають об'єкти, які тік labd опитує без блокування; таймаут HB Pico — 750 ms (firmware/pico/supervisor.py).

| План | Кроки |
|---|---|
| `boot` (перший тік labd) | PPS noselect → налаштування з читанням назад → кваліфікований фікс → PPS select |
| `reset` (`gnss_reset`) | locationd `invalidate GNSS_RESET` → PPS noselect → RTC і останній добрий фікс застарілі → імпульс 200 ms через policy → доведене відпускання → налаштування (воно ж чекає першого речення) → кваліфікований фікс → PPS select |
| `config` (`gnss_config`) | як `boot`, на запит оператора |
| `watch` (сам, у `SELECTED`) | PPS noselect → кваліфікований фікс → PPS select; коли 5 s немає знімка або свіжого звіту глушіння «добре» |

У сирому режимі кроки «кваліфікований фікс» і «PPS select» замінює `position_only`: кожен план закінчується станом `POSITION_ONLY` без вибору PPS (див. «srrx-locationd»). Із засувкою глушіння план `boot` — лише PPS noselect, далі `JAMMED`.

| Межа | Значення |
|---|---|
| Опитування знімка | 1 s, у кожному кінцевому стані теж |
| Утримання `qualified_fix` перед PPS select | 10 s без жодного некваліфікованого чи відсутнього знімка і без знімка без свіжого звіту глушіння «добре» |
| Свіжий звіт глушіння (`$PAIRSPF`/`$PQTMJAMMINGSTATUS`, статус 1) | ≤5 s (`JAMMING_FRESH_MS`) |
| `SELECTED` без такого звіту чи без знімка | 5 s, далі план `watch` (`WATCH_LOST_MS`) |
| Повтор невдалого noselect (`boot`, `watch` і щоразу, коли PPS ще може бути обрано) | кожні 5 s, доки не підтверджено |
| Доведене відпускання після імпульсу | ≤2 s, інакше `GNSS_RESET_RELEASE_TIMEOUT` |
| Перше речення в `srrx-gnss-config` | ≤40 s |
| Увесь крок налаштування | ≤150 s, інакше `GNSS_CONFIG_TIMEOUT` |
| Кваліфікований фікс | ≤15 хв, інакше `FIX_TIMEOUT` |

- Імпульсу немає без підтвердженого `PPS_NOSELECT`: у планах `reset` і `config` невдалий noselect завершує план без імпульсу й налаштування (`PPS_NOSELECT_FAILED`). Якщо PPS перед тим міг бути обраним, labd далі повторює лише noselect кожні 5 s (стан `PPS_NOSELECT_FAULT`), доки його не підтверджено, і тільки тоді стан `FAILED`. Нескінченний повтор noselect плану `boot` (немає timegate, chronyd чи refclock PPS, а налаштування chrony ставлять вручну) оператора не блокує: `gnss_reset` і `gnss_config` замінюють його. Відмова `GNSS_ORCHESTRATION_BUSY: <стан>` іншим крокам містить у дужках і `last_error`.
- Невдалий `invalidate` (locationd недосяжний, таймаут або відмова, наприклад коли всі 8 клієнтських місць зайняті операторами) записується як попередження `LOCATION_INVALIDATE_FAILED` і план не зупиняє. Тоді знімок locationd ще кілька секунд показує старий фікс як живий, доки той не застаріє (`fresh_ms` 3 s, а на час налаштування gpsd або сам locationd зупинено). Меню HMI з власним `GpsdClient` у режимі gpsd інвалідацію не отримує ніколи: його фікс старіє за `fresh_ms` або з розривом з'єднання, коли `srrx-gnss-config` зупиняє gpsd.
- `gnss_reset` спершу проходить ті самі перевірки, що й раніше (власна чинна оренда, налаштовані виходи MCP, свіжий статус Pico без MCP RESET), і перевірку самої policy (`gnss_reset_refusal`: ширина, інтервал 30 s, 3 за 15 хв, засувка) — ще до зняття вибору PPS. Відповідь — `{"ok":true,"state":"ACCEPTED",…}`; імпульс дає наступний тік з повторною перевіркою того самого власника. Якщо policy все ж відмовляє, приймач не скидався: попередження `GNSS_RESET_REFUSED` і далі план `config` (із засувкою глушіння — `JAMMED`, без налаштування).
- Ворота глушіння fail closed. Кожен знімок у вікні 10 s мусить мати свіжий (≤5 s) звіт зі статусом 1 («добре»): це єдиний знак, що виявлення глушіння приймача взагалі доходить до locationd. Без жодного звіту (`reports == 0`: не працює `"raw":1` gpsd, `$PAIR391` не діє або речення не виводиться), зі старим звітом чи зі статусом 0 («невідомо») PPS не обирається (`jamming_visible: false`). У `SELECTED` знімок без такого звіту або недосяжний locationd довше 5 s знімає PPS з вибору й запускає план `watch` (попередження `JAMMING_WATCH_LOST`); коли звіти повертаються, PPS обирається знову після тих самих 10 s, без скидання, бо прапорця не було. Частоту `$PAIRSPF` на прошивці LC76G не підтверджено: якщо речення приходить рідше ніж раз на 5 s, PPS не обирається ніколи. Тоді після виміру на Q6A змінюють `JAMMING_FRESH_MS` або вмикають `PQTMJAMMINGSTATUS` (`--jamming-status-message`, build/07:498; записується лише в проході із записом, тобто при розбіжності читання назад).
- `RELEASE_UNCONFIRMED`, невдале налаштування (`GNSS_CONFIG_FAILED: <код>`) і `FIX_TIMEOUT` — кінцеві стани з PPS у `noselect`; якщо після невдалого select PPS міг бути обраним, перед `FIX_TIMEOUT` його знову знімають з вибору. Прапорець глушіння в будь-який момент (під час плану й у кожному кінцевому стані) — `PPS_NOSELECT_JAMMING` (повтор кожні 5 s, доки не підтверджено) і засувка `JAMMED`.
- Засувка `JAMMED` виконує build/07:484: після прапорця — холодний перезапуск і повторне надсилання налаштувань, і лише тоді довіра PPS. Тому `gnss_config` у засувці відхиляється (`GNSS_JAMMED_RESET_REQUIRED`), вийти можна лише через `gnss_reset`, а знімається засувка тільки після доведеного відпускання імпульсу; повторне надсилання налаштувань — крок налаштування того самого плану (читання назад і запис при розбіжності, build/07:500). Відхилений policy або не доведений імпульс засувку не знімає. Якщо прапорець ще тримається (60 s після останнього звіту), план після скидання засувається знову, тож скидати варто, коли `jamming_active: false`.
- Засувка переживає перезапуск labd і ОС: файл `/var/lib/srrx-gnss/jamming-latch.json` (`StateDirectory=srrx-gnss`, `0700`; атомарне перейменування без fsync, щоб тік не чекав на носій: знеструмлення, яке могло б утратити запис, саме є холодним перезапуском LC76G). З ним план `boot` лише знімає PPS з вибору й завершується `JAMMED` (`GNSS_JAMMED_RESET_REQUIRED`) без налаштування й select. Нечитабельний або несподіваний файл чи відсутній каталог — теж засувка (`latch_error`: `GNSS_JAM_LATCH_UNREADABLE`, `GNSS_JAM_LATCH_DIRECTORY_MISSING`); невдалий запис — `GNSS_JAM_LATCH_STORE_FAILED`. Видалити файл вручну означає оминути вимогу build/07:484; правильний вихід — `gnss_reset`.
- Автоматичного повторного RESET, повтору імпульсу чи ескалації немає; ліміти policy діють як і раніше.
- Результат `srrx-gnss-config` приймається лише з `started_boottime_ms` не раніше моменту запиту (CLOCK_BOOTTIME); вердикт попереднього запуску ігнорується. Запуск — `systemctl --no-ask-password --no-block start srrx-gnss-config.service` (≤10 s, інакше `GNSS_CONFIG_START_TIMEOUT`; відмова polkit — `GNSS_CONFIG_START_REFUSED`).
- Помилка самої оркестрації дає `FAILED` з `GNSS_ORCHESTRATOR_ERROR: <тип>` і ніколи не trip policy живлення. Якщо PPS тоді міг бути обраним, labd спершу знімає його з вибору (`PPS_NOSELECT_FAULT`, повтор кожні 5 s) і лише потім ставить `FAILED`; знімки й там опитуються щосекунди, тож прапорець глушіння засувається і в `FAILED`.
- Операції labd: `gnss_reset` (як вище) і `gnss_config` (власна чинна оренда; з `--gnss off` — `GNSS_ORCHESTRATION_OFF`; у засувці — `GNSS_JAMMED_RESET_REQUIRED`). CLI: `labctl gnss_reset --width-ms 200`, `labctl gnss_config`.

`engine.status()["gnss"]` (`None` при `--gnss off`): `state` (`STARTING`, `LOCATION_INVALIDATE`, `PPS_NOSELECT`, `RESET_PULSE`, `RESET_RELEASE`, `GNSS_CONFIG`, `AWAIT_FIX`, `PPS_SELECT`, `SELECTED`, `POSITION_ONLY`, `PPS_NOSELECT_JAMMING`, `JAMMED`, `PPS_NOSELECT_FAULT`, `FAILED`, `FIX_TIMEOUT`), `step`, `plan`, `orchestration` (`boot`, `reset`, `config`, `watch`), `pps_selected` (останній підтверджений запит timegate; `None` — невідомо, зокрема після невдалого select), `rtc_stale`, `pps_gate_open` (`SELECTED`, PPS обрано і RTC не застарілий), `jamming_seen` (від старту labd), `jamming_active` і `jamming_visible` (з останнього знімка; `None` — знімка немає), `reset_required` (засувка), `latch_error`, `qualified_since_ms`, `last_error`, `warnings`, `config` (`ok`, `error`, `readback_match`, `wrote`, `version`), `events` (16 останніх кодів), `automatic_reset: false`. Координат у статусі немає. `pps_gate_open` — ворота labd, а не доказ, що chrony справді обрав PPS: після перезапуску chronyd PPS знову `noselect`, а chrony може не обрати PPS і з власних причин. Справжній вибір показують `chronyc -n sources` (PPS із `*`) і `chronyc -n selectdata` на Q6A (build/07:502).

### Розгортання

- Облікові записи: системна група `srrx-gnss` без членів (як і раніше), системний користувач `srrx-loc` зі своєю групою без login-оболонки (`useradd --system --user-group --no-create-home --shell /usr/sbin/nologin srrx-loc`), `_chrony` з пакета chrony (`getent passwd _chrony` на noble — RUNTIME_ONLY).
- `python3 deployment/deploy.py stage --dest <нова тека> --devices devices.json --gnss gpsd|raw|off` (типово `gpsd`) записує `SRRX_GNSS=<режим>` у `etc/srrx/devices.env`. Для `gpsd` і `raw` ще: `etc/polkit-1/rules.d/60-srrx-gnss-config.rules`, `srrx-locationd.service.d/40-gnss-mode.conf`, `dev-lab-gnss.device.d/50-srrx-device-timeout.conf` (30 s) і в режимі gpsd — `gpsd.service.d/30-lab-devices.conf` з `Wants=`/`After=dev-lab-gnss.device` (`gpsd -n` відкриває UART при старті). Так читач GNSS упорядковано після свого вузла (DEP-11 для ланцюга GNSS); `srrx.service` після `dev-lab-gnss.device` не впорядковано, бо labd цей вузол не відкриває. Статичні units пристроїв не згадують: QEMU guest без `/dev/lab` не чекає нічого.
- Правило polkit дозволяє користувачу `labd` рівно `start` для `srrx-gnss-config.service`: ні `stop`/`restart`, ні інших units, ні інших користувачів.
- `srrx.service` має `StateDirectory=srrx-gnss` (`StateDirectoryMode=0700`, власник `labd`) для файла засувки глушіння; labd бере шлях з `--gnss-latch` (типово `/var/lib/srrx-gnss/jamming-latch.json`); `ProtectSystem=strict` лишається: systemd робить цей каталог записуваним так само, як `RuntimeDirectory`.
- Три нові units не отримують release guard (`20-release-guard.conf`): вони нічого не живлять, працюють як `srrx-loc`/`_chrony` без доступу до записів приймання й cache, а oneshot не повинен хешувати cache при кожному запуску з labd.
- Налаштування gpsd і chrony за build/07 §18 тепер пише stage ([DEPLOYMENT](DEPLOYMENT.md), «Системні файли»): `/etc/default/gpsd` за режимом, udev `/dev/pps-gnss` і чорний список модулів gnss. Offset NMEA (`<виміряна медіана>`) ще не виміряно, тому рядки `refclock … noselect` stage кладе лише як інертний `etc/chrony/conf.d/60-srrx-gnss.conf.candidate` з `TBD_MEASURED_MEDIAN_S`; активним файлом його роблять після виміру.
- `deploy.py doctor` (і release guard labd) перевіряє за файлами, що UART читає рівно один: `SRRX_GNSS` задано; у режимі gpsd `DEVICES` рівно `/dev/lab/gnss`, `GPSD_OPTIONS` містить `-n -b`, `USBAUTO="false"`; у сирому режимі gpsd не перелічує `/dev/lab/gnss`, не ввімкнений (`*.wants/gpsd.service|socket`), а drop-in locationd з групою `srrx-gnss` є; поза сирим режимом цього drop-in немає. Release guard labd працює від користувача `labd`, тож `devices.env` і `/etc/default/gpsd` мають бути для нього читабельними (наприклад, `0640 root:labd`); нечитабельний файл блокує старт так само (`GNSS reader configuration unreadable`). Живий стан служб на Q6A — RUNTIME_ONLY.

### Що лишається відкритим

- QEMU guest (BUILDER, ще не зроблено): заблоковані деби gpsd, chrony і gpsd-clients (залежать від source-lock); `gpsfake` з безіменним синтетичним журналом NMEA разом із `$PAIRSPF`; чи справді gpsd 3.25 з `"raw":1` перемежовує сирі NMEA з JSON; chrony із SHM NMEA і тестовим `refclock SHM 1 refid PPS` для перевірки перемикання `selectopts` (`chronyc -n selectdata`); правило polkit на polkit noble (labd запускає, не зупиняє, інші користувачі відхилені); `systemd-analyze verify` трьох units; `StateDirectory` labd і старт labd із наявним файлом засувки; SIGTERM `srrx-gnss-config` посеред `systemctl stop gpsd`.
- Q6A (RUNTIME_ONLY/BENCH): справжній UART6 (09-testy.md:55, W-04), поля відповідей прошивки LC76G (`$PQTMVERNO`, `PQTMCFGPPS,R`, `PAIR401`/`PAIR411`, результати `PAIR001`) і положення статусу глушіння, частота `$PAIRSPF` після `$PAIR391,1` і чи переживає `$PAIR391` збереження та знеструмлення (W-05: «є PAIRSPF»), pps-gpio, вибір PPS chrony протягом 10 хв після 3D-фіксу (build/07:502) і після перезапуску chronyd, GNSS-01/GNSS-02, E3-08, повторне відкриття UART gpsd після втрати, `stat -L /dev/lab/gnss` після старту gpsd.
- Меню HMI у режимі gpsd і далі читає gpsd напряму (`location_callbacks`); переведення консолі на знімки `srrx-locationd`, без якого в сирому режимі меню позиції не бачить, не виконано.

## Перевірки

```sh
PYTHONPATH=software python3 -m unittest discover -s software/tests -p 'test_gnss_*.py' -v
PYTHONPATH=software python3 -m unittest discover -s software/tests -p 'test_locationd.py' -v
PYTHONPATH=software python3 -m unittest discover -s software/tests -p 'test_timegate.py' -v
python3 -m unittest discover -s deployment/tests -p 'test_gnss_chain.py' -v
python3 deployment/module_lab/location_scenarios.py --project . --output /tmp/srrx-location.json
```

- `test_gnss_orchestrator.py` (фальшиві ефекти, симульований Engine з `SimHardware`/`SimLink`, справжні AF_UNIX-сокети): boot обирає PPS лише після читання назад і 10 s кваліфікованого фіксу; будь-який некваліфікований знімок починає вікно заново; без свіжого звіту глушіння «добре» (немає звітів, старий, статус 0, поля немає) PPS не обирається; `reset` знімає вибір PPS до імпульсу і обирає знову після налаштування й фіксу; без підтвердженого noselect імпульсу немає, а noselect повторюється, доки PPS міг бути обраним; відхилений імпульс веде до плану `config`; `RELEASE_UNCONFIRMED`, невдале налаштування, таймаути налаштування й фіксу — без повторів; невдалий select робить `pps_selected` невідомим, і перед `FIX_TIMEOUT` PPS знову знімають з вибору; глушіння знімає вибір і засувається; `gnss_config` у засувці відхиляється, знімає її лише доведене скидання, а відхилений чи не доведений імпульс — ні; скидання, поки прапорець тримається, засувається знову; засувка переживає перезапуск labd (boot лише знімає PPS з вибору) і файл засувки fail closed; сирий режим ніколи не обирає PPS (`POSITION_ONLY`); помилка в `SELECTED` знімає PPS з вибору до `FAILED`; втрата знімків чи звітів глушіння в `SELECTED` дає план `watch`; невдалий noselect при глушінні повторюється; оператор замінює нескінченний повтор noselect плану `boot`; зайняті плани відхиляють нові запити; у статусі немає координат; через Engine — ширина 99 і зайвий ключ відхиляються до будь-якого ефекту, імпульс 200 ms відпускається, сеанс живлення лишається; помилка оркестрації не робить trip; неблокувальні запити (відповідь шматками, недосяжний сокет, таймаут, некоректна відповідь) і `ConfigRun` (результат лише цього запуску, відмова, таймаут запуску).
- `test_locationd.py` (Linux PTY, AF_UNIX, socketpair замість gpsd): прапорець глушіння (статус 2, некоректний, утримання 60 s, хибна контрольна сума, фрагменти); змішаний потік gpsd на кожній межі фрагментації; `JammingGpsdClient` надсилає `"raw":1` і передає TPV/SKY трекеру, а `$PAIRSPF` — монітору; ворота `qualified_fix` (3D, ≥6 супутників, свіжість, глушіння); `invalidate` лишає лише застарілий `last_good`; перепідключення не частіше 5 s; втрата UART → код 3; байти PTY доходять і до трекера, і до монітора; preflight сирого режиму (неактивним вважається лише код 3 `systemctl is-active`; 1, 4 і сигнал — `LOCATIOND_GPSD_STATE_UNKNOWN`) і gpsd-режиму; авторизація сокета (labd, член групи лише читає, сторонній закритий до читання), некоректні й завеликі запити; перевірки каталогу сокета; статична перевірка, що locationd, timegate і оркестратор не відкривають і не пишуть пристрої.
- `test_timegate.py`: точні argv; лише UID labd і лише два запити; невдалий `selectopts` без `reselect`; таймаут і відсутній chronyc; без shell і з мінімальним оточенням; через справжній сокет — одна відповідь на з'єднання, два рядки, завеликий рядок і порожній другий рядок дають `TIMEGATE_REQUEST_FRAMING` без chronyc, рядок без кінця закривається сервером після `READ_TIMEOUT_S` без chronyc, сторонній UID закритий до читання.
- `test_gnss_config.py` (симульований LC76G на PTY): 12 контрольних сум і точний збіг з build/07 §18 (зокрема заборонені назви); розбір кадрів і відповідей; `Port.send` нічого не надсилає поза allowlist; єдиний шлях запису в UART; збіг читання назад без записів; втрачене налаштування записується раз і читається назад; відмови приймача й налаштування, що «не тримається»; мовчазний приймач і відсутня відповідь обмежені в часі; `run()` зупиняє gpsd або locationd до відкриття й запускає знову навіть після невдачі; SIGTERM посеред зупинки gpsd (окремий процес) дає `GNSS_CONFIG_TERMINATED`, а читач усе одно запускається, `result.json` записується, повторний SIGTERM цього не перериває, межі `systemctl` 15 s; `open_rw` — `O_RDWR`, `TIOCEXCL`, `flock` без витоку дескриптора.
- `deployment/tests/test_gnss_chain.py`: units з найменшими правами й без рядків пристроїв (зокрема `TimeoutStartSec=120`/`TimeoutStopSec=30` oneshot і `StateDirectory=srrx-gnss` labd); stage gpsd/raw/off (правило polkit, drop-ins, `SRRX_GNSS`, відсутність release guard у трьох нових units, впорядкування після `dev-lab-gnss.device`); CLI `stage --gnss`; перевірка doctor «один читач» на тимчасових коренях і на щойно staged rootfs.

- `test_gnss_uart.py` (Linux PTY + тимчасовий sysfs): зворотне читання termios; fd `O_RDONLY` (запис → EBADF), `O_CLOEXEC`; виклик `TIOCEXCL` через інжектований ioctl; прив'язка (правильний батько проходить; хибний батько, шлях `ttyHS1`, сам вузол ядра, звичайний файл, розбіжність `dev` відхиляються без витоку дескриптора); фрагментація між викликами; 64 KiB за кілька обмежених викликів і рівно 8×2048 за виклик; затримка → flush + invalidate без «дописування» старого рядка; пізній перший `poll()` не передає накопичене від відкриття; затримка після тиші дає `STARTING`, а не `RECEIVING`; HUP → `disconnected` без повторного відкриття; тиша 2 s → одноразова інвалідація, 10 s → `SILENT`; статична перевірка, що модуль не має шляху запису; Pico на `998000.serial` відхиляє `validate_devices`/`udev_rules`/`stage`. Тест також запускає NMEA-сценарії module lab із цим виробничим читачем.
- `test_gnss_reset.py` (`SimHardware`, `LinuxHardware` над фальшивим регістровим файлом MCP23017, змодельований Engine із `SimLink`, labctl): assert у t0; ще утримано в t0+199; відпущено в t0+200; trip/disarm/ініціалізація посеред імпульсу; другий імпульс протягом 30 s і четвертий за 15 хв відхилено; ширини 99, 501, `True` відхилено; відмова без ініціалізації, із засувкою, без оренди; пізній тік у t0+5000 → `OVERRUN`; невдале зняття → trip із низьким затвором; сирий `E3_GNSS_RESET_GATE` і далі відхилено. З `LinuxHardware`: зламана шина при знятті, trip, disarm, збої `read_inputs` чи assert дає `RELEASE_UNCONFIRMED` з `release_ms=None`, хоча образ показує низький затвор, а регістр OLAT — ще високий; повторних записів немає; одноразовий збій з успішним `all_off` дає `IDLE`; відновлення лише після MCP RESET і `clear_fault`, а 30 s відлічуються від доказу.

Ці тести не доводять апаратну роботу. Відкритими лишаються: pinmux і справжня швидкість UART6 (09-testy.md:55, W-04), осцилограма імпульсу RESET і всіх виходів MCP #4 (09-testy.md:105, Ж-15), TTFF і `$PQTMVERNO` (09-testy.md:179, GNSS-01), відпускання через Pico/Q306/R326 (E3-08), живий udev/sysfs на Q6A. Усі вони мають статус RUNTIME_ONLY/BLOCKED, а не PASS.
