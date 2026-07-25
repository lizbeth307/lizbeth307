"""Parse raw messages into AST using a discovered format hypothesis."""

from __future__ import annotations

from .align import FieldHypothesis, FormatHypothesis, _read_u16, _read_u32, _read_varint
from .ast_nodes import AstNode


class ParseError(ValueError):
    pass


def parse_message(message: bytes, fmt: FormatHypothesis) -> AstNode:
    children: list[AstNode] = []
    cursor = 0
    length_value: int | None = None

    for field in fmt.fields:
        if field.kind == "payload":
            if length_value is not None:
                end = cursor + length_value
            else:
                # leave room for trailing non-payload fields with known size
                trailer = sum(f.size for f in fmt.fields if f.size > 0 and f.offset < 0)
                end = len(message) - trailer
            if end < cursor or end > len(message):
                raise ParseError(
                    f"payload bounds invalid: cursor={cursor} end={end} len={len(message)}"
                )
            payload = message[cursor:end]
            children.append(
                AstNode(
                    name=field.name,
                    kind=field.kind,
                    offset=cursor,
                    size=len(payload),
                    value=payload,
                )
            )
            cursor = end
            continue

        if field.offset < 0:
            # trailer relative to end — handled after payload; size known
            size = field.size
            start = len(message) - size
            if start < cursor:
                # already consumed; read from cursor
                start = cursor
            chunk = message[start : start + size]
            node = _leaf(field, start, chunk)
            children.append(node)
            cursor = start + size
            continue

        size = field.size
        if cursor + size > len(message):
            raise ParseError(f"field {field.name} overruns message")
        chunk = message[cursor : cursor + size]
        if field.kind == "length":
            if fmt.length_width == "u32":
                length_value = _read_u32(message, cursor, fmt.length_endian)
            elif fmt.length_width == "varint":
                parsed = _read_varint(message, cursor)
                if not parsed:
                    raise ParseError("invalid varint length")
                length_value, _ = parsed
            else:
                length_value = _read_u16(message, cursor, fmt.length_endian)
            children.append(
                AstNode(
                    name=field.name,
                    kind=field.kind,
                    offset=cursor,
                    size=size,
                    value=length_value,
                )
            )
        else:
            children.append(_leaf(field, cursor, chunk))
        cursor = cursor + size

    if cursor != len(message):
        # Allow exact consumption only; leftover means hypothesis mismatch.
        raise ParseError(f"unconsumed trailing bytes: {len(message) - cursor}")

    return AstNode(
        name="message",
        kind="root",
        offset=0,
        size=len(message),
        children=children,
    )


def _leaf(field: FieldHypothesis, offset: int, chunk: bytes) -> AstNode:
    if field.kind == "fixed" and field.values and len(field.values) == len(chunk):
        value: object = bytes(field.values).hex() if len(chunk) > 1 else chunk[0]
    elif len(chunk) == 1:
        value = chunk[0]
    elif len(chunk) == 2:
        value = chunk[0] | (chunk[1] << 8)
    else:
        value = chunk
    return AstNode(
        name=field.name,
        kind=field.kind,
        offset=offset,
        size=len(chunk),
        value=value,
    )
