# Навчання за розміченими спектральними фрагментами

`srrx.learning` навчає nearest-centroid classifier на явно розмічених користувачем прикладах. Він працює на CPU без NumPy. Це класифікація форми спектра: модуль не декодує сигнал, не встановлює особу передавача та не керує живленням або GPIO.

Допустимі мітки:

| Мітка | Значення для розмітки |
|---|---|
| `unknown_energy` | Невідома спектральна енергія. Це також зарезервований результат OOD: таку розмітку можна зберегти, але вона не навчається як клас |
| `analog_broadcast` | Приклад аналогового мовлення, підтверджений користувачем |
| `digital_broadcast` | Приклад цифрового мовлення, підтверджений користувачем |
| `weather_satellite` | Приклад метеосупутникового прийому |
| `amateur_digital` | Приклад аматорського цифрового прийому |
| `voice_spectrogram` | Користувацька мітка спектральної форми голосового сигналу, без запису мовного вмісту |

Інші мітки відхиляються. Немає класів військових сигналів, radar, drone/FPV/RC, EW, ідентифікації передавачів або приватного змісту. У JSON немає вільного тексту, місцезнаходження, ідентифікатора передавача чи декодованого payload. Вхід допускає лише поля `SpectrumFrame` версії 1. Додаткові поля, зокрема IQ/GNSS/location/payload, відхиляє спільний валідатор.

## Робочий запуск

З кореня репозиторію:

```sh
PYTHONPATH=software python -m srrx.learning demo --output /tmp/srrx-learning-demo
PYTHONPATH=software python -m srrx.learning train --dataset /tmp/srrx-learning-demo/annotations.json --model /tmp/srrx-learning-demo/retrained.json --seed 7
PYTHONPATH=software python -m srrx.learning infer --model /tmp/srrx-learning-demo/retrained.json --frame /tmp/srrx-learning-demo/example-spectrum.json --start 0 --end 256 --backend npu
```

`demo` створює 12 **синтетичних** прикладів трьох класів, справді навчає модель, перевіряє відкладені capture groups і класифікує окремий синтетичний приклад. Демо не є доказом розпізнавання реальних радіопротоколів. За відсутності NPU остання команда явно повертає `backend: "CPU"`, `npu.available: false` та причину.

Розмітка свого canonical spectrum JSON:

```sh
PYTHONPATH=software python -m srrx.learning annotate --dataset ./annotations.json --frame ./spectrum.json --start 32 --end 160 --label amateur_digital --group 19523f8b-3dfe-4e95-afca-470986f60174 --user-confirmed
```

Для нової незалежної сесії збирання створюють новий випадковий UUID. Усі приклади з тієї самої сесії повинні отримати **той самий** UUID. Це анонімна група збирання для розділення train/validation; її не слід прив’язувати до передавача. У датасеті зберігається SHA256 цього UUID. Один кадр не можна рознести в різні групи.

## Дані й точні межі

- Один annotation box — послідовні frequency bins **одного** спектрального кадру: `start_bin` включно, `end_bin` виключно. Розмір від 8 до 4096 bins. Це не часова область waterfall.
- Кожний bin усередині box має бути валідним. Box із хоча б одним masked/invalid/null bin відхиляється цілком.
- `mask_frame()` повторно застосовується перед annotation, feature extraction, перевіркою збереженого датасету, training та inference. Обов’язкові no-data діапазони визначені в `srrx.spectrum`: 3–30 kHz, 225–400 MHz, 406.0–406.1 MHz (Cospas-Sarsat), 1530–1660 MHz включно з FFT bins, що торкаються меж. Caller-invalid bins не відновлюються. Неповний FFT не є прикладом.
- `annotate(..., scope=None)` додатково перевіряє абсолютну смугу box через `scope_policy.scope_check` (стоп замаскованої смуги — завжди). Якщо передано засувку сеансу `scope_policy.ScopeLatch`, стоп Artemis на смузі box або засувка налаштованої смуги відхиляє мітку з повідомленням `Annotation span is out of scope` без частоти; інший об'єкт замість засувки відхиляється. Правило лише додає відмову, див. [SCOPE-POLICY.md](SCOPE-POLICY.md). CLI `annotate` засувки не має, тому там діє лише стоп замаскованої смуги.
- Під час перевірки датасету кожний збережений кадр повторно маскується й порівнюється з canonical копією один раз. Boxes вирізаються з цієї вже перевіреної копії, тож вартість не множиться на кількість annotations.
- Датасет: максимум 2000 annotations та 1 048 576 сумарних bins у збережених унікальних кадрах. Один JSON-файл — максимум 64 MiB.
- Зберігаються canonical **masked power spectra**, геометрія частот для повторної перевірки маски, label/box, анонімна capture group і час явної розмітки. Raw IQ, звук, payload та координати не записуються. Canonical frames не містять додаткових метаданих.
- Повторені нормалізовані фрагменти, зокрема копії зі зміною gain, відхиляються. Перекривні boxes одного кадру також відхиляються. Перевірка не доводить незалежності близьких у часі, але чисельно відмінних кадрів; правильне групування сесій потрібне від користувача.
- Збереження JSON — `fsync`, atomic `replace`, права `0600`. На POSIX після `replace` виконується `fsync` каталогу; його помилка повідомляється як `durability not confirmed`, бо файл уже замінено. Windows не має `fsync` каталогу, тому там цей крок пропускається. Перевіряються schema, числові межі, SHA256, унікальність і consistency. SHA256 виявляє зміни; це не цифровий підпис та не сертифікат походження.

