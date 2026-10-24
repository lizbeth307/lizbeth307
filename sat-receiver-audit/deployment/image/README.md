# Образ ОС SR-RX-v2.1: рецепт A/B UFS, комплект відновлення, наскрізний порядок

Цей каталог перетворює зафіксований образ Radxa OS r2 `_4096` і staged-дерево контролера (`deploy.py stage` + `bundle`) на встановлений образ UFS з коренями A/B. Тут же — розмітка, ланцюг завантаження, комплект відновлення, процедура запису на UFS і модельна перевірка завантаження в QEMU. Результат — **кандидат**: `hardware_ready` завжди false, а стендові ворота W-01, W-02, W-03, W-08, W-09 і W-10 ([build/09](../../build/09-testy.md)) лишаються OPEN. Перевірки CI — це модель на Linux ARM64 і QEMU, а не приймання Q6A.

Образ містить вміст Radxa OS r2, прошивки й бібліотеки Qualcomm (зокрема набір QNN). Його не публікують ([рішення](../../build/15-rishennia-komplektu.md), «Образ ОС»). Репозиторій публічний, а артефакт GitHub Actions у публічному репозиторії може завантажити будь-хто з обліковим записом GitHub. Тому `sr-rx-image.yml` вивантажує сам образ лише з приватного репозиторію (з зберіганням 1 день), а звідси — тільки маніфест, факти, журнал і карту екстентів. Сторонній збирач відтворює образ із цього рецепта.

## Склад

| Файл | Що робить |
|---|---|
| `partition-layout.json` | Машиночитна GPT: сектори 4096 B, ESP 1 GiB, root A і root B по 22 GiB, `/data` — решта; GUID типів, мітки, опції монтування, bind `/srv/srrx-cache`; квоти — TBD |
| `layout.py` | Перевірка розмітки, ідентифікатори з записаного seed (uuid5), сценарій sfdisk, `/etc/fstab` для кожного слота, команди mkfs |
| `recipe.json` | Порядок і списки рецепта з джерелами: deb ядра, holds, purge, masks, плагіни kernel-install, хуки rsetup, маршрути A/B, юніти |
| `bootchain.py` | Командний рядок ядра, записи BLS Type #1, loader.conf, плагін kernel-install, самоперевірка завантаження, Route B write-back і commit |
| `build_image.py` | Збирач: `plan`, `fetch`, `facts`, `blank`, `build` |
| `recovery_kit.py` | Карта екстентів, комплект відновлення, перевірка, захищений запис на UFS |
| `smoke_qemu.py` | Модельне завантаження образу маршруту A в QEMU virt з UEFI (AAVMF) |
| `files/` | Файли, які збирач кладе в корінь: `90-srrx-bls.install`, `install.conf`, `srrx-boot-check.service`, `srrx-boot-route-a.pref`, Route B (`srrx-ab-commit.service`, initramfs-хук і скрипт), `kit-README.uk.txt` |

Тести без root — `deployment/tests/test_image.py` (входять до хостової регресії). Усе, що потребує root, loop-пристроїв або справжнього образу r2, виконує `.github/workflows/sr-rx-image.yml` на `ubuntu-24.04-arm`.

## Базовий образ r2: зафіксовані факти

`build_image.py facts` (і перший крок `build`) розпаковує `radxa-dragon-q6a_noble_gnome_r2.output_4096.img.xz` (SHA-256 `c83ce7f6…` з `deployment/sources.lock.json`) у розріджений файл, підключає його лише для читання через `losetup --sector-size 4096` і записує `image-facts.json`. Прогін CI 24.10.2026 (артефакт `image-route-A-manifest`) показав:

- GPT на секторах 4096 B, три розділи: `config` (vfat, 128 MiB: `before.txt`, `config.txt`, `logo.bmp`), ESP `efi` (vfat, 1 GiB), `rootfs` (ext4, близько 8.75 GiB, зайнято 4.55 GB). Розпакований образ — 10 GiB.
- `/etc/kernel/cmdline`: `root=UUID=… console=ttyMSM0,115200n8 quiet splash loglevel=4 rw earlycon consoleblank=0 console=tty1 coherent_pool=2M irqchip.gicv3_pseudo_nmi=0 cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory swapaccount=1 kasan=off`. «…» у STACK.md:847 — це `quiet splash loglevel=4`.
- ESP: `EFI/BOOT/BOOTAA64.EFI` — embloader (той самий SHA-256, що `/usr/share/embloader/embloader.efi`), `sdboot-is-embloader` підміняє `systemd-bootaa64.efi` через dpkg-divert, пакет embloader — версії 0.4. Єдиний запис — `RadxaOS-6.18.2-3-qcom.conf` (ядро образу), без рядка `devicetree`; `loader.conf` — лише `timeout 3`. Записи писав `90-loaderentry.install` systemd 255.4-1ubuntu8.12.
- Плагіни kernel-install Radxa: `91-u-boot-menu.install` (extlinux) і `99-update-overlay.install` (оверлеї rsetup на ESP); `/etc/kernel/postinst.d/yz-update-overlays` і `postrm.d/yz-update-overlays` — посилання на `/usr/bin/rsetup`.
- Конфігурація ядра 6.18.2-4 з зафіксованого deb: `VIRTIO_BLK`, `VIRTIO_PCI`, `PCI_HOST_GENERIC`, `SERIAL_AMBA_PL011`, `EFI_STUB` — `y`; `VFAT_FS` — модуль; `QUOTA=y`, `QFMT_V2` — модуль. DTB пакета — `/usr/lib/linux-image-6.18.2-4-qcom/qcom/qcs6490-radxa-dragon-q6a.dtb`.
- `/etc/machine-id` відсутній; людських облікових записів немає (root заблокований): `radxa`/`rock` з паролями за замовчуванням створює лише перше завантаження rsetup (`/config/before.txt`, там же `resize_root` і підключення Wi-Fi).
- Увімкнені мережеві служби (NetworkManager, wpa_supplicant, bluetooth, avahi, cups, samba, `ssh.socket`) і списки PPA mozillateam та ubuntu-qcom-iot у `sources.list.d`.

Будь-яке значення з фактів, що змінює рецепт, звіряється на першому завантаженні Q6A (W-03), бо перше завантаження r2 могло б переписати його; цей образ перше завантаження rsetup вимикає.

## Розмітка UFS (IMG-02)

| Розділ | Початок, сектор 4 KiB | Розмір | Тип GPT | ФС і мітка | Монтування |
|---|---|---|---|---|---|
| 1 ESP | 256 (1 MiB) | 1 GiB | `C12A7328-F81F-11D2-BA4B-00A0C93EC93B` (EFI System) | FAT32, `mkfs.vfat -F 32 -S 4096`, `SRRX-ESP` | `/boot/efi`, `umask=0077` |
| 2 root A | 262400 | 22 GiB | `0FC63DAF-8483-4772-8E79-3D69D8477DE4` (Linux filesystem) | ext4 `srrx-root-a` | `/` слота A |
| 3 root B | 6029568 | 22 GiB | той самий | ext4 `srrx-root-b`, власний UUID | `/` слота B |
| 4 /data | 11796736 | решта UFS (в образі — 4 GiB) | той самий | ext4 `srrx-data` | `/data`, `nodev,nosuid,noexec` |

GUID типів підтверджує таблиця `sfdisk --list-types --label gpt` util-linux 2.39.3 на збирачі (крок «Runner resources» у CI). Diskguid, PARTUUID, UUID ФС, том vfat і `hash_seed` ext4 виводяться як uuid5 від `uuid_seed` розмітки (`SR-RX-v2.1/golden-image/layout-1`); `--uuid-seed` дає окремий набір для кожного пристрою, і маніфест записує seed. Корінь кожного слота монтується з `root=PARTUUID=` у командному рядку; `/etc/fstab` слота містить свій корінь, ESP, `/data` (усе за PARTUUID) і bind `/data/srrx-cache → /srv/srrx-cache` (`ro`): release guard перевіряє там зафіксований базовий образ і deb ядра при кожному старті `srrx.service`. Розділ `config` r2 до образу не переноситься.

