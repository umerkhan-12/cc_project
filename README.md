# Lumina Compiler Construction Project

Lumina is a complete academic compiler project for a small custom programming language. It implements lexical analysis, syntax analysis, semantic analysis, intermediate code generation, optimization, and target code generation with independent command-line scripts for every phase.

The implementation is original, file-based, deterministic, and written in plain Python with no external dependencies.

## Folder Structure

```text
cc_project/
├── Phase1_Lexical/
├── Phase2_Syntax/
├── Phase3_Semantic/
├── Phase4_ICG/
├── Phase5_Optimization/
├── Phase6_CodeGeneration/
├── TestCases/
├── Documentation/
├── compiler_core/
├── README.md
└── run_lumina.py
```

`compiler_core/` contains shared implementation code. The six phase folders contain independent executable scripts.

## Language Features

Lumina supports:

- variable declarations using `int`, `float`, `char`, and `bool`
- assignment statements
- arithmetic and relational expressions
- logical expressions
- `if` / `else` statements
- `while` loops
- `print(...)` output statements
- nested blocks and lexical scoping
- single-line and block comments

Example:

```c
int i = 0;
int sum = 0;

while (i < 5) {
    sum = sum + i;
    i = i + 1;
}

if (sum >= 10) {
    print(sum);
} else {
    print(0);
}
```

The full grammar is documented in [Documentation/Grammar.md](Documentation/Grammar.md).

## Requirements

- Python 3.10 or newer is recommended.
- No third-party packages are required.

## How to Run Each Phase

Run commands from inside the project root directory.

### Phase 1: Lexical Analysis

```bash
python Phase1_Lexical/lexer.py TestCases/valid_basic.lum
```

Produces a token table with token type, lexeme, line, column, and literal value.

### Phase 2: Syntax Analysis

```bash
python Phase2_Syntax/parser.py TestCases/valid_basic.lum
```

Builds and prints an AST using the real grammar.

### Phase 3: Semantic Analysis

```bash
python Phase3_Semantic/semantic.py TestCases/valid_nested_scope.lum
```

Performs type checking, declaration checking, scope checking, and prints the symbol table.

### Phase 4: Intermediate Code Generation

```bash
python Phase4_ICG/icg.py TestCases/valid_loop_if.lum
```

Generates three-address code with temporaries and labels.

To generate plain TAC for the optimizer:

```bash
python Phase4_ICG/icg.py TestCases/valid_loop_if.lum --plain > loop.tac
```

### Phase 5: Optimization

```bash
python Phase5_Optimization/optimize.py TestCases/optimization_input.tac --show-before-after
```

The optimizer reads TAC and applies constant folding, constant propagation, copy propagation, dead code elimination, and peephole branch simplification.

It can also compile source to TAC internally:

```bash
python Phase5_Optimization/optimize.py TestCases/optimization_demo.lum --from-source
```

### Phase 6: Target Code Generation

```bash
python Phase6_CodeGeneration/codegen.py TestCases/optimization_input.tac
```

Generates readable stack-machine target code. TAC input is optimized before target code is emitted, so the output corresponds to optimized intermediate code.

From a source file:

```bash
python Phase6_CodeGeneration/codegen.py TestCases/valid_basic.lum --from-source
```

### Unified Runner

A convenient root entrypoint is `run_lumina.py`. Run all compiler phases sequentially from source with:

```bash
python run_lumina.py --all TestCases/valid_basic.lum
```

Run a single phase by number or name:

```bash
python run_lumina.py --phase 4 TestCases/valid_loop_if.lum --plain
python run_lumina.py --phase optimize TestCases/optimization_input.tac --show-before-after
python run_lumina.py --phase codegen TestCases/valid_basic.lum --from-source
```

## Error Handling Demonstrations

Lexical error:

```bash
python Phase1_Lexical/lexer.py TestCases/lexical_error.lum
```

Syntax error:

```bash
python Phase2_Syntax/parser.py TestCases/syntax_error.lum
```

Semantic errors:

```bash
python Phase3_Semantic/semantic.py TestCases/semantic_error.lum
```

## Intermediate Representation

The compiler uses three-address code. Example:

```text
t1 = i < 5
IF_FALSE t1 GOTO L2
t2 = sum + i
sum = t2
GOTO L1
```

The optimizer reads this TAC format directly.

## Target Machine

The final target is a simple stack machine:

- `PUSH value` pushes a constant.
- `LOAD name` pushes a variable value.
- `STORE name` pops and stores a value.
- `ADD`, `SUB`, `MUL`, `DIV`, `MOD` compute arithmetic.
- `LT`, `LE`, `GT`, `GE`, `EQ`, `NE` compute comparisons.
- `AND`, `OR`, `NOT` compute boolean logic.
- `JMP label` and `JZ label` control flow.
- `PRINT` outputs the top of stack.

## Test Cases

- `valid_basic.lum`: declarations, expressions, conditionals, output

## Web Frontend

A simple browser-based frontend is available from the project root. Start the server with:

```bash
python web_frontend/app.py
```

Then open `http://127.0.0.1:8000` in your browser.

The frontend lets you paste Lumina source code, choose a compiler phase, and see the results live in the browser.

- `valid_loop_if.lum`: while loop and if/else
- `valid_nested_scope.lum`: nested block scopes and shadowing
- `optimization_demo.lum`: source-level optimization opportunities
- `optimization_input.tac`: TAC-level optimization input
- `lexical_error.lum`: illegal character
- `syntax_error.lum`: missing semicolon
- `semantic_error.lum`: redeclaration, undeclared variable, invalid type use

## Academic Notes

This project intentionally keeps the language small so each compiler phase can be understood and defended in viva. The implementation still performs real processing in every phase: tokenization, AST construction, symbol table management, type checking, TAC generation, optimization, and target code generation.
