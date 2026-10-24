# FFT і спектральна межа даних

`software/srrx/spectrum.py` виконує справжній NumPy FFT і повертає перевірений JSON-compatible spectrum frame. IQ зберігається лише в обмеженому RAM-буфері; module не має запису raw IQ, декодування приватного вмісту, журналу окремих випромінювачів або GNSS-позицій.

## API

```python
import numpy as np
from srrx.spectrum import SpectrumProcessor, append_survey, mask_frame, validate_frame

processor = SpectrumProcessor(fft_size=1024)
iq = .5 * np.exp(2j * np.pi * 31 * np.arange(1024) / 1024)
frame = processor.process(iq, center_hz=145e6, sample_rate_hz=1.024e6,
                          source='SIMULATION')
append_survey('survey.jsonl', frame)
```

NumPy — optional dependency. Поточна перевірка використовувала NumPy2.3.5; без нього `SpectrumProcessor`/`SampleRing` дають явний `SpectrumDependencyError`, без фіктивного FFT fallback. Встановлення: `python -m pip install numpy`. Перевірка/маскування вже готового metadata frame працюють і без NumPy.

Функції:

- `SpectrumProcessor(fft_size=1024, *, capacity_bytes=8*1024**2, chunk_samples=65536)`; FFT size — степінь двійки16…1048576.
- `.process(samples, center_hz, sample_rate_hz, source='SIMULATION') -> frame`. Вхід — одновимірний numeric ndarray/list/tuple, зазвичай нормований complex IQ. NaN/Inf, object/string/bool arrays і переповнення complex64 відхиляються, history очищується.
- `.clear()` очищує власний IQ history. Зміна center/rate/source автоматично очищує history, щоб не змішувати різні налаштування.
- `mask_frame(frame) -> new frame` перевіряє структуру/геометрію і повторно застосовує всі маски. Caller-invalid bins ніколи не стають valid. Invalid power примусово `None`; input не мутується.
- `validate_frame(frame) -> new frame` додатково відхиляє вже немаскований або неканонічний frame. Помилки — `SpectrumError(ValueError)`.
- `append_survey(path, frame, *, storage_guard=None) -> sanitized frame` **спершу mask, потім validate, потім JSONL write**. Воно не довіряє `valid`, не пише extra keys/raw IQ і не торкається файла для невалідної структури. Переданий `StorageGuard` виконує запис після цієї перевірки; без нього зберігається звичайна локальна поведінка зі створенням parent directories.

Перед UI, annotation, export, feature extraction і training споживач мусить виконати `safe = mask_frame(untrusted_frame)`. Вибрані для annotation/training bins мають бути valid; прогалини не інтерполювати й не підміняти нулями. Сам exporter також повторно застосовує цю межу.

## Прив'язка запису до змонтованого тому

Для removable storage можна передати `storage_guard=guard`, де `guard = StorageGuard(root, device)` із `srrx.storage`. `root` — точна вже змонтована точка, `device` — явний block device тому, бажано шлях `/dev/disk/by-uuid/…` з UUID, перевіреним оператором. UUID T7 не вигадується. Відносний шлях у guarded API лежить під root, абсолютний також мусить бути всередині; батьківські каталоги мають вже існувати. Приклад API після зовнішнього налаштування й перевірки тому:

```python
from srrx.storage import StorageGuard

with StorageGuard('/media/T7', '/dev/disk/by-uuid/REPLACE_WITH_VERIFIED_UUID') as guard:
    append_survey('survey.jsonl', frame, storage_guard=guard)
```

Placeholder треба замінити фактичним перевіреним UUID. Guard звіряє block identity, `st_dev`, Linux mount ID та pinned directory fd; використовує `dirfd`/`O_NOFOLLOW`, не створює відсутніх каталогів і не переносить запис на rootfs, коли mount зник. Заміна/втрата тому, bind/nested-mount підміна, read-only або помилка IO/ENOSPC назавжди відкликає екземпляр guard; повторний запис потребує усунення причини та нової явної прив'язки. Звичайний локальний API без guard такого захисту не має.

