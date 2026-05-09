# Sample Outputs

These samples show the expected style of output. Exact temporary names may vary only if the implementation is changed.

## Lexical Analysis

```text
Lexical Analysis Successful
TYPE         LEXEME  LINE  COLUMN  LITERAL
-----------  ------  ----  ------  -------
KEYWORD      int     2     1
IDENTIFIER   count   2     5
OPERATOR     =       2     11
INT_LITERAL  3       2     13      3
DELIMITER    ;       2     14
...
EOF          <EOF>   14    1
```

## Syntax Error

```text
Syntax Error at line 2, column 1: Expected ';' after variable declaration near 'if'
```

## Semantic Symbol Table

```text
Semantic Analysis Successful

SCOPE     LEVEL  NAME   TYPE   INIT  USED  DECLARED_LINE
--------  -----  -----  -----  ----  ----  -------------
global    0      value  int    yes   yes   1
global    0      show   bool   yes   yes   2
if_1      1      value  int    yes   yes   5
block_2   2      value  float  yes   yes   9
```

## Intermediate Code

```text
Intermediate Code Generation Successful
001: i = 0
002: sum = 0
003: LABEL L1
004: t1 = i < 5
005: IF_FALSE t1 GOTO L2
006: t2 = sum + i
007: sum = t2
008: t3 = i + 1
009: i = t3
010: GOTO L1
011: LABEL L2
```

## Optimizer

```text
Optimization Summary
- Constant Folding: 4 change(s)
- Constant Propagation: 8 change(s)
- Copy Propagation: 2 change(s)
- Dead Code Elimination: 4 change(s)
- Peephole Branch Simplification: 1 change(s)
```

## Target Code

```text
; Lumina stack-machine target code
; Instructions: PUSH/LOAD/STORE, arithmetic ops, jumps, and PRINT
    PUSH 14
    STORE a
    PUSH 14
    STORE b
    PUSH 14
    STORE c
    LOAD c
    PRINT
```

