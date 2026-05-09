from __future__ import annotations

from typing import List

from .ast_nodes import (
    Assignment,
    BinaryExpression,
    Block,
    IfStatement,
    Literal,
    PrintStatement,
    Program,
    UnaryExpression,
    VarDecl,
    VariableReference,
    WhileStatement,
)
from .lexer import Token, tokenize_source


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        lexeme = token.lexeme if token.lexeme else "<EOF>"
        super().__init__(
            f"Syntax Error at line {token.line}, column {token.column}: {message} near {lexeme!r}"
        )
        self.message = message
        self.token = token


class Parser:
    TYPE_KEYWORDS = {"int", "float", "char", "bool"}

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        statements = []
        while not self._is_at_end():
            statements.append(self._statement())
        first = self.tokens[0] if self.tokens else Token("EOF", "", 1, 1)
        return Program(line=first.line, column=first.column, statements=statements)

    def _statement(self):
        if self._match_keyword(*self.TYPE_KEYWORDS):
            return self._var_declaration(self._previous())
        if self._match_keyword("if"):
            return self._if_statement(self._previous())
        if self._match_keyword("while"):
            return self._while_statement(self._previous())
        if self._match_keyword("print"):
            return self._print_statement(self._previous())
        if self._match_delimiter("{"):
            return self._block_after_open(self._previous())
        if self._check("IDENTIFIER") and self._check_next("OPERATOR", "="):
            return self._assignment()

        raise ParseError("Expected a declaration, assignment, if, while, print, or block", self._peek())

    def _var_declaration(self, type_token: Token) -> VarDecl:
        name = self._consume("IDENTIFIER", "Expected variable name after type")
        initializer = None
        if self._match_operator("="):
            initializer = self._expression()
        self._consume_delimiter(";", "Expected ';' after variable declaration")
        return VarDecl(
            line=type_token.line,
            column=type_token.column,
            var_type=type_token.lexeme,
            name=name.lexeme,
            initializer=initializer,
        )

    def _assignment(self) -> Assignment:
        name = self._consume("IDENTIFIER", "Expected assignment target")
        self._consume_operator("=", "Expected '=' in assignment")
        expression = self._expression()
        self._consume_delimiter(";", "Expected ';' after assignment")
        return Assignment(line=name.line, column=name.column, name=name.lexeme, expression=expression)

    def _if_statement(self, if_token: Token) -> IfStatement:
        self._consume_delimiter("(", "Expected '(' after if")
        condition = self._expression()
        self._consume_delimiter(")", "Expected ')' after if condition")
        then_block = self._required_block("Expected block after if condition")
        else_block = None
        if self._match_keyword("else"):
            else_block = self._required_block("Expected block after else")
        return IfStatement(
            line=if_token.line,
            column=if_token.column,
            condition=condition,
            then_block=then_block,
            else_block=else_block,
        )

    def _while_statement(self, while_token: Token) -> WhileStatement:
        self._consume_delimiter("(", "Expected '(' after while")
        condition = self._expression()
        self._consume_delimiter(")", "Expected ')' after while condition")
        body = self._required_block("Expected block after while condition")
        return WhileStatement(line=while_token.line, column=while_token.column, condition=condition, body=body)

    def _print_statement(self, print_token: Token) -> PrintStatement:
        self._consume_delimiter("(", "Expected '(' after print")
        expression = self._expression()
        self._consume_delimiter(")", "Expected ')' after print expression")
        self._consume_delimiter(";", "Expected ';' after print statement")
        return PrintStatement(line=print_token.line, column=print_token.column, expression=expression)

    def _required_block(self, message: str) -> Block:
        if not self._match_delimiter("{"):
            raise ParseError(message, self._peek())
        return self._block_after_open(self._previous())

    def _block_after_open(self, open_brace: Token) -> Block:
        statements = []
        while not self._check("EOF") and not self._check("DELIMITER", "}"):
            statements.append(self._statement())
        self._consume_delimiter("}", "Expected '}' to close block")
        return Block(line=open_brace.line, column=open_brace.column, statements=statements)

    def _expression(self):
        return self._logical_or()

    def _logical_or(self):
        expression = self._logical_and()
        while self._match_operator("||"):
            operator = self._previous()
            right = self._logical_and()
            expression = BinaryExpression(
                line=operator.line,
                column=operator.column,
                operator=operator.lexeme,
                left=expression,
                right=right,
            )
        return expression

    def _logical_and(self):
        expression = self._equality()
        while self._match_operator("&&"):
            operator = self._previous()
            right = self._equality()
            expression = BinaryExpression(
                line=operator.line,
                column=operator.column,
                operator=operator.lexeme,
                left=expression,
                right=right,
            )
        return expression

    def _equality(self):
        expression = self._comparison()
        while self._match_operator("==", "!="):
            operator = self._previous()
            right = self._comparison()
            expression = BinaryExpression(
                line=operator.line,
                column=operator.column,
                operator=operator.lexeme,
                left=expression,
                right=right,
            )
        return expression

    def _comparison(self):
        expression = self._term()
        while self._match_operator("<", "<=", ">", ">="):
            operator = self._previous()
            right = self._term()
            expression = BinaryExpression(
                line=operator.line,
                column=operator.column,
                operator=operator.lexeme,
                left=expression,
                right=right,
            )
        return expression

    def _term(self):
        expression = self._factor()
        while self._match_operator("+", "-"):
            operator = self._previous()
            right = self._factor()
            expression = BinaryExpression(
                line=operator.line,
                column=operator.column,
                operator=operator.lexeme,
                left=expression,
                right=right,
            )
        return expression

    def _factor(self):
        expression = self._unary()
        while self._match_operator("*", "/", "%"):
            operator = self._previous()
            right = self._unary()
            expression = BinaryExpression(
                line=operator.line,
                column=operator.column,
                operator=operator.lexeme,
                left=expression,
                right=right,
            )
        return expression

    def _unary(self):
        if self._match_operator("!", "-"):
            operator = self._previous()
            operand = self._unary()
            return UnaryExpression(line=operator.line, column=operator.column, operator=operator.lexeme, operand=operand)
        return self._primary()

    def _primary(self):
        if self._match("INT_LITERAL"):
            token = self._previous()
            return Literal(line=token.line, column=token.column, value=token.literal, literal_type="int")
        if self._match("FLOAT_LITERAL"):
            token = self._previous()
            return Literal(line=token.line, column=token.column, value=token.literal, literal_type="float")
        if self._match("CHAR_LITERAL"):
            token = self._previous()
            return Literal(line=token.line, column=token.column, value=token.literal, literal_type="char")
        if self._match("BOOL_LITERAL"):
            token = self._previous()
            return Literal(line=token.line, column=token.column, value=token.literal, literal_type="bool")
        if self._match("IDENTIFIER"):
            token = self._previous()
            return VariableReference(line=token.line, column=token.column, name=token.lexeme)
        if self._match_delimiter("("):
            expression = self._expression()
            self._consume_delimiter(")", "Expected ')' after expression")
            return expression
        raise ParseError("Expected expression", self._peek())

    def _match(self, token_type: str, lexeme: str | None = None) -> bool:
        if self._check(token_type, lexeme):
            self._advance()
            return True
        return False

    def _match_keyword(self, *keywords: str) -> bool:
        if self._check("KEYWORD") and self._peek().lexeme in keywords:
            self._advance()
            return True
        return False

    def _match_operator(self, *operators: str) -> bool:
        if self._check("OPERATOR") and self._peek().lexeme in operators:
            self._advance()
            return True
        return False

    def _match_delimiter(self, delimiter: str) -> bool:
        return self._match("DELIMITER", delimiter)

    def _consume(self, token_type: str, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise ParseError(message, self._peek())

    def _consume_operator(self, operator: str, message: str) -> Token:
        if self._check("OPERATOR", operator):
            return self._advance()
        raise ParseError(message, self._peek())

    def _consume_delimiter(self, delimiter: str, message: str) -> Token:
        if self._check("DELIMITER", delimiter):
            return self._advance()
        raise ParseError(message, self._peek())

    def _check(self, token_type: str, lexeme: str | None = None) -> bool:
        if self._is_at_end() and token_type != "EOF":
            return False
        token = self._peek()
        if token.type != token_type:
            return False
        return lexeme is None or token.lexeme == lexeme

    def _check_next(self, token_type: str, lexeme: str | None = None) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        token = self.tokens[self.current + 1]
        if token.type != token_type:
            return False
        return lexeme is None or token.lexeme == lexeme

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == "EOF"

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]


def parse_source(source: str) -> Program:
    return Parser(tokenize_source(source)).parse()

