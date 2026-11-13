# Локальна touch-консоль SR-RX

`srrx.hmi` реалізує Qt-консоль із шістьма сторінками та переносну модель
`ConsoleController`. Команди живлення/комутації передаються тільки службі
`labd` через `srrx.daemon.request_once`; консоль не відкриває GPIO, I²C чи
UART. HTTP-сервера немає. Апаратні дозволи й інтерлоки залишаються у labd/Pico.

## Запуск

Python 3.11+, Linux; PySide6 встановлюється окремо в операторському середовищі.
Із кореня репозиторію після встановлення залежності:

```sh
PYTHONPATH=software:. python3 -m srrx.hmi --socket /tmp/srrx/control.sock --fullscreen
```

Для dev-запуску з `--socket /tmp/srrx/control.sock` labd відмовляє в старті,
якщо каталог сокета не належить його ефективному UID або доступний на запис
групі чи іншим: інакше сторонній обліковий запис може підмінити сокет і отримувати
запити оператора. Застарілий `/tmp/srrx`, що належить іншому обліковому запису, треба
спершу видалити. Новий каталог labd створює з правами 0700, тому консоль
запускають від того самого користувача; у системній службі доступ дає група
`/run/srrx` (`RuntimeDirectoryMode=0750`).

Явна демонстрація без апаратних пристроїв:

```sh
PYTHONPATH=software:. python3 -m srrx.hmi --demo
```

`--demo` запускає окремий справжній `srrx.daemon --simulate --stdio` через
обмежені локальні pipes. Кожен статус містить SIMULATION. Дочірній процес
одержує явний шлях до пакета; наявні елементи PYTHONPATH, зокрема ізольований
Qt, зберігаються. EOF/закриття зупиняє Engine; після обмеженого очікування
завислий дочірній процес припиняється. GUI ніколи не запускає фізичний labd.
Лише перша відповідь daemon має до 10 с на холодний старт (оренди ще немає);
далі діє звичайний timeout 1 с, і пропущена відповідь назавжди закриває SIM daemon.

Без Qt імпорт `srrx.hmi`, модель і її тести працюють; запуск GUI повертає
зрозуміле повідомлення про залежність. Локальні `--help` не потребують Qt.

Опціональне читання вже налаштованого локального gpsd:

```sh
PYTHONPATH=software:. python3 -m srrx.hmi --socket /tmp/srrx/control.sock \
  --gpsd-host 127.0.0.1 --gpsd-port 2947 --gpsd-device /перевірена/ідентичність
```

Endpoint задається явно; `GpsdClient` дозволяє лише loopback. Без цих параметрів
мережевого з'єднання немає. Консоль не налаштовує gpsd, serial device або pinmux.

## ARM, HOLD і відмови

- **ARM + HOLD** — один явний ARM і поновлення оренди раз на секунду, TTL 3 с.
  Виходи починають з OFF; готовність визначає labd/Pico.
- **RECOVER + ARM** — явне відновлення після усунення причини. Чинний backend
  виконує новий ARM handshake; це пояснює напис кнопки й діалог підтвердження.
- **HOLD lease** підтримує вже активний стан. Ця кнопка сама не виконує ARM.
  Натискання під час ARM handshake не скасовує ARM: HOLD уже активний, межа
  handshake 2,5 с і перевірки fault лишаються.
- **DISARM / STOP** припиняє HOLD і просить вимкнути виходи. OFF/PARK доступні
  без активної оренди; backend перевіряє можливість виконання.
- Зміна **field/lab** можлива лише disarmed і застосовується наступним явним ARM.
- **Shutdown** спершу робить DISARM, потім просить штатний ARM_OFF/shutdown.
  OFF_NOW/root poweroff bridge не викликається консольним запитом напряму.

IPC працює в окремому Qt worker. Полінг — 250 мс, socket timeout — 400 мс;
дії мають чергу до 16 записів. Відмова оренди, новий fault, невдалий ARM,
помилка служби чи розрив полінгу >1,5 с припиняють поновлення й викликають
спробу DISARM. labd зберігає перший fault до ACTIVE, тому ARM, перерваний
labd, консоль бачить через `last_error` (ARM його очищує, кожен trip
встановлює) і зупиняє HOLD на першому ж полінгу. Heartbeat GUI також має межу
1,5 с. Після reconnect/fault автоматичного ARM немає. Якщо DISARM не
підтверджений, консоль показує це; останній TTL і незалежний Pico лишаються
обмежувачами дозволу.

Дії Teach / Classify (анотація, навчання, класифікація, load/save датасету й
моделі) виконуються як **одна фонова задача за раз** в окремому потоці Python
(`LearningRunner`), з індикатором прогресу та кнопкою **Cancel learning job**.
Поки задача триває, кнопки цих дій вимкнені, друга задача відхиляється й не
стає в чергу; HOLD лишається ON, DISARM, Shutdown і LOCK доступні. Межі
heartbeat не змінено: `worker.ui_at` оновлює лише GUI thread, тож справжня
зупинка GUI thread і далі знімає HOLD через 1,5 с. Задача отримує лише дані
(датасет, кадр, модель, bins, мітку, шлях) і відокремлену копію засувки
сеансу; вона не викликає labd, не поновлює lease і не торкається Qt-об'єктів,
тому DISARM, fault чи зупинка worker її не скасовують. Cancel спрацьовує на
найближчій контрольній точці `srrx.learning` (кадр, анотація, запис); задача
понад 300 с скасовується автоматично; закриття вікна скасовує задачу й на неї
не чекає. Перевірка смуги box для анотації та класифікації лишається в GUI
thread до старту задачі (засувка й переривання SIM capture одразу, як
раніше). Стоп, який знайшло лише фонове навчання, засувається в сеансі, а
SIM capture переривається тоді, коли задача завершилася, скасована чи
відхилена. Результат застосовується лише в GUI thread і лише якщо за час
задачі не з'явилося нової засувки, а датасет, модель і (для класифікації)
показаний кадр не змінилися; інакше «run it again». Після Cancel результат
відкидається, навіть якщо задача встигла завершитися (крім уже записаного
файлу). Датасет сеансу обмежено 2 MiB файлу консолі: анотацію, після
якої збережений файл перевищив би 2 MiB, відхилено, тож усе зібране в консолі
можна зберегти й знову завантажити (CLI `srrx.learning` має свою межу 64 MiB).
Межа збереження вимірює саме байти файлу (canonical JSON + перевід рядка),
які `load_json` прочитає назад.

