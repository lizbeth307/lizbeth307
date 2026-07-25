"""Parse NSS SSLKEYLOGFILE and decrypt TLS Application Data when possible."""

from __future__ import annotations

import hashlib
import hmac
import struct
from dataclasses import dataclass, field
from pathlib import Path

from .aes_gcm import aes_gcm_decrypt


@dataclass
class KeylogSecrets:
    """Secrets indexed by client_random hex (64 chars)."""

    master_secrets: dict[str, bytes] = field(default_factory=dict)  # TLS 1.2
    client_handshake: dict[str, bytes] = field(default_factory=dict)
    server_handshake: dict[str, bytes] = field(default_factory=dict)
    client_traffic: dict[str, bytes] = field(default_factory=dict)  # TLS 1.3
    server_traffic: dict[str, bytes] = field(default_factory=dict)
    exporter: dict[str, bytes] = field(default_factory=dict)
    lines: int = 0

    @property
    def client_randoms(self) -> set[str]:
        keys = set()
        for d in (
            self.master_secrets,
            self.client_handshake,
            self.server_handshake,
            self.client_traffic,
            self.server_traffic,
        ):
            keys.update(d)
        return keys


def parse_keylog(path: str | Path) -> KeylogSecrets:
    """Parse NSS Key Log Format (SSLKEYLOGFILE)."""
    secrets = KeylogSecrets()
    text = Path(path).expanduser().read_text(encoding="utf-8", errors="replace")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        label, client_random, secret_hex = parts[0], parts[1].lower(), parts[2]
        try:
            secret = bytes.fromhex(secret_hex)
        except ValueError:
            continue
        secrets.lines += 1
        cr = client_random.lower()
        if label == "CLIENT_RANDOM":
            secrets.master_secrets[cr] = secret
        elif label == "CLIENT_HANDSHAKE_TRAFFIC_SECRET":
            secrets.client_handshake[cr] = secret
        elif label == "SERVER_HANDSHAKE_TRAFFIC_SECRET":
            secrets.server_handshake[cr] = secret
        elif label == "CLIENT_TRAFFIC_SECRET_0":
            secrets.client_traffic[cr] = secret
        elif label == "SERVER_TRAFFIC_SECRET_0":
            secrets.server_traffic[cr] = secret
        elif label == "EXPORTER_SECRET":
            secrets.exporter[cr] = secret
    return secrets


def extract_client_random(handshake_body: bytes) -> bytes | None:
    """ClientHello body → 32-byte client_random (after type+len+version)."""
    if len(handshake_body) < 38 or handshake_body[0] != 0x01:
        return None
    return handshake_body[6:38]


def find_client_randoms_in_records(records: list[bytes]) -> list[bytes]:
    out: list[bytes] = []
    for rec in records:
        if len(rec) < 6 or rec[0] != 0x16:
            continue
        body = rec[5:]
        rnd = extract_client_random(body)
        if rnd:
            out.append(rnd)
    return out


def _hkdf_expand_label(secret: bytes, label: bytes, context: bytes, length: int) -> bytes:
    """TLS 1.3 HKDF-Expand-Label (RFC 8446)."""
    full_label = b"tls13 " + label
    hkdf_label = (
        struct.pack(">H", length)
        + bytes([len(full_label)])
        + full_label
        + bytes([len(context)])
        + context
    )
    return _hkdf_expand(secret, hkdf_label, length)


def _hkdf_expand(secret: bytes, info: bytes, length: int) -> bytes:
    hash_len = 32
    n = (length + hash_len - 1) // hash_len
    okm = b""
    prev = b""
    for i in range(1, n + 1):
        prev = hmac.new(secret, prev + info + bytes([i]), hashlib.sha256).digest()
        okm += prev
    return okm[:length]


def _tls13_traffic_key_iv(traffic_secret: bytes) -> tuple[bytes, bytes]:
    key = _hkdf_expand_label(traffic_secret, b"key", b"", 16)
    iv = _hkdf_expand_label(traffic_secret, b"iv", b"", 12)
    return key, iv


def _decrypt_tls13_record(
    record: bytes,
    key: bytes,
    iv: bytes,
    seq: int,
) -> bytes | None:
    """Decrypt TLS 1.3 Application Data (content type 23) AES-128-GCM."""
    if len(record) < 5 + 16:
        return None
    if record[0] != 0x17:
        return None
    length = (record[3] << 8) | record[4]
    ciphertext = record[5 : 5 + length]
    if len(ciphertext) < 16:
        return None
    nonce = bytearray(iv)
    for i in range(8):
        nonce[12 - 1 - i] ^= (seq >> (8 * i)) & 0xFF
    aad = record[:5]
    try:
        plain = aes_gcm_decrypt(key, bytes(nonce), ciphertext, aad)
    except Exception:
        return None
    # TLS 1.3: last byte is inner content type
    if not plain:
        return None
    return plain[:-1]


