# Аудит TX LimeSuiteNG 37cb183 — частина I (публічні точки входу)

**Статус: AUDIT_DRAFT_CI_CHECKED.** Це чернетка аудиту, яку написав агент і перевірив лише CI (тести хоста, збирання `sr-rx-packages`). Вона не є рецензією: статус REVIEWED може поставити лише рецензент після лавних вимірів RX-08-hw. Lime runtime лишається заблокованим: `deploy.py verify_build` відхиляє бібліотеки Lime, пакети `liblimesuiteng` і `limesuiteng-soapysdr` утримано з репозиторію (recipes/README.md), апаратного PASS немає.

Частина I (пакет W2 SW-LIME-1) охоплює публічні точки входу: модуль SoapySDR (`plugins/soapysdr`), нативний C++ API `SDRDevice` з реалізаціями `LimeSDR_Micro` і `LMS7002M_SDRDevice`, API `LimePlugin`, застарілий C API `LMS_*` (`src/legacyapi`) і продукти збирання. Частина II (SW-LIME-2) — внутрішні шляхи: `src/chips/LMS7002M`, `src/chips/LA9310` (команди VSPA, TX-тон калібрування), `drivers/linux/la9310_limesdr` (кільце DMA TX), `embedded/lms7002m`, `src/streaming/TRXLooper.cpp`, прошивки й EEPROM, а також перевірка експорту `nm -D`.

## Джерело

- Архів закріпленого коміту: https://github.com/myriadrf/LimeSuiteNG/archive/37cb1833e35955f7072c0fb91642d14ae5515f28.tar.gz, завантажено й прочитано 07.11.2026; SHA-256 `818cb504284991acf69cc214469d695eff35b35244b73ace23768a95c7d9c749`, 13197691 байт — збігається з `sources.lock.json` (компонент `limesuiteng`). Ліцензія Apache-2.0 (`upstream-fixtures/limesuiteng/COPYING`).
- Усі посилання `файл:рядок` нижче — на файли цього архіву **до** патча (`deployment/patches/limesuiteng-rx-only.patch`).
- Чотири нові цілі патча (`plugins/soapysdr/Settings.cpp`, `src/API/LimePlugin.cpp`, `src/boards/LMS7002M_SDRDevice.cpp`, `src/boards/LimeSDR_Micro/calibrations.cpp`) скопійовано в `deployment/upstream-fixtures/limesuiteng/` байт у байт з того самого архіву; їхні `before_sha256` записано в `deployment/patches/target-hashes.json`.
- Типові реалізації SoapySDR (рядок A-24): https://raw.githubusercontent.com/pothosware/SoapySDR/soapy-sdr-0.8.1/lib/Device.cpp, прочитано 07.11.2026 (у noble — `libsoapysdr-dev` 0.8.1).

## Вердикти

- `blocked` — шлях не компілюється (опцією рецепта) або upstream уже повертає помилку чи нічого не робить.
- `reachable→patched` — шлях досяжний ззовні бібліотеки й тепер відхиляється патчем (позначка `SRRX_RX_ONLY` у коді).
- `internal-only` — шлях лишається, бо його викликає лише бібліотека для RX (калібрування RX із внутрішньою петлею TX дозволяє STACK.md:128).
- `no-TX` — шлях не може ввімкнути чи налаштувати TX (читання, спільний такт).
- `open→part-II` — залишок, який закриває частина II або лава.

Стовпець «Якір» — текст, що стоїть у вказаному рядку; `deployment/tests/test_lime_tx_audit.py` звіряє якорі з копіями `upstream-fixtures/limesuiteng/` і перевіряє, що кожна точка `reachable→patched` у цих файлах після патча має захист.

## A. Модуль SoapySDR (`limesuiteng-soapysdr`, єдиний інтерфейс споживачів)

