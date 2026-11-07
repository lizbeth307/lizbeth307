"""Declarative Lab Shell menu (STACK.md:884) and its capability check, evaluated by selftest RX-11.

Pure data and pure functions: no Qt, no I/O, no labd call. The Qt 6.4.2 QML Lab Shell and its
greetd/labwc session are not built (STACK.md:160, :884); this model is the contract the shell is
built against and the data of the CI menu test STACK.md:884 asks for: every leaf leads to an
existing backend, declares its backend without the Lime and without the T7, and a critical leaf
works from keys and encoders alone (STACK.md:110). The touch console srrx.hmi has its own model
(srrx.menu_model); the key, encoder and backend vocabulary is shared with it.

A leaf names its hub, its label, the backend it reaches (menu_model.BACKEND_KINDS: a labd operation,
an engine unit, a decoder preset of srrx.decoder_policy or a page backed by an srrx module), what it
also needs (`requires`: PACKAGES by name, system units such as the engine lease templates, which are
never --user (STACK.md:76), srrx modules, decoder presets), an entry of
the receive-only policy allowlists it uses (`allowlist`: an SDRangel plugin, an OpenWebRX+ mode or a
SatDump pipeline, the lists of deployment/receive-only-policy.json), whether it needs the Lime or the
T7 with the backend it declares without them (`fallback_text`), whether it is critical, the inputs
that operate it and a standing `hidden_reason`. A backend name "planned.<feature>" marks a backend
the repository does not build yet (PLANNED, with its source); such a leaf is always hidden.

visible_leaves(capabilities) shows a leaf only when nothing in hide_reasons() applies: its backend
and requirements exist in the capabilities, its allowlist entry is allowed and not denied, its
decoder presets are accepted and its Lime/T7 needs hold. Everything else is hidden with stable
reasons, never shown as a dead leaf. The capabilities are what selftest RX-11 reads from a staged
root (capabilities() lists the fields); hide_reasons() itself reads nothing.
"""
import fnmatch
import re

from .menu_model import BACKEND_KINDS, ENCODERS, HOLD_STOP, KEYS, NO_LIME, NO_T7

# Top hubs in STACK.md:884 order ("Верхні хаби меню (за lab_ui_hf, з виправленнями)").
HUBS = ({"id": "satellites", "label": "Satellites"}, {"id": "hf", "label": "HF"},
        {"id": "air_sea", "label": "Air & Sea"}, {"id": "sondes", "label": "Sondes"},
        {"id": "spectrum", "label": "Spectrum"}, {"id": "radio_astronomy", "label": "Radio Astronomy"},
        {"id": "instruments", "label": "Instruments"}, {"id": "signals_ai", "label": "Signals AI"},
        {"id": "recordings", "label": "Recordings"}, {"id": "map_point", "label": "Map & Point"},
        {"id": "gnss_time", "label": "GNSS & Time"}, {"id": "system", "label": "System"})
