"""Declarative menu of the local touch console (srrx.hmi), evaluated by selftest RX-11.

Pure data and a schema check: no Qt, no I/O, no labd call. srrx.hmi builds its tabs in
PAGES order and refuses to start when a built tab differs from its entry. Each leaf
names the control as the console shows it, the backend it reaches and the inputs that
operate it; deployment/selftest.py RX-11 (build/07 §23 row 11, STACK.md:884) checks
every backend against a staged rootfs, requires a declared no-Lime/no-T7 backend for
each Lime/T7 leaf and a key or encoder for each critical leaf (STACK.md:110: the
capacitive panel does not work through gloves). The model describes the console as
built and adds no control: fallback_text is a declaration, the console does not show it.
"""
import re

# firmware/pico/hmi.py KEY_NAMES, in counter order; GESTURES[i] is what srrx.hmi.HMINavigation
# makes of KEYS[i] (HMI.md table). ENC1 turns pages, ENC2 scrolls the current page.
KEYS = ("HOME", "BACK", "REC", "MARK", "FN", "LOCK", "ENC1_PRESS", "ENC2_PRESS")
GESTURES = ("home", "back", "rec_note", "mark", "next_page", "lock", "focus_next", "focus_prev")
ENCODERS = ("ENC1", "ENC2")
BACKEND_KINDS = ("labd_op", "engine_unit", "decoder_preset", "page_only")
FRAME = "frame"  # the window around the tabs: command row, bottom row and the physical inputs
PAGES = ({"id": "overview", "label": "Overview"}, {"id": "receiver", "label": "Receiver"},
         {"id": "spectrum", "label": "Spectrum"}, {"id": "location", "label": "Location"},
         {"id": "learning", "label": "Teach / Classify"}, {"id": "bench", "label": "Bench"})
# Units every console leaf depends on: labd answers labd_op leaves, the user unit runs the console.
LABD_UNIT = {"kind": "engine_unit", "name": "srrx.service", "scope": "system", "program": "srrx.daemon"}
CONSOLE_UNIT = {"kind": "engine_unit", "name": "srrx-menu.service", "scope": "user", "program": "srrx.hmi"}
# Bench rows in srrx.hmi.EN_OUTPUTS order; the two optional loads declare their no-module backend.
OUTPUTS = tuple("EN_" + name for name in (
    "LNA1", "LNA2", "LNA3", "LNA4", "LNB", "BONI", "SB_LNA", "RTLA",
    "RTLB", "HFP", "LIME3V3", "T7", "LABPORT", "AUX12"))
NO_LIME = "No Lime build: EN_LIME3V3 stays OFF (OFF needs no lease in labd); RTL-A, RTL-B and HF+ cover reception"
NO_T7 = "No T7: EN_T7 stays OFF; storage falls back to UFS and the V30 microSD (STACK.md:977)"

_LEAF_FIELDS = frozenset(("id", "page", "label", "backend", "needs_lime", "needs_t7", "fallback_text", "critical", "controls"))
_ID = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z0-9_]+){0,3}\Z")
_PROGRAM = re.compile(r"srrx\.[a-z_]+\Z|/[A-Za-z0-9_./+-]+\Z")


class MenuModelError(ValueError):
    """Schema defect of the menu model; the text names the leaf or page, never runtime data."""


def _leaf(leaf_id, page, label, kind, name, *, touch=True, keys=(), critical=False, lime=False, t7=False, fallback=None):
    return {"id": leaf_id, "page": page, "label": label, "backend": {"kind": kind, "name": name},
            "needs_lime": lime, "needs_t7": t7, "fallback_text": fallback, "critical": critical,
            "controls": {"touch": touch, "keys": tuple(keys)}}


