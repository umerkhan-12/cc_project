from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compiler_core.ast_nodes import format_ast
from compiler_core.lexer import LexerError
from compiler_core.parser import ParseError, parse_source


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2: Syntax Analysis and AST construction.")
    parser.add_argument("input_file", help="Path to a Lumina source file")
    args = parser.parse_args()

    try:
        source = Path(args.input_file).read_text(encoding="utf-8")
        ast = parse_source(source)
    except FileNotFoundError:
        print(f"File Error: input file not found: {args.input_file}", file=sys.stderr)
        return 1
    except (LexerError, ParseError) as exc:
        print(exc, file=sys.stderr)
        return 1

    print("Syntax Analysis Successful")
    print(format_ast(ast))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

