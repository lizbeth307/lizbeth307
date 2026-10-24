# Огляд інтеграції сервісу, 20 жовтня 2026

Доповнення v0.3.1: наведені нижче лічильники й обмеження AF_UNIX описують початковий хостовий набір. Для перевірки справжніх Linux IPC, systemd, UID/permissions і відмов підготовлено окреме [середовище Ubuntu ARM64](../deployment/linux_lab/README.md). Поточні виправлення UART, RX worker і накопичувача описані в [FINDINGS.md](../deployment/linux_lab/FINDINGS.md); результати VM не підміняють хостовий SKIP.

Додано `tests/test_service_failures.py`: **19 тестів, 18 PASS, 1 явний SKIP** у цьому середовищі. Перевірено справжні `Engine`, `SimLink`, обидва wire codecs і переносну модель Pico Supervisor. Поточний загальний результат усіх `software/tests` збережено в `verification/software-tests.json`; цей огляд фіксує окремий набір інтеграційних сценаріїв. Окремо успішно запущено реальний дочірній процес `python -m srrx.daemon --simulate --stdio` із JSON-запитами через pipes.

Це програмні інтеграційні перевірки. Вони не створюють hardware acceptance, не вимірюють ADC, не керують GPIO/I²C/UART пристрою і не закривають апаратних воріт E1–E5.

## Результати відмов

| Сценарій | Перевірений результат |
|---|---|
| Pico STATUS перестає надходити | Після >500 ms свіжість втрачена, всі навантаження/реле/маршрути вимкнені, CHG_INHIBIT залишається HIGH |
| Повторюється старий STATUS із тим самим sequence | Повтор не оновлює `last_status_ms`; спрацьовує той самий timeout |
| Host→Pico heartbeat зникає, зворотний STATUS ще доступний | Справжня модель Pico застосовує свій 750 ms watchdog, asserts MCP RESET і вимикає display; host скидає дозвіл |
| UART write або GPIO/I²C read дає OSError | Host переходить у trip; відновлення виклику не поновлює дозвіл чи навантаження |
| Active-low FAULT, потім справний HIGH | Fault залишається засувкою; один лише HIGH не відновлює роботу |
| Закінчується lease; потім приходить пізнє поновлення | Виходи вимкнені, lease не знімає fault і не виконує arm |
| Pico перезапускає сесію | Попередній дозвіл відкликано; новий HELLO не відновлює навантаження |
| Explicit recover після усунення fault | Можна повторно armed, але всі попередньо увімкнені навантаження залишаються OFF |
| Некоректні типи RPC, NaN, глибокий JSON | Parser повертає відмову без energizing; `_owner` береться із server peer UID, а не з JSON |
| Сторонній owner намагається ввімкнути навантаження | Відмова; вимкнути навантаження дозволено навіть іншому owner |
| Link.close дає OSError | Hardware і telemetry все одно закриваються через finally; safe image вже застосовано |

CHG_INHIBIT=HIGH у таблиці означає програмний safe image для ініціалізованого MCP. Поки MCP утримується в RESET, його контакти Hi-Z; програмне забезпечення не гарантує HIGH на фізичній лінії. У цей час заряджання обмежують автономні апаратні захисти/NTC, які ще потребують приймання.

У fake-clock тестах час подається з кроком 20 ms. Це перевіряє логіку дедлайнів, а не гарантує планування Linux під навантаженням або фізичний час reset. Успіх операції в симуляції не є виміром струму, RF/DC-порога, наявності живлення чи pinout отриманого модуля.

## Виправлені під час незалежного огляду дефекти

1. **Тип поля `state` у codec-valid STATUS.** Раніше `state=[]` або `{}` потрапляв у membership set і давав uncaught TypeError. Root додав перевірку типу до membership. Регресія пропускає ці payload через реальний encoder/decoder і підтверджує trip без винятку. Також перевірено ACTIVE із RESET HIGH, неправильним типом RESET, false calibration/commissioning/Q6A/HB readiness.
2. **Live Pico identity перед фізичним ARM.** Тепер HELLO має serial, calibration CRC32 і `qualification_record`; Engine звіряє перші два з уже завантаженим acceptance, а digest — із SHA256 точних байтів цього acceptance (HW-10; хибний чи відсутній digest дає `pico_qualification_record_mismatch`). Missing/wrong serial і wrong CRC блокують ARM до MCP-конфігурації; matching fixture дозволяє розпочати handshake. Це перевірка внутрішньої boundary із in-memory fixture, а не підроблений прийнятий файл чи реальна кваліфікація пристрою.
3. **Cleanup при помилці link.close.** Root додав вкладені finally, що забезпечують виклики hardware/telemetry close і позначення closed, навіть коли транспорт кидає виняток. Регресія підтверджує звільнення решти ресурсів і вимкнений стан.

Після цих виправлень відкритого дефекту в перевірених сценаріях не виявлено. Це не замінює ширшого апаратного приймання та перевірки встановлення.

## Фізичний режим і симуляція

Default backend — SIMULATION, із synthetic branch samples і явним `hardware_qualified=false`. Тест підтверджує, що симуляція не створює acceptance. Фізичний startup у `daemon.main` має спершу пройти `commissioning.load_acceptance`, отримати явно задані I²C/UART шляхи, а потім свіжий Pico handshake з відповідними serial/calibration CRC. Без acceptance або із mismatch виходи не ініціалізуються й ARM не передається.

`Engine` — внутрішній single-writer компонент; його аргумент acceptance є вже перевіреним словником від startup validator. Прямий Python-виклик конструктора з довільним словником не є процедурою hardware commissioning. Тестова fixture не зберігається в acceptance чи вимірювальних файлах. Branches без фізичного ADC залишаються reservations/unknown, а не «виміряними» каналами; це також покривають policy/telemetry тести інших модулів.

CRC UART виявляє помилки, serial/CRC metadata зв'язує конфігурацію із заявленим Pico; вони не є автентифікацією UART або криптографічним доказом фактично завантаженої прошивки. Фізичне розгортання й hardware gates лишаються обов'язковими.

## Реальний IPC smoke і пропущена перевірка

Дочірній stdio-сервіс пройшов послідовність: status SIMULATION/disarmed → explicit arm → ACTIVE → EN_LNA1 ON → invalid RPC відхилено → втрата Pico link → всі виходи OFF → повернення link → стан залишається latched → EOF → clean exit0. Це реальні pipes/процес і той самий Engine, а не окремий mock daemon.

Тест реального **AF_UNIX socket** збережено, але тут він SKIP: сама `socket.socket(AF_UNIX, SOCK_STREAM)` повертає `[Errno1] Operation not permitted` до bind/listen. Parser/UID boundary окремо перевірено прямим викликом server handler із тестовим peer UID. Реальні SO_PEERCRED, socket permissions, single-writer lock, oversized socket-client disconnect і Unix-client cleanup мають бути прогнані на Linux, де дозволено AF_UNIX. Їх не позначено PASS на підставі stdio-тесту.

Відтворення з кореня репозиторію:

```sh
PYTHONPATH=software python -m unittest discover -s software/tests -p test_service_failures.py -v
```

Огляд читав `srrx/engine.py`, `daemon.py`, `link.py`, `hardware.py`, `policy.py`, `runtime_telemetry.py`, `commissioning.py`, `wire.py` та `firmware/pico/supervisor.py`/`main.py`. Змінено лише цей звіт і `tests/test_service_failures.py`; PCB та схемні графи не змінювалися.