Guarded append до наявного файла дописує лише новий рядок у той самий перевірений inode (O(рядка), без копії файла); помилка write/fsync обрізає файл до попередніх повних рядків, а обірваний останній рядок після втрати живлення не продовжується. Новий файл створюється staging+atomic replace. Ліміт — **64 MiB на файл**, без автоматичного rollover: це близько 1900 кадрів при N=1024 і близько 115 при N=16384 (рядок 34–38 KB / 560–600 KB). Потрібен один writer і каталоги, доступні для запису лише довіреному writer; advisory lock не є захистом від чужих процесів, що його ігнорують, або привілейованого перемонтування. Помилка до atomic replace зберігає попередній файл. Після replace помилка directory fsync може означати невизначену durability; збереження попередніх байтів і витримування power loss не заявляються.

`labrx` приймає цю прив'язку лише парою `--storage-root`/`--storage-device`; приклад і cleanup RX наведено в [RX.md](RX.md). Guard не монтує, не форматує, не робить unmount і не вимикає EN_T7. Оператор спершу зупиняє capture і закриває guard, потім виконує перевірений sync/unmount/power-off workflow. Фізичний T7, USB3/UAS та апаратний порядок вимкнення залишаються непідтвердженими.

## Точний frame contract

Рівно ці ключі; extra keys відхиляються:

```json
{
  "v": 1,
  "kind": "spectrum",
  "center_hz": 145000000.0,
  "sample_rate_hz": 1024000.0,
  "fft_size": 1024,
  "power_dbfs": [0.0, null],
  "valid": [true, false],
  "relative_frequency_hz": [-512000.0, -511000.0],
  "source": "SIMULATION",
  "sample_count": 1024
}
```

Три масиви в прикладі скорочено; насправді кожен має рівно `fft_size` елементів. Numeric fields мають бути скінченними JSON numbers, boolean не є числом; source — тільки `SIMULATION` або `HARDWARE`. `sample_count` — integer0…FFT size. `relative_frequency_hz[i] = (i - N//2)*(sample_rate_hz/N)` у відсортованому fftshift порядку; підмінити цей grid для обходу маски не можна.

При недостатніх зібраних samples повертається фактичний `sample_count<N` і **всі** bins — `None/False`, без zero-padding, що виглядає як повний вимір. Для повного FFT sample_count=N. Порожній новий блок повертає no-data/count0, а не кешований попередній FFT. Перекривні вікна після непорожнього блоку дозволені. Рамка не містить timestamp/позначення випромінювача або координат.

`source='HARDWARE'` — позначення від acquisition backend, а не доказ commissioning чи амплітудного калібрування. Сам DSP не відкриває SDR, не змінює його смугу/частоту і не видає апаратного дозволу.

## Нормування

Використано periodic Hann: `np.hanning(N+1)[:-1]`, FFT і fftshift. Для кожного біна:

`power_dbfs = 20*log10(max(abs(FFT(iq*window))/sum(window), 1e-15))`.

Це еквівалентно10log10 квадрату амплітуди відносно full-scale complex tone. Нормований complex tone амплітуди1 рівно на FFT-біні дає0dBFS; amplitude0.5 —−6.0206dBFS. Реальний cosine має дві спектральні складові, тому це не автоматично conventional real-ADC sine/RMS calibration. Значення — window/coherent-amplitude bin power, **не dBm і не PSD/dBFS/Hz**. Для інтегральної noise power потрібні окремі ENBW/calibration правила. Нуль має скінченний floor−300dBFS; no-data має `null`, а не floor.

## Обов'язкові no-data маски

| Абсолютна частота | Generic survey/NPU результат |
|---|---|
| 3…30 kHz | no-data |
| 225…400 MHz | no-data |
| 406.0…406.1 MHz, Cospas-Sarsat | no-data |
| 1530…1660 MHz, private/MSS (включно з Cospas-Sarsat 1544.0…1545.0 MHz) | no-data |

Обидві межі включені. Маскується кожний бін, чия **повна ширина** `center+relative ± sample_rate/(2N)`, розширена на захисну смугу `GUARD_BINS=8` бінів з кожного боку, торкається діапазону, навіть коли сам центр біна ще зовні. Перший even-FFT Nyquist-бін має також wrapped half-bin на верхній межі capture; ця частина теж перевіряється з тією самою смугою. Реальний RF-сигнал у complex baseband з'являється і на `-f`, тому коли capture перетинає 0 Hz (HF+ від 9 kHz, RTL від 500 kHz), маскуються й біни з від'ємною абсолютною частотою, чий модуль торкається діапазону.

