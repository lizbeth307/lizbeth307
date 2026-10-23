import collections
import datetime as dt
import json
import unittest
from unittest.mock import patch

from srrx.location import (GpsdClient, GpsdJSONDecoder, LocationTracker,
                           MAX_GPSD_BYTES, MAX_INPUT_BYTES, MAX_NMEA_BYTES)


def tpv(second=0, **updates):
    report = {"class": "TPV", "device": "configured-gnss-device", "mode": 3,
              "time": "2026-10-20T12:00:%02d.000Z" % second,
              "lat": 50.0, "lon": 20.0, "eph": 4.5,
              "speed": 0.0, "track": 0.0, "altMSL": 120.0, "altHAE": 155.0}
    report.update(updates)
    return report


def nmea(body):
    checksum = 0
    for byte in body.encode("ascii"):
        checksum ^= byte
    return ("$%s*%02X\r\n" % (body, checksum)).encode("ascii")


def rmc(time="120000.000", date="201026", **changes):
    fields = ["GNRMC", time, "A", "5000.000000", "N", "02000.000000", "E",
              "0.0", "0.0", date, "", "", "A", "V"]
    for key, value in changes.items():
        fields[int(key)] = value
    return nmea(",".join(fields))


def gga(time="120000.000", **changes):
    fields = ["GNGGA", time, "5000.000000", "N", "02000.000000", "E", "1", "08",
              "0.9", "120.0", "M", "35.0", "M", "", ""]
    for key, value in changes.items():
        fields[int(key)] = value
    return nmea(",".join(fields))


