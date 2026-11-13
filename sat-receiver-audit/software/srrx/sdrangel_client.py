"""labd's SDRangel REST client: the Airspy HF+ LO correction (LOppmTenths) per preset (stdlib only).

libairspyhf reads the flash-stored calibration_ppb when a receiver is opened and applies it, but
SDRangel 7.27.2 overwrites it with LOppmTenths x 100 on every init and start
(plugins/samplesource/airspyhf/airspyhfinput.cpp:467-476 at 97e9e21, airspyhf_set_calibration;
the default LOppmTenths is 0, airspyhfsettings.cpp:32). labd therefore writes LOppmTenths =
round(ppb/100) into every AirspyHF preset of sdrangelsrv over its REST API and reads it back after
each preset load (STACK.md:143, build/07-pz-vstanovlennia.md:324). labrx adds no correction.

- lo_ppm_tenths(ppb): integer ppb to tenths of a ppm, halves away from zero (Python's round()
  would give 2 for 250 ppb), within the GUI range -100..100 (+-10.0 ppm, airspyhfgui.ui:174-185).
- RestTransport: JSON over HTTP to http://127.0.0.1:<port> or http://[::1]:<port> only; the
  lease starts sdrangelsrv with -a 127.0.0.1 -p 8091 (software/systemd/srrx-lease-sdrangelsrv@.service;
  DEFAULT_URL is that address), so any other host is refused before a connection is made. One
  sdrangelsrv lease at a time owns that port (build/15, «SDRangel: один sdrangelsrv»). A
  connection factory can be given (the tests use an AF_UNIX one: the host regression denies
  AF_INET sockets).
- SdrangelClient.push_live_lo_ppm(ppb, device_set): PATCH the running AirspyHF device set with
  LOppmTenths and read it back; verify_live_lo_ppm() is the read-back alone. This is the lease
  path: each lease starts sdrangelsrv with an empty HOME (RuntimeDirectory=), so there are no
  device sets and no presets, and a preset saved there is gone when the lease ends.
- SdrangelClient.push_lo_ppm(ppb, device_set, presets): for each preset: load it, PATCH the
  AirspyHF device settings with LOppmTenths, read it back, save the preset (PUT
  /sdrangel/preset), load it again and read LOppmTenths back once more. A load is PATCH
  /sdrangel/preset (202: queued) after the device was moved 1 Hz off the preset's centre
  frequency, then polling until the device shows that frequency again, so a GET never reads
  the settings from before the load. verify_lo_ppm() is the read-back alone, after each load.
  Every mismatch is refused (LO_PPM_MISMATCH).

The lease contract for labd (its call is not wired yet, OPEN): after the lease unit starts, POST
/sdrangel/deviceset?direction=0 and wait until GET /sdrangel lists the new set, PUT
/sdrangel/deviceset/{i}/device with {"hwType": "AirspyHF", "serial": <HF+ serial of
/etc/srrx/devices.json>, "direction": 0}, then push_live_lo_ppm(); after every later preset load
(which carries the preset's own LOppmTenths) push_live_lo_ppm() again or verify_live_lo_ppm().
Presets labd imports into the lease (PUT /sdrangel/preset/file from var/lib/lab/sdrangel, a
policy config path) go through push_lo_ppm() before they are used.

The REST paths and JSON fields are those of sdrbase/resources/webapi/doc/swagger/swagger.yaml at
97e9e21 (/sdrangel, /sdrangel/presets, /sdrangel/preset, /sdrangel/deviceset/{i}/device/settings;
DeviceSettings.deviceHwType, airspyHFSettings.LOppmTenths). Host-tested against a fake REST
server (software/tests/test_sdrangel_client.py); the read-back on a Q6A with an HF+ is the device
row HF-5 (build/09-testy.md:161). Refusals are stable codes (ERRORS) and carry no response body.
"""
import http.client
import ipaddress
import json
import time
from urllib.parse import urlencode, urlsplit

