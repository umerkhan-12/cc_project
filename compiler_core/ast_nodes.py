from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Node:
    line: int
    column: int


@dataclass
class Program(Node):
    statements: List[Node]


@dataclass
class Block(Node):
    statements: List[Node]


@dataclass
class VarDecl(Node):
    var_type: str
    name: str
    initializer: Optional[Node]


@dataclass
class Assignment(Node):
    name: str
    expression: Node


@dataclass
class IfStatement(Node):
    condition: Node
    then_block: Block
    else_block: Optional[Block]


@dataclass
class WhileStatement(Node):
    condition: Node
    body: Block


@dataclass
class PrintStatement(Node):
    expression: Node


@dataclass
class BinaryExpression(Node):
    operator: str
    left: Node
    right: Node


@dataclass
class UnaryExpression(Node):
    operator: str
    operand: Node


@dataclass
class Literal(Node):
    value: Any
    literal_type: str


@dataclass
class VariableReference(Node):
    name: str


def format_ast(node: Node, indent: int = 0) -> str:
    """Return a readable tree representation for parser output."""
    pad = "  " * indent

    if isinstance(node, Program):
        lines = [f"{pad}Program"]
        for statement in node.statements:
            lines.append(format_ast(statement, indent + 1))
        return "\n".join(lines)

    if isinstance(node, Block):
        lines = [f"{pad}Block"]
        for statement in node.statements:
            lines.append(format_ast(statement, indent + 1))
        return "\n".join(lines)

    if isinstance(node, VarDecl):
        lines = [f"{pad}VarDecl type={node.var_type} name={node.name}"]
        if node.initializer is not None:
            lines.append(f"{pad}  Initializer")
            lines.append(format_ast(node.initializer, indent + 2))
        return "\n".join(lines)

    if isinstance(node, Assignment):
        return "\n".join(
            [
                f"{pad}Assignment name={node.name}",
                format_ast(node.expression, indent + 1),
            ]
        )

    if isinstance(node, IfStatement):
        lines = [f"{pad}IfStatement", f"{pad}  Condition"]
        lines.append(format_ast(node.condition, indent + 2))
        lines.append(f"{pad}  Then")
        lines.append(format_ast(node.then_block, indent + 2))
        if node.else_block is not None:
            lines.append(f"{pad}  Else")
            lines.append(format_ast(node.else_block, indent + 2))
        return "\n".join(lines)

    if isinstance(node, WhileStatement):
        return "\n".join(
            [
                f"{pad}WhileStatement",
                f"{pad}  Condition",
                format_ast(node.condition, indent + 2),
                f"{pad}  Body",
                format_ast(node.body, indent + 2),
            ]
        )

    if isinstance(node, PrintStatement):
        return "\n".join(
            [
                f"{pad}PrintStatement",
                format_ast(node.expression, indent + 1),
            ]
        )

    if isinstance(node, BinaryExpression):
        return "\n".join(
            [
                f"{pad}BinaryExpression operator={node.operator}",
                format_ast(node.left, indent + 1),
                format_ast(node.right, indent + 1),
            ]
        )

    if isinstance(node, UnaryExpression):
        return "\n".join(
            [
                f"{pad}UnaryExpression operator={node.operator}",
                format_ast(node.operand, indent + 1),
            ]
        )

    if isinstance(node, Literal):
        return f"{pad}Literal type={node.literal_type} value={node.value!r}"

    if isinstance(node, VariableReference):
        return f"{pad}VariableReference name={node.name}"

    return f"{pad}{node.__class__.__name__}"