| ID | Точка входу | 37cb183 файл:рядок | Якір | Вердикт | Що зроблено / чому |
|---|---|---|---|---|---|
| A-01 | Конструктор `Soapy_limesuiteng`: TX-канали | plugins/soapysdr/Settings.cpp:59 | `sdrDevice->EnableChannel(socIndex, TRXDir::Tx, channel, true);` | reachable→patched | Upstream одразу після `Init()` (:53) вмикає TX кожного каналу (TXEN_A/TXEN_B, TX-тракт). Патч: `EnableChannel(Tx, false)` — під час відкриття TX вимкнено; нативний `EnableChannel(Tx, true)` відхиляє B-03. Деструктор (:91) лише вимикає |
| A-02 | `setupStream(SOAPY_SDR_TX)` | plugins/soapysdr/Streaming.cpp:107 | `SoapySDR::Stream* Soapy_limesuiteng::setupStream(` | reachable→patched | Патч етапу 3: напрям ≠ RX — виняток до виділення потоку; `StreamCreate` (:182) з TX-каналами ще й відхиляє B-25 |
| A-03 | `writeStream` | plugins/soapysdr/Streaming.cpp:362 | `int Soapy_limesuiteng::writeStream(` | reachable→patched | Патч етапу 3: у тілі немає `Transmit`, повертає `SOAPY_SDR_NOT_SUPPORTED` |
| A-04 | `setAntenna(TX)` | plugins/soapysdr/Settings.cpp:158 | `void Soapy_limesuiteng::setAntenna(` | reachable→patched | TX: смуга TRF і перемикач TX_SW (B-08). Патч: `srrxRejectTx` — напрям ≠ RX відхиляється |
| A-05 | `setDCOffsetMode(TX)` | plugins/soapysdr/Settings.cpp:204 | `void Soapy_limesuiteng::setDCOffsetMode(` | reachable→patched | Налаштування TX TSP. Патч: `srrxRejectTx` |
| A-06 | `setDCOffset(TX)` | plugins/soapysdr/Settings.cpp:221 | `void Soapy_limesuiteng::setDCOffset(` | reachable→patched | Корекція TX DC. Патч: `srrxRejectTx` |
| A-07 | `setIQBalance(TX)` | plugins/soapysdr/Settings.cpp:242 | `void Soapy_limesuiteng::setIQBalance(` | reachable→patched | Корекція TX IQ. Патч: `srrxRejectTx` |
| A-08 | `setGain(TX)` (загальне) | plugins/soapysdr/Settings.cpp:276 | `void Soapy_limesuiteng::setGain(const int direction, const size_t channel, const double value)` | reachable→patched | TX PAD (B-06). Патч: `srrxRejectTx` |
| A-09 | `setGain(TX, name)` | plugins/soapysdr/Settings.cpp:303 | `void Soapy_limesuiteng::setGain(const int direction, const size_t channel, const std::string& name` | reachable→patched | TX PAD/IAMP (B-06). Патч: `srrxRejectTx` |
| A-10 | `setFrequency(TX)` | plugins/soapysdr/Settings.cpp:368 | `void Soapy_limesuiteng::setFrequency(int direction` | reachable→patched | SXT (B-04). Патч: `srrxRejectTx` |
| A-11 | `setFrequency(TX, "RF"/"BB")` | plugins/soapysdr/Settings.cpp:386 | `void Soapy_limesuiteng::setFrequency(const int direction,` | reachable→patched | RF → SXT, BB → `SetNCOFrequency(Tx)` (:413). Патч: `srrxRejectTx` |
| A-12 | `setSampleRate(TX)` | plugins/soapysdr/Settings.cpp:483 | `void Soapy_limesuiteng::setSampleRate(` | reachable→patched | На Micro такт спільний (B-14), але TX-напрям не потрібен RX-програмам. Патч: `srrxRejectTx`; `OVERSAMPLING` (:948-951) перевстановлює TX-частоту лише якщо вона колись була задана — тепер ніколи |
| A-13 | `setBandwidth(TX)` | plugins/soapysdr/Settings.cpp:542 | `void Soapy_limesuiteng::setBandwidth(` | reachable→patched | TX LPF (B-07). Патч: `srrxRejectTx` перед перевіркою `bw == 0` |
| A-14 | `setHardwareTime` | plugins/soapysdr/Settings.cpp:631 | `void Soapy_limesuiteng::setHardwareTime(` | no-TX | Upstream нічого не пише (TODO, :643-647) |
| A-15 | `writeRegister("RFIC<n>"/"BBIC", addr, value)` | plugins/soapysdr/Settings.cpp:753 | `void Soapy_limesuiteng::writeRegister(const std::string& name` | reachable→patched | RFIC → `SDRDevice::WriteRegister` (будь-який регістр LMS7002M, зокрема 0x0020 TXEN), BBIC → FPGA. Патч: завжди виняток |
| A-16 | `writeRegister(addr, value)` | plugins/soapysdr/Settings.cpp:799 | `void Soapy_limesuiteng::writeRegister(const unsigned addr` | reachable→patched | Регістр FPGA (`useFPGA=true`). Патч: завжди виняток |
| A-17 | `readRegister("RFIC0", 0x0020)` | plugins/soapysdr/Settings.cpp:780 | `unsigned Soapy_limesuiteng::readRegister(const std::string& name` | no-TX | Читання; шлях read-back 0x0020 (build/07-pz-vstanovlennia.md:355) лишається |
| A-18 | `writeSetting(key, value)` (на весь пристрій) | plugins/soapysdr/Settings.cpp:846 | `void Soapy_limesuiteng::writeSetting(const std::string& key` | reachable→patched | TX-ключі `TXTSP_CONST` (:857), `CALIBRATE_TX` (:865), `ENABLE_TX_GFIR_LPF`/`DISABLE_TX_GFIR_LPF` (:889, :905), `TXTSG_NCO` (:921); `LOAD_CONFIG` (:935) вантажить файл регістрів, `SAVE_CONFIG` (:929) пише файл; будь-який інший ключ іде в `SetParameter` за назвою поля (:1089), напр. `TXEN_A=1`. Патч: алоу-лист `RXTSP_CONST`, `CALIBRATE_RX`, `ENABLE_RX_GFIR_LPF`, `DISABLE_RX_GFIR_LPF`, `RXTSG_NCO`, `OVERSAMPLING` і лише `TXEN_A=0`/`TXEN_B=0` |
| A-19 | `writeSetting(direction, channel, key, value)` | plugins/soapysdr/Settings.cpp:1008 | `void Soapy_limesuiteng::writeSetting(const int direction` | reachable→patched | `CALIBRATE_TX` → `Calibrate(Tx)` (:1024) за будь-якого напряму; невідомий ключ → `SetParameter(key)` (:1089). Патч: напрям лише RX, алоу-лист `TSP_CONST`, `CALIBRATE_RX`, `CALIBRATE`, `ENABLE_GFIR_LPF`, `DISABLE_GFIR_LPF`, `TSG_NCO` і `TXEN_A=0`/`TXEN_B=0` |
| A-20 | `writeSetting(RX, ch, "CALIBRATE_RX")` | plugins/soapysdr/Settings.cpp:1033 | `sdrDevice->Calibrate(socIndex, TRXDir::Rx, channel, bw);` | internal-only | RX IQ/DC-калібрування з внутрішнім TX-тоном (B-23), дозволено STACK.md:128 |
| A-21 | `readSetting` | plugins/soapysdr/Settings.cpp:1147 | `uint16_t val = sdrDevice->GetParameter(0, channel, key);` | no-TX | Читання поля, зокрема read-back `TXEN_A`/`TXEN_B` |
| A-22 | `writeGPIO` | plugins/soapysdr/Settings.cpp:1161 | `void Soapy_limesuiteng::writeGPIO(` | reachable→patched | GPIO плати (на Micro `GPIOWrite` — NotImplemented, B-29; на інших платах GPIO діє). Патч: виняток; `writeGPIO(bank, value, mask)` SoapySDR (Device.cpp:775) викликає цей метод |
| A-23 | `writeGPIODir` | plugins/soapysdr/Settings.cpp:1181 | `void Soapy_limesuiteng::writeGPIODir(` | reachable→patched | Напрям GPIO плати. Патч: виняток |
| A-24 | Методи SoapySDR без перевизначення: `writeRegisters`, `writeI2C`, `transactSPI`, `writeUART`, `setClockSource`, `setMasterClockRate`, `setGainMode`, `setFrequencyCorrection` | SoapySDR 0.8.1 lib/Device.cpp:719 | `void SoapySDR::Device::writeRegisters(const std::string &, const unsigned, const std::vector<unsigned> &)` | blocked | Типові реалізації порожні (Device.cpp:719, :810, :823, :836, :609, :574, :282); `setFrequencyCorrection` (:248) діє лише для компонента `CORR`, а модуль повідомляє тільки `RF` і `BB` (Settings.cpp:443-450) |

