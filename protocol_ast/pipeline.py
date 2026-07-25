"""End-to-end: discover format from corpus, parse messages into AST."""

from __future__ import annotations

from dataclasses import dataclass

from .align import FormatHypothesis, discover_format, mean_agreement
from .ast_nodes import AstNode
from .parser import ParseError, parse_message
from .sequitur import Sequitur, tokenize_message


@dataclass
class DiscoveryResult:
    format: FormatHypothesis
    trees: list[AstNode]
    parse_errors: list[str]
    sequitur_grammar: str
    sequitur_tree: dict
    header_agreement: float

    @property
    def success_rate(self) -> float:
        total = len(self.trees) + len(self.parse_errors)
        return len(self.trees) / total if total else 0.0


def discover_and_parse(messages: list[bytes]) -> DiscoveryResult:
    fmt = discover_format(messages)
    trees: list[AstNode] = []
    errors: list[str] = []
    for i, msg in enumerate(messages):
        try:
            trees.append(parse_message(msg, fmt))
        except ParseError as exc:
            errors.append(f"msg[{i}]: {exc}")

    seq = Sequitur()
    # Feed a few tokenized messages so hierarchical rules appear.
    for msg in messages[:8]:
        seq.feed_many(tokenize_message(msg) + ["|"])

    return DiscoveryResult(
        format=fmt,
        trees=trees,
        parse_errors=errors,
        sequitur_grammar=seq.summary(),
        sequitur_tree=seq.tree(),
        header_agreement=mean_agreement(messages, limit=8),
    )
