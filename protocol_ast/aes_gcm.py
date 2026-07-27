"""AES-GCM decrypt: cryptography → pure Python (Termux-safe, no pip build)."""

from __future__ import annotations


def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes | None:
    """Decrypt AES-GCM; returns plaintext or None on auth failure."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        return AESGCM(key).decrypt(nonce, ciphertext, aad)
    except ImportError:
        pass
    except Exception:
        return None
    return _pure_aes_gcm_decrypt(key, nonce, ciphertext, aad)


def backend_name() -> str:
    try:
        import cryptography  # noqa: F401

        return "cryptography"
    except ImportError:
        return "pure-python"


# ---------------------------------------------------------------------------
# Minimal AES-128/256 + GCM (decrypt only)
# ---------------------------------------------------------------------------

_SBOX = bytes(
    [
        99, 124, 119, 123, 242, 107, 111, 197, 48, 1, 103, 43, 254, 215, 171, 118,
        202, 130, 201, 125, 250, 89, 71, 240, 173, 212, 162, 175, 156, 164, 114, 192,
        183, 253, 147, 38, 54, 63, 247, 204, 52, 165, 229, 241, 113, 216, 49, 21,
        4, 199, 35, 195, 24, 150, 5, 154, 7, 18, 128, 226, 235, 39, 178, 117,
        9, 131, 44, 26, 27, 110, 90, 160, 82, 59, 214, 179, 41, 227, 47, 132,
        83, 209, 0, 237, 32, 252, 177, 91, 106, 203, 190, 57, 74, 76, 88, 207,
        208, 239, 170, 251, 67, 77, 51, 133, 69, 249, 2, 127, 80, 60, 159, 168,
        81, 163, 64, 143, 146, 157, 56, 245, 188, 182, 218, 33, 16, 255, 243, 210,
        205, 12, 19, 236, 95, 151, 68, 23, 196, 167, 126, 61, 100, 93, 25, 115,
        96, 129, 79, 220, 34, 42, 144, 136, 70, 238, 184, 20, 222, 94, 11, 219,
        224, 50, 58, 10, 73, 6, 36, 92, 194, 211, 172, 98, 145, 149, 228, 121,
        231, 200, 55, 109, 141, 213, 78, 169, 108, 86, 244, 234, 101, 122, 174, 8,
        186, 120, 37, 46, 28, 166, 180, 198, 232, 221, 116, 31, 75, 189, 139, 138,
        112, 62, 181, 102, 72, 3, 246, 14, 97, 53, 87, 185, 134, 193, 29, 158,
        225, 248, 152, 17, 105, 217, 142, 148, 155, 30, 135, 233, 206, 85, 40, 223,
        140, 161, 137, 13, 191, 230, 66, 104, 65, 153, 45, 15, 176, 84, 187, 22,
    ]
)

_RCON = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36]


def _xtime(a: int) -> int:
    return ((a << 1) ^ 0x1B) & 0xFF if a & 0x80 else (a << 1) & 0xFF


def _sub_word(w: int) -> int:
    return (
        (_SBOX[(w >> 24) & 0xFF] << 24)
        | (_SBOX[(w >> 16) & 0xFF] << 16)
        | (_SBOX[(w >> 8) & 0xFF] << 8)
        | _SBOX[w & 0xFF]
    )


def _rot_word(w: int) -> int:
    return ((w << 8) | (w >> 24)) & 0xFFFFFFFF


def _key_expansion(key: bytes) -> list[list[int]]:
    key_len = len(key)
    n_k = key_len // 4
    n_r = {16: 10, 24: 12, 32: 14}[key_len]
    w = [0] * (4 * (n_r + 1))
    for i in range(n_k):
        w[i] = int.from_bytes(key[4 * i : 4 * i + 4], "big")
    for i in range(n_k, 4 * (n_r + 1)):
        temp = w[i - 1]
        if i % n_k == 0:
            temp = _sub_word(_rot_word(temp)) ^ (_RCON[i // n_k] << 24)
        elif n_k > 6 and i % n_k == 4:
            temp = _sub_word(temp)
        w[i] = w[i - n_k] ^ temp
    rounds = []
    for r in range(n_r + 1):
        block = []
        for c in range(4):
            word = w[r * 4 + c]
            block.extend([(word >> 24) & 0xFF, (word >> 16) & 0xFF, (word >> 8) & 0xFF, word & 0xFF])
        rounds.append(block)
    return rounds


def _add_round_key(state: list[int], rk: list[int]) -> None:
    for i in range(16):
        state[i] ^= rk[i]


def _sub_bytes(state: list[int]) -> None:
    for i in range(16):
        state[i] = _SBOX[state[i]]


def _shift_rows(state: list[int]) -> None:
    state[1], state[5], state[9], state[13] = state[5], state[9], state[13], state[1]
    state[2], state[6], state[10], state[14] = state[10], state[14], state[2], state[6]
    state[3], state[7], state[11], state[15] = state[15], state[3], state[7], state[11]


def _mix_columns(state: list[int]) -> None:
    for c in range(4):
        i = 4 * c
        a0, a1, a2, a3 = state[i], state[i + 1], state[i + 2], state[i + 3]
        state[i] = _xtime(a0) ^ _xtime(a1) ^ a1 ^ a2 ^ a3
        state[i + 1] = a0 ^ _xtime(a1) ^ _xtime(a2) ^ a2 ^ a3
        state[i + 2] = a0 ^ a1 ^ _xtime(a2) ^ _xtime(a3) ^ a3
        state[i + 3] = _xtime(a0) ^ a0 ^ a1 ^ a2 ^ _xtime(a3)


def _aes_encrypt_block(block: bytes, round_keys: list[list[int]]) -> bytes:
    state = list(block)
    n_r = len(round_keys) - 1
    _add_round_key(state, round_keys[0])
    for r in range(1, n_r):
        _sub_bytes(state)
        _shift_rows(state)
        _mix_columns(state)
        _add_round_key(state, round_keys[r])
    _sub_bytes(state)
    _shift_rows(state)
    _add_round_key(state, round_keys[n_r])
    return bytes(state)


def _gf_mult(x: int, y: int) -> int:
    """GCM field multiplication (NIST bit-reflected convention)."""
    r = 0
    for _ in range(128):
        if y & (1 << 127):
            r ^= x
        y = (y << 1) & ((1 << 128) - 1)
        lsb = x & 1
        x >>= 1
        if lsb:
            x ^= 0xE1000000000000000000000000000000
    return r


def _ghash(h: int, data: bytes) -> int:
    y = 0
    for i in range(0, len(data), 16):
        block = data[i : i + 16].ljust(16, b"\x00")
        y ^= int.from_bytes(block, "big")
        y = _gf_mult(y, h)
    return y


def _inc32(counter: bytearray) -> None:
    for i in range(15, 11, -1):
        counter[i] = (counter[i] + 1) & 0xFF
        if counter[i] != 0:
            break


def _pure_aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes | None:
    if len(key) not in (16, 32) or len(ciphertext) < 16:
        return None
    tag = ciphertext[-16:]
    body = ciphertext[:-16]
    rk = _key_expansion(key)
    h = int.from_bytes(_aes_encrypt_block(b"\x00" * 16, rk), "big")

    if len(nonce) == 12:
        j0 = bytearray(nonce + b"\x00\x00\x00\x01")
    else:
        pad = b"\x00" * ((16 - (len(nonce) % 16)) % 16)
        s = _ghash(h, nonce + pad + (len(nonce) * 8).to_bytes(16, "big"))
        j0 = bytearray(s.to_bytes(16, "big"))

    # CTR decrypt starting from incr(J0)
    counter = bytearray(j0)
    _inc32(counter)
    plain = bytearray()
    for i in range(0, len(body), 16):
        block = body[i : i + 16]
        keystream = _aes_encrypt_block(bytes(counter), rk)
        plain.extend(b ^ k for b, k in zip(block, keystream))
        _inc32(counter)

    aad_pad = ((16 - (len(aad) % 16)) % 16)
    ct_pad = ((16 - (len(body) % 16)) % 16)
    ghash_in = aad + b"\x00" * aad_pad + body + b"\x00" * ct_pad
    ghash_in += (len(aad) * 8).to_bytes(8, "big") + (len(body) * 8).to_bytes(8, "big")
    s = _ghash(h, ghash_in)
    t = bytes(a ^ b for a, b in zip(_aes_encrypt_block(bytes(j0), rk), s.to_bytes(16, "big")))
    if t != tag:
        return None
    return bytes(plain)
