# Primary-source audit,20 October2026

`sources.lock.json` records preserved STACK versions and independently resolved refs. These are not claims that every Ubuntu package or source archive was rebuilt. Full archive SHA256 values are null until actual bytes are independently acquired and reviewed.

| Source | Verified exact ref | Primary API/source |
|---|---|---|
| RTL-SDR |797f8143266d983c56d8f35d2d442527529dd8a5|https://api.github.com/repos/osmocom/rtl-sdr/commits/797f814|
| RTL SOVERSION revert |7ebcb041f2ce887ef4d1a64607558889a86ff169|https://github.com/osmocom/rtl-sdr/commit/7ebcb041f2ce887ef4d1a64607558889a86ff169|
| LimeSuiteNG |37cb1833e35955f7072c0fb91642d14ae5515f28|https://api.github.com/repos/myriadrf/LimeSuiteNG/git/trees/37cb1833e35955f7072c0fb91642d14ae5515f28?recursive=1|
| AirspyHF1.6.8 |8891387edddcd185e2949e9814e9ef35f46f0722|https://api.github.com/repos/airspy/airspyhf/commits/1.6.8|
| SatDump |1aedd602055c154401384a8cc7876713bb371254|https://github.com/SatDump/SatDump/commit/1aedd602055c154401384a8cc7876713bb371254|
| gr-satellites |4210dc45c9725e30d8f612eeec614f3f353cd09c|https://github.com/daniestevez/gr-satellites/commit/4210dc45c9725e30d8f612eeec614f3f353cd09c|
| SDR++ |8c9f5ee8fe405775bfcd62c8c8f8c0fc928a64af|https://github.com/AlexandreRouma/SDRPlusPlus/commit/8c9f5ee8fe405775bfcd62c8c8f8c0fc928a64af|
| SDRangel v7.27.2 |97e9e21fe9754b363ae70caac822802d908e8acd|https://api.github.com/repos/f4exb/sdrangel/commits/v7.27.2|
| SoapyAirspyHF0.2.1 |0b3daf0b47c3c1d0857c873bb184f6a86a37333c|https://api.github.com/repos/pothosware/SoapyAirspyHF/commits/0b3daf0|
| SoapySDR0.8.1 |1cf5a539a21414ff509ff7d0eedfc5fa8edb90c6|https://api.github.com/repos/pothosware/SoapySDR/commits/soapy-sdr-0.8.1|
| readsb v3.16.17 |094720939c01943de82b14df6f42f67fff1cd514|https://api.github.com/repos/wiedehopf/readsb/commits/v3.16.17|
| AIS-catcher v0.70 |8833c64b3da0c42e9a724b9bd13eaab2fffadcca|https://api.github.com/repos/jvde-github/AIS-catcher/commits/v0.70|
| radiosonde_auto_rx v1.9.0 |53d03c72ad18ce4357c0cedd1f4acf2bf1efb36e|https://api.github.com/repos/projecthorus/radiosonde_auto_rx/commits/v1.9.0|
| OpenWebRX+1.2.126 |f2a8feca17afd9e983af10f1794a3283a146c5bd|https://api.github.com/repos/luarvique/openwebrx/commits/1.2.126|
| QtTinySA v2.0.1 |4a31b823a98b8200f9bde38e314648c5b22d90e6|https://api.github.com/repos/g4ixt/QtTinySA/commits/v2.0.1|

Slowrx pin `sjlongland/slowrx-daemon@c94327ae40ab970b0bea20ebb378d71f8e69b98a` returned primary404 on 20 October; on 24 October the same commit was found through the `windytan/slowrx` fork network (see the closure section below). No substitute or current branch was chosen. The exact QAIRT archive remains unresolved rather than guessed.

Six additional preserved STACK pins were resolved through official commit APIs (also machine-readable in `extra-pins.json`): GNSS-SDR `1ddd4562723040fd66cb334b578a5b69455625f4`, Gpredict `1d80049b0fecc06a18378d88f09b1d154a070234`, NanoVNA-Saver `3445a0ab86161f9c886c9d6f215eb57cab9b6f45`, redsea `4cc27df9939798e800c4ff7cb484be6d9bf68b4d`, welle.io `0aacf578d77d79212483cd6fce436fb66523f63f`, labwc `6ab9d3fe464b31eed25fe2126d6b0dfb6cd0bff4`. Virgo3.8.9 was not resolved on 20 October because the lock named `varenius/virgo`; STACK's source list names `0xCoto/Virgo`, where tag v3.8.9 exists (closure section below).

## Acquired source archive bytes

19 full pinned main-repository tar.gz archives were actually downloaded over HTTPS, SHA256/size recorded in `sources.lock.json`, and re-read by `verify_cache(..., include_core=False)`. The result is `source-cache-verification.json`:19 source entries match; `hardware_ready=false`. This is not a claim that submodules, transitive packages or device binaries are complete. The cache is separate from git at acquisition; relative `sources/<id>.tar.gz` names and immutable commit URLs make it relocatable.