class GpsdTrackingTests(unittest.TestCase):
    def test_valid_gpsd_position_reports_source_age_and_unknown_confidence(self):
        tracker = LocationTracker()
        self.assertTrue(tracker.ingest_gpsd(tpv(), 100))
        status = tracker.status(200)
        self.assertTrue(status["available"])
        self.assertTrue(status["fresh"])
        self.assertEqual((status["source"], status["origin"], status["age_ms"]), ("gpsd", "gpsd", 100))
        self.assertEqual((status["lat"], status["lon"]), (50.0, 20.0))
        self.assertEqual(status["uncertainty_m"], 4.5)
        self.assertEqual(status["uncertainty_confidence"], "unknown")
        self.assertFalse(status["utc_verified"])

    def test_freshness_boundary_and_last_good_error_not_current_radius(self):
        tracker = LocationTracker()
        tracker.ingest_gpsd(tpv(), 0)
        self.assertTrue(tracker.status(2999)["fresh"])
        status = tracker.status(3000)
        self.assertEqual(status["source"], "last_good")
        self.assertFalse(status["fresh"])
        self.assertEqual(status["age_ms"], 3000)
        self.assertIsNone(status["uncertainty_m"])
        self.assertEqual(status["fix_uncertainty_m"], 4.5)
        self.assertEqual(status["uncertainty_basis"], "stale_position_unbounded")

    def test_missing_optional_fields_do_not_refresh_cached_coordinates(self):
        tracker = LocationTracker()
        tracker.ingest_gpsd(tpv(), 0)
        self.assertFalse(tracker.ingest_gpsd({"class": "TPV", "mode": 3,
                                           "device": "configured-gnss-device"}, 2500))
        self.assertEqual(tracker.status(3000)["source"], "last_good")

    def test_duplicate_epoch_enriches_accuracy_without_refreshing_age(self):
        tracker = LocationTracker()
        tracker.ingest_gpsd(tpv(), 0)
        self.assertFalse(tracker.ingest_gpsd(tpv(eph=2.0), 2500))
        self.assertEqual(tracker.status(2500)["age_ms"], 2500)
        self.assertEqual(tracker.status(2500)["uncertainty_m"], 2.0)
        self.assertFalse(tracker.status(3000)["fresh"])

    def test_no_fix_and_impossible_fixes_preserve_last_good_only(self):
        cases = ({"mode": 1}, {"lat": 91}, {"lon": -181}, {"lat": True}, {"lat": 10 ** 500},
                 {"lat": float("nan")}, {"eph": float("inf")}, {"eph": -1},
                 {"speed": 101}, {"track": 360}, {"altHAE": 1e9},
                 {"status": True}, {"status": 5}, {"status": 6}, {"status": 8})
        for changes in cases:
            with self.subTest(changes=changes):
                tracker = LocationTracker()
                tracker.ingest_gpsd(tpv(), 0)
                self.assertFalse(tracker.ingest_gpsd(tpv(1, **changes), 1000))
                status = tracker.status(1000)
                self.assertEqual(status["source"], "last_good")
                self.assertEqual((status["lat"], status["lon"]), (50, 20))
                json.dumps(status, allow_nan=False)

    def test_axis_uncertainties_and_missing_accuracy_are_explicit(self):
        tracker = LocationTracker()
        report = tpv(epx=3.0, epy=4.0)
        del report["eph"]
        tracker.ingest_gpsd(report, 0)
        status = tracker.status(0)
        self.assertEqual(status["uncertainty_m"], 5.0)
        self.assertEqual(status["uncertainty_basis"], "gpsd_axis_rss")
        tracker = LocationTracker()
        del report["epx"], report["epy"]
        tracker.ingest_gpsd(report, 0)
        self.assertIsNone(tracker.status(0)["uncertainty_m"])

    def test_separate_gpsd_gst_enriches_same_epoch_without_new_fix(self):
        tracker = LocationTracker()
        tracker.ingest_gpsd(tpv(), 0)
        gst = {"class": "GST", "device": "configured-gnss-device",
               "time": "2026-10-20T12:00:00Z", "lat": 3, "lon": 4}
        self.assertFalse(tracker.ingest_gpsd(gst, 1000))
        self.assertEqual(tracker.status(1000)["uncertainty_m"], 5)
        self.assertEqual(tracker.status(1000)["age_ms"], 1000)
        tracker.ingest_gpsd(dict(gst, time="2026-10-20T12:00:01Z", lat=20), 1100)
        self.assertEqual(tracker.status(1100)["uncertainty_m"], 5)

    def test_two_dimensional_fix_does_not_reuse_deprecated_or_stale_altitude(self):
        tracker = LocationTracker()
        tracker.ingest_gpsd(tpv(mode=2, alt=9999), 0)
        status = tracker.status(0)
        self.assertEqual(status["mode"], 2)
        self.assertIsNone(status["alt_msl_m"])
        self.assertIsNone(status["alt_hae_m"])

    def test_position_jump_and_contradictory_same_epoch_rejected(self):
        for second in (0, 1):
            tracker = LocationTracker()
            tracker.ingest_gpsd(tpv(), 0)
            self.assertFalse(tracker.ingest_gpsd(tpv(second, lat=51.0), 1000))
            self.assertIn(tracker.status(1000)["reason"], ("POSITION_JUMP", "CONTRADICTORY_EPOCH"))

    def test_time_forward_backward_and_invalid_iso_rejected(self):
        for time in ("2026-10-20T12:01:00Z", "2026-10-20T11:59:59Z",
                     "2026-02-30T12:00:01Z", "2026-10-20T12:00:01+02:00",
                     "no-time", None, "2026-10-20T12:00:60Z"):
            tracker = LocationTracker()
            tracker.ingest_gpsd(tpv(), 0)
            self.assertFalse(tracker.ingest_gpsd(tpv(time=time), 1000), time)
            self.assertFalse(tracker.status(1000)["fresh"])

    def test_trusted_utc_reference_requires_three_distinct_3d_epochs(self):
        epoch = dt.datetime(2026, 10, 20, 12, tzinfo=dt.timezone.utc).timestamp()
        reference = [epoch]
        tracker = LocationTracker(utc_reference=lambda: reference[0])
        for second in range(3):
            reference[0] = epoch + second
            self.assertTrue(tracker.ingest_gpsd(tpv(second), second * 1000))
            self.assertEqual(tracker.status(second * 1000)["utc_verified"], second == 2)
        tracker.ingest_gpsd(tpv(3, time="2020-01-01T00:00:00Z"), 3000)
        self.assertEqual(tracker.status(3000)["reason"], "UTC_REFERENCE_MISMATCH")

    def test_leap_second_supported_without_utc_certification(self):
        tracker = LocationTracker()
        self.assertTrue(tracker.ingest_gpsd(tpv(time="2016-12-31T23:59:60Z"), 0))
        self.assertTrue(tracker.status(0)["leap_second"])
        self.assertFalse(tracker.status(0)["utc_verified"])

    def test_dateline_and_poles_are_valid_and_null_island_not_guessed_invalid(self):
        tracker = LocationTracker(max_speed_mps=100)
        self.assertTrue(tracker.ingest_gpsd(tpv(lat=0, lon=179.9999), 0))
        self.assertTrue(tracker.ingest_gpsd(tpv(1, lat=0, lon=-179.9999), 1000))
        for lat, lon in ((90, 180), (-90, -180), (0, 0)):
            tracker = LocationTracker()
            self.assertTrue(tracker.ingest_gpsd(tpv(lat=lat, lon=lon), 0))

    def test_explicit_or_first_reported_device_identity_prevents_mixing(self):
        for tracker in (LocationTracker(), LocationTracker(device="configured-gnss-device")):
            tracker.ingest_gpsd(tpv(), 0)
            self.assertFalse(tracker.ingest_gpsd(tpv(1, device="other-actual-device", lat=30), 1000))
            self.assertEqual(tracker.status(1000)["device"], "configured-gnss-device")
            self.assertTrue(tracker.status(1000)["fresh"])

    def test_receiver_timeline_discontinuity_reacquires_only_after_three_consistent_epochs(self):
        # E.g. host suspend under CLOCK_MONOTONIC: receiver UTC +60 s, monotonic +1 s.
        epoch = dt.datetime(2026, 10, 20, 12, tzinfo=dt.timezone.utc).timestamp()
        reference = [epoch]
        tracker = LocationTracker(utc_reference=lambda: reference[0])
        for second in range(3):
            reference[0] = epoch + second
            self.assertTrue(tracker.ingest_gpsd(tpv(second), second * 1000))
        self.assertTrue(tracker.status(2000)["utc_verified"])
        accepted, verified = [], []
        for step in range(1, 8):
            reference[0] = epoch + 61 + step
            accepted.append(tracker.ingest_gpsd(tpv(time="2026-10-20T12:01:%02d.000Z" % (1 + step)), 2000 + step * 1000))
            status = tracker.status(2000 + step * 1000)
            verified.append(status["utc_verified"])
            if not accepted[-1]:
                self.assertEqual((status["source"], status["reason"]), ("last_good", "UTC_TIME_JUMP"))
        self.assertEqual(accepted, [False, False, False, True, True, True, True])
        self.assertEqual(verified, [False, False, False, False, False, True, True])

    def test_single_or_unstable_time_jumps_never_replace_the_reference(self):
        tracker = LocationTracker()
        tracker.ingest_gpsd(tpv(0), 0)
        self.assertFalse(tracker.ingest_gpsd(tpv(time="2026-10-20T12:05:00.000Z"), 1000))
        self.assertTrue(tracker.ingest_gpsd(tpv(2), 2000))
        for step in range(1, 12):
            # Each epoch lands on a different timeline: no consistent new reference.
            time = "2026-10-20T13:%02d:%02d.000Z" % (step * 3, step)
            self.assertFalse(tracker.ingest_gpsd(tpv(time=time), 2000 + step * 1000))
        self.assertEqual(tracker.status(13000)["source"], "last_good")
        self.assertTrue(tracker.ingest_gpsd(tpv(14), 14000))

    def test_gst_without_optional_time_or_axis_errors_keeps_fix_live(self):
        epoch = dt.datetime(2026, 10, 20, 12, tzinfo=dt.timezone.utc).timestamp()
        reference = [epoch]
        tracker = LocationTracker(utc_reference=lambda: reference[0])
        gst = {"class": "GST", "device": "configured-gnss-device", "rms": 1.0}
        for second in range(4):
            reference[0] = epoch + second
            self.assertTrue(tracker.ingest_gpsd(tpv(second), second * 1000))
            partial = dict(gst, time="2026-10-20T12:00:%02d.000Z" % second) if second % 2 else gst
            self.assertFalse(tracker.ingest_gpsd(partial, second * 1000 + 100))
            status = tracker.status(second * 1000 + 100)
            self.assertTrue(status["fresh"])
            self.assertIsNone(status["reason"])
            self.assertEqual(status["uncertainty_m"], 4.5)
        self.assertTrue(tracker.status(3100)["utc_verified"])
        tracker.ingest_gpsd(dict(gst, time="2026-10-20T12:00:03.000Z", lat="bad", lon=1), 3200)
        self.assertEqual(tracker.status(3200)["reason"], "GPSD_GST_ERROR")