## B. Нативний C++ API (`SDRDevice`, `LimeSDR_Micro`, `LMS7002M_SDRDevice`)

Публічний заголовок — `src/include/limesuiteng/SDRDevice.h` (встановлюється пакетом `limesuiteng-dev`, src/include/CMakeLists.txt:18). Споживача C++ API серед пакетів SR-RX немає: `limesuiteng-dev` — лише для chroot збирача, а бібліотеку відкриває тільки модуль Soapy (див. «Залишки», п. 1). Micro не перевизначає `EnableChannel`, `SetFrequency`, `SetGain`, `SetLowPassFilter`, `SetParameter`, `LoadConfig`, `GetInternalChip`, тож вони захищені в базі `LMS7002M_SDRDevice` — так само для всіх плат LMS7002M.

| ID | Точка входу | 37cb183 файл:рядок | Якір | Вердикт | Що зроблено / чому |
|---|---|---|---|---|---|
| B-01 | `Configure` з TX (SDRDevice.h:70) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:426 | `OpStatus LimeSDR_Micro::Configure(` | reachable→patched | Патч етапу 3: `tx.enabled` каналу 0 чи 1 → NotSupported. Тепер також `tx.calibrate`, `tx.testSignal.enabled`, `tx.centerFrequency > 0`, непорожній `tx.gain`. Дозволено: refclk (`referenceClockFreq`/`referenceClockSource` → `fw->SetReferenceClock`, :433-440) і `tx.enabled=false` → `chip.EnableChannel(Tx, false)` (LMS7002M_SDRDevice.cpp:1237) — це і є шлях `--txen=0` (cli/limeConfig.cpp:125). `LMSSetPath(Tx)` у Configure (:461) лише вибирає смугу; `CalibrateTx` (:481) недосяжний |
| B-02 | `Init()` → `InitLMS7002M` (LimeSDR_Micro.cpp:493) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:313 | `values.push_back(0xFFFD); // back to A channel only` | reachable→patched | Upstream пише 0x0020 = 0xFFFF, а наприкінці 0xFFFD (:305, :313): TXEN_A/TXEN_B = 1, як і апаратне значення за замовчуванням (src/chips/LMS7002M/registersHardwareDefaults.h:14). Патч: 0xFFF3 і 0xFFF1 — TXEN очищено, MAC і RXEN ті самі. Після `Init()` TX вимкнено на рівні регістра навіть без Configure. `Init()` викликають конструктор Soapy (A-01) і Configure (:445) |
| B-03 | `EnableChannel(Tx, true)` (SDRDevice.h:109) | src/boards/LMS7002M_SDRDevice.cpp:107 | `OpStatus LMS7002M_SDRDevice::EnableChannel(` | reachable→patched | → `lms7002m_enable_channel` (embedded/lms7002m/lms7002m.c:108; TXEN_A :116, TX-тракт і SXT). Патч: TX можна лише вимкнути |
| B-04 | `SetFrequency(Tx)` (SDRDevice.h:145) | src/boards/LMS7002M_SDRDevice.cpp:179 | `OpStatus LMS7002M_SDRDevice::SetFrequency(` | reachable→patched | Налаштовує SXT. Патч: Tx → NotSupported; RX і перевірка TDD без змін |
| B-05 | `SetClockFreq(CLK_SXT)` | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:543 | `OpStatus LimeSDR_Micro::SetClockFreq(` | reachable→patched | `CLK_SXT` → `lms7002m_set_frequency_sx(self, true, …)` (embedded/lms7002m/lms7002m.c:1666) — інший шлях до TX LO. Патч: `CLK_SXT` → NotSupported; REFERENCE, CGEN і SXR лишаються |
| B-06 | `SetGain(Tx)` і TX-типи `PAD`, `LoopbackPAD`, `IAMP`, `PA` (SDRDevice.h:236) | src/boards/LMS7002M_SDRDevice.cpp:452 | `OpStatus LMS7002M_SDRDevice::SetGain(` | reachable→patched | `PAD`/`IAMP` пишуть TX-підсилення навіть з напрямом Rx (:467-472). Патч: усе це → NotSupported; `LMS7002ChannelConfigure` (:1255) отримує NotSupported для TX-підсилень |
| B-07 | `SetLowPassFilter(Tx)` (SDRDevice.h:253) | src/boards/LMS7002M_SDRDevice.cpp:305 | `OpStatus LMS7002M_SDRDevice::SetLowPassFilter(` | reachable→patched | TX LPF. Патч: Tx → NotSupported |
| B-08 | `SetAntenna(Tx)` (SDRDevice.h:270) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:845 | `OpStatus LimeSDR_Micro::SetAntenna(` | reachable→patched | → `LMSSetPath(Tx)` (:682): `SetBandTRF` і TX_SW (біт 1 GPIOB розширювача 0x20 або PHY-таймер 15, :692-715). Живлення TX не вмикає, але це TX-налаштування. Патч: Tx → NotSupported; Configure викликає `LMSSetPath` напряму (:461) |
| B-09 | `SetNCOFrequency`/`SetNCOIndex` | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:511 | `OpStatus LimeSDR_Micro::SetNCOFrequency(` | blocked | Upstream повертає NotSupported (:514, :524) |
| B-10 | `SetTestSignal` | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:643 | `OpStatus LimeSDR_Micro::SetTestSignal(` | blocked | NotImplemented (:650) |
| B-11 | `SetDCOffsetMode` | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:554 | `OpStatus LimeSDR_Micro::SetDCOffsetMode(` | blocked | NotImplemented (:556) |
| B-12 | `SetDCOffset`/`SetIQBalance` | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:564 | `OpStatus LimeSDR_Micro::SetDCOffset(` | blocked | NotImplemented (:573, :591) |
| B-13 | `ConfigureGFIR`/`SetGFIRCoefficients`/`SetGFIR` | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:611 | `OpStatus LimeSDR_Micro::ConfigureGFIR(` | blocked | NotImplemented (:614, :625, :630) |
| B-14 | `SetSampleRate` (будь-який напрям) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:532 | `OpStatus LimeSDR_Micro::SetSampleRate(` | no-TX | Спільний системний такт LA9310 для RX і TX (`SetLA9310SamplingRate`), TX не вмикає |
| B-15 | `WriteRegister` (SDRDevice.h:384) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:600 | `OpStatus LimeSDR_Micro::WriteRegister(` | reachable→patched | Сирий `SPI_write` у будь-який регістр LMS7002M. Патч: лише запис TX-off у 0x0020 (біти 2-3, TXEN_A/TXEN_B, = 0) |
| B-16 | Базовий `WriteRegister` (інші плати, `useFPGA`) | src/boards/LMS7002M_SDRDevice.cpp:671 | `OpStatus LMS7002M_SDRDevice::WriteRegister(` | reachable→patched | Те саме правило; запис FPGA (`useFPGA`) відхиляється |
| B-17 | `ReadRegister` | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:594 | `unsigned int LimeSDR_Micro::ReadRegister(` | no-TX | Читання; read-back 0x0020 лишається |
| B-18 | `SPI(MOSI, MISO, count)` (SDRDevice.h:563) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:662 | `OpStatus LimeSDR_Micro::SPI(` | reachable→patched | Сирий SPI-обмін; слово з бітом 31 — запис (src/chips/LMS7002M/LMS7002M.cpp:1325). Патч: читання проходять, запис — лише TX-off у 0x0020 |
| B-19 | `SetParameter(name, value)` (SDRDevice.h:418) | src/boards/LMS7002M_SDRDevice.cpp:706 | `OpStatus LMS7002M_SDRDevice::SetParameter(uint8_t moduleIndex, uint8_t channel, const std::string& parameterKey` | reachable→patched | Будь-яке поле CSR за назвою (`TXEN_A`, `PD_TXPAD_TRF`…). Патч: лише `TXEN_A=0`/`TXEN_B=0` |
| B-20 | `SetParameter(address, msb, lsb, value)` | src/boards/LMS7002M_SDRDevice.cpp:729 | `OpStatus LMS7002M_SDRDevice::SetParameter(` | reachable→patched | Будь-яке поле за адресою. Патч: лише нуль у бітах 3..2 регістра 0x0020. Базовий `SetNCOIndex` (:265) користується цим методом, але Micro його перевизначає (B-09); на інших платах він тепер повертає NotSupported |
| B-21 | `Calibrate(Tx)` (SDRDevice.h:446) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:605 | `OpStatus LimeSDR_Micro::Calibrate(` | reachable→patched | Патч етапу 3: Tx → NotSupported |
| B-22 | `CalibrateTx()` — публічний член експортованого класу (`class LIME_API LimeSDR_Micro`, LimeSDR_Micro.h:33, :168) | src/boards/LimeSDR_Micro/calibrations.cpp:952 | `OpStatus LimeSDR_Micro::CalibrateTx()` | reachable→patched | Викликається з B-01 і B-21, а також напряму через символ бібліотеки. Патч: NotSupported на початку |
| B-23 | `Calibrate(Rx)` → `CalibrateRx()` | src/boards/LimeSDR_Micro/calibrations.cpp:670 | `OpStatus LimeSDR_Micro::CalibrateRx()` | internal-only | RX IQ/DC: TX-тон VSPA через внутрішню петлю (`SetupInternalLoopbackForRx`, :707; `EN_LOOPB_TXPAD_TRF`), тимчасово вмикає TXEN і AFE (`lms7002m_enable_channel_power_controls`, :302-317, виклик :437) і відновлює 0x0020 (:717). Дозволено STACK.md:128; витік вимірює лава (RX-08-hw). Тон VSPA — частина II |
| B-24 | `StreamSetup` (застарілий, SDRDevice.h:518) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:897 | `OpStatus LimeSDR_Micro::StreamSetup(` | blocked | Повертає Error (:899) |
| B-25 | `StreamCreate` з TX-каналами (SDRDevice.h:551) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:850 | `std::unique_ptr<lime::RFStream> LimeSDR_Micro::StreamCreate(` | reachable→patched | Патч етапу 3: непорожній список TX-каналів → nullptr |
| B-26 | `UploadTxWaveform` (SDRDevice.h:559) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:825 | `OpStatus LimeSDR_Micro::UploadTxWaveform(` | reachable→patched | Upstream NotImplemented; патч етапу 3 — явне NotSupported без доступу до семплів |
| B-27 | `I2CWrite` (SDRDevice.h:566) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:886 | `OpStatus LimeSDR_Micro::I2CWrite(` | reachable→patched | Сирий I2C через M4 (LMS64C): розширювач 0x20 (RX_SW2/RX_SW3/TX_SW) та інші пристрої шини LA9310. Патч: NotSupported |
| B-28 | Запис GPIOB розширювача в `LMSSetPath` | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:753 | `I2CWrite(0, i2c_expander_address, gpiob_addr, 1, &value, 1);` | internal-only | Вибір шляху RX і смуги TX у Configure/SetAntenna(Rx) (:704-751). Патч лише міняє виклик на `LMS64CProtocol::I2C_Write` (той самий кадр), бо публічний `I2CWrite` закрито (B-27) |
| B-29 | `GPIOWrite` (SDRDevice.h:589) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:840 | `OpStatus LimeSDR_Micro::GPIOWrite(` | blocked | NotImplemented (:842); `GPIODirWrite` (src/include/limesuiteng/SDRDevice.cpp:70) — NotImplemented, `GetGPIOControls` (:132) — nullptr |
| B-30 | `CustomParameterWrite` (SDRDevice.h:640) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:672 | `OpStatus LimeSDR_Micro::CustomParameterWrite(` | reachable→patched | Передає M4 будь-які id. Micro описує id 0 «VCTCXO DAC (volatile)» і id 1 — температуру, лише читання (:65-66). Патч: лише id 0 (підстроювання опорного генератора, не TX) |
| B-31 | `GetInternalChip` (SDRDevice.h:654) | src/boards/LMS7002M_SDRDevice.cpp:755 | `void* LMS7002M_SDRDevice::GetInternalChip(` | reachable→patched | Вказівник на `LMS7002M` — публічний клас (src/include/limesuiteng/LMS7002M.h:41) з `SPI_write` (:245) і `Modify_SPI_Reg_bits` (:216) в обхід усіх перевірок. Патч: виняток `std::logic_error`. Залишок — «Залишки», п. 1 |
| B-32 | `getICSR` (SDRDevice.h:699) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:943 | `ICSR* LimeSDR_Micro::getICSR()` | reachable→patched | `new LA9310_CSR` — сирий доступ до CSR LA9310 (DMA, VSPA). Патч: nullptr |
| B-33 | `LoadConfig` (SDRDevice.h:393) | src/boards/LMS7002M_SDRDevice.cpp:679 | `OpStatus LMS7002M_SDRDevice::LoadConfig(` | reachable→patched | INI-файл регістрів з будь-якими TX-полями. Патч: NotSupported. `SaveConfig` (:685) — no-TX: читає регістри й пише файл |
| B-34 | `Synchronize(toChip)` (SDRDevice.h:496) | src/boards/LMS7002M_SDRDevice.cpp:737 | `OpStatus LMS7002M_SDRDevice::Synchronize(` | internal-only | Вивантажує кеш регістрів бібліотеки; зовнішні значення потрапляють у кеш лише через захищені виклики |
| B-35 | `UploadMemory` (ARM_M4, VSPA, EEPROM; SDRDevice.h:666) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:757 | `OpStatus LimeSDR_Micro::UploadMemory(` | reachable→patched | Довільна прошивка M4/VSPA може передавати. Патч: NotSupported. Завантаження прошивок з `/lib/firmware` у конструкторі (:202-235) і VSPA у `StreamCreate` (:852-866) — внутрішні; хеші прошивок — частина II (`release_blockers` lock) |
| B-36 | `MemoryWrite` (EEPROM; SDRDevice.h:674) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:805 | `OpStatus LimeSDR_Micro::MemoryWrite(` | reachable→patched | Запис EEPROM у полі заборонено (build/07-pz-vstanovlennia.md:354). Патч: NotSupported |
| B-37 | `WriteSerialNumber` (EEPROM 0xFFF0; SDRDevice.h:691) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:1168 | `OpStatus LimeSDR_Micro::WriteSerialNumber(` | reachable→patched | Патч: NotSupported |
| B-38 | `OEMTest` (SDRDevice.h:686) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:1118 | `OpStatus LimeSDR_Micro::OEMTest(` | reachable→patched | Пише EEPROM (:1131) і запускає `RFTest` (:1072) з TX-конфігураціями `RunTxTestConfig` (:1007). Патч: NotSupported |
| B-39 | `RunTxTestConfig`/`RFTest` (публічні члени) | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:1007 | `OpStatus LimeSDR_Micro::RunTxTestConfig(` | blocked | TX вмикають лише через `Configure(tx.enabled=true)` (:1043), а це відхиляє B-01 |
| B-40 | `Reset` | src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp:499 | `OpStatus LimeSDR_Micro::Reset()` | blocked | NotImplemented (:501). Базовий `Reset` → `ResetChip` інших плат — частина II |
| B-41 | `RFStream::Transmit` на RX-потоці | src/include/limesuiteng/RFStream.h:86 | `Transmit(` | open→part-II | `StreamCreate` не створює TX-каналів (B-25); поведінка `LA9310_TRX`/`TRXLooper` з порожнім TX — аудит частини II |

