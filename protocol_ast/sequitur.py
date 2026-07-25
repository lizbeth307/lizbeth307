"""Minimal Sequitur-style hierarchical digram compression.

Turns a token stream into a context-free grammar that exposes repeated
structure — useful as an online hierarchical AST prior for unknown protocols.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Rule:
    name: str
    body: list[str] = field(default_factory=list)


class Sequitur:
    """Online digram uniqueness + rule utility (simplified Sequitur)."""

    def __init__(self) -> None:
        self.rules: dict[str, Rule] = {"S": Rule("S")}
        self._next_id = 0
        self._digram_index: dict[tuple[str, str], list[tuple[str, int]]] = {}

    def _new_rule_name(self) -> str:
        self._next_id += 1
        return f"R{self._next_id}"

    def feed(self, token: str) -> None:
        start = self.rules["S"]
        start.body.append(token)
        if len(start.body) >= 2:
            self._enforce(start.name, len(start.body) - 2)

    def feed_many(self, tokens: list[str]) -> None:
        for t in tokens:
            self.feed(t)

    def _enforce(self, rule_name: str, index: int) -> None:
        rule = self.rules[rule_name]
        if index < 0 or index + 1 >= len(rule.body):
            return
        digram = (rule.body[index], rule.body[index + 1])
        locations = self._digram_index.get(digram, [])
        # remove stale locations
        locations = [
            (rn, i)
            for rn, i in locations
            if rn in self.rules
            and i + 1 < len(self.rules[rn].body)
            and (self.rules[rn].body[i], self.rules[rn].body[i + 1]) == digram
        ]
        # current occurrence
        current = (rule_name, index)
        other = [loc for loc in locations if loc != current]
        if not other:
            self._digram_index[digram] = locations + [current]
            return

        # Create or reuse a rule for this digram
        existing_rule = None
        for name, r in self.rules.items():
            if name != "S" and r.body == list(digram):
                existing_rule = name
                break
        if existing_rule is None:
            existing_rule = self._new_rule_name()
            self.rules[existing_rule] = Rule(existing_rule, list(digram))

        # Replace all occurrences with the rule nonterminal
        for rn, i in other + [current]:
            body = self.rules[rn].body
            if i + 1 < len(body) and (body[i], body[i + 1]) == digram:
                body[i : i + 2] = [existing_rule]
                # recursively check around the substitution
                if i - 1 >= 0:
                    self._enforce(rn, i - 1)
                if i < len(self.rules[rn].body) - 1:
                    self._enforce(rn, i)

        self._digram_index.pop(digram, None)
        self._prune_unused()

    def _prune_unused(self) -> None:
        used = {"S"}
        stack = ["S"]
        while stack:
            name = stack.pop()
            for sym in self.rules[name].body:
                if sym in self.rules and sym not in used:
                    used.add(sym)
                    stack.append(sym)
        for name in list(self.rules):
            if name not in used:
                del self.rules[name]

    def expand(self, name: str = "S") -> list[str]:
        out: list[str] = []
        for sym in self.rules[name].body:
            if sym in self.rules and sym != name:
                out.extend(self.expand(sym))
            else:
                out.append(sym)
        return out

    def tree(self, name: str = "S") -> dict:
        children = []
        for sym in self.rules[name].body:
            if sym in self.rules and sym != name:
                children.append(self.tree(sym))
            else:
                children.append({"token": sym})
        return {"rule": name, "children": children}

    def summary(self) -> str:
        lines = []
        for name, rule in self.rules.items():
            lines.append(f"{name} -> {' '.join(rule.body)}")
        return "\n".join(lines)


def tokenize_message(message: bytes) -> list[str]:
    """Byte tokens with a length marker for variable payloads."""
    return [f"B{b:02X}" for b in message]
