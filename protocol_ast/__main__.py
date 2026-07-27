"""Demo: recover AST from an unknown synthetic protocol.

Usage:
  python -m protocol_ast
  python -m protocol_ast --messages 60 --show 2
"""

from __future__ import annotations

import argparse
import json
import sys

from .pipeline import discover_and_parse
from .synthesize import make_corpus, raw_messages


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Unknown-protocol AST discovery demo")
    p.add_argument("--messages", type=int, default=40, help="corpus size")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--show", type=int, default=2, help="how many ASTs to print")
    p.add_argument("--json", action="store_true", help="emit machine-readable summary")
    args = p.parse_args(argv)

    corpus = make_corpus(n=args.messages, seed=args.seed)
    messages = raw_messages(corpus)
    result = discover_and_parse(messages)

    if args.json:
        payload = {
            "header_agreement": result.header_agreement,
            "success_rate": result.success_rate,
            "parse_errors": result.parse_errors,
            "fields": [
                {
                    "name": f.name,
                    "offset": f.offset,
                    "size": f.size,
                    "kind": f.kind,
                    "notes": f.notes,
                }
                for f in result.format.fields
            ],
            "sample_ast": result.trees[0].to_dict() if result.trees else None,
            "sequitur_grammar": result.sequitur_grammar,
        }
        print(json.dumps(payload, indent=2))
        return 0 if result.success_rate >= 0.95 else 1

    print("=== Format hypothesis (from bytes only) ===")
    for f in result.format.fields:
        size = "dyn" if f.size < 0 else str(f.size)
        print(f"  {f.name:12} kind={f.kind:8} off={f.offset:3} size={size:4}  {f.notes}")
    print(f"\nheader agreement (first 8 bytes): {result.header_agreement:.2%}")
    print(f"parse success: {result.success_rate:.2%}  ({len(result.trees)} ok, {len(result.parse_errors)} err)")

    print("\n=== Sequitur grammar (hierarchical repeats) ===")
    print(result.sequitur_grammar)

    print("\n=== Sample ASTs ===")
    for tree in result.trees[: args.show]:
        print(tree.pretty())
        print("---")

    # Quick oracle check against ground truth for the demo narrative
    if result.trees:
        t0 = result.trees[0]
        g0 = corpus[0]
        by_name = {c.name: c for c in t0.children}
        magic_ok = any(c.kind == "fixed" and c.offset == 0 for c in t0.children)
        length_nodes = [c for c in t0.children if c.kind == "length"]
        payload_nodes = [c for c in t0.children if c.kind == "payload"]
        print("=== Oracle checks (ground truth vs recovered) ===")
        print(f"  magic/fixed@0 recovered: {magic_ok}")
        if length_nodes and payload_nodes:
            print(
                f"  length={length_nodes[0].value} payload_len={payload_nodes[0].size} "
                f"truth_payload_len={len(g0.payload)} match={payload_nodes[0].size == len(g0.payload)}"
            )
        checksum = by_name.get("checksum")
        if checksum is not None:
            print(f"  checksum recovered: value={checksum.value}")

    return 0 if result.success_rate >= 0.95 else 1


if __name__ == "__main__":
    sys.exit(main())
