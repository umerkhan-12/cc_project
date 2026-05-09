from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compiler_core.codegen import CodeGenerationError, generate_target_code
from compiler_core.icg import ICGError, compile_source_to_tac, parse_instructions
from compiler_core.lexer import LexerError
from compiler_core.optimizer import optimize_instructions
from compiler_core.parser import ParseError


def read_tac_or_source(path: Path, force_source: bool):
    text = path.read_text(encoding="utf-8")
    if force_source:
        tac = compile_source_to_tac(text)
        return optimize_instructions(tac)[0]
    try:
        instructions = parse_instructions(text)
        if instructions:
            return optimize_instructions(instructions)[0]
    except ICGError:
        pass
    tac = compile_source_to_tac(text)
    return optimize_instructions(tac)[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 6: Target Code Generation for a stack-machine target."
    )
    parser.add_argument("input_file", help="Path to optimized TAC, unoptimized TAC, or Lumina source")
    parser.add_argument("--from-source", action="store_true", help="Treat input as Lumina source code")
    args = parser.parse_args()

    try:
        instructions = read_tac_or_source(Path(args.input_file), args.from_source)
        print(generate_target_code(instructions))
    except FileNotFoundError:
        print(f"File Error: input file not found: {args.input_file}", file=sys.stderr)
        return 1
    except (LexerError, ParseError, ICGError, CodeGenerationError) as exc:
        print(exc, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
