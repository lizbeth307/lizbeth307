<!-- SR-RX-v2.1 notice 2026-10-19: STACK.md remains the source of truth -->
> **Джерело істини — [STACK.md](../STACK.md) (стек v2).** Поправки v2.1 від 19.10.2026 зафіксовано в STACK; подробиці — у [поправках v2.1](../build/12-revision-v2.1.md). Стан — [COMPLETION](../COMPLETION.md), ворота приймання — [OPEN_ITEMS](../OPEN_ITEMS.md), монтажні карти — [E5](../design/E5-connection-guide.md). Нижче — матеріал пакета v2; якщо він розходиться зі STACK.md, правильний STACK.md.
>
> **Апаратний випуск BLOCKED:** пристрій не зібрано й не випробувано. Щомісячна зарядка/балансування через ISDT 608PD та зовнішній raw-balance порт **заборонені до закриття E1-02**; J102 — DNP/service-only. Внутрішні sense-проводи Daly зберігаються. Вимкнення головного ключа або запобіжник не доводять ізоляцію B0/P−; не переносити B0 на P− і не застосовувати raw B− як обхід.
>
> **Старі габарити, маса й ціни не є чинною специфікацією закупівлі.** LAB5 змінено на D36V50F5 #4091 (25.4×25.4×9.5 mm); S-band LaNA WB + sysmocom cf2235-kt30 перенесено в зовнішній антенний вузол, а не всередину ручного корпуса. Деталі та фільтр 2170–2300 MHz — у поправках v2.1. Кошторис v2 залишається історичною оцінкою, новий перелік схеми — [11-schematic-bom.csv](../build/11-schematic-bom.csv).
>
> Власні labd/labrx, Pico/IMU/HMI і експериментальні бібліотечні патчі реалізовані як вихідний код і перевірені на хості та в ARM64 VM (ПЗ 0.3.1; [software/README](../software/README.md), [14-control-software](14-control-software.md)), але не встановлені, не прошиті й не кваліфіковані на Q6A/MCU; кваліфікованої NPU/HTP-системи немає. `readiness-contract.json` — специфікація, не працюючий GPIO-захист. Остаточні звіти й експорти формуються після фінального запуску `tools/run_checks.py --export`; точні лічильники та висновок ERC беріть із згенерованих звітів, а не з історичного тексту.