## C. API `LimePlugin` (компілюється в бібліотеку завжди: src/CMakeLists.txt:91; експорт src/include/limesuiteng/LimePlugin.h:149)

| ID | Точка входу | 37cb183 файл:рядок | Якір | Вердикт | Що зроблено / чому |
|---|---|---|---|---|---|
| C-01 | `LimePlugin_Init` | src/API/LimePlugin.cpp:756 | `int LimePlugin_Init(` | reachable→patched | Трансиверний API (споживач upstream — плагін Amarisoft, у нас вимкнений). Патч: −1 |
| C-02 | `LimePlugin_Setup` | src/API/LimePlugin.cpp:1019 | `int LimePlugin_Setup(` | reachable→patched | Configure з TX, сирі SPI-записи FPGA (:1082), `LoadConfig` через `GetInternalChip` (:487). Патч: −1 |
| C-03 | `LimePlugin_Write_complex32f/16/12` → `LimePlugin_Write` | src/API/LimePlugin.cpp:1126 | `static int LimePlugin_Write(` | reachable→patched | `stream->Transmit` (:1131). Патч: −1 |
| C-04 | `LimePlugin_SetTxGain` | src/API/LimePlugin.cpp:198 | `void LimePlugin_SetTxGain(` | reachable→patched | TX-підсилення через `GetInternalChip`. Патч: нічого не робить |