`/data` в образі компактний (4 GiB: каталоги `products` і `srrx-cache` з копією кешу 1.66 GB). Після запису `recovery_kit.py write` переносить резервну GPT у кінець UFS, розширює розділ 4 до кінця пристрою і запускає `e2fsck -f` та `resize2fs`. Квоти TBD: build07:148 називає 27.4 GiB і близько 46.6 GiB, але не каталоги й тип. Ядро має `QFMT_V2` модулем, а ядро збирача без `quota_v2` не монтує ext4 з квотами, тому функцію вмикають на пристрої офлайн (`tune2fs -O quota,project -Q prjquota`), коли визначено політику (IMG-06/labd).

## Ланцюг завантаження (IMG-03, IMG-04)

**Командний рядок.** `bootchain.cmdline` складає рядок слота: повний базовий рядок r2 без `root=` (як у фактах), `root=PARTUUID=<слот>`, далі додатки STACK.md:850 (`preempt=full drm.edid_firmware=HDMI-A-1:edid/field.bin video=HDMI-A-1:1920x1080@60 panic=10 usbcore.usbfs_memory_mb=0`) і, у збірці з Lime, STACK.md:853 (`pcie_aspm=off isolcpus=nohz,domain,managed_irq,7 nohz_full=7 rcu_nocbs=7 irqaffinity=0-6`). Перевірка поштучна: токени розділені одним пробілом, кожен відповідає `[A-Za-z0-9_.,:/=+@-]+` (символ `@` потрібен для `video=…@60`), без лапок і пробільних символів, не довше 2048 B, без `clk_ignore_unused`; базовий рядок без `root=`, щонайменше три токени, і жоден його ключ не суперечить додаткам. `/etc/kernel/cmdline` кожного слота — саме цей рядок; його SHA-256 записано в маніфесті (`cmdline_sha256`) для RX-17.

**ab-config, схема 2** (`deployment/ab.template.json`, `/etc/srrx/boot.json` в образі): `route` A|B, `active_slot`, `trial_slot`, `dt_profile` lab|field, `lime_build`, `kernel_version`, PARTUUID ESP і слотів, базовий рядок, для кожного слота окремі `kernel`, `initrd`, `lab_dtb`, `field_dtb` під `/srrx/<слот>/` на ESP і окремий rescue (ядро r2 6.18.2-3, `dtb` null — як у r2, DTB від прошивки). Схема 1, де обидва слоти ділили одне ядро/initrd/DTB, відхиляється. `deploy.py stage-ab` генерує з неї лише кандидати записів у новий каталог; активної конфігурації він не змінює.

**Записи.** `labA.conf`, `labB.conf` (`sort-key srrx`, `version` — покоління), `labA-rescue.conf`, `labB-rescue.conf` (`sort-key srrx-rescue`), явний `devicetree` на lab.dtb або field.dtb слота. Маршрут A: `loader.conf` — `default lab*`, `timeout 3`, `editor no`. systemd-boot 255 упорядковує записи так: без спроб — в кінець, далі sort-key, далі version за спаданням (src/boot/efi/boot.c v255.4, `boot_entry_compare`), тож завантажується найновіший слот, що не став поганим; коли обидва lab-записи погані, першим стає rescue. Пробний слот має `lab<S>+3.conf` (з `/etc/kernel/tries`) і вище покоління; systemd-boot зменшує лічильник при кожній спробі, а systemd-bless-boot після `boot-complete.target` прибирає його. Маршрут B (embloader 0.4: лічильника немає, `default` — точна назва без `.conf`, embloader/src/sdboot/file.c і src/loader/loader.c тегу 0.4): `default lab<S>`, маркер `srrx/ab/trial` на ESP, initramfs пробного слота одразу повертає `default` на інший слот (`srrx-ab-writeback`), а `srrx-ab-commit.service` після `boot-complete.target` закріплює пробний слот. Конфігурація embloader 0.4 для Q6A (configs/radxa-q6a/config.static.yaml) задає власні bootargs `loglevel=8 panic=30 console=ttyMSM0 earlycon=qcom_geni,0x994000` і вмикає оверлей `qcs6490-kvm`; чи застосовує embloader їх до записів sdboot з явним `devicetree`, не перевірено. Самоперевірка допускає додаткові токени завантажувача (лише примітка), а sha256 `/sys/firmware/fdt` на маршруті B може не збігатися з lab.dtb — ризик для W-10.

