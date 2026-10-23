# Приймальний процес labrx

Реалізовано потік **джерело → RAM → FFT → обов'язкова маска → спектр/огляд**. Синтетичний вхід працює без SDR. Фізичні bindings використовують офіційні C API librtlsdr та libairspyhf; відкриття відбувається лише за явним унікальним serial. Це Python/NumPy реалізація для спектральної обробки, а не підтверджений C++ тракт 56 MS/s. Пропускну здатність Q6A, паралельний LRPT/HRPT та приймання Lime тут не заявлено.

## Запуск

З кореня проєкту, Python3.11+ і NumPy:

```sh
PYTHONPATH=software:. python3 -m srrx.labrx --simulate --center-hz 100000000 --sample-rate 1024000 --frames 10 --output /tmp/srrx/latest.json --survey /tmp/srrx/survey.jsonl
```

`--frames 0` працює до Ctrl-C. `latest.json` атомарно замінюється; JSONL містить лише маскований спектр. Усі синтетичні результати мають `source=SIMULATION`. Усі частоти задаються в Hz, sample rate — комплексних відліків за секунду. Наявність RF-сигналу не є доказом класу або публічності його вмісту.

Маски [SPECTRUM](SPECTRUM.md) застосовуються також до вигаданого або завантаженого кадру перед записом/навчанням. Немає IQ/audio recorder, raw-sample UDP/TCP export, EEPROM write або bias-ON API. Голосові позначки зберігають лише спектр. Жодних координат передавачів чи їхніх ідентифікаторів не записується.

## Запис на знімний накопичувач

Для такого запису треба явно ввімкнути `StorageGuard`: **обидва** параметри `--storage-root` і `--storage-device`. Root має бути вже наявною точною точкою монтування, а device — перевіреним оператором block device саме змонтованого тому, наприклад `/dev/disk/by-uuid/…`. UUID реального T7 невідомий і в проєкті не призначений. Якщо змонтовано розділ, прив'язка має вказувати його, а не весь диск. Приклад після перевірки й монтування оператором:

```sh
PYTHONPATH=software:. python3 -m srrx.labrx --simulate --frames 10 --storage-root /media/T7 --storage-device /dev/disk/by-uuid/REPLACE_WITH_VERIFIED_UUID --output latest.json --survey survey.jsonl
```

`REPLACE_WITH_VERIFIED_UUID` — обов'язкова заміна на фактичний перевірений UUID, не готова конфігурація пристрою. У guarded mode відносні output/survey шляхи відраховуються від `--storage-root`; абсолютні мають лишатися всередині нього. Усі батьківські каталоги вже повинні існувати. Guard не створює відсутній mountpoint чи каталоги, не переходить через symlink або сторонній вкладений mount і не підставляє root filesystem після втрати диска. Без цих параметрів лишається звичайний локальний запис зі створенням parent directories; його не можна використовувати як доказ захищеного запису на T7.

Guard звіряє явний block device, `st_dev`, Linux mount ID з `mountinfo`/`fdinfo` та закріплений directory fd. Втрата, переміщення або підміна mount/bind mount, заміна шляху, read-only стан чи помилка запису, зокрема ENOSPC, назавжди відкликає цей екземпляр guard. Автоматичного відновлення немає: після усунення причини потрібні нова явна прив'язка та запуск capture. Відмова під час уже відкритого guarded capture проходить через cleanup: RX worker закривається й до labd надсилається OFF належної гілки приймача. Це не команда вимкнути живлення T7.

Працює один writer, а mount/output directories мають бути доступні для запису лише довіреному процесу. Advisory lock не захищає від іншого writer, який його ігнорує, або привілейованих змін mount namespace. Запис іде через `dirfd`/`O_NOFOLLOW` та staging file з atomic replace. Попередній файл зберігається при помилці **до commit**; помилка directory fsync після replace вже не гарантує збереження попередніх байтів чи стійкість при втраті живлення.