class NmeaTrackingTests(unittest.TestCase):
    def test_official_quectel_rmc_and_gga_examples(self):
        tracker = LocationTracker()
        sample = b"$GNRMC,040143.000,A,3149.334166,N,11706.941670,E,0.01,0.00,010522,,,D,V*0E\r\n"
        self.assertEqual(tracker.ingest_nmea(sample, 0), 1)
        status = tracker.status(0)
        self.assertAlmostEqual(status["lat"], 31 + 49.334166 / 60)
        self.assertAlmostEqual(status["lon"], 117 + 6.941670 / 60)
        # LC76G NavStatus V is unsupported; RMC Status A remains the validity flag.
        self.assertTrue(status["fresh"])
        sample = b"$GNGGA,040143.000,3149.334166,N,11706.941670,E,2,36,0.48,61.496,M,-0.335,M,,*58\r\n"
        self.assertEqual(tracker.ingest_nmea(sample, 100), 0)  # Same epoch enriches only.
        self.assertEqual(tracker.status(100)["satellites"], 36)
        self.assertAlmostEqual(tracker.status(100)["alt_msl_m"], 61.496)

    def test_byte_fragmentation_at_every_boundary_and_complete_text_record(self):
        sample = rmc()
        for cut in range(len(sample) + 1):
            tracker = LocationTracker()
            count = tracker.ingest_nmea(sample[:cut], 0) + tracker.ingest_nmea(sample[cut:], 0)
            self.assertEqual(count, 1)
            self.assertTrue(tracker.status(0)["fresh"])
        tracker = LocationTracker()
        self.assertEqual(tracker.ingest_nmea(sample.decode().strip(), 0), 1)

    def test_south_west_and_minute_or_degree_validation(self):
        tracker = LocationTracker()
        self.assertEqual(tracker.ingest_nmea(rmc(**{"4": "S", "6": "W"}), 0), 1)
        self.assertEqual((tracker.status(0)["lat"], tracker.status(0)["lon"]), (-50, -20))
        for changes in ({"3": "5060.000"}, {"3": "9100.0"}, {"5": "18100.0"},
                        {"3": "+5000.0"}, {"4": "E"}, {"3": "nan"}, {"8": "360"}):
            tracker = LocationTracker()
            self.assertEqual(tracker.ingest_nmea(rmc(**changes), 0), 0)
            self.assertFalse(tracker.status(0)["available"])

    def test_warning_dead_reckoning_quality_zero_and_poor_hdop_rejected(self):
        for sample in (rmc(**{"2": "V"}), rmc(**{"12": "E"}), rmc(**{"12": "N"}),
                       rmc(**{"7": "200"}), gga(**{"6": "0"}), gga(**{"6": "6"}),
                       gga(**{"8": "99.99"}), gga(**{"8": "30"}), gga(**{"7": "0"}), gga(**{"7": "2"})):
            tracker = LocationTracker()
            self.assertEqual(tracker.ingest_nmea(sample, 0), 0)
            self.assertFalse(tracker.status(0)["fresh"])

    def test_gga_without_date_has_position_and_time_of_day_but_no_guessed_utc(self):
        tracker = LocationTracker()
        self.assertEqual(tracker.ingest_nmea(gga(), 0), 1)
        self.assertIsNone(tracker.status(0)["utc"])
        self.assertEqual(tracker.status(0)["hdop"], 0.9)
        self.assertIsNone(tracker.status(0)["uncertainty_m"])
        self.assertEqual(tracker.status(0)["uncertainty_basis"], "hdop_not_accuracy")
        self.assertEqual(tracker.ingest_nmea(gga("120001.000"), 1000), 1)

    def test_ggas_midnight_rollover_and_rmc_date_anchor(self):
        tracker = LocationTracker()
        tracker.ingest_nmea(rmc("235959.000", "310126"), 0)
        self.assertEqual(tracker.ingest_nmea(gga("000000.000"), 1000), 1)
        self.assertEqual(tracker.status(1000)["utc"], "2026-02-01T00:00:00.000Z")
        tracker = LocationTracker()
        tracker.ingest_nmea(gga("235959.000"), 0)
        self.assertEqual(tracker.ingest_nmea(gga("000000.000"), 1000), 1)

    def test_duplicate_rmc_can_date_undated_gga_without_refresh(self):
        tracker = LocationTracker()
        tracker.ingest_nmea(gga(), 0)
        self.assertEqual(tracker.ingest_nmea(rmc(), 100), 0)
        self.assertEqual(tracker.status(100)["age_ms"], 100)
        self.assertEqual(tracker.status(100)["utc"], "2026-10-20T12:00:00.000Z")
        self.assertEqual(tracker.ingest_nmea(gga("120001.000"), 1000), 1)
        self.assertEqual(tracker.status(1000)["utc"], "2026-10-20T12:00:01.000Z")

    def test_zda_full_year_supplies_century_and_does_not_set_position(self):
        tracker = LocationTracker()
        self.assertEqual(tracker.ingest_nmea(nmea("GNZDA,120000.000,20,10,2080,,"), 0), 0)
        self.assertFalse(tracker.status(0)["available"])
        self.assertEqual(tracker.ingest_nmea(rmc(date="201080"), 0), 1)
        self.assertEqual(tracker.status(0)["utc"], "2080-10-20T12:00:00.000Z")

    def test_gsa_fix_dimension_and_gst_error_association(self):
        tracker = LocationTracker()
        gsa = ["GNGSA", "A", "3"] + [""] * 12 + ["1.2", "0.9", "1.0"]
        tracker.ingest_nmea(nmea(",".join(gsa)), 0)
        tracker.ingest_nmea(nmea("GNGST,120000.000,1.0,1.0,1.0,0.0,3.0,4.0,5.0"), 0)
        tracker.ingest_nmea(rmc(), 0)
        self.assertEqual(tracker.status(0)["mode"], 3)
        self.assertEqual(tracker.status(0)["uncertainty_m"], 5)
        self.assertEqual(tracker.status(0)["uncertainty_confidence"], "unknown")
        gsa[2] = "1"
        tracker.ingest_nmea(nmea(",".join(gsa)), 100)
        self.assertEqual(tracker.status(100)["source"], "last_good")

    def test_gst_after_position_enriches_without_refreshing_it(self):
        tracker = LocationTracker()
        tracker.ingest_nmea(rmc(), 0)
        tracker.ingest_nmea(nmea("GNGST,120000.000,1.0,1.0,1.0,0.0,3.0,4.0,5.0"), 1000)
        self.assertEqual(tracker.status(1000)["uncertainty_m"], 5)
        self.assertEqual(tracker.status(1000)["age_ms"], 1000)
        self.assertFalse(tracker.status(3000)["fresh"])

    def test_empty_optional_gst_and_zda_fields_do_not_invalidate_live_fix(self):
        tracker = LocationTracker()
        tracker.ingest_nmea(rmc(), 0)
        for sample in (nmea("GNGST,120000.000,1.2,,,,,,"), nmea("GNGST,120000.000,1.2,,,,3.0,,"),
                       nmea("GNGST,,,,,,3.0,4.0,"), nmea("GNZDA,,,,,,"), nmea("GNZDA,120000.000,,,,,")):
            with self.subTest(sample=sample):
                self.assertEqual(tracker.ingest_nmea(sample, 100), 0)
                status = tracker.status(100)
                self.assertTrue(status["fresh"])
                self.assertIsNone(status["reason"])
                self.assertIsNone(status["uncertainty_m"])
        tracker.ingest_nmea(nmea("GNGST,120000.000,1.0,1.0,1.0,0.0,x,4.0,5.0"), 200)
        self.assertEqual(tracker.status(200)["reason"], "NMEA_NUMBER")

    def test_explicit_2d_gsa_does_not_publish_held_gga_altitude(self):
        for mode, expected in (("2", (None, None)), ("3", (120.0, 155.0)), (None, (120.0, 155.0))):
            with self.subTest(mode=mode):
                tracker = LocationTracker()
                if mode:
                    tracker.ingest_nmea(nmea(",".join(["GNGSA", "A", mode] + [""] * 12 + ["1.2", "0.9", "1.0"])), 0)
                self.assertEqual(tracker.ingest_nmea(gga(), 0), 1)
                status = tracker.status(0)
                self.assertEqual(status["mode"], int(mode or 2))
                self.assertEqual((status["alt_msl_m"], status["alt_hae_m"]), expected)

    def test_rmc_zda_discontinuity_reacquires_after_three_consistent_epochs(self):
        def epoch(second, now):
            stamp = "12%02d%02d.000" % divmod(second, 60)
            return tracker.ingest_nmea(nmea("GNZDA,%s,20,10,2026,00,00" % stamp) + rmc(stamp), now)
        tracker = LocationTracker()
        self.assertEqual(epoch(0, 0) + epoch(1, 1000), 2)
        accepted = [epoch(61 + step, 1000 + step * 1000) for step in range(1, 7)]
        # The third consistent ZDA retires the old anchor before that epoch's RMC,
        # which is then a first fix, still checked against the last good position.
        self.assertEqual(accepted, [0, 0, 1, 1, 1, 1])
        status = tracker.status(7000)
        self.assertTrue(status["fresh"])
        self.assertEqual(status["utc"], "2026-10-20T12:01:07.000Z")
        self.assertIsNone(status["reason"])

    def test_gga_zda_stream_follows_a_receiver_date_correction_after_three_zdas(self):
        def epoch(second, now, day):
            stamp = "1200%02d.000" % second
            return tracker.ingest_nmea(nmea("GNZDA,%s,%02d,10,2026,00,00" % (stamp, day)) + gga(stamp), now)
        tracker = LocationTracker()
        self.assertEqual(epoch(0, 0, 20) + epoch(1, 1000, 20), 2)
        # Date-only correction: time of day continues, ZDA now reports the 21st.
        accepted = [epoch(1 + step, 1000 + step * 1000, 21) for step in range(1, 7)]
        self.assertEqual(accepted, [1, 1, 1, 1, 1, 1])  # Positions keep their own timeline.
        status = tracker.status(7000)
        self.assertTrue(status["fresh"])
        self.assertEqual(status["utc"], "2026-10-21T12:00:07.000Z")  # Not locked to the old day.
        rejected = tracker.rejected_count
        epoch(8, 8000, 21)
        self.assertEqual(tracker.rejected_count, rejected)  # No NMEA_DATE_JUMP every second.

    def test_single_or_unstable_zda_date_jumps_never_move_the_anchor(self):
        def epoch(second, now, day):
            stamp = "1200%02d.000" % second
            return tracker.ingest_nmea(nmea("GNZDA,%s,%02d,10,2026,00,00" % (stamp, day)) + gga(stamp), now)
        tracker = LocationTracker()
        epoch(0, 0, 20)
        for step, day in enumerate((21, 20, 22, 20, 21, 20, 23, 24), 1):
            self.assertEqual(epoch(step, step * 1000, day), 1)
        self.assertEqual(tracker.status(8000)["utc"], "2026-10-20T12:00:08.000Z")
        self.assertEqual(tracker.last_error, "NMEA_DATE_JUMP")

    def test_undated_gga_stream_recovers_after_outage_longer_than_half_a_day(self):
        tracker = LocationTracker()
        self.assertEqual(tracker.ingest_nmea(gga("120000.000"), 0) + tracker.ingest_nmea(gga("120001.000"), 1000), 2)
        start = 1000 + 13 * 3600 * 1000
        accepted = [tracker.ingest_nmea(gga("01%02d%02d.000" % divmod(1 + step, 60)), start + step * 1000) for step in range(1, 6)]
        self.assertEqual(accepted, [0, 0, 0, 1, 1])
        self.assertTrue(tracker.status(start + 5000)["fresh"])

    def test_time_jumps_and_bad_dates_preserve_last_good(self):
        for sample in (rmc("120010.000"), rmc("115959.000"),
                       rmc(date="310226"), rmc("120060.000")):
            tracker = LocationTracker()
            tracker.ingest_nmea(rmc(), 0)
            self.assertEqual(tracker.ingest_nmea(sample, 1000), 0)
            self.assertEqual(tracker.status(1000)["source"], "last_good")

    def test_checksum_corruption_oversize_and_resync_do_not_refresh(self):
        tracker = LocationTracker()
        tracker.ingest_nmea(rmc(), 0)
        bad = bytearray(rmc("120001.000"))
        bad[10] ^= 1
        tracker.ingest_nmea(bad, 1000)
        self.assertEqual(tracker.status(1000)["reason"], "NMEA_CHECKSUM")
        tracker.ingest_nmea(b"$" + b"X" * (MAX_NMEA_BYTES + 10), 1100)
        self.assertLessEqual(len(tracker._nmea_buffer), MAX_NMEA_BYTES)
        tracker.ingest_nmea(b"garbage" + rmc("120002.000"), 2000)
        self.assertTrue(tracker.status(2000)["fresh"])
        self.assertEqual(tracker.status(2000)["age_ms"], 0)

    def test_nonascii_huge_chunk_and_batch_are_bounded(self):
        tracker = LocationTracker()
        tracker.ingest_nmea("😀", 0)
        self.assertEqual(tracker.last_error, "NMEA_ASCII")
        tracker.ingest_nmea(b"x" * (MAX_INPUT_BYTES + 1), 0)
        self.assertEqual(len(tracker._nmea_buffer), 0)
        tracker.ingest_nmea(rmc() + b"\n" * 129, 0)
        self.assertEqual(tracker.last_error, "NMEA_BATCH_LIMIT")
        self.assertFalse(tracker.status(0)["fresh"])


