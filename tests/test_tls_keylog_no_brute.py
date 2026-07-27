"""Regression: mismatched keylog must not brute-force every secret (Termux hang)."""

from __future__ import annotations

import time
from pathlib import Path

from protocol_ast.tls_keylog import KeylogSecrets, decrypt_tls_records


def _fake_appdata(n: int = 40) -> list[bytes]:
    # Minimal TLS Application Data records (type 0x17), undecryptable garbage.
    out: list[bytes] = []
    for i in range(n):
        body = bytes([i & 0xFF]) * 64
        out.append(bytes([0x17, 0x03, 0x03]) + len(body).to_bytes(2, "big") + body)
    return out


def test_decrypt_no_overlap_returns_fast_even_with_huge_keylog():
    secrets = KeylogSecrets()
    # Simulate ~900 TLS1.3 sessions in a fat SSLKEYLOGFILE
    for i in range(900):
        cr = f"{i:064x}"
        secrets.client_traffic[cr] = bytes(48)
        secrets.server_traffic[cr] = bytes(48)
    secrets.lines = 1800

    records = _fake_appdata(50)
    t0 = time.perf_counter()
    res = decrypt_tls_records(records, secrets)
    elapsed = time.perf_counter() - t0

    assert res is not None
    assert res.diagnostics.get("reason") == "no_overlap"
    assert res.diagnostics.get("overlap") == 0
    assert res.decrypted == []
    # Brute-forcing 900 secrets × 50 records used to take minutes/hours on phone.
    assert elapsed < 2.0, f"decrypt took {elapsed:.2f}s — brute-force regress?"


def test_pick_pcap_mtime_fallback(tmp_path: Path):
    from protocol_ast.find_keylog import pick_pcap_for_keylog

    old = tmp_path / "old.pcap"
    new = tmp_path / "new.pcap"
    kl = tmp_path / "sslkeylogfile.txt"
    # Minimal valid-ish files for size checks; overlap will be 0 (empty traffic).
    old.write_bytes(b"\xd4\xc3\xb2\xa1" + b"\x00" * 100)
    new.write_bytes(b"\xd4\xc3\xb2\xa1" + b"\x00" * 100)
    kl.write_text(
        "CLIENT_RANDOM " + ("ab" * 32) + " " + ("cd" * 48) + "\n",
        encoding="utf-8",
    )
    now = time.time()
    import os

    os.utime(old, (now - 86400, now - 86400))
    os.utime(new, (now - 60, now - 60))
    os.utime(kl, (now, now))

    path, ov, msg = pick_pcap_for_keylog(
        kl, seed_paths=[old, new], max_candidates=8, max_bytes=12_000_000
    )
    assert ov == 0
    assert path == new
    assert "overlap" in msg