HOME = "home"  # the Home tile grid and the physical inputs around every hub (not a hub)
PLANNED_PREFIX = "planned."
# Backends the repository does not build yet, by feature; a leaf on one is hidden "planned:<feature>".
PLANNED = {
    "labinput": "labinput, the UART7 key and encoder bridge of the Shell session (STACK.md:76); not in this repository",
    "touch_lock": "LOCK: labd writes the labwc rc.xml touch fragment and runs labwc --reconfigure (STACK.md:884)",
    "satdump_live": "live SatDump decode from labrx over net_source cf32 UDP on localhost (STACK.md:886); HRPT only live (STACK.md:973)",
    "slowrx": "SSTV through slowrx built from source (STACK.md:85); sources.lock.json slowrx has no recipe",
    "gr_satellites": "CubeSat decode through gr-satellites (sources.lock.json gr-satellites); no recipe",
    "beacon_lock": "labrx QO-100 beacon lock and beacon levels (lab_ui_hf, extra-studies.md:73983)",
    "openwebrx_lease": "OpenWebRX+ as an exclusive engine lease (STACK.md:76); srrx.engine_leases has no OpenWebRX+ engine",
    "ibp_schedule": "IBP beacon schedule with a labrx level log (lab_ui_hf, extra-studies.md:74068)",
    "power_log": "labrx power log for SID; the SDRangel SID feature (featuresid) is denied by the policy",
    "labd_logs": "labd log collector (lab_ui_hf, extra-studies.md:74108)",
    "auto_rx_lease": "radiosonde_auto_rx as an engine lease (STACK.md:76; sources.lock.json radiosonde-auto-rx, no recipe)",
    "labclassify": "labclassify inference (STACK.md:76, :920)",
    "l_band_power_scan": "NCS 1537-1545 MHz power-only scan, no carrier list or log in 1544.0-1545.0 MHz (STACK.md:884)",
    "geo_carrier_check": "GEO carrier check with the visible-from-here flag (STACK.md:884)",
    "ku_humps": "Ku hump survey (STACK.md:884)",
    "instrument_drivers": "labd instrument drivers over serial: tinySA, VNA, LBE-1420, FNB58, scope/LA (STACK.md:873, :884)",
    "sled_attenuator": "sled attenuator step through the TCA9517 LAB BUS (STACK.md:873, :884)",
    "calibration": "frequency and level calibration with a labrx carrier measurement (STACK.md:884)",
    "recordings_index": "recordings browser and index (lab_ui_hf, extra-studies.md:74273)",
    "update_media": "update from a USB stick or microSD into the inactive slot (STACK.md:884, :906)",
    "t7_storage": "T7 health, the 55 C stop and its deauthorization in L-band, S-band and GNSS sessions (STACK.md:87)",
    "map_layers": "live map layers: aircraft, vessels, sondes, satellite tracks, APRS (STACK.md:884); srrx.location has the own position only",
    "peak_on_signal": "peak-on-signal pointing without a bearing line or emitter marker, nothing stored (STACK.md:884)",
    "wifi_home": "home-only Wi-Fi after a 1.5 s hold, blocked in every field and QUIET profile (STACK.md:884); srrx.rfkill only blocks",
    "selftest_view": "logs and self-test view (lab_ui_hf, extra-studies.md:74393)",
}
# Standing decisions that hide a leaf whatever is installed.
HIDDEN_REASONS = {"bluetooth_off_permanently": "Bluetooth is off for good (STACK.md:884); srrx.rfkill only blocks"}
# Installable software a leaf can need: its sources.lock.json component, the executables that show an
# installed copy on a root (systemd's search path; none known while no recipe builds it) and a deferral.
PACKAGES = {
    "satdump": {"lock": "satdump", "binaries": ("satdump",), "deferred": None},  # srrx.satdump_pass SATDUMP
    "sdrangelsrv": {"lock": "sdrangel", "binaries": ("sdrangelsrv",), "deferred": None},  # srrx-lease-sdrangelsrv@.service
    "readsb": {"lock": "readsb", "binaries": ("readsb",), "deferred": None},  # srrx-lease-readsb@.service
    "ais-catcher": {"lock": "ais-catcher", "binaries": ("AIS-catcher",), "deferred": None},  # srrx-lease-aiscatcher@.service
    "wsjt-decoders": {"lock": "wsjt-decoders", "binaries": ("jt9", "wsprd"), "deferred": None},  # STACK.md:127
    "dream": {"lock": None, "binaries": ("dream",), "deferred": None},  # receive-only-policy.json dream.binary_names
    # OpenWebRX+ is deferred: its lock entry keeps release blockers and has no recipe, and its DSP
    # dependencies csdr, pycsdr and owrx_connector have no sources.lock.json component.
    "openwebrx": {"lock": "openwebrx-plus", "binaries": ("openwebrx",),
                  "deferred": "sources.lock.json openwebrx-plus: release_blockers, no recipe; csdr, pycsdr, owrx_connector not locked"},
    "slowrx": {"lock": "slowrx", "binaries": (), "deferred": None},
    "gr-satellites": {"lock": "gr-satellites", "binaries": (), "deferred": None},
    "radiosonde-auto-rx": {"lock": "radiosonde-auto-rx", "binaries": (), "deferred": None},
    "nanovna-saver": {"lock": "nanovna-saver", "binaries": (), "deferred": None},
    "qttinysa": {"lock": "qttinysa", "binaries": (), "deferred": None},
}
# Policy component -> (allow list key, deny list key, how a deny entry matches): the selftest rules
# of the same lists (RX-02 tokens, RX-04 exact pipeline names, RX-05 fnmatch mode patterns).
ALLOWLISTS = {"sdrangel": ("allow_plugins", "deny_tokens", "token"), "openwebrx": ("allow_modes", "deny_modes", "pattern"),
              "satdump": ("allow_pipelines", "pipeline_deny_tokens", "token")}
