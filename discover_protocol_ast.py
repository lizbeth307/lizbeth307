#!/usr/bin/env python3
"""
discover_protocol_ast.py — повноцінний скрипт для індукції AST невідомого бінарного протоколу.

Алгоритми:
  1. Consensus field discovery (Protocol Informatics / Discoverer style)
  2. Sequitur — онлайн ієрархічна граматика повторів
  3. Парсер → AST за відновленою схемою

Приклади:
  python3 discover_protocol_ast.py demo
  python3 discover_protocol_ast.py demo --count 60 --show 3
  python3 discover_protocol_ast.py gen-corpus -o corpus.hex --count 100
  python3 discover_protocol_ast.py discover -i corpus.hex -o format.json
  python3 discover_protocol_ast.py parse -f format.json -i corpus.hex
  python3 discover_protocol_ast.py online --count 80 --refine-every 10
  python3 discover_protocol_ast.py test
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path
from typing import Any

# Дозволяє запуск як ./discover_protocol_ast.py без pip install
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from protocol_ast.align import FormatHypothesis, discover_format
from protocol_ast.ast_nodes import AstNode
from protocol_ast.io_utils import (
    hex_dump,
    load_messages,
    load_messages_from_stdin,
    save_corpus_binary,
    save_corpus_hex,
)
from protocol_ast.parser import ParseError, parse_message
from protocol_ast.pipeline import DiscoveryResult, discover_and_parse
from protocol_ast.sequitur import Sequitur, tokenize_message
from protocol_ast.serde import format_to_dict, load_format, save_format
from protocol_ast.synthesize import GroundTruthMessage, make_corpus, raw_messages


# ---------------------------------------------------------------------------
# Вивід
# ---------------------------------------------------------------------------


def _print_format(fmt: FormatHypothesis) -> None:
    print("=== Відновлена схема (лише з байтів) ===")
    for f in fmt.fields:
        size = "dyn" if f.size < 0 else str(f.size)
        vals = ""
        if f.values:
            vals = f" values={list(f.values)}"
        print(
            f"  {f.name:14} kind={f.kind:8} offset={f.offset:4} "
            f"size={size:4}{vals}  {f.notes}"
        )
    print(f"  message length: min={fmt.min_len} max={fmt.max_len}")
    if fmt.length_field_offset is not None:
        print(f"  length field @ offset {fmt.length_field_offset}")


def _print_result_summary(result: DiscoveryResult) -> None:
    print(f"\nheader agreement (перші 8 байт): {result.header_agreement:.1%}")
    print(
        f"parse success: {result.success_rate:.1%} "
        f"({len(result.trees)} ok, {len(result.parse_errors)} err)"
    )
    if result.parse_errors:
        print("помилки:")
        for err in result.parse_errors[:5]:
            print(f"  {err}")
        if len(result.parse_errors) > 5:
            print(f"  ... ще {len(result.parse_errors) - 5}")


def _print_trees(trees: list[AstNode], show: int) -> None:
    print(f"\n=== AST (перші {min(show, len(trees))} повідомлень) ===")
    for i, tree in enumerate(trees[:show]):
        print(f"--- message #{i} ({tree.size} bytes) ---")
        print(tree.pretty())
        print()


def _print_sequitur(result: DiscoveryResult) -> None:
    print("\n=== Sequitur grammar ===")
    print(result.sequitur_grammar or "(порожньо)")


def _print_oracle(corpus: list[GroundTruthMessage], trees: list[AstNode]) -> None:
    if not corpus or not trees:
        return
    print("\n=== Перевірка проти oracle (синтетичний протокол) ===")
    mismatches = 0
    for i, (truth, tree) in enumerate(zip(corpus, trees)):
        payload_nodes = [c for c in tree.children if c.kind == "payload"]
        if not payload_nodes:
            mismatches += 1
            continue
        if payload_nodes[0].value != truth.payload:
            mismatches += 1
            if mismatches <= 3:
                print(
                    f"  msg[{i}] payload mismatch: "
                    f"got {len(payload_nodes[0].value)} bytes, "
                    f"want {len(truth.payload)}"
                )
    ok = len(trees) - mismatches
    print(f"  payload match: {ok}/{len(trees)} ({ok / len(trees):.1%})")
    t0 = trees[0]
    magic = any(c.kind == "fixed" and c.offset == 0 for c in t0.children)
    has_len = any(c.kind == "length" for c in t0.children)
    has_chk = any(c.name == "checksum" for c in t0.children)
    print(f"  magic@0: {magic}  length field: {has_len}  checksum: {has_chk}")


def result_to_json(
    result: DiscoveryResult,
    trees_limit: int | None = None,
) -> dict[str, Any]:
    trees = result.trees[:trees_limit] if trees_limit else result.trees
    return {
        "header_agreement": result.header_agreement,
        "success_rate": result.success_rate,
        "parse_errors": result.parse_errors,
        "format": format_to_dict(result.format),
        "trees": [t.to_dict() for t in trees],
        "sequitur_grammar": result.sequitur_grammar,
        "sequitur_tree": result.sequitur_tree,
    }


# ---------------------------------------------------------------------------
# Команди
# ---------------------------------------------------------------------------


def cmd_demo(args: argparse.Namespace) -> int:
    corpus = make_corpus(n=args.count, seed=args.seed)
    messages = raw_messages(corpus)
    result = discover_and_parse(messages)

    if args.json:
        print(json.dumps(result_to_json(result, trees_limit=args.show), indent=2))
        return 0 if result.success_rate >= args.min_success else 1

    print("Демо: «невідомий» бінарний протокол (oracle лише для перевірки)\n")
    _print_format(result.format)
    _print_result_summary(result)
    _print_sequitur(result)
    _print_trees(result.trees, args.show)
    _print_oracle(corpus, result.trees)

    if args.dump_hex:
        print("\n=== Hex dump (перше повідомлення) ===")
        print(hex_dump(messages[0]))

    return 0 if result.success_rate >= args.min_success else 1


def cmd_gen_corpus(args: argparse.Namespace) -> int:
    corpus = make_corpus(n=args.count, seed=args.seed)
    messages = raw_messages(corpus)
    out = Path(args.output)
    if out.suffix.lower() in {".bin", ".corpus"}:
        save_corpus_binary(messages, out)
    else:
        save_corpus_hex(messages, out)
    print(f"Збережено {len(messages)} повідомлень → {out}")
    if args.verbose:
        print(f"  приклад: {messages[0].hex()}")
    return 0


def _load_input_messages(args: argparse.Namespace) -> list[bytes]:
    if args.input:
        return load_messages(args.input)
    if not sys.stdin.isatty():
        return load_messages_from_stdin()
    raise SystemExit("потрібен --input або stdin з hex-рядками")


def cmd_discover(args: argparse.Namespace) -> int:
    messages = _load_input_messages(args)
    if not messages:
        raise SystemExit("немає повідомлень для аналізу")

    result = discover_and_parse(messages)

    if args.output:
        save_format(result.format, args.output)
        print(f"Схему збережено → {args.output}")

    if args.json:
        print(json.dumps(result_to_json(result, trees_limit=args.show), indent=2))
    else:
        print(f"Проаналізовано {len(messages)} повідомлень\n")
        _print_format(result.format)
        _print_result_summary(result)
        _print_sequitur(result)
        if args.show:
            _print_trees(result.trees, args.show)

    return 0 if result.success_rate >= args.min_success else 1


def cmd_parse(args: argparse.Namespace) -> int:
    fmt = load_format(args.format)
    messages = _load_input_messages(args)
    trees: list[AstNode] = []
    errors: list[str] = []

    for i, msg in enumerate(messages):
        try:
            trees.append(parse_message(msg, fmt))
        except ParseError as exc:
            errors.append(f"msg[{i}]: {exc}")

    total = len(trees) + len(errors)
    rate = len(trees) / total if total else 0.0

    if args.json:
        payload = {
            "success_rate": rate,
            "parse_errors": errors,
            "trees": [t.to_dict() for t in trees[: args.show or len(trees)]],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Парсинг {len(messages)} повідомлень за схемою {args.format}")
        print(f"успіх: {rate:.1%} ({len(trees)} ok, {len(errors)} err)")
        if errors:
            for e in errors[:5]:
                print(f"  {e}")
        if args.show:
            _print_trees(trees, args.show)
        if args.dump_hex and messages:
            print("\n=== Hex (перше повідомлення) ===")
            print(hex_dump(messages[0]))

    return 0 if rate >= args.min_success else 1


def cmd_online(args: argparse.Namespace) -> int:
    """Онлайн-режим: discovery на перших N, потім refine + parse на решті."""
    corpus = make_corpus(n=args.count, seed=args.seed)
    messages = raw_messages(corpus)

    train_n = max(args.train, args.refine_every)
    fmt = discover_format(messages[:train_n])
    seq = Sequitur()

    parsed = 0
    errors: list[str] = []
    refinements = 0

    for i, msg in enumerate(messages):
        if i > 0 and i % args.refine_every == 0:
            fmt = discover_format(messages[: i + 1])
            refinements += 1
            if args.verbose and not args.json:
                print(f"\n[refine #{refinements} @ msg {i}]")
                _print_format(fmt)

        seq.feed_many(tokenize_message(msg) + ["|"])

        try:
            tree = parse_message(msg, fmt)
            parsed += 1
            if args.verbose and not args.json and i < args.show:
                print(f"\n--- online msg #{i} ---")
                print(tree.pretty())
        except ParseError as exc:
            errors.append(f"msg[{i}]: {exc}")

    total = len(messages)
    rate = parsed / total if total else 0.0

    if args.json:
        print(
            json.dumps(
                {
                    "success_rate": rate,
                    "refinements": refinements,
                    "parse_errors": errors,
                    "format": format_to_dict(fmt),
                    "sequitur_grammar": seq.summary(),
                },
                indent=2,
            )
        )
    else:
        print(f"Онлайн-режим: train={train_n}, refine кожні {args.refine_every} msg\n")
        _print_format(fmt)
        print(f"\nрезультат: {parsed}/{total} ({rate:.1%}), refinements={refinements}")
        print(f"Sequitur rules: {len(seq.rules)}")
        if args.verbose:
            print(seq.summary())

    return 0 if rate >= args.min_success else 1


def cmd_test(_args: argparse.Namespace) -> int:
    import unittest

    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--json",
        action="store_true",
        help="вивід у JSON",
    )
    common.add_argument(
        "--min-success",
        type=float,
        default=0.95,
        metavar="RATIO",
        help="мінімальний success rate для exit 0 (default: 0.95)",
    )

    parser = argparse.ArgumentParser(
        prog="discover_protocol_ast.py",
        description=textwrap.dedent(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_demo = sub.add_parser(
        "demo",
        parents=[common],
        help="демо на синтетичному «невідомому» протоколі",
    )
    p_demo.add_argument("--count", type=int, default=40, help="кількість повідомлень")
    p_demo.add_argument("--seed", type=int, default=42)
    p_demo.add_argument("--show", type=int, default=2, help="скільки AST показати")
    p_demo.add_argument("--dump-hex", action="store_true", help="hex dump першого msg")
    p_demo.set_defaults(func=cmd_demo)

    p_gen = sub.add_parser("gen-corpus", help="згенерувати корпус для discover")
    p_gen.add_argument("-o", "--output", required=True, help="файл .hex або .bin")
    p_gen.add_argument("--count", type=int, default=50)
    p_gen.add_argument("--seed", type=int, default=42)
    p_gen.add_argument("-v", "--verbose", action="store_true")
    p_gen.set_defaults(func=cmd_gen_corpus)

    p_disc = sub.add_parser(
        "discover",
        parents=[common],
        help="відновити схему + AST з файлу або stdin",
    )
    p_disc.add_argument("-i", "--input", help="файл .hex / .bin (або stdin)")
    p_disc.add_argument("-o", "--output", help="зберегти схему як JSON")
    p_disc.add_argument("--show", type=int, default=2)
    p_disc.set_defaults(func=cmd_discover)

    p_parse = sub.add_parser(
        "parse",
        parents=[common],
        help="парсити повідомлення за збереженою схемою",
    )
    p_parse.add_argument("-f", "--format", required=True, help="JSON схема")
    p_parse.add_argument("-i", "--input", help="файл .hex / .bin")
    p_parse.add_argument("--show", type=int, default=2)
    p_parse.add_argument("--dump-hex", action="store_true")
    p_parse.set_defaults(func=cmd_parse)

    p_on = sub.add_parser(
        "online",
        parents=[common],
        help="онлайн discovery + refine на льоту",
    )
    p_on.add_argument("--count", type=int, default=80)
    p_on.add_argument("--seed", type=int, default=42)
    p_on.add_argument("--train", type=int, default=20, help="перші N для початкового train")
    p_on.add_argument("--refine-every", type=int, default=10)
    p_on.add_argument("--show", type=int, default=2)
    p_on.add_argument("-v", "--verbose", action="store_true")
    p_on.set_defaults(func=cmd_online)

    p_test = sub.add_parser("test", help="запустити unit-тести")
    p_test.set_defaults(func=cmd_test)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
