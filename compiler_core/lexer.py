from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass(frozen=True)
class Token:
    type: str
    lexeme: str
    line: int
    column: int
    literal: Optional[Any] = None

    def display_literal(self) -> str:
        if self.literal is None:
            return ""
        return repr(self.literal)


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Lexical Error at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    KEYWORDS = {"int", "float", "char", "bool", "if", "else", "while", "print"}
    BOOLEAN_LITERALS = {"true": True, "false": False}
    DELIMITERS = {";", ",", "(", ")", "{", "}"}
    SINGLE_OPERATORS = {"+", "-", "*", "/", "%", "=", "<", ">", "!"}
    MULTI_OPERATORS = {"==", "!=", "<=", ">=", "&&", "||"}
    VALID_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "'": "'", "\\": "\\", "0": "\0"}

    def __init__(self, source: str):
        self.source = source
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()

        self.tokens.append(Token("EOF", "", self.line, self.column))
        return self.tokens

    def _scan_token(self) -> None:
        c = self._advance()

        if c in {" ", "\r", "\t"}:
            return
        if c == "\n":
            return

        if c == "/" and self._match("/"):
            self._skip_single_line_comment()
            return

        if c == "/" and self._match("*"):
            self._skip_block_comment()
            return

        if c.isalpha() or c == "_":
            self._identifier()
            return

        if c.isdigit():
            self._number()
            return

        if c == "'":
            self._char_literal()
            return

        two_char = c + self._peek()
        if two_char in self.MULTI_OPERATORS:
            self._advance()
            self._add_token("OPERATOR", two_char)
            return

        if c in self.SINGLE_OPERATORS:
            self._add_token("OPERATOR", c)
            return

        if c in self.DELIMITERS:
            self._add_token("DELIMITER", c)
            return

        raise LexerError(f"Unexpected character {c!r}", self.line, self._token_column())

    def _identifier(self) -> None:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        text = self.source[self.start : self.current]
        if text in self.BOOLEAN_LITERALS:
            self._add_token("BOOL_LITERAL", text, self.BOOLEAN_LITERALS[text])
        elif text in self.KEYWORDS:
            self._add_token("KEYWORD", text)
        else:
            self._add_token("IDENTIFIER", text)

    def _number(self) -> None:
        while self._peek().isdigit():
            self._advance()

        is_float = False
        if self._peek() == "." and self._peek_next().isdigit():
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()

        if self._peek().isalpha() or self._peek() == "_":
            while self._peek().isalnum() or self._peek() == "_":
                self._advance()
            text = self.source[self.start : self.current]
            raise LexerError(f"Invalid numeric literal {text!r}", self.line, self._token_column())

        text = self.source[self.start : self.current]
        if is_float:
            self._add_token("FLOAT_LITERAL", text, float(text))
        else:
            self._add_token("INT_LITERAL", text, int(text))

    def _char_literal(self) -> None:
        start_line = self.line
        start_column = self._token_column()

        if self._is_at_end() or self._peek() == "\n":
            raise LexerError("Unterminated character literal", start_line, start_column)

        if self._peek() == "\\":
            self._advance()
            escape = self._advance()
            if escape not in self.VALID_ESCAPES:
                raise LexerError(f"Invalid escape sequence \\{escape}", start_line, start_column)
            value = self.VALID_ESCAPES[escape]
        else:
            value = self._advance()

        if self._peek() != "'":
            while not self._is_at_end() and self._peek() not in {"'", "\n"}:
                self._advance()
            if self._peek() == "'":
                self._advance()
            raise LexerError("Character literal must contain exactly one character", start_line, start_column)

        self._advance()
        text = self.source[self.start : self.current]
        self._add_token("CHAR_LITERAL", text, value)

    def _skip_single_line_comment(self) -> None:
        while self._peek() != "\n" and not self._is_at_end():
            self._advance()

    def _skip_block_comment(self) -> None:
        start_line = self.line
        start_column = self._token_column()
        while not self._is_at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                self._advance()
                self._advance()
                return
            self._advance()
        raise LexerError("Unterminated block comment", start_line, start_column)

    def _add_token(self, token_type: str, lexeme: str, literal: Optional[Any] = None) -> None:
        self.tokens.append(Token(token_type, lexeme, self.line, self._token_column(), literal))

    def _advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        if c == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return c

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self._advance()
        return True

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _token_column(self) -> int:
        return self.column - (self.current - self.start)


def tokenize_source(source: str) -> List[Token]:
    return Lexer(source).tokenize()


def format_tokens(tokens: List[Token]) -> str:
    rows = [("TYPE", "LEXEME", "LINE", "COLUMN", "LITERAL")]
    for token in tokens:
        rows.append(
            (
                token.type,
                token.lexeme if token.lexeme else "<EOF>",
                str(token.line),
                str(token.column),
                token.display_literal(),
            )
        )

    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines = []
    for index, row in enumerate(rows):
        line = "  ".join(row[i].ljust(widths[i]) for i in range(len(row)))
        lines.append(line)
        if index == 0:
            lines.append("  ".join("-" * width for width in widths))
    return "\n".join(lines)