class SelectionAndClockTests(unittest.TestCase):
    def test_none_manual_fresh_and_most_recent_fallback_sources(self):
        tracker = LocationTracker()
        self.assertEqual(tracker.status(0)["source"], "none")
        status = tracker.manual(50, 20, 0)
        self.assertEqual(status["source"], "manual")
        self.assertFalse(status["live_fix"])
        self.assertIsNone(status["uncertainty_m"])
        tracker.ingest_gpsd(tpv(1), 1000)
        tracker.manual(50.0001, 20.0001, 2000)
        self.assertEqual(tracker.status(2000)["source"], "gpsd")
        self.assertEqual(tracker.status(4000)["source"], "manual")
        tracker.ingest_gpsd(tpv(5), 5000)
        self.assertEqual(tracker.status(8000)["source"], "last_good")

    def test_fresh_alternative_source_survives_gpsd_failure(self):
        tracker = LocationTracker()
        tracker.ingest_gpsd(tpv(), 0)
        tracker.ingest_nmea(rmc(), 0)
        tracker.ingest_gpsd({"class": "TPV", "mode": 1,
                             "device": "configured-gnss-device"}, 1000)
        self.assertEqual(tracker.status(1000)["source"], "nmea")
        self.assertTrue(tracker.status(1000)["fresh"])

    def test_recovered_fault_is_history_not_the_current_fallback_reason(self):
        tracker = LocationTracker()
        self.assertEqual(tracker.ingest_nmea(b"junk" + rmc(), 0), 1)
        self.assertIsNone(tracker.status(0)["reason"])
        status = tracker.manual(50.0001, 20.0001, 10000)
        self.assertEqual((status["source"], status["reason"], status["last_error"]),
                         ("manual", "MANUAL_FALLBACK", "NMEA_RESYNC"))
        tracker = LocationTracker()
        tracker.ingest_gpsd(tpv(), 0)
        tracker.ingest_gpsd(tpv(1, lat=51.0), 1000)
        tracker.ingest_gpsd(tpv(2), 2000)
        self.assertEqual(tracker.status(6000)["reason"], "STALE")
        tracker.ingest_gpsd(tpv(7, mode=1), 7000)
        self.assertEqual(tracker.status(7000)["reason"], "GPSD_NO_FIX")

    def test_unrecovered_fault_of_one_source_survives_another_source_fix(self):
        tracker = LocationTracker()
        tracker.ingest_gpsd(tpv(), 0)
        tracker.invalidate("gpsd", "GPSD_HANDSHAKE_TIMEOUT")  # GpsdClient: no auto-reconnect.
        self.assertEqual(tracker.ingest_nmea(rmc("120001.000"), 1000), 1)
        self.assertIsNone(tracker.status(1000)["reason"])  # Live NMEA fix.
        status = tracker.status(5000)
        self.assertEqual((status["source"], status["origin"]), ("last_good", "nmea"))
        self.assertEqual(status["reason"], "GPSD_HANDSHAKE_TIMEOUT")
        tracker.ingest_nmea(rmc("120002.000", **{"2": "V"}), 5100)
        self.assertEqual(tracker.status(5100)["reason"], "NMEA_NO_FIX")  # The fallback's own source first.
        self.assertTrue(tracker.ingest_gpsd(tpv(6), 6000))
        self.assertEqual(tracker.status(9500)["reason"], "NMEA_NO_FIX")

    def test_monotonic_clock_reversal_latches_unknown_age(self):
        tracker = LocationTracker()
        tracker.ingest_gpsd(tpv(), 1000)
        self.assertFalse(tracker.ingest_gpsd(tpv(1), 500))
        status = tracker.status(1200)
        self.assertEqual(status["source"], "last_good")
        self.assertIsNone(status["age_ms"])
        self.assertFalse(status["fresh"])
        self.assertFalse(tracker.ingest_gpsd(tpv(2), 2000))

    def test_invalid_configuration_manual_and_clock_types_raise(self):
        for arguments in ({"fresh_ms": 0}, {"max_speed_mps": float("nan")},
                          {"jump_slack_m": -1}, {"device": ""}):
            with self.assertRaises(ValueError):
                LocationTracker(**arguments)
        tracker = LocationTracker()
        for lat, lon in ((91, 0), (0, -181), (float("nan"), 0), (True, 2)):
            with self.assertRaises(ValueError):
                tracker.manual(lat, lon, 0)
        for now in (-1, True, 0.1):
            with self.assertRaises(ValueError):
                tracker.status(now)