## D. Застарілий C API `LMS_*` (src/legacyapi)

Опція `BUILD_LEGACYAPI` (src/legacyapi/CMakeLists.txt:13) у рецепті `OFF`, а `forbid_paths` рецепта відхиляють `*legacyapi*` і `*LimeSuite.h`, тож бібліотеки `LMS_*` немає (`blocked`). Якщо її колись зберуть для споживача (build/07 §10), кожна функція запису йде через уже захищений метод `SDRDevice`:

| ID | Точка входу | 37cb183 файл:рядок | Якір | Вердикт | Що зроблено / чому |
|---|---|---|---|---|---|
| D-01 | `LMS_Init` | src/legacyapi/LMS_APIWrapper.cpp:258 | `API_EXPORT int CALL_CONV LMS_Init(` | blocked | → `Init()`, B-02 |
| D-02 | `LMS_EnableChannel` | src/legacyapi/LMS_APIWrapper.cpp:295 | `API_EXPORT int CALL_CONV LMS_EnableChannel(` | blocked | → B-03 |
| D-03 | `LMS_SetSampleRateDir` | src/legacyapi/LMS_APIWrapper.cpp:320 | `API_EXPORT int CALL_CONV LMS_SetSampleRateDir(` | blocked | → B-14 |
| D-04 | `LMS_SetLOFrequency` | src/legacyapi/LMS_APIWrapper.cpp:379 | `API_EXPORT int CALL_CONV LMS_SetLOFrequency(` | blocked | → B-04 |
| D-05 | `LMS_SetAntenna` | src/legacyapi/LMS_APIWrapper.cpp:442 | `API_EXPORT int CALL_CONV LMS_SetAntenna(` | blocked | → B-08 |
| D-06 | `LMS_SetLPFBW`, `LMS_SetLPF` (:1243) | src/legacyapi/LMS_APIWrapper.cpp:486 | `API_EXPORT int CALL_CONV LMS_SetLPFBW(` | blocked | → B-07 |
| D-07 | `LMS_SetNormalizedGain`, `LMS_SetGaindB` (:538) | src/legacyapi/LMS_APIWrapper.cpp:517 | `API_EXPORT int CALL_CONV LMS_SetNormalizedGain(` | blocked | → B-06 |
| D-08 | `LMS_Calibrate` | src/legacyapi/LMS_APIWrapper.cpp:596 | `API_EXPORT int CALL_CONV LMS_Calibrate(` | blocked | → B-21 |
| D-09 | `LMS_SetTestSignal` | src/legacyapi/LMS_APIWrapper.cpp:610 | `API_EXPORT int CALL_CONV LMS_SetTestSignal(` | blocked | → B-10 |
| D-10 | `LMS_SetupStream` (TX) | src/legacyapi/LMS_APIWrapper.cpp:664 | `API_EXPORT int CALL_CONV LMS_SetupStream(` | blocked | → `StreamCreate`, B-25 |
| D-11 | `LMS_SendStream` | src/legacyapi/LMS_APIWrapper.cpp:948 | `API_EXPORT int CALL_CONV LMS_SendStream(` | blocked | → `Transmit` (:936), B-25/B-41 |
| D-12 | `LMS_GPIOWrite`, `LMS_GPIODirWrite` (:1067) | src/legacyapi/LMS_APIWrapper.cpp:1043 | `API_EXPORT int CALL_CONV LMS_GPIOWrite(` | blocked | → B-29 |
| D-13 | `LMS_WriteCustomBoardParam`, `LMS_VCTCXOWrite` (:1742) | src/legacyapi/LMS_APIWrapper.cpp:1105 | `API_EXPORT int CALL_CONV LMS_WriteCustomBoardParam(` | blocked | → B-30; `LMS_VCTCXOWrite` ще й `MemoryWrite`, B-36 |
| D-14 | `LMS_SetClockFreq` | src/legacyapi/LMS_APIWrapper.cpp:1171 | `API_EXPORT int CALL_CONV LMS_SetClockFreq(` | blocked | → B-05 |
| D-15 | `LMS_Synchronize` | src/legacyapi/LMS_APIWrapper.cpp:1203 | `API_EXPORT int CALL_CONV LMS_Synchronize(` | blocked | → B-34 |
| D-16 | `LMS_LoadConfig` | src/legacyapi/LMS_APIWrapper.cpp:1313 | `API_EXPORT int CALL_CONV LMS_LoadConfig(` | blocked | → B-33 |
| D-17 | `LMS_SetGFIRLPF`, `LMS_SetGFIRCoeff` (:1366), `LMS_SetGFIR` (:1403) | src/legacyapi/LMS_APIWrapper.cpp:1353 | `API_EXPORT int CALL_CONV LMS_SetGFIRLPF(` | blocked | → B-13 |
| D-18 | `LMS_WriteParam` | src/legacyapi/LMS_APIWrapper.cpp:1430 | `API_EXPORT int CALL_CONV LMS_WriteParam(` | blocked | → B-20 |
| D-19 | `LMS_SetNCOFrequency`, `LMS_SetNCOPhase` (:1483), `LMS_SetNCOIndex` (:1546) | src/legacyapi/LMS_APIWrapper.cpp:1442 | `API_EXPORT int CALL_CONV LMS_SetNCOFrequency(` | blocked | → B-09; `LMS_SetNCOPhase` ще й `WriteRegister`/`SetParameter`, B-15/B-20 |
| D-20 | `LMS_WriteLMSReg` | src/legacyapi/LMS_APIWrapper.cpp:1572 | `API_EXPORT int CALL_CONV LMS_WriteLMSReg(` | blocked | → B-15 |
| D-21 | `LMS_WriteFPGAReg`, `LMS_EnableTxWFM` (:1669) | src/legacyapi/LMS_APIWrapper.cpp:1604 | `API_EXPORT int CALL_CONV LMS_WriteFPGAReg(` | blocked | → `WriteRegister(useFPGA)`, B-15/B-16 |
| D-22 | `LMS_UploadWFM` | src/legacyapi/LMS_APIWrapper.cpp:1636 | `API_EXPORT int CALL_CONV LMS_UploadWFM(` | blocked | → B-26 |
| D-23 | `LMS_Program` | src/legacyapi/LMS_APIWrapper.cpp:1714 | `API_EXPORT int CALL_CONV LMS_Program(` | blocked | → `UploadMemory`, B-35 |