Guarded JSONL append до наявного файла дописує лише новий рядок у той самий перевірений inode (вартість O(рядка), без копії всього файла) і після помилки write/fsync обрізає файл до попередніх повних рядків. Новий файл створюється через staging і atomic replace. Втрата живлення під час append може лишити один обірваний останній рядок; наступний append до такого файла відмовляє й відкликає guard. Ліміт файла — **64 MiB**, автоматичного rollover немає. Рядок спектра має приблизно 34–38 KB при `--fft-size 1024` (близько 1900 кадрів на файл) і 560–600 KB при 16384 (близько 115 кадрів); за частоти кадрів RX це хвилини або секунди. До межі слід завершити capture й явно обрати новий файл. Досягнення межі дає помилку та відкликає guard.

Перед sync/unmount/вимкненням живлення оператор має завершити capture і закрити guard, який утримує directory fd тому. Сам guard не монтує, не форматує, не виконує unmount і не керує EN_T7. Фізичний T7, USB3/UAS, поведінка при USB removal, тривалий запис і порядок sync/unmount/power-off залишаються непідтвердженими; програмні fixture-перевірки цього не замінюють.

## Фізичний шлях

Спершу треба завершити справжнє приймання з [software/README](README.md). `labrx --hardware` самостійно повторно перевіряє весь acceptance, потім зв'язує driver record із його hashed artifacts. Приклад фізичного запуску після приймання:

```sh
PYTHONPATH=software:. python3 -m srrx.labrx --hardware --acceptance /etc/srrx/acceptance.json --driver-record /opt/srrx/evidence/rtl-driver.json --socket /run/srrx/control.sock --center-hz 100000000 --sample-rate 1024000 --frames 100 --output /data/products/latest.json
```

Driver record має точні поля `v=1`, `backend` (`rtl` або `airspyhf`), `branch` (`RTLA`/`RTLB` або `HFP`), `serial`, `library_path`, `library_sha256`, `rx_only_reviewed=true`, `bias_disabled_verified=true`, `dependencies_reviewed=true`. Сам JSON мусить бути локальним файлом усередині проєкту й фігурувати як `{path,sha256}` у доказах прийнятого gate. Шаблон [rtl-driver.template.json](config/rtl-driver.template.json) навмисно неприйнятний. Прив'язка — до всього прийнятого acceptance record (будь-який gate), а не до окремого RX gate. Worker відкриває бібліотеку з `O_NOFOLLOW`, хешує байти з цього descriptor і виконує dlopen того самого inode через `/proc/self/fd`, тож перейменування в каталозі між хешем і завантаженням не підмінить байти. Дайджест зв'язує байти; він не доводить справність ELF, залежностей, V4-підтримки або фізичне вимкнення bias.

Для HF+ driver-record serial — рівно **16 hex digits**, які передаються до `airspyhf_open_sn` як uint64. Повний USB descriptor `AIRSPYHF SN:…` використовується окремо в udev/devices config; копіювати префікс у driver record не можна.

Процес лише спостерігає за `labd`: живий прийнятий Pico, ACTIVE, налаштований MCP, armed policy і ввімкнена конкретна VBUS-гілка обов'язкові. Оренду створює оператор у меню/`labctl hold`, а не RX-процес. Зміна Pico session, відмова control service, втрата дозволу/живлення або відсутність свіжого блока припиняє потік. Запуск worker (spawn, імпорт NumPy, відкриття драйвера) обмежено 10 s; лише після його сигналу готовності діє межа свіжості 1 s на кожен блок. Стан labd перевіряється приблизно кожні 50 ms, зокрема й під час запуску. Повторне відкриття після відмови потребує явного запуску.

