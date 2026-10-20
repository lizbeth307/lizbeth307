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

Slowrx pin `sjlongland/slowrx-daemon@c94327ae40ab970b0bea20ebb378d71f8e69b98a` returned primary404. No substitute or current branch was silently chosen. LA9310 driver repository URLs and exact QAIRT archives remain unresolved rather than guessed.

Six additional preserved STACK pins were resolved through official commit APIs (also machine-readable in `extra-pins.json`): GNSS-SDR `1ddd4562723040fd66cb334b578a5b69455625f4`, Gpredict `1d80049b0fecc06a18378d88f09b1d154a070234`, NanoVNA-Saver `3445a0ab86161f9c886c9d6f215eb57cab9b6f45`, redsea `4cc27df9939798e800c4ff7cb484be6d9bf68b4d`, welle.io `0aacf578d77d79212483cd6fce436fb66523f63f`, labwc `6ab9d3fe464b31eed25fe2126d6b0dfb6cd0bff4`. Virgo3.8.9 was not resolved through either queried tag spelling and stays disabled/unresolved.

## Acquired source archive bytes

19 full pinned main-repository tar.gz archives were actually downloaded over HTTPS, SHA256/size recorded in `sources.lock.json`, and re-read by `verify_cache(..., include_core=False)`. The result is `source-cache-verification.json`:19 source entries match; `hardware_ready=false`. This is not a claim that submodules, transitive packages or device binaries are complete. The cache is separate from git at acquisition; relative `sources/<id>.tar.gz` names and immutable commit URLs make it relocatable.

The actual complete Lime archive (`818cb504284991acf69cc214469d695eff35b35244b73ace23768a95c7d9c749`,13,197,691bytes) was additionally checked through `vendor_patch.py --archive`, safely extracted and patched with all expected target/post hashes. This extends the small-fixture application test to the acquired full tree. No SDK build or hardware TX test is implied.

SatDump's101,357,307-byte source archive was acquired; SDRangel exceeded the128MiB acquisition cap and its archive hash remains null.11 of30 full source archive hashes remain unresolved. Large Radxa image/kernel binaries were not downloaded merely to obtain a hash; their official release asset metadata provided it. All cache-byte verification and source-application results are separate from the36 physical acceptance gates.

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

`sh deployment/test.sh` applies patches to temporary copies, checks exact post hashes, rejects altered source, and compiles the actual inserted Lime guard prefixes/removal bodies with host g++ (`-std=c++20 -Wall -Werror`). It verifies RX allowance/TX rejection at those guards. It does not compile the complete SDK, mock hardware behavior, close a hardware gate or establish absence of TX across every native/raw API. CMake installation produces a candidate only; Lime remains rejected by the release verifier.

RTL GPIO0ON is deliberately hard-disabled pending a separately audited labd token bridge; GPIO5 and OFF calls remain unconditionally available. OFF writes inherit upstream's limited error reporting, so their electrical result still needs a voltmeter/oscilloscope. The patch is not a claim of0V throughout USB power-up.

Upstream RTL files are GPL-2.0-or-later; LimeSuiteNG COPYING is Apache-2.0. Preserve author notices and `licenses/` texts when redistributing derived patches. Exact filenames/hash records and primary URLs are provenance, not signatures. systemd/udev behavior is referenced to version255 documentation; service files are staged without enable/start:

- https://www.freedesktop.org/software/systemd/man/255/systemd.service.html
- https://www.freedesktop.org/software/systemd/man/255/udev.html
