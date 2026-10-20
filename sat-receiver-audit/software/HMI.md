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

Явна демонстрація без апаратних пристроїв:

```sh
PYTHONPATH=software:. python3 -m srrx.hmi --demo
```

`--demo` запускає окремий справжній `srrx.daemon --simulate --stdio` через
обмежені локальні pipes. Кожен статус містить SIMULATION. Дочірній процес
одержує явний шлях до пакета; наявні елементи PYTHONPATH, зокрема ізольований
Qt, зберігаються. EOF/закриття зупиняє Engine; після обмеженого очікування
завислий дочірній процес припиняється. GUI ніколи не запускає фізичний labd.

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
- **DISARM / STOP** припиняє HOLD і просить вимкнути виходи. OFF/PARK доступні
  без активної оренди; backend перевіряє можливість виконання.
- Зміна **field/lab** можлива лише disarmed і застосовується наступним явним ARM.
- **Shutdown** спершу робить DISARM, потім просить штатний ARM_OFF/shutdown.
  OFF_NOW/root poweroff bridge не викликається консольним запитом напряму.

IPC працює в окремому Qt worker. Полінг — 250 мс, socket timeout — 400 мс;
дії мають чергу до 16 записів. Відмова оренди, новий fault, невдалий ARM,
помилка служби чи розрив полінгу >1,5 с припиняють поновлення й викликають
спробу DISARM. Heartbeat GUI також має межу 1,5 с. Після reconnect/fault
автоматичного ARM немає. Якщо DISARM не підтверджений, консоль показує це;
останній TTL і незалежний Pico лишаються обмежувачами дозволу.

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
| Location | Великі координати, джерело, live/saved/manual статус, вік і невідома/повідомлена точність; ручний ввід, snapshot і опціональний gpsd |
| Teach / Classify | Читабельний результат клас/UNKNOWN, heuristic score, CPU/NPU причина, кількість training/held-out groups; явні анотації, train/infer і перевірене save/load |
| Bench | Stage field/lab, явні підтвердження навантажень/Boni, named EN ON/OFF; дозволи перевіряє labd |

SIM capture запускає лише `python -m srrx.labrx --simulate ...`, з обмеженням
20 с і одним процесом. Фізичний SDR GUI автоматично не відкриває; для нього
потрібний окремий прийнятий driver/acceptance record і явний labrx CLI.
Створення SIM-кадру не вмикає жодного EN.

Спектральні/навчальні JSON обмежені 2 MiB; дублікати ключів, non-finite і
неправильна схема відхиляються. У waterfall колонка з хоча б одним masked
bin залишається порожньою. Інтерполяції через no-data немає; історія
очищається при зміні центра, sample rate, FFT size або джерела. Вибраний
spectrum-файл відстежується за mtime; це snapshot/file stream, а не доказ
поточного апаратного приймання. Дані source не підміняються словом HARDWARE.

Файлова Location завжди позначена snapshot і не стає live GNSS. Ручні
координати мають source=manual, live_fix=false та невідому uncertainty.
Лише tracker/gpsd визначає свіжість справжнього fix. IMU й фізичні HMI snapshots
додатково старіють за часом після GUI poll; старий кватерніон не лишається
чинним. Показник accuracy IMU не перетворюється на true-north heading.

Навчальні дії використовують API `srrx.learning` і повторні маски. Потрібне
явне підтвердження анотації; нова independent session створюється окремою
дією. Перевантаження того самого кадру не створює групу автоматично.
Використовуються лише coarse labels, CPU baseline і heuristic score;
польова точність та NPU acceleration не оголошуються виміряними.

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
| LOCK | Блокує touch-команди та вкладки; DISARM/shutdown лишаються доступними |

LOCK не змінює поточні виходи; вже обрана оренда підтримується, поки UI
відповідає. Нові queued energizing-команди при LOCK відкидаються. Повторний
LOCK або підтверджене **Unlock touch** розблоковує UI без ARM. Валідні lux
показуються до 2 с; жодного GPIO PWM/керування яскравістю немає. Реальна
проводка дисплея/brightness лишається апаратним gate E3-01.

## Перевірки й межі

```sh
PYTHONPATH=software:. python3 -m unittest discover -s software/tests -p test_hmi.py -v
QT_QPA_PLATFORM=offscreen PYTHONPATH=/tmp/srrx-qt:software:. \
  python3 -m unittest discover -s software/tests -p test_hmi.py -v
```

Перевірені faults/lease/clock, strict requests, bench, stale IMU/HMI, counter
wrap/generation, справжній stdio daemon та labrx SIM subprocess, усі 6 Qt
сторінок і закриття реального Qt worker після SIM ARM. Offscreen PNG та JSON
звіту збережені у [verification/hmi-views](../verification/hmi-views/).
Натискання в рукавицях, сонячне освітлення, DPI/орієнтація дисплея, latency
на Q6A, фізичні клавіші/енкодери/VEML7700 ще потребують апаратного приймання.
Розмір кнопок/контраст і scroll закладені в UI, але польових вимірів немає.

Первинні Qt джерела: [Threads and QObjects](https://doc.qt.io/qtforpython-6/overviews/qtdoc-threads-qobject.html),
[QThread](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html),
[signals/slots](https://doc.qt.io/qtforpython-6/tutorials/basictutorial/signals_and_slots.html).
Widgets змінюються тільки у GUI thread; worker передає стан сигналами.