Живлення самої консолі (DISP12) вмикає Pico, а не консоль: воно є, поки Q6A
увімкнена, крім OFF/SHUTTING_DOWN, гарячої або невідомої температури панелі
та trip CASE_HOT/FAN_STALLED. Після CASE_HOT чи FAN_STALLED екран темний до
нового прийнятого ARM або фізичного перезапуску, тому відновлення йде через
локальний CLI (`labctl recover` або `labctl arm`); інші trip лишають консоль
увімкненою, щоб показати fault і RECOVER + ARM ([Pico](../firmware/pico/README.md);
політику DISP12 записано в блоці поправок v2.1 [STACK.md](../STACK.md)).

Без свіжого статусу labd банер показує `CONTROL UNKNOWN` і `MODE UNKNOWN`, а не
OFF. Батарея, температури й стан Pico показуються лише тоді, коли labd
повідомляє `pico_fresh=true` (поле `Engine.status()` з тією самою межею 500 мс,
що й відмова ARM; поруч `pico_age_ms` — вік останнього прийнятого статусу Pico
або null). `pico_fresh=false` дає `PICO STATUS STALE` і попередження з цим віком,
що ARM буде відхилено. Якщо labd старішої ревізії поля не повідомляє, показники
приховуються з `PICO FRESHNESS UNREPORTED`, без твердження про stale чи відмову
ARM. Числа поза діапазоном float (валідні JSON int) показуються як недоступні,
а не обривають рендер. В обох
випадках захисний fault labd лишається видимим, але без свіжого Pico консоль
ніколи не пише «ready for an explicit start». Так само й зі свіжим статусом у режимі
HARDWARE, коли labd повідомляє `live_identity_verified=false` (HELLO поточного сеансу
не пройшов звірку serial/CRC/`qualification_record`, і labd відмовляє в ARM): замість
доброякісної зупинки консоль показує причину `pico_identity_or_calibration_mismatch`
чи `pico_qualification_record_mismatch` з `last_error`, журналу подій labd або
зафіксованого fault (`srrx.hmi.binding_fault`); інший зафіксований fault лишається
першим рядком. Після нового provisioning (`srrx.provision`) або заміни Pico HELLO
нового сеансу проходить звірку (`live_identity_verified=true`), а labd і далі тримає
стару причину як перший fault, проте вже приймає RECOVER: консоль пише «Earlier Pico
binding failure (…); the current Pico HELLO verifies — RECOVER + ARM required»
(`srrx.hmi.latched_fault_text`), без «ARM refused» і без нового «re-provision»;
ARM + HOLD для цього fault консоль не надсилає, потрібна кнопка RECOVER + ARM.
Інша причина звірки в поточному сеансі показується окремим рядком під «Earlier Pico
binding failure (…)». Помилка консолі виводиться окремим рядком `Console:` під
захисним fault labd і не приховує його. Помилку зв'язку прибирає перший свіжий
статус, у якому labd disarmed; поки labd ще armed, «Disarm unconfirmed»
лишається. Якщо Qt worker зупинився не через закриття вікна, банер постійно
показує «Control worker stopped», кнопки ARM/RECOVER/HOLD і командні елементи
вкладок (route, HF relay, Stage, OFF, підтвердження Bench) вимикаються, нові
команди не ставляться в чергу, а рядок стану пояснює, що команду не надіслано.

Звичайне закриття вікна спершу зупиняє worker і посилає DISARM. Після kill,
втрати живлення чи зависання процесу покладатися потрібно на TTL/supervisor;
GUI не замінює апаратний аварійний захист. Служба ідентифікує оператора за
UID сокета; окремої автентифікації консоль не додає.

## Сторінки

| Сторінка | Робочі функції |
|---|---|
| Overview | Картки батареї/температур/controller+lease, захист, таблиця каналів ON/OFF/route, невідомі струми й зарезервований бюджет; raw status лише в необов'язкових Diagnostics |
| Receiver | Receive-only route/relay через labd; явний SIM labrx capture із 10 кадрів; центр 0…6 GHz, sample rate 48 kHz…56 MHz |
| Spectrum | Читання canonical JSON або останнього запису JSONL; повторне mask_frame; trace і waterfall до 96 рядків/512 колонок |
| Location | Великі координати, джерело, live/saved/manual статус, вік і невідома/повідомлена точність; ручний ввід, snapshot і опціональний gpsd. Завантажений snapshot закріплений: live tracker не перезаписує його до **Return to live position**. Група **Pointing — QO-100 (read-only)**: азимут від істинної півночі, кут місця, підказка повороту LNB, «видно звідси», джерело/вік і ворота фіксу; **Load pass plan…** показує збережений план проходів як snapshot |
| Teach / Classify | Читабельний результат клас/UNKNOWN, heuristic score, CPU/NPU причина, кількість training/held-out groups; явні анотації, train/infer і перевірене save/load — фоновою задачею з прогресом і Cancel; датасет сеансу до 2 MiB |
| Bench | Stage field/lab, явні підтвердження навантажень/Boni, named EN ON/OFF; галочки показують лише прийняті підтвердження; дозволи перевіряє labd |

SIM capture запускає лише `python -m srrx.labrx --simulate ...`, з обмеженням
20 с і одним процесом. Фізичний SDR GUI автоматично не відкриває; для нього
потрібний окремий прийнятий driver/acceptance record і явний labrx CLI.
Створення SIM-кадру не вмикає жодного EN.