Захисна смуга прибирає головну пелюстку й ближні бічні пелюстки periodic Hann від потужного випромінювача біля межі: тон −0.9 dBFS усередині 225 MHz давав −19 dBFS у сусідньому valid біні, тепер найближчий valid бін ≈ −70 dBFS. Залишкові дальні бічні пелюстки, циклічний leakage через протилежний край capture, aliasing сигналів поза capture та IMD приймача маска не усуває. Маскування не змінює center/sample_rate/relative-frequency coverage SDR: воно прибирає значення відповідних bins. `valid=False` завжди відповідає `power_dbfs=None`.

Маскування бінів — лише шар `srrx.spectrum`. Засувка сеансу `ScopeLatch` ([SCOPE-POLICY](SCOPE-POLICY.md); HMI-сеанс і `labrx.run_capture(..., scope=…)`) відхиляє як «out of scope» **усю** налаштовану смугу, що торкається замаскованого діапазону, зокрема 406.0–406.1 MHz, а не лише її біни. Тому захоплення радіозондів тримають `400.0 MHz < center − rate/2` і `center + rate/2 < 406.0 MHz` (скан 400.0–405.9 MHz, STACK.md:600; 225–400 MHz теж замасковано); CLI `python -m srrx.labrx` засувки не створює, і там діє тільки маска бінів.

Це проєктні межі даних для generic survey/annotation/training. API не декодує повідомлень, не надає каналів приватного вмісту і не створює журналів GNSS/окремих емітерів. Координати, raw samples, emitter IDs або довільні annotations не можна додати до spectrum frame як extra metadata.

## Маска голосу для сирого IQ (`srrx.voice_mask`, selftest RX-14)

Шар для майбутнього вузького записувача проходів (STACK.md:977; записувача ще немає,
підключення — пункт IQ-1). Модуль нічого не пише, не демодулює й не класифікує.
Планування частот працює на чистому Python, фільтр потребує NumPy (без нього —
`VoiceMaskDependencyError`, без фіктивного запасного шляху).

- `plan_windows(plan, transmitters)` — вікна алоу-листа з плану `srrx.passes` з
  перевіреним UTC (`time_verified=true`, інакше відмова): для кожного проходу NORAD id
  з алоу-листа даних — AOS−60 s … LOS+60 s і низхідна ± (смуга/2 + Доплер LEO при
  7 km/s + 20 kHz), як у вікні LRPT STACK.md:977. Режим не з `DATA_MODES` (FM, SSB,
  голос) і низхідна в смузі голосу поза аматорськими супутниковими ділянками
  145.8–146 і 435–438 MHz відхиляються. `active_windows(windows, utc_s)` дає смуги,
  чинні в момент запису.
- `bin_keep(center, rate, n, windows, bench=False)` — дозвіл запису кожного біна (порядок
  fftshift, бін оцінюється на всю ширину, як у масках вище). Бін пишеться лише всередині
  вікна або в явному стендовому/кондуктивному захопленні (`bench=True`). Завжди
  вирізаються: статичні маски голосу 437.800 MHz (ретранслятор МКС), 436.795 MHz (SO-50)
  і 145.800 MHz (ARISS) ±8 kHz — також усередині вікна; смуги голосу `VOICE_BANDS_HZ`
  поза вікном; смуги `srrx.spectrum.MASKED_BANDS_HZ` (також дзеркально нижче 0 Hz). Вікно повертає бін смуги голосу лише в аматорській супутниковій ділянці, тож
  PMR446, сухопутна рухома служба, морський VHF і авіація не відкриваються жодним вікном.
  Виняток вікон ARISS SSTV зі STACK.md:977 (slowrxd наживо) не реалізовано, тому маска
  145.800 MHz діє й там.
- `excise(samples, center, rate, windows, bench=False)` і потоковий `VoiceExcisor` — FFT
  overlap-save. Множник — FFT лінійно-фазового FIR (1023 відводи, вікно Кайзера β=10),
  складеного з відрізків дозволених бінів після звуження на ширину переходу. Тому
  overlap-save — точна лінійна згортка, а кожна вирізана смуга лежить у смузі
  затримання. Конструктор перевіряє відгук на кожному вирізаному біні (≤ −80 dB) і
  інакше відмовляє (`FILTER_STOPBAND_NOT_MET`). Затримка — 511 відліків; `excise`
  її компенсує.