CAPABILITY_FIELDS = ("lime", "t7", "packages", "units", "modules", "ops", "presets", "policy")
REQUIRE_KINDS = ("packages", "units", "modules", "presets")
TOUCH = {"touch": True, "keys": ()}
# No-Lime / no-T7 backends of the Lime and T7 leaves (STACK.md:884: every item declares them).
NO_LIME_HRPT = "No Lime build: hidden; RTL-A at 2.56 Msps is marginal for HRPT (lab_ui_hf), LRPT stays on RTL-A"
NO_LIME_AHRPT = "No Lime build: hidden; the 3.5 MHz Metop AHRPT band exceeds the 2.56 Msps of the V4L (STACK.md:178)"
NO_LIME_GEO = "No Lime build: hidden; lab_ui_hf names only Lime RX1 for the 1.69 GHz GEO downlink (extra-studies.md:73958)"
NO_LIME_CLASSES = "No Lime build: occupancy classes without wifi and bt_ble (STACK.md:126, :920)"
NO_T7_DATASET = "No T7: datasets stay on /data (UFS) and leave through Recordings > Export to a USB stick or microSD (STACK.md:884)"

_LEAF_FIELDS = frozenset(("id", "hub", "label", "backend", "requires", "allowlist", "needs_lime", "needs_t7",
                          "fallback_text", "critical", "controls", "hidden_reason"))
_ID = re.compile(r"[a-z][a-z0-9_]*\.[a-z0-9_]+\Z")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.@+-]{0,127}\Z")
_PROGRAM = re.compile(r"srrx\.[a-z_]+\Z|/[A-Za-z0-9_./+-]+\Z")


class LabShellMenuError(ValueError):
    """Schema defect of the Lab Shell model; the text names the leaf or hub, never runtime data."""


def _leaf(leaf_id, label, kind, name, *, packages=(), units=(), modules=(), presets=(), allowlist=None,
          lime=False, t7=False, fallback=None, critical=False, controls=TOUCH, hidden=None, scope=None, program=None):
    """One leaf. An engine_unit backend also takes the unit's scope ("system" or "user") and the program
    its ExecStart runs (srrx.<module> or an absolute path), as menu_model's unit backends."""
    backend = {"kind": kind, "name": name}
    if kind == "engine_unit":
        backend.update(scope=scope, program=program)
    return {"id": leaf_id, "hub": leaf_id.split(".", 1)[0], "label": label, "backend": backend,
            "requires": {"packages": tuple(packages), "units": tuple(units), "modules": tuple(modules), "presets": tuple(presets)},
            "allowlist": None if allowlist is None else {"component": allowlist[0], "name": allowlist[1]},
            "needs_lime": lime, "needs_t7": t7, "fallback_text": fallback, "critical": critical,
            "controls": {"touch": controls["touch"], "keys": tuple(controls["keys"])}, "hidden_reason": hidden}


def _lease(leaf_id, label, plugin, **kwargs):
    """A leaf that runs through labd's engine_lease of sdrangelsrv (srrx.engine_leases) with one allowed plugin."""
    return _leaf(leaf_id, label, "labd_op", "engine_lease", packages=("sdrangelsrv",),
                 units=("srrx-lease-sdrangelsrv@.service",), allowlist=("sdrangel", plugin), **kwargs)


def _planned(leaf_id, label, feature, kind="page_only", **kwargs):
    return _leaf(leaf_id, label, kind, PLANNED_PREFIX + feature, **kwargs)


