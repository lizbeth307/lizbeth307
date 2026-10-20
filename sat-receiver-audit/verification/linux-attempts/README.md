# Попередні Linux-прогони — історичні результати

Ці запуски завершились FAIL і не підтверджують поточну редакцію. Первинні результати збережені без переписування статусів; project-manifest.json прив’язує їх до тодішнього payload. Фінальний актуальний результат зберігається окремо в ../linux-lab/.

- run03: виявлені termios EIO та RX core-collector дефекти; відсутній C++ compiler і неправильне очікування першого ENOSPC у harness. Ці причини виправлялися перед наступними запусками.
- run04: production/regression/PTY/RX/storage/module набори пройшли. System smoke отримав GPIO-stale safety trip під навантаженням від запуску нового Python process на кожний RPC; залежні GUI/XCB не мали control socket. Старий lease_expiry_latched PASS мав іншу причину fault і не доводить саме expiry: наступний harness перевіряє точний fault.

- run05: unit/system/GUI/RX/storage/module набори пройшли. PTY recovery handshake не завершився; той звіт не мав достатнього trace для точної причини. Пізніше виправлено доведені protocol/queue races у fixture, зокрема відсутність повторного HELLO, і додано структурну діагностику. XCB observer відмовив через один timeout read-only запиту під час Qt startup; наступний harness має bounded retry та явно звітує прогалини спостереження.

- run06: ABORTED через втрату exec-server до тестів. Зафіксовані нерухомі timestamps і read-only lock/image перевірки; результатів застосунку немає. Цей overlay не використано для наступного кешу.

Cached OS/dependencies від цих зупинених VM могли використовуватися наступними запусками. Це записано в run.json; current sources щоразу замінені, звірені hashes і перевірені повторно. Історичні PASS не переносяться на змінені джерела, апаратне приймання не виконувалось.
