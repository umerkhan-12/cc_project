from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

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
from .parser import parse_source
from .semantic import analyze_program


@dataclass
class Instruction:
    op: str
    result: Optional[str] = None
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    operator: Optional[str] = None

    def format(self) -> str:
        if self.op == "label":
            return f"LABEL {self.result}"
        if self.op == "goto":
            return f"GOTO {self.result}"
        if self.op == "if_false":
            return f"IF_FALSE {self.arg1} GOTO {self.result}"
        if self.op == "print":
            return f"PRINT {self.arg1}"
        if self.op == "assign":
            return f"{self.result} = {self.arg1}"
        if self.op == "binop":
            return f"{self.result} = {self.arg1} {self.operator} {self.arg2}"
        if self.op == "unary":
            return f"{self.result} = {self.operator} {self.arg1}"
        raise ValueError(f"Unknown instruction op {self.op!r}")


class ICGError(Exception):
    pass


class TACGenerator:
    def __init__(self):
        self.instructions: List[Instruction] = []
        self.temp_count = 0
        self.label_count = 0
        self.scope_count = 0
        self.scope_ids: List[int] = [0]
        self.scopes: List[dict[str, str]] = [{}]

    def generate(self, program: Program) -> List[Instruction]:
        for statement in program.statements:
            self._statement(statement)
        return self.instructions

    def _new_temp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def _new_label(self) -> str:
        self.label_count += 1
        return f"L{self.label_count}"

    def _enter_scope(self) -> None:
        self.scope_count += 1
        self.scope_ids.append(self.scope_count)
        self.scopes.append({})

    def _exit_scope(self) -> None:
        if len(self.scopes) > 1:
            self.scopes.pop()
            self.scope_ids.pop()

    def _declare_name(self, source_name: str) -> str:
        scope_id = self.scope_ids[-1]
        target_name = source_name if scope_id == 0 else f"{source_name}_s{scope_id}"
        self.scopes[-1][source_name] = target_name
        return target_name

    def _resolve_name(self, source_name: str) -> str:
        for scope in reversed(self.scopes):
            if source_name in scope:
                return scope[source_name]
        return source_name

    def _statement(self, node: Node) -> None:
        if isinstance(node, VarDecl):
            target_name = None
            if node.initializer is not None:
                value = self._expression(node.initializer)
                target_name = self._declare_name(node.name)
                self.instructions.append(Instruction("assign", result=target_name, arg1=value))
            if target_name is None:
                self._declare_name(node.name)
        elif isinstance(node, Assignment):
            value = self._expression(node.expression)
            self.instructions.append(Instruction("assign", result=self._resolve_name(node.name), arg1=value))
        elif isinstance(node, PrintStatement):
            value = self._expression(node.expression)
            self.instructions.append(Instruction("print", arg1=value))
        elif isinstance(node, Block):
            self._block(node)
        elif isinstance(node, IfStatement):
            self._if_statement(node)
        elif isinstance(node, WhileStatement):
            self._while_statement(node)

    def _block(self, block: Block) -> None:
        self._enter_scope()
        for statement in block.statements:
            self._statement(statement)
        self._exit_scope()

    def _if_statement(self, node: IfStatement) -> None:
        else_label = self._new_label()
        end_label = self._new_label()
        condition = self._expression(node.condition)

        self.instructions.append(Instruction("if_false", arg1=condition, result=else_label))
        self._block(node.then_block)
        self.instructions.append(Instruction("goto", result=end_label))
        self.instructions.append(Instruction("label", result=else_label))
        if node.else_block is not None:
            self._block(node.else_block)
        self.instructions.append(Instruction("label", result=end_label))

    def _while_statement(self, node: WhileStatement) -> None:
        start_label = self._new_label()
        end_label = self._new_label()

        self.instructions.append(Instruction("label", result=start_label))
        condition = self._expression(node.condition)
        self.instructions.append(Instruction("if_false", arg1=condition, result=end_label))
        self._block(node.body)
        self.instructions.append(Instruction("goto", result=start_label))
        self.instructions.append(Instruction("label", result=end_label))

    def _expression(self, node: Node) -> str:
        if isinstance(node, Literal):
            return self._literal_value(node)
        if isinstance(node, VariableReference):
            return self._resolve_name(node.name)
        if isinstance(node, UnaryExpression):
            operand = self._expression(node.operand)
            temp = self._new_temp()
            self.instructions.append(Instruction("unary", result=temp, operator=node.operator, arg1=operand))
            return temp
        if isinstance(node, BinaryExpression):
            left = self._expression(node.left)
            right = self._expression(node.right)
            temp = self._new_temp()
            self.instructions.append(
                Instruction("binop", result=temp, arg1=left, operator=node.operator, arg2=right)
            )
            return temp
        raise ICGError(f"Cannot generate code for expression {node.__class__.__name__}")

    def _literal_value(self, node: Literal) -> str:
        if node.literal_type == "bool":
            return "true" if node.value else "false"
        if node.literal_type == "char":
            return repr(node.value)
        return str(node.value)


def generate_tac(program: Program) -> List[Instruction]:
    return TACGenerator().generate(program)


def compile_source_to_tac(source: str) -> List[Instruction]:
    program = parse_source(source)
    semantic_result = analyze_program(program)
    if not semantic_result.ok:
        raise ICGError("\n".join(semantic_result.errors))
    return generate_tac(program)


def format_instructions(instructions: List[Instruction], include_numbers: bool = True) -> str:
    lines = []
    for index, instruction in enumerate(instructions, start=1):
        text = instruction.format()
        lines.append(f"{index:03d}: {text}" if include_numbers else text)
    return "\n".join(lines)


def parse_instructions(text: str) -> List[Instruction]:
    instructions: List[Instruction] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line and line.split(":", 1)[0].strip().isdigit():
            line = line.split(":", 1)[1].strip()

        if line.startswith("LABEL "):
            instructions.append(Instruction("label", result=line.split(None, 1)[1]))
            continue

        if line.startswith("GOTO "):
            instructions.append(Instruction("goto", result=line.split(None, 1)[1]))
            continue

        if line.startswith("IF_FALSE "):
            parts = line.split()
            if len(parts) != 4 or parts[2] != "GOTO":
                raise ICGError(f"Invalid IF_FALSE instruction at line {line_number}: {raw_line}")
            instructions.append(Instruction("if_false", arg1=parts[1], result=parts[3]))
            continue

        if line.startswith("PRINT "):
            instructions.append(Instruction("print", arg1=line.split(None, 1)[1]))
            continue

        if "=" in line:
            target, rhs = [part.strip() for part in line.split("=", 1)]
            parts = rhs.split()
            if len(parts) == 1:
                instructions.append(Instruction("assign", result=target, arg1=parts[0]))
                continue
            if len(parts) == 2 and parts[0] in {"-", "!"}:
                instructions.append(Instruction("unary", result=target, operator=parts[0], arg1=parts[1]))
                continue
            if len(parts) == 3:
                instructions.append(
                    Instruction("binop", result=target, arg1=parts[0], operator=parts[1], arg2=parts[2])
                )
                continue

        raise ICGError(f"Invalid TAC instruction at line {line_number}: {raw_line}")

    return instructions
