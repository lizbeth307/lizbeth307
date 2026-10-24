# Рецепт SatDump +lab (2.0.0~alpha+git20260929+lab1)

Стан: **PENDING_BUILDER**. Рецепт, повнота опцій і накладання патчів перевірено офлайн, на закріплених файлах 1aedd60 24.10.2026. Збирання arm64, трасування плагінів і декодування фікстури ще не виконувалися: збирач пакетів +lab — окремий пакет етапу 3.

| Файл | Що містить |
|---|---|
| `recipe.json` | джерело (архів з `sources.lock.json`), патчі з SHA256 і blob-ідентифікаторами цільових файлів, усі 105 опцій CMake поіменно (ON лише алоу-лист плагінів `receive-only-policy.json`, `PLUGINS_ALL=OFF`), розкладка встановлення, крок пакування, перевірки збирача |
| `upstream-options.json` | кожен `option()` зі 117 файлів `CMakeLists.txt`/`*.cmake` закріпленого дерева (git trees API, 24.10.2026), з типовими значеннями й умовами `OR PLUGINS_ALL` |
| `patches/0001-cli-add-option-c0b6f88.patch` | cherry-pick c0b6f8876c51… (#1191): `--key value` і `--key=value` |
| `patches/0002-clock-recovery-free-6b5957f.patch` | cherry-pick 6b5957fa5268…: звільнення буфера clock recovery |
| `patches/0003-lab-udp-loopback.patch` | +lab: `net::UDPServer` слухає 127.0.0.1 замість INADDR_ANY (другий шар під unit з IPAddressDeny=any) |
| `check_recipe.py` | `check` (рецепт проти маніфесту, патчів і політики), `verify-source --source DIR` (розпакований архів), `package --root DESTDIR [--manifest OUT]` (п'ять конвеєрів без `elektro_ggak_mqtt`, строгий `satdump_cfg.json` з «Never» і без URL TLE, лише алоу-лист плагінів) |

SatDump розповсюджується за GPL-3.0 (upstream `LICENSE`, blob f288702d2fa16d3cdf0035b15a9fcbc552cd88e7). Патчі — похідні зміни за тією самою ліцензією.

Порядок для збирача (без мережі, `unshare --user --map-root-user --net`): перевірити SHA256 архіву → розпакувати → `check_recipe.py verify-source` → `patch -p1` 0001–0003 → `cmake` з `cmake.definitions` → збірка `-j4` → `DESTDIR=… cmake --install build` → `check_recipe.py package --root … --manifest stage.json`. Отримані SHA256 ELF, плагінів, конвеєрів і конфігу адміністратор переносить у root-owned запис встановлення `decoder_policy.load_satdump_installation` (див. [DECODERS](../../../software/DECODERS.md)).

Відкрите питання до власника: `PLUGIN_SIMD_NEON` вимкнено, бо `simd_neon` немає в алоу-листі плагінів STACK. Вмикати його — лише окремим рішенням після заміру CPU на Q6A.