**Плагін kernel-install** `/etc/kernel/install.d/90-srrx-bls.install` → `bootchain.py kernel-install`. `install.conf`: `layout=other` (штатні 90-loaderentry/55-initrd/90-uki-copy у systemd 255 діють лише для `bls`/`uki`), `BOOT_ROOT=/boot/efi`; плагіни 90-loaderentry, 90-uki-copy, 91-u-boot-menu і 99-update-overlay замасковано посиланнями на `/dev/null`, хуки rsetup перенесено `dpkg-divert --local --rename`. Плагін пише лише запис і файли свого слота (`/etc/srrx/slot`), ігнорує ядра, крім зафіксованого 6.18.2-4-qcom, і відмовляє (а з ним і хук пакета), якщо `/etc/kernel/cmdline` відрізняється від рядка, згенерованого з `boot.json`, ESP не змонтовано, бракує initrd або lab.dtb/field.dtb не є об'єднаним DTB з оверлеєм SR-RX (`/usr/lib/srrx/dtb/<kver>/dtb.json`). Лише збирач у CI ставить `SRRX_ALLOW_UNMERGED_DTB=1`: джерел оверлеїв (IMG-05) у дереві ще немає, тому lab.dtb і field.dtb у кандидаті — це незмінений DTB пакета з позначкою `merged: false`, а маніфест містить блокер `dt_overlays_missing`.

**Самоперевірка** `srrx-boot-check.service` (`RequiredBy=`/`Before=boot-complete.target`) → `bootchain.py boot-check`: ядро — зафіксоване; `/proc/cmdline` містить усі токени рядка слота, рівно один `root=PARTUUID` цього слота і не містить `clk_ignore_unused`; `/` і `/boot/efi` змонтовано з очікуваних PARTUUID, `/data` змонтовано; `deploy.radio_off_issues`, заборонені пакети і виконувані файли політики. Будь-яка невідповідність — `boot-complete.target` не досягається, слот не благословляється, лічильник спливає. Відкат на Q6A — W-03 (OPEN).

## Збирання (IMG-01)

Потрібен нативний arm64 Linux (Ubuntu 24.04) з root, `dosfstools e2fsprogs util-linux fdisk rsync xz-utils device-tree-compiler`; CI — `ubuntu-24.04-arm` (диск 145 GB, KVM немає).

```sh
python3 deployment/image/build_image.py plan --route A
python3 deployment/image/build_image.py fetch --cache /srv/srrx-cache
sudo python3 deployment/image/build_image.py build --cache /srv/srrx-cache --work /var/tmp/srrx-work --out /var/tmp/srrx-out --route A
# Лише кандидат CI без джерел оверлеїв IMG-05:
sudo python3 deployment/image/build_image.py build ... --allow-unmerged-dtb
```

`fetch` бере лише файли `artifacts` з `sources.lock.json` (GitHub-релізи), перевіряє розмір і SHA-256 до перейменування й викликає `deploy.verify_cache`. Збирач працює лише зі звичайними файлами: кожен loop-пристрій перевіряється на свій файл (`/sys/block/loopN/loop/backing_file`) і сектор 4096 B до будь-якого sfdisk, mkfs чи mount; шляхи `/dev/sd*`, `/dev/mmcblk*`, `/dev/nvme*`, `/dev/disk/*` відхиляються. У chroot — мінімальний `/dev` (лише вузли розділів власного образу з посиланнями by-partuuid/by-uuid для хука fsck initramfs), `proc`, `sys` лише для читання, `policy-rc.d` з `exit 101`. Порядок кроків (`plan` друкує його повністю):

