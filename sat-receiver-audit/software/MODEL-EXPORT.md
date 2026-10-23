# ONNX-експорт centroid-моделі та перевірка на CPU

`srrx.model_export` створює справжній ONNX, який виконує той самий розрахунок RMS-відстаней, що й `srrx.learning`. Є float32 export, необов’язкова static INT8 QDQ quantization та перевірка фактичним ONNX Runtime. Скомпільованого QNN blob, доступного QAIRT 2.42 SDK або перевірки HTP у цьому середовищі немає.

## Встановлення окремого середовища

Основний сервіс не потребує ONNX. Для export/CPU validation потрібні NumPy, `onnx` та `onnxruntime`:

```sh
python -m venv --system-site-packages /tmp/srrx-model-tools
/tmp/srrx-model-tools/bin/python -m pip install 'onnx>=1.16,<2' 'onnxruntime>=1.18,<2'
PYTHONPATH=software /tmp/srrx-model-tools/bin/python -m srrx.model_export dependencies
```

У цій перевірці окреме середовище містило ONNX 1.23.2, ONNX Runtime 1.31.0 та NumPy 2.3.5. Доступні providers: Azure і CPU; QNN provider недоступний. За відсутності optional dependencies модуль імпортується, `--help` працює, export повертає явне повідомлення й exit code 3. Тести, що потребують справжнього runtime, позначаються skipped.

## Вимкнення телеметрії до initialization