The actual complete Lime archive (`818cb504284991acf69cc214469d695eff35b35244b73ace23768a95c7d9c749`,13,197,691bytes) was additionally checked through `vendor_patch.py --archive`, safely extracted and patched with all expected target/post hashes. This extends the small-fixture application test to the acquired full tree. No SDK build or hardware TX test is implied.

SatDump's101,357,307-byte source archive was acquired; SDRangel exceeded the128MiB acquisition cap on 20 October and was acquired on 24 October without a cap (below). 1 of 30 source archive hashes (QAIRT) remains unresolved. Large Radxa image/kernel binaries were not downloaded merely to obtain a hash; their official release asset metadata provided it. All cache-byte verification and source-application results are separate from the 37 physical acceptance gates.

Radxa official downloads documentation explicitly links r2 UFS4096 image: https://docs.radxa.com/en/dragon/q6a/download . Release APIs provided actual asset SHA256/size for that image and kernel6.18.2-4 packages:

- https://api.github.com/repos/radxa-build/radxa-dragon-q6a/releases/tags/rsdk-r2
- https://api.github.com/repos/radxa-pkg/linux-qcom/releases/tags/6.18.2-4

Only metadata was retrieved for large binaries; a matching metadata digest is not a claim that downloaded cache bytes were tested. No BIOS or storage write occurred.

## Exact small source fixtures

`upstream-fixtures/` contains only the target C/C++/CMake files needed to reproduce source-application tests, plus upstream license text. File bytes were obtained from the official GitHub contents API at the exact refs above, not reconstructed from remembered APIs. Git blob SHA1 matched the API values before writing patches; SHA256 before/after is in `patches/target-hashes.json`.

| Target | Official git blob SHA1 | Actual original SHA256 |
|---|---|---|
| RTL src/librtlsdr.c |55d2ef1255c0389c87484bc8e6a51b868b309993|8c872716cd6959b3cefb047c4808179b77bedb17dd9572ffc92445d3ded1275c|
| RTL src/CMakeLists.txt |408a2705d871a3e6c5ac33b270b4a7e09a9829ab|70ee7266476ce86acd73ef6463c1ffa0fb24e7fa0f48b6ce8b4bb07119f54f6e|
| Lime plugins/soapysdr/Streaming.cpp |af148a45ba20a4a075d6b9929a34df361b98a7d6|fe9477323e5e947237bae337a4c7e6a77882ec9bee28c3092f6eb1f64104c8ac|
| Lime src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp |a6c361ac50c7011f12ce7be7445165bb9f20572a|f76a14d5589fa516090984e9a95258bd3ae481f6e4134dc7e6ff298d5f98ce09|

Lime CMake option names were inspected in CMakeLists.txt, plugins/CMakeLists.txt and plugins/gr-limesuiteng/CMakeLists.txt at37cb183. `BUILD_PLUGINS_GNURADIO=OFF` is real; merely disabling Amarisoft/GUI would leave the GNU Radio plugin enabled by default when dependencies are present.

AirspyHF1.6.8 source and public header were inspected: no `airspyhf_set_bias_tee` symbol exists; USB serial is the literal prefix `AIRSPYHF SN:` plus16 hex digits. The deployment validator accepts this raw string and compares sysfs attributes, avoiding udev's normalized ID_SERIAL_SHORT. Default Ubuntu SONAME1 packaging is retained as a requirement; no unverified ABI patch is generated.

## Scope of completed tests