## Навчання й оцінка

Потрібні щонайменше два класи та дві незалежні capture groups для кожного класу. Мало прикладів дає слабку перевірку; додаткові незалежні сесії потрібні для практичної оцінки. Група повністю належить train або validation. Класи мають залишитися в обох частинах; якщо це неможливо, training відхиляється.

`relative_shape_v1` має 36 безрозмірних ознак: 32 інтерпольовані значення нормалізованої форми та mean/occupancy/roughness/deviation. Віднімається 10-й percentile, масштаб задається різницею 90-го й 10-го percentile з мінімумом 1 dB. Абсолютна частота та абсолютний рівень не входять в ознаки. `voice_spectrogram` залишається назвою користувацького класу; один FFT не містить часових ознак мовлення.

Centroids обчислюються тільки за training annotations. Евклідова RMS-відстань порівнюється з per-class radius: `max(0.08, 1.5 × максимальна training distance)`. Якщо distance більша за radius або margin між двома найближчими класами менша за 0.1, результат — `unknown_energy`, `ood: true`.

Annotations `unknown_energy` залишаються в датасеті, але не входять у train/validation і не стають класом моделі. Інакше OOD-відхилення відкладеного прикладу `unknown_energy` рахувалося б як правильний збіг і завищувало б accuracy. Модель із класом `unknown_energy` відхиляється. Для навчання потрібні щонайменше два інші класи.

`confidence` — **евристична оцінка форми**, не калібрована ймовірність та не доказ типу протоколу. Модель може помилятися на іншому SNR, FFT, receiver, gain, bandwidth, propagation або схожій спектральній формі. Немає автоматичного виконання команд за prediction.

Модель містить dataset SHA256, точні train/validation annotation IDs і groups, seed, час fit, кількості SIMULATION/HARDWARE прикладів, centroids/radii та confusion matrix. `validation.scope` дорівнює `held_out_capture_groups_only_not_field_accuracy`. Не слід називати точність синтетичного holdout точністю польового застосування. Поле source — надане походження SpectrumFrame, не апаратний сертифікат.

## Python API

```python
from uuid import uuid4
from srrx.learning import empty_dataset, annotate, train, infer, save_dataset, save_model

dataset = empty_dataset()
dataset = annotate(dataset, frame, 32, 160, "amateur_digital",
                   group_id=uuid4(), user_confirmed=True)
# Додати інші підтверджені приклади та незалежні capture groups.
model = train(dataset, seed=7, validation_fraction=0.25)
save_dataset("annotations.json", dataset)
save_model("model.json", model)
result = infer(model, query_frame, 32, 160, backend="cpu")
```

Додаткові API: `extract_features`, `validate_dataset`, `validate_model`, `load_dataset`, `load_model`, `export_interchange`, `box_spans`. Annotation повертає новий датасет, не змінює вхідні об’єкти. `train_model` — alias `train`. `export_interchange(path, model)` зберігає той самий валідований навчений JSON; це **не** ONNX і не скомпільована QNN-модель.

