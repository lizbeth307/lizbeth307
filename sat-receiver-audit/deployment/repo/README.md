# Підписаний офлайн-репозиторій пакетів +lab

Редакція 24.10.2026. Єдине джерело apt на пристрої — одна підписана публікація aptly пакетів `+labN` (build/07, розділ 2), плюс окрема публікація віддзеркаленого знімка noble. Тут описано розкладку, підпис, перевірку й церемонію ключа власника. Приватний ключ випуску ніколи не потрапляє в CI, Git чи на пристрій (build/15, «Ключ підпису офлайн-репозиторію»); CI підписує лише тестовим ключем, що існує один job.

## Файли

| Файл | Призначення |
|---|---|
| `repo-policy.json` | origin `srrx-lab`, дистрибутив `noble-lab`, компонент `main`, архітектура `arm64`, шлях keyring на пристрої і пакети, яким заборонено надходити з лабораторного репозиторію (ядро, завантажувач і BIOS/SPI, прошивки плати, DSP/FastRPC). Статус DRAFT до церемонії ключа |
| `aptly.conf.template.json` | конфігурація aptly: лише arm64, без Contents, без джерел і без залежностей Suggests/Recommends |
| `publish.sh` | `publish.sh НОВИЙ_КАТАЛОГ FINGERPRINT DEB...`: repo → snapshot → `publish snapshot` з підписом ключем із `GNUPGHOME`; назви бере з `repo-policy.json` |
| `srrx-lab.sources` | запис apt deb822 для пристрою з `Signed-By: /usr/share/keyrings/srrx-lab.gpg` |
| `lab.pref` | `/etc/apt/preferences.d/lab.pref`: `o=srrx-lab` 1001, `o=srrx-mirror` 990, усе інше −1 (структура, яку перевіряє selftest RX-16) |
| `check_repo.py` | перевірки CI: пакети проти записів збірки (`packages`) і випадки підробки (`tamper`) |

Назви origin у build/07 (розділ 2, перелік TBD) були не задані: тут їх зафіксовано як `srrx-lab` (пакети `+labN`) і `srrx-mirror` (віддзеркалений знімок noble, OpenWebRX+ і radxa), як і в тестах RX-16. Публікацію `srrx-mirror` ще не зібрано: для неї потрібне закриття пакетів цільового образу (IMG-08).

## Перевірка: `deploy.py verify-repo`

```sh
python3 deployment/deploy.py verify-repo --repo /srv/srrx-repo/lab --keyring /usr/share/keyrings/srrx-lab.gpg \
    --fingerprint <40 hex> --build-record rtlsdr.build-record.json --build-record limesuiteng.build-record.json \
    --sources-entry /etc/apt/sources.list.d/srrx-lab.sources --inrelease-sha256 <sha256> --target-status /mnt/inactive/var/lib/dpkg/status
```

Послідовність: `gpgv` перевіряє `dists/noble-lab/InRelease` лише явним keyring і приймає лише добрий підпис закріпленого fingerprint; розбирається тільки текст, який gpgv назвав підписаним. Далі кожен файл `dists/` звіряється зі списком SHA256 підписаного Release (файл поза списком — відмова), кожен рядок `Packages` — з байтами `.deb` у `pool/` і з записом збірки (назва, версія, архітектура, SHA-256, розмір), а запис збірки — з lock (компонент, версія, SHA-256 архіву джерел, дата знімка). Відмова також для: іншого Origin/Suite/Components/Architectures, `.deb` у `pool/`, якого немає в індексі, версії без `+labN`/`-0labN`, пакета з переліку ядра/завантажувача/прошивок, пакета, який забороняє `receive-only-policy.json`, зміни версії утримуваного пакета (`--target-status`, dpkg status кореня, що оновлюється), запису apt без `Signed-By` на keyring пристрою та InRelease, відмінного від закріпленого (`--inrelease-sha256`).

`release-guard` викликає цю перевірку замість хешу одного файла: у `release.template.json` поле `offline_snapshot` тепер містить `repo`, `keyring`, `signing_fingerprint`, `inrelease_sha256`, `sources_entry` і `build_records` (шлях і SHA-256 кожного запису). Утримувані пакети звіряються з `/var/lib/dpkg/status` активного кореня.

**Valid-Until не ставиться.** Пристрій офлайн, а годинник RTC може бути неправильним, тож перевірка часу або блокувала б справний пристрій, або нічого не давала б. Свіжість задає запис випуску: `inrelease_sha256` закріплює одну конкретну підписану публікацію, і старішу підписану публікацію (атаку відкату) буде відхилено.

## Церемонія ключа власника (ручний крок, OPEN)

1. Офлайн-комп'ютер без мережі (live-образ), новий `GNUPGHOME` на зашифрованому носії. Ключ підпису (ed25519 або RSA 4096) з терміном дії й окремим сертифікатом відкликання; uid без особистої адреси, наприклад `SR-RX lab repository signing key`.
2. Записати повний fingerprint у двох місцях поза репозиторієм; у `repo-policy.json` (status REVIEWED) і в запис випуску його вносить власник.
3. Експортувати **лише** відкритий ключ: `gpg --export <fingerprint> > srrx-lab.gpg`. Він іде в образ як `/usr/share/keyrings/srrx-lab.gpg`.
4. На тому самому офлайн-комп'ютері: перевірені `.deb` і записи збірки з артефакту CI (SHA-256 звірити з `*.build-record.json`), потім `sh deployment/repo/publish.sh /media/repo-<дата> <fingerprint> *.deb`, потім `deploy.py verify-repo` над `/media/repo-<дата>/public`.
5. SHA-256 `dists/noble-lab/InRelease` внести в `offline_snapshot.inrelease_sha256` запису випуску; приватний ключ лишається лише на зашифрованому носії (дві копії в різних місцях).

Тестовий ключ CI має uid `SR-RX lab CI TEST KEY - not for release`, живе два дні й видаляється наприкінці job. Його відкритий ключ є в артефакті лише для повторної перевірки; довіряти йому на пристрої заборонено.

## Межі

Перевірка доводить цілісність і походження байтів від записів збірки й lock, а не відсутність TX у пакетах (це `verify_build` і рецензія аудиту) і не правильність установлення. Сам інсталятор оновлення в неактивний слот (IMG-09: заряд батареї ≥50 %, пробне завантаження і благословення кореня) ще не реалізовано; апаратний відкат — ворота W-03, OPEN.
