# HANDOFF: супутниковий приймач лише на прийом + портативна радіолабораторія

Стан на 2026-10-18 21:21 UTC. Цей файл — повна передача роботи іншій моделі/людині. Читати повністю перед продовженням.

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


### Зроблені пакети виправлень P6: fix:A:b1, fix:A:b2, fix:A:b3, fix:B:b1, fix:B:b2, fix:B:b3, fix:B:b4
### Готові автори P7: ще жоден
### Файли в build/: 02-zhyvlennia.svg, 05-mekhanika.md, 07-pz-vstanovlennia.md


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



## 5a. Ще не виправлені проблеми STACK.md (34 шт.; якщо список порожній — усе виправлено)
Кожна: де, що не так, як виправити, доказ. Виправляти прямо в STACK.md, перевіряючи за джерелами з final/.

- [A51 | contradiction | reaudit_AB] ДЕ: 1.2 #102 «RG6 з компресійними F-роз'ємами»; 9.1 step 11 «деталі F/75 Ohm, RG6 з компресійними F, LC»; 11.4 row 20 «(RG6 з компресійними F-роз'ємами)»
  ПРОБЛЕМА: The chosen LNB lead is the Goobay 58814 (75 Ohm, moulded F on both ends, class A+, 5.4 mm) in 2.10, 5.3 and the 9.1 Reichelt order. These rows still specify an RG6 lead with compression F connectors, a different and thicker part.
  ВИПРАВЛЕННЯ: Replace «RG6 з компресійними F-роз'ємами» with «Goobay 58814 (75 Ohm, F-F, клас A+, 1 м; 2.10)» in 1.2 #102, 9.1 step 11 and 11.4 row 20.
  ДОКАЗ: analogs_G1_receivers_rf.json cable-set decision (Goobay 58814 picked; the RG6-class 'Good Connections' candidate rejected). reaudit_B_receivers_rf.json results[3].corrections[9]: 'Keep double-shielded 75 Ohm coax and tight F connectors' (no RG6). v2_edit_notes 05b b2: 'RG6 with compression F part on

- [A52 | contradiction | reaudit_AB] ДЕ: 1.1 C24 «(Lime залишено, QO-100 куплено)»; 5.3 «QO-100 NB (Європа, кут місця 12-46°; LNB куплено)»; 6.2 «надбудову QO-100 куплено»; 8 «Додаток QO-100 (куплено) і Lime уже входять у збірку»; 11 intro «QO-100 куплено»; 11.4 row 18; 11.6 row 39
  ПРОБЛЕМА: BOM 2.4 and 2.11.2 say «Європа: купується», and 9.1 step 11 still schedules the purchase (2× Bullseye BE01 from Passion Radio). Other sections say the add-on is already bought.
  ВИПРАВЛЕННЯ: Use «купується (входить у збірку)» in all listed places. Or, if it really has been bought, drop it from 9.1 step 11 and mark the BOM rows as bought. The files support «купується».
  ДОКАЗ: final/user_requirements.md line 49: 'the QO-100 add-on ... is bought' (a consequence of region Europe). STACK 9.1 step 11. v2_edit_notes 04 b2 (kept «купується») vs 05b b2 («куплено»).