`sh deployment/test.sh` applies patches to temporary copies with `core.autocrlf=false`/`core.eol=lf`/`apply.whitespace=nowarn` (post hashes are independent of the caller's git config), checks exact post hashes, rejects altered source, and compiles the actual inserted Lime guard prefixes/removal bodies, including `Calibrate(Tx)`, with host g++ (`-std=c++20 -Wall -Werror`). It also compiles the actual patched RTL `rtlsdr_set_bias_tee_gpio` body with host cc against stubs that keep upstream's `uint8_t` GPIO parameters: GPIO0 ON and wrapped numbers such as 256/-256/512 are rejected without touching GPO/GPOE, GPIO5 and in-range OFF still work, and the unpatched body is shown to wrap 256 to GPIO0. It verifies RX allowance/TX rejection at those guards. With `SRRX_RELEASE_BUILDER=1`, a missing cc or g++ blocks test.sh instead of skipping these tests. It does not compile the complete SDK, mock hardware behavior, close a hardware gate or establish absence of TX across every native/raw API. CMake installation produces a candidate only; Lime remains rejected by the release verifier.

RTL GPIO0ON is deliberately hard-disabled pending a separately audited labd token bridge. GPIO numbers outside 0..7 return `-EINVAL`, because upstream's `uint8_t` helpers would otherwise reduce e.g. 256 or -256 to GPIO0; in-range GPIO5 and OFF calls remain available. OFF writes inherit upstream's limited error reporting, so their electrical result still needs a voltmeter/oscilloscope. The patch is not a claim of0V throughout USB power-up.

Upstream RTL files are GPL-2.0-or-later; LimeSuiteNG COPYING is Apache-2.0. Preserve author notices and `licenses/` texts when redistributing derived patches. Exact filenames/hash records and primary URLs are provenance, not signatures. systemd/udev behavior is referenced to version255 documentation; service files are staged without enable/start:

- https://www.freedesktop.org/software/systemd/man/255/systemd.service.html
- https://www.freedesktop.org/software/systemd/man/255/udev.html

## Source lock closure, 24 October 2026

`deployment/fetch_sources.py` streams every download through SHA-256 in 1 MiB chunks and moves a file into the cache only when hash and size match the lock; a locked entry can never grow past its locked size, and `acquire` (for a not yet locked archive) has no fixed cap. All 29 resolved components (73 cache files, 445,040,683 bytes) were downloaded again on 24 October and re-read by `verify_cache(..., include_core=False)`: `source-cache-verification.json` now lists 29 components and is bound to the new lock by `source_lock_sha256`. The 19 archives of 20 October were byte-identical.

| Component | Pin | Evidence read on 24 October 2026 |
|---|---|---|
| SDRangel v7.27.2 | 97e9e21f, archive 138,256,778 B, SHA-256 11e599d1... | GitHub archive measured by `fetch_sources.py acquire`; content tree equals commit tree fca67811 with gitlink `external/windows` 72317cca (GitHub git/trees API) |
| WSJT-X 2.7.0 (wsjt-decoders) | b4f9a431 (tag object d2d9c46a), `wsjtx-2.7.0.tgz` 26,603,107 B, SHA-256 3788f5df... | `git ls-remote https://git.code.sf.net/p/wsjt/wsjtx`; size and MD5 fd558b60... equal the SourceForge file metadata (RSS feed of `/wsjtx-2.7.0`). The tarball is a superbuild (src/wsjtx.tgz plus src/hamlib-4.6.1.tar.gz) and names no commit. CI run 40113667357 compared src/wsjtx.tgz with a clone of the tag: all common files are byte-identical; the release lacks only `.gitattributes`, `plots/` and `samples/` |
| GNU Radio 3.10.9.2-1.1ubuntu2, VOLK 3.1.2-1.1build1 | noble/universe | gpgv of the snapshot.ubuntu.com 20261020T000000Z InRelease against key F6ECB3762474EDA9D21B7022871920D1991BC93C (the key of the ARM64 lab locks; noble InRelease SHA-256 equals the lab lock), then Sources.xz/Packages.xz from the signed list, then Checksums-Sha256 and every arm64/all binary (25 and 4 .deb) |
| gpsd 3.25-3ubuntu3.2, chrony 4.5-1ubuntu4.2 | noble-updates/main | the same signed chain (8 and 1 .deb); the snapshot keeps these versions even after newer security uploads |
| Virgo v3.8.9 | 0xCoto/Virgo ac699cb4, 58,747,050 B | lightweight tag via git/refs API; archive tree equals commit tree 2de46dc8 |
| slowrx-daemon c94327a | c94327ae (Stuart Longland, 2024-12-17), 50,640 B | the fork `sjlongland/slowrx-daemon` returns 404, but the commit (166 commits ahead of `windytan/slowrx` master) is served through that fork network; archive tree equals commit tree 415a8214. Same commit id, so no substitute; the cached archive must be kept because no live primary remains |
| la9310_limesdr 0.2.1, la9310_uart_module 1.0.0 | LimeSuiteNG 37cb183, the already locked archive | `drivers/linux/la9310_limesdr/CMakeLists.txt` declares `project(la9310_limesdr VERSION 0.2.1)` and `add_kernel_module(NAME la9310_uart_module VERSION "1.0.0" ...)` |

Every GitHub archive now carries `git_tree_sha1` (and `git_submodules` where the commit has gitlinks): `fetch_sources.py tree` recomputes the git tree from the archive bytes, and all 24 matched the commit trees from the GitHub API. The archives omit submodule contents: SatDump `android/deps` and `docs/res`, gr-satellites `satellite-recordings` and SDRangel `external/windows` are not part of the cached bytes.

`documented_artifacts` records release-asset digests from the GitHub release API that the documents already named, outside the core cache (release_guard does not require them): edk2-qcs6490 and edk2-radxa-dragon-q6a 0.1.0-5 (the held SPI BIOS packages; the edk2-qcs6490 digest equals build/07 section 0.1) and the Phase 0 firmware candidates radxa-firmware(-qcs6490) 0.2.29 and 0.2.42 (the 0.2.29 digest equals components/compute_os.md). `fetch_sources.py fetch --documented` downloaded all six on 24 October and they matched; the Phase 0 selection stays null. The BIOS 260120 zip and edl-ng-dist-v1.6.0.zip have no documented digest yet.

Still open: QAIRT 2.42.0.251225 (licensed zip, 1,543,955,191 B, SHA-256 1a744ed7... in STACK) must be acquired by the owner under its licence; it is never redistributed or fetched in CI. The full target package closure of the image (Radxa, Mesa, Qt and the rest) and the Python wheelhouse are separate locks and stay OPEN.