## E. Продукти збирання й інші плати

| ID | Точка входу | 37cb183 файл:рядок | Якір | Вердикт | Що зроблено / чому |
|---|---|---|---|---|---|
| E-01 | CLI: `limeTRX`, `limeSPI`, `limeConfig` та інші | CMakeLists.txt:253 | `cmake_dependent_option(BUILD_CLI` | blocked | `BUILD_CLI=OFF`, `forbid_paths` `usr/bin/*`. `limeConfig --txen` (cli/limeConfig.cpp:44, :125) — це `Configure(tx.enabled)`, B-01 |
| E-02 | `limeGUI` | CMakeLists.txt:262 | `cmake_dependent_option(BUILD_GUI` | blocked | `BUILD_GUI=OFF` |
| E-03 | Плагіни Amarisoft, gr-limesuiteng (plugins/gr-limesuiteng/CMakeLists.txt:40), HDSDR (plugins/CMakeLists.txt:48) | plugins/CMakeLists.txt:7 | `cmake_dependent_option(BUILD_PLUGINS_AMARISOFT` | blocked | Усі `OFF` у рецепті |
| E-04 | Плати LimeSDR-USB (FX3) і LimeSDR-Mini (FT601) | src/boards/CMakeLists.txt:15 | `if(LIMESUITENG_USB_FX3)` | blocked | Цей пакет ставить `LIMESUITENG_USB_FX3=OFF` і `LIMESUITENG_USB_FTDI=OFF` (опції src/comms/USB/FX3/CMakeLists.txt:41, src/comms/USB/FT601/CMakeLists.txt:38): драйверів цих плат, чиї TX-шляхи не патчено, у бібліотеці немає (src/boards/CMakeLists.txt:15-23) |
| E-05 | Плати LimeSDR-X3, XTRX, MMX8, sSDR | src/boards/CMakeLists.txt:6 | `if(LIMESUITENG_PCIE)` | open→part-II | Компілюються під тією самою опцією, що й Micro. Фабрика (src/boards/DeviceFactoryPCIe.cpp:108-120) шукає `/sys/class/limepcie` (src/comms/PCIe/LimePCIe.cpp:43), а модуля limepcie немає (`BUILD_DRIVERS=OFF`, `LIMEPCIE_DKMS=OFF`), тож на SR-RX вони недосяжні; Micro знаходить `/sys/class/la9310_limesdr` (src/boards/DeviceFactoryLA9310.cpp:26, :126). Їхні власні перевизначення не патчено; варіант частини II — патч CMake, що лишає лише LimeSDR_Micro |