ORT 1.31.0 містить увімкнену за замовчуванням 1DS-телеметрію. Під час інтеграційного запуску виявлено небажану спробу HTTPS-з’єднання; повторний native runtime запуск призупинено до захисту. За первинною [Microsoft Privacy.md](https://github.com/microsoft/onnxruntime/blob/main/docs/Privacy.md), також включеною у встановлений wheel, `ORT_DISABLE_TELEMETRY=1` треба встановити **до initialization**. Сам виклик `disable_telemetry_events()` після import може бути запізнілим для initialization event.

`load_ort_private()` встановлює цей opt-out до optional imports, статично перевіряє встановлені Privacy.md та наявність control string у native binary, потім імпортує ORT і негайно викликає `disable_telemetry_events()` перед будь-якими provider/session queries. Runtime, завантажений раніше поза guard, відсутній/непрацездатний API або непідтверджена підтримка opt-out блокують model tools. Наразі guard перевірено для Linux 1DS; інші платформи потребують окремого аудиту замість припущення про legacy telemetry backend.

Під час виправлення guard перевірено шістьма ізольованими fake-runtime тестами без import справжнього ORT. Повний запуск виконує root лише через offline launcher із забороненим INET/INET6; цей додатковий бар’єр не замінює pre-init opt-out. Launcher повинен використовувати `load_ort_private()`, а не прямий ORT import; тест перевіряє, що жоден модуль `srrx` чи тест не імпортує `onnxruntime` напряму. Тести з реальним ORT виконуються лише на Linux: на інших платформах guard навмисно блокує ORT, тому там вони skipped. Нові runtime/hardware результати не можна вважати перевіреними тільки через проходження fake tests.

## Формат моделі

- Вхід: `features`, **float32[1,36]**, ознаки `relative_shape_v1`, отримані через валідатор і маску `srrx.learning`.
- Вихід: `distances`, **float32[1,C]**; порядок класів точно відповідає `model.json["labels"]`.
- Формула для класу `c`: `sqrt(mean((features - centroid[c])²))`.
- ONNX opset 13, IR version 8; статична геометрія, жодних dynamic axes або external tensor files.
- Float graph: `Sub → Mul → ReduceMean → Sqrt → Unsqueeze`. Centroids з реальної навченої JSON-моделі включені в ONNX як float32 initializer.
- Metadata містить SHA256 навченої моделі, feature version, порядок labels, representation і `srrx.npu_qualified=false`.
- Максимум 4 MiB на ONNX artifact; запис атомарний із `fsync` і правами `0600`.

Це export distance graph. Виділення ознак, пошук найближчого класу, евристичний confidence та OOD-пороги залишаються в `srrx.learning` на CPU. Правила дозволених класів і частотні маски не змінені.

## Робочі команди

З кореня репозиторію:

```sh
PYTHONPATH=software /tmp/srrx-model-tools/bin/python -m srrx.learning demo --output /tmp/srrx-model-example
PYTHONPATH=software /tmp/srrx-model-tools/bin/python -m srrx.model_export float --model /tmp/srrx-model-example/model.json --dataset /tmp/srrx-model-example/annotations.json --output /tmp/srrx-model-example/centroids.onnx --report /tmp/srrx-model-example/float-report.json
PYTHONPATH=software /tmp/srrx-model-tools/bin/python -m srrx.model_export quantize --model /tmp/srrx-model-example/model.json --dataset /tmp/srrx-model-example/annotations.json --input /tmp/srrx-model-example/centroids.onnx --output /tmp/srrx-model-example/centroids.int8.onnx --report /tmp/srrx-model-example/int8-report.json --allow-simulation-calibration
PYTHONPATH=software /tmp/srrx-model-tools/bin/python -m srrx.model_export validate --model /tmp/srrx-model-example/model.json --dataset /tmp/srrx-model-example/annotations.json --artifact /tmp/srrx-model-example/centroids.int8.onnx
```

`demo` створює синтетичний набір. Прапорець `--allow-simulation-calibration` потрібний саме тому, що в ньому немає апаратних capture. Без цього явного opt-in synthetic calibration відхиляється. Прапорець не перетворює синтетичні приклади на апаратні виміри.

Export без `--dataset` створює ONNX із `cpu_validated=false`. Параметр `--dataset` запускає фактичне CPU execution та порівняння. CLI повертає code 2, якщо validation gate не пройдено; successful export сам по собі не є результатом validation.

## Calibration і holdout

Модуль перевіряє SHA256 датасету, точні annotation IDs, анонімні capture groups, class/source counts та повторно обчислює centroids із записаних training annotations. Змінені або невідповідні дані відхиляються.

Static quantization використовує **тільки training annotation IDs** з provenance. Features повторно виділяються з валідованих masked spectra; випадкові calibration arrays не підставляються. Validation IDs і groups не потрапляють до calibration reader. Сам прапорець `source=HARDWARE` у кадрі залишається заявленим походженням; це не апаратний acceptance certificate.

Викликається ONNX Runtime `quant_pre_process` зі shape inference та без graph optimization, потім `quantize_static` із MinMax calibration, `QuantFormat.QDQ`, signed `QInt8` activations/weights. Після quantization код перевіряє граф: є `QuantizeLinear`/`DequantizeLinear`, кожний zero point Q/DQ є signed INT8 initializer, а кожна квантована вага (initializer на вході `DequantizeLinear`) має тип INT8. Інакше artifact не публікується. `integer_type`, `int8_weights` і `mixed_float_ops` у report виміряні з графа, а не записані константами. Representation містить float operators між Q/DQ; це не твердження про повністю цілочисельне фізичне виконання.

Static quantization бере діапазони активацій лише з training features (MinMax). Тому `validate_cpu` додатково виконує 2 + 2×C синтетичних range probes: кути простору ознак (усі 0 і всі 1), кожний centroid і найвіддаленіший від нього кут. Це не calibration data. Для float32 distances на probes мають збігтися в межах допуску float32. QDQ поза каліброваним діапазоном насичується, тому на probes gate вимагає лише тих самих label/OOD рішень, а похибка, `range_probe_distances_within_tolerance` і `max_range_probe_distance` (фактична межа насичення) записуються в report.

Порівняння виконується через явний `CPUExecutionProvider` на **відкладених capture groups**:

| Artifact | Допустима похибка кожної distance |
|---|---|
| Float32 | `2e-6 + 2e-6 × abs(reference)` |
| INT8 QDQ | `0.01 + 0.02 × abs(reference)` — не слабше за чинний QAIRT adapter |

Додатково мають збігтися всі validation labels і OOD decisions, а також label/OOD decisions на всіх range probes. Якщо QDQ gate не проходить, quantized artifact не публікується; попередній файл output зберігається. Report містить максимальні абсолютну/відносну/нормовану похибки, RMS error, sample counts, IDs/groups, calibration provenance, versions і SHA256.

## Фактично виміряний приклад

Тестовий synthetic few-shot набір: 12 annotations, 3 класи, 9 training/calibration records і 3 незалежні validation records, 9 порівнюваних distances. Це перевірка чисельного export, не точність польового розпізнавання.

| Показник | Float32 ONNX CPU | Signed INT8 QDQ ONNX CPU |
|---|---:|---:|
| Max absolute distance error | 2.1397×10⁻⁸ | 0.00819412 |
| RMS distance error | 1.1380×10⁻⁸ | 0.00361653 |
| Max normalized error відносно gate | 0.007970 | 0.806200 |
| Label agreement | 3/3 | 3/3 |
| OOD agreement | 3/3 | 3/3 |
| Range probes: max absolute distance error | 5.0456×10⁻⁸ | 0.580624 |
| Range probes: max distance output | 0.924862 | 0.344238 (насичення) |
| Range probes: label/OOD agreement | 8/8 | 8/8 |

У QDQ max relative error дорівнює **1.0**: деякі дуже малі distances округлюються до нуля. Абсолютний gate пройдено, але confidence може змінюватися; це не калібрована ймовірність. QDQ distances у цьому прикладі насичуються приблизно на 0.344, тож значення поза held-out діапазоном не еквівалентні float32. Radius 0.08 значно нижчий за межу насичення, тому OOD-рішення на probes збереглися; runtime adapter відхиляє такі відстані через допуск, і рішення береться з CPU. Інший датасет може не пройти gate і потребуватиме іншої precision/calibration. Висновок не поширюється на весь простір сигналів або на HTP.

## Manifest і межа QAIRT

`write_qairt_manifest(model, artifact, actual_backend_path, output)` створює лише file binding, сумісний зі схемою `QairtAdapter`. Потрібні справжні наявні artifact і backend `libQnnHtp.so` або `QnnHtp.dll`: перевіряються розмір, ELF/PE header та SHA256. Відсутні, порожні й звичайні placeholder-файли відхиляються; без backend файл manifest не створюється. Header/hash не доводять ABI або працездатність SDK.

```sh
PYTHONPATH=software /tmp/srrx-model-tools/bin/python -m srrx.model_export manifest --model ./model.json --artifact ./qualified-model.onnx --backend-library /actual/sdk/lib/libQnnHtp.so --output ./qairt-manifest.json
```

Шлях у прикладі навмисно має бути замінений на фактичний SDK backend. Report завжди містить `npu_qualified=false`, `qnn_compiled=false` та `scope=file_binding_only_not_runtime_or_ABI_qualification`.

Signed INT8 QDQ тут перевірено тільки CPU runtime. Документація QNN описує окремі вимоги HTP до precision, supported ops і статичних shapes; поширені QNN configurations використовують unsigned activations. Потрібні належна target-specific quantization/conversion, QAIRT SDK, сумісний backend/SoC та фактичний запуск із забороненим CPU EP fallback. Успішний ONNX checker або CPU error gate не доводить HTP support. QNN blob/context binary не створювався; жодного HTP PASS не записано.

Python API: `dependency_status`, `export_float`, `validate_cpu`, `quantize_static_int8`, `write_qairt_manifest`. API використовує ознаки, відстані й рішення з `learning.py` без окремої копії; annotations `unknown_energy` не входять у calibration/validation так само, як у training.

## Тести

```sh
PYTHONPATH=software /tmp/srrx-model-tools/bin/python -m unittest discover -s software/tests -p 'test_model_export.py' -v
```

Перевіряються фактичний ONNX Runtime, heldout/edge distances, range probes і насичення QDQ, QDQ nodes і signed INT8 zero points/weights, відсутність прямого ORT import, split provenance, opt-in synthetic calibration, error gate, атомарна заміна, artifact/model binding, external/custom graph rejection, placeholder backend rejection та CLI. Позитивний тест manifest із реальним SDK backend позначений skipped, доки явно не задано `SRRX_QNN_HTP_LIBRARY`; він теж не заявляє апаратний запуск.

Первинні джерела: [ONNX helper API](https://onnx.ai/onnx/api/helper.html), [ONNX Runtime quantization](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html), [QNN Execution Provider](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html). Export використовує документовані helper constructors і static QDQ calibration API; сумісність HTP перевіряється окремо.
