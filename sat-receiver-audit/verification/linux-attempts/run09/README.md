# ARM64 Linux — фактичний результат

Загальний стан **PASS**. Справжній ARM64 Linux `6.8.0-147-generic`, systemd як PID1, QEMU TCG/Cortex-A76, 4 vCPU/3 GiB. Мережевих карт, USB passthrough та спільних каталогів хоста немає; loopback використовується локальними GPSD fixtures. ОС Ubuntu24.04 з generic kernel, а не цільовий Q6A образ/ядро.

| Набір | Фактичний стан |
|---|---|
| `dependency-verification.json` | PASS |
| `software-tests.json` | PASS |
| `system-smoke.json` | PASS |
| `pty-smoke.json` | PASS |
| `gui-smoke.json` | PASS_LINUX_OFFSCREEN_SIMULATION |
| `xcb-smoke.json` | PASS |
| `rx-worker-smoke.json` | PASS |
| `storage-smoke.json` | PASS |
| `module-lab/report.json` | EMULATION_PASS_WITH_GAPS |

Регресії: **838 PASS**, **2 SKIP** із 840 тестів. Причини пропусків наведені в `software-tests.json`; пропуски не зараховані як PASS. System smoke перевіряє справжні systemd sandbox/restart/peer UID і відмову запускати hardware service з OPEN/missing records. PTY, Qt offscreen, XCB/Xvfb і native RX worker lifecycle виконуються реальними процесами.

Storage smoke: **5 PASS** на окремому віртуальному ext4 block device. Перевірено запис маскованого спектра, неправильний пристрій, підміну mount ID, ENOSPC і втрату mount без запису на rootfs. Це не Samsung T7/USB або перевірка фізичного відключення живлення.

[Таблиця модулів](../module-lab/MODULE-RESULTS.md) та автономний `../module-lab/module-results.html` відокремлюють програмні драйвери від моделі з'єднань. Повний `../module-lab/report.json` зберігає всі сценарії та обмеження. Модель з'єднань: `CONNECTION_MODEL_PASS`; її точні лічильники — в `../module-lab/connectivity.json`.

Прогін почато з незмінного locked Ubuntu image без OS cache (`base_overlay: null` у `run.json`). Усі locked DEB і wheels перевстановлено з hash-перевіреного payload, а `dependency-verification.json` підтверджує, що встановлені версії точно збігаються з обома lock. Усі поточні вихідні файли замінено й перевірено за SHA256, пакет перевстановлено, усі набори виконано повторно. `source-binding.json` і `project-manifest.json` дозволяють звірити реально виконаний код. Годинник задається з host preparation timestamp; це не GNSS/PPS/RTC qualification.

37 апаратних воріт залишаються OPEN. Фізичне залізо, аналогові RF/живлення, BMS, калібрування, Q6A peripheral pinmux, повний Lime/56MS/s/HTP та виробничий випуск не прийняті.
