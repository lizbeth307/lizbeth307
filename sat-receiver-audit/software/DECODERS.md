# Декодери: дозвільні профілі та фактична межа

Модуль `srrx.decoder_policy` реалізує виконуваний **офлайн WAV → PNG профіль цивільної погоди**. Наявність коду не означає встановлення зовнішнього декодера. У цьому комплекті немає прийнятого запису встановлення; запуск за замовчуванням недоступний. Апаратне приймання не виконано.

```sh
PYTHONPATH=software:. python3 -m srrx.decoder_policy status
PYTHONPATH=software:. python3 -m unittest discover -s software/tests -p test_decoder_policy.py -v
```

| Профіль | Стан і межа |
|---|---|
| `noaa-apt-weather` | Реалізований file-only runner для **noaa-apt 1.4.1**, вихід — лише погодне PNG і звіт фіксованої структури; потрібні прийняте встановлення та погоджений mono PCM16 WAV |
| `satdump-weather` | Недоступний: конкретний встановлений RX-only build і відповідна версія CLI не кваліфіковані |
| `egc-safetynet` | Вимкнений. Окремий модуль `srrx.egc_gate` класифікує заголовки за правилами egc-gate на синтетичних пакетах, але цей профіль його не імпортує і жодних байтів пакетів не читає; вмикання — лише після перевірки таблиці C2, змішаного запису ПОЛ-06 і алгоритму контрольної суми ([SCOPE-POLICY.md](SCOPE-POLICY.md)) |
| `dsc-safety` | Вимкнений до перевіреного парсера format/category і тестових векторів; жодні адреси/MMSI або payload не читаються |
| `amateur-digital` | Недоступний: конкретний decode-only профіль і версія CLI не кваліфіковані |
| `ais-public`, `adsb-public` | Недоступні: не реалізовано/не кваліфіковано обов'язкові фільтри військових об'єктів та їхні дані |

EGC/DSC не замінені фільтром уже декодованого тексту. Відмова відбувається за назвою профілю **до відкриття джерела чи метаданих**. Немає заяви про виконаний SafetyNET/DSC gate: юніт-тести `egc_gate` на синтетичних пакетах профіль не вмикають, і окремий тест перевіряє, що `availability()` далі повертає `DISABLED_NO_VERIFIED_HEADER_PARSER_AND_TEST_VECTORS`. Непідтверджені протокольні поля не вигадані.

## Межі сеансу (стоп Artemis і маски)

`make_plan(..., scope=None)` і `execute(..., scope=None)` приймають засувку сеансу `scope_policy.ScopeLatch` ([SCOPE-POLICY.md](SCOPE-POLICY.md)). Перевіряється вся смуга метеосупутників 137–138 MHz: стоп замаскованої смуги діє завжди, передана засувка додає стоп Artemis. Перевірка `decode` виконується після схеми метаданих, але **до** будь-якого доступу до запису встановлення чи файла джерела; перевірка `export` — безпосередньо перед атомарним перейменуванням результату, тож стоп під час роботи декодера залишає лише видалений тимчасовий каталог. Відмова — `OUT_OF_SCOPE` без частоти; інший об'єкт замість засувки — `SCOPE_LATCH_REQUIRED`. Без засувки поведінка CLI не змінилася. Уже опубліковані результати автоматично не видаляються.

## Перевірена зовнішня команда

Джерела перевірено 20.10.2026:

