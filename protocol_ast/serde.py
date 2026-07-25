"""JSON serialization for discovered protocol formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .align import FieldHypothesis, FormatHypothesis


def format_to_dict(fmt: FormatHypothesis) -> dict[str, Any]:
    return {
        "min_len": fmt.min_len,
        "max_len": fmt.max_len,
        "length_field_offset": fmt.length_field_offset,
        "length_endian": fmt.length_endian,
        "length_width": fmt.length_width,
        "fields": [
            {
                "name": f.name,
                "offset": f.offset,
                "size": f.size,
                "kind": f.kind,
                "values": list(f.values),
                "notes": f.notes,
            }
            for f in fmt.fields
        ],
    }


def format_from_dict(data: dict[str, Any]) -> FormatHypothesis:
    fields = [
        FieldHypothesis(
            name=f["name"],
            offset=f["offset"],
            size=f["size"],
            kind=f["kind"],
            values=tuple(f.get("values", ())),
            notes=f.get("notes", ""),
        )
        for f in data["fields"]
    ]
    return FormatHypothesis(
        fields=fields,
        min_len=data["min_len"],
        max_len=data["max_len"],
        length_field_offset=data.get("length_field_offset"),
        length_endian=data.get("length_endian", "le"),
        length_width=data.get("length_width", "u16"),
    )


def save_format(fmt: FormatHypothesis, path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(format_to_dict(fmt), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_format(path: str | Path) -> FormatHypothesis:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return format_from_dict(data)