## Що лишається дозволеним (RX-алоу-лист)

- **refclk:** нативний `Configure` з `referenceClockFreq`/`referenceClockSource` (LimeSDR_Micro.cpp:433-440), а також `SetClockFreq(CLK_REFERENCE)`. У модулі Soapy API тактування немає (`setClockSource`/`setMasterClockRate` SoapySDR порожні, Device.cpp:609, :574) — див. «Залишки», п. 5.
- **`--txen=0`:** нативний `Configure` з `tx.enabled=false` (LMS7002M_SDRDevice.cpp:1237); `EnableChannel(Tx, false)`; `SetParameter("TXEN_A"/"TXEN_B", 0)`; `WriteRegister(0x0020, v)` або SPI-запис 0x0020, якщо `(v & 0x000C) == 0`; у Soapy — `writeSetting("TXEN_A", "0")`/`writeSetting("TXEN_B", "0")`; відкриття Soapy саме вимикає TX (A-01), а `Init()` очищає TXEN (B-02).
- **read-back 0x0020:** `ReadRegister` (LimeSDR_Micro.cpp:594), Soapy `readRegister("RFIC0", 0x0020)` (Settings.cpp:780), `readSetting("TXEN_A")` (Settings.cpp:1147) — без змін.
- **Калібрування RX:** `Calibrate(Rx)`, Soapy `CALIBRATE_RX`/`CALIBRATE` (RX), `Configure` з `rx.calibrate` DCIQ (LimeSDR_Micro.cpp:473-478) — внутрішня петля B-23.
- Усі RX-налаштування й RX-потоки Soapy, а також читання (getters, сенсори, `readRegister`, `readSetting`) не змінено.