DEFAULT_URL = "http://127.0.0.1:8091"  # the lease's -a 127.0.0.1 -p 8091 (a host test compares them)
HWTYPE = "AirspyHF"
LO_PPM_TENTHS_LIMIT = 100
LOAD_TIMEOUT_S = 10.0
POLL_S = 0.2
ERRORS = ("SDRANGEL_NOT_LOOPBACK", "SDRANGEL_BAD_PPB", "SDRANGEL_PPB_OUT_OF_RANGE", "SDRANGEL_HTTP", "SDRANGEL_BAD_REPLY",
          "SDRANGEL_NOT_AIRSPYHF", "SDRANGEL_NO_PRESET", "SDRANGEL_PRESET_NOT_LOADED", "LO_PPM_MISMATCH")


class SdrangelError(ValueError):
    """A refusal with a stable code (ERRORS)."""

    def __init__(self, code, detail=""):
        if code not in ERRORS:
            raise ValueError("unknown SDRangel client error code: " + str(code))
        self.code, self.detail = code, detail
        super().__init__(code + (": " + detail if detail else ""))


def lo_ppm_tenths(ppb):
    """LOppmTenths for a flash calibration of `ppb` parts per billion: round(ppb/100), halves away
    from zero. Refuses a non-integer ppb and a result outside -100..100 (the GUI range)."""
    if type(ppb) is not int:
        raise SdrangelError("SDRANGEL_BAD_PPB", "ppb must be an integer")
    tenths = (abs(ppb) + 50) // 100
    tenths = -tenths if ppb < 0 else tenths
    if abs(tenths) > LO_PPM_TENTHS_LIMIT:
        raise SdrangelError("SDRANGEL_PPB_OUT_OF_RANGE", "LOppmTenths %d outside -%d..%d" % (tenths, LO_PPM_TENTHS_LIMIT, LO_PPM_TENTHS_LIMIT))
    return tenths


def loopback_endpoint(url):
    """(host, port) of an http URL whose host is a loopback IP literal; anything else is refused."""
    parts = urlsplit(url)
    try:
        port = parts.port
        address = ipaddress.ip_address(parts.hostname or "")
    except ValueError:
        raise SdrangelError("SDRANGEL_NOT_LOOPBACK", "not an http://<loopback IP>:<port> URL") from None
    if (parts.scheme != "http" or not address.is_loopback or port is None or not 1024 <= port <= 65535
            or parts.path not in ("", "/") or parts.query or parts.fragment or parts.username or parts.password):
        raise SdrangelError("SDRANGEL_NOT_LOOPBACK", "not an http://<loopback IP>:<port> URL")
    return str(address), port


