# Lumina Language Grammar

Lumina is a small block-structured teaching language designed for this compiler project. Programs are plain text files, usually saved with the `.lum` extension.

## Lexical Elements

- Identifiers: start with a letter or `_`, followed by letters, digits, or `_`.
- Keywords: `int`, `float`, `char`, `bool`, `if`, `else`, `while`, `print`, `true`, `false`.
- Literals: integer, floating-point, character, and boolean literals.
- Comments: `// single-line` and `/* block comments */`.
- Operators: `+`, `-`, `*`, `/`, `%`, `=`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `&&`, `||`, `!`.
- Delimiters: `;`, `,`, `(`, `)`, `{`, `}`.

## Context-Free Grammar

```ebnf
program         -> statement* EOF ;

statement       -> variable_decl
                 | assignment
                 | if_statement
                 | while_statement
                 | print_statement
                 | block ;

variable_decl   -> type IDENTIFIER ( "=" expression )? ";" ;
type            -> "int" | "float" | "char" | "bool" ;

assignment      -> IDENTIFIER "=" expression ";" ;
if_statement    -> "if" "(" expression ")" block ( "else" block )? ;
while_statement -> "while" "(" expression ")" block ;
print_statement -> "print" "(" expression ")" ";" ;
block           -> "{" statement* "}" ;

expression      -> logical_or ;
logical_or      -> logical_and ( "||" logical_and )* ;
logical_and     -> equality ( "&&" equality )* ;
equality        -> comparison ( ( "==" | "!=" ) comparison )* ;
comparison      -> term ( ( "<" | "<=" | ">" | ">=" ) term )* ;
term            -> factor ( ( "+" | "-" ) factor )* ;
factor          -> unary ( ( "*" | "/" | "%" ) unary )* ;
unary           -> ( "!" | "-" ) unary | primary ;
primary         -> INT_LITERAL
                 | FLOAT_LITERAL
                 | CHAR_LITERAL
                 | BOOL_LITERAL
                 | IDENTIFIER
                 | "(" expression ")" ;
```

## Scope Rules

- The global program body is scope level `0`.
- Every `{ ... }` block creates a new nested scope.
- A variable may not be redeclared in the same scope.
- A variable may shadow another variable from an outer scope.
- Uses resolve to the nearest enclosing declaration.

## Type Rules

- `int` and `float` support arithmetic operators.
- `%` requires two `int` operands.
- Relational operators compare numeric values and produce `bool`.
- `==` and `!=` compare equal types, or compatible numeric values.
- `&&`, `||`, and `!` require `bool` operands.
- Assignment requires matching types, except `int` may be assigned to `float`.