LEAVES = (
    # Home and the physical inputs. DISARM / STOP is critical: touch sends labd disarm, and holding LOCK
    # (menu_model.HOLD_STOP) stops on the Pico itself without labd or Qt (W2 FW-STOP).
    _leaf("home.tiles", "Home: 4x3 tiles with live status", "labd_op", "status", critical=True,
          controls={"touch": True, "keys": ("HOME",)}),
    _leaf("home.stop", "DISARM / STOP", "labd_op", "disarm", critical=True, controls={"touch": True, "keys": (HOLD_STOP["key"],)}),
    _planned("home.back", "BACK", "labinput", critical=True, controls={"touch": False, "keys": ("BACK",)}),
    _planned("home.encoders", "ENC1 / ENC2: focus and select", "labinput", critical=True,
             controls={"touch": False, "keys": ("ENC1", "ENC2", "ENC1_PRESS", "ENC2_PRESS")}),
    _planned("home.lock", "LOCK (touch lock)", "touch_lock", critical=True, controls={"touch": False, "keys": ("LOCK",)}),
    # Satellites: the hub shows only allowlisted SatDump pipelines (STACK.md:873).
    _leaf("satellites.passes", "Pass list", "labd_op", "plan_passes"),
    _leaf("satellites.lrpt", "LRPT (pass card: V: bisector N-S / V: tips N-S)", "labd_op", "baseband_schedule",
          packages=("satdump",), presets=("satdump-weather",), allowlist=("satdump", "Meteor-M.json")),
    _planned("satellites.hrpt", "HRPT", "satdump_live", packages=("satdump",), allowlist=("satdump", "Meteor-M.json"),
             lime=True, fallback=NO_LIME_HRPT),
    _planned("satellites.metop_aws", "Metop/AWS (experimental)", "satdump_live", packages=("satdump",),
             allowlist=("satdump", "MetOp.json"), lime=True, fallback=NO_LIME_AHRPT),
    _planned("satellites.elektro", "Elektro GGAK/LRIT (visible from here)", "satdump_live", packages=("satdump",),
             modules=("geo_look",), allowlist=("satdump", "Elektro_Arktika.json"), lime=True, fallback=NO_LIME_GEO),
    _planned("satellites.fy2h", "FY-2H (visible from here)", "satdump_live", packages=("satdump",), modules=("geo_look",),
             allowlist=("satdump", "FengYun-2.json"), lime=True, fallback=NO_LIME_GEO),
    _planned("satellites.iss_sstv", "ISS SSTV 437.550", "slowrx", packages=("slowrx",)),
    _lease("satellites.iss_aprs", "ISS APRS 437.825", "demodpacket"),
    _lease("satellites.iss_fm", "ISS FM 437.800 (listen)", "demodnfm"),
    _planned("satellites.cubesats", "CubeSats", "gr_satellites", packages=("gr-satellites",)),
    _lease("satellites.qo100", "QO-100 NB (rotate LNB hint, elevation from the GNSS fix)", "demodssb", modules=("geo_look",)),
    _planned("satellites.beacons", "QO-100 beacon monitor (F1A: two tones)", "beacon_lock", modules=("geo_look",)),
    _leaf("satellites.safetynet", "Inmarsat-C SafetyNET", "decoder_preset", "egc-safetynet", modules=("egc_gate",)),
    _leaf("satellites.tle", "TLE/OMM (home Wi-Fi, USB stick or microSD)", "page_only", "orbits", modules=("norad_allowlist",)),
    _leaf("satellites.products", "Products", "page_only", "decoder_policy", packages=("satdump",)),
    # HF (STACK.md:884, :886).
    _lease("hf.listen", "Listen", "demodam"),
    _planned("hf.drm", "DRM", "openwebrx_lease", packages=("openwebrx", "dream"), allowlist=("openwebrx", "drm")),
    _leaf("hf.band_survey", "Band survey (occupancy only)", "page_only", "spectrum"),
    _lease("hf.navtex", "NAVTEX", "demodnavtex"),
    _planned("hf.sitor_b", "SITOR-B", "openwebrx_lease", packages=("openwebrx",), allowlist=("openwebrx", "sitorb")),
    _leaf("hf.dsc", "DSC (patched demoddsc in sdrangelsrv only)", "decoder_preset", "dsc-safety", packages=("sdrangelsrv",),
          units=("srrx-lease-sdrangelsrv@.service",), allowlist=("sdrangel", "demoddsc")),
    _planned("hf.wefax", "WEFAX (fax in OpenWebRX+)", "openwebrx_lease", packages=("openwebrx",), allowlist=("openwebrx", "fax")),
    _lease("hf.time_signals", "Time signals", "radioclock", modules=("scope_policy",)),
    _planned("hf.ibp", "IBP beacons", "ibp_schedule"),
    _leaf("hf.ft8", "FT8/FT4/WSPR (decode only)", "decoder_preset", "amateur-digital", packages=("wsjt-decoders",)),
    _lease("hf.cw_rtty_psk", "CW/RTTY/PSK31 (amateur bands only)", "demodrtty"),
    _planned("hf.sid", "SID: civil DX carriers", "power_log"),
    _leaf("hf.antenna", "Antenna (HF relay)", "labd_op", "relay"),
    _planned("hf.quiet", "HF Quiet", "labinput"),
    _planned("hf.background_logging", "Background logging", "openwebrx_lease", packages=("openwebrx",)),
    # Air & Sea: ADS-B and AIS only through readsb and AIS-catcher with the privacy filters (STACK.md:886).
    _leaf("air_sea.adsb", "ADS-B", "labd_op", "engine_lease", packages=("readsb",), units=("srrx-lease-readsb@.service",),
          presets=("adsb-public",)),
    _leaf("air_sea.ais", "AIS", "labd_op", "engine_lease", packages=("ais-catcher",), units=("srrx-lease-aiscatcher@.service",),
          presets=("ais-public",)),
    _lease("air_sea.vor_ndb", "VOR/NDB", "demodvor"),
    _planned("air_sea.logs", "Logs", "labd_logs"),
    _planned("sondes.live", "Sondes (radiosonde_auto_rx)", "auto_rx_lease", packages=("radiosonde-auto-rx",)),
    # Spectrum and the new STACK.md:884 items that live there.
    _leaf("spectrum.waterfall", "Live waterfall", "page_only", "labrx"),
    _lease("spectrum.listen", "Listen VHF/UHF (no digital voice, no pagers)", "demodnfm"),
    _leaf("spectrum.survey", "Survey (occupancy only)", "page_only", "spectrum"),
    _planned("spectrum.survey_classes", "Survey classes wifi and bt_ble", "labclassify", lime=True, fallback=NO_LIME_CLASSES),
    _leaf("spectrum.measure", "Measure", "page_only", "spectrum"),
    _leaf("spectrum.interference_hunt", "Interference hunt (live reading, no log)", "page_only", "spectrum"),
    _leaf("spectrum.noise_floor", "Noise floor A/B", "labd_op", "route"),
    _planned("spectrum.ncs_scan", "NCS scan 1537-1545 MHz (power only)", "l_band_power_scan"),
    _planned("spectrum.geo_carriers", "GEO carrier check (visible from here)", "geo_carrier_check", modules=("geo_look",)),
    _planned("spectrum.ku_humps", "Ku humps", "ku_humps"),
    _lease("radio_astronomy.hydrogen_line", "Hydrogen line 1420.406 MHz", "radioastronomy"),
    _lease("radio_astronomy.sun_drift", "Sun drift scan", "radioastronomy"),
    # Instruments (STACK.md:884): bench-only items say so in their label.
    _leaf("instruments.bench", "Bench mode", "labd_op", "mode"),
    _planned("instruments.s11_s21", "Conducted S11/S21 (DUT/load only, Bench only)", "instrument_drivers", packages=("nanovna-saver",)),
    _planned("instruments.tinysa", "tinySA", "instrument_drivers", packages=("qttinysa",)),
    _planned("instruments.signal_generator", "Signal generator (Bench only, 1.5 s hold: antenna disconnected)", "instrument_drivers"),
    _lease("instruments.noise_figure", "Noise figure (Bench only)", "noisefigure"),
    _planned("instruments.reference", "Reference/GPSDO = LBE-1420", "instrument_drivers"),
    _planned("instruments.calibration", "Frequency/Level calibration", "calibration"),
    _planned("instruments.channel_power", "tinySA channel power", "instrument_drivers"),
    _leaf("instruments.rf_path", "RF path (HMC7992, G6K)", "labd_op", "route"),
    _planned("instruments.scope_capture", "Oscilloscope/LA capture", "instrument_drivers"),
    _planned("instruments.fnb58", "FNB58 logging", "instrument_drivers"),
    _planned("instruments.sled_attenuator", "Sled attenuator step", "sled_attenuator"),
    _planned("instruments.tinysa_survey", "tinySA survey", "instrument_drivers"),
    # Signals AI.
    _planned("signals_ai.live_labels", "Live labels", "labclassify"),
    _leaf("signals_ai.label", "Label on waterfall", "page_only", "learning"),
    _leaf("signals_ai.train", "Train on device (CPU)", "page_only", "learning"),
    _leaf("signals_ai.models", "Models (ONNX export)", "page_only", "model_export"),
    _leaf("signals_ai.dataset_export", "Dataset export / model import (T7)", "page_only", "learning", modules=("storage",),
          t7=True, fallback=NO_T7_DATASET),
    # Recordings: export and update through external storage, a USB stick or microSD (STACK.md:884).
    _planned("recordings.browser", "Browser", "recordings_index"),
    _leaf("recordings.export", "Export (USB stick or microSD)", "page_only", "storage"),
    _planned("recordings.update", "Update (USB stick or microSD)", "update_media"),
    _planned("recordings.t7", "T7 storage", "t7_storage", t7=True, fallback=NO_T7),
    # srrx.location gives the own GNSS position only; the other STACK.md:884 layers are planned.
    _leaf("map_point.live_map", "Live map (own position)", "page_only", "location"),
    _planned("map_point.layers", "Live map layers: aircraft, vessels, sondes, satellite tracks, APRS", "map_layers"),
    _planned("map_point.peak", "Peak on signal (LEO, GEO beacons, Sun, published beacons)", "peak_on_signal"),
    _leaf("gnss_time.fix", "Fix and sky plot", "page_only", "location"),
    _leaf("gnss_time.egnos", "EGNOS (SBAS)", "labd_op", "gnss_config"),
    _leaf("gnss_time.time_sources", "Time sources (UTC verified)", "labd_op", "status"),
    _leaf("gnss_time.reset", "GNSS reset", "labd_op", "gnss_reset"),
    # System.
    _leaf("system.power", "Power", "labd_op", "status"),
    _planned("system.wifi", "Wi-Fi (home only, 1.5 s hold)", "wifi_home"),
    _leaf("system.bluetooth", "Bluetooth", "page_only", "rfkill", hidden="bluetooth_off_permanently"),
    _leaf("system.profiles", "Profiles (FIELD / LAB)", "labd_op", "mode"),
    _leaf("system.storage", "Storage", "page_only", "storage"),
    _planned("system.selftest", "Logs & self-test", "selftest_view"),
    _leaf("system.lime_power", "Lime power cycle (M.2 3.3 V load switch)", "labd_op", "control", lime=True, fallback=NO_LIME),
    _leaf("system.shutdown", "Restart / shut down", "labd_op", "shutdown"),
)


