from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compiler_core.lexer import LexerError
from compiler_core.parser import ParseError, parse_source
from compiler_core.semantic import analyze_program, format_symbol_table


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3: Semantic Analysis and symbol table generation.")
    parser.add_argument("input_file", help="Path to a Lumina source file")
    args = parser.parse_args()

    try:
        source = Path(args.input_file).read_text(encoding="utf-8")
        ast = parse_source(source)
        result = analyze_program(ast)
    except FileNotFoundError:
        print(f"File Error: input file not found: {args.input_file}", file=sys.stderr)
        return 1
    except (LexerError, ParseError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if result.ok:
        print("Semantic Analysis Successful")
    else:
        print("Semantic Analysis Failed")

    for warning in result.warnings:
        print(warning)
    for error in result.errors:
        print(error)

    print()
    print(format_symbol_table(result.symbols))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