## Залишки та OPEN

1. **Код у тому ж процесі.** Клас `LMS7002M` публічний і експортований (src/include/limesuiteng/LMS7002M.h:41, `LIME_API` за `-fvisibility=hidden`, CMakeLists.txt:102), а `GetDescriptor().socTree` містить вказівники `DeviceTreeNode` на `LMS7002M` і LA9310 (LimeSDR_Micro.cpp:288-290). Бібліотека не може захиститися від довільного C++-коду в тому ж процесі. Структурний контроль — пакування: бібліотеку відкриває лише модуль Soapy, `limesuiteng-dev` є тільки в chroot збирача, Lime runtime заблоковано. Частина II додає перевірку `nm -D` проти рецензованого списку експорту.
2. **Плати X3/XTRX/MMX8/sSDR** (E-05) — частина II.
3. **Внутрішні шляхи** — команди VSPA і TX-тон, кільце DMA TX `la9310_limesdr`, `TRXLooper`, `ResetChip`, прошивки M4/VSPA та їхні хеші, EEPROM (`la9310->eeprom`) — частина II.
4. **Пін `LMS_TXEN`.** Прошивка M4 виставляє його високим під час ініціалізації (STACK.md:128, LimeSDR-Micro issue #1). Регістр 0x0020 тепер має TXEN_A/TXEN_B = 0 після `Init()` і після відкриття Soapy, але стан піна й фактична тиша TX перевіряються лише на лаві.
5. **refclk через Soapy** відсутній: labd не має шляху refclk без нативного виклику `Configure` або RX-only `limeConfig` (STACK.md:128). Бекенду Lime в labd немає (software/srrx/receivers.py:153), тож вибір лишається OPEN до розблокування Lime.
6. **Лава RX-08-hw:** TXEN/0x0020 після кожного configure і calibrate, кондуктивний витік на X1 ≤ −60 dBm (build/09 §12) — OPEN.
7. Аудит агентний; статус REVIEWED, `verify_build` і утримання пакетів не змінюються.

## Перевірки

- `deployment/tests/test_lime_tx_audit.py` (регресія хоста x86_64 і aarch64): кожен якір цього документа стоїть у вказаному рядку копії `upstream-fixtures/limesuiteng/` (з `SRRX_LIMESUITENG_TREE=<розпакований архів>` — і в решті файлів); кожна точка `reachable→patched` у цих файлах після патча захищена; вирізані з патченого коду захисти компілюються `g++` з мінімальними типами й відхиляють TX, сирі записи й налаштування поза алоу-листом, а RX-шляхи, `TXEN=0` і TX-off запис 0x0020 пропускають.
- `deployment/tests/test_deployment.py` `VendorPatchTests` і module lab `LIME`: патч застосовується до точних копій upstream через `vendor_patch.py`, підробка цілі відхиляється.
- `sr-rx-packages`: `limesuiteng` збирається на arm64 з цим патчем двічі (однакові SHA-256 `.deb`), пакети Lime утримано з тестового репозиторію.
- Це докази CI, а не рецензія і не апаратний PASS.