def capabilities(lime=False, t7=False, packages=(), units=(), modules=(), ops=(), presets=None, policy=None):
    """A capability set as hide_reasons() reads it. policy is the output of policy_lists()."""
    return {"lime": bool(lime), "t7": bool(t7), "packages": frozenset(packages), "units": frozenset(units),
            "modules": frozenset(modules), "ops": frozenset(ops), "presets": dict(presets or {}),
            "policy": dict(policy or {})}


def policy_lists(policy):
    """{component: (allow, deny, how)} from a loaded receive-only-policy.json, for the ALLOWLISTS components."""
    out = {}
    for component, (allow, deny, how) in ALLOWLISTS.items():
        entry = policy["components"][component]
        out[component] = (tuple(entry[allow]), tuple(entry[deny]), how)
    return out


def preset_accepted(status):
    """An accepted installation of decoder_policy.availability() (FILE_/LRPT_FILE_PRESET_ACCEPTED_*)."""
    return type(status) is str and "PRESET_ACCEPTED" in status and not status.startswith(("DISABLED", "UNAVAILABLE"))


def allowlist_reason(entry, lists):
    """None when the policy allows the entry; else denied:<component>:<name> or not_allowlisted:<component>:<name>."""
    allow, deny, how = lists.get(entry["component"], ((), (), "token"))
    name = entry["name"].lower()
    if how == "pattern":
        denied = any(fnmatch.fnmatchcase(name, p.lower()) for p in deny)
        allowed = any(fnmatch.fnmatchcase(name, p.lower()) for p in allow)
    else:
        denied = any(t.lower() in name for t in deny)
        allowed = entry["name"] in allow
    if denied:
        return "denied:%s:%s" % (entry["component"], entry["name"])
    return None if allowed else "not_allowlisted:%s:%s" % (entry["component"], entry["name"])


