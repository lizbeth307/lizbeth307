# Виконуване ПЗ керування — 20.10.2026

Після схем E1–E5 реалізовано Pico Supervisor, зовнішній RP2040-Zero/BNO085, shared UART/CRC, Linux I²C/UART service `labd`, CLI `labctl`, калібрування/приймання та systemd units. Актуальні команди запуску, інтерлоки, межі й формат приймання — [software/README.md](../software/README.md).

Програмні тести, перевірка реального stdio-процесу та детермінована симуляція не є стендовим PASS. `verification/software-tests.json` містить фактичні результати, skips і hashes. `verification/software-simulation.json` показує повний шлях ARM → bias → втрата UART → OFF/RESET → зв'язок без auto-arm → явне recovery з усіма навантаженнями OFF → FAULT latch.

Для плат підготовлено [PCB package](13-pcb-preparation.md) і реальний KiCad placement starter на 71 компонент. Його 187 контактів зіставлено зі схемою. Усі траси ще нерозведені; raw DRC збережено, Gerber не випускався. Це не закриває 425 невизначених footprint решти активних custom-board елементів.

Наступним етапом реалізовано [RX/FFT](../software/RX.md), [Qt-меню](../software/HMI.md), [GNSS](../software/LOCATION.md), [навчання](../software/LEARNING.md), [декодерні адаптери](../software/DECODERS.md) та [deployment](../software/DEPLOYMENT.md). Консоль реально запускає SIM labd і FFT, анотує спектр, навчає й зберігає модель. Qt offscreen views — verification/hmi-views. Є також окремий прототип внутрішнього розведення DC_CORE; його README/raw DRC описують поточний стан точніше за опис первинного нерозведеного starter.

Усі 37 апаратних умов залишаються OPEN. Стан випуску — BLOCKED. Потрібні реальні ревізії/розпіновки модулів, фізичні докази приймання, MPN/корпус/зовнішні інтерфейси й завершені виробничі плати. Повний C++ data plane56MS/s/Lime, весь каталог декодерів, HTP/QAIRT-приймання та встановлений A/B образ не заявлені як виконані. Цей стан зафіксовано в STACK.md; фрази «власного ПЗ ще немає» застаріли.