def _prf_tls12(secret: bytes, label: bytes, seed: bytes, out_len: int) -> bytes:
    """TLS 1.2 PRF with SHA256 (most modern suites)."""
    seed_full = label + seed

    def p_hash(key: bytes, data: bytes, n: int) -> bytes:
        a = data
        out = b""
        while len(out) < n:
            a = hmac.new(key, a, hashlib.sha256).digest()
            out += hmac.new(key, a + data, hashlib.sha256).digest()
        return out[:n]

    return p_hash(secret, seed_full, out_len)


def _decrypt_tls12_gcm(
    record: bytes,
    key: bytes,
    implicit_iv: bytes,
    seq: int,
) -> bytes | None:
    """Decrypt TLS 1.2 AES-GCM Application Data."""
    if len(record) < 5 + 8 + 16:
        return None
    if record[0] != 0x17:
        return None
    length = (record[3] << 8) | record[4]
    body = record[5 : 5 + length]
    if len(body) < 8 + 16:
        return None
    explicit = body[:8]
    ciphertext = body[8:]
    nonce = implicit_iv + explicit
    aad = struct.pack(">Q", seq) + record[:3] + struct.pack(">H", length - 8)
    try:
        return aes_gcm_decrypt(key, nonce, ciphertext, aad)
    except Exception:
        return None


@dataclass
class DecryptResult:
    client_random: str
    secrets_matched: list[str]
    decrypted: list[bytes]
    failed: int
    tls_version: str


def decrypt_tls_records(
    records: list[bytes],
    secrets: KeylogSecrets,
) -> DecryptResult | None:
    """Try TLS 1.3 then TLS 1.2 decrypt for Application Data records."""
    randoms = find_client_randoms_in_records(records)
    if not randoms:
        # still try all known secrets if ClientHello not in this batch
        candidates = list(secrets.client_randoms)
    else:
        candidates = [r.hex() for r in randoms]

    for cr_hex in candidates:
        matched: list[str] = []
        # --- TLS 1.3 ---
        c_sec = secrets.client_traffic.get(cr_hex)
        s_sec = secrets.server_traffic.get(cr_hex)
        if c_sec or s_sec:
            if c_sec:
                matched.append("CLIENT_TRAFFIC_SECRET_0")
            if s_sec:
                matched.append("SERVER_TRAFFIC_SECRET_0")
            decrypted: list[bytes] = []
            failed = 0
            c_seq = s_seq = 0
            c_key_iv = _tls13_traffic_key_iv(c_sec) if c_sec else None
            s_key_iv = _tls13_traffic_key_iv(s_sec) if s_sec else None
            for rec in records:
                if len(rec) < 5 or rec[0] != 0x17:
                    continue
                ok = None
                if c_key_iv:
                    ok = _decrypt_tls13_record(rec, c_key_iv[0], c_key_iv[1], c_seq)
                    if ok is not None:
                        c_seq += 1
                        decrypted.append(ok)
                        continue
                if s_key_iv:
                    ok = _decrypt_tls13_record(rec, s_key_iv[0], s_key_iv[1], s_seq)
                    if ok is not None:
                        s_seq += 1
                        decrypted.append(ok)
                        continue
                failed += 1
            if decrypted:
                return DecryptResult(
                    client_random=cr_hex,
                    secrets_matched=matched,
                    decrypted=decrypted,
                    failed=failed,
                    tls_version="1.3",
                )

        # --- TLS 1.2 ---
        master = secrets.master_secrets.get(cr_hex)
        if not master:
            continue
        matched = ["CLIENT_RANDOM"]
        # Need server_random from ServerHello — scan handshake records
        server_random = _find_server_random(records)
        client_random = bytes.fromhex(cr_hex)
        if not server_random:
            continue
        key_block = _prf_tls12(
            master,
            b"key expansion",
            server_random + client_random,
            40,  # AES-128-GCM: 16+16+4+4
        )
        c_key, s_key = key_block[0:16], key_block[16:32]
        c_iv, s_iv = key_block[32:36], key_block[36:40]
        decrypted = []
        failed = 0
        c_seq = s_seq = 0
        for rec in records:
            if len(rec) < 5 or rec[0] != 0x17:
                continue
            plain = _decrypt_tls12_gcm(rec, c_key, c_iv, c_seq)
            if plain is not None:
                c_seq += 1
                decrypted.append(plain)
                continue
            plain = _decrypt_tls12_gcm(rec, s_key, s_iv, s_seq)
            if plain is not None:
                s_seq += 1
                decrypted.append(plain)
                continue
            failed += 1
        if decrypted:
            return DecryptResult(
                client_random=cr_hex,
                secrets_matched=matched,
                decrypted=decrypted,
                failed=failed,
                tls_version="1.2",
            )

    return None


def _find_server_random(records: list[bytes]) -> bytes | None:
    for rec in records:
        if len(rec) < 6 or rec[0] != 0x16:
            continue
        body = rec[5:]
        if len(body) < 38 or body[0] != 0x02:  # ServerHello
            continue
        return body[6:38]
    return None


def keylog_summary(secrets: KeylogSecrets) -> dict:
    return {
        "lines": secrets.lines,
        "client_randoms": len(secrets.client_randoms),
        "tls12_master": len(secrets.master_secrets),
        "tls13_client_traffic": len(secrets.client_traffic),
        "tls13_server_traffic": len(secrets.server_traffic),
    }
