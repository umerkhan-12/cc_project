from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compiler_core.lexer import LexerError, format_tokens, tokenize_source


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1: Lexical Analysis for Lumina source files.")
    parser.add_argument("input_file", help="Path to a Lumina source file")
    args = parser.parse_args()

    try:
        source = Path(args.input_file).read_text(encoding="utf-8")
        tokens = tokenize_source(source)
    except FileNotFoundError:
        print(f"File Error: input file not found: {args.input_file}", file=sys.stderr)
        return 1
    except LexerError as exc:
        print(exc, file=sys.stderr)
        return 1

    print("Lexical Analysis Successful")
    print(format_tokens(tokens))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

