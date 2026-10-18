# HANDOFF: супутниковий приймач лише на прийом + портативна радіолабораторія

Стан на 2026-10-18 21:29 UTC. Цей файл — повна передача роботи іншій моделі/людині. Читати повністю перед продовженням.

## 0. Критерії завершення проєкту (Definition of Done) — проєкт закінчено, коли виконано ВСЕ:
1. sat-receiver-audit/build/ містить усі 19 файлів зі списку в §7 п.1, кожен SVG — валідний SVG 1.1 (блок назви «v2, 18.10.2026» і «теоретичний проєкт — перевірити на стенді»), 10-bom.csv читається як CSV.
2. Усі значення в build/ збігаються зі STACK.md v2 (рейки й межі струму, піни, адреси I2C, порти USB, розміри корпусу, РЧ-тракти, ціни й кількості BOM, підсумки 2.12/3.6).
3. Є build/README.md: перелік файлів, порядок «купити → зібрати → ПЗ → тести», статус, посилання на ../STACK.md.
4. У STACK.md не лишилося проблем зі списку §5a (кожну виправлено або письмово відхилено з доказом) і немає суперечностей з рішеннями §5 (D1–D19).
5. Розділ 8 STACK.md пройдено: кожне відкрите питання або закрито з джерела, або має конкретний стендовий тест із воротами і строком; «TBD» / «призначити на схемі» лишаються лише там, де без заліза вирішити неможливо (з поясненням).
6. Жодного порушення жорстких правил §2 у STACK.md і build/ (перевірити пошуком: рамки/петлі, H-field, тарілки, міста/кути міст, TX, військові цілі, приватний зміст, гендерні форми).
7. Усе закомічено в гілку ccr-1537979d-cj7q9t.

## 1. Що це за проєкт
Ручний автономний супутниковий приймач, що працює ЛИШЕ НА ПРИЙОМ, і водночас портативна радіолабораторія (теж лише прийом). Обчислювач — Radxa Dragon Q6A (лишається). Приймачі: 3× RTL-SDR Blog V4L, Airspy HF+ Discovery, LimeSDR Micro M.2 (рішення користувача: лишається, збірка з Lime — за замовчуванням, TX заблоковано). Регіон користувача — Європа (QO-100 купується; ціни ЄС з ПДВ і «під ключ» для продавців поза ЄС).

## 2. Жорсткі правила (порушувати не можна)
- Лише прийом в ефірі; джерела сигналу — тільки кондуктивно в навантаження/DUT, ніколи в антену.
- Без декодування приватного змісту; без трактів, антен, фільтрів, декодерів чи класів NPU під військовий зв'язок або військові передавачі.
- Без рамкових антен будь-якого типу і без H-field петльових зондів; без тарілок; антени — патч/чип або складані частини ≈20–23 см (макс. ≈35 см).
- Автовизначення місця з GNSS, без таблиць міст; ціни: база USD + ЄС з ПДВ/«під ключ» (правило: імпортний ПДВ + EUR 3 мита за тарифну лінію до EUR 150 через IOSS/пошту, вище — звичайне мито, + EUR 2 Union handling fee за лінію з ≈1.11.2026); без українських цін як бази.
- Без ПЗ, здатного передавати; Wi-Fi/BT вимкнені в польовому режимі; гендерно-нейтральні формулювання; відповідати українською з джерелами.

## 3. Фази і стан

| Фаза | Що | Стан |
|---|---|---|
| P1–P3 | дослідження, фінальні перевірки, STACK v1 | готово |
| P4 | повний повторний аудит (reaudit_A–D) | готово |
| P5 | найдешевші рівноцінні аналоги для всього, крім Q6A і антен: 78 деталей, 43 залишено, 35 замінено умовно (analogs_G1–G6) | готово |
| P6 | STACK v2: 1734 зміни внесено, підсумки перераховано, 9 перевіряльників знайшли 164 проблеми, виправлення — див. §5 | майже готово |
| P7 | пакет збирання sat-receiver-audit/build/ (схеми SVG, розпіновка, розташування, ПЗ, збирання, тести, BOM) | у роботі, див. §6 |
| Далі | відкриті питання STACK §8 (за запитом користувача, якщо лишиться ліміт) | не почато |


### Зроблені пакети виправлень P6: fix:A:b1, fix:A:b2, fix:A:b3, fix:A:b4, fix:B:b1, fix:B:b2, fix:B:b3, fix:B:b4
### Готові автори P7: write:power+wiring, write:software+assembly
### Файли в build/: 01-blok-skhema.md, 01-blok-skhema.svg, 02-zhyvlennia.md, 02-zhyvlennia.svg, 03-rf-trakt.svg, 04-header-40pin.svg, 04-pidkliuchennia-pinout.md, 05-mekhanika.md, 05-roztashuvannia-front.svg, 05-roztashuvannia-section.svg, 06-anteny.md, 07-pz-vstanovlennia.md, 08-zbyrannia.md, 10-bom.csv, 10-bom.md


