from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .ast_nodes import (
    Assignment,
    BinaryExpression,
    Block,
    IfStatement,
    Literal,
    Node,
    PrintStatement,
    Program,
    UnaryExpression,
    VarDecl,
    VariableReference,
    WhileStatement,
)


@dataclass
class Symbol:
    name: str
    data_type: str
    scope_id: int
    scope_name: str
    scope_level: int
    declared_line: int
    initialized: bool = False
    used: bool = False


@dataclass
class Scope:
    scope_id: int
    name: str
    level: int
    symbols: Dict[str, Symbol]


@dataclass
class SemanticResult:
    symbols: List[Symbol]
    errors: List[str]
    warnings: List[str]

    @property
    def ok(self) -> bool:
        return not self.errors


class SymbolTable:
    def __init__(self):
        self.scopes: List[Scope] = [Scope(0, "global", 0, {})]
        self.all_symbols: List[Symbol] = []
        self.next_scope_id = 1

    @property
    def current_scope(self) -> Scope:
        return self.scopes[-1]

    def enter_scope(self, prefix: str = "block") -> None:
        scope_id = self.next_scope_id
        self.next_scope_id += 1
        self.scopes.append(Scope(scope_id, f"{prefix}_{scope_id}", len(self.scopes), {}))

    def exit_scope(self) -> None:
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name: str, data_type: str, line: int, initialized: bool) -> Optional[str]:
        scope = self.current_scope
        if name in scope.symbols:
            previous = scope.symbols[name]
            return (
                f"Semantic Error at line {line}: variable {name!r} is already declared "
                f"in scope {scope.name} at line {previous.declared_line}"
            )

        symbol = Symbol(
            name=name,
            data_type=data_type,
            scope_id=scope.scope_id,
            scope_name=scope.name,
            scope_level=scope.level,
            declared_line=line,
            initialized=initialized,
        )
        scope.symbols[name] = symbol
        self.all_symbols.append(symbol)
        return None

    def lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self.scopes):
            if name in scope.symbols:
                return scope.symbols[name]
        return None