C driver працює в окремому дочірньому процесі; його USB read не блокує перевірку labd. Блоки не пишуться на диск, черги обмежені. Процес capture/FFT до дозволу живлення та дочірній worker до завантаження драйвера вимагають `RLIMIT_CORE=0` і Linux `PR_SET_DUMPABLE=0` із перевіркою `PR_GET_DUMPABLE=0`; worker повторює перевірку після конструктора драйвера. Відсутня підтверджена заборона дампів — capture відхиляється. Захист зберігається після cleanup, доки процес може містити залишки IQ у heap. Самого `RLIMIT_CORE=0` недостатньо для систем із piped core collector; див. [core(5)](https://man7.org/linux/man-pages/man5/core.5.html). При завершенні worker закривається, до labd надсилається OFF вибраної VBUS-гілки навіть після помилки конструктора/cleanup. Це стосується також SIGTERM/SIGHUP/SIGINT (kill, systemd stop, обрив SSH, Ctrl-C): обробник запускає той самий cleanup, код виходу 128+номер сигналу. Після першого сигналу наступні ігнорують; перший сигнал, що надійшов уже під час cleanup (закриття worker або запит OFF), не перериває його, а лише дає йому завершитися. Попередження в stderr не може зламати cleanup, навіть якщо термінал уже зник після обриву SSH. Відповідь labd на OFF перевіряється; непідтверджений OFF друкує попередження в stderr, `branch_off_confirmed=false` і код виходу 3. Worker спершу отримує до 0.5 s на штатний вихід із rtlsdr_close/airspyhf_stop+close, потім SIGTERM, потім SIGKILL. Убитий процес не доводить фізичний USB timing; це предмет стендового тесту. Захист від swap забезпечує окрема конфігурація системи, а не Python.

Батьківський процес за кожну ітерацію забирає все, що вже чекає в pipe, і залишає лише найновіші суміжні samples (не менше 16384). Якщо RAM-черга HF+ (64 блоки) заповнена через повільного споживача, callback відкидає новий transfer, а не backlog; наступний блок, що потрапив у чергу, позначається як розрив. Блоки з черги забирає лише `read()`, а прапорець розриву змінює лише callback-потік, тому блок, позначений суміжним, ніколи не йде після відкинутого. Ціна — затримка: після паузи споживача worker спершу вичитує старіший backlog (до 64 transfers), а не найновіші samples. Відкинутий у батьківському процесі backlog або позначений розрив очищують FFT history, тому FFT ніколи не з'єднує несуміжні блоки. USB `dropped_samples` HF+ лишається фатальною помилкою. Послідовні RTL `read_sync` блоки (8192 samples) не доведено суміжними: кожен FFT RTL рахується з одного блока, а `--fft-size` понад 8192 для RTL відхиляється до спостереження labd.

RTL налаштовується з direct sampling OFF, bias OFF, tuner AGC і digital AGC OFF; bias ON не викликається. Серійні номери мають бути унікальними; індекс 0 як fallback заборонений. HF+ використовує live supported-rate list та штатну калібровку бібліотеки без додаткової ppm-компенсації. У версії1.6.8 bias API немає; при наявності пізнішого API викликається тільки OFF. Відповідність плати й відсутність небажаного живлення все одно має бути виміряна.

Lime залишається заблокованим у runtime. Експериментальний source patch у deployment не є доказом повного аудиту всіх TX/raw-register шляхів або приймання на Micro M.2; приймальні програми не можуть відкрити його через цей backend. SatDump/live decoder transport та весь початковий каталог декодерів ще не інтегровані в цей спектральний процес.

Первинні ABI: [Osmocom rtl-sdr.h](https://github.com/osmocom/rtl-sdr/blob/master/include/rtl-sdr.h), [AirspyHF header](https://github.com/airspy/airspyhf/blob/master/libairspyhf/src/airspyhf.h), [AirspyHF1.6.8 implementation](https://github.com/airspy/airspyhf/blob/1.6.8/libairspyhf/src/airspyhf.c). Довідкові URL не є supply-chain pin; точні перевірені ревізії та hashes містяться в deployment.