> **Стан 20.10.2026:** ПЗ керування Pico/IMU та labd/labctl реалізоване й пройшло хостові тести; див. [актуальний запуск](../software/README.md). Фізичне встановлення/приймання не виконано. Старі фрази про відсутню прошивку нижче описують етап 19.10. **Стан 23.10.2026:** офлайн-рядки таблиці самоперевірок §23 реалізує `deployment/selftest.py` з політикою `deployment/receive-only-policy.json` (DRAFT); рядки BUILDER/DEVICE/HARDWARE мають статус RUNTIME_ONLY і PASS не дають, а підсумок сьогодні BLOCKED ([офлайн-самоперевірка](../software/DEPLOYMENT.md#офлайн-самоперевірка-лише-прийом-і-приватності)). GNSS UART/RESET — [GNSS-UART](../software/GNSS-UART.md), політики labd — [SCOPE-POLICY](../software/SCOPE-POLICY.md). CI репозиторію виконує хостові регресії, CAD і module lab, але не +lab збірки нижче.

> Це план встановлення й майбутньої розробки. Команди, що посилаються на власні пакети/патчі, не означають наявність їхнього коду або успішне проходження CI.

---

# 07. Встановлення ПЗ (лише прийом)

**Документ:** 07-pz-vstanovlennia · **версія:** v2, 18.10.2026 · **одиниці:** V, A, MHz, Msps, MiB/GiB, °C
**Статус:** теоретичний проєкт — перевірити на стенді.
**Джерело істини:** STACK.md v2, розділи 1.1 (C5, C7, C11, C13, C16, C22), 2.11.1, 5.2, 5.3, 5.4, 5.5, 8, 8.1, 9.2, 11.1. Де STACK.md залишає значення відкритим — «TBD (STACK.md §x)».

Правила, що діють на кожному кроці: пристрій лише приймає; жодного ПЗ, здатного передавати; Lime TX заблоковано і навантажено на ANNE-50+; приватний вміст не декодується (лише алоу-листи); місце — лише з GNSS-фіксу, таблиць міст немає; рамкових антен і H-зондів немає.

---

## 0. Порядок робіт і передумови

| етап | коли (STACK.md 9.2) | що встановлюється |
|---|---|---|
| A | Ворота плати W1-2, день 1 (B1) | дампи SPI, ядро 6.18.2-4 з GitHub-релізу, утримання і піни −1, DKMS pps-gpio, оверлей |
| B | W1-2 далі | ланцюг A/B (маршрут A), librtlsdr2 +lab, тести V4L-0/2/3/6/7/8, дисплей, PPS, UART, I2C, NPU Phase 0 |
| C | після W1-2 | рушії й декодери за алоу-листами, сервіси lab*, CI і самоперевірки |
| D | після доставки Lime (15.12.2026) | LimeSuiteNG 37cb183 із заблокованим TX, la9310 DKMS, перевірка SoapySDRUtil до першого RX |

Передумови (5.4, 9.2 крок 1):
- Плата живиться 12 V від лабораторного джерела з обмеженням струму в J21; USB-C Q6A при підключеному J21 не під'єднувати; EDL лише з живленням J21 (кабель A-A, 05c6:9008).
- Консоль — debug UART на пінах 8/10 (Raspberry Pi Debug Probe SC0889); F2/F12 UEFI по UART.
- Режими UEFI «Radxa Platform Configuration → GPIO → QUPV3»: SE0/SE2 = I2C, SE6/SE7 = UART; записати разом із дампом SPI (5.2).
- Ніколи не запускати rsetup System Update чи Update SPI Bootloader; у полі — без full-upgrade, rsetup чи rupdate (5.4).

### 0.1. День 1: SPI і BIOS (9.2 крок 1)

1. До будь-чого іншого — два повні сирі дампи SPI; обидва мають однаковий SHA-256 і розмір 33,554,432 B.
2. Ніколи не прошивати через rsetup/setup.sh. Перепрошивати лише якщо BIOS старіший за 20251230 або це 260916 — через EDL образом 260120 — із сервісного ПК окремою збіркою **edl-ng v1.6.0** (edl-ng-dist-v1.6.0.zip з архіву відновлення; не deb edl-ng 1.4.1, утриманий на платі), два повні читання (33,554,432 B) з однаковим SHA-256 (STACK.md 1.2, 5.4).
3. Цільова прошивка: SPI BIOS 6.0.260120; пакети edk2-qcs6490 і edk2-radxa-dragon-q6a 0.1.0-5 (sha256 deb `2a311f20d32ab814b6e624b304011cca822d1bbf3ece0a5904f8b43b3de951ae`), 0.1.0-7 — лише в архіві (5.4).

---

## 1. Базова система і ядро (STACK.md 5.4 «Базова система», «Утримання»)

Образ: Radxa OS r2 (noble). Утримуване ядро: **linux-image-6.18.2-4-qcom**. В індексі apt Radxa (dists/qcs6490-noble) лише 7.0.11-7, а 6.18.2-4 і 6.18.2-3 повертають 404, тому деби беруться лише з GitHub-релізу **radxa-pkg/linux-qcom «Release 6.18.2-4» (16 активів)**.

### 1.1. Завантаження і перевірка

| пакет | розмір, B | sha256 |
|---|---|---|
| linux-image-6.18.2-4-qcom | 68,282,992 | `0bbdbfda97627a0e51afefb3d0aa7dc23c3658151e5f14aee24c276d0bb7fbeb` |
| linux-headers-6.18.2-4-qcom | 9,025,048 | `696e4279fe530e6974c5b3e388e41f82e6c02aa617cbe009115561f4a74fef2d` |
| linux-image/headers-radxa-dragon-q6a 6.18.2-4 | TBD (STACK.md 5.4: хеш не наведено) | TBD (STACK.md 5.4) |

```sh
# 1) завантажити всі 16 активів релізу 6.18.2-4 у /srv/kernel-6.18.2-4/ (ім'я файлів — як у релізі)
cd /srv/kernel-6.18.2-4
sha256sum linux-image-6.18.2-4-qcom_*.deb linux-headers-6.18.2-4-qcom_*.deb
#    порівняти з таблицею вище; розбіжність = стоп
# 2) локальний apt-репозиторій (дзеркало aptly linux-image/headers 6.18.2-4) на пристрої + копія поза пристроєм
# 3) встановити ДО будь-якого apt upgrade
sudo dpkg -i linux-image-6.18.2-4-qcom_*.deb linux-headers-6.18.2-4-qcom_*.deb \
             linux-image-radxa-dragon-q6a_6.18.2-4*.deb linux-headers-radxa-dragon-q6a_6.18.2-4*.deb
sudo apt-mark hold linux-image-6.18.2-4-qcom linux-headers-6.18.2-4-qcom
```

- 6.18.2-3 (з образу r2) лишається рятувальним записом і запасним варіантом для NPU.
- 7.0.11-7 — лише після тестів HDMI (тема 31304), FastRPC/NPU, PPS і EDID; apt ніколи не підтягує його в слот A чи B (пін −1 на `linux-image-7.*`, `linux-headers-7.*`).

### 1.2. Утримання (apt-mark hold + пріоритет aptly 1001)

| група | пакети і версії (5.4) |
|---|---|
| BIOS/відновлення | edk2-qcs6490, edk2-radxa-dragon-q6a 0.1.0-5; edl-ng 1.4.1 (deb Radxa на платі; EDL-читання і прошивання — лише із сервісного ПК збіркою edl-ng v1.6.0, edl-ng-dist-v1.6.0.zip в архіві відновлення); rsetup, rsetup-config-first-boot 0.4.26 |
| завантажувач | embloader (маршрут B — 0.4; маршрут A — ще й −1); systemd-boot і systemd-boot-efi на одній віддзеркаленій версії (255.4-1ubuntu8.18 з noble-security або 8.12 з r2); u-boot-menu 4.2.3ubuntu1; radxa-overlays-dkms 0.2.18 |
| прошивки | radxa-firmware і radxa-firmware-qcs6490 0.2.29 (якщо Phase 0 не обере 0.2.42); linux-firmware 20240318.git3b128b60-0ubuntu2.23; linux-firmware-dragonwing 1.0.0+20251203; qcom-iot-defaults 1.19 |
| системна конфігурація | radxa-system-config-* 0.6.30 (у 0.7.4 postinst дописує clk_ignore_unused); task-qcs6490, task-qualcomm, task-qualcomm-npu, task-qualcomm-gstreamer 0.1.0-7; task-radxa-dragon-q6a 0.4.42; alsa-ucm-conf 1.2.14-1radxa2; aic8800-usb-dkms, aic8800-firmware 4.0+git20250410.b99ca8b6-5 |
| QNN | qcom-qnn-sdk-v68 0.1.0-2, radxa-qcom-qairt 0.1.0-2 (QAIRT 2.42.0.251225) |
| графіка | Mesa 25.2.8-0ubuntu0.24.04.4; libdrm2 2.4.125-1ubuntu0.1~24.04.2; labwc 0.7.4+lab1 (відкат 0.7.1-1build1); XWayland 2:23.2.6; wlroots (noble libwlroots 0.17.1-2.1build1); qt6 6.4.2; pipewire |
| радіо | librtlsdr2 2.0.3-0+lab1; libairspyhf1 1.6.8-4build1; libairspy0 1.0.10-3build1 (лише якщо куплено Airspy Mini за воротами G6 #12; відкриває лише labrx); gpsd 3.25-3ubuntu3.2; chrony 4.5-1ubuntu4.2 |
| FastRPC | набір, обраний матрицею Phase 0 — TBD (STACK.md 5.4, Phase 0) |

Після утримання: `unattended-upgrades` прибрати; таймери apt і fwupd замаскувати; brltty видалити; ModemManager замаскувати (5.4).

```sh
sudo apt-get purge unattended-upgrades brltty
sudo systemctl mask apt-daily.timer apt-daily-upgrade.timer fwupd-refresh.timer ModemManager.service
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
# /etc/systemd/logind.conf: IdleAction=ignore, HandlePowerKey=ignore (labpowerd обробляє KEY_POWER)
```

---

## 2. Пакування і піни apt (STACK.md 5.4 «Пакування», «Закріплено на −1»)

- Одне джерело apt — одна підписана публікація aptly (deb +labN з тегованих комітів на arm64-збирачі). Пін — на дзеркалі aptly, на пристрої і на збиральному хості.
- Списки PPA, які додає rsdk (ubuntu-qcom-iot/qcom-ppa, kisak/turtle, ppa:mozillateam), видаляються при першому завантаженні; перевірка — `ls /etc/apt/sources.list.d`.
- Кожен вихідний пакет +lab збирається у власному chroot sbuild (libhamlib-dev — лише в chroot lab-wsjt-decoders; chroot SDRangel — без libhamlib-dev, libdsdcc, libmbe, libcodec2-dev; chroot Gpredict — без libgps-dev і libhamlib-dev).
- Сторонні deb дзеркаляться: OpenWebRX+ 1.2.126, linux-image/headers 6.18.2-4-qcom, прошивки radxa, qcom-qnn-sdk-v68.

```text
# /etc/apt/preferences.d/lab.pref  (пріоритети — STACK.md 5.4)
Package: *
Pin: release o=<origin лабораторних +labN>      # назва origin — TBD (STACK.md 5.4 її не задає)
Pin-Priority: 1001

Package: *
Pin: release o=<origin віддзеркаленого знімка>   # noble, noble-updates, noble-security, підмножини OpenWebRX+, radxa noble, qcs6490 — TBD назва
Pin-Priority: 990

Package: *
Pin: origin *
Pin-Priority: -1
```

Піни −1 за шаблоном (`Package: <шаблон>` / `Pin: release *` / `Pin-Priority: -1`), щоб нові пакети кодеків і драйверів лишалися заблокованими:

| група | пакети |
|---|---|
| Hamlib/WSJT/TX | wsjtx, libhamlib4t64, libhamlib-utils, libhamlib-dev, fldigi, qsstv, direwolf, js8call, python3-js8py |
| Soapy/Lime | soapysdr-module-all, soapysdr0.8-module-all, soapysdr0.8-module-remote, -lms7, -hackrf, -bladerf, -uhd, -redpitaya, `libsoapysdr0.9*`, limesuite, limesuiteng-gui, gr-limesuiteng (і limesuiteng-cli, якщо його TX-підкоманди не вилучено при компіляції) |
| RTL | librtlsdr0, librtlsdr2 (= 2.0.1-2build1) |
| декодери OpenWebRX+ | rtl-433, `digiham*`, python3-digiham, `codecserver*`, `codecserver-driver-*` (ambe3k, all), acarsdec, dumphfdl, dumpvdl2, libacars-tools / `libacars*`, dump1090-fa, dump1090-fa-minimal, `dump978-fa*`, skyaware978, `dxlaprs-tetra*`, dxlaprs-lora, python3-meshtastic, python3-bleak, m17-demod, nrsc5, hpsdrconnector, dream (якщо не власна RX-only збірка) |
| інше | multimon-ng (європейська збірка), lame, python3-paho-mqtt, gr-gsm, gr-iridium, kalibrate-rtl, urh |
| замінені пакети noble | gpredict (= 2.3-115-g0f3beb6-3build3), gr-satellites (= 5.5.0-2build2) |
| Qualcomm/Mesa/ядро | `qcom-fastrpc*`, linux-firmware-dragonwing 20260825, `qairt-*` (зокрема qairt-dsp-binaries 2.49.0), `libqnn*`, `libsnpe*`, qnn-tools, snpe-tools, `qcom-adreno*`, dragonwing-defaults, firmware-qcom-audioreach, firmware-qcom-soc, linux-firmware-qualcomm-misc, `hexagon-dsp-binaries*`, firmware-qcom-dsp, mesa ≥ 26, `linux-image-7.*`, `linux-headers-7.*`, `edk2-*` (≥ 0.1.0-8), embloader (маршрут A) |
| за походженням | LP-PPA-ubuntu-qcom-iot-qcom-ppa, LP-PPA-kisak-turtle, LP-PPA-mozillateam |

Перевірка (CI, 5.4): `apt-get -s dist-upgrade` показує 0 змін проти повного початкового списку джерел; жодного походження launchpad; `apt policy` дає −1 для пакетів QNN/QAIRT/прошивок із qcom-ppa; `dpkg -V` чистий для пакетів прошивок і FastRPC.

---

## 3. Ланцюг завантаження A/B (STACK.md 5.4, 5.5 «Сховище»)

Розмітка UFS 128 GB (близько 119 GiB), 4K-native (образ _4096 або sgdisk на пристрої):

| розділ | розмір | примітка |
|---|---|---|
| ESP | 1 GiB | FAT32, `mkfs.vfat -S 4096` |
| root A | 22 GiB | systemd-boot, лічильник спроб, рятувальний пункт |
| root B | 22 GiB | новий UUID файлової системи |
| /data | решта (близько 74 GiB) | квоти 27.4 GiB, записи близько 46.6 GiB |

### 3.1. Маршрут A (основний; на цьому стеку ще не підтверджено — перевірити на образі)

```sh
sudo apt purge sdboot-is-embloader          # повертає бінарник .distrib
sudo bootctl install
# embloader — пін −1; systemd-boot і systemd-boot-efi — hold на одній віддзеркаленій версії
echo 3 | sudo tee /etc/kernel/tries          # + boot-complete.target; systemd-bless-boot благословляє після самоперевірки
# об'єднаний DTB (базовий DTB ніколи не перезбирається):
fdtoverlay -i /dtbs/6.18.2-4-qcom/qcom/qcs6490-radxa-dragon-q6a.dtb -o lab.dtb lab-q6a.dtbo
#   польовий варіант — field.dtb з польовим оверлеєм (pcie0 disabled)
```

- Записи BLS Type #1 пише лише власний плагін kernel-install (ніколи rsetup); кожен — з явним рядком `devicetree` на lab.dtb або field.dtb. Рядки `devicetree-overlay` на цьому маршруті не діють (systemd-boot 255 їх ігнорує). Без UKI.
- Токени записів labA/labB для кожного слота, `root=PARTUUID`, скінченний timeout, редактор вимкнено; 6.18.2-3 — рятувальний запис.

### 3.2. Маршрут B (запасний, неперевірений)

Утримано embloader 0.4 з пробним «write-back default» у loader.conf як userspace-прапорцем A/B (оновлення ставить default на B, initramfs B одразу повертає A, B закріплює себе лише після boot-complete); зависання до boot-complete скидає супервізор Pico; збій до initramfs потребує рятувальної microSD.

### 3.3. Перевірки

| перевірка | прохід |
|---|---|
| `sha256sum /sys/firmware/fdt` | = об'єднаний DTB (DTB пакета + оверлеї) |
| `/proc/device-tree` у польовому профілі | pcie0 disabled |
| тест B3 (примусова помилка) | відкат на A; при провалі — маршрут B (9.2 крок 1) |
| fio після будь-якої зміни DT | без помилок |
| 20 холодних завантажень з карткою даних і накопичувачем LAB | усі на UFS (на носіях даних ESP немає) |

---

## 4. Командний рядок ядра (STACK.md 5.4)

Через /etc/kernel/cmdline і kernel-install. Файл містить **повний** базовий рядок r2 точно таким, яким його записано при першому завантаженні (`console=ttyMSM0,115200n8 … rw earlycon consoleblank=0 console=tty1 coherent_pool=2M irqchip.gicv3_pseudo_nmi=0 cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory swapaccount=1 kasan=off`; `root=PARTUUID` для кожного слота), а за ним — лабораторні додатки:

```
preempt=full drm.edid_firmware=HDMI-A-1:edid/field.bin video=HDMI-A-1:1920x1080@60 panic=10 usbcore.usbfs_memory_mb=0
# збірка з Lime (за замовчуванням):
pcie_aspm=off isolcpus=nohz,domain,managed_irq,7 nohz_full=7 rcu_nocbs=7 irqaffinity=0-6
# (запасна збірка без Lime — без рядка вище)
```

- Без `clk_ignore_unused`. EDID — в initramfs. Режими 59.986/51.677 Hz закріплює kanshi; `video=` впливає лише на консоль.
- CI: SHA-256 /etc/kernel/cmdline і /proc/cmdline.

---

## 5. Оверлей lab-q6a.dtso і піни (STACK.md 5.2, 5.4; C6, C13)

### 5.1. Вміст

| фрагмент | джерело | піни 40-pin | призначення |
|---|---|---|---|
| uart6 (spi6/i2c6 вимкнено, qup_uart6_tx/rx, okay) | radxa-overlays 0.2.31 | 16/18 | LC76G; alias `serial1 = …/serial@998000` → /dev/ttyHS1 |
| uart7 (взаємовиключний зі spi7/i2c7/gpio30/31) | radxa-overlays 0.2.31 (у 0.2.18 образу r2 його немає) | 32 TX / 29 RX | Pico; alias `serial2 = …/serial@99c000` |
| i2c0, 100 kHz | radxa-overlays 0.2.31 | 13/15 | лише INA228 (0x40 або 0x45) |
| i2c2, 100 kHz | radxa-overlays 0.2.31 | 27/28 | MCP23017 #1 0x20, #3 0x22, #4 0x23 (A2..A0 = 011, STACK.md 5.2), INA3221 0x41 і 0x43, TCA9517 до LAB BUS |
| вузол `compatible = "pps-gpio"`, `gpios = <&tlmm 96 GPIO_ACTIVE_HIGH>` | власний | **пін 7 (GPIO96)** | PPS LC76G, дріт ≤20 см |
| польовий варіант: `pcie0` disabled; gpio-hog WIFI_PWR_EN output-low | власний | — | лінія TLMM WIFI_PWR_EN — TBD (STACK.md 5.2: знайти у W1-2) |
| опційно FastRPC: `memory-region = <&adsp_rpc_remote_heap_mem>`, shared-dma-pool @0xc6500000, 8 MiB | власний | — | лише якщо Phase 0 покаже, що змінює результати |

- Шляхи вузлів aliases взяти з /proc/device-tree. Прапорець `qcom,enable-gsi-dma` нічого не робить (qcom_geni_serial його ігнорує).
- libgpiod адресує лінії за міткою чипа TLMM (gpiochip4), ніколи за номером.
- Готового оверлею pps-gpio в upstream немає (radxa-overlays e713889).

### 5.2. DKMS pps-gpio (C13)

- Джерело: radxa/kernel 559f4f9 drivers/pps/clients/pps-gpio.c; пакет +labN для 6.18.2-4 (CONFIG_PPS=y, PPS_CLIENT_GPIO не задано).
- Збирати gcc-12 (`MAKE[0]` з `CC=gcc-12`; ядро зібране Debian gcc 12.2.0; MODULE_SIG вимкнено); перевірити `modinfo pps-gpio | grep vermagic` проти 6.18.2-4-qcom.
- Запасний Route A — GPIO v2 ioctl з EVENT_CLOCK_REALTIME, ніколи разом з pps-gpio.

### 5.3. Перевірки на запуску (9.2 крок 1)

```sh
cat /sys/kernel/debug/pinctrl/*/pinmux-pins | grep -E 'gpio96|pin 96'   # власник лише pps-gpio
ls -l /dev/lab/gnss /dev/lab/pico /dev/pps-gnss
i2cdetect -l                                                            # номери шин I2C0 / I2C2 (N0, N2 — TBD, STACK.md 5.2 їх не задає)
i2cdetect -y -r N0 ; i2cdetect -y -r N2                                 # адреси, не UU
```

| перевірка | прохід |
|---|---|
| UART6 TX→RX перемичкою | без помилок, також на 921600 |
| UART7 | оверлей завантажено; якщо TX мертвий (#31422) — режим FIFO або H1 USB-CDC |
| I2C0, I2C2 | 1e6 читань кожна, нуль помилок |
| aliases | стабільні ttyHS1/ttyHS2 за 20 перезавантажень |
| pinmux-pins | у кожного піна один власник (UART6 проти GPIO24/25; піни 29/32) |
| dmesg UART6 | без помилок прошивки |

---

## 6. NPU/FastRPC (STACK.md 5.4 «Золотий набір»)

- Золотий набір визначається лише за SHA-256 і береться лише з radxa-firmware-qcs6490 (не з linux-msm/hexagon-dsp-binaries). Кандидати 0.2.29 і 0.2.42 — вибір матриці Phase 0: TBD (STACK.md 5.4, розділ 8).
- Userspace fastrpc 1.0.4-1 (GitHub-реліз) або 1.0.7-3 — увесь набір (fastrpc, libcdsprpc1, libadsprpc1, libsdsprpc1, lib{a,c,s}dsp-default-listener1, fastrpc-dev, fastrpc-test) ставиться **до** qcom-qnn-sdk-v68, потім hold.
- Для 1.0.4-1 постачаємо udev `KERNEL=="fastrpc-*"` і `dma_heap/*` з `GROUP="fastrpc" MODE="0660"` плюс групу через sysusers.d.
- Один спосіб завантаження DSP: власний хук initramfs lab-dsp-fw для 0.2.29 (копіює `{adsp,cdsp}.mbn`, `*.jsn`, a660_zap.mbn, перевіряє SHA-256); для 0.2.42 — лише його хук. Файли DSP ніколи не копіюються вручну.
- Перед кожним update-initramfs і стартом NPU: `dpkg -V radxa-firmware-qcs6490 fastrpc libcdsprpc1` — чисто; `dpkg -S` — один власник.
- QAIRT 2.42.0.251225 з qcom-qnn-sdk-v68 0.1.0-2 (44,221,844 B); ніколи onnxruntime-qnn через pip; QAIRT 2.49 — −1.

---

## 7. librtlsdr2 2.0.3-0+lab1 і ворота bias (STACK.md 5.4, 5.3; C11, C21)

### 7.1. Рецепт збірки

| параметр | значення |
|---|---|
| upstream | osmocom v2.0.3 (797f814) з відкатом 7ebcb04 |
| SONAME / API | librtlsdr.so.2, ті самі 37 експортів rtlsdr_*, заголовки без змін з 2.0.1 |
| пакування | debian/ з noble, буквально `-DENABLE_ZEROCOPY=OFF -DDETACH_KERNEL_DRIVER=ON` (змінна DEB_ZEROCOPY_OPTION у noble розгортається неправильно) |
| лабораторний патч | (a) ворота лише для GPIO0; (b) GPIO0=0 наприкінці rtlsdr_open і в rtlsdr_close; (c) порт d80421b — лише за термічними воротами V4L-5 |
| запасний варіант | noble 2.0.1 (420086a) + 65f06585 + 0204c9cf з тим самим патчем = librtlsdr2 2.0.1-2build1+lab1 |
| після встановлення | `apt-mark hold librtlsdr2`; rtl_biast через dpkg-divert; обгортка rtl_eeprom (лише -r, -s і відновлення -m/-p) |
| ніколи | форк rtl-sdr-blog; rtl_tcp у польових профілях (інакше лише 127.0.0.1) |

Ворота bias — лише всередині `rtlsdr_set_bias_tee_gpio()` (і `rtlsdr_set_bias_tee`, що йде через GPIO0):

```c
if (gpio == 0 && on && access("/run/labd/bias/<serial>", F_OK) != 0) return -1;
/* GPIO5 (перемикач входів V4L вище 28.8 MHz) і кожен запит «off» проходять без воріт */
```

- Токен — наявність файлу **/run/labd/bias/<serial>** у власності root, який пише лише labd (STACK.md 5.4); ніколи не змінна оточення. Це ворота політики, не межа безпеки; шаром безпеки лишаються апаратні DC-sense і eFuse.

```sh
cat >/etc/modprobe.d/lab-rtl-blacklist.conf <<'EOF'
blacklist dvb_usb_rtl28xxu
blacklist rtl2832
blacklist rtl2830
blacklist r820t
EOF
sudo dpkg-divert --local --rename --add /usr/bin/rtl_biast
```

### 7.2. Серійні номери (STACK.md C21, 8.1 V4L-4)

| SDR | серійний номер | порт |
|---|---|---|
| RTL-A | LABRXA | синій порт J5 нижній без Lime / CH334F H2 з Lime |
| RTL-B | LABRXB | J5 верхній (FE1.1s P1) |
| запасний V4L | LABRXC | LAB USB-A (H3) |

```sh
rtl_eeprom -d 0 -s LABRXA        # через обгортку; лише -s і відновлення -m/-p
rtl_test -d LABRXB               # з трьома підключеними відкриває потрібний екземпляр
```
Шаблон `^LAB[A-Z]{3}$`; кожна конфігурація рушіїв вибирає SDR лише за серійним номером; udev /dev/lab/<name>. На прийманні: біт 0x02 байта 7 EEPROM = 1 (5.3).

### 7.3. Перевірки (5.4, 8.1 V4L-0..V4L-8, 9.2 крок 1)

| тест | прохід |
|---|---|
| журнал збірки | містить «zero-copy support disabled» |
| `strings librtlsdr.so.2 \| grep -c zero-copy` | 0 |
| `objdump -p` / `nm -D` | SONAME librtlsdr.so.2 / 37 експортів rtlsdr_* |
| `ldd` кожного споживача RTL (rtl_connector, labrx, SDR++, SDRangel тощо; SatDump RTL не відкриває — лише net_source з labrx) | веде до лабораторної .so.2 |
| stderr самотесту | ніколи «Allocating 15 zero-copy buffers» |
| без токена: 7 → 137.1 → 145.8 → 437.55 → 1090 → 7 MHz; 100/400/1090 MHz; offset tuning | rc==0, входи перемикаються, пін bias < 0.1 V (шина bias 0 V) |
| при підключенні без токена | 0 V на bias; `lsmod \| grep rtl28` порожній |
| V4L-6: 30 хв `rtl_test -s 2560000` на кожному порту | 0 втрачених байтів |
| V4L-7 | `lsusb -t` — V4L на 480M; VBUS на кінці подовжувача ≥4.75 V при 2.56 Msps |
| V4L-8: зняти VBUS (GPA2/GPA3) посеред потоку | сторож labrx закриває, знімає VBUS на 1 с, відкриває за серійним |
| ідентифікація | у лозі «Found Rafael Micro R820T tuner», потім «RTL-SDR Blog V4 Lite Detected» |

---

## 8. libairspyhf і HF+ (STACK.md 5.4 «Інше з apt»)

- За замовчуванням: **noble libairspyhf1 / airspyhf / libairspyhf-dev 1.6.8-4build1** (справжня 1.6.8, soname 1), hold, дзеркало 990.
- Опція (не за замовчуванням): бекпорт Debian 1.6.8-5 (87cf12a) = upstream 1.8.1 як 1.6.8-5~lab1 — лише разом з перезбіркою airspyhf tools, SoapyAirspyHF, SDR++, SDRangel, SatDump, AIS-catcher і labrx у тому самому знімку; символи API bias-tee є лише в збірці 1.8.1; `airspyhf_set_bias_tee` — лише в тестах.
- Ніколи upstream `make install` (SOVERSION 0); ніколи коміт з вікна e1dcc17..0130450^.
- udev: `ATTR{idVendor}=="03eb", ATTR{idProduct}=="800c", GROUP="plugdev", TAG+="uaccess"`; labrx і sdrangel — у plugdev.
- Airspy Mini (лише за воротами G6 #12, STACK.md 2.11.3): libairspy0 1.0.10-3build1 (noble arm64), відкриває лише labrx (libairspy додано до labrx); SatDump отримує cf32 через net_source на 127.0.0.1, плагін airspy SatDump не збирається; bias-T Mini вимкнено (airspy_set_rf_bias — лише за токеном labd); soapysdr0.8-module-airspy не потрібен (STACK.md 11.1).
- Корекції ppm у labrx немає: ppb з флешу застосовує libairspyhf. labd пише LOppmTenths = round(ppb/100) у пресети AirspyHF SDRangel через REST і зчитує назад; частоту 256000 в OpenWebRX+ заборонено.

---

## 9. SoapySDR (STACK.md 5.4)

| пакет | версія | примітка |
|---|---|---|
| SoapySDR | 0.8.1-4build1 | ніколи не змішувати з 0.9 (`libsoapysdr0.9*` — −1) |
| SoapyRTLSDR | 0.3.3-1build1 | на +lab .so.2 |
| SoapyAirspyHF | тег soapy-airspyhf-0.2.1 (0b3daf0) +lab | проти SoapySDR 0.8.1 |
| limesuiteng-soapysdr | з пакування LimeSuiteNG, пропатчений | лише збірка з Lime |
| soapysdr-module-all, -remote, -lms7, -hackrf, -bladerf, -uhd, -redpitaya | — | −1; SoapyRemote заборонено |

Перевірка: `SoapySDRUtil --info` показує лише rtlsdr, airspyhf і пропатчений модуль LimeSuiteNG; `SOAPY_SDR_PLUGIN_PATH` не задано в жодному unit.

---

## 10. LimeSuiteNG з заблокованим TX (STACK.md 5.4 «Lime залишено», 5.3; 9.2 крок 12)

```sh
git clone <LimeSuiteNG> && cd LimeSuiteNG
git checkout 37cb1833e35955f7072c0fb91642d14ae5515f28     # limesdr-micro-staging (або пізніший закріплений)
# + патч, що валить TX setupStream (Lime TX заблоковано)
cmake -B build -DBUILD_PLUGINS_AMARISOFT=OFF -DBUILD_GUI=OFF
```

- З пакування — лише liblimesuiteng (+ патч блокування TX), limesuiteng-soapysdr, limesuiteng-udev, limepcie-dkms; limesuiteng-legacyapi — лише якщо потрібна споживачу; limesuiteng-cli — лише з вилученими при компіляції всіма TX-підкомандами; limesuiteng-gui, gr-limesuiteng — ніколи; решта — −1.
- la9310_limesdr 0.2.1 + la9310_uart_module 1.0.0 — локальний DKMS +lab, зібраний GCC проти linux-headers-6.18.2-4-qcom; вантажиться при завантаженні (modalias).
- /lib/firmware: limesdr-micro-m4.bin і limesdr-micro-iqplayer.eld — у пакеті +lab з перевіркою хешів; limesdr-micro-eeprom.bin — ніколи. Хеші — TBD (STACK.md 5.4: «закріплені», значень не наведено).
- У полі — жодних записів EEPROM/завантажувача чи limeFLASH; заборонені limeSPI, limeI2C, limeCSR, limeOEM, limeFLASH, limeVSPA, limePPSDO, limeGUI, limeTRX --input/--repeater.
- labd після кожного configure/calibrate повторно задає `--txen=0` і зчитує регістр 0x0020; не вмикає живлення/потік нижче 0 °C за TMP1075; частоти дискретизації нижче **7 Msps** відхиляються (профілів Lime нижче 7 Msps немає; STACK.md 2.11.1, 5.3); перед від'єднанням — внутрішня опорна.
- Живлення Lime — шина LIME3V3 через ключ TI TPS259470ARPWR (EN — MCP23017 #4 GPA0, FLT — MCP #4 GPB3, адреса 0x23; STACK.md 2.11.1, 5.2). Після завантаження EN низький (100k до землі): Lime знеструмлена, labd вмикає її і пересканує PCIe. Відновлення після зависання (sysclk нижче 30 MHz може завісити DMA VSPA): labd спершу розриває PCIe-лінк, потім перемикає LIME3V3; VCC_3V3_MKEY слота Q6A не перемикати. Приймання: примусове зависання → відновлення перемиканням живлення; FLT не спрацьовує на 20 ввімкненнях.
- Райзер — Gen2; Gen3 — лише після 60-хв приймального тесту без помилок AER. L-4/P7 — лише з прошивкою ≥1f70189.
- CI падає на будь-якому amarisoft .so.

---

## 11. SatDump (STACK.md 5.4 «Дозволені декодери», «Доступ до SDR»)

SatDump не відкриває жодного SDR: його зібрано без апаратних джерел SDR і без мережевих SDR-серверів, єдиний живий вхід — net_source з labrx (за замовчуванням — декодування записаного файлу labrx).

```sh
# рецепт: deployment/recipes/satdump/recipe.json (стан PENDING_BUILDER; check_recipe.py check | verify-source | package)
# джерело: архів 1aedd602055c154401384a8cc7876713bb371254 із sha256 sources.lock.json; patches/0001 = c0b6f88, 0002 = 6b5957f, 0003 = +lab bind 127.0.0.1
patch -p1 < patches/0001-cli-add-option-c0b6f88.patch   # далі 0002 і 0003; 96bb626 (лише HRIT) у рецепт не входить
cmake -S . -B build -G Ninja -DPLUGINS_ALL=OFF -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib \
  -DPLUGIN_METEOR=ON -DPLUGIN_NOAA_METOP=ON -DPLUGIN_AWS=ON \
  -DPLUGIN_ELEKTRO_ARKTIKA=ON -DPLUGIN_XRIT=ON -DPLUGIN_FY2=ON \
  -DPLUGIN_NET_SOURCE_SDR_SUPPORT=ON  # і кожна з решти 105 опцій 1aedd60 поіменно: recipe.json cmake.definitions
# на 1aedd60 PLUGINS_ALL типово ON, а SDR-джерела, PORTAUDIO/AAUDIO sink, TOOLS/WIPSETTINGS/WEBHOOK/EXPERIMENTAL — option(... ON), тож OFF задано явно
# пакет 2.0.0~alpha+git20260929+lab1 (без inmarsat_support); -j4 із zram, без мережі (unshare --user --map-root-user --net)
```

| вимкнено (OFF) | |
|---|---|
| плагіни | 47 опцій під PLUGINS_ALL, ON лише METEOR, NOAA_METOP, AWS, ELEKTRO_ARKTIKA, XRIT, FY2; OFF — зокрема GK2A, FY3, FY4, GOES, METOPSG, ANALOG, CUBESAT, RADIOSONDE, HIMAWARI, GEONETCAST; ніколи INMARSAT, ORBCOMM, DMSP, WSF, SPACEX, BLUEWALKER3 |
| sdr_sources | 24 опції: усі апаратні PLUGIN_*_SDR_SUPPORT (на 1aedd60 здебільшого типово ON), Soapy, SDDC, HAROGIC, RTAUDIO, SPYSERVER, RTLTCP, SDRPP_SERVER, REMOTE_SDR; ON лише NET_SOURCE |
| застосунки | EXPERIMENTAL_DEVICES, WEBHOOK_APP, TOOLS_APP, WIPSETTINGS_EDITOR_APP, BITVIEW_APP, WIPTRACKING_APP, SCRIPTING, BOCHUM; SIMD_SSE41/AVX2/NEON (simd_neon немає в алоу-листі плагінів STACK; вмикати — лише рішенням після заміру CPU на Q6A); без autotrack і satdump_sdr_server; `*_sdr_sink`, PORTAUDIO/AAUDIO/RTAUDIO sink |

- Алоу-лист конвеєрів поіменно: лише Meteor-M.json, MetOp.json, AWS.json, FengYun-2.json і Elektro_Arktika.json (з вилученим elektro_ggak_mqtt); конвеєри GOES, GK-2A і FY-4 у європейську збірку не входять; жодних інших JSON чи .json.inc (крок `package` рецепта видаляє решту `share/satdump/resources/pipelines`). Приховано: Cosmos-2558 dump, DMSP RTD, Yunhai AHRPT, syracuse3_tlm, wsf_m_db, angels_l_band і все військове або шифроване.
- Вхід: файл labrx — лише вузький baseband LRPT ci16 256 kS/s за політикою v2.1 (`satdump pipeline <id> baseband <файл> <вихід> --samplerate=256000 --baseband_format=cs16`, srrx.satdump_pass); наживо — `satdump legacy live <id> <вихід> --source net_source --mode udp --port P --samplerate 256000 --frequency F --timeout T` (legacy-парсер 1aedd60 читає лише «--key value»), cf32 UDP від labrx після масок, ≤8188 відліків на датаграму (8192 × 8 B > 65 507 B); net_source на 1aedd60 слухає INADDR_ANY, тож localhost тримає unit (IPAddressDeny=any + IPAddressAllow=localhost), а +lab patch 0003 — другий шар.
- satdump_cfg.json: крок `package` пише строгий JSON: `satdump_general.kepler_update_interval` = «Never», `kepler_settings.urls_to_fetch` і `norads_to_fetch` порожні; запис вимкнено (record off); TLE/OMM постачає labd (CSV на 17 стовпців або JSON) — передачу в unit ще не реалізовано (BUILDER omm-csv).
- Unit проходу: один transient `systemd-run` (srrx.satdump_pass.unit_properties): користувач srrx-satdump, порожній root-owned WorkingDirectory /var/lib/srrx-satdump/empty, HOME — приватний RuntimeDirectory (без pipelines.json і конфігу користувача), /data — порожній tmpfs з одним baseband лише для читання, ProtectHome=yes, LC_ALL=C.UTF-8, PrivateNetwork=yes для файлу (наживо — IPAddressDeny=any з входом лише з localhost), провал при «CALCEPH ERROR»; після будь-якої спроби декодування baseband видаляється.
- Повтор LRPT на CADU: `dd bs=8192 skip=4` (#1212) — перевірка BUILDER.
- CI на arm64 декодує один збережений базовий файл на кожен дозволений конвеєр — перевірки BUILDER у recipe.json; збирача пакетів ще немає, тож це не виконано.

---

## 12. gr-satellites (STACK.md 5.4)

- main 4210dc45c9725e30d8f612eeec614f3f353cd09c як 5.10.0~git20260922-0lab1 проти GNU Radio 3.10.9.2-1.1ubuntu2 і numpy 1.26 (містить виправлення PR #832, 10d27cb, 1bcf1d8). Запасний — v5.9.0 + cherry-pick 10d27cb і 1bcf1d8; ніколи 5.5.0 (noble gr-satellites — −1).
- config.ini `submit_tlm = no` плюс `GR_SATELLITES_SUBMIT_TLM=0`.
- Unit: PrivateNetwork=yes (файл) або IPAddressDeny=any, ProtectHome=yes, ReadWritePaths лише на каталог продуктів, NoNewPrivileges=yes.

---

## 13. SDR++ (STACK.md 5.4 «Алоу-лист збірки SDRangel і SDR++»)

| | модулі |
|---|---|
| коміт | 8c9f5ee8fe405775bfcd62c8c8f8c0fc928a64af; системна librtlsdr через pkg-config |
| ON | SOAPY_SOURCE, RTL_SDR, AIRSPYHF, NETWORK_SOURCE, FILE_SOURCE, RIGCTL_SERVER (localhost:4532) |
| OFF | RECORDER, IQ_EXPORTER, PAGER_DECODER, NETWORK_SINK, DISCORD_PRESENCE, RIGCTL_CLIENT; джерела HACKRF, PLUTOSDR, HERMES, RFSPACE, SPECTRAN_HTTP, SPYSERVER, RTL_TCP, SDRPP_SERVER; M17, FALCON9 |

- Точні імена опцій CMake звірити з CMakeLists.txt коміту 8c9f5ee8. `directSamplingMode=0`. Ніколи `sdrpp --server`. Аудит падає на iq_exporter.so, recorder.so, network_sink.so, pager_decoder.so.

## 14. SDRangel 7.27.2 RX-only (STACK.md 5.4)

- v7.27.2 (97e9e21), Qt5, `-DENABLE_EXTERNAL_LIBRARIES=OFF`, `ENABLE_LIMESUITE=OFF`, `ENABLE_CHANNELRX_DEMODINMARSAT=OFF`; усі ENABLE_* вимкнено, крім:

| клас | дозволено |
|---|---|
| channelrx | chanalyzer, channelpower, demodam, demodbfm, demodwfm, demodnfm, demodssb, demodnavtex, demodrtty, demodft8, demodpacket (лише APRS), radioclock, radioastronomy, freqtracker, demodvor, demodils, noisefigure (лише Bench) |
| samplesource | rtlsdr, airspyhf, soapysdrinput (лише з пропатченим модулем LimeSuiteNG), fileinput, sigmffileinput, testsource |
| feature | satellitetracker, startracker, skymap, freqdisplay, antennatools, demodanalyzer, denoiser, morsedecoder |

- Явно відсутні: усе channeltx, channelmimo, samplesink, samplemimo (пакування видаляє кожен .so, зокрема testmi, testmosync); feature/sid, demoddsc (крім лабораторного патчу, що пройде свій тест, — тоді лише в sdrangelsrv), **demodadsb, demodais, feature ais (ADS-B і AIS — лише readsb і AIS-catcher, розділ 16)**, audiocatsiso, remotetcpsink, udpsink, localsink, rigctlserver, ambe, demodm17, demodfreedv, demodchirpchat, demodendoftrain, demodpager, demodmesh*, demoddsd, demodinmarsat, heatmap, filesink, sigmffilesink, remotesink, kiwisdr/remotetcpinput/aaroniartsainput, remotecontrol, pertester, simpleptt, limerfe; MIMO doa2, interferometer, beamsteeringcwmod.
- APT, радіозонди і DAB з алоу-листа нотаток у збірку SDRangel не входять (радіозонди — auto_rx, DAB — welle-cli). DSC — лише через demoddsc з лабораторним патчем, що відкидає формати 120/123/114 до декодування адрес (протестованим), і лише в sdrangelsrv; без патча demoddsc не збирається. APRS/AX.25 — лише через demodpacket SDRangel (лише APRS): режиму packet в OpenWebRX+ немає, direwolf заборонено. Текстові декодери (RTTY, NAVTEX, packet) — лише в sdrangelsrv на частотах, заданих labd.
- Запуск: `sdrangelsrv -a 127.0.0.1 -w /var/lib/lab/fftw/sdrangel.wisdom` (інакше REST слухає всі інтерфейси на 8091). Мудрість FFTW — на Q6A (`fftwf-wisdom` з libfftw3-bin).
- Аудит під час роботи хешує кожен файл у `<prefix>/lib/sdrangel/*` і `<prefix>/bin/lib/*` за підписаним маніфестом.

## 15. OpenWebRX+ 1.2.126+lab1 (STACK.md 5.4 «АЛОУ-ЛИСТ режимів»)

- Перепакування з пропатченим `owrx/modes.py`; встановлення `--no-install-recommends`; unit IPAddressAllow=localhost; PATH unit обмежено.
- Лишаються лише: nfm, wfm, am, sam, lsb, usb, cw, usbd, drm (лише з пропатченою RX-only Dream), dab, bpsk31/63, rtty170/450/85, sitorb, navtex, ft8, ft4, jt9, wspr, sstv, fax, sonde-*, meteor-lrpt, elektro-lrit.
- Вилучено: dsc, page, selcall, zvei, eas, tetra, p25, dmr, dstar, nxdn, ysf, m17, freedv, radel/radeu, ism, wmbus, lora-*, meshtastic, meshcore, meshcom, speech, hfdl, vdl2, acars, **adsb, uat, ais** (STACK.md 5.4).
- Заблоковані налаштування: `allow_center_freq_changes=false`, `allow_audio_recording=false`, `allow_chat=false`, `speech_url=''`, MQTT вимкнено, керування радіо вимкнено, PSKReporter/WSPRnet у полі вимкнено, пароль адміністратора задано; без ключів direct_sampling/direct_samp.
- Дзеркало: owrx-connector/rtl-connector/rtl-tcp-connector/soapy-connector 0.6.5, csdr/libcsdr0/python3-csdr 0.18.40, redsea 1.3.1. WSJT: заглушка `/usr/bin/wsjtx_app_version`, що друкує «WSJT-X 2.7.0».
- CI опитує запущений список функцій і режимів і падає на будь-якому режимі поза списком (найважливіше — TETRA).

## 16. ADS-B і AIS з фільтрами приватності (STACK.md 5.4)

| рушій | версія і запуск | фільтри |
|---|---|---|
| readsb | v3.16.17, `--db-file <закріплений aircraft.csv.gz із записаним sha256>`, `--net-bind-address 127.0.0.1` | приховати, якщо dbFlags & 1, & 4 (PIA) або & 8 (LADD), або ICAO у milRange() (закріплена копія з tar1090); профіль відмовляє, якщо aircraft.csv.gz немає або він старший за 90 днів (fail closed) |
| AIS-catcher | v0.70, без -X | судно не показується й не журналюється до статичного повідомлення (5, 19, 24B) з типом ≠ 35; пізній тип 35 — вилучення |
| radiosonde_auto_rx | v1.9.0 | sondehub_enabled = False, payload_summary_enabled = False, web_host = 127.0.0.1, SDR за серійним |

Заборонені: dump978-fa, skyaware978, повний dump1090-fa, piaware; без журналів пеленгів.

## 17. Інші дозволені декодери (STACK.md 5.4)

| інструмент | версія / джерело |
|---|---|
| jt9, wsprd | пакет **lab-wsjt-decoders** (+lab, тег wsjtx-2.7.0, b4f9a43, власний chroot sbuild з libhamlib-dev; лише `make jt9 wsprd`) |
| SSTV | slowrxd (sjlongland slowrx-daemon c94327ae40ab970b0bea20ebb378d71f8e69b98a), FM-аудіо від labrx через snd-aloop або віртуальне джерело PipeWire |
| DAB+ / RDS | welle-cli з noble welle.io 2.4 (на +lab .so.2); redsea 1.3.1 |
| наука / навігація | Virgo v3.8.9; GNSS-SDR 0.0.19 (0.0.22 — опційно); GNU Radio 3.10.9.2-1.1ubuntu2, VOLK 3.1.2-1.1build1 |
| DRM | лише пропатчена з джерел RX-only Dream (CI перевіряє рядки --transmitter / CDRMTransmitter), інакше DRM немає |
| multimon-ng | у європейській збірці НЕ встановлюється (−1) |

## 18. gpsd, chrony, PPS і LC76G (STACK.md 5.4, 5.2; C13)

```sh
# /etc/default/gpsd   (gpsd 3.25-3ubuntu3.2)
DEVICES="/dev/lab/gnss"
GPSD_OPTIONS="-n -b -s 115200"
USBAUTO="false"
```
```text
# /etc/chrony/chrony.conf  (chrony 4.5-1ubuntu4.2)
refclock SHM 0 refid NMEA offset <виміряна медіана> delay 0.2 noselect   # offset — TBD до виміру (STACK.md C13: близько 0.05-0.15)
refclock PPS /dev/pps-gnss lock NMEA refid PPS noselect
maxchange 5 1 -1
makestep 1 3
rtcsync
```
```text
# udev
SUBSYSTEM=="pps", ATTR{name}=="<вузол pps-gpio>", SYMLINK+="pps-gnss"
KERNELS=="998000.serial", SYMLINK+="lab/gnss"
# /etc/modprobe.d/lab-gnss-blacklist.conf
blacklist gnss-usb
blacklist gnss-ubx
blacklist gnss-mtk
blacklist gnss-sirf
blacklist gnss-serial
```

- Ворота PPS: при прийнятті — `chronyc selectopts PPS -noselect` + `chronyc reselect`; на прапорець глушіння (`$PAIRSPF`, `PQTMJAMMINGSTATUS` ≥2) чи підміни — `chronyc selectopts PPS +noselect` і зупинка дисциплінування від PPS/NMEA; після виходу — холодний перезапуск (`$PAIR006*3C` або імпульс RESET через MCP #4) і повторне надсилання налаштувань.
- LC76G, одноразово при зупиненому gpsd (або в ExecStartPre):

```text
$PQTMVERNO*58                      (записати версію)
$PQTMCFGPPS,W,1,1,100,3,0,0*70     (PPS лише з 3D-фіксом)
$PQTMSAVEPAR*5A
$PQTMCFGPPS,R,1*6A                 (перевірка)
$PAIR391,1*2C                      (виявлення глушіння)
$PAIR410,1*22
$PAIR400,2*20
$PAIR513*3D
$PAIR401*3F                        (читання)
$PAIR411*3E                        (читання)
опційно: $PQTMCFGMSGRATE,W,PQTMJAMMINGSTATUS,1,1*11 + $PQTMSAVEPAR*5A
```
- Ніколи `$PAIR007`, `$PAIR752,2,100`, `$PAIR753`, стаціонарний режим чи оновлення прошивки в полі. LC76G втрачає конфігурацію при знеструмленні — при кожному ввімкненні зчитати назад і повторно надіслати, якщо не збігається, до довіри PPS.
- AppArmor: `cat /sys/kernel/security/lsm; aa-status`; локальні правила (gpsd `/dev/ttyHS[0-9]* rw`, chronyd `capability ipc_owner`) — лише якщо lsm містить apparmor.
- Прохід: chrony обирає PPS протягом 10 хв після 3D-фіксу (9.2 крок 1); `chronyc sourcestats` підтвердити у W1-2.
- Служба місця: фікс 3D і ≥6 супутників; перший запуск — 3D, ≥8 супутників, у межах 50 м 5 хв; WMM2025 — pygeomag 1.1.0 у venv; таблиці міст немає; у експорті — 0.1° або 4-символьний локатор.

## 19. Gpredict RX-only (STACK.md 5.4)

- 1d80049b0fecc06a18378d88f09b1d154a070234 (2.6+git20261011, GTK3), без libgps і без hamlib; локальний патч rotctld_socket_rw (recv sizeout-1, перевірка від'ємних повернень, повний буфер = помилка).
- Радіо лише «RX only» (типи TX only / Simplex TRX / Duplex TRX заборонено в конфігах); мережеві оновлення TLE і транспондерів вимкнено; QTH — статичний файл від служби місця; єдиний клієнт rigctl — SDR++ RIGCTL_SERVER localhost:4532.
- Міст псевдонімів «6-значний номер → псевдонім» живе в labd. Аудит `ldd` не показує ні libgps, ні libhamlib.

## 20. Python (STACK.md 5.4; C22)

| venv | вміст |
|---|---|
| NanoVNA-Saver | pipx з git @3445a0a, constraints PySide6==6.11.2, лише за TCP-проксі Bench labd |
| QtTinySA | v2.0.1 з джерел, pyside6==6.11.0 |
| lab-venv | scikit-rf[visa]==2.1.0, pyvisa-py 0.8.1, Skyfield 1.55, sgp4 2.27, numpy<2, GNU Radio з apt; прогноз проходів labd (`plan_passes`) працює не тут, а в окремому `/opt/srrx/passes-venv` з тими самими Skyfield 1.55 / sgp4 2.27, але numpy 2.3.5 і без GNU Radio ([DEPLOYMENT](../software/DEPLOYMENT.md)) |
| inferd-cpu | onnxruntime 1.31.0 cp312 manylinux_2_28_aarch64 (21,420,804 B, sha256 `35758d7606d578ec5b9d65f6e8a1f488013194c3f6097038a3223cb26d35ef9a`) |
| ступінь 2 | torch 2.14.1+cpu з /whl/cpu (sha256 `2af649994b36dffc627175c3f306d9e513a309b58d4619ac7107577613336454`), faiss-cpu 1.15.1, scikit-learn 1.9.1 |

## 21. Сервіси lab* і пісочниці (STACK.md 5.4 «Процеси», 5.5)

| unit | ключові налаштування |
|---|---|
| labd (Python, D-Bus) | I2C2 (MCP #1/#3/#4, TCA9517), оренди, перемикачі, токени `/run/labd/bias/<serial>`, політики (маски 3-30 kHz, 225-400 MHz, 1544.0-1545.0 MHz — лише потужність; TDF 162 kHz у вівторок 06:00-12:00 UTC; Artemis-стоп; egc-gate), засувки FAULT кожного TPS2553DBVR-1 (FAULT VBUS RTL-B / HF+ / RTL-A — MCP #4 GPB0-GPB2), ключ LIME3V3 (EN — MCP #4 GPA0, FLT — GPB3), RESET LC76G (MCP #4 GPA1), тривога INA3221 >20 % над базовим; OOMScoreAdjust −1000; CLI labctl |
| labrx (C++) | єдиний відкривач SDR у режимі labrx; LimitMEMLOCK=infinity, OOMScoreAdjust −900; кільце 4 GiB (з Lime) або 1.5 GiB (без Lime); маски до запису; FFTW (VkFFT — лише після воріт) |
| labclassify / inferd-htp | WatchdogSec=5, MemoryMax=1G, CPUAffinity 0-3, User=labnpu, SupplementaryGroups=fastrpc, `Environment=ADSP_LIBRARY_PATH=/opt/lab/npu/2.42/dsp;/usr/lib/dsp/cdsp`, LD_LIBRARY_PATH=/opt/lab/npu/2.42/lib, DevicePolicy=closed + DeviceAllow /dev/fastrpc-cdsp rw, /dev/fastrpc-cdsp-secure rw, /dev/dma_heap/system rw; Requires/After=fastrpc.service cdsprpcd.service |
| labtrain | тимчасовий unit: A78, SCHED_IDLE, nice 19, MemoryMax 2G |
| labpowerd | INA228 на I2C0 (неперервний режим), `ina238` у чорному списку; Restart=always; poweroff, ніколи halt; OOMScoreAdjust −1000 |
| labinput | UART7 /dev/lab/pico, кадри з CRC; heartbeat Pico — основний апаратний сторож |

Оренда рушія (лише системні unit): `User=lab`, `DevicePolicy=closed`, `DeviceAllow=/dev/bus/usb/BBB/DDD rw`, `DeviceAllow=/dev/dri/renderD128 rw`, `ProtectSystem=strict`, `ReadOnlyPaths=/data`, `ReadWritePaths=/data/products/<lease>`, `IPAddressAllow=localhost`, аудіо лише через сокет PipeWire. Потрібно `CONFIG_CGROUP_BPF=y`: `grep CGROUP_BPF /boot/config-6.18.2-4-qcom`. Запасний варіант — udev ACL / група на кожну оренду.

Ізоляція кожного декодера: непривілейований користувач, ProtectSystem=strict, ReadWritePaths лише на свій вихід, ProtectHome=yes, NoNewPrivileges=yes, IPAddressDeny=any. Пам'ять: без дискового swap, zram 1 GiB; OOMScoreAdjust тренер 900, Expert-GUI 700, OpenWebRX+ 500, inferd 300.

UI: labwc 0.7.4+lab1 (бекпорт 6ab9d3f), kanshi 1.5.1 (профілі field60 «output HDMI-A-1 mode 1920x1080@59.986Hz» і field52 «…@51.677Hz»), greetd 0.9.0-4ubuntu1 з lab-session, gtk-layer-shell 0.8.2, wvkbd 0.14.3; `QSG_RHI_BACKEND=opengl`, `LABWC_FALLBACK_OUTPUT=NOOP-fallback`, `QT_IM_MODULE=qtvirtualkeyboard`.

## 22. Заборонене ПЗ (STACK.md 5.4 «Заборонено»)

wsjtx GUI і пакет wsjtx, fldigi, QSSTV, direwolf, SoapyRemote, URH, gr-iridium, gr-gsm, kalibrate, libhamlib-utils (rigctl, rigctld), декодери пейджерів і транкінгу, плагін Amarisoft LimeSuiteNG, limesuiteng-gui, gr-limesuiteng, пакетний і непропатчений dream, librtlsdr з форку rtl-sdr-blog, rtl_tcp у польових профілях, режими запису rtl_eeprom (крім -s і відновлення -m/-p), SDR-застосунки через snap/flatpak/AppImage/docker, ненульове пряме дискретизування, dump978-fa, skyaware978, повний dump1090-fa, piaware, опції bias у конфігах рушіїв, aicrf-test (/usr/bin/wifi_test, bt_test).

## 23. CI і самоперевірки пристрою: доказ відсутності TX і приватних шляхів

| # | перевірка | прохід | джерело |
|---|---|---|---|
| 1 | пошук заборонених пакетів і файлів (розділ 22) у `dpkg -l` і в ФС | жодного збігу | 5.4 |
| 2 | SDRangel: жодного .so channeltx/samplesink/samplemimo/channelmimo, DSD, Inmarsat, Heat Map, demodadsb/demodais, FileSink/SigMF sink; хеші за підписаним маніфестом | 0 зайвих; хеші збігаються | 5.4 |
| 3 | SDR++: відсутні iq_exporter.so, recorder.so, network_sink.so, pager_decoder.so | 0 | 5.4 |
| 4 | SatDump: лише дозволені плагіни; жодного `*_sdr_sink`, апаратного чи мережевого sdr_source (єдиний живий вхід — net_source з labrx на 127.0.0.1); лише 5 конвеєрів (без GOES, GK-2A, FY-4); декодування базового файлу на кожен | так | 5.4, 8 |
| 5 | OpenWebRX+: живий список режимів ⊆ алоу-листа; заблоковані налаштування | так (TETRA відсутня) | 5.4 |
| 6 | `SoapySDRUtil --info` | лише rtlsdr, airspyhf, пропатчений LimeSuiteNG | 5.4 |
| 7 | будь-який amarisoft .so | відсутній | 5.4 |
| 8 | Lime: `--txen=0` і зчитування 0x0020 після configure/calibrate; TX setupStream падає | так | 5.4 |
| 9 | librtlsdr: zero-copy, SONAME, 37 експортів, ldd споживачів; тести без токена | розділ 7.3 | 5.4 |
| 10 | Gpredict: `ldd` без libgps і libhamlib; радіо лише RX only | так | 5.4 |
| 11 | меню: кожен лист веде до наявного бекенда, оголошує бекенд без Lime і без T7, працює з кнопок і енкодерів | так | 5.4 «UI» |
| 12 | оренда: open() неорендованого /dev/bus/usb → EPERM; запис у /data → EROFS; /data/products/<lease> записуваний; EGL не llvmpipe | так | 5.4 |
| 13 | маска NPU: синтетичний сигнал названого класу на 20 kHz, 300 MHz і 1544.5 MHz | не записано | 5.4 |
| 14 | маска голосу: синтетичний NFM на 145.500, 433.500 і 446.006 MHz у закріпленому сирому захопленні | вирізано | 5.5 |
| 15 | маніфест датасету: заборонені назви класів (lfm-radar, dmr, p25 тощо) | CI падає | 5.4 |
| 16 | `apt-get -s dist-upgrade`; походження; `dpkg -V` прошивок і FastRPC | 0 змін; без launchpad; чисто | 5.4 |
| 17 | SHA-256 /etc/kernel/cmdline і /proc/cmdline | збігаються з еталоном | 5.4 |
| 18 | labbar видно поверх кожного Expert-GUI на весь екран | так | 5.4 «UI» |

## 24. Оновлення (STACK.md 5.4 «Оновлення»)

Підписаний GPG офлайн-пакет з USB-накопичувача на LAB USB; потребує ≥50 % батареї; ставить у неактивний корінь; відмовляє, якщо змінився б утримуваний пакет, ядро, embloader/systemd-boot чи прошивка SPI, і в кожному пакеті не з лабораторного aptly; далі самоперевірка і благословення кореня, інакше лічильник спроб відкочує.

## 25. Перелік TBD

| пункт | чому TBD | розділ STACK.md |
|---|---|---|
| лінія TLMM WIFI_PWR_EN для gpio-hog | знайти у W1-2 | 5.2 |
| набір FastRPC і прошивка DSP 0.2.29 / 0.2.42 | вибір матриці Phase 0 | 5.4, 8 |
| маршрут A чи B завантажувача | маршрут A ще не підтверджено на образі | 5.4 |
| offset NMEA у chrony | виміряна медіана | 5.4, C13 |
| хеші прошивок Lime і пакета radxa-dragon-q6a 6.18.2-4 | у STACK.md значень немає | 5.4 |
| назви origin aptly у preferences | STACK.md задає лише пріоритети | 5.4 |
| аргументи CLI `satdump live` + net_source | STACK.md не наводить | 5.4 |
| порт d80421b у librtlsdr | лише за термічними воротами V4L-5 | 5.4, 8.1 |
| VkFFT замість FFTW | лише після стендових воріт W1-2/P0 | 5.4 |
| demoddsc у sdrangelsrv, DRM (Dream) | лише після проходження власних тестів | 5.4 |
