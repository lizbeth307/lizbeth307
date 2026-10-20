# Виконуване ПЗ керування — 20.10.2026

Після схем E1–E5 реалізовано Pico Supervisor, зовнішній RP2040-Zero/BNO085, shared UART/CRC, Linux I²C/UART service `labd`, CLI `labctl`, калібрування/приймання та systemd units. Актуальні команди запуску, інтерлоки, межі й формат приймання — [software/README.md](../software/README.md).

Програмні тести, перевірка реального stdio-процесу та детермінована симуляція не є стендовим PASS. `verification/software-tests.json` містить фактичні результати, skips і hashes. `verification/software-simulation.json` показує повний шлях ARM → bias → втрата UART → OFF/RESET → зв'язок без auto-arm → явне recovery з усіма навантаженнями OFF → FAULT latch.

Для плат підготовлено [PCB package](13-pcb-preparation.md) і реальний KiCad placement starter на 71 компонент. Його 187 контактів зіставлено зі схемою. Усі траси ще нерозведені; raw DRC збережено, Gerber не випускався. Це не закриває 425 невизначених footprint решти активних custom-board елементів.

Усі 36 апаратних умов залишаються OPEN. Стан випуску — BLOCKED. Потрібні реальні ревізії/розпіновки модулів, фізичні докази приймання та завершене розведення; також залишаються повний SDR data plane, частина HMI, NPU та перевірений системний образ. Ця редакція має пріоритет над фразою «власного ПЗ ще немає» в історичних матеріалах від 19.10.2026.