1. Вхідні дані: кеш, staging і детермінований bundle контролера.
2. Факти r2 і розріджений файл нового образу; GPT через `losetup --sector-size 4096` (sfdisk 2.39 не має `--sector-size` для файлів), mkfs з виведеними UUID.
3. `rsync -aHAXx` кореня r2 у root A, копія ESP r2, від'єднання й видалення базового файла.
4. Bundle у root A з перевіркою SHA-256 кожного файла за `stage-files.json`.
5. lab.dtb/field.dtb (fdtoverlay, коли є джерела IMG-05).
6. Маршрут A: `dpkg --purge sdboot-is-embloader`, `bootctl install --esp-path=/boot/efi --no-variables --make-entry-directory=no`, пін −1 на embloader; маршрут B: embloader лишається, версія має бути 0.4.
7. Файли ланцюга завантаження (див. вище), `/etc/srrx/boot.json`, `/etc/srrx/slot`, `/etc/kernel/cmdline`, fstab слота A.
8. `dpkg -i` чотирьох deb build07:68-69 до будь-якого apt; хук пакета викликає плагін, і той пише `labA+3.conf`. Метапакет `linux-libc-dev-radxa-dragon-q6a` лишається в кеші: він залежить від `linux-libc-dev-6.18.2-4-qcom`, якого lock не містить.
9. `apt-mark hold` (build07 §1.2; лише встановлені), purge unattended-upgrades/brltty, masks (таймери apt/fwupd, ModemManager, цілі сну, `rsetup.service`), видалення списків PPA з токенами політики, блокування облікових записів з придатним паролем, порожній `/etc/machine-id`.
10. Увімкнено `srrx-radio-off.service` і `srrx-boot-check.service` (маршрут B — ще `srrx-ab-commit.service`); `srrx.service` не вмикається (IMG-06).
11. `/data`: каталоги й копія зафіксованого кешу.
12. `selftest.py offline --profile controller` на root A (політика DRAFT, тож очікувано BLOCKED).
13. Root B: `rsync` з A, власні fstab/cmdline/`slot`, `kernel-install add` у chroot B (плагін пише запис і файли слота B).
14. Еталонні записи: labA (покоління 2) і labB (1) благословлені, rescue для обох слотів, `loader.conf`; сторонні записи r2 видалено, файли ядра r2 лишаються для rescue.
15. `sfdisk --verify`, `e2fsck -fn`, `fsck.vfat -n`, карта екстентів `<image>.map.json`, `image-manifest.json`.

Маніфест (`image-manifest.json`) містить: статус (`CANDIDATE_IMAGE_BUILT` або `BLOCKED` з помилкою), маршрут, профіль DT, ідентифікатори й геометрію, SHA-256 входів (lock, рецепт, розмітка, bundle), DTB, кроки, holds/masks/purge/списки apt, увімкнені юніти, записи й інвентар ESP з SHA-256, SHA-256 cmdline обох слотів, підсумок selftest, перевірки ФС, `blocking` — що заважає вважати образ придатним, і `bench_gates_open`. Бітова відтворюваність не заявляється: часові мітки, порядок inode і випадкові seed відрізняються; зміст прив'язують хеші маніфесту.

## Комплект відновлення і запис на UFS (IMG-14)

```sh
python3 deployment/image/recovery_kit.py assemble --image OUT/srrx-golden-routeA.img --map OUT/srrx-golden-routeA.img.map.json \
  --manifest OUT/image-manifest.json --facts OUT/image-facts.json --cache /srv/srrx-cache --lock deployment/sources.lock.json \
  --extra bios-260120=/path/dragon-q6a_flat_build_wp_260120.zip:<SHA-256> --out /media/kit
python3 /media/kit/tools/recovery_kit.py verify --kit /media/kit
sudo python3 /media/kit/tools/recovery_kit.py write --kit /media/kit --target /dev/disk/by-id/<UFS>            # сухий прогін
sudo python3 /media/kit/tools/recovery_kit.py write --kit /media/kit --target /dev/disk/by-id/<UFS> --execute  # запис
```