class SemanticAnalyzer:
    NUMERIC_TYPES = {"int", "float"}

    def __init__(self):
        self.table = SymbolTable()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def analyze(self, program: Program) -> SemanticResult:
        self._visit_program(program)
        return SemanticResult(self.table.all_symbols, self.errors, self.warnings)

    def _visit_program(self, program: Program) -> None:
        for statement in program.statements:
            self._visit_statement(statement)

    def _visit_block(self, block: Block, scope_prefix: str = "block") -> None:
        self.table.enter_scope(scope_prefix)
        for statement in block.statements:
            self._visit_statement(statement)
        self.table.exit_scope()

    def _visit_statement(self, statement: Node) -> None:
        if isinstance(statement, VarDecl):
            self._visit_var_decl(statement)
        elif isinstance(statement, Assignment):
            self._visit_assignment(statement)
        elif isinstance(statement, IfStatement):
            self._visit_if(statement)
        elif isinstance(statement, WhileStatement):
            self._visit_while(statement)
        elif isinstance(statement, PrintStatement):
            self._infer_expression(statement.expression)
        elif isinstance(statement, Block):
            self._visit_block(statement)

    def _visit_var_decl(self, node: VarDecl) -> None:
        initializer_type = None
        if node.initializer is not None:
            initializer_type = self._infer_expression(node.initializer)
            if not self._is_assignable(node.var_type, initializer_type):
                self.errors.append(
                    f"Semantic Error at line {node.line}: cannot initialize {node.name!r} "
                    f"of type {node.var_type} with expression of type {initializer_type}"
                )

        error = self.table.declare(
            node.name,
            node.var_type,
            node.line,
            initialized=node.initializer is not None and self._is_assignable(node.var_type, initializer_type),
        )
        if error:
            self.errors.append(error)

    def _visit_assignment(self, node: Assignment) -> None:
        symbol = self.table.lookup(node.name)
        expression_type = self._infer_expression(node.expression)
        if symbol is None:
            self.errors.append(f"Semantic Error at line {node.line}: variable {node.name!r} is not declared")
            return

        if not self._is_assignable(symbol.data_type, expression_type):
            self.errors.append(
                f"Semantic Error at line {node.line}: cannot assign expression of type "
                f"{expression_type} to variable {node.name!r} of type {symbol.data_type}"
            )
            return

        symbol.initialized = True

    def _visit_if(self, node: IfStatement) -> None:
        condition_type = self._infer_expression(node.condition)
        if condition_type != "bool" and condition_type != "error":
            self.errors.append(f"Semantic Error at line {node.line}: if condition must be bool, got {condition_type}")
        self._visit_block(node.then_block, "if")
        if node.else_block is not None:
            self._visit_block(node.else_block, "else")

    def _visit_while(self, node: WhileStatement) -> None:
        condition_type = self._infer_expression(node.condition)
        if condition_type != "bool" and condition_type != "error":
            self.errors.append(f"Semantic Error at line {node.line}: while condition must be bool, got {condition_type}")
        self._visit_block(node.body, "while")

    def _infer_expression(self, node: Node) -> str:
        if isinstance(node, Literal):
            return node.literal_type

        if isinstance(node, VariableReference):
            symbol = self.table.lookup(node.name)
            if symbol is None:
                self.errors.append(f"Semantic Error at line {node.line}: variable {node.name!r} is not declared")
                return "error"
            symbol.used = True
            if not symbol.initialized:
                self.warnings.append(
                    f"Semantic Warning at line {node.line}: variable {node.name!r} may be used before initialization"
                )
            return symbol.data_type

        if isinstance(node, UnaryExpression):
            operand_type = self._infer_expression(node.operand)
            if operand_type == "error":
                return "error"
            if node.operator == "-" and operand_type in self.NUMERIC_TYPES:
                return operand_type
            if node.operator == "!" and operand_type == "bool":
                return "bool"
            self.errors.append(
                f"Semantic Error at line {node.line}: operator {node.operator!r} cannot be applied to {operand_type}"
            )
            return "error"

        if isinstance(node, BinaryExpression):
            left_type = self._infer_expression(node.left)
            right_type = self._infer_expression(node.right)
            if "error" in {left_type, right_type}:
                return "error"
            return self._infer_binary(node, left_type, right_type)

        self.errors.append(f"Semantic Error at line {node.line}: unsupported expression node {node.__class__.__name__}")
        return "error"

    def _infer_binary(self, node: BinaryExpression, left_type: str, right_type: str) -> str:
        operator = node.operator

        if operator in {"+", "-", "*", "/"}:
            if left_type in self.NUMERIC_TYPES and right_type in self.NUMERIC_TYPES:
                return "float" if "float" in {left_type, right_type} else "int"
            self.errors.append(
                f"Semantic Error at line {node.line}: arithmetic operator {operator!r} requires numeric operands"
            )
            return "error"

        if operator == "%":
            if left_type == "int" and right_type == "int":
                return "int"
            self.errors.append("Semantic Error at line " f"{node.line}: modulo operator requires int operands")
            return "error"

        if operator in {"<", "<=", ">", ">="}:
            if left_type in self.NUMERIC_TYPES and right_type in self.NUMERIC_TYPES:
                return "bool"
            self.errors.append(
                f"Semantic Error at line {node.line}: relational operator {operator!r} requires numeric operands"
            )
            return "error"

        if operator in {"==", "!="}:
            if left_type == right_type or (left_type in self.NUMERIC_TYPES and right_type in self.NUMERIC_TYPES):
                return "bool"
            self.errors.append(
                f"Semantic Error at line {node.line}: equality operator {operator!r} compares incompatible "
                f"types {left_type} and {right_type}"
            )
            return "error"

        if operator in {"&&", "||"}:
            if left_type == "bool" and right_type == "bool":
                return "bool"
            self.errors.append(
                f"Semantic Error at line {node.line}: logical operator {operator!r} requires bool operands"
            )
            return "error"

        self.errors.append(f"Semantic Error at line {node.line}: unknown operator {operator!r}")
        return "error"

    def _is_assignable(self, target_type: str, source_type: Optional[str]) -> bool:
        if source_type is None or source_type == "error":
            return False
        if target_type == source_type:
            return True
        return target_type == "float" and source_type == "int"


def analyze_program(program: Program) -> SemanticResult:
    return SemanticAnalyzer().analyze(program)


def format_symbol_table(symbols: List[Symbol]) -> str:
    if not symbols:
        return "Symbol table is empty."

    rows = [("SCOPE", "LEVEL", "NAME", "TYPE", "INIT", "USED", "DECLARED_LINE")]
    for symbol in symbols:
        rows.append(
            (
                symbol.scope_name,
                str(symbol.scope_level),
                symbol.name,
                symbol.data_type,
                "yes" if symbol.initialized else "no",
                "yes" if symbol.used else "no",
                str(symbol.declared_line),
            )
        )

    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines = []
    for index, row in enumerate(rows):
        lines.append("  ".join(row[i].ljust(widths[i]) for i in range(len(row))))
        if index == 0:
            lines.append("  ".join("-" * width for width in widths))
    return "\n".join(lines)

