from __future__ import annotations

import argparse
import sys
from pathlib import Path

from compiler_core.ast_nodes import format_ast
from compiler_core.codegen import CodeGenerationError, generate_target_code
from compiler_core.icg import ICGError, compile_source_to_tac, format_instructions, parse_instructions
from compiler_core.lexer import LexerError, format_tokens, tokenize_source
from compiler_core.optimizer import optimize_instructions
from compiler_core.parser import ParseError, parse_source
from compiler_core.semantic import analyze_program, format_symbol_table


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_lexical(source: str) -> None:
    tokens = tokenize_source(source)
    print("=== Phase 1: Lexical Analysis ===")
    print(format_tokens(tokens))


def run_syntax(source: str) -> None:
    ast = parse_source(source)
    print("=== Phase 2: Syntax Analysis ===")
    print(format_ast(ast))


def run_semantic(source: str) -> None:
    ast = parse_source(source)
    result = analyze_program(ast)

    print("=== Phase 3: Semantic Analysis ===")
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

    if not result.ok:
        raise SystemExit(1)


def run_icg(source: str, plain: bool = False) -> list[object]:
    instructions = compile_source_to_tac(source)
    print("=== Phase 4: Intermediate Code Generation ===")
    if plain:
        print(format_instructions(instructions, include_numbers=False))
    else:
        print(format_instructions(instructions, include_numbers=True))
    return instructions


def read_tac_or_source(path: Path, force_source: bool) -> list[object]:
    text = read_source(path)
    if force_source:
        return compile_source_to_tac(text)
    try:
        instructions = parse_instructions(text)
        if instructions:
            return instructions
    except ICGError:
        pass
    return compile_source_to_tac(text)


def run_optimize(path: Path, force_source: bool = False, show_before_after: bool = False) -> list[object]:
    original = read_tac_or_source(path, force_source)
    optimized, report = optimize_instructions(original)

    print("=== Phase 5: Optimization ===")
    print(report.format())
    print()
    if show_before_after:
        print("Original TAC")
        print(format_instructions(original))
        print()
        print("Optimized TAC")
    print(format_instructions(optimized))
    return optimized


def run_codegen(path: Path, force_source: bool = False) -> None:
    text = read_source(path)
    if force_source:
        instructions = optimize_instructions(compile_source_to_tac(text))[0]
    else:
        try:
            instructions = optimize_instructions(parse_instructions(text))[0]
        except ICGError:
            instructions = optimize_instructions(compile_source_to_tac(text))[0]

    print("=== Phase 6: Target Code Generation ===")
    print(generate_target_code(instructions))


def run_all(path: Path, plain: bool = False, show_before_after: bool = False) -> None:
    source = read_source(path)
    run_lexical(source)
    print()
    run_syntax(source)
    print()
    run_semantic(source)
    print()
    instructions = run_icg(source, plain=plain)
    print()
    optimized, report = optimize_instructions(instructions)
    print("=== Phase 5: Optimization ===")
    print(report.format())
    print()
    if show_before_after:
        print("Original TAC")
        print(format_instructions(instructions))
        print()
        print("Optimized TAC")
    print(format_instructions(optimized))
    print()
    print("=== Phase 6: Target Code Generation ===")
    print(generate_target_code(optimized))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Lumina compiler phases from the project root.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Run all phases sequentially")
    group.add_argument(
        "--phase",
        choices=["1", "2", "3", "4", "5", "6", "lexical", "syntax", "semantic", "icg", "optimize", "codegen"],
        help="Run a specific phase"
    )
    parser.add_argument("input_file", help="Path to a Lumina source file or TAC file")
    parser.add_argument("--plain", action="store_true", help="Print TAC without line numbers for Phase 4")
    parser.add_argument("--show-before-after", action="store_true", help="Show original and optimized TAC for Phase 5")
    parser.add_argument("--from-source", action="store_true", help="Treat input as Lumina source for Phase 5 or Phase 6")
    args = parser.parse_args()

    try:
        path = Path(args.input_file)
        if args.all:
            run_all(path, plain=args.plain, show_before_after=args.show_before_after)
        elif args.phase in {"1", "lexical"}:
            run_lexical(read_source(path))
        elif args.phase in {"2", "syntax"}:
            run_syntax(read_source(path))
        elif args.phase in {"3", "semantic"}:
            run_semantic(read_source(path))
        elif args.phase in {"4", "icg"}:
            run_icg(read_source(path), plain=args.plain)
        elif args.phase in {"5", "optimize"}:
            run_optimize(path, force_source=args.from_source, show_before_after=args.show_before_after)
        elif args.phase in {"6", "codegen"}:
            run_codegen(path, force_source=args.from_source)
        else:
            parser.print_help()
            return 1
    except FileNotFoundError:
        print(f"File Error: input file not found: {args.input_file}", file=sys.stderr)
        return 1
    except (LexerError, ParseError, ICGError, CodeGenerationError) as exc:
        print(exc, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