class RestTransport:
    """request(method, path, body=None, query=None) -> (status, decoded JSON or None)."""

    def __init__(self, url=DEFAULT_URL, timeout=5.0, connection_factory=None):
        self.host, self.port = loopback_endpoint(url)
        self.timeout = timeout
        self.connection_factory = connection_factory or (lambda: http.client.HTTPConnection(self.host, self.port, timeout=self.timeout))

    def request(self, method, path, body=None, query=None):
        target = path + ("?" + urlencode(query) if query else "")
        payload = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers = {"Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        connection = self.connection_factory()
        try:
            connection.request(method, target, body=payload, headers=headers)
            response = connection.getresponse()
            data = response.read()
            status = response.status
        except (OSError, http.client.HTTPException) as exc:
            raise SdrangelError("SDRANGEL_HTTP", "%s %s: %s" % (method, path, type(exc).__name__)) from None
        finally:
            connection.close()
        if not data:
            return status, None
        try:
            return status, json.loads(data.decode("utf-8"))
        except ValueError:
            raise SdrangelError("SDRANGEL_BAD_REPLY", "%s %s: not JSON" % (method, path)) from None


def _preset_id(preset):
    """A PresetIdentifier (swagger.yaml): groupName, centerFrequency, type, name; Rx presets only."""
    if type(preset) is not dict:
        raise SdrangelError("SDRANGEL_NO_PRESET", "a preset is an object")
    group, frequency, kind, name = (preset.get(k) for k in ("groupName", "centerFrequency", "type", "name"))
    if type(group) is not str or type(name) is not str or type(frequency) is not int or kind != "R":
        raise SdrangelError("SDRANGEL_NO_PRESET", "a preset needs groupName, centerFrequency, name and type R")
    return {"groupName": group, "centerFrequency": frequency, "type": kind, "name": name}


class SdrangelClient:
    def __init__(self, transport=None, load_timeout=LOAD_TIMEOUT_S, poll=POLL_S, clock=time.monotonic, sleep=time.sleep):
        self.transport = transport or RestTransport()
        self.load_timeout, self.poll, self.clock, self.sleep = load_timeout, poll, clock, sleep

    def _call(self, method, path, expect, body=None, query=None):
        status, data = self.transport.request(method, path, body=body, query=query)
        if status != expect:
            raise SdrangelError("SDRANGEL_HTTP", "%s %s gave %s, expected %s" % (method, path, status, expect))
        if type(data) is not dict:
            raise SdrangelError("SDRANGEL_BAD_REPLY", "%s %s: no JSON object" % (method, path))
        return data

    def device_hwtype(self, device_set):
        summary = self._call("GET", "/sdrangel", 200)
        sets = ((summary.get("devicesetlist") or {}).get("deviceSets")) or []
        if type(device_set) is not int or not 0 <= device_set < len(sets):
            raise SdrangelError("SDRANGEL_NOT_AIRSPYHF", "no device set %r" % (device_set,))
        return ((sets[device_set] or {}).get("samplingDevice") or {}).get("hwType")

    def rx_presets(self):
        """Every Rx preset of GET /sdrangel/presets as a PresetIdentifier."""
        listing = self._call("GET", "/sdrangel/presets", 200)
        found = []
        for group in listing.get("groups") or []:
            for item in group.get("presets") or []:
                if item.get("type") == "R":
                    found.append(_preset_id(dict(item, groupName=group.get("groupName"))))
        return found

    def airspyhf_settings(self, device_set):
        data = self._call("GET", "/sdrangel/deviceset/%d/device/settings" % device_set, 200)
        settings = data.get("airspyHFSettings")
        if data.get("deviceHwType") != HWTYPE or type(settings) is not dict:
            raise SdrangelError("SDRANGEL_NOT_AIRSPYHF", "device set %d holds %s" % (device_set, data.get("deviceHwType")))
        return settings

    def _wait(self, device_set, done):
        """Poll the AirspyHF settings until done(settings) or the load timeout; returns (ok, settings).
        SDRangel applies device PATCHes and preset loads through message queues, so a GET right
        after them may still show the previous values."""
        deadline = self.clock() + self.load_timeout
        while True:
            settings = self.airspyhf_settings(device_set)
            if done(settings):
                return True, settings
            if self.clock() >= deadline:
                return False, settings
            self.sleep(self.poll)

    def _patch_device(self, device_set, values):
        return self._call("PATCH", "/sdrangel/deviceset/%d/device/settings" % device_set, 200,
                          body={"deviceHwType": HWTYPE, "direction": 0, "airspyHFSettings": dict(values)})

    def load_preset(self, device_set, preset):
        """Load one preset into the AirspyHF device set and return the device settings once the load
        has landed. The load is asynchronous (202, MsgLoadPreset), and the device may already sit
        on the preset's centre frequency, so the device is first moved 1 Hz off it (a marker the
        load must overwrite): only then does the preset's frequency prove that this load landed."""
        marker = preset["centerFrequency"] + 1
        self._patch_device(device_set, {"centerFrequency": marker})
        if not self._wait(device_set, lambda s: s.get("centerFrequency") == marker)[0]:
            raise SdrangelError("SDRANGEL_PRESET_NOT_LOADED", "%s/%s: the device did not take the marker frequency"
                                % (preset["groupName"], preset["name"]))
        self._call("PATCH", "/sdrangel/preset", 202, body={"deviceSetIndex": device_set, "preset": preset})
        landed, settings = self._wait(device_set, lambda s: s.get("centerFrequency") == preset["centerFrequency"])
        if not landed:
            raise SdrangelError("SDRANGEL_PRESET_NOT_LOADED", "%s/%s" % (preset["groupName"], preset["name"]))
        return settings

    @staticmethod
    def _check(settings, preset, expected, stage):
        value = settings.get("LOppmTenths")
        if value != expected:
            raise SdrangelError("LO_PPM_MISMATCH", "%s/%s %s: LOppmTenths %r, expected %d"
                                % (preset["groupName"], preset["name"], stage, value, expected))

    def _targets(self, device_set, presets):
        if self.device_hwtype(device_set) != HWTYPE:
            raise SdrangelError("SDRANGEL_NOT_AIRSPYHF", "device set %d is not an AirspyHF" % device_set)
        chosen = self.rx_presets() if presets is None else [_preset_id(p) for p in presets]
        if not chosen:
            raise SdrangelError("SDRANGEL_NO_PRESET", "no Rx preset")
        return chosen

    def push_lo_ppm(self, ppb, device_set, presets=None):
        """Write LOppmTenths = round(ppb/100) into each preset (default: every Rx preset) through the
        AirspyHF device set and read it back after the write and after reloading the saved preset."""
        expected = lo_ppm_tenths(ppb)
        done = []
        for preset in self._targets(device_set, presets):
            self.load_preset(device_set, preset)
            reply = self._patch_device(device_set, {"LOppmTenths": expected})
            if (reply.get("airspyHFSettings") or {}).get("LOppmTenths") != expected:
                raise SdrangelError("LO_PPM_MISMATCH", "%s/%s: the PATCH reply does not carry LOppmTenths %d"
                                    % (preset["groupName"], preset["name"], expected))
            self._check(self._wait(device_set, lambda s: s.get("LOppmTenths") == expected)[1], preset, expected, "after the write")
            self._call("PUT", "/sdrangel/preset", 202, body={"deviceSetIndex": device_set, "preset": preset})
            self._check(self.load_preset(device_set, preset), preset, expected, "after reloading the saved preset")
            done.append(dict(preset))
        return {"status": "LO_PPM_WRITTEN", "lo_ppm_tenths": expected, "ppb": ppb, "device_set": device_set, "presets": done,
                "hardware_ready": False}

    def verify_lo_ppm(self, ppb, device_set, presets=None):
        """Load each preset and refuse unless LOppmTenths equals round(ppb/100) (STACK.md:143)."""
        expected = lo_ppm_tenths(ppb)
        checked = []
        for preset in self._targets(device_set, presets):
            self._check(self.load_preset(device_set, preset), preset, expected, "after loading")
            checked.append(dict(preset))
        return {"status": "LO_PPM_VERIFIED", "lo_ppm_tenths": expected, "ppb": ppb, "device_set": device_set, "presets": checked,
                "hardware_ready": False}

    def _live(self, device_set):
        if self.device_hwtype(device_set) != HWTYPE:
            raise SdrangelError("SDRANGEL_NOT_AIRSPYHF", "device set %d is not an AirspyHF" % device_set)
        return {"groupName": "device set %d" % device_set, "name": "live settings"}

    def push_live_lo_ppm(self, ppb, device_set):
        """Write LOppmTenths = round(ppb/100) into the running AirspyHF device set (no preset: the
        lease path) and read it back until it has landed; a mismatch is refused."""
        expected = lo_ppm_tenths(ppb)
        label = self._live(device_set)
        reply = self._patch_device(device_set, {"LOppmTenths": expected})
        if (reply.get("airspyHFSettings") or {}).get("LOppmTenths") != expected:
            raise SdrangelError("LO_PPM_MISMATCH", "%s: the PATCH reply does not carry LOppmTenths %d" % (label["groupName"], expected))
        self._check(self._wait(device_set, lambda s: s.get("LOppmTenths") == expected)[1], label, expected, "after the write")
        return {"status": "LO_PPM_LIVE_WRITTEN", "lo_ppm_tenths": expected, "ppb": ppb, "device_set": device_set, "presets": [],
                "hardware_ready": False}

    def verify_live_lo_ppm(self, ppb, device_set):
        """Refuse unless the running AirspyHF device set holds LOppmTenths = round(ppb/100)."""
        expected = lo_ppm_tenths(ppb)
        label = self._live(device_set)
        self._check(self.airspyhf_settings(device_set), label, expected, "now")
        return {"status": "LO_PPM_LIVE_VERIFIED", "lo_ppm_tenths": expected, "ppb": ppb, "device_set": device_set, "presets": [],
                "hardware_ready": False}