Спектральні/навчальні JSON обмежені 2 MiB; дублікати ключів, non-finite,
надмірна вкладеність і неправильна схема відхиляються. У waterfall колонка з
хоча б одним masked bin залишається порожньою. Інтерполяції через no-data
немає; історія очищається при зміні центра, sample rate, FFT size або джерела.
Вибраний spectrum-файл відстежується за mtime; це snapshot/file stream, а не
доказ поточного апаратного приймання. Дані source не підміняються словом
HARDWARE. Якщо відстежуваний файл зник або перевищив 2 MiB, відстеження
зупиняється з повідомленням на сторінці Spectrum; відхилена версія не
перечитується щотику. Кроки heartbeat (SIM capture, файл, location) незалежні:
збій одного не зупиняє інші.

Tracker і gpsd client отримують час від одного годинника: на Linux
`CLOCK_BOOTTIME`, який рахує й suspend (без нього — monotonic). Після сну хоста
старий fix не виглядає свіжим, а UTC приймача не виглядає стрибком часу.
Файлова Location завжди позначена snapshot і не стає live GNSS. Ручні
координати мають source=manual, live_fix=false та невідому uncertainty; ручний
ввід передається tracker і відновлює live-оновлення. Лише tracker/gpsd визначає
свіжість справжнього fix. Збій location provider показує «Location
unavailable», а не останній live fix. Provider опитується кожного heartbeat і
тоді, коли snapshot закріплений: socket gpsd не накопичує backlog, і після
**Return to live position** старі епохи не показуються як свіжий fix. Під час
закріплення збій provider змінює лише примітку під координатами. Примітка
відповідає показаному джерелу: після ручного вводу свіжий GNSS fix від tracker
змінює її на «Live tracker position»; повідомлення про відхилений файл лишається,
доки показаний стан не зміниться.

Група Pointing на сторінці Location лише показує числа й нічого не вмикає:
вона не керує LNB, ротатором, EN чи живленням антени. Кути рахує `srrx.geo_look`
(модель WGS84) для номінальної позиції 25.9°E з тієї самої точки, що й текст
Location; координат у групі немає. Азимут — від істинної, не магнітної півночі.
Знак підказки LNB: «+» — поворот проти годинникової стрілки, якщо дивитися ззаду
на LNB у бік супутника, за шкалою шийки ±45°; це стартова точка, остаточне
положення дає пошук піку C/N0 маяка кроками 5° (П-09). Біля екватора (|lat| < 1°)
перекіс не визначено й показано окремим рядком. «Видно звідси» стає «так» лише
зі стаціонарним allowlist-елементом QO100; у цій ревізії консоль OMM не завантажує,
тому рядок каже «not confirmed … nominal slot 25.9E; TLE not verified», навіть
коли геометрія дає ≥5°. Кваліфікований fix — лише свіжий live gpsd/nmea, 3D, ≥6
супутників і завершене вікно першого запуску (3D, ≥8 супутників, у межах 50 м
протягом 5 хв; рахується в цьому процесі консолі за тим самим годинником
`CLOCK_BOOTTIME`, не зберігається; будь-який невдалий зразок або пауза понад 5 с
між зразками починає вікно заново). Невідома кількість супутників (gpsd TPV її не
містить) fix не кваліфікує. Ручні координати й snapshot файлу дають кути з
позначкою «not a GNSS fix» або «fix not fresh» і ніколи не стають кваліфікованим
fix. Без позиції, при збої provider чи збої монотонного годинника tracker група
пише «pointing unavailable». **Load pass plan…** читає лише JSON до 2 MiB, що
пройшов `srrx.passes.validate_plan` (спостерігач округлений до 0.1°), і позначає
його як snapshot із версіями Skyfield/sgp4 та станом UTC («UTC not verified —
times are provisional»); консоль сама проходи не рахує й Skyfield не імпортує.
Під кнопкою — рядок стану labd `plan_passes` лише для читання (`status["passes"]`:
стан, код останньої помилки, стан UTC, до чотирьох найближчих проходів, без
координат); запит плану робить `labctl plan_passes` ([LOCATION](LOCATION.md)),
не консоль.

IMU й фізичні HMI snapshots
додатково старіють за часом після GUI poll; старий кватерніон не лишається
чинним. Показник accuracy IMU не перетворюється на true-north heading.

Навчальні дії використовують API `srrx.learning` і повторні маски. Потрібне
явне підтвердження анотації; воно прив'язує кадр, показаний у момент позначки.
Зміна bins чи мітки або новий кадр іншої геометрії (centre, rate, FFT size,
source) знімає підтвердження; потокові кадри тієї ж геометрії не скидають
вибраний діапазон. Нова independent session створюється окремою
дією. Перевантаження того самого кадру не створює групу автоматично.
Використовуються лише coarse labels, CPU baseline і heuristic score;
польова точність та NPU acceleration не оголошуються виміряними.

## Декларативна модель меню (selftest RX-11)

`srrx.menu_model` — чисті дані без Qt, I/O і викликів labd. `PAGES` задає шість
сторінок у порядку вкладок; `LEAVES` — кожен лист консолі: напис, як його показує
консоль, бекенд, прапорці `needs_lime`/`needs_t7` з `fallback_text`, ознаку
`critical` і входи `controls` (touch; клавіші Pico `HOME BACK REC MARK FN LOCK
ENC1_PRESS ENC2_PRESS`, енкодери `ENC1`/`ENC2`). Види бекенда: `labd_op` — операція
`Engine.request`; `page_only` — модуль srrx, що виконує дію в консолі (для SIM
capture — `srrx.labrx --simulate` окремим процесом); `engine_unit` — unit systemd і
його програма; `decoder_preset` — пресет `decoder_policy.availability()`. Листи
консолі мають лише `labd_op` і `page_only`; два інші види — для майбутніх хабів Lab
Shell (наприклад, WEFAX → режим fax OpenWebRX+, STACK.md:884). Сама консоль
залежить від двох unit: `srrx.service` (labd, `-m srrx.daemon`) і користувацького
`srrx-menu.service` (`-m srrx.hmi`).

