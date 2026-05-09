# Compiler Phase Explanation

## Phase 1: Lexical Analysis

The lexer reads a source file character by character and produces tokens. It recognizes keywords, identifiers, literals, operators, delimiters, and comments. Lexical errors include unexpected characters, invalid numeric literals, invalid character literals, and unterminated block comments.

Command:

```bash
python Phase1_Lexical/lexer.py TestCases/valid_basic.lum
```

## Phase 2: Syntax Analysis

The parser uses recursive descent parsing with operator precedence. It builds an AST containing declarations, assignments, blocks, conditionals, loops, print statements, and expressions. Syntax errors identify the line, column, expected construct, and nearby token.

Command:

```bash
python Phase2_Syntax/parser.py TestCases/valid_basic.lum
```

## Phase 3: Semantic Analysis

The semantic analyzer walks the AST and maintains a scoped symbol table. It checks declarations, redeclarations, undeclared variables, assignment compatibility, expression type validity, boolean conditions, initialization status, and usage.

Command:

```bash
python Phase3_Semantic/semantic.py TestCases/valid_nested_scope.lum
```

## Phase 4: Intermediate Code Generation

The ICG phase converts the validated AST to three-address code. Temporaries are generated for expression results, and labels are generated for control flow. Inner-scope variables are given deterministic storage names such as `value_s1` so shadowed variables do not collide. The TAC includes assignment, arithmetic, relational operations, conditional jumps, unconditional jumps, labels, and print.

Command:

```bash
python Phase4_ICG/icg.py TestCases/valid_loop_if.lum
```

To produce plain TAC suitable for a file:

```bash
python Phase4_ICG/icg.py TestCases/valid_loop_if.lum --plain
```

## Phase 5: Optimization

The optimizer reads TAC and applies genuine transformations:

- Constant folding evaluates constant expressions at compile time.
- Constant propagation replaces variables and temporaries known to hold constants.
- Copy propagation replaces simple aliases such as `b = a`.
- Dead code elimination removes unused temporary computations.
- Peephole branch simplification removes or rewrites branches with constant conditions.

Command:

```bash
python Phase5_Optimization/optimize.py TestCases/optimization_input.tac --show-before-after
```

The script also accepts a Lumina source file for convenience:

```bash
python Phase5_Optimization/optimize.py TestCases/optimization_demo.lum --from-source
```

## Phase 6: Target Code Generation

The target generator converts TAC to readable stack-machine instructions. It emits `PUSH`, `LOAD`, `STORE`, arithmetic operations, comparison operations, `JMP`, `JZ`, labels, and `PRINT`.

Command:

```bash
python Phase6_CodeGeneration/codegen.py TestCases/optimization_input.tac
```

From source, the code generation phase internally performs parsing, semantic analysis, ICG, and optimization before emitting target code:

```bash
python Phase6_CodeGeneration/codegen.py TestCases/valid_basic.lum --from-source
```
