# KiCad-проєкт SR-RX-v2: схема електрична принципова

Цей проєкт KiCad 10 побудовано через KiCad MCP сервер. Джерело всіх даних — [../../STACK.md](../../STACK.md) (стек v2). Статус: теоретичний проєкт, перевірити на стенді.

## Склад
| Файл | Що це |
|---|---|
| `sr-rx-v2.kicad_pro`, `sr-rx-v2.kicad_sch` | проєкт і коренева схема з п'ятьма ієрархічними аркушами |
| `E1.kicad_sch` | живлення: акумулятор, захист, перетворювачі, INA3221 |
| `E2.kicad_sch` | захищені канали (4× TPS259470ARPWR, TPS2553DBVR-1, TPS259630DDAR) і LNB (TPS7A4701) |
| `E3.kicad_sch` | керування: 40-пінний роз'єм Q6A, I2C2, MCP23017 #1/#3/#4, GNSS LC76G, IMU, HMI |
| `E4.kicad_sch` | РЧ-тракт: порти P1–P7 і BENCH, фільтри, LNA, HMC7992, SDR |
| `E5.kicad_sch` | USB, VBUS і роз'єми корпусу |
| `sr_rx_v2_pwr.kicad_sym`, `sr_rx_v2_sig.kicad_sym` | символи проєкту, яких немає в стандартних бібліотеках; виводи взято з даташитів |
| `sr-rx-v2.pdf`, `svg/` | експорт через `kicad-cli` |

Позначення елементів кожного аркуша мають свій діапазон, щоб номери не повторювалися між аркушами:

| Аркуш | Позиції |
|---|---|
| E1 | 100–199 |
| E2 | 200–299 |
| E3 | 300–399 |
| E4 | 400–499 |
| E5 | 500–599 |

Між аркушами кола з'єднуються глобальними мітками з однаковими назвами: VBAT, LAB5, LIME3V3, I2C2_SDA, MCP_INT, EN_*, FLT_* тощо. Значення, які STACK.md лишає відкритими, мають позначку `TBD`. Біля кожного такого значення стоїть примітка з розділом STACK і стендовим тестом, який його визначить.

## Як підключити той самий MCP сервер у себе
Сервер: [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) v2.8.2 (MIT). Він працює через stdio JSON-RPC, а для живої роботи з відкритим KiCad є експериментальний режим через IPC API.

Потрібно:
- KiCad 10 (на Ubuntu — PPA `kicad/kicad-10.0-releases`);
- Node.js 20+;
- Python з модулем `pcbnew`.

Встановлення:

```bash
git clone https://github.com/mixelpixx/KiCAD-MCP-Server.git && cd KiCAD-MCP-Server
python3 -m venv --system-site-packages venv && ./venv/bin/pip install -r python/requirements.txt
npm install && npm run build
claude mcp add kicad -- node "$PWD/dist/index.js"
```

Конфігурація для інших клієнтів:

```json
{ "mcpServers": { "kicad": { "command": "node", "args": ["/шлях/KiCAD-MCP-Server/dist/index.js"],
  "env": { "PYTHONPATH": "/usr/share/kicad/scripting/plugins", "KICAD_AUTO_LAUNCH": "false" } } } }
```

На що зважати:
- **Бібліотеки символів.** Якщо KiCad ще жодного разу не запускали, скопіюйте `/usr/share/kicad/template/sym-lib-table` у `~/.config/kicad/10.0/`, інакше сервер не бачить стандартних бібліотек.
- **Тайм-аут пошуку.** Перший `search_symbols` індексує всі бібліотеки, і це може тривати понад 30 с. Такий запит обривається вбудованим тайм-аутом сервера, тому збільште його.
- **Конфлікт Python.** Не додавайте `/usr/lib/python3/dist-packages` у `PYTHONPATH`, якщо версія Python у venv інша, ніж у системі: тоді не завантажується Pillow.