`create_window` будує вкладки в порядку `PAGES` і відмовляє в старті
(`RuntimeError`), якщо побудована вкладка має інший напис; інших змін поведінки
немає. `software/tests/test_menu_model.py` в offscreen Qt перевіряє, що кожен
touch-лист є кнопкою чи галочкою на своїй сторінці (або в рамці вікна), а кожна
кнопка чи галочка вікна — листом моделі; пари ON/OFF на Bench — рядки `EN_*`.
Той самий тест натискає віджет кожного touch-листа з записувальним labd. Лист
`labd_op` має надіслати саме свою операцію через `action()`, чергу worker і
`ConsoleController`: ARM/RECOVER одразу поновлюють оренду, Shutdown спершу дає
disarm, «Close + DISARM» — disarm. Лист `page_only` не надсилає нічого (діалоги
скасовано, SIM capture і навчальні задачі підмінено). Там само: `KEYS` дорівнює
`KEY_NAMES` прошивки Pico, `GESTURES` — `HMINavigation.NAMES`, `OUTPUTS` — `EN_OUTPUTS`,
а набір операцій листів дорівнює тому, який може надіслати `ConsoleController`
(ключі таблиці `required` у `command()` і літерали `{"op": …}` класу, розбір `hmi.py`).

Збірка без Lime і без T7: маршрут LIME і EN_LIME3V3 оголошують бекенд без Lime
(LIME лишається PARK, EN_LIME3V3 — OFF; OFF і PARK labd приймає без оренди), EN_T7 —
бекенд без T7 (OFF; сховище — UFS і microSD V30, STACK.md:977). Це декларація для
перевірки: консоль цей текст не показує й нічого не ховає. Перевірка можливостей,
що ховає пункти лише для Lime (STACK.md:884), належить Lab Shell, а не цій консолі: це
модель `srrx.lab_shell_menu` (рішення W2 SW-MENU, [build/15](../build/15-rishennia-komplektu.md)) —
дванадцять хабів STACK.md:884 і листи Home, кожен з бекендом (ті самі види, що тут; `engine_unit`
— з областю system/user і програмою), потрібними пакетами (`PACKAGES`: компонент `sources.lock.json`
і виконувані файли на шляху пошуку systemd), системними unit (шаблони оренд — лише системні,
STACK.md:76, тож RX-11 шукає їх і їхні drop-in лише в системних шляхах unit, як RX-12), модулями
srrx, пресетами, записом алоу-листа політики (плагін SDRangel, режим OpenWebRX+, конвеєр SatDump),
`needs_lime`/`needs_t7` з `fallback_text` і `hidden_reason`; бекенд `planned.<функція>` — ще не
зібраний (`PLANNED` з джерелом). `visible_leaves(capabilities)` показує лист, лише коли все це є на
корені, запис дозволено й не заборонено, пресет прийнято, а Lime/T7 є; інакше лист приховано з
причинами (`hide_reasons`), напр. WEFAX — `package_deferred:openwebrx` (OpenWebRX+ відкладено: у
`sources.lock.json` немає csdr, pycsdr і owrx_connector), SafetyNET — `preset:egc-safetynet=DISABLED_…`,
DSC — `denied:sdrangel:demoddsc`, HRPT — `no_lime`. Live map показує лише власне місце
(`srrx.location`); шари літаків, суден, зондів, трас і APRS — окремий запланований лист.
RX-11 оцінює її на тому самому корені після консолі: Lime — з `/etc/srrx/devices.json` і бібліотеки
Lime, T7 (знімний, без прив'язки офлайн) — з ним і без нього. FAIL у
`software/srrx/lab_shell_menu.py` з id листа як `item`: `lab_shell_menu_invalid` (без листа),
`lab_shell_backend_unknown`, `lab_shell_requirement_unknown` (ім'я не зібране й не в `PLANNED` або
запис алоу-листа, якого політика ні дозволяє, ні забороняє), `no_lime_backend_undeclared`/
`no_t7_backend_undeclared`; BLOCKED `critical_leaf_touch_only`. Перевірка досяжності видимого листа
пише знахідку за шляхом unit чи модуля: `lab_shell_unit_program_mismatch` (FAIL: unit не запускає
виконуваний файл пакета листа), `unit_interpreter_missing` (BLOCKED) і для листа `engine_unit`
`backend_program_missing` (FAIL) — з id листа (`backend_unit_missing` такого листа — у
`software/srrx/lab_shell_menu.py`), а `target_module_differs` (BLOCKED, спільне з консоллю) — за
шляхом модуля цілі без id листа. Кожен прихований лист — примітка
`lab_shell_hidden:<лист>:<причини>`; прихований критичний лист — ще й примітка
`lab_shell_critical_hidden:<лист>:<причини>`. PASS RX-11 означає лише, що критичні листи оголошують
клавіші чи енкодери: BACK, ENC1/ENC2 і LOCK приховано (`planned:labinput`, `planned:touch_lock`),
доки немає labinput і блокування дотику, тож шлях у рукавицях для них лишається OPEN (МЕН-03, Д-06).
Сама QML-оболонка не зібрана (примітка `lab_shell_qml_not_built`).

Критичні листи — дії, потрібні в рукавицях, коли ємнісна панель не працює
(STACK.md:110): навігація HOME/BACK/FN/ENC1/ENC2/ENC1_PRESS/ENC2_PRESS, LOCK,
Overview (статус і захисний fault за HOME) і **DISARM / STOP**. Фізичний шлях DISARM
(рішення W2 FW-STOP, [build/15](../build/15-rishennia-komplektu.md)): утримання
**LOCK ≥ 1,0 с** — локальний STOP на Pico. Вхідне ядро (`firmware/pico/hmi.py`) API
живлення не має: воно лише повідомляє тривалість утримання за свіжими читаннями
клавіш. `firmware/pico/main.py` (`LOCK_STOP_HOLD_MS`) подає вхід `operator_stop`, і
Supervisor у WARMING/CONFIGURING/ACTIVE дає trip `OPERATOR_STOP`: MCP RESET (усі EN
вимкнено), повне охолодження, новий сеанс. Цей вхід Supervisor перевіряє останнім:
захисна причина в тому самому знімку (втрата Q6A, недійсний датчик, гаряча панель
чи корпус, зупинка вентилятора) сама називає trip, тож CASE_HOT і FAN_STALLED і тоді гасять DISP12 (див. вище). SAFE,
TRIPPED, SHUTTING_DOWN і OFF не змінюються; поки LOCK утримано, ARM відхиляється.
Застаріле читання клавіш — не STOP.
Шлях діє лише в бік вимкнення й без labd, Qt чи Q6A; labd іде за trip Pico
(`pico_OPERATOR_STOP`), консоль показує причину, а повторний старт — лише явний ARM
хоста в новому сеансі. Час 1,0 с відрізняється від утримання кнопки корпусу 1,5 с
(shutdown). `frame.disarm` оголошує клавішу LOCK, тож RX-11 більше не дає
`critical_leaf_touch_only`; тест стежить, щоб `menu_model.HOLD_STOP` дорівнював
сталій прошивки. Якщо натискання LOCK зафіксовано, утримання рахується як одне
натискання: touch-блокування консолі перемикається один раз (LOCK, затиснена до
старту чи відновлення шини, перемикання не дає). Затримку
«LOCK → EN off» у рукавицях вимірюють лише на пристрої (МЕН-01). Без touch лишаються
й `labctl disarm` та `labctl shutdown` з локального терміналу. Оренду консоль
поновлює, поки GUI відповідає, тож зупинка GUI знімає HOLD через 1,5 с, а TTL 3 с і
Pico обмежують решту. Shutdown критичним листом не вважається: RF він не вимикає
швидше за DISARM.

## Фізичні клавіші й енкодери

Використовується лише перевірений `status.hmi` від labd:
`ok,fresh,age_ms,keys,presses[8],encoders[2],lux,lux_valid,lux_age_ms,sequence,
error,generation`. `status.session` — nonce Pico. Натискання — uint16 rising
counters, енкодери — signed int32 totals; generation — uint16.

Перший snapshot, новий session/generation, stale/invalid або reconnect
встановлює baseline. Однаковий sequence не повторюється; запізнілий менший
sequence ігнорується. Прирости обчислюються modulo 16/32 біти; >4 натискань
однієї кнопки або >16 detents за snapshot відкидаються з новим baseline.
Qt споживає поточний стан моделі з урахованим віком, а не стару queued signal.

| Вхід | Дія GUI |
|---|---|
| HOME / BACK / FN | Overview / попередня сторінка / наступна сторінка |
| ENC1 | Вибір сторінки |
| ENC2 | Вертикальний scroll поточної сторінки |
| ENC1_PRESS / ENC2_PRESS | Переміщення focus вперед/назад |
| MARK | Локальний лічильник spectral marks; файл автоматично не записується |
| REC | Повідомлення про отриману кнопку; capture/ARM/EN автоматично не запускаються |
| LOCK | Натискання блокує touch-команди, вкладки й кнопки ARM/RECOVER/HOLD; DISARM/shutdown лишаються доступними. Утримання ≥ 1,0 с — фізичний STOP на Pico (усі EN вимкнено, розділ вище); якщо натискання зафіксовано, touch-блокування при цьому перемикається один раз |

Натискання LOCK не змінює поточні виходи; вже обрана оренда підтримується, поки UI
відповідає. Нові queued energizing-команди при LOCK відкидаються; заблокована
команда не відкриває діалог підтвердження, а рядок стану пояснює відмову. Повторний
LOCK або підтверджене **Unlock touch** розблоковує UI без ARM. Валідні lux
показуються до 2 с; жодного GPIO PWM/керування яскравістю немає. Реальна
проводка дисплея/brightness лишається апаратними воротами E3-02 (керування
яскравістю) та E5-01 (DC/USB-touch проводка Wisecoco).

## Перевірки й межі

```sh
PYTHONPATH=software:. python3 -m unittest discover -s software/tests -p test_hmi.py -v
QT_QPA_PLATFORM=offscreen PYTHONPATH=/tmp/srrx-qt:software:. \
  python3 -m unittest discover -s software/tests -p test_hmi.py -v
QT_QPA_PLATFORM=offscreen PYTHONPATH=/tmp/srrx-qt:software:. \
  python3 -m unittest discover -s software/tests -p test_menu_model.py -v
```

Перевірені faults/lease/clock, strict requests, bench, stale IMU/HMI, counter
wrap/generation, справжній stdio daemon та labrx SIM subprocess, усі 6 Qt
сторінок і закриття реального Qt worker після SIM ARM. Додатково: перерваний
ARM через справжній Engine (first-fault latch), HOLD під час handshake, disarm
за зупинки GUI heartbeat при живому worker, CONTROL/MODE UNKNOWN, stale і
неповідомлена свіжість Pico (також проти справжнього Engine), окремий рядок
помилки консолі, закріплений location snapshot з безперервним опитуванням
provider, примітка Location за показаним джерелом, незалежні кроки
heartbeat, прив'язка анотації до підтвердженого кадру, read-back підтверджень
Bench, LOCK без діалогів і стійке попередження про зупинений worker із
вимкненими командами вкладок, спільний suspend-aware годинник location, числа
поза діапазоном float і ворота генератора знімків. Група Pointing: текст за
воротами fix (mode 2, 5 супутників, невідома кількість, вікно першого запуску),
snapshot/manual без кваліфікації, екватор і горизонт, збій provider, а також
строге завантаження плану проходів і відмова для неокругленого спостерігача. Тести справжнього stdio
daemon, labrx subprocess і справжнього Engine виконуються лише на Linux/POSIX.
Фонові навчальні задачі (`LearningRunnerTests` без Qt і Qt-тести): одна задача
без черги, результат повертається рівно один раз, Cancel на контрольній точці
без зміни вхідних даних, close без очікування, автоматичне скасування після
межі часу, будь-який виняток як результат-помилка; довга CPU-задача (3 с) при
справжньому worker і монотонному годиннику не знімає HOLD, не надсилає DISARM,
lease поновлюється, а найбільший проміжок heartbeat GUI менший за 1 с (на
повільному емульованому хості — не більше ніж на 0,5 с понад природний);
засувка, додана під час задачі, відкидає результат; стоп, знайдений фоновим
навчанням, засувається й перериває SIM capture лише в GUI thread і дає один
рядок журналу; load/save через задачу, відмова збереження понад межу консолі,
межа 2 MiB датасету сеансу; задача ніколи не викликає labd.

Offscreen PNG та JSON звіту у [verification/hmi-views](../verification/hmi-views/)
перегенеровано в CI 07.11.2026 (job `linux-lab`, run 42355259865) для `hmi.py`
цієї ревізії з фоновими навчальними задачами (на сторінці Teach/Classify видно
вимкнену кнопку «Cancel learning job»). Після будь-якої зміни `hmi.py` вони перестають бути записом
перевірки поточного коду, доки їх не перегенеровано; чинність визначає
`hmi_sha256` у звіті (див. нижче). Перегенерація на Linux:

```sh
python3 tools/render_hmi_views.py --output verification/hmi-views
```

Інструмент спершу запускає `software/tests/test_hmi.py` в окремому offscreen
процесі й нічого не записує, якщо хоч один тест не пройшов або не виконано
справжній offscreen render і закриття реального Qt worker. Потім він запускає
справжнє вікно проти дочірнього `srrx.daemon --simulate --stdio`, бере
seeded кадр `srrx.labrx --simulate` і модель `learning.demo`, робить один явний
SIM ARM+HOLD, знімає шість сторінок у стані READY/CONTROL ARMED, закриває
консоль (DISARM) і лише тоді кодує PNG. `report.json` записується останнім.
Запис чинний лише тоді, коли `hmi_sha256` у ньому дорівнює SHA256 поточного
`software/srrx/hmi.py`.

Натискання в рукавицях, сонячне освітлення, DPI/орієнтація дисплея, latency
на Q6A, фізичні клавіші/енкодери/VEML7700 ще потребують апаратного приймання.
Розмір кнопок/контраст і scroll закладені в UI, але польових вимірів немає.

Первинні Qt джерела: [Threads and QObjects](https://doc.qt.io/qtforpython-6/overviews/qtdoc-threads-qobject.html),
[QThread](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html),
[signals/slots](https://doc.qt.io/qtforpython-6/tutorials/basictutorial/signals_and_slots.html).
Widgets змінюються тільки у GUI thread; worker передає стан сигналами.

Станом на 24.10.2026 анотація, навчання CPU-моделі, класифікація та load/save датасету й моделі виконуються у фоновій задачі (див. вище), а не в GUI thread; датасет сеансу обмежено 2 MiB, тож задача триває секунди, а не хвилини. Найдовший неподільний крок (один збережений кадр або перевірка печатки всього датасету) визначає затримку Cancel. Відкрито: затримку на Q6A не виміряно; у GUI thread лишаються три попоінтові проходи на кожен показаний кадр до 2 MiB (`accept_frame`, `Plot.add` через `spectrum_columns`, перечитування відстежуваного файлу). Якщо GUI thread усе ж зупиниться понад 1,5 с, worker і далі знімає HOLD (відмова безпечна).

## Сеанс на дисплеї: greetd, lab-session, labwc

Станом на 07.11.2026 (W2 SYS-SESSION) файли сеансу генерує `deployment/system/system_files.py`
(`session_files()`), а `deploy.py stage` кладе їх у rootfs для кожного режиму GNSS. Пакети greetd,
labwc, kanshi і cage та greetd як display-manager додає образ (лінія IMG). Поки Lab Shell не має
коду, клієнтом сеансу є ця консоль (`srrx-menu.service`, `-m srrx.hmi`). Поведінку greetd 0.9.0,
labwc 0.7.1, kanshi 1.5.1 і cage 0.1.5 прочитано з вихідних пакетів noble (SHA-256 архівів
збігаються з .dsc), а systemd v255 — з його upstream-тега; усі джерела перелічено наприкінці
розділу, файли й функції — у коментарях `system_files.py` і скриптів `deployment/system/session`.

| Файл у rootfs | Призначення |
|---|---|
| `usr/lib/sysusers.d/srrx.conf` | Обліковий запис `srrx-ui`: `u`, домівка `/var/lib/srrx-ui`, оболонка `/usr/sbin/nologin`, створюється вимкненим (без пароля). Єдиний рядок `m srrx-ui labd`: група `labd` відкриває `/run/srrx` (0750) і `control.sock` (0660). `srrx-pico` і `srrx-gnss` лишаються без членів |
| `usr/lib/tmpfiles.d/srrx-session.conf` | Домівка `/var/lib/srrx-ui` 0700 (sysusers записує лише шлях) і каталог лічильника `/run/srrx-session` 0700 |
| `etc/greetd/config.toml` | `vt = 1`, `source_profile = false`, лише `default_session`: `/usr/lib/srrx/lab-session` від `srrx-ui`. Замінює conffile пакета (agreety на VT 7); `/etc/greetd/greetd.conf` greetd 0.9.0 читав би раніше, тому його не має бути |
| `etc/systemd/system/greetd.service.d/60-srrx-session.conf` | `StartLimitBurst=0` (unit пакета дозволяє 5 перезапусків за 30 с) і `Conflicts=`/`After=getty@tty1.service` (патч Debian переніс конфлікт на tty7) |
| `usr/lib/srrx/lab-session` (0755) | Обгортка сеансу, яка ніколи не завершується через збій (нижче) |
| `usr/lib/srrx/labwc/rc.xml`, `environment`, `autostart` | Конфігурація, яку lab-session передає labwc через `-C`: каталоги XDG, зокрема пакетний `/etc/xdg/labwc` зі swaybg, waybar і swayidle, не читаються |
| `usr/lib/srrx/kanshi/field60`, `field52` | Профілі з польового EDID: `output HDMI-A-1 mode 1920x1080@59.986Hz` і `…@51.677Hz` |

greetd запускає `/bin/sh -c "exec /usr/lib/srrx/lab-session"` від `srrx-ui` (клас greeter, PAM
`greetd-greeter`, без автентифікації) незалежно від оболонки облікового запису і сам завершується,
щойно default_session виходить, не створивши сеансу. Тому lab-session наглядає за графічним етапом
і рахує кожне його завершення як збій:

1. **normal** — `labwc -C /usr/lib/srrx/labwc`. Автозапуск запускає `kanshi -c /usr/lib/srrx/kanshi/field60`
   (або `field52`, якщо адміністратор під час введення в дію записав це слово в
   `/etc/srrx/display-profile`; kanshi 1.5.1-1 у noble зібрано без IPC, тож `kanshictl switch`
   недоступний), імпортує `WAYLAND_DISPLAY` у менеджер користувача і, якщо `srrx-menu.service`
   увімкнено, виконує `systemctl --user start --wait srrx-menu.service`. Коли консоль зупиняється,
   автозапуск завершує свій labwc (`labwc --exit`, лише якщо `LABWC_PID` ще належить labwc).
   Якщо менеджер користувача не відповідає (`is-enabled` не друкує жодного стану), автозапуск теж
   завершує labwc: це збій сеансу, а не «консоль не ввімкнено».
2. **safe** — після 3 збоїв за 600 с: `cage -d -- /usr/lib/srrx/lab-session client`, тобто лише
   консоль (той самий user unit з тією самою пісочницею) без labwc, kanshi та інших вікон; режим
   екрана — бажаний режим EDID (DTD1, 59.986 Hz). Якщо консолі немає (unit не ввімкнено або його
   старт пропущено без venv), клієнт виходить зі статусом 69, cage 0.1.5 повертає його, і
   lab-session одразу, без лічильника, переходить у text: чорний cage без клієнта нічого б не показав.
3. **text** — ще 3 збої за 600 с: текст стану на VT 1 (`python3 -m srrx.cli … status`, тобто
   `labctl status`), оновлення кожні 30 с, до перезавантаження. labd працює далі. Перший рядок
   називає причину (`/run/srrx-session/reason`).

Режим і моменти збоїв (секунди `/proc/uptime`, тож крок годинника від GNSS чи RTC їх не зсуває)
лежать у `/run/srrx-session`: перезапуск greetd їх зберігає, перезавантаження очищає. Без цього
каталогу лічильник працює в `$XDG_RUNTIME_DIR/srrx-session`, але лише до перезапуску greetd.

Зупинка й перезапуск greetd. greetd 0.9.0 надсилає SIGTERM лише обгортці (sub_task,
`session/interface.rs`), а вихід worker-а знімає VT, і SIGHUP від цього labwc 0.7.1 сприймає як
«перечитати конфігурацію» (`src/server.c`). Тому кожен етап (labwc, cage, пауза текстового режиму)
працює у фоні, а SIGTERM, SIGHUP чи SIGINT обгортка передає етапу як SIGTERM, чекає до 5 с, далі
SIGKILL, і лише тоді виходить (143, 129 чи 130); зупинка не рахується як збій. Перед кожним
графічним етапом lab-session зупиняє `srrx-menu.service`, щоб консоль, яка лишилася від попереднього
compositor-а (Ubuntu не вбиває процеси закритого сеансу, KillUserProcesses=no), не тримала
`start --wait` нового автозапуску на старому дисплеї.

Журнал. greetd з'єднує stdin/stdout/stderr сеансу з VT (`session/worker.rs`), тож без цього повідомлення
обгортки й compositor-а не потрапляли б у journald. Поки існує потоковий сокет journald
(`/run/systemd/journal/stdout`), lab-session пише свої рядки ще й через `systemd-cat -t lab-session`, а
labwc і cage запускає через `systemd-cat -t labwc` / `-t cage` (systemd-cat v255 виконує команду
через execvp, тож PID етапу не змінюється; вивід автозапуску й kanshi іде з labwc). Журнал сеансу:
`journalctl -t lab-session -t labwc -t cage`. Без сокета все лишається на VT.

`srrx-menu.service` має `ConditionPathExists=/opt/srrx/venv/bin/python3` і `Restart=no` (перезапуск
робить lab-session). Без venv `systemctl --user start --wait` повертає 0 одразу (systemd v255: умова
не виконана — job `done`, unit `inactive`), тож автозапуск після нього читає
`systemctl --user show -P ConditionResult`: `no` означає визначений стан «venv немає» — labwc працює
далі без консолі, збою немає. Пресет користувача лишається `disable`: консоль стартує лише після
того, як адміністратор увімкне unit після збирання й аудиту venv; до того labwc теж працює без
консолі. Увімкнути unit без venv (наприклад, для сценарію QEMU) отже безпечно: сеанс лишається в
normal з активним labwc.

rc.xml має один `<touch mapToOutput="HDMI-A-1"/>` без `deviceName` (типовий запис для всіх сенсорних
пристроїв) і по одній прив'язці клавіатури й миші з дією `None`: labwc 0.7.1 тоді не завантажує
типових прив'язок (термінал, запускач, кореневе меню з Exit) і відкидає прив'язки без дій, тож
кіоск не має жодної. Правило вікна `lab.shell` (без декорацій, розгорнуте) чекає на Lab Shell.

Перевірки хоста (CI-модель, не апаратний результат): `deployment/tests/test_system_files.py`,
класи `SessionFilesTests` (вміст, розбір config.toml за правилами greetd 0.9.0, один рядок `m`,
staging і режими в архіві) і `LabSessionExecutionTests` (справжні lab-session і автозапуск під
POSIX sh з підробленими labwc, cage, systemctl, systemd-cat, kanshi і sleep: 3 збої → safe, ще 3 →
текст, вікно 600 с, режим після перезапуску greetd, клієнт safe-режиму, safe без консолі → одразу
текст, SIGTERM/SIGHUP обгортці доходять до labwc, який ігнорує SIGHUP, а labwc, що ігнорує й
SIGTERM, отримує SIGKILL, пропущений за умовою старт консолі лишає labwc, менеджер користувача без
відповіді — збій, рядки журналу через systemd-cat, вибір профілю kanshi).

Відкрито:
- Стенд W1-2 (STACK.md:1442, :1486): режим 59.986 Hz і дотик на HDMI Q6A, відновлення greetd
  (Lab Shell → консоль), повернення VT у текстовий режим після виходу labwc чи cage, доступ сеансу
  класу greeter до DRM і вводу через logind і запуск user@ для `srrx-ui` (`loginctl`); групи
  `video` та `input` не додано.
- `LABWC_FALLBACK_OUTPUT=NOOP-fallback` записано, але labwc 0.7.1 його ігнорує (резервний вихід
  з'явився в 0.7.2): поведінку при від'єднанні HDMI з 0.7.1 перевіряє стенд; 0.7.4+lab1 — група E.
- `WLR_DRM_DEVICES` (by-path контролера дисплея Q6A) — TBD до читання на стенді.
- Порожній робочий стіл labwc — суцільний чорний фон wlroots 0.17.1 (0x00), який правило палітри
  STACK.md:884 забороняє для великих заливок; консоль на весь екран його закриває, клієнта фону
  в образі немає.
- `PrivateTmp=yes` у user unit потребує просторів імен; чи стартує консоль у noble, покаже
  сценарій сеансу QEMU (лінія IMG).
- LOCK (фрагмент rc.xml із `sendEventsMode=no`) потребує записуваного каталогу конфігурації — разом
  із Lab Shell.
- `/var/lib/srrx-ui` записуваний для `srrx-ui`: перевизначення user unit у цій домівці має блокувати
  RX-11 (у selftest її ще немає серед домівок).
- Перемикання VT у labwc лишається: labwc 0.7.1 обробляє XF86Switch_VT_1…12 (Ctrl+Alt+F1…F12) раніше
  за прив'язки (`src/input/keyboard.c`, `handle_change_vt_key`), тож з USB-клавіатурою можна дійти до
  getty, які logind запускає на вимогу (autovt). cage без `-s` перемикання VT не дозволяє, тож це
  стосується лише режиму normal. Чи ставити logind `NAutoVTs=0`/`ReserveVT=0`, вирішує власник або
  пакет SYS (logind тут не змінено).
- Ескалація до SIGKILL через 5 с і запис у журнал через systemd-cat перевірено лише на підроблених
  процесах (CI-модель); на Q6A — стенд W1-2 (STACK.md:1486 (a), `journalctl -t lab-session`).

Джерела (прочитано 07.11.2026):
- greetd: http://archive.ubuntu.com/ubuntu/pool/universe/g/greetd/greetd_0.9.0.orig.tar.gz і
  greetd_0.9.0-4ubuntu1.debian.tar.xz (`greetd/src/{context.rs,server.rs,config/mod.rs}`,
  `session/{worker.rs,interface.rs}`, `debian/patches/systemd_service_tweaks.patch`).
- labwc: http://archive.ubuntu.com/ubuntu/pool/universe/l/labwc/labwc_0.7.1.orig.tar.gz і
  labwc_0.7.1-1build1.debian.tar.xz (`src/server.c`, `src/main.c`, `src/config/{rcxml.c,session.c,touch.c}`,
  `src/input/keyboard.c`); https://raw.githubusercontent.com/labwc/labwc/0.7.4/NEWS.md.
- kanshi: http://archive.ubuntu.com/ubuntu/pool/universe/k/kanshi/kanshi_1.5.1.orig.tar.gz і
  kanshi_1.5.1-1.debian.tar.xz; cage:
  http://archive.ubuntu.com/ubuntu/pool/universe/c/cage/cage_0.1.5+20240127.orig.tar.gz (`cage.c`).
- wlroots 0.17.1: https://gitlab.freedesktop.org/wlroots/wlroots/-/raw/0.17.1/types/scene/wlr_scene.c.
- systemd v255: https://raw.githubusercontent.com/systemd/systemd/v255/ — `src/basic/ratelimit.h`,
  `src/core/load-fragment-gperf.gperf.in`, `src/core/job.c`, `src/login/logind-session.c`,
  `src/journal/cat.c`, `src/libsystemd/sd-journal/journal-send.c`, `src/systemctl/{systemctl.c,
  systemctl-start-unit.c,systemctl-is-enabled.c}`, `src/shared/bus-wait-for-units.c`,
  `man/{sysusers.d.xml,systemd.unit.xml,systemd.exec.xml,logind.conf.xml}`; systemd noble
  http://archive.ubuntu.com/ubuntu/pool/main/s/systemd/systemd_255.4-1ubuntu8.debian.tar.xz
  (`debian/rules`: `-Ddefault-kill-user-processes=false`).
- Qt: https://raw.githubusercontent.com/qt/qtbase/v6.12.0/src/gui/kernel/qguiapplication.cpp.
- Версії noble: Launchpad API `https://api.launchpad.net/1.0/ubuntu/+archive/primary?ws.op=getPublishedSources`
  (greetd 0.9.0-4ubuntu1, labwc 0.7.1-1build1, kanshi 1.5.1-1, cage 0.1.5+20240127-2build1,
  wlroots 0.17.1-2.1build1, wlopm 0.1.0-1).
