"""Export discovered format to Wireshark Lua dissector."""

from __future__ import annotations

from typing import Any

MAX_FIELDS = 32


def _sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)


def format_to_lua(fmt: dict[str, Any], *, flow: str, proto_name: str | None = None) -> str:
    """Generate Wireshark Lua dissector from discover_format() dict."""
    fields = fmt.get("fields", [])[:MAX_FIELDS]
    truncated = len(fmt.get("fields", [])) > MAX_FIELDS
    endian = fmt.get("endian") or fmt.get("length_endian") or "be"
    enc = "big" if endian == "be" else "little"
    safe_flow = _sanitize(flow.replace(":", "_"))
    pname = proto_name or f"discovered_{safe_flow.lower()}"
    plabel = flow.replace("_", " ")

    lines = [
        f"-- Auto-generated dissector for flow {flow}",
        f"-- Endian: {endian}" + (" (truncated)" if truncated else ""),
        f'local proto = Proto("{pname}", "Discovered {plabel}")',
        "",
    ]

    field_vars: list[str] = []
    for i, f in enumerate(fields):
        kind = f.get("kind", "")
        name = _sanitize(f.get("name", f"field_{i}"))
        var = f"f_{name}"
        field_vars.append((var, name, kind, f))
        if kind == "length":
            lines.append(
                f'local {var} = ProtoField.uint16("{pname}.{name}", "{name}", base.DEC, nil, base.{enc.upper()})'
            )
        elif kind == "payload":
            lines.append(
                f'local {var} = ProtoField.bytes("{pname}.{name}", "{name}")'
            )
        elif kind == "enum":
            lines.append(
                f'local {var} = ProtoField.uint8("{pname}.{name}", "{name}", base.HEX)'
            )
        else:
            lines.append(
                f'local {var} = ProtoField.uint8("{pname}.{name}", "{name}", base.HEX)'
            )

    lines.append(f"proto.fields = {{{', '.join(v[0] for v in field_vars)}}}")
    lines.append("")
    lines.append("function proto.dissector(buffer, pinfo, tree)")
    lines.append(f'    pinfo.cols.protocol = "{plabel}"')
    lines.append("    local subtree = tree:add(proto, buffer(), \"Discovered message\")")
    lines.append("    local offset = 0")
    lines.append("    local len_field = nil")

    for var, name, kind, f in field_vars:
        size = f.get("size", 1)
        if kind == "length":
            lines.append(f"    len_field = buffer(offset, 2):uint{enc}()")
            lines.append(f"    subtree:add({var}, buffer(offset, 2))")
            lines.append("    offset = offset + 2")
        elif kind == "payload":
            lines.append("    if len_field then")
            lines.append(f"        subtree:add({var}, buffer(offset, len_field))")
            lines.append("    else")
            lines.append(f"        subtree:add({var}, buffer(offset))")
            lines.append("    end")
        elif size and size > 1:
            lines.append(f"    subtree:add({var}, buffer(offset, {size}))")
            lines.append(f"    offset = offset + {size}")
        else:
            lines.append(f"    if offset < buffer:len() then")
            lines.append(f"        subtree:add({var}, buffer(offset, 1))")
            lines.append("        offset = offset + 1")
            lines.append("    end")

    lines.append("end")
    lines.append("")

    # Register on port
    upper = flow.upper()
    if upper.startswith("TCP:"):
        port = int(flow.split(":")[-1])
        lines.append(f'DissectorTable.get("tcp.port"):add({port}, proto)')
    elif upper.startswith("UDP:"):
        port = int(flow.split(":")[-1])
        lines.append(f'DissectorTable.get("udp.port"):add({port}, proto)')
    else:
        lines.append("-- No port registration (unknown flow label)")

    return "\n".join(lines) + "\n"


def export_flow_lua(flow: str, fmt: dict[str, Any]) -> str:
    return format_to_lua(fmt, flow=flow)