class DecoderTests(unittest.TestCase):
    def test_json_fragmentation_and_combined_reports(self):
        packet = json.dumps(tpv()).encode() + b"\r\n"
        for cut in range(len(packet) + 1):
            decoder = GpsdJSONDecoder()
            self.assertEqual(decoder.feed(packet[:cut]) + decoder.feed(packet[cut:]), [tpv()])
        decoder = GpsdJSONDecoder()
        self.assertEqual(decoder.feed(packet + packet), [tpv(), tpv()])

    def test_malformed_duplicate_nonfinite_deep_and_truncated_json_recover(self):
        bad = (b'{"class":"TPV",\n', b'{"x":1,"x":2}\n', b'{"x":NaN}\n',
               b'{"x":1e999}\n', b'{"x":"\xff"}\n', b'[]\n',
               b'{"x":' + b'[' * 40 + b'0' + b']' * 40 + b'}\n')
        good = json.dumps(tpv()).encode() + b"\n"
        for packet in bad:
            decoder = GpsdJSONDecoder()
            self.assertEqual(decoder.feed(packet + good), [tpv()])
            self.assertGreater(decoder.errors, 0)
        decoder = GpsdJSONDecoder()
        decoder.feed(b"x" * (MAX_GPSD_BYTES + 100))
        self.assertLessEqual(decoder.buffered_bytes, MAX_GPSD_BYTES)
        self.assertEqual(decoder.feed(b"\n" + good), [tpv()])

    def test_huge_input_and_many_objects_have_fixed_bounds(self):
        decoder = GpsdJSONDecoder()
        self.assertEqual(decoder.feed(b"x" * (MAX_INPUT_BYTES + 1)), [])
        packet = b'{"class":"SKY"}\n'
        self.assertEqual(len(decoder.feed(packet * 128)), 64)
        self.assertGreater(decoder.errors, 0)