| смуга голосу | MHz | джерело меж |
|---|---|---|
| аматорська 2 m | 144.000–146.000 | STACK.md:977 |
| аматорська 70 cm | 430.000–440.000 | STACK.md:977 |
| PMR446 | 446.000–446.200 | STACK.md:977, ECC/DEC/(15)05 |
| авіаційна (R) | 117.975–137.000 | STACK.md:977 (118–137), край ITU RR ст. 5 |
| морська VHF | 156.000–162.050 | ITU RR дод. 18, розширено назовні — DRAFT |
| сухопутна рухома | 26.960–27.410 (CB), 68.0–87.5, 146–174, 406.1–430, 440–470 | регіональна таблиця CEPT — DRAFT |

Межі DRAFT перевіряє рецензент політики разом з `receive-only-policy.json`
(статус DRAFT); регіональний профіль може розширити смуги, але не звузити. Ризик для
рецензента: статичні маски можуть зачепити сусідні аматорські супутникові низхідні
даних біля 437 MHz.

Відкриті питання рецензенту: цих виділень із голосом у `VOICE_BANDS_HZ` немає, а
стендове захоплення (`bench=True`) їх запише. Розширення списку — дозволений напрямок.

- 108–117.975 MHz: VOR з ATIS (AM-голос).
- Сухопутна рухома служба нижче 68 MHz (регіональні виділення).
- Низхідні рухомої служби IMT у межах RTL/Lime, зокрема 790–960 і 1805–1880 MHz
  (цифрові, але несуть голос).
- Інші FM-ділянки аматорів: 29.6 MHz (10 m), 51 MHz (6 m), 1240–1300 MHz (23 cm).
- Голосові смуги КХ нижче 30 MHz (аматорський SSB, морський і авіаційний КХ-зв'язок)
  для стендового захоплення HF+.

Перевірки: `software/tests/test_voice_mask.py` (правила бінів, вікна
плану, синтетичний NFM на 145.500/145.800/433.500/446.006 MHz, LRPT у вікні, потокова
обробка, відмова фільтра й відсутність NumPy) і рядок selftest RX-14
([DEPLOYMENT](DEPLOYMENT.md#офлайн-самоперевірка-лише-прийом-і-приватності)). Запис проходу з
голосом ретранслятора на пристрої (ПОЛ-05) лишається відкритим.

## Межа пам'яті

`SampleRing` ліниво зберігає owned complex64 chunks,8bytes/sample; default capacity8MiB, дозволена верхня межа4GiB. Capacity має бути integer, кратний8; ring для processor мусить вміщати щонайменше N samples. Вказати4GiB не означає виділити4GiB одразу. Найстаріші samples витісняються. Array views, що тримають велике старе backing allocation, не залишаються; власні chunks копіюються та очищуються при clear/eviction.

Кількість chunks теж обмежено8192, щоб нескінченні append по одному sample не створили необмежений metadata overhead. За дуже дрібних chunks history може витіснятися раніше за byte-capacity. `allocated_bytes` — фактично retained IQ payload, `chunk_count` — кількість chunks. Поточний conversion chunk і FFT/window/result arrays — додаткова обмежена робоча пам'ять; byte-capacity не є лімітом усього Python process. Caller-owned input не входить у цей buffer limit. Module не створює IQ-файлів/memmap; OS swap/core-dump policy належить розгортанню.

## Перевірки

```sh
PYTHONPATH=software python -m unittest discover -s software/tests -p test_spectrum.py -v
```

**28 тестів PASS**: справжні positive/negative tones і dBFS, finite zero floor, часткові/порожні блоки, retune/source flush, усі маски, включені межі з захисною смугою, обов'язкові смуги Cospas-Sarsat 406.0–406.1 MHz і 1544–1545 MHz (маска бінів кадру 2 MS/s біля 405.5 MHz лишає 405.9 MHz валідним; такий захват із засувкою сеансу відхиляється цілком, див. вище), Nyquist wrap, дзеркало від'ємних частот біля 0 Hz, leakage потужного тона біля межі, forged `valid`, підмінений grid, NaN/Inf/extra fields, remasking перед JSONL, відсутність IQ persistence calls, точне витіснення/owned copies, bounded chunk metadata та lazy4GiB validation. Тести не доводять калібрування приймача або натурні RF-вимірювання.

Первинна документація NumPy: [fft](https://numpy.org/doc/stable/reference/generated/numpy.fft.fft.html), [fftshift](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftshift.html), [Hann/hanning](https://numpy.org/doc/stable/reference/generated/numpy.hanning.html). Implementation використовує базові API без версійних `out=` оптимізацій; відсутність dependency перевірено окремо.