def hide_reasons(leaf, capabilities):
    """Every reason, in a fixed order, why the leaf is hidden with these capabilities; () = visible."""
    caps, backend, needs = capabilities, leaf["backend"], leaf["requires"]
    reasons = []
    if leaf["hidden_reason"] is not None:
        reasons.append("hidden:" + leaf["hidden_reason"])
    if leaf["needs_lime"] and not caps["lime"]:
        reasons.append("no_lime")
    if leaf["needs_t7"] and not caps["t7"]:
        reasons.append("no_t7")
    planned = backend["name"].startswith(PLANNED_PREFIX)
    if planned:
        reasons.append("planned:" + backend["name"][len(PLANNED_PREFIX):])
    for name in needs["packages"]:
        package = PACKAGES[name]
        if package["deferred"]:
            reasons.append("package_deferred:" + name)
        elif not package["binaries"]:
            reasons.append("package_unbuilt:" + name)
        elif name not in caps["packages"]:
            reasons.append("package_missing:" + name)
    reasons += ["unit_missing:" + name for name in needs["units"] if name not in caps["units"]]
    reasons += ["module_missing:" + name for name in needs["modules"] if name not in caps["modules"]]
    if leaf["allowlist"] is not None:
        verdict = allowlist_reason(leaf["allowlist"], caps["policy"])
        if verdict:
            reasons.append(verdict)
    presets = needs["presets"] + ((backend["name"],) if backend["kind"] == "decoder_preset" else ())
    for name in presets:
        status = caps["presets"].get(name)
        if not preset_accepted(status):
            reasons.append("preset:%s=%s" % (name, status or "MISSING"))
    if not planned:
        if backend["kind"] == "labd_op" and backend["name"] not in caps["ops"]:
            reasons.append("labd_op_missing:" + backend["name"])
        elif backend["kind"] == "page_only" and backend["name"] not in caps["modules"]:
            reasons.append("module_missing:" + backend["name"])
        elif backend["kind"] == "engine_unit" and backend["name"] not in caps["units"]:
            reasons.append("unit_missing:" + backend["name"])
    return tuple(dict.fromkeys(reasons))