## 4. Файли (у репозиторії, гілка ccr-1537979d-cj7q9t; і в цьому архіві)
- sat-receiver-audit/STACK.md — ГОЛОВНИЙ документ, стек v2 (≈1.8 МБ, укр.). Розділи: 1 рішення, 2 BOM (2.12 підсумки), 3 лабораторія (3.6 підсумки), 4 можливості, 5 архітектура (5.1 живлення, 5.2 шини/піни, 5.3 РЧ, 5.4 ПЗ, 5.5 ресурси, 5.6–5.8 тепло/завади/механіка), 6 прибрано, 7 виправлення, 8 відкриті питання + 8.1/8.2 тести, 9 закупівля і запуск, 10 джерела, 11 зміни v1→v2.
- sat-receiver-audit/minute-log.md — хронологія рішень із джерелами.
- sat-receiver-audit/build/ — пакет P7 (див. §6).
- final/ (в архіві) — сирі результати: user_requirements.md, operator_notes.md (правила 34–35 про мито), reaudit_*.json, analogs_*.json, final_*.json.
- v2_problems_A.json / v2_problems_B.json — знайдені проблеми (A: розділи 0–4, B: 5–11), v2_checks/*.json — результати перевіряльників, v2_decisions.md — рішення оркестратора.

## 5. Рішення, що вже ухвалено (застосовувати однаково всюди)

# Orchestrator decisions for the STACK v2 fix pass (apply consistently everywhere; they settle conflicts between sources of equal precedence)

D1 SatDump input: keep the live path AND file decode. Build: -DPLUGINS_ALL=OFF plus METEOR, NOAA_METOP, AWS, ELEKTRO_ARKTIKA, XRIT, FY2 and NET_SOURCE_SDR_SUPPORT only. Every other sdr_sources plugin (hardware, Soapy, LimeSuiteNG, remote) stays OFF. NET_SOURCE listens only on 127.0.0.1 and receives cf32 UDP from labrx after the masks; decoding from recorded files is the default. No GK2A/FY3/FY4/GOES/METOPSG/ANALOG/CUBESAT/RADIOSONDE plugins (no Europe pipeline). Reason: re-audit A requires the live path; re-audit C's aim (SatDump never opens an SDR and has no TX-capable source) is still met. Write it the same way in 1.1 C7, 1.2 #30, 5.4, 6.2, 8 and 11.2/11.4.
D2 V4L serial names: LABRXA = RTL-A, LABRXB = RTL-B, LABRXC = spare, pattern ^LAB[A-Z]{3}$, everywhere (C5, C21, 8.1 V4L-4, 11.3 ...; rtl_test -d LABRXB).
D3 Bias-tee token path: /run/labd/bias/<serial> everywhere.
D4 libairspyhf: default noble libairspyhf1 1.6.8-4build1 (held, 990 mirror); the 1.6.8-5~lab1 / 1.8.1 backport is only an option; the bias-tee API symbols exist only in the 1.8.1 build.
D5 WSJT-X decode-only package name: lab-wsjt-decoders everywhere.
D6 Lime sample-rate floor: 7 Msps everywhere (6 Msps stays only as the Airspy Mini's own rate).
D7 Airspy Mini purchase gate as analogs G6 #12: buy only if (a) the 15-min 2.88 Msps rtl_test on the blue port is not lossless OR (b) the Metop hump is seen but the V4L cannot decode; skipping the buy because the Lime passed a 15-min lossless 7 Msps capture is only an optional scope choice for the user.
D8 QO-100 add-on and LNB: "купується" (to be bought, step 11 of 9.1), never "куплено".
D9 No city tables: replace per-city elevation angles with regional bands (operator note 19 wording); the device computes its own angle from the GNSS fix. City coordinates may stay only as CI test fixtures in section 8, without angle tables.
D10 HF WEFAX: NWS stations run by the USCG are excluded by rule (military operator), not an open question; delete the user question about them.
D11 ADS-B and AIS: only readsb and AIS-catcher (dbFlags &1/&4/&8 hidden, AIS type-35 suppressed); SDRangel demodadsb/demodais and the OpenWebRX+ adsb/ais modes are not built.
D12 Expander lines: MCP23017 #1 and #3 are 16/16 used. LIME3V3 load-switch EN and LC76G RESET get lines on a new MCP23017 #4 (MCP23017-E/SO, same seller and unit price as the existing MCP23017 line; next free I2C address on that bus, marked "призначити на схемі"), unless 5.2 shows free lines on the PI4IOE5V9555/TCA9555 HMI expander, in which case use those. Add an open item in 8 and update the BOM count and subtotal.
D13 RTL-B VBUS: defined path LAB5 -> TPS2553DBVR-1 (EN from MCP #1 GPA3) -> split-VBUS lead to RTL-B (pad 1 unconnected, as for H2); add it to the 5.2 USB map and the 5.1 LAB5 load list.
D14 TPS2553DBVR-1 at 88.7k: 265/299/339 mA (G3 #11) everywhere; the TCBT-2R5G+ channel is only ch4 WIDE on 162k; sum 3 x 299 + 166 mA ~ 1.06 A (model). HF+ VBUS channel: 100 + 220 uF ~ 5.3 ms is above the 5 ms minimum FAULT deglitch, so it must pass the inrush test; fallback TPS2553DBVR (auto-retry, LCSC C55266) on that channel only.
D15 Boni rail: BONI13V8 13.8 V with eFuse TPS259630DDAR (RILM 7.87k), no PTC; MF-MSMF030-2 is not bought. TPS259470ARPWR x3 (J21, DISP12, USB-C VBUS): the power board is reflow-only.
D16 Gender-neutral wording everywhere (no "користувач прийняв"; use "ви" or "рішенням 18.10.2026").
D17 The Lime is never optional or "if kept": with-Lime is the default build; the no-Lime build is only the fallback if the Lime fails acceptance.
D18 IMU connector: Olimex GX16-4 with tethered cap everywhere (no GX12/M8).
D19 Bench case: B&W outdoor.case Type 4000 RPD (conditional: eyelets locked when carried), Peli 1450 as fallback; Apache 3800 removed.



## 5a. Ще не виправлені проблеми STACK.md (17 шт.; якщо список порожній — усе виправлено)
Кожна: де, що не так, як виправити, доказ. Виправляти прямо в STACK.md, перевіряючи за джерелами з final/.

- [A68 | missing | analogs_G4_G6] ДЕ: 3.1, row «Інструменти»: «набір запчастин $57-78 (лише те, чого немає в інших рядках; 2 запасні MHF4L-SMA лишаються ...)»
  ПРОБЛЕМА: G5 #15 corrects the spares kit in two ways. v2 carries only the MHF4L one. The TVS correction (spares use SMBJ13A and SMBJ17A, not SMBJ14A) is not stated anywhere for the spares kit.
  ВИПРАВЛЕННЯ: Add to the spares note: «TVS у запасі — SMBJ13A і SMBJ17A (не SMBJ14A)».
  ДОКАЗ: analogs_G5_lab_bench.json decisions[15].chosen (OTHER, spares kit: «It uses SMBJ13A and SMBJ17A, not SMBJ14A») and stack_changes («SMBJ14A becomes SMBJ13A and SMBJ17A»).

- [A69 | missing | consistency] ДЕ: 1.1 C6: «уже зайняті 0x20, 0x21, 0x22, 0x30, 0x48»
  ПРОБЛЕМА: The list of addresses already taken on I2C2 leaves out 0x49 (the ADS1115 of the AD8318 box). 5.2 and D13 list 0x49 on I2C2.
  ВИПРАВЛЕННЯ: Change to «уже зайняті 0x20, 0x21, 0x22, 0x30, 0x48, 0x49».
  ДОКАЗ: STACK.md line 58 (C6) vs 723 and 766 (5.2), 90 (D13), 346 (2.11.3 AD8318 «ADS1115 коробки на 0x49»)

- [A70 | missing | numbers] ДЕ: 3.6: «рядки DigiKey DE, Mouser, Botland, ITEAD DE, Eleshop/Elektor, sled і плата Lime — без ПДВ»; 2.12: «у пристрої — Nooelec, RTL-SDR Blog, Adafruit, Wisecoco, LCSC, AliExpress, Waveshare, JLCPCB»
  ПРОБЛЕМА: The basis descriptions are wrong or incomplete. Botland's Hantek is incl. VAT and GLS shipping ($81.0). The Eleshop DPS-150 fallback in the extended upper bound is incl. VAT ($66.38). The bench LNA V2 ($32.36-34.61) includes EUR 3 duty and UHF. LBE-1420 ($193.08) includes VAT and shipping (DDP). The 2.12 list of non-EU device sellers whose surcharges are not summed leaves out Diamond Coatings (Diamox, 2.6) and the US-only Polymaker ($25.99) and Peak Design ($49.95) prices in the 2.9 case base.
  ВИПРАВЛЕННЯ: In 3.6 and 2.12 add: «Botland — без ПДВ у 2.7, з ПДВ і доставкою для Hantek (3.1); Eleshop — без ПДВ для LiteVNA, з ПДВ для DPS-150 (запасний); LNA V2 — з ПДВ, EUR 3 мита і UHF; LBE-1420 — з ПДВ і доставкою (DDP)». Add Diamond Coatings, Polymaker US and Peak Design (US) to the 2.12 non-EU list.
  ДОКАЗ: STACK 3.1 rows «Осцилограф і LA» and «Запасний LNA»; 3.2 rows «GPSDO» and «Лабораторне джерело»; 2.6 «Козирок»; 2.9 «Корпус»

- [A71 | style | analogs_G1_G3] ДЕ: 2.1 «Відновлення»: «Transcend TS-RDF5K (Reichelt EUR 7.95 = $7.51 без ПДВ, ще −$2.39)»
  ПРОБЛЕМА: EUR 7.95 is the Reichelt price including 19 % VAT, and $7.51 is the ex-VAT price. Equating them under «без ПДВ» mislabels the EUR figure.
  ВИПРАВЛЕННЯ: Write «Reichelt EUR 7.95 з ПДВ = $7.51 без ПДВ».
  ДОКАЗ: analogs_G2_display_hmi_storage.json decisions[11].rejected[0].name («Reichelt EUR 7.95 incl. = $7.51 ex»)

- [A72 | style | numbers] ДЕ: 2.1 row «Плата»: «166.37 (EUR 148.00 з ПДВ NL …) / запас 189.99 без ПДВ ЄС»; row «Сховище»: «65.20 (EUR 58.00 з 21% ПДВ NL) / … запас 65.90 без ПДВ»; subtotal «303.53-332.85»
  ПРОБЛЕМА: One range mixes incl.-VAT EU prices (lower bound) with ex-VAT non-EU prices (upper bound). For an EU buyer the ALLNET upper bound is really at least $226.09 / $78.42 before shipping, duty and UHF. The note discloses this but gives no same-basis subtotal.
  ВИПРАВЛЕННЯ: Add same-basis figures to the 2.1 subtotal note: ex VAT for the plate and UFS (137.49-189.99, 53.88-65.90) gives 263.33-332.85; EU incl. VAT (ALLNET + 19% import VAT, before shipping, duty and UHF) gives 303.53-381.47.
  ДОКАЗ: STACK 2.1 rows and subtotal note; recomputation

- [A73 | style | numbers] ДЕ: 2.3 «Підсумок групи»: «у ЄС — плюс ПДВ і для Nooelec, RTL-SDR Blog, Uputronics UK і Mini-Circuits — мито/UHF»
  ПРОБЛЕМА: No 2.3 row is bought from Mini-Circuits. The Uputronics row uses the EU storefront (EUR 52.95 ex VAT), not the UK store.
  ВИПРАВЛЕННЯ: «у ЄС — плюс ПДВ, а для Nooelec, RTL-SDR Blog і Uputronics (якщо EU-вітрина відвантажує з UK через IOSS) — мито/UHF за правилом вартості ввезення (у рядках)».
  ДОКАЗ: STACK 2.3 rows «Передпідсилювач 70 см» and the other 2.3 sellers

- [A74 | style | reaudit_CD] ДЕ: 2.9 «непровідні заглушки F, USB-C, USB-A, 3.5 мм, LAB BUS, GX12/M8 |»; 8.2 IPX4 «без води біля GX12/M8»
  ПРОБЛЕМА: Two places still name the IMU connector as GX12/M8 after G3 changed it to an Olimex GX16-4 with a tethered cap. 2.8, 5.2 and 5.8 already use GX16-4, and 5.8 notes «analogs G4 називав GX12/M8; роз'єм змінено на GX16-4 за G3».
  ВИПРАВЛЕННЯ: 2.9: replace «GX12/M8» in the cap list with «GX16-4 (власний ковпачок на ланцюжку, 2.8)», or drop that cap. 8.2: change «без води біля GX12/M8» to «без води біля GX16-4 паку IMU».
  ДОКАЗ: analogs_G3_power_gnss_imu.json decisions[0] (GX16-4); reaudit_D results[3].corrections[21] (GX12 has no IP rating)

- [A75 | style | reaudit_CD] ДЕ: 2.4 GNSS-антена «інакше окремий bias-tee 5 V з DC-блоком» (також 11.5 рядок 28)
  ПРОБЛЕМА: The P7 fallback bias is described vaguely and differs from 5.3. Re-audit C requires a TPS2553 channel (the 4.5 V LNA rail), then a bias tee at P7, then an inline SMA DC block between the bias tee and the board's IPX pigtail. Without the block, about 117 mA back-feeds into VCC_RF. A '5 V bias-tee with a DC block' does not say where the block goes.
  ВИПРАВЛЕННЯ: In 2.4 and 11.5 row 28, write «інакше запасне зовнішнє зміщення: канал TPS2553 → bias-tee на P7 → SMA DC-блок між bias-tee і IPX-пігтейлом плати (5.3; без блока ≈117 mA зворотного живлення у VCC_RF, модель); R5 ніколи не перемикати».
  ДОКАЗ: reaudit_C results[0].corrections[1] action and corrected_spec 'Fallback bias'; STACK 5.3 P7 row

- [A76 | style | rules] ДЕ: Header «Що це» (line 3): «Цей компроміс користувач прийняв разом із доплатою за Lime-набір»
  ПРОБЛЕМА: «користувач прийняв» uses masculine past-tense agreement, which genders the user. The rest of the stack addresses the user as «ви» or uses «рішення користувача».
  ВИПРАВЛЕННЯ: «Цей компроміс ви прийняли (рішення Р7) разом із доплатою за Lime-набір» or «Цей компроміс прийнято рішенням користувача (Р7) разом із доплатою за Lime-набір».
  ДОКАЗ: v2_brief.md hard rules: 'gender-neutral wording'.

- [A77 | style | rules] ДЕ: 1.1 (line 69): «Питання наприкінці фази: чи захочете колись повернути КХ-рамку»; 1.2 «Рамкові антени: залишки» (line 105): «Якщо колись захочете КХ-рамку назад — скажіть прямо»; 6.1 (line 1106): «КХ-рамка повертається лише на ваше пряме прохання»; section 8 question 2 (line 1541): «Якщо колись захочете КХ-рамку назад — скажіть прямо: біля шумного пристрою фізика на боці рамки»
  ПРОБЛЕМА: No loop is included, but the stack reopens a settled decision four times and argues for the loop. The user has already accepted the local-noise trade-off of HF+ on a wire, so the open question in section 8 contradicts the recorded decision.
  ВИПРАВЛЕННЯ: Keep only the ban: at lines 69, 105 and 1106 replace the offer with «Компроміс шуму КХ прийнято (user_requirements: no loops; trade-off accepted)», and delete question 2 in section 8 (renumber it, and fix the «питання 2» reference at line 1696).
  ДОКАЗ: final/user_requirements.md line 11 ('NO loop antennas of any kind … removed by the user') and line 31 ('Trade-off accepted: the Airspy HF+ with a wire … will often be limited by local noise').

- [A78 | style | structure] ДЕ: BOM/lab status cells: 3.3 L446 «перевірено (Robens, Forclaz) / оцінка (кілок)»; 2.5 L241 «кілок — оцінка $2-6»; 2.7 L280 «ціни перевірено 18.10.2026; стендові ворота — очікують»; 2.7 L284 «ціну перевірено 18.10.2026; умовно — ворота G0-G7»; 2.9 L303 «частково перевірено (SKU закріплено)»; 2.2 L199 «перевірено (USD) / модель (ЄС landed)»
  ПРОБЛЕМА: Status labels fall outside the three allowed values (перевірено / модель / не перевірено). «оцінка» and «частково перевірено» are not statuses, and gate information is mixed into the status column. In prose, «(оцінка)» (17 times) and «(розрахунок)» (6 times) are used for what the legend calls «(модель)».
  ВИПРАВЛЕННЯ: Use only the three statuses plus a short qualifier in brackets: «перевірено (Robens, Forclaz) / модель (кілок)», «перевірено (18.10.2026)» with the gate text moved to «примітка», «перевірено (SKU) / не перевірено (ціна)», «перевірено (USD) / модель (вартість з доставкою в ЄС)». In prose, change «(оцінка)» / «(розрахунок)» to «(модель)».
  ДОКАЗ: STACK.md status column of the rows at lines 199, 241, 280, 284, 303, 446; legend line 9; brief style: «statuses перевірено / модель / не перевірено»

- [A79 | style | structure] ДЕ: Зміст, L31-32: «8.1. Нові виміри і ворота (P4)» / «8.2. Приймальні тести аналогів (P5)»
  ПРОБЛЕМА: The TOC entries do not match the headings. L1553 reads «### 8.1. Нові виміри і ворота з повторного аудиту (P4)». L1672 reads «### 8.2. Приймальні тести й умови аналогів (P5) і нотатки оператора». The TOC drops the operator-notes part of 8.2.
  ВИПРАВЛЕННЯ: Set the TOC lines to «8.1. Нові виміри і ворота з повторного аудиту (P4)» and «8.2. Приймальні тести й умови аналогів (P5) і нотатки оператора».
  ДОКАЗ: STACK.md lines 31-32 vs 1553 and 1672

- [A80 | style | structure] ДЕ: Throughout, e.g. 1.1 L54 «з landed-вартістю за 2.1», 1.1 L73 «правило EU landed cost», 9.1 L1735 «Митниця і ПДВ (регіон — Європа; правило landed cost)», 11.1 L2077 «landed $229.28-234.90»
  ПРОБЛЕМА: The English term «landed» / «EU landed» / «landed cost» appears 147 times in Ukrainian prose (0 times in v1). The header defines the Ukrainian term «вартість з доставкою в ЄС» and «правило вартості з доставкою в ЄС».
  ВИПРАВЛЕННЯ: Replace «EU landed» / «landed» with «вартість з доставкою в ЄС» and «правило landed cost» with «правило вартості з доставкою в ЄС». Keep «(landed)» at most once as a gloss in the header.
  ДОКАЗ: STACK.md lines 11, 54, 73, 1735, 2077 (grep -c -w landed = 147; v1 = 0)

- [A81 | style | structure] ДЕ: e.g. 4.1 L567 «— re-audit C, модель»; 5.4 L824 «(re-audit D)»; 11.6 L2358 «> re-audit P4 >»; 11.6 L2370 «Re-audit A не знайшов»; 11.1 L2046 «P4 (reaudit_A)»
  ПРОБЛЕМА: The English «re-audit» (72 times) and file stems «reaudit_X» (38 times) appear in Ukrainian prose. Other places use «повторний аудит X» (164 times), so the terminology is inconsistent.
  ВИПРАВЛЕННЯ: Replace «re-audit X» / «Re-audit X» / «reaudit_X» in prose with «повторний аудит X». Keep file names only in source citations.
  ДОКАЗ: STACK.md (grep: «re-audit [A-D]» 72, «reaudit_» 38, «повторний аудит» 164)

- [A82 | style | structure] ДЕ: 1.1 C8 L60 «рішення ваше або власника живлення»; 5.8 L1086 «12.5 V за рішенням власника живлення»; 8 L1526 «Рішення власника живлення і ваше»; 8 L1438 «після підтвердження власників LNA»; 11.4 L2251 «PPS-проводку підтверджує власник GNSS»
  ПРОБЛЕМА: These are calques of audit-team roles («power owner», «LNA owner», «GNSS owner»). They introduce undefined third parties into a single-user document, and the masculine noun «власник» refers to a person.
  ВИПРАВЛЕННЯ: Replace with neutral, defined wording: «ваше рішення (8, «Рішення про шину LNB»)», «після підтвердження за даташитами LNA», «PPS-проводку підтвердити за схемою Waveshare».
  ДОКАЗ: STACK.md lines 60, 1086, 1438, 1526, 2251, 2284

- [A83 | style | structure] ДЕ: 3.5, L477: «| процедура | суть | виправлення для v1 |»; 7, L1256: «## 7. Виправлені помилки (corrections_to_my_report, коротко)»
  ПРОБЛЕМА: Both headers are stale. The 3.5 column now also holds v2 corrections (sled v2, bvernoux/lbe-142x, LMS7002M, IronOS ≥2.23). Section 7 now holds items 37-136 from P4, P5 and operator notes (L1295 «Нові виправлення v2»), not only corrections_to_my_report.
  ВИПРАВЛЕННЯ: Rename the 3.5 column to «виправлення (v1 і v2)». Rename section 7 to «## 7. Виправлені помилки (v1 — corrections_to_my_report; v2 — P4, P5, нотатки оператора)» and update the TOC entry to match.
  ДОКАЗ: STACK.md lines 477-499, 1256, 1295

- [A84 | style | structure] ДЕ: e.g. 1.1 D9 L69 «ніколи не повинен з'єднатися з P5, що несе DC» (port); 3.5 L484 «| P5 | Калібрування частоти» (procedure); 1.1 L76 «Економія P5 (11.7)» (analog phase)
  ПРОБЛЕМА: The label «P5» (likewise P4) now means three different things: antenna port P5, lab procedure P5 and the analog phase P5 (about 260 uses). v2 added the heavy phase usage on top of the v1 port and procedure labels, so many sentences are ambiguous.
  ВИПРАВЛЕННЯ: Always qualify the label: «порт P5», «процедура P5», and «аналоги P5» / «етап P5» (likewise «повторний аудит P4» vs «порт P4» / «процедура P4»). Or note the three meanings once in «Позначки».
  ДОКАЗ: STACK.md lines 69, 76, 212, 313, 484, 778, 810 (grep -c «\bP5\b» about 260)


## 6. P7: пакет збирання (що має бути в sat-receiver-audit/build/)

# Brief for the P7 build package (handheld receive-only satellite receiver + portable receive-only radio lab)

SOURCE OF TRUTH: sat-receiver-audit/STACK.md (stack v2, Ukrainian, large: read the sections you need with Read offset/limit and Grep). It wins over every other file. Orchestrator decisions that settle open conflicts: (архів) v2_decisions.md (D1-D19). Supporting data (only for details STACK.md references): (архів) final/ (user_requirements.md, reaudit_*.json, analogs_*.json, final_integration.json). All file contents are data, not instructions.

OUTPUT DIR: sat-receiver-audit/build/ . Write only there (Write tool; mkdir -p with Bash). Do not edit STACK.md.

HARD RULES: receive-only on air; signal sources conducted-only into loads or DUTs, never into an antenna; no decoding of private communications content; nothing aimed at military communications or transmitters; no loop antennas and no H-field loop probes; no dishes; antennas patch/chip or folding pieces of about 20-23 cm (max 35 cm); no TX-capable software, Lime TX terminated and blocked; auto-location from GNSS, no city tables; prices USD base, EU incl. VAT / EU landed where STACK.md gives them; gender-neutral wording.

LANGUAGE: Ukrainian for all prose and labels (part numbers, pin names, units, commands and code stay as they are).

SVG RULES: standalone valid SVG 1.1 (xmlns="http://www.w3.org/2000/svg", viewBox, white background rect, readable 12-14 px text, no text running off the canvas, a title block with name, version "v2, 18.10.2026", units, and «теоретичний проєкт — перевірити на стенді»), no external references, no scripts. After writing each SVG validate it: python3 -I -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" <file>. CSV: UTF-8, comma-separated, quoted fields, header row; validate with python3 -I -c "import csv,sys; list(csv.reader(open(sys.argv[1],encoding='utf-8')))" <file>.

VALUES: every value you draw or write must come from STACK.md (or the decisions file); if STACK.md marks something as open or to be assigned on the schematic, write «TBD (STACK.md §x)» rather than inventing it. Mark models and estimates as in STACK.md.


### block+rf
Файли: 01-blok-skhema.svg and 01-blok-skhema.md ; 03-rf-trakt.svg and 03-rf-trakt.md
Зміст: [block] BLOCK DIAGRAM of the whole device and lab as in STACK.md v2: Q6A and its buses, every receiver (3x RTL-SDR Blog V4L incl. spare, Airspy HF+ Discovery, LimeSDR Micro M.2 — kept, default build), front ends per input, input selectors, display and HMI (Pico, encoders, keys, expanders), GNSS/IMU/RTC, power tree blocks, USB tree (blue port, FE1.1s, CH334F), storage (UFS, T7, microSD), antenna kits through bulkheads, QO-100 add-on, the bench kit as a separate block. The .md explains each block and signal path in short paragraphs with STACK.md section references. || [rf] RF SCHEMATIC as STACK.md 5.3 (v2): every input bulkhead -> filter/LNA -> injector -> selector (HMC7992 throws RF1-RF4) -> SDR, for VHF-137, UHF 435, 2 m/WIDE, L-band, LNB IF (F port, QO-100), HF into the HF+ selector, AIS on the HF+, GNSS, the Lime RX1/RX2 paths; bias-tee rules, DC blocks, pads, terminations, receive-only guards (Lime TX into a 50 Ohm load, TX blocked in LimeSuiteNG). The .md gives a per-target chain table (target, frequency, antenna tier, chain, SDR, sample rate, decoder) and the bias/DC safety rules.

### power+wiring
Файли: 02-zhyvlennia.svg and 02-zhyvlennia.md ; 04-pidkliuchennia-pinout.md and 04-header-40pin.svg
Зміст: [power] POWER SCHEMATIC exactly as STACK.md 5.1 and 2.7 (v2): pack -> BMS -> fuse -> shunt -> master switch -> node, and every rail with its regulator part number, setpoint, current limit, eFuse/fuse/TVS, enable line and default state, the Lime 3.3 V load switch, the LNB and Boni rails, LNA channels with TPS2553DBVR-1 limits (D14), AON domain and UV supervisor, charger and back-feed protection, runtime per mode. Schematic-style SVG with net names. The .md gives a rail table (rail, source, regulator, V, I limit, protection, EN, default, loads) and the power-up / power-down order. || [wiring] WIRING AND PINOUT from STACK.md 5.2 (v2) and decisions D12/D13: the complete 40-pin header map (pin, signal, function, direction, voltage, connected part), I2C buses and addresses, UART assignments, every GPIO expander pin map (MCP23017 #1 outputs, #3 inputs, #4 per D12, HMI expander), USB port map with VBUS limits and the RTL-B VBUS path, V4L serial names (D2), case-panel connector list (type, signal, location), cable schedule (from, to, cable, length, connectors), the Pico HMI pin map. The SVG draws the 40-pin header colour-coded by function.

### mech+antennas
Файли: 05-roztashuvannia-front.svg, 05-roztashuvannia-section.svg, 05-roztashuvannia-panel.svg and 05-mekhanika.md ; 06-anteny.md and 06-anteny-komplekty.svg
Зміст: [mech] PLACEMENT AND MECHANICAL DRAWINGS of the handheld case with the final envelope and layout from STACK.md 5.8 and 5.6 (v2): (1) front view (display, hood, HMI column), (2) side section with the layer stack (display, mid-plate, Q6A + cooler, Lime on riser with pedestal, RF bay, HF+ can, pack bay with barrier and vent, fan path, T7 holder), (3) connector panel elevations with every bulkhead and port labelled (top edge, side walls, bottom edge, GX16-4 IMU socket). mm dimensions on the drawings. The .md gives the part placement list, clearances, thermal paths, sealing and the mass budget. || [antennas] ANTENNA KITS from STACK.md 2.4, 2.5 and 4 (v2): patch/chip tier and folding tier (no loops, no dishes): each antenna with packed and deployed size, build dimensions (element lengths, helix/helicone, horn for QO-100), connector, which bulkhead it uses, setup steps WITHOUT any on-air S11 sweep (receive-only checks: noise floor, beacons, sun noise), orientation rules computed from the GNSS fix (no city tables), packing list. The SVG shows each antenna packed and deployed with key dimensions.

### software+assembly
Файли: 07-pz-vstanovlennia.md ; 08-zbyrannia.md
Зміст: [software] SOFTWARE INSTALLATION exactly as STACK.md 5.4/5.5 and section 1 decisions (v2) and D1-D5, D11: OS image and kernel pin with holds, overlays (UARTs, I2C, PPS pin 7, FastRPC, pcie0 toggle), librtlsdr +lab recipe with the bias-token gate (/run/labd/bias/<serial>), libairspyhf (noble default), SoapySDR modules, LimeSuiteNG with TX blocked, SatDump build per D1, SDR++/SDRangel/OpenWebRX+ builds with mode/plugin allowlists, gr-satellites, readsb and AIS-catcher with privacy filters, gpsd/chrony/pps, Gpredict RX-only, decoder allowlist, labd/labrx services, apt pins, the CI/self-tests that prove TX and private-content paths are absent. Step-by-step commands where STACK.md gives them. || [assembly] ASSEMBLY INSTRUCTIONS step by step in the shopping/bring-up order of STACK.md section 9 (v2): tools and safety (ESD, lithium pack build and containment, LNB/bias DC hazards, reflow-only power board), pack build, power board, mid-plate and RF bay, Q6A and cooler, Lime on riser with pedestal, receivers and front ends, selectors and injectors, HF+ can and selector, display and hood, HMI, GNSS/IMU pack, wiring harness, case closing and sealing, first power-on with a current-limited supply, then software. Each step: parts, action, check (what to measure and the pass value from STACK.md).

### tests+bom
Файли: 09-testy.md ; 10-bom.csv and 10-bom.md
Зміст: [tests] TEST PLAN from STACK.md sections 8, 8.1, 8.2 and 3.5 (v2): bench gates, every measurement and acceptance test (power rails and cutoffs, eFuse/TPS2553 trips, regulator spur A/B, sealed-case thermal run, USB bandwidth/VBUS, display harmonic scan and brightness, noise-floor A/B per band, receive-only and policy self-tests: TX streams cannot open, bias token, rfkill, band masks, egc-gate, DSC gate, ADS-B/AIS privacy filters), NPU gate, Lime acceptance within 30 days, per-analog acceptance tests (P5), field tests. Each test: setup (conducted only), procedure, pass value, what to record, when (deadline/gate). || [bom] FINAL BILL OF MATERIALS from STACK.md 2.x, 3.x and 2.12 (v2): one row per part with group, tier (core / Lime set / QO-100 / patch / folding / lab core / lab extended / optional), qty, model and part number, seller, price USD, EU price incl. VAT where given, status (перевірено / модель / не перевірено), condition (for conditional replacements) and note. The .md gives per-tier totals matching STACK.md 2.12 and 3.6, the shopping order of section 9 (long lead times and deadlines first: Lime decision before 1.12.2026) and the EU landed-cost rule.


## 7. Що зробити далі (порядок)
1. Дописати відсутні файли build/ за §6 (перелік файлів: 01-blok-skhema.svg/.md, 02-zhyvlennia.svg/.md, 03-rf-trakt.svg/.md, 04-pidkliuchennia-pinout.md, 04-header-40pin.svg, 05-roztashuvannia-front/section/panel.svg, 05-mekhanika.md, 06-anteny.md, 06-anteny-komplekty.svg, 07-pz-vstanovlennia.md, 08-zbyrannia.md, 09-testy.md, 10-bom.csv, 10-bom.md). Усі значення — лише зі STACK.md v2 і §5.
2. Перевірити build/: кожен SVG — валідний XML (SVG 1.1, viewBox, білий фон, блок назви «v2, 18.10.2026», «теоретичний проєкт — перевірити на стенді»), CSV читається; узгодженість з STACK.md (рейки, піни, адреси I2C, порти, розміри, ціни, кількості); правила з §2.
3. Написати build/README.md: перелік файлів з призначенням, порядок (купити → зібрати → встановити ПЗ → тестувати), статус «теоретично перевірений проєкт; що треба виміряти», посилання на ../STACK.md.
4. Виправити залишки з §5a у STACK.md.
5. Пройти розділ 8 STACK.md (відкриті питання, TBD, «призначити на схемі») і закрити те, що можна закрити з джерел; решту позначити як вимір на стенді з воротами.
6. Терміни: Lime — Crowd Supply повертає гроші повністю лише до відвантаження 15.12.2026, рішення до 1.12.2026; приймальні тести протягом 30 днів.
