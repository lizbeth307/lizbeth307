"""AST node types for recovered protocol messages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AstNode:
    name: str
    kind: str
    offset: int
    size: int
    value: Any = None
    children: list["AstNode"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "offset": self.offset,
            "size": self.size,
            "value": _jsonable(self.value),
            "children": [c.to_dict() for c in self.children],
        }

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        val = ""
        if self.value is not None and not self.children:
            if isinstance(self.value, (bytes, bytearray)):
                shown = self.value if len(self.value) <= 16 else self.value[:16]
                hexv = shown.hex()
                suffix = "..." if len(self.value) > 16 else ""
                val = f" = {hexv}{suffix}"
            else:
                val = f" = {self.value}"
        line = f"{pad}{self.name}:{self.kind}[{self.offset}:{self.offset + self.size}]{val}"
        if not self.children:
            return line
        kids = "\n".join(c.pretty(indent + 1) for c in self.children)
        return f"{line}\n{kids}"


def _jsonable(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    return value