def visible_leaves(capabilities, leaves=None):
    """Leaves the Lab Shell shows with these capabilities (LEAVES order)."""
    return tuple(leaf for leaf in (LEAVES if leaves is None else leaves) if not hide_reasons(leaf, capabilities))


def hidden_leaves(capabilities, leaves=None):
    """(leaf id, reasons) of every hidden leaf, in LEAVES order."""
    out = []
    for leaf in LEAVES if leaves is None else leaves:
        reasons = hide_reasons(leaf, capabilities)
        if reasons:
            out.append((leaf["id"], reasons))
    return tuple(out)


def referenced(leaves=None):
    """Names the model needs from a root: {"modules", "units", "packages", "presets", "ops"}."""
    out = {key: set() for key in ("modules", "units", "packages", "presets", "ops")}
    for leaf in LEAVES if leaves is None else leaves:
        backend = leaf["backend"]
        for kind in REQUIRE_KINDS:
            out[kind].update(leaf["requires"][kind])
        if backend["name"].startswith(PLANNED_PREFIX):
            continue
        key = {"labd_op": "ops", "page_only": "modules", "engine_unit": "units", "decoder_preset": "presets"}[backend["kind"]]
        out[key].add(backend["name"])
    return {key: tuple(sorted(value)) for key, value in out.items()}


def _text(value, label, limit=240):
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise LabShellMenuError(label + " must be a non-empty string of at most %d characters" % limit)


def _backend(value, label):
    kind = value.get("kind") if type(value) is dict else None
    expected = {"kind", "name", "scope", "program"} if kind == "engine_unit" else {"kind", "name"}
    if kind not in BACKEND_KINDS or set(value) != expected:
        raise LabShellMenuError(label + " backend has an unknown kind or fields")
    _text(value["name"], label + " backend name", 128)
    if value["name"].startswith(PLANNED_PREFIX):
        if value["name"][len(PLANNED_PREFIX):] not in PLANNED:
            raise LabShellMenuError(label + " names a planned backend that PLANNED does not list")
    elif not _NAME.fullmatch(value["name"]):
        raise LabShellMenuError(label + " backend name is not a plain name")
    if kind == "engine_unit" and (value["scope"] not in ("system", "user") or type(value["program"]) is not str
                                  or not _PROGRAM.fullmatch(value["program"]) or not value["name"].endswith(".service")):
        raise LabShellMenuError(label + " unit backend needs a .service name, a system/user scope and a program")