class FakeSocket:
    def __init__(self, connect_result=0):
        self.incoming = collections.deque()
        self.sent = bytearray()
        self.closed = False
        self.connect_result = connect_result
        self.send_limit = 1000

    def setblocking(self, value):
        self.blocking = value

    def connect_ex(self, address):
        self.address = address
        return self.connect_result

    def recv(self, size):
        if self.incoming:
            return self.incoming.popleft()
        raise BlockingIOError

    def send(self, value):
        count = min(self.send_limit, len(value))
        self.sent.extend(value[:count])
        return count

    def close(self):
        self.closed = True


class ClientTests(unittest.TestCase):
    def test_no_default_endpoint_no_dns_and_loopback_only(self):
        tracker = LocationTracker()
        for host, port in (("example.com", 2947), ("192.0.2.1", 2947),
                           ("0.0.0.0", 2947), ("127.0.0.1", 0), (None, 2947)):
            with self.assertRaises(ValueError):
                GpsdClient(tracker, host, port)
        client = GpsdClient(tracker, "localhost", 2947)
        self.assertEqual(client.poll(0), 0)
        self.assertIsNone(client.sock)

    def test_nonblocking_version_watch_short_writes_fix_and_disconnect(self):
        fake = FakeSocket()
        fake.send_limit = 5
        tracker = LocationTracker()
        client = GpsdClient(tracker, "127.0.0.1", 2947)
        with patch("srrx.location.socket.socket", return_value=fake):
            self.assertTrue(client.start(0))
        self.assertFalse(fake.blocking)
        fake.incoming.append(b'{"class":"VERSION","proto_major":3,"proto_minor":15}\n')
        for now in range(0, 100, 10):
            client.poll(now)
        self.assertEqual(bytes(fake.sent), client.WATCH)
        fake.incoming.append(b'{"class":"WATCH","enable":true,"json":true}\n' + json.dumps(tpv()).encode() + b"\n")
        self.assertEqual(client.poll(100), 1)
        self.assertTrue(client.watching)
        self.assertTrue(tracker.status(100)["fresh"])
        fake.incoming.append(b"")
        client.poll(200)
        self.assertEqual(client.error, "GPSD_DISCONNECTED")
        self.assertEqual(tracker.status(200)["source"], "last_good")

    def test_unsupported_protocol_unnegotiated_watch_and_timeout_close(self):
        for packet, expected in ((b'{"class":"VERSION","proto_major":4}\n', "GPSD_PROTOCOL_UNSUPPORTED"),
                                 (b'{"class":"WATCH","enable":true,"json":true}\n', "GPSD_WATCH_REFUSED")):
            fake, tracker = FakeSocket(), LocationTracker()
            client = GpsdClient(tracker, "::1", 2947)
            with patch("srrx.location.socket.socket", return_value=fake):
                client.start(0)
            fake.incoming.append(packet)
            client.poll(0)
            self.assertEqual(client.error, expected)
            self.assertIsNone(client.sock)
        fake, tracker = FakeSocket(), LocationTracker()
        client = GpsdClient(tracker, "127.0.0.1", 2947)
        with patch("srrx.location.socket.socket", return_value=fake):
            client.start(0)
        client.poll(3000)
        self.assertEqual(client.error, "GPSD_HANDSHAKE_TIMEOUT")

    def test_late_polls_drain_received_handshake_before_deadline(self):
        version = b'{"class":"VERSION","proto_major":3,"proto_minor":15}\n'
        ack = b'{"class":"WATCH","enable":true,"json":true}\n' + json.dumps(tpv()).encode() + b"\n"
        for polls in ((2900, 3000), (5000, 5250)):
            with self.subTest(polls=polls):
                fake, tracker = FakeSocket(), LocationTracker()
                client = GpsdClient(tracker, "127.0.0.1", 2947)
                with patch("srrx.location.socket.socket", return_value=fake):
                    client.start(0)
                fake.incoming.append(version)
                self.assertEqual(client.poll(polls[0]), 0)
                self.assertEqual(bytes(fake.sent), client.WATCH)
                fake.incoming.append(ack)
                self.assertEqual(client.poll(polls[1]), 1)
                self.assertTrue(client.watching)
                self.assertIsNone(client.error)
        # VERSION without a WATCH acknowledgement still expires (3 s after VERSION).
        fake, tracker = FakeSocket(), LocationTracker()
        client = GpsdClient(tracker, "127.0.0.1", 2947)
        with patch("srrx.location.socket.socket", return_value=fake):
            client.start(0)
        fake.incoming.append(version)
        client.poll(1000)
        client.poll(3999)
        self.assertIsNotNone(client.sock)
        client.poll(4000)
        self.assertEqual(client.error, "GPSD_HANDSHAKE_TIMEOUT")
        self.assertIsNone(client.sock)


if __name__ == "__main__":
    unittest.main()