LEAVES = (
    # Command row and bottom row (touch). DISARM is critical and touch-only: RX-11 reports it BLOCKED
    # until a physical DISARM path exists; the Pico input core has no power API (firmware/pico/hmi.py).
    _leaf("frame.arm", FRAME, "ARM + HOLD", "labd_op", "arm"),
    _leaf("frame.recover", FRAME, "RECOVER + ARM", "labd_op", "recover"),
    _leaf("frame.disarm", FRAME, "DISARM / STOP", "labd_op", "disarm", critical=True),
    _leaf("frame.hold", FRAME, "HOLD lease", "labd_op", "lease"),
    _leaf("frame.shutdown", FRAME, "Shutdown…", "labd_op", "shutdown"),
    _leaf("frame.unlock", FRAME, "Unlock touch…", "page_only", "hmi"),
    _leaf("frame.close", FRAME, "Close + DISARM", "labd_op", "disarm"),
    # Physical inputs (srrx.hmi.HMINavigation): they navigate and lock, they never power anything.
    _leaf("frame.home", FRAME, "HOME", "page_only", "hmi", touch=False, keys=("HOME",), critical=True),
    _leaf("frame.back", FRAME, "BACK", "page_only", "hmi", touch=False, keys=("BACK",), critical=True),
    _leaf("frame.next_page", FRAME, "FN", "page_only", "hmi", touch=False, keys=("FN",), critical=True),
    _leaf("frame.page_turn", FRAME, "ENC1", "page_only", "hmi", touch=False, keys=("ENC1",), critical=True),
    _leaf("frame.scroll", FRAME, "ENC2", "page_only", "hmi", touch=False, keys=("ENC2",), critical=True),
    _leaf("frame.focus", FRAME, "ENC1_PRESS / ENC2_PRESS", "page_only", "hmi", touch=False,
          keys=("ENC1_PRESS", "ENC2_PRESS"), critical=True),
    _leaf("frame.lock", FRAME, "LOCK", "page_only", "hmi", touch=False, keys=("LOCK",), critical=True),
    _leaf("frame.mark", FRAME, "MARK", "page_only", "hmi", touch=False, keys=("MARK",)),
    _leaf("frame.rec_note", FRAME, "REC", "page_only", "hmi", touch=False, keys=("REC",)),
    # Overview: status cards, protection fault and channel table, shown by HOME without touch.
    _leaf("overview.status", "overview", "Overview", "labd_op", "status", touch=False, keys=("HOME",), critical=True),
    _leaf("overview.diagnostics", "overview", "Controller diagnostics…", "page_only", "hmi"),
    # Receiver: the SIM capture runs `python -m srrx.labrx --simulate`; routes and relay go to labd.
    _leaf("receiver.sim_capture", "receiver", "Start SIM capture · 10 frames", "page_only", "labrx"),
    _leaf("receiver.route.rtla", "receiver", "Apply route", "labd_op", "route"),
    _leaf("receiver.route.rtlb", "receiver", "Apply route", "labd_op", "route"),
    _leaf("receiver.route.lime", "receiver", "Apply route", "labd_op", "route", lime=True,
          fallback="No Lime build: keep LIME on PARK; the route switch has no receiver behind it"),
    _leaf("receiver.relay", "receiver", "Apply HF relay", "labd_op", "relay"),
    _leaf("spectrum.load", "spectrum", "Load spectrum JSON / survey JSONL", "page_only", "spectrum"),
    _leaf("location.load", "location", "Load saved position…", "page_only", "hmi"),
    _leaf("location.live", "location", "Return to live position", "page_only", "location"),
    _leaf("location.manual", "location", "Use manual location", "page_only", "location"),
    _leaf("location.jump", "location", "Confirm position move (>100 km)…", "page_only", "geo_look"),
    _leaf("location.pass_plan", "location", "Load pass plan…", "page_only", "passes"),
    _leaf("location.diagnostics", "location", "Location diagnostics…", "page_only", "hmi"),
    _leaf("learning.confirm", "learning", "I explicitly confirm this coarse label and independent capture grouping",
          "page_only", "learning"),
    _leaf("learning.annotate", "learning", "Add annotation", "page_only", "learning"),
    _leaf("learning.train", "learning", "Train CPU model", "page_only", "learning"),
    _leaf("learning.infer", "learning", "Classify selected bins", "page_only", "learning"),
    _leaf("learning.new_group", "learning", "New independent session…", "page_only", "hmi"),
    _leaf("learning.load_dataset", "learning", "Load dataset", "page_only", "learning"),
    _leaf("learning.save_dataset", "learning", "Save dataset", "page_only", "learning"),
    _leaf("learning.load_model", "learning", "Load model", "page_only", "learning"),
    _leaf("learning.save_model", "learning", "Save model", "page_only", "learning"),
    _leaf("learning.cancel", "learning", "Cancel learning job", "page_only", "hmi"),
    _leaf("learning.diagnostics", "learning", "Learning diagnostics…", "page_only", "hmi"),
    _leaf("bench.mode.field", "bench", "Stage FIELD", "labd_op", "mode"),
    _leaf("bench.mode.lab", "bench", "Stage LAB", "labd_op", "mode"),
    _leaf("bench.confirm.bench_loads", "bench", "Bench loads connected and checked", "labd_op", "confirmations"),
    _leaf("bench.confirm.boni_connected", "bench", "Boni antenna/module connected", "labd_op", "confirmations"),
    _leaf("bench.confirm.boni_profile", "bench", "Boni profile/current window checked", "labd_op", "confirmations"),
) + tuple(_leaf("bench.output." + name[3:].lower(), "bench", name, "labd_op", "control",
                lime=name == "EN_LIME3V3", t7=name == "EN_T7",
                fallback=NO_LIME if name == "EN_LIME3V3" else NO_T7 if name == "EN_T7" else None)
          for name in OUTPUTS)


