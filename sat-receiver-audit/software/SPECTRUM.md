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
- `append_survey(path, frame) -> sanitized frame` **спершу mask, потім validate, потім JSONL write**. Воно не довіряє `valid`, не пише extra keys/raw IQ і не торкається файла для невалідної структури.

Перед UI, annotation, export, feature extraction і training споживач мусить виконати `safe = mask_frame(untrusted_frame)`. Вибрані для annotation/training bins мають бути valid; прогалини не інтерполювати й не підміняти нулями. Сам exporter також повторно застосовує цю межу.

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
| 1530…1660 MHz, private/MSS | no-data |

Обидві межі включені. Маскується кожний бін, чия **повна ширина** `center+relative ± sample_rate/(2N)` торкається діапазону, навіть коли сам центр біна ще зовні. Перший even-FFT Nyquist-бін має також wrapped half-bin на верхній межі capture; ця частина теж перевіряється. Маскування не змінює center/sample_rate/relative-frequency coverage SDR: воно прибирає значення відповідних bins. `valid=False` завжди відповідає `power_dbfs=None`.

Це проєктні межі даних для generic survey/annotation/training. API не декодує повідомлень, не надає каналів приватного вмісту і не створює журналів GNSS/окремих емітерів. Координати, raw samples, emitter IDs або довільні annotations не можна додати до spectrum frame як extra metadata.

## Межа пам'яті

`SampleRing` ліниво зберігає owned complex64 chunks,8bytes/sample; default capacity8MiB, дозволена верхня межа4GiB. Capacity має бути integer, кратний8; ring для processor мусить вміщати щонайменше N samples. Вказати4GiB не означає виділити4GiB одразу. Найстаріші samples витісняються. Array views, що тримають велике старе backing allocation, не залишаються; власні chunks копіюються та очищуються при clear/eviction.

Кількість chunks теж обмежено8192, щоб нескінченні append по одному sample не створили необмежений metadata overhead. За дуже дрібних chunks history може витіснятися раніше за byte-capacity. `allocated_bytes` — фактично retained IQ payload, `chunk_count` — кількість chunks. Поточний conversion chunk і FFT/window/result arrays — додаткова обмежена робоча пам'ять; byte-capacity не є лімітом усього Python process. Caller-owned input не входить у цей buffer limit. Module не створює IQ-файлів/memmap; OS swap/core-dump policy належить розгортанню.

## Перевірки

```sh
PYTHONPATH=software python -m unittest discover -s software/tests -p test_spectrum.py -v
```

**24 тести PASS**: справжні positive/negative tones і dBFS, finite zero floor, часткові/порожні блоки, retune/source flush, усі маски, включені межі й Nyquist wrap, forged `valid`, підмінений grid, NaN/Inf/extra fields, remasking перед JSONL, відсутність IQ persistence calls, точне витіснення/owned copies, bounded chunk metadata та lazy4GiB validation. Тести не доводять калібрування приймача або натурні RF-вимірювання.

Первинна документація NumPy: [fft](https://numpy.org/doc/stable/reference/generated/numpy.fft.fft.html), [fftshift](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftshift.html), [Hann/hanning](https://numpy.org/doc/stable/reference/generated/numpy.hanning.html). Implementation використовує базові API без версійних `out=` оптимізацій; відсутність dependency перевірено окремо.
