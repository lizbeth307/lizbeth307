# Приймальний процес labrx

Реалізовано потік **джерело → RAM → FFT → обов'язкова маска → спектр/огляд**. Синтетичний вхід працює без SDR. Фізичні bindings використовують офіційні C API librtlsdr та libairspyhf; відкриття відбувається лише за явним унікальним serial. Це Python/NumPy реалізація для спектральної обробки, а не підтверджений C++ тракт 56 MS/s. Пропускну здатність Q6A, паралельний LRPT/HRPT та приймання Lime тут не заявлено.

## Запуск

З кореня проєкту, Python3.11+ і NumPy:

```sh
PYTHONPATH=software:. python3 -m srrx.labrx --simulate --center-hz 100000000 --sample-rate 1024000 --frames 10 --output /tmp/srrx/latest.json --survey /tmp/srrx/survey.jsonl
```

`--frames 0` працює до Ctrl-C. `latest.json` атомарно замінюється; JSONL містить лише маскований спектр. Усі синтетичні результати мають `source=SIMULATION`. Усі частоти задаються в Hz, sample rate — комплексних відліків за секунду. Наявність RF-сигналу не є доказом класу або публічності його вмісту.

Маски [SPECTRUM](SPECTRUM.md) застосовуються також до вигаданого або завантаженого кадру перед записом/навчанням. Немає IQ/audio recorder, raw-sample UDP/TCP export, EEPROM write або bias-ON API. Голосові позначки зберігають лише спектр. Жодних координат передавачів чи їхніх ідентифікаторів не записується.

## Фізичний шлях

Спершу треба завершити справжнє приймання з [software/README](README.md). `labrx --hardware` самостійно повторно перевіряє весь acceptance, потім зв'язує driver record із його hashed artifacts. Приклад фізичного запуску після приймання:

```sh
PYTHONPATH=software:. python3 -m srrx.labrx --hardware --acceptance /etc/srrx/acceptance.json --driver-record /opt/srrx/evidence/rtl-driver.json --socket /run/srrx/control.sock --center-hz 100000000 --sample-rate 1024000 --frames 100 --output /data/products/latest.json
```

Driver record має точні поля `v=1`, `backend` (`rtl` або `airspyhf`), `branch` (`RTLA`/`RTLB` або `HFP`), `serial`, `library_path`, `library_sha256`, `rx_only_reviewed=true`, `bias_disabled_verified=true`, `dependencies_reviewed=true`. Сам JSON мусить бути локальним файлом усередині проєкту й фігурувати як `{path,sha256}` у доказах прийнятого gate. Шаблон [rtl-driver.template.json](config/rtl-driver.template.json) навмисно неприйнятний. Дайджест зв'язує байти; він не доводить справність ELF, залежностей, V4-підтримки або фізичне вимкнення bias.

Для HF+ driver-record serial — рівно **16 hex digits**, які передаються до `airspyhf_open_sn` як uint64. Повний USB descriptor `AIRSPYHF SN:…` використовується окремо в udev/devices config; копіювати префікс у driver record не можна.

Процес лише спостерігає за `labd`: живий прийнятий Pico, ACTIVE, налаштований MCP, armed policy і ввімкнена конкретна VBUS-гілка обов'язкові. Оренду створює оператор у меню/`labctl hold`, а не RX-процес. Зміна Pico session, відмова control service, втрата дозволу/живлення або відсутність свіжого блока припиняє потік. Повторне відкриття після відмови потребує явного запуску.

C driver працює в окремому дочірньому процесі; його USB read не блокує перевірку labd. Блоки не пишуться на диск, черги обмежені, core dumps вимкнені у worker. При завершенні worker закривається, до labd надсилається OFF вибраної VBUS-гілки навіть після помилки конструктора/cleanup. Убитий процес не доводить фізичний USB timing; це предмет стендового тесту. Захист від swap забезпечує окрема конфігурація системи, а не Python.

RTL налаштовується з direct sampling OFF, bias OFF, tuner AGC і digital AGC OFF; bias ON не викликається. Серійні номери мають бути унікальними; індекс 0 як fallback заборонений. HF+ використовує live supported-rate list та штатну калібровку бібліотеки без додаткової ppm-компенсації. У версії1.6.8 bias API немає; при наявності пізнішого API викликається тільки OFF. Відповідність плати й відсутність небажаного живлення все одно має бути виміряна.

Lime залишається заблокованим у runtime. Експериментальний source patch у deployment не є доказом повного аудиту всіх TX/raw-register шляхів або приймання на Micro M.2; приймальні програми не можуть відкрити його через цей backend. SatDump/live decoder transport та весь початковий каталог декодерів ще не інтегровані в цей спектральний процес.

Первинні ABI: [Osmocom rtl-sdr.h](https://github.com/osmocom/rtl-sdr/blob/master/include/rtl-sdr.h), [AirspyHF header](https://github.com/airspy/airspyhf/blob/master/libairspyhf/src/airspyhf.h), [AirspyHF1.6.8 implementation](https://github.com/airspy/airspyhf/blob/1.6.8/libairspyhf/src/airspyhf.c). Довідкові URL не є supply-chain pin; точні перевірені ревізії та hashes містяться в deployment.