Комплект: образ (розріджений) і карта з SHA-256 кожного екстенту, маніфест і факти, зафіксовані upstream-файли, `tools/recovery_kit.py` (лише стандартна бібліотека), `README.uk.txt`, `kit-manifest.json` і `SHA256SUMS`. Те, чого lock ще не фіксує або що дає лише стенд — образ r2 `_512` для рятувальної microSD, BIOS 260120, `edl-ng-dist-v1.6.0.zip`, два дампи SPI (W-01), знімок офлайн-репозиторію (IMG-08/IMG-09), — має статус MISSING, доки оператор не додасть перевірену копію через `--extra NAME=PATH:SHA256` (STACK.md:1700). `write` без `--execute` нічого не пише. З `--execute` він приймає лише цілий диск через `/dev/disk/by-id/`, LOG-SEC 4096, розмір не менший за образ, без змонтованих розділів, swap і власників (отже не диск поточного root і не диск, де лежить сам образ), відкриває ціль з `O_EXCL`, пише екстенти, читає кожен назад і звіряє SHA-256, потім переносить резервну GPT і розширює `/data`. CI перевіряє все це на 4K loop-пристрої поверх звичайного файла (`--test-loop-target`), разом із відмовами для `/dev/loopN` без цього прапорця, для цілі з сектором 512 B і для диска root раннера. Запис на UFS Q6A — стендовий крок (W-01, W-09), у CI його немає.

## Модельне завантаження в QEMU (IMG-15)

`smoke_qemu.py` завантажує розріджену копію образу маршруту A в QEMU `virt` з прошивкою AAVMF (edk2), диском virtio-blk із секторами 4096 B, без мережі; на `ubuntu-24.04-arm` — TCG. Ядро слота (6.18.2-4-qcom) і його initramfs ті самі, що в образі: конфігурація ядра має потрібні virtio/PCI/PL011 вбудованими. У копії змінено лише lab-записи: без `devicetree` (DT дає QEMU), з `console=ttyAMA0` і `systemd.run=` для звіту, після якого гість вимикається. Три завантаження: (1) пробний `labA+3` → самоперевірка, `boot-complete.target`, systemd-bless-boot → `labA.conf`; (2) пробний `labB+1` новішого покоління без токена `usbcore.usbfs_memory_mb=0` → самоперевірка відмовляє, благословення немає, systemd-boot лишає `labB+0-1.conf`; (3) поганий B сортується в кінець, завантажується A. Звіт — `smoke/smoke-report.json` і журнали консолі в артефакті. Це модель ланцюга systemd-boot → ядро → initramfs → systemd на чужій прошивці й машині: вона не замінює W-03 і W-10 на Q6A.

## Наскрізний порядок: від репозиторію до UFS (IMG-16)

| # | Крок | Як перевірено |
|---|---|---|
| 0 | Стенд: живлення J21, UART, два дампи SPI, BIOS 260120, рятувальні microSD (build07 §0.1, W-01, W-09) | СТЕНД, OPEN |
| 1 | Зафіксувати входи: коміт дерева, `sources.lock.json` (артефакти), `recipe.json`, `partition-layout.json`; за потреби seed пристрою | CI: host-тести рецепта |
| 2 | `fetch` і `build` на arm64-збирачі (маршрут A; маршрут B — резервний варіант) | CI: `sr-rx-image.yml`, `image-manifest.json` |
| 3 | Переглянути маніфест: `status`, `blocking`, `filesystem_checks`, записи ESP, SHA-256 cmdline, DTB | людина; CI друкує підсумок |
| 4 | Модельне завантаження в QEMU (маршрут A) | CI: модель, `smoke-report.json` |
| 5 | Додати джерела оверлеїв (IMG-05), системні файли й облікові записи (IMG-06), EDID (IMG-07), закриття пакетів і lab.pref (IMG-08), venv HMI (IMG-10) і перезібрати без `--allow-unmerged-dtb` | інші пакети етапу 3; OPEN |
| 6 | `assemble` комплекту з `--extra` (BIOS, edl-ng, дампи SPI, `_512`) і `verify` | CI: на тестовому образі; повний комплект — стенд |
| 7 | Завантаження з рятувальної microSD, `write` (сухий прогін, потім `--execute`) | СТЕНД, OPEN |
| 8 | Перше холодне завантаження з UFS: `/proc/cmdline` = рядок слота (RX-17-proc), `sha256 /sys/firmware/fdt` = lab.dtb з `dtb.json`, `bootctl list`, `systemctl status srrx-boot-check boot-complete.target systemd-bless-boot` | СТЕНД, W-03/W-10 OPEN |
| 9 | Відкат: примусова помилка слота B (`init=/bin/false`, отруєний initrd), 20 холодних завантажень (build07 §3.3) | СТЕНД, W-03 OPEN |
| 10 | Прошивка Pico/IMU ([Pico](../../firmware/pico/README.md), [IMU](../../firmware/imu/README.md)) | СТЕНД, OPEN |
| 11 | Приймання → `srrx.provision` → записи `/etc/srrx` (devices, acceptance, release, build manifest) → release guard ([DEPLOYMENT](../../software/DEPLOYMENT.md)) | СТЕНД, OPEN |

