from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compiler_core.icg import ICGError, compile_source_to_tac, format_instructions
from compiler_core.lexer import LexerError
from compiler_core.parser import ParseError


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 4: Intermediate Code Generation using three-address code.")
    parser.add_argument("input_file", help="Path to a semantically valid Lumina source file")
    parser.add_argument("--plain", action="store_true", help="Print TAC without line numbers")
    args = parser.parse_args()

    try:
        source = Path(args.input_file).read_text(encoding="utf-8")
        instructions = compile_source_to_tac(source)
    except FileNotFoundError:
        print(f"File Error: input file not found: {args.input_file}", file=sys.stderr)
        return 1
    except (LexerError, ParseError, ICGError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.plain:
        print(format_instructions(instructions, include_numbers=False))
    else:
        print("Intermediate Code Generation Successful")
        print(format_instructions(instructions, include_numbers=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
