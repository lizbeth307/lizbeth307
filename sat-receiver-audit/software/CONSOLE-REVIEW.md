# Наскрізний огляд консолі та спектрального pipeline

20 жовтня2026: додано `tests/test_console_integration.py`. **Усі7 наскрізних тестів PASS**. Окремий запуск зайняв близько52s у цьому середовищі; CLI-підпроцеси мають bounded timeouts і обмежену кількість NumPy/BLAS threads. Це реальні локальні Python-процеси й metadata-файли, без SDR, RF TX, фізичних I²C/GPIO або приймання приватного вмісту.

## Реальний виконаний workflow

1. `python -m srrx.labrx --simulate` створює synthetic IQ у RAM, виконує справжній NumPy FFT і атомарно записує canonical spectrum metadata. CLI повертає `source=SIMULATION`, `raw_iq_persisted=false`, `physical_tests_performed=false`.
2. HMI `load_spectrum` читає snapshot або останній JSONL survey frame і повторно застосовує маски; display aggregation залишає masked pixels порожніми.
3. Чотири реальні FFT frames із двох синтетичних spectral shapes передано через annotation CLI з explicit confirmation та різними anonymous capture UUID. Перший frame походить безпосередньо з labrx CLI; решта — із FFT незалежно seeded simulation inputs. Labels є навмисною тестовою розміткою форми, а не доказом визначення радіопротоколу.
4. Training CLI справді обчислює CPU nearest-centroid model, відділяє capture groups для holdout та записує модель. Датасет і модель завантажуються повторно й перевіряються.
5. Inference CLI читає новий FFT query. Запит NPU без qualified runtime чесно повертає виконаний CPU backend із `npu.available=false`; результат і model source provenance залишаються SIMULATION, HARDWARE count=0. Train/validation groups не перетинаються.

У збережених frames рівно SpectrumFrame contract; жодних IQ/audio/позицій/ідентифікаторів випромінювачів не з'являється. У model є справжні центроїди, provenance та holdout metrics; synthetic validation не названа польовою точністю.

## Перевірені межі даних

| Межа | Результат |
|---|---|
| Capture CLI на300MHz → survey JSONL → HMI → annotation | Усі bins лишаються `None/False`; plot columns порожні; annotation відхиляється |
| Forged `valid=true` і marker power у protected half-band | HMI повторно маскує; збережений датасет не містить marker; box, що перетинає private bins, відхиляється |
| `raw_iq`, GNSS position extra metadata, підмінений frequency grid або string замість valid bool | Відмова на HMI/annotation boundary |
| NaN у JSON | HMI loader відхиляє файл |
| `--hardware` без acceptance | CLI відмовляє до створення spectrum/survey artifacts |
| Справжній armed DemoTransport/ConsoleController із EN_RTLA ON | Він усе одно SIMULATION і не проходить physical ControlGuard; source factory не викликається |
| Pico session змінюється між source read і export | Capture зупиняється до запису, source закривається, запитується EN_RTLA OFF |
| Malformed nested control data/policy/pico/outputs | Чиста RuntimeError-відмова, без AttributeError traceback і без відкриття receiver |

ControlGuard лишається observer: сам не ARM/recover і не поновлює lease. Після session mismatch потрібен явний новий capture; raw samples не експортуються, якщо post-read readiness check уже не проходить. Fixture з HARDWARE-полями в guard-тесті існує лише в пам'яті й не є hardware acceptance.

## Виправлення, узгоджені під час огляду

- Root додав перевірки nested status dictionaries у `ControlGuard`, щоб malformed JSON не виходив як AttributeError. Наскрізний тест підтверджує відмову до export.
- Root переніс створення hardware source під try/finally та забезпечив branch OFF attempt навіть за source-open/source-close failures; окремі capture cleanup regressions перевірено root. Наш session-change тест додатково підтверджує cleanup на межі read→FFT/export.
- HMI-agent узгодив ReceiverSimulation/Qt input bounds із capture CLI: integer center0…6GHz, rate48k…56MHz. Попередня HMI minimum8k могла запускати child, який гарантовано відмовляв. Whole-valued Qt floats перетворюються на integer CLI arguments.

Доповнення 23 жовтня 2026 (межа HMI → learning, перевірено в `tests/test_hmi.py`):

- Явне підтвердження анотації прив'язане до кадру, показаного в момент позначки. Потоковий кадр тієї ж геометрії (SIM capture, відстежуваний survey) більше не скидає вибрані bins на `[start,256)` і не підміняє кадр, що потрапляє в датасет; зміна bins/мітки чи новий кадр іншої геометрії знімає підтвердження.
- Глибоко вкладений JSON відхиляється HMI loader як `ValueError`, а не `RecursionError`, що раніше виходила з Qt slot без повідомлення «Rejected».
- `test_console_integration.py` імпортує `srrx.labrx` (POSIX `resource`) і виконується лише на Linux; кількість наскрізних тестів не змінилася.

Доповнення 24 жовтня 2026 (APP-05): HMI запускає `learning.annotate/train/infer` і load/save датасету й моделі як одну фонову задачу з прогресом і Cancel ([HMI.md](HMI.md)); задача отримує відокремлену копію `ScopeLatch` ([SCOPE-POLICY.md](SCOPE-POLICY.md)), а датасет сеансу обмежено 2 MiB. Контракт learning для CLI і цього наскрізного сценарію не змінився: `checkpoint` необов'язковий і CLI його не передає.

Після цих виправлень у перевірених cross-module сценаріях відкритого дефекту не виявлено. Цей огляд не включає візуальну оцінку Qt на фізичному дисплеї, фізичні SDR-бібліотеки/серійні номери, hardware calibration, GP/NPU виконання чи фактичний GNSS fix. Вони не виводяться з успіху simulation pipeline.

Відтворення:

```sh
PYTHONPATH=software OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m unittest discover -s software/tests -p test_console_integration.py -v
```

Прочитані модулі: `labrx`, `receivers`, `spectrum`, `learning`, `hmi`, `location`, `decoder_policy` та їхні контракти. Змінено лише `tests/test_console_integration.py` і цей звіт. Решту implementation fixes виконали відповідні власники модулів.