## Тести образу

Рядки для [build/09](../../build/09-testy.md) (їх туди переносить інтегратор; тут — первинний перелік):

| ID | Тест | Критерій | Стан |
|---|---|---|---|
| ОБР-01 | GPT і ФС на 4K loop-файлі (`build_image.py blank --test-sizes`) | `BLANK_IMAGE_OK`: геометрія, PARTUUID, UUID, `sfdisk --verify`, fsck | CI-модель |
| ОБР-02 | Запис комплекту в 4K loop-ціль, читання назад, розширення `/data`, відмови для небезпечних цілей | `WRITTEN_AND_READ_BACK`, перевірки 0, PARTUUID збережено, розділ 4 більший | CI-модель |
| ОБР-03 | Збирання маршрутів A і B з r2 | `CANDIDATE_IMAGE_BUILT`, перевірки ФС 0, записи labA/labB/rescue | CI-модель; кандидат з `dt_overlays_missing` |
| ОБР-04 | QEMU: благословення A, відмова B, відкат на A | `MODEL_PASS` у трьох сценаріях | CI-модель |
| ОБР-05 | Запис на UFS Q6A з рятувальної microSD | `WRITTEN_AND_READ_BACK`, LOG-SEC 4096, `/data` до кінця UFS | СТЕНД, OPEN |
| ОБР-06 | Перше завантаження з UFS (маршрут A) | `/proc/cmdline` = рядок слота; sha256 `/sys/firmware/fdt` = lab.dtb; `labA.conf` благословлено | СТЕНД, OPEN (W-03, W-10) |
| ОБР-07 | Відкат маршрутом A на Q6A | зламаний B → після 3 спроб A; 20 холодних завантажень на UFS | СТЕНД, OPEN (W-03) |
| ОБР-08 | Маршрут B (embloader write-back) | зависання B до `boot-complete.target` → наступне завантаження A; закріплення B лише після нього | СТЕНД, OPEN |

## Відкрите для інших пакетів

- IMG-05: `lab-q6a.dtso`/`field-q6a.dtso` і DKMS pps-gpio. Збирач шукає оверлеї за шляхами `recipe.json` → `dt_overlays`.
- IMG-06: sysusers (labd, lab, srrx-pico, srrx-gnss…), tmpfiles, udev, gpsd/chrony, logind, zram, greetd/labwc, пресети, вимкнення зайвих мережевих служб, облікові записи для сервісного доступу. В образі зараз немає жодного облікового запису з паролем.
- IMG-07: `edid/field.bin` і хук initramfs (командний рядок уже посилається на нього).
- IMG-08/IMG-09: повне закриття пакетів, `lab.pref` з назвами origin, підписаний офлайн-репозиторій і оновлювач у неактивний слот (він же ставить `trial_slot`).
- IMG-10: venv HMI і генератор build manifest; IMG-12: NPU; IMG-13: прошивка MCU.
