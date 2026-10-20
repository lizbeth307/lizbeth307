"""Portable fail-closed BNO085 configuration/freshness state machine."""
try:
    from .shtp import (CONTROL, INPUT_NORMAL, ROTATION_VECTOR, REPORT_INTERVAL_US,
                       FRESHNESS_MS, ImuError, parse_product_id, product_id_request,
                       set_feature, get_feature, validate_feature_response,
                       parse_sensor_cargo)
except ImportError:
    from shtp import (CONTROL, INPUT_NORMAL, ROTATION_VECTOR, REPORT_INTERVAL_US,
                      FRESHNESS_MS, ImuError, parse_product_id, product_id_request,
                      set_feature, get_feature, validate_feature_response,
                      parse_sensor_cargo)


class ImuSession:
    """Product ID -> verified Get Feature response -> new, fresh samples.

    A fault never re-emits cached orientation. reset() is used only after the
    hardware adapter has reset the sensor and SHTP decoder, not as a clear flag.
    """
    def __init__(self, now_ms=0):
        self.reset(now_ms)

    def reset(self, now_ms):
        self.state = "WAIT_PRODUCT"
        self.started_ms = now_ms
        self._last_now = now_ms
        self.product = None
        self.last_sample_ms = None
        self.next_sample_seq = None
        self.fault = None

    def first_command(self):
        return (CONTROL, product_id_request())

    def failure(self, reason, now_ms):
        self.fault = str(reason)[:48]
        self.state = "FAULT"
        self.last_sample_ms = None
        self.next_sample_seq = None
        return {"ok": False, "fresh": False, "quaternion": None,
                "error": self.fault, "at_ms": now_ms & 0xFFFFFFFF}

    def tick(self, now_ms):
        if self.fault:
            return None
        if now_ms < self._last_now:
            return self.failure("clock_regression", now_ms)
        self._last_now = now_ms
        if self.state == "STREAMING":
            if now_ms - self.last_sample_ms >= FRESHNESS_MS:
                return self.failure("sample_timeout", now_ms)
        elif now_ms - self.started_ms >= 3000:
            return self.failure("configuration_timeout", now_ms)
        return None

    def receive(self, channel, payload, now_ms, rx_latency_ms=0):
        """Return (commands, imu_events); all errors become latched health events."""
        if self.fault:
            return [], []
        commands, events = [], []
        try:
            if now_ms < self._last_now:
                raise ImuError("clock_regression")
            self._last_now = now_ms
            if type(rx_latency_ms) is not int or not 0 <= rx_latency_ms < FRESHNESS_MS:
                raise ImuError("transport_latency")
            if channel == 0:
                return commands, events  # Bounded startup advertisements, no orientation.
            if channel == 1:
                if payload == b"\x01" and self.state == "WAIT_PRODUCT":
                    return commands, events  # Expected initial reset-complete.
                raise ImuError("sensor_reset")
            if channel == CONTROL:
                if payload and payload[0] == 0xF8:
                    product = parse_product_id(payload)
                    if self.state == "WAIT_PRODUCT":
                        self.product = product
                        self.state = "WAIT_FEATURE"
                        commands = [(CONTROL, set_feature()), (CONTROL, get_feature())]
                    # SH-2 can return multiple firmware product entries.
                    return commands, events
                if payload and payload[0] == 0xFC:
                    validate_feature_response(payload)
                    if self.state not in ("WAIT_FEATURE", "WAIT_FIRST", "STREAMING"):
                        raise ImuError("unexpected_feature_response")
                    if self.state == "WAIT_FEATURE":
                        self.state = "WAIT_FIRST"
                    return commands, events
                # Initial SH-2 unsolicited initialization report on control channel.
                if len(payload) == 16 and payload[0] == 0xF1 and payload[2] == 4:
                    if self.state == "WAIT_PRODUCT":
                        return commands, events
                    raise ImuError("sensor_reset")
                raise ImuError("unexpected_control_report")
            if channel != INPUT_NORMAL or self.state not in ("WAIT_FEATURE", "WAIT_FIRST", "STREAMING"):
                raise ImuError("report_before_configuration")
            samples = parse_sensor_cargo(payload)
            if self.state == "WAIT_FEATURE":
                # Set Feature may start streaming before Get Feature's echo.
                # Validate then discard; orientation is withheld until confirmed.
                if any(sample["report_id"] != ROTATION_VECTOR for sample in samples):
                    raise ImuError("unconfigured_report")
                return commands, events
            # Validate the entire batch/sequence before emitting any orientations.
            next_seq = self.next_sample_seq
            for sample in samples:
                if sample["report_id"] != ROTATION_VECTOR:
                    raise ImuError("unconfigured_report")
                sequence = sample["sample_seq"]
                if next_seq is not None and sequence != next_seq:
                    raise ImuError("report_sequence")
                next_seq = (sequence + 1) & 255
                age_ms = (sample["sensor_age_us"] + 999) // 1000 + rx_latency_ms
                if age_ms >= FRESHNESS_MS:
                    raise ImuError("stale_sensor_report")
                if sample["status"] == 0:
                    # CEVA explicitly calls status0 unreliable; disclose without a valid quaternion.
                    event = {"ok": False, "fresh": False, "quaternion": None,
                             "error": "accuracy_unreliable", "status": 0,
                             "report_id": ROTATION_VECTOR, "sample_seq": sequence,
                             "at_ms": now_ms & 0xFFFFFFFF}
                else:
                    event = {"ok": True, "fresh": True,
                             "quaternion": sample["quaternion"],
                             "report_id": ROTATION_VECTOR, "status": sample["status"],
                             "heading_accuracy_rad": sample["heading_accuracy_rad"],
                             "age_ms": age_ms, "at_ms": now_ms & 0xFFFFFFFF,
                             "sample_seq": sequence}
                events.append(event)
            self.next_sample_seq = next_seq
            self.last_sample_ms = now_ms
            self.state = "STREAMING"
        except (ImuError, IndexError, TypeError, ValueError) as error:
            return [], [self.failure(str(error), now_ms)]
        return commands, events