- [Офіційна інструкція noaa-apt](https://noaa-apt.mbernardi.com.ar/usage.html) описує `input.wav -o output.png`, `--map no`, `--rotate no`, `--quiet`; IQ без FM-демодуляції не підтримується.
- [Офіційний release v1.4.1](https://github.com/martinber/noaa-apt/releases/tag/v1.4.1) вказує commit **48a9eb8321f722634aafd1f9dcf4d80e9bfe274d**; [зміна версії в цьому коміті](https://github.com/martinber/noaa-apt/commit/48a9eb8321f722634aafd1f9dcf4d80e9bfe274d) встановлює 1.4.1.
- Перевірено [парсер аргументів саме цього коміту](https://github.com/martinber/noaa-apt/blob/48a9eb8321f722634aafd1f9dcf4d80e9bfe274d/src/config.rs) і [режими запуску](https://github.com/martinber/noaa-apt/blob/48a9eb8321f722634aafd1f9dcf4d80e9bfe274d/src/main.rs). `--version` у цій версії **безумовно виконує перевірку оновлень через мережу**, тому runner його не запускає. Натомість bounded `--help` перевіряє потрібний інтерфейс; точна версія прив'язується прийнятим source commit і SHA256 бінарника.

Команда завжди створюється всередині модуля:

```text
/прийнятий/шлях/noaa-apt /тимчасовий/input.wav -o /тимчасовий/output.png --map no --rotate no --quiet
```

Job не може додати аргументи, оточення, pipeline, URL, SDR-пристрій, gain, bias, TX, shell або output sink. `shell=False`; executable — абсолютний ELF `noaa-apt`, root-owned, без group/world write, з точним SHA256. Усі батьківські каталоги executable і запису встановлення теж мають належати root без group/world write (world-writable дозволено лише зі sticky bit), бо runner повторно хешує файл і запускає його за шляхом: інакше процес без прав root може перейменуванням підмінити бінарник між перевіркою та `execve`. Скрипти й PATH lookup не приймаються. Не запускаються SatDump live/record, TX-capable GUI або довільний декодер.

Санітарний звіт і plan manifest містять лише фіксовані поля, hash, розміри й символічні аргументи. Шляхи джерела, evidence text, stdout/stderr і декодовані текстові повідомлення до звіту не потрапляють. Decode stdout/stderr відразу спрямовані в `/dev/null`; лише bounded `--help` тимчасово читається в пам'яті. Тайм-аут декодування 0.05–300 s; окрема перевірка `--help` має до 3 s. При завершенні/тайм-ауті закривається вся створена process group.

Це політика запуску довіреного декодера, **не OS sandbox для недовіреного виконуваного файла**. Прийнятий ELF та його походження мають бути перевірені адміністратором. Модуль не підтверджує сам факт походження бінарника лише за написаним у JSON source commit. Зміна SHA256 скасовує прийняття; інша версія відхиляється. Відсутні root-owned записи не створюються автоматично.

## Метадані погодженого джерела

`labrx` не зобов'язаний записувати IQ, щоб працював цей профіль: потрібен окремо погоджений **FM-демодульований погодний WAV** або погоджений публічний архів. Цей модуль не виконує IQ-демодуляцію, не вмикає запис IQ і не відкриває SDR. NOAA APT профіль також придатний для історичних записів; тут немає обіцянки, що певний супутник зараз передає.

Приклад структури, який треба заповнити фактичним SHA256 і evidence ID:

```json
{
  "v": 1,
  "sha256": "ACTUAL_64_LOWERCASE_HEX_SHA256",
  "purpose": "public_civil_weather",
  "satellite": "NOAA-19",
  "origin": "approved_public_archive",
  "evidence_id": "archive/acceptance-001",
  "voice_present": false,
  "private_payload": false,
  "military": false,
  "emitter_geolocation": false,
  "iq_retained": false,
  "format": "wav_pcm_s16le_mono"
}
```

Допустимі джерела: `approved_labrx_audio` або `approved_public_archive`; супутники — NOAA-15/18/19. Невідомі поля заборонені. Кожне з п'яти заборонних полів мусить бути саме boolean `false`, а не `0`, рядок або null. Mono PCM16 WAV перевіряється реально, включно з довжиною sample data, 8–192 kHz і межею 256 MiB. SHA256 перевіряється перед запуском і повторно для окремого тимчасового snapshot.

Ці поля — **запис прийняття від довіреного джерела/оператора, не автоматичне розпізнавання вмісту сигналу**. Підписати приватний чи голосовий запис словом «погода» недостатньо для прийняття в системі. Не передавайте приймальні записи неперевіреним клієнтам для самостійного редагування; daemon не надає RPC, що обминає це правило. Захист voice/no-IQ і military band mask на вході залишається обов'язком приймального data plane.

## Прийняте встановлення та запуск

Запис встановлення — локальний root-owned JSON без group/world write у каталогах із тим самим правилом. Його готує адміністратор після перевірки пакета/збірки, а не завдання декодування:

```json
{
  "v": 1,
  "tool_id": "noaa-apt",
  "version": "1.4.1",
  "source_commit": "48a9eb8321f722634aafd1f9dcf4d80e9bfe274d",
  "executable": "/opt/noaa-apt/noaa-apt",
  "sha256": "ACTUAL_64_LOWERCASE_HEX_SHA256",
  "evidence_id": "admin/reproducible-build-and-package-verification-001"
}
```

Приклад не є чинним приймальним записом. Реальний vendor binary тут не встановлено й end-to-end погодне зображення зовнішнім декодером не отримано.

```sh
PYTHONPATH=software:. python3 -m srrx.decoder_policy plan \
  --preset noaa-apt-weather --source /дані/погодний.wav \
  --metadata /дані/погодний.metadata.json \
  --installation /etc/srrx/noaa-apt.accepted.json

PYTHONPATH=software:. python3 -m srrx.decoder_policy run \
  --preset noaa-apt-weather --source /дані/погодний.wav \
  --metadata /дані/погодний.metadata.json \
  --installation /etc/srrx/noaa-apt.accepted.json \
  --output-directory /результати/новий-сеанс --timeout-s 60
```

Батьківська папка результату має існувати; папка нового сеансу — ще ні. Публікуються лише `weather.png` і `report.json`. PNG перевіряється на структуру/CRC/розміри, ancillary text/EXIF chunks видаляються, решта тимчасових файлів декодера не передається. Це не оцінка правильності метеорологічного зображення. Тести використовують синтетичний PNG та підміну vendor boundary; окремі process tests справді запускають bounded дочірній процес. Вони не видаються за встановлений або випробуваний noaa-apt на Q6A.
