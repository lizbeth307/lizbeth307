"""Тести на реальних протоколах (Modbus TCP, DNS, NTP, TLS record)."""

from __future__ import annotations

import unittest

from protocol_ast.align import discover_format
from protocol_ast.fixtures.real_protocols import (
    DNS_MESSAGES,
    MODBUS_TCP_MESSAGES,
    NTP_MESSAGES,
    REAL_PROTOCOLS,
    TLS_RECORD_MESSAGES,
    parse_modbus_tcp,
    parse_tls_record,
)
from protocol_ast.parser import parse_message
from protocol_ast.pipeline import discover_and_parse


class TestModbusTcpReal(unittest.TestCase):
  """Modbus TCP ADU — промисловий протокол, length BE @ offset 4."""

  def setUp(self) -> None:
    self.messages = MODBUS_TCP_MESSAGES
    self.result = discover_and_parse(self.messages)

  def test_finds_length_field_be_at_offset_4(self) -> None:
    fmt = self.result.format
    self.assertEqual(fmt.length_field_offset, 4)
    self.assertEqual(fmt.length_endian, "be")

  def test_protocol_id_zero_is_fixed(self) -> None:
    fixed = [f for f in self.result.format.fields if f.kind == "fixed"]
    self.assertTrue(fixed)
    # bytes 2-3 = 0x0000 у всіх кадрах
    proto = next(
      (f for f in fixed if f.offset <= 2 < f.offset + f.size),
      None,
    )
    self.assertIsNotNone(proto)
    assert proto is not None
    self.assertIn(0, proto.values)
    self.assertIn(0, proto.values)

  def test_parse_all_messages(self) -> None:
    self.assertEqual(self.result.success_rate, 1.0)

  def test_oracle_length_matches_modbus_spec(self) -> None:
    for raw, tree in zip(self.messages, self.result.trees):
      pdu = parse_modbus_tcp(raw)
      length_node = next(c for c in tree.children if c.kind == "length")
      payload_node = next(c for c in tree.children if c.kind == "payload")
      self.assertEqual(length_node.value, pdu.length)
      self.assertEqual(len(payload_node.value), pdu.length)
      self.assertEqual(payload_node.value[0], pdu.unit_id)
      self.assertEqual(payload_node.value[1], pdu.function)


class TestTlsRecordReal(unittest.TestCase):
  """TLS record layer — length BE @ offset 3."""

  def setUp(self) -> None:
    self.result = discover_and_parse(TLS_RECORD_MESSAGES)

  def test_finds_length_be(self) -> None:
    fmt = self.result.format
    self.assertEqual(fmt.length_field_offset, 3)
    self.assertEqual(fmt.length_endian, "be")

  def test_parse_success(self) -> None:
    self.assertEqual(self.result.success_rate, 1.0)

  def test_oracle_fragment_length(self) -> None:
    for raw, tree in zip(TLS_RECORD_MESSAGES, self.result.trees):
      rec = parse_tls_record(raw)
      length_node = next(c for c in tree.children if c.kind == "length")
      payload_node = next(c for c in tree.children if c.kind == "payload")
      self.assertEqual(length_node.value, rec.length)
      self.assertEqual(payload_node.value, rec.fragment)


class TestNtpReal(unittest.TestCase):
  """NTP — фіксовані 48-байтні пакети (RFC 5905)."""

  def setUp(self) -> None:
    self.messages = NTP_MESSAGES
    self.result = discover_and_parse(self.messages)

  def test_all_packets_same_size(self) -> None:
    self.assertTrue(all(len(m) == 48 for m in self.messages))
    self.assertEqual(self.result.format.min_len, 48)
    self.assertEqual(self.result.format.max_len, 48)

  def test_first_byte_version_mode_recovered(self) -> None:
    # LI/VN/Mode у старших бітах першого байта — домени enum/variable
    first_fields = [f for f in self.result.format.fields if f.offset == 0]
    self.assertTrue(first_fields)
    vals = set()
    for m in self.messages:
      vals.add(m[0])
    self.assertGreaterEqual(len(vals), 2)  # 0x1b, 0x23, 0x24 ...

  def test_parse_fixed_length_corpus(self) -> None:
    self.assertEqual(self.result.success_rate, 1.0)


class TestDnsReal(unittest.TestCase):
  """DNS — змінна довжина, 12-байтний заголовок (RFC 1035)."""

  def setUp(self) -> None:
    self.messages = DNS_MESSAGES
    self.fmt = discover_format(self.messages)

  def test_header_at_least_12_bytes_before_payload(self) -> None:
    payload = next(f for f in self.fmt.fields if f.kind == "payload")
    self.assertGreaterEqual(payload.offset, 12)

  def test_no_checksum_trailer(self) -> None:
    self.assertFalse(any(f.name == "checksum" for f in self.fmt.fields))

  def test_parses_queries_and_responses(self) -> None:
    result = discover_and_parse(self.messages)
    # DNS має змінну структуру після QNAME — очікуємо високий, але не 100%, success
    self.assertGreaterEqual(result.success_rate, 0.85)


class TestRealProtocolRegistry(unittest.TestCase):
  def test_all_protocols_have_messages(self) -> None:
    for key, meta in REAL_PROTOCOLS.items():
      self.assertGreater(len(meta["messages"]), 0, key)


if __name__ == "__main__":
  unittest.main()
