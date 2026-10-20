"""Validate the separately framed IMU pack stream; never cache valid attitude.

Orientation is optional telemetry and is not a power-readiness input. Calibration
accuracy status is passed through; it does not establish true-north heading.
"""


def _finite(value, low, high):
    return type(value) in (int, float) and value == value and low <= value <= high


class IMURelay:
    def __init__(self):
        self.session = None
        self.last_seq = None
        self.last_good_at = None
        self._await_hello = True
        self._last_error = None
        self._started_at = None
        self._last_age_ms = 0

    def _bad(self, error, now_ms):
        if self._last_error == error:
            return None
        self._last_error = error
        return {"imu": {"ok": False, "fresh": False, "quaternion": None,
                        "error": error, "age_ms": None,
                        "pack_session": self.session, "pack_q": self.last_seq}}

    def invalidate(self, error, now_ms):
        self._await_hello = True
        self.last_good_at = None
        self._started_at = now_ms
        return self._bad(error, now_ms)

    def receive(self, frame, now_ms, rx_age_ms=0):
        if self._started_at is None:
            self._started_at = now_ms
        if (not isinstance(frame, dict) or type(frame.get("v")) is not int
                or frame["v"] != 1 or type(frame.get("s")) is not int
                or not 0 <= frame["s"] <= 0xffffffff
                or type(frame.get("q")) is not int or not 0 <= frame["q"] < 0xffffffff
                or not isinstance(frame.get("p"), dict)):
            self._await_hello = True
            return self._bad("IMU_FRAME", now_ms)
        kind, payload = frame.get("t"), frame["p"]
        hello = (kind == "HELLO" and payload.get("role") == "imu"
                 and type(payload.get("protocol")) is int and payload["protocol"] == 1)
        if frame["s"] != self.session:
            if not hello:
                self._await_hello = True
                return self._bad("IMU_SESSION_NEEDS_HELLO", now_ms)
            self.session = frame["s"]
            self.last_seq = frame["q"]
            self._await_hello = False
            self.last_good_at = None
            self._started_at = now_ms
            return self._bad("IMU_NEW_SESSION", now_ms)
        if frame["q"] <= self.last_seq:
            self._await_hello = True
            return self._bad("IMU_REPLAY", now_ms)
        if frame["q"] != self.last_seq + 1 and not hello:
            self.last_seq = frame["q"]
            self._await_hello = True
            return self._bad("IMU_SEQUENCE_GAP", now_ms)
        self.last_seq = frame["q"]
        if hello:
            self._await_hello = False
            self.last_good_at = None
            self._started_at = now_ms
            return None
        if self._await_hello:
            return self._bad("IMU_NEEDS_HELLO", now_ms)
        if kind != "EVENT" or not isinstance(payload.get("imu"), dict):
            return self._bad("IMU_EVENT_INVALID", now_ms)
        value = payload["imu"]
        if value.get("ok") is not True or value.get("fresh") is not True:
            self._await_hello = True
            error = value.get("error")
            return self._bad(error[:48] if isinstance(error, str) else "IMU_PACK_FAULT", now_ms)
        quaternion = value.get("quaternion")
        if (not isinstance(quaternion, list) or len(quaternion) != 4
                or any(not _finite(part, -1.1, 1.1) for part in quaternion)
                or not 0.7 <= sum(part * part for part in quaternion) <= 1.3
                or type(value.get("report_id")) is not int or value["report_id"] != 5
                or type(value.get("status")) is not int or not 1 <= value["status"] <= 3
                or not _finite(value.get("heading_accuracy_rad"), 0, 16)
                or type(value.get("at_ms")) is not int or not 0 <= value["at_ms"] <= 0xffffffff
                or type(value.get("sample_seq")) is not int or not 0 <= value["sample_seq"] <= 255
                or type(value.get("age_ms")) is not int or not 0 <= value["age_ms"] < 500):
            self._await_hello = True
            return self._bad("IMU_REPORT_INVALID", now_ms)
        age = value["age_ms"] + rx_age_ms
        if age >= 500:
            return self.invalidate("IMU_RX_STALE", now_ms)
        self.last_good_at = now_ms
        self._last_age_ms = age
        self._last_error = None
        # Whitelist to keep outgoing EVENT bounded and reject hidden payloads.
        result = {key: value.get(key) for key in ("quaternion", "report_id", "status",
                                                 "heading_accuracy_rad", "at_ms", "sample_seq")}
        result.update({"ok": True, "fresh": True, "age_ms": age,
                       "pack_session": self.session, "pack_q": self.last_seq})
        return {"imu": result}

    def forwarding(self, payload, received_at, now_ms):
        if payload["imu"]["ok"]:
            age = payload["imu"]["age_ms"] + max(0, now_ms - received_at)
            if age >= 500:
                return self.invalidate("IMU_FORWARD_STALE", now_ms)
            payload["imu"]["age_ms"] = age
        return payload

    def step(self, now_ms):
        if self._started_at is None:
            self._started_at = now_ms
        reference = self.last_good_at if self.last_good_at is not None else self._started_at
        age = self._last_age_ms if self.last_good_at is not None else 0
        if now_ms - reference + age >= 500:
            self._await_hello = True
            return self._bad("IMU_STALE", now_ms)
        return None
