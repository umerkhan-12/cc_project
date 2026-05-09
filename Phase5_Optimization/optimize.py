from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compiler_core.icg import ICGError, compile_source_to_tac, format_instructions, parse_instructions
from compiler_core.lexer import LexerError
from compiler_core.optimizer import optimize_instructions
from compiler_core.parser import ParseError


def comment_block(text: str) -> str:
    return "\n".join(f"# {line}" for line in text.splitlines())


def read_tac_or_source(path: Path, force_source: bool):
    text = path.read_text(encoding="utf-8")
    if force_source:
        return compile_source_to_tac(text)
    try:
        instructions = parse_instructions(text)
        if instructions:
            return instructions
    except ICGError:
        pass
    return compile_source_to_tac(text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 5: Optimization. Reads TAC by default, or Lumina source as a convenience."
    )
    parser.add_argument("input_file", help="Path to a TAC file produced by Phase 4, or a Lumina source file")
    parser.add_argument("--from-source", action="store_true", help="Treat input as Lumina source code")
    parser.add_argument("--show-before-after", action="store_true", help="Show both original and optimized TAC")
    args = parser.parse_args()

    try:
        original = read_tac_or_source(Path(args.input_file), args.from_source)
        optimized, report = optimize_instructions(original)
    except FileNotFoundError:
        print(f"File Error: input file not found: {args.input_file}", file=sys.stderr)
        return 1
    except (LexerError, ParseError, ICGError) as exc:
        print(exc, file=sys.stderr)
        return 1

    print(comment_block(report.format()))
    print()
    if args.show_before_after:
        print("Original TAC")
        print(format_instructions(original))
        print()
        print("Optimized TAC")
    print(format_instructions(optimized))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