Фонова задача (HMI): `validate_dataset`, `annotate`, `train` і `save_dataset` мають необов'язковий keyword-only `checkpoint=None`. Виклик `checkpoint(stage, done, total)` отримує лише назву етапу й лічильники, ніколи дані: перед перевіркою печатки, на кожен збережений кадр і анотацію, перед фінальною копією, а в `train` ще на кожен навчальний запис у проходах scope, features і holdout. Для `annotate` це не більше ніж 2 × (кадри + анотації) + 8 викликів; `save_dataset` викликає його лише до запису файлу. Результат від checkpoint не залежить. Щоб зупинити задачу, checkpoint піднімає `LearningCancelled`: це не `ValueError`/`RuntimeError`/`OSError`, тож ні CLI, ні HMI не показують його як «Rejected», а вхідні об'єкти лишаються незмінними. Затримку скасування обмежує найбільший неподільний крок: один збережений кадр або перевірка печатки й копія всього датасету. CLI checkpoint не передає. `box_spans(frame, start_bin, end_bin)` повертає RF-смуги, які перевіряє scope guard (для box від bin 0 — також загорнутий верхній пів-bin), для ранньої відмови в UI; `frame` має бути результатом `mask_frame()`, межі bins перевіряються як для анотації.

## QAIRT / QNN HTP

NPU необов’язковий. CPU path не потребує NumPy. Опціональний `QairtAdapter` потребує реального ONNX Runtime з `QNNExecutionProvider`, NumPy, відповідного HTP backend та окремо підготовленого й перевіреного ONNX artifact. Модуль не створює квантованих чи скомпільованих QNN artifacts і не заявляє їх перевірку на Q6A.

Manifest JSON має рівно такі поля:

```json
{
  "schema_version": 1,
  "kind": "srrx_qairt_htp_distances",
  "model_sha256": "SHA256_TRAINED_MODEL_FROM_MODEL_JSON",
  "feature_version": "relative_shape_v1",
  "labels": ["analog_broadcast", "digital_broadcast"],
  "artifact_path": "qualified-distance-model.onnx",
  "artifact_sha256": "SHA256_ONNX_FILE",
  "backend_path": "libQnnHtp.so",
  "backend_sha256": "SHA256_ACTUAL_HTP_LIBRARY"
}
```

Приклад містить placeholders; без справжніх файлів він не є робочим manifest. Labels і порядок мають точно збігатися з trained model. Вхід ONNX — один `float32[1,36]`; вихід — один tensor `[1,number_of_labels]` невід’ємних RMS-відстаней до відповідних centroids. Artifact і backend обмежені 1 GiB кожний та перевіряються потоковим SHA256.

Адаптер вимагає QNN HTP, забороняє CPU EP fallback, перевіряє активний provider і tensor shapes та реально викликає `session.run`. Перевірка результату допускає похибку `0.01 + 2% × CPU distance`. Host features, OOD і ця контрольна CPU-перевірка лишаються на CPU. Label, OOD, distance і confidence завжди обчислюються з точних CPU-відстаней. Біля порогу radius/margin допуск міг би змінити рішення, тому HTP-результат зараховується лише тоді, коли його відстані в межах допуску й дають ті самі `label`, `nearest_label` та `ood`. Інакше повертається CPU-результат із `npu.available: false` і причиною. Лише успішний і узгоджений виклик HTP позначається `QAIRT_QNN_HTP`. Звичайний Python callback не може позначити CPU як NPU.

`--backend npu --npu-manifest ./manifest.json` або `infer(..., backend="npu", npu_manifest=...)` за будь-якої недоступності повертає справжній CPU-результат із `npu.available: false` та причиною. Тести перевіряють цей шлях; апаратний HTP тут не тестувався.

Використано первинну документацію [ONNX Runtime QNN Execution Provider](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html): HTP backend та `session.disable_cpu_ep_fallback`. Сумісність конкретного runtime, квантованого artifact і цільового SoC треба підтвердити на обладнанні.

## Перевірка

```sh
PYTHONPATH=software python -m unittest discover -s software/tests -p 'test_learning.py' -v
```

Тести охоплюють mask bypass, стоп меж сеансу для annotation, invalid capture/geometry, дозволені класи, explicit annotation, gain-copy duplicates, overlap/capture-group leakage, реальний fit/holdout/inference/OOD, зарезервований `unknown_energy`, одне маскування на збережений кадр, atomic persistence і помилку `fsync` каталогу, пошкоджені models/JSON/provenance, чесний NPU fallback, збіг NPU-рішення з CPU та робочі CLI demo/train/infer. `CheckpointTests`: однаковий результат із checkpoint і без, порядок етапів, межа кількості викликів, `LearningCancelled` на першому, середньому й останньому виклику без зміни вхідного датасету, скасоване збереження не торкається файлу, `box_spans` збігається зі смугами scope guard.