def page_index(page_id):
    """Tab index of a page in the console (PAGES order)."""
    for index, page in enumerate(PAGES):
        if page["id"] == page_id:
            return index
    raise MenuModelError("unknown page " + str(page_id)[:64])


def _text(value, label, limit=240):
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise MenuModelError(label + " must be a non-empty string of at most %d characters" % limit)


def _backend(value, label):
    kind = value.get("kind") if type(value) is dict else None
    expected = {"kind", "name", "scope", "program"} if kind == "engine_unit" else {"kind", "name"}
    if kind not in BACKEND_KINDS or set(value) != expected:
        raise MenuModelError(label + " backend has an unknown kind or fields")
    _text(value["name"], label + " backend name", 128)
    if kind == "engine_unit" and (value["scope"] not in ("system", "user") or type(value["program"]) is not str
                                  or not _PROGRAM.fullmatch(value["program"]) or not value["name"].endswith(".service")):
        raise MenuModelError(label + " unit backend needs a .service name, a system/user scope and a program")


def validate(pages=None, leaves=None):
    """Raise MenuModelError for any schema defect; semantic row-11 rules are RX-11 findings.
    Without arguments the module's current PAGES and LEAVES are checked."""
    pages = PAGES if pages is None else pages
    leaves = LEAVES if leaves is None else leaves
    if type(pages) not in (tuple, list) or not pages:
        raise MenuModelError("pages must be a non-empty sequence")
    page_ids = []
    for page in pages:
        if type(page) is not dict or set(page) != {"id", "label"} or type(page["id"]) is not str or not _ID.fullmatch(page["id"]):
            raise MenuModelError("page entries need exactly a lowercase id and a label")
        _text(page["label"], "page " + page["id"], 64)
        page_ids.append(page["id"])
    if len(set(page_ids)) != len(page_ids) or FRAME in page_ids:
        raise MenuModelError("page ids must be unique and differ from the frame")
    seen = set()
    for leaf in leaves:
        if type(leaf) is not dict or set(leaf) != _LEAF_FIELDS:
            raise MenuModelError("leaf entries need exactly the leaf fields")
        if type(leaf["id"]) is not str or not _ID.fullmatch(leaf["id"]) or len(leaf["id"]) > 64 or leaf["id"] in seen:
            raise MenuModelError("leaf ids must be unique dotted lowercase names")
        seen.add(leaf["id"])
        label = "leaf " + leaf["id"]
        if leaf["page"] not in page_ids and leaf["page"] != FRAME:
            raise MenuModelError(label + " names an unknown page")
        _text(leaf["label"], label + " label", 128)
        _backend(leaf["backend"], label)
        if any(type(leaf[key]) is not bool for key in ("needs_lime", "needs_t7", "critical")):
            raise MenuModelError(label + " flags must be booleans")
        if leaf["fallback_text"] is not None:
            _text(leaf["fallback_text"], label + " fallback_text")
        controls = leaf["controls"]
        if type(controls) is not dict or set(controls) != {"touch", "keys"} or type(controls["touch"]) is not bool:
            raise MenuModelError(label + " controls need exactly touch and keys")
        keys = controls["keys"]
        if type(keys) is not tuple or len(set(keys)) != len(keys) or any(k not in KEYS + ENCODERS for k in keys):
            raise MenuModelError(label + " names an unknown key or encoder")
        if not controls["touch"] and not keys:
            raise MenuModelError(label + " has no control")
    if not leaves:
        raise MenuModelError("the menu has no leaves")
