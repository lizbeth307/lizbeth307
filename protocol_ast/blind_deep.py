"""Сліпий глибокий аналіз — не знаємо протокол, лише байти.

Рекурсивно шукає:
  - u16/u24 length-поля (LE/BE)
  - QUIC-подібні varint
  - вкладені кадри (TLS record, length-prefixed PDU)
  - Sequitur-ієрархію на токенах
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .align import FormatHypothesis, discover_format
from .deep_decode import deep_analyze_flow, split_tls_records
from .pipeline import discover_and_parse
from .sequitur import Sequitur, tokenize_message


@dataclass
class InnerFrame:
    offset: int
    size: int
    raw: bytes
    child_format: FormatHypothesis | None = None


@dataclass
class BlindReport:
    flow: str
    outer_messages: int
    outer_format: FormatHypothesis
    length_splits: list[dict]
    inner_frames: list[InnerFrame]
    sequitur_rules: int
    notes: list[str] = field(default_factory=list)


def _read_varint(data: bytes, off: int) -> tuple[int, int] | None:
    if off >= len(data):
        return None
    first = data[off]
    prefix = 1 << (first >> 6)
    if off + prefix > len(data):
        return None
    if prefix == 1:
        return first & 0x3F, 1
    if prefix == 2:
        return ((first & 0x3F) << 8) | data[off + 1], 2
    if prefix == 4:
        v = 0
        for i in range(1, 4):
            v = (v << 8) | data[off + i]
        return (first & 0x3F) << 24 | v, 4
    v = 0
    for i in range(1, 8):
        v = (v << 8) | data[off + i]
    return (first & 0x3F) << 56 | v, 8


def _score_varint_length(messages: list[bytes], off: int) -> float:
    hits = total = 0
    for m in messages:
        if off >= len(m):
            continue
        parsed = _read_varint(m, off)
        if not parsed:
            continue
        total += 1
        val, used = parsed
        rest = len(m) - off - used
        if val == rest or val == rest - 1 or val == rest - 2:
            hits += 1
    return hits / total if total else 0.0


def _score_tls_like(messages: list[bytes]) -> tuple[float, list[bytes]]:
    """Сліпо ріжемо на кадри type|ver|len(BE) без назви TLS."""
    frames: list[bytes] = []
    ok = 0
    for m in messages:
        off = 0
        pkt_ok = True
        while off + 5 <= len(m):
            ctype, v1, v2, ln = m[off], m[off + 1], m[off + 2], (m[off + 3] << 8) | m[off + 4]
            if ctype not in range(20, 26):
                pkt_ok = False
                break
            if v1 != 3:
                pkt_ok = False
                break
            end = off + 5 + ln
            if end > len(m):
                pkt_ok = False
                break
            frames.append(m[off:end])
            off = end
        if pkt_ok and off == len(m):
            ok += 1
    rate = ok / len(messages) if messages else 0
    return rate, frames


def _split_quic_packets(messages: list[bytes]) -> tuple[float, list[bytes]]:
    """Сліпий QUIC: long header з валідною version."""
    from .deep_decode import parse_quic_packet

    frames: list[bytes] = []
    ok = 0
    for m in messages:
        p = parse_quic_packet(m)
        if p:
            frames.append(m)
            ok += 1
    rate = ok / len(messages) if messages else 0
    return rate, frames


def _entropy_note(payloads: list[bytes]) -> str:
    """Середня унікальність байтів — не зупинка, а маркер «шифрований шар»."""
    if not payloads:
        return ""
    total = uniq = 0
    for p in payloads[:20]:
        for b in p[:32]:
            total += 1
            uniq += 1  # simplified
        uniq -= max(0, 32 - len(set(p[:32])))
    ratio = len(set(b for p in payloads[:10] for b in p[:16])) / max(1, min(16, min(len(p) for p in payloads)))
    if ratio > 0.85:
        return "висока ентропія → шукаємо вкладені кадри та повтори (Sequitur)"
    return "структурований шар"


def _find_best_length_offset(messages: list[bytes]) -> list[dict]:
    """Усі кандидати length-полів з оцінкою (u16 + varint)."""
    if not messages:
        return []
    min_len = min(map(len, messages))
    cands: list[dict] = []
    for off in range(min(24, min_len - 1)):
        for end in ("le", "be"):
            hits = total = 0
            for m in messages:
                if off + 2 >= len(m):
                    continue
                total += 1
                if end == "le":
                    decl = m[off] | (m[off + 1] << 8)
                else:
                    decl = (m[off] << 8) | m[off + 1]
                rest = len(m) - off - 2
                if decl == rest or abs(decl - rest) <= 2:
                    hits += 1
            if total:
                score = hits / total
                if score >= 0.5:
                    cands.append({"offset": off, "kind": f"u16_{end}", "score": round(score, 3)})
        vs = _score_varint_length(messages, off)
        if vs >= 0.5:
            cands.append({"offset": off, "kind": "varint", "score": round(vs, 3)})
    return sorted(cands, key=lambda x: -x["score"])[:5]


def blind_analyze(flow: str, payloads: list[bytes]) -> BlindReport:
    notes: list[str] = []
    outer = discover_format(payloads)

    tls_rate, tls_frames = split_tls_records(payloads)
    quic_rate, quic_frames = _split_quic_packets(payloads)

    inner: list[InnerFrame] = []
    splits = _find_best_length_offset(payloads)

    notes.append(_entropy_note(payloads))

    deep = deep_analyze_flow(flow, payloads)
    if deep:
        kind = deep.get("kind")
        if kind == "tls" and deep.get("sni_hosts"):
            notes.append(f"SNI: {', '.join(deep['sni_hosts'][:6])}")
        if kind == "dns" and deep.get("domains"):
            notes.append(f"DNS domains: {', '.join(deep['domains'][:6])}")
        if kind == "quic":
            notes.append(
                f"QUIC parsed: long={deep.get('long_header', 0)} "
                f"short={deep.get('short_header', 0)} {deep.get('types', {})}"
            )
        if kind == "ntp":
            notes.append(f"NTP: modes={deep.get('modes', {})}")
        if kind == "xmpp":
            notes.append(f"XMPP binary frames: protobuf={deep.get('protobuf_like', 0)}")

    if tls_rate >= 0.6:
        notes.append(f"вкладені кадри type|ver|len: {tls_rate:.0%} повідомлень ({len(tls_frames)} кадрів)")
        if tls_frames:
            inner_fmt = discover_format(tls_frames)
            for fr in tls_frames[:3]:
                inner.append(InnerFrame(0, len(fr), fr, inner_fmt))
            # AST на внутрішніх кадрах
            inner_result = discover_and_parse(tls_frames)
            notes.append(f"внутрішній parse: {inner_result.success_rate:.0%}")

    if quic_rate >= 0.5 and not tls_frames:
        long_n = sum(1 for p in quic_frames if p[0] & 0x80)
        notes.append(f"UDP-кадри (QUIC-подібні): {quic_rate:.0%}, long-header={long_n}")
        if quic_frames:
            qfmt = discover_format(quic_frames)
            inner_result = discover_and_parse(quic_frames)
            notes.append(f"внутрішній parse: {inner_result.success_rate:.0%}")
            for fr in quic_frames[:2]:
                inner.append(InnerFrame(0, len(fr), fr, qfmt))

    if not any("вкладені" in n or "UDP-кадри" in n for n in notes):
        if splits:
            notes.append(f"length-кандидати: {splits[0]}")

    seq = Sequitur()
    for p in payloads[:12]:
        seq.feed_many(tokenize_message(p) + ["|"])

    return BlindReport(
        flow=flow,
        outer_messages=len(payloads),
        outer_format=outer,
        length_splits=splits,
        inner_frames=inner,
        sequitur_rules=len(seq.rules),
        notes=notes,
    )