- [A53 | contradiction | reaudit_AB] ДЕ: 4.1 row S-band, decoder cell «SatDump лише з цивільними й аматорськими конвеєрами з алоу-листа»
  ПРОБЛЕМА: The Europe SatDump pipeline allowlist (1.2 #30, 5.4) has only Meteor-M, MetOp, AWS, FengYun-2 and Elektro_Arktika JSONs, none of them S-band. So no SatDump decoder exists for Black Kite or PHASMA.
  ВИПРАВЛЕННЯ: Decoder cell: «SatDump — S-band конвеєра в європейському алоу-листі немає / gr-satellites (розбір кадрів не перевірено)».
  ДОКАЗ: STACK 1.2 #30 and 5.4 pipeline allowlist. v2_edit_notes 04 b2: 'That leaves no SatDump pipeline for the S-band Black Kite/PHASMA rows'.

- [A54 | contradiction | reaudit_AB] ДЕ: 4.1 row «GNSS L1 + regional SBAS»
  ПРОБЛЕМА: Region Europe sets SBAS = EGNOS, and 11.6 row 43 says «regional SBAS» was replaced by «EGNOS», but the 4.1 target name still says regional SBAS.
  ВИПРАВЛЕННЯ: Rename the row to «GNSS L1 + SBAS (EGNOS)».
  ДОКАЗ: final/user_requirements.md line 49 'SBAS = EGNOS'. STACK 11.6 row 43. v2_edit_notes 04 b1: 'The GNSS target cell still says regional SBAS'.

- [A55 | contradiction | reaudit_CD] ДЕ: 1.1 C24 «близько 1.72-1.94 kg»; 2.12 «плюс 0.15 kg за Lime = 1.72-1.94 kg»; 1.1 D14 «на спині 6.8-8.2 і 7.7-9.4 kg»; 2.5 Сумки «вміст 5.54-6.92 kg без КХ»; 11.4 рядок 34 «близько 5.2-7.1 kg без КХ і щогли»; 5.8 «вміст **5.60-7.01 kg**»
  ПРОБЛЕМА: The device and backpack weights with Lime disagree across sections. 5.8 adds up its own mass table: parts 1.58-1.81 kg (battery row 0.33-0.34 kg, HF+ shield +0.05-0.07), so 1.73-1.96 kg with Lime. Backpack contents are 5.60-7.01 / 6.50-8.26 kg, and on the back 6.85-8.26 / 7.75-9.51 kg. C24 and 2.12 still give parts 1.57-1.79 / 1.72-1.94 kg. C24, D14, 2.12, 2.5 and 11.1 still give G4's backpack figures (5.54-6.92 / 6.44-8.17; 6.8-8.2 / 7.7-9.4), which G4 computed with a 1.67-1.87 kg device. 11.4 row 34 still gives the pre-Lime 5.2-7.1 / 6.1-8.4 kg and says 2.12 and D14 carry the same figures, w
  ВИПРАВЛЕННЯ: Use the 5.8 sum everywhere. In C24 and 2.12: device with Lime 1.73-1.96 kg (parts 1.58-1.81 kg), without Lime 1.58-1.81 kg. In C24, D14, 2.12, 2.5 «Сумки», 11.1 (G4 rows) and 11.4 row 34: backpack contents 5.60-7.01 kg without HF and mast and 6.50-8.26 kg full, on the back 6.85-8.26 / 7.75-9.51 kg. Keep 5.54-6.92 / 6.44-8.17 only as «G4, пристрій 1.67-1.87 kg». Delete 5.2-7.1 / 6.1-8.4 from 11.4 row 34. Either recompute with the Rollei 1.14 kg (calculation from the 5.8 rows: 5.57-6.80 / 6.47-8.05 kg, on the back 6.82-8.05 / 7.72-9.30 kg) or state that 1.17-1.35 kg is a conservative tripod value.
  ДОКАЗ: STACK 5.8 mass table (rows sum to 1.58-1.81 kg); reaudit_D_power_mech_display_lab.json results[3].corrections[16] (battery 0.33-0.34 kg); reaudit_C_antennas_targets.json results[1].corrections[15]; analogs_G4_mechanical_field.json decisions[4] (Rollei 1.14 kg) and decisions[5] (backpack computed wit

- [A56 | contradiction | reaudit_CD] ДЕ: 4.1 Metop-B/C «далі Lime ≥6 Msps ci16 (гелікон + SAWbird+ GOES → Lime RX)»; 4.1 AWS «після приходу Lime — Lime ≥6 Msps ci16; Airspy Mini»; 5.3 «також для Metop/AWS на ≥6 Msps ci16»; 1.2 #91 «на цьому тракті. 6 Msps; продавець і ціна»; 9.1 «захоплення без втрат на ≥6 Msps на тракті гелікон»; 11.4 рядок 26 «Lime ≥6 Msps ci16, Airspy Mini — лише запасний за воротами»
  ПРОБЛЕМА: The Lime sample rate for Metop/AWS conflicts between sections. 2.11.1, 2.11.3, 5.7, 8 (L-3) and 8.1 all state a hard 7 Msps floor and say «reaudit C називав 6 Msps, але швидкості Lime нижче 7 Msps заблоковано». The 9.1 Airspy condition defines an acceptance capture at a blocked rate. 1.2 #91 also has a stray fragment «. 6 Msps;» left over from an edit.
  ВИПРАВЛЕННЯ: Replace «≥6 Msps» with «7 Msps ci16 (нижня межа профілів Lime; L-3 у 8.1)» in the 4.1 Metop and AWS rows, the 5.3 «Лише з Lime» row, 9.1 and 11.4 row 26. In 1.2 #91, delete the fragment «6 Msps;» and change «Lime на ≥6 Msps прибирає 82 %» to «Lime на 7 Msps прибирає 82 %». In 9.1, make the Airspy condition «15-хв захоплення без втрат на 7 Msps».
  ДОКАЗ: reaudit_B_receivers_rf.json Lime sample rates ('Allowed: 7-61.44 Msps ... Block anything below 7 Msps'; 'the 7 Msps floor stays'); analogs_G6_extended_optional.json decisions[12].conditions_or_tests ('15-minute zero-drop 7 Msps capture'); reaudit_C results[2].corrections[11] (the 6 Msps that was ove

- [A57 | contradiction | reaudit_CD] ДЕ: 1.2 #91 «лише після воріт «горб на одній спіралі» і тесту V4L 2.88 Msps і лише якщо Lime не пройшов»; 2.11.3 «Airspy Mini купувати лише якщо ворота (a)/(b) провалені І Lime не пройшов»; 9.1 «і лише якщо Lime не пройде 15-хв захоплення без втрат на ≥6 Msps»
  ПРОБЛЕМА: The Airspy Mini purchase gate is inconsistent. In 4.1, 8 and 8.2 the gate follows G6 #12: buy if (a) 15 min of rtl_test at 2.88 Msps fails, OR (b) the Metop hump is seen but the V4L cannot decode. The Lime condition there is an optional scope choice for the user. 1.2 #91, 2.11.3 and 9.1 instead require a gate AND a failed Lime capture, which turns the Lime condition into a mandatory one.
  ВИПРАВЛЕННЯ: In 1.2 #91, 2.11.3 «Швидкий L-band SDR» and 9.1, use the G6 wording already in 4.1 and 8: «купувати лише якщо (a) 15 хв rtl_test 2.88 Msps на синьому порту не проходять без втрат АБО (b) горб Metop видно, а V4L не декодує; опційно не купувати, якщо Lime уже пройшов 15-хв захоплення без втрат на 7 Msps на тракті гелікон + SAWbird+ GOES — вибір обсягу (компроміс такту й живлення), вирішуєте ви».
  ДОКАЗ: analogs_G6_extended_optional.json decisions[12].conditions_or_tests ('Buy only if gate (a) fails ... or gate (b) shows the Metop hump but the V4L cannot decode. Optionally ... That is a scope choice, and it must be told to the user')

- [A58 | contradiction | reaudit_CD] ДЕ: 4.1, рядок «S-band | ті самі | складаний + Lime», декодер «SatDump лише з цивільними й аматорськими конвеєрами з алоу-листа»
  ПРОБЛЕМА: The S-band decoder cell names SatDump pipelines, but the v2 package ships only Meteor-M, MetOp, AWS, FengYun-2 and Elektro_Arktika (1.2 #30, 5.4, 11.4 row 30). No SatDump pipeline exists for Black Kite or PHASMA. An editor flagged this and it is still open.
  ВИПРАВЛЕННЯ: Change the decoder cell to «gr-satellites (розбір кадрів не перевірено); конвеєра SatDump для Black Kite/PHASMA у пакеті немає (лише Meteor-M, MetOp, AWS, FengYun-2, Elektro_Arktika)».
  ДОКАЗ: reaudit_C results[2].corrections[0] action (package only Meteor-M.json, MetOp.json, AWS.json, FengYun-2.json, Elektro_Arktika.json); edit notes 04_capabilities b2 ('Possible inconsistency ... S-band Black Kite/PHASMA rows')

- [A59 | contradiction | reaudit_CD] ДЕ: 1.2 #7 «SHM 0 refid NMEA noselect + PPS lock NMEA prefer»; 11.5 рядок 47 «KERNELS=="998000.serial" → /dev/gnss0»; 11.2 рядок 15 «refclock PPS /dev/pps0 lock NMEA refid PPS prefer» … «узгоджується при зведенні»
  ПРОБЛЕМА: GNSS timing and device names conflict with the body text. 5.4, C13 and 11.5 row 31 set PPS to /dev/pps-gnss with noselect, enabled by the gate through chronyc selectopts. 5.2 and 5.4 use /dev/lab/gnss, and 6.2 lists /dev/gnss0 as removed. 5.4 has already chosen GPSD_OPTIONS -n -b. #7 still says PPS 'prefer', 11.5 row 47 says /dev/gnss0, and 11.2 row 15 says /dev/pps0 'prefer' and calls the gpsd options unresolved.
  ВИПРАВЛЕННЯ: 1.2 #7: «chrony 4.5: refclock SHM 0 refid NMEA offset <виміряна медіана> delay 0.2 noselect + refclock PPS /dev/pps-gnss lock NMEA refid PPS noselect; ворота вмикають PPS через chronyc selectopts PPS -noselect». 11.5 row 47: change «→ /dev/gnss0» to «→ /dev/lab/gnss (ім'я — за повторним аудитом A; /dev/gnss0 прибрано, 6.2)». 11.2 row 15: replace «/dev/pps0 … prefer» with «/dev/pps-gnss … noselect (повторний аудит D)» and «узгоджується при зведенні» with «обрано -n -b -s 115200 (5.4)».
  ДОКАЗ: reaudit_D results[1].corrections[5] (chrony action), corrections[11] (/dev/pps-gnss), corrections[12] (-b); STACK 5.4 gpsd/chrony row and 6.2 («/dev/gnss0 як ім'я GNSS»)

- [A60 | contradiction | rules] ДЕ: 1.2 #31 (line 126): «явний алоу-лист channelrx: AM/NFM/SSB/WFM, ADS-B (лише з нашими правилами показу dbFlags &1/&4/&8, інакше вимкнено), AIS (лише з придушенням type-35, інакше вимкнено)»; 11.6 row 35 (line 2396), same text; 11.6 row 27 (line 2388): «ADS-B у SDRangel — лише з цими правилами показу»
  ПРОБЛЕМА: These rows list SDRangel ADS-B and AIS as allowed when the filters apply. Elsewhere the stack says SDRangel demodadsb/demodais are never built, because the military, PIA and LADD dbFlags filters and the type-35 suppression exist only in readsb and AIS-catcher, and the SDRangel plugins bypass them: 4.3 line 603, 5.4 lines 854/867/871, 6.1 line 1126, 8 line 1464 (CI fails on demodadsb/demodais), 11.2 row 33 line 2147. A builder following 1.2 #31 or 11.6 could ship a path that shows PIA/LADD and military tracks (operator note 25).
  ВИПРАВЛЕННЯ: Line 126 and line 2396: replace the ADS-B/AIS items with «ADS-B і AIS — не в SDRangel (demodadsb/demodais не збираються); лише readsb і AIS-catcher з dbFlags &1/&4/&8 і придушенням типу 35». Line 2388: replace «ADS-B у SDRangel — лише з цими правилами показу» with «ADS-B — лише readsb з цими правилами; demodadsb у SDRangel не збирається (5.4, 6.1)».
  ДОКАЗ: operator_notes.md item 25 (PIA &4 / LADD &8 not shown or logged). STACK.md line 867 («ADS-B і AIS — лише в readsb і AIS-catcher … бо ці фільтри є лише там») and line 1126 («demodadsb/demodais обходять фільтри dbFlags readsb і ship-type 35 AIS»).

- [A61 | contradiction | structure] ДЕ: 1.1, L49: «Ці рішення заморожені для v1 і переважають усе, що суперечить їм в інших файлах.»
  ПРОБЛЕМА: This v1 sentence was carried over unchanged. It contradicts the v2 source order in the header (user decisions > operator rules > P5 > P4 > v1 text). In v2, C1, C2, C4, C23, D8 and others were rewritten by those higher sources.
  ВИПРАВЛЕННЯ: Replace with «Рішення заморожено у v1; у v2 їх змінено лише там, де цього вимагають рішення користувача 18.10.2026, правила нотаток оператора, рішення аналогів P5 або повторний аудит P4 (порядок — у шапці; кожна зміна — у розділі 11).»
  ДОКАЗ: STACK.md line 49 vs line 13 («Пріоритет джерел у v2») and section 11 rows

- [A62 | contradiction | structure] ДЕ: 2 (intro), L183: «ціни й продавці — з final_world_sourcing.json»
  ПРОБЛЕМА: Stale v1 claim. In v2, part, seller and price are decided by the P5 analog decisions (header L13, 11.1). final_world_sourcing.json no longer sets prices or sellers.
  ВИПРАВЛЕННЯ: Change to «ціни й продавці — з рішень аналогів P5 (final/analogs_G1-G6; див. 11.1), а де P5 нічого не змінив — з final_world_sourcing.json».
  ДОКАЗ: STACK.md line 183 vs line 13 and 11.1 intro (line 2026)

- [A63 | contradiction | structure] ДЕ: 1.2, row «Варіант Lime з GNSS (#83)», L157: «Лише якщо Lime залишено.»
  ПРОБЛЕМА: A stale v1 condition. Lime is kept (user decision 18.10.2026), so the consequence column still reads as if Lime were optional.
  ВИПРАВЛЕННЯ: Replace with «Lime залишено (рішення 18.10.2026): варіант з GNSS не брати.»
  ДОКАЗ: STACK.md line 157 vs line 53 (C1) and line 319

- [A64 | contradiction | structure] ДЕ: 4.1, L554: «Elektro-L5/FY-2H: Берлін 7.6/5.8°, Рим 10.8/8.5°, Варшава 12.0/10.3°, Атени 20.6/18.2°»; 1.2 L170 «Лісабон −4.9/−7.3°, Лондон −0.1/−2.1°, Париж +1.9/−0.1°…»; 11.4 L2270
  ПРОБЛЕМА: Per-city elevation angles were added back. The same document states that city-specific angles were removed by rule: 1.2 #6 L106 «кути для конкретних міст прибрано» and 6.1 L1116 «константи поля і кути наведення для конкретних міст».
  ВИПРАВЛЕННЯ: Replace the city lists with regional bands, as 11.6 L2382 already does: «Elektro-L5/FY-2H: нижче або біля горизонту в Іберії, Ірландії й Великій Британії, близько 6-12° у центральній Європі, близько 18-21° на південному сході (модель)». Keep city fixes only as CI test coordinates (8, L1489).
  ДОКАЗ: STACK.md lines 106, 170, 554, 1116, 2270, 2382; final/user_requirements.md lines 13, 39, 49 («no city tables»)

- [A65 | contradiction | structure] ДЕ: 3.1, row «Банк живлення», L411, status: «перевірено через агрегатор (сторінки магазинів — 403)»
  ПРОБЛЕМА: The document's legend says (перевірено) means seen at the primary source. Here the price comes from an aggregator (billiger.de) and the shop pages returned 403. By the document's own definition the status is not «перевірено».
  ВИПРАВЛЕННЯ: Status: «не перевірено (ціна з агрегатора billiger.de; сторінки MediaMarkt/Saturn — 403)».
  ДОКАЗ: STACK.md line 411 (status cell) vs line 9 («(перевірено) — … побачені на першоджерелі»)

- [A66 | missing | analogs_G1_G3] ДЕ: 2.6 «Логіка інтерфейсу»: «5× AOS AO3400A (вентилятор Q6A, повітродувка, котушки G6K K1 і K2, запасний шлях вентилятора)»; 2.1 «Охолодження»: «вентилятор шляху 1 — ключ з боку плюса (P-MOSFET або 5 V load switch) з діодом»
  ПРОБЛЕМА: G2 #1 says the 3-wire tach fan on path 1 must be switched high-side by a P-MOSFET plus driver, or by a 5 V load switch. No BOM row lists or prices that P-MOSFET or load switch. The interface-logic set (G2 #10) has only the N-channel AO3400A for «вентилятор Q6A», and on its own that is a low-side switch.
  ВИПРАВЛЕННЯ: Add to 2.6 «Логіка інтерфейсу» (or the 2.1 cooling row) an unpriced item «P-MOSFET верхнього ключа вентилятора шляху 1 (або ключ навантаження 5 V) + діод зворотного ходу — деталь не обрано, модель (G2 #1, п. 3); AO3400A «вентилятор Q6A» — його драйвер затвора».
  ДОКАЗ: analogs_G2_display_hmi_storage.json decisions[1].stack_changes 3 («switch path-1 high-side (P-MOSFET plus a small driver, or a 5 V load switch)»); decisions[10].chosen (AO3400A list)

- [A67 | missing | analogs_G4_G6] ДЕ: 1.1 D2: «Проводка AWG 18-20 у колі батареї.»; 5.1: «Проводка в колі батареї — AWG 18-20.»; 3.1 «Інструменти»: «Jokari 20050 +$28.63 (якщо тракт батареї 18 AWG)»
  ПРОБЛЕМА: G5 #15 stack_changes requires stating one gauge, 20 AWG or 18 AWG, for the battery path, because 18 AWG needs the second stripper (Jokari 20050). v2 still says 18-20 AWG, so the tools line cannot be closed. The same stack already uses an 18 AWG silicone XT30 service lead and a 16 AWG XT60-XT30 lead (2.7 «Збирання батареї»), which falls inside the 18 AWG branch.
  ВИПРАВЛЕННЯ: Fix one gauge in D2 and 5.1. If it is 18 AWG (or if the 18 AWG service lead and the 16 AWG XT60-XT30 lead are counted), move Jokari 20050 (+$28.63, TME) from «Опції» into the tools set. If it is 20 AWG, write «20 AWG — лише Jokari 40026» and keep the 8.x stripper test.
  ДОКАЗ: analogs_G5_lab_bench.json decisions[15].stack_changes («Wire gauge: state 20 AWG or 18 AWG for the battery path, since 18 AWG needs a second stripper») and conditions_or_tests 4. STACK 2.7 «Збирання батареї» (18 AWG silicone; XT60-XT30 16 AWG).

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