def _requires(value, label):
    if type(value) is not dict or set(value) != set(REQUIRE_KINDS):
        raise LabShellMenuError(label + " requires needs exactly " + ", ".join(REQUIRE_KINDS))
    for kind in REQUIRE_KINDS:
        names = value[kind]
        if type(names) is not tuple or len(set(names)) != len(names) or any(type(n) is not str or not _NAME.fullmatch(n) for n in names):
            raise LabShellMenuError(label + " requires." + kind + " must be a tuple of distinct names")
    if any(name not in PACKAGES for name in value["packages"]):
        raise LabShellMenuError(label + " requires a package that PACKAGES does not list")
    if any(not name.endswith(".service") for name in value["units"]):
        raise LabShellMenuError(label + " requires a unit that is not a .service")


def validate(hubs=None, leaves=None):
    """Raise LabShellMenuError for any schema defect; semantic menu rules are RX-11 findings.
    Without arguments the module's HUBS and LEAVES are checked."""
    hubs = HUBS if hubs is None else hubs
    leaves = LEAVES if leaves is None else leaves
    if type(hubs) not in (tuple, list) or not hubs:
        raise LabShellMenuError("hubs must be a non-empty sequence")
    hub_ids = []
    for hub in hubs:
        if type(hub) is not dict or set(hub) != {"id", "label"} or type(hub["id"]) is not str or not re.fullmatch(r"[a-z][a-z0-9_]*", hub["id"]):
            raise LabShellMenuError("hub entries need exactly a lowercase id and a label")
        _text(hub["label"], "hub " + hub["id"], 64)
        hub_ids.append(hub["id"])
    if len(set(hub_ids)) != len(hub_ids) or HOME in hub_ids:
        raise LabShellMenuError("hub ids must be unique and differ from home")
    seen, scopes = set(), {}
    for leaf in leaves:
        if type(leaf) is not dict or set(leaf) != _LEAF_FIELDS:
            raise LabShellMenuError("leaf entries need exactly the leaf fields")
        if type(leaf["id"]) is not str or not _ID.fullmatch(leaf["id"]) or len(leaf["id"]) > 64 or leaf["id"] in seen:
            raise LabShellMenuError("leaf ids must be unique <hub>.<name> names")
        seen.add(leaf["id"])
        label = "leaf " + leaf["id"]
        if leaf["hub"] not in hub_ids + [HOME] or leaf["id"].split(".", 1)[0] != leaf["hub"]:
            raise LabShellMenuError(label + " names an unknown hub or another hub's prefix")
        _text(leaf["label"], label + " label", 128)
        _backend(leaf["backend"], label)
        _requires(leaf["requires"], label)
        allow = leaf["allowlist"]
        if allow is not None and (type(allow) is not dict or set(allow) != {"component", "name"} or allow["component"] not in ALLOWLISTS
                                  or type(allow["name"]) is not str or not _NAME.fullmatch(allow["name"])):
            raise LabShellMenuError(label + " allowlist needs a policy component of ALLOWLISTS and a name")
        if any(type(leaf[key]) is not bool for key in ("needs_lime", "needs_t7", "critical")):
            raise LabShellMenuError(label + " flags must be booleans")
        if leaf["fallback_text"] is not None:
            _text(leaf["fallback_text"], label + " fallback_text")
        if leaf["hidden_reason"] is not None and leaf["hidden_reason"] not in HIDDEN_REASONS:
            raise LabShellMenuError(label + " hidden_reason is not a HIDDEN_REASONS code")
        controls = leaf["controls"]
        if type(controls) is not dict or set(controls) != {"touch", "keys"} or type(controls["touch"]) is not bool:
            raise LabShellMenuError(label + " controls need exactly touch and keys")
        keys = controls["keys"]
        if type(keys) is not tuple or len(set(keys)) != len(keys) or any(k not in KEYS + ENCODERS for k in keys):
            raise LabShellMenuError(label + " names an unknown key or encoder")
        if not controls["touch"] and not keys:
            raise LabShellMenuError(label + " has no control")
        # A required unit is a system unit (engine leases, STACK.md:76); a unit name has one scope.
        units = [(name, "system") for name in leaf["requires"]["units"]]
        if leaf["backend"]["kind"] == "engine_unit":
            units.append((leaf["backend"]["name"], leaf["backend"]["scope"]))
        for name, scope in units:
            if scopes.setdefault(name, scope) != scope:
                raise LabShellMenuError(label + " names a unit in another scope than an earlier leaf")
    if not leaves:
        raise LabShellMenuError("the menu has no leaves")
