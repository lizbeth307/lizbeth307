# SIMULATION-only model artifacts

Ці файли справді створено `srrx.learning` і `srrx.model_export` та виконано в ONNX Runtime CPU. Це маленький синтетичний приклад перевірки pipeline, а не навчена на ефірі модель або QNN/HTP artifact. Calibration: 9 SIM training examples; validation: 3 інші capture groups. Координат, raw IQ чи decoder payloads немає.

`centroids.onnx` — float32, `centroids.int8.onnx` — signed INT8 QDQ зі змішаними float operations. Float max absolute error2.14e-8; QDQ0.008194, labels/OOD3/3. Відносна похибка QDQ біля нульових відстаней досягає1.0; повний звіт збережено. Ці цифри не є польовою точністю.

Оригінальні reports збережено побайтово, тому поле artifact містить тимчасовий шлях генерації. SHA256 відповідає сусіднім скопійованим ONNX-файлам. `model.json` та `annotations.json` дозволяють повторити export/validation за [MODEL-EXPORT](../../MODEL-EXPORT.md).

Жодного compiled QNN blob, прийнятої HTP-бібліотеки або hardware-enabled manifest тут немає.
