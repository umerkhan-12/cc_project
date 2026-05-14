from __future__ import annotations

import json
import sys
from contextlib import redirect_stdout
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from compiler_core.codegen import CodeGenerationError, generate_target_code
from compiler_core.ast_nodes import format_ast
from compiler_core.icg import ICGError, compile_source_to_tac, format_instructions, parse_instructions
from compiler_core.lexer import LexerError, format_tokens, tokenize_source
from compiler_core.optimizer import optimize_instructions
from compiler_core.parser import ParseError, parse_source
from compiler_core.semantic import analyze_program, format_symbol_table

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def capture_output(func, *args, **kwargs) -> str:
    buffer = StringIO()
    with redirect_stdout(buffer):
        func(*args, **kwargs)
    return buffer.getvalue()


def read_tac_or_source(text: str, force_source: bool) -> list[object]:
    if force_source:
        return compile_source_to_tac(text)

    try:
        instructions = parse_instructions(text)
        if instructions:
            return instructions
    except ICGError:
        pass

    return compile_source_to_tac(text)


def run_lexical(source: str) -> str:
    tokens = tokenize_source(source)
    return format_tokens(tokens)


def run_syntax(source: str) -> str:
    ast = parse_source(source)
    return format_ast(ast)


def run_semantic(source: str) -> str:
    ast = parse_source(source)
    result = analyze_program(ast)
    output = StringIO()
    if result.ok:
        output.write("Semantic Analysis Successful\n")
    else:
        output.write("Semantic Analysis Failed\n")

    for warning in result.warnings:
        output.write(f"{warning}\n")
    for error in result.errors:
        output.write(f"{error}\n")

    output.write("\n")
    output.write(format_symbol_table(result.symbols))

    if not result.ok:
        raise SystemExit(1)

    return output.getvalue()


def run_icg(source: str, plain: bool = False) -> str:
    instructions = compile_source_to_tac(source)
    return format_instructions(instructions, include_numbers=not plain)


def run_optimize(text: str, force_source: bool = False, show_before_after: bool = False) -> str:
    original = read_tac_or_source(text, force_source)
    optimized, report = optimize_instructions(original)
    output = StringIO()
    output.write(report.format())
    output.write("\n\n")
    if show_before_after:
        output.write("Original TAC\n")
        output.write(format_instructions(original))
        output.write("\n\nOptimized TAC\n")
    output.write(format_instructions(optimized))
    return output.getvalue()


def run_codegen(text: str, force_source: bool = False) -> str:
    if force_source:
        instructions = optimize_instructions(compile_source_to_tac(text))[0]
    else:
        try:
            instructions = optimize_instructions(parse_instructions(text))[0]
        except ICGError:
            instructions = optimize_instructions(compile_source_to_tac(text))[0]

    return generate_target_code(instructions)


def run_all(source: str, plain: bool = False, show_before_after: bool = False) -> str:
    output = StringIO()
    output.write("=== Phase 1: Lexical Analysis ===\n")
    output.write(run_lexical(source))
    output.write("\n\n=== Phase 2: Syntax Analysis ===\n")
    output.write(run_syntax(source))
    output.write("\n\n=== Phase 3: Semantic Analysis ===\n")
    try:
        output.write(run_semantic(source))
    except SystemExit as exc:
        raise RuntimeError("Semantic analysis failed") from exc
    output.write("\n=== Phase 4: Intermediate Code Generation ===\n")
    instructions = compile_source_to_tac(source)
    output.write(format_instructions(instructions, include_numbers=not plain))
    output.write("\n\n=== Phase 5: Optimization ===\n")
    optimized, report = optimize_instructions(instructions)
    output.write(report.format())
    output.write("\n\n")
    if show_before_after:
        output.write("Original TAC\n")
        output.write(format_instructions(instructions))
        output.write("\n\nOptimized TAC\n")
    output.write(format_instructions(optimized))
    output.write("\n\n=== Phase 6: Target Code Generation ===\n")
    output.write(generate_target_code(optimized))
    return output.getvalue()


class CompilerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/compile":
            self.handle_compile()
        else:
            self.send_error(404, "Not Found")

    def handle_compile(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode("utf-8"))
        except Exception as exc:
            self.send_json({"success": False, "error": f"Invalid request body: {exc}"}, status=400)
            return

        source = request_data.get("source", "")
        phase = request_data.get("phase", "all").lower()
        plain = bool(request_data.get("plain", False))
        show_before_after = bool(request_data.get("showBeforeAfter", False))
        from_source = bool(request_data.get("fromSource", False))

        try:
            if phase in {"1", "lexical"}:
                output = run_lexical(source)
            elif phase in {"2", "syntax"}:
                output = run_syntax(source)
            elif phase in {"3", "semantic"}:
                output = run_semantic(source)
            elif phase in {"4", "icg"}:
                output = run_icg(source, plain=plain)
            elif phase in {"5", "optimize"}:
                output = run_optimize(source, force_source=from_source, show_before_after=show_before_after)
            elif phase in {"6", "codegen"}:
                output = run_codegen(source, force_source=from_source)
            else:
                output = run_all(source, plain=plain, show_before_after=show_before_after)

            self.send_json({"success": True, "output": output})
        except (LexerError, ParseError, ICGError, CodeGenerationError, RuntimeError, SystemExit) as exc:
            self.send_json({"success": False, "error": str(exc)}, status=400)
        except Exception as exc:
            self.send_json({"success": False, "error": f"Unexpected error: {exc}"}, status=500)

    def send_json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data, indent=2)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(payload.encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    server_address = (DEFAULT_HOST, DEFAULT_PORT)
    with ThreadingHTTPServer(server_address, CompilerHandler) as httpd:
        print(f"Lumina Web Frontend running at http://{DEFAULT_HOST}:{DEFAULT_PORT}")
        print("Open the URL in your browser and paste Lumina source code to run compiler phases.")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
