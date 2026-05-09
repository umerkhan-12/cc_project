from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .icg import Instruction


@dataclass
class OptimizationReport:
    counts: Dict[str, int] = field(
        default_factory=lambda: {
            "constant_folding": 0,
            "constant_propagation": 0,
            "copy_propagation": 0,
            "dead_code_elimination": 0,
            "peephole_branch": 0,
        }
    )

    def add(self, key: str, amount: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + amount

    def format(self) -> str:
        names = {
            "constant_folding": "Constant Folding",
            "constant_propagation": "Constant Propagation",
            "copy_propagation": "Copy Propagation",
            "dead_code_elimination": "Dead Code Elimination",
            "peephole_branch": "Peephole Branch Simplification",
        }
        lines = ["Optimization Summary"]
        for key, label in names.items():
            lines.append(f"- {label}: {self.counts.get(key, 0)} change(s)")
        return "\n".join(lines)


class Optimizer:
    def __init__(self):
        self.report = OptimizationReport()

    def optimize(self, instructions: List[Instruction]) -> Tuple[List[Instruction], OptimizationReport]:
        propagated = self._propagate_and_fold(instructions)
        simplified = self._simplify_branches(propagated)
        cleaned = self._dead_code_elimination(simplified)
        return cleaned, self.report

    def _propagate_and_fold(self, instructions: List[Instruction]) -> List[Instruction]:
        const_env: Dict[str, str] = {}
        copy_env: Dict[str, str] = {}
        output: List[Instruction] = []

        def clear_env() -> None:
            const_env.clear()
            copy_env.clear()

        def kill(name: Optional[str]) -> None:
            if not name:
                return
            const_env.pop(name, None)
            copy_env.pop(name, None)
            for key, value in list(copy_env.items()):
                if value == name:
                    copy_env.pop(key, None)

        def resolve_copy(name: str) -> str:
            seen = set()
            current = name
            while current in copy_env and current not in seen:
                seen.add(current)
                current = copy_env[current]
            return current

        def replace(operand: Optional[str]) -> Optional[str]:
            if operand is None:
                return None
            copied = resolve_copy(operand)
            if copied != operand:
                self.report.add("copy_propagation")
                operand = copied
            if operand in const_env:
                self.report.add("constant_propagation")
                return const_env[operand]
            return operand

        for instruction in instructions:
            if instruction.op == "label":
                clear_env()
                output.append(instruction)
                continue

            if instruction.op == "goto":
                output.append(instruction)
                clear_env()
                continue

            if instruction.op == "if_false":
                arg1 = replace(instruction.arg1)
                output.append(Instruction("if_false", arg1=arg1, result=instruction.result))
                clear_env()
                continue

            if instruction.op == "print":
                output.append(Instruction("print", arg1=replace(instruction.arg1)))
                continue

            if instruction.op == "assign":
                arg1 = replace(instruction.arg1)
                kill(instruction.result)
                if is_constant(arg1):
                    const_env[instruction.result or ""] = arg1 or ""
                elif is_identifier(arg1):
                    copy_env[instruction.result or ""] = arg1 or ""
                output.append(Instruction("assign", result=instruction.result, arg1=arg1))
                continue

            if instruction.op == "unary":
                arg1 = replace(instruction.arg1)
                folded = fold_unary(instruction.operator, arg1)
                kill(instruction.result)
                if folded is not None:
                    self.report.add("constant_folding")
                    const_env[instruction.result or ""] = folded
                    output.append(Instruction("assign", result=instruction.result, arg1=folded))
                else:
                    output.append(Instruction("unary", result=instruction.result, operator=instruction.operator, arg1=arg1))
                continue

            if instruction.op == "binop":
                arg1 = replace(instruction.arg1)
                arg2 = replace(instruction.arg2)
                folded = fold_binary(instruction.operator, arg1, arg2)
                killed_result = instruction.result
                kill(killed_result)
                if folded is not None:
                    self.report.add("constant_folding")
                    const_env[killed_result or ""] = folded
                    output.append(Instruction("assign", result=killed_result, arg1=folded))
                    continue

                simplified = simplify_algebraic(instruction.operator, arg1, arg2)
                if simplified is not None:
                    self.report.add("constant_folding")
                    if is_constant(simplified):
                        const_env[killed_result or ""] = simplified
                    elif is_identifier(simplified):
                        copy_env[killed_result or ""] = simplified
                    output.append(Instruction("assign", result=killed_result, arg1=simplified))
                    continue

                output.append(
                    Instruction("binop", result=killed_result, arg1=arg1, operator=instruction.operator, arg2=arg2)
                )

        return output

    def _simplify_branches(self, instructions: List[Instruction]) -> List[Instruction]:
        output: List[Instruction] = []
        for instruction in instructions:
            if instruction.op == "if_false" and is_bool_constant(instruction.arg1):
                if instruction.arg1 == "true":
                    self.report.add("peephole_branch")
                    continue
                self.report.add("peephole_branch")
                output.append(Instruction("goto", result=instruction.result))
                continue
            output.append(instruction)
        return output

    def _dead_code_elimination(self, instructions: List[Instruction]) -> List[Instruction]:
        live: Set[str] = set()
        output_reversed: List[Instruction] = []

        for instruction in reversed(instructions):
            if instruction.op == "print":
                add_if_identifier(live, instruction.arg1)
                output_reversed.append(instruction)
                continue

            if instruction.op == "if_false":
                add_if_identifier(live, instruction.arg1)
                output_reversed.append(instruction)
                continue

            if instruction.op in {"label", "goto"}:
                output_reversed.append(instruction)
                continue

            if instruction.op in {"assign", "unary", "binop"}:
                result = instruction.result
                removable_temp = result is not None and result.startswith("t") and result not in live
                if removable_temp:
                    self.report.add("dead_code_elimination")
                    continue

                if result in live:
                    live.remove(result)
                add_if_identifier(live, instruction.arg1)
                add_if_identifier(live, instruction.arg2)
                output_reversed.append(instruction)
                continue

            output_reversed.append(instruction)

        output_reversed.reverse()
        return output_reversed


def optimize_instructions(instructions: List[Instruction]) -> Tuple[List[Instruction], OptimizationReport]:
    return Optimizer().optimize(instructions)


def add_if_identifier(live: Set[str], operand: Optional[str]) -> None:
    if is_identifier(operand):
        live.add(operand or "")


def is_identifier(value: Optional[str]) -> bool:
    if value is None or is_constant(value):
        return False
    if not value:
        return False
    return (value[0].isalpha() or value[0] == "_") and all(ch.isalnum() or ch == "_" for ch in value)


def is_constant(value: Optional[str]) -> bool:
    return parse_constant(value) is not None


def is_bool_constant(value: Optional[str]) -> bool:
    parsed = parse_constant(value)
    return parsed is not None and parsed[0] == "bool"


def parse_constant(value: Optional[str]) -> Optional[Tuple[str, object]]:
    if value is None:
        return None
    if value == "true":
        return ("bool", True)
    if value == "false":
        return ("bool", False)
    if len(value) >= 3 and value.startswith("'") and value.endswith("'"):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return None
        if isinstance(parsed, str) and len(parsed) == 1:
            return ("char", parsed)
    try:
        if "." in value:
            return ("float", float(value))
        return ("int", int(value))
    except ValueError:
        return None


def format_constant(value: object, data_type: str) -> str:
    if data_type == "bool":
        return "true" if value else "false"
    if data_type == "char":
        return repr(value)
    if data_type == "int":
        return str(int(value))
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def fold_unary(operator: Optional[str], operand: Optional[str]) -> Optional[str]:
    parsed = parse_constant(operand)
    if parsed is None:
        return None
    data_type, value = parsed
    if operator == "-" and data_type in {"int", "float"}:
        result = -value
        return format_constant(result, data_type)
    if operator == "!" and data_type == "bool":
        return format_constant(not value, "bool")
    return None


def fold_binary(operator: Optional[str], left: Optional[str], right: Optional[str]) -> Optional[str]:
    left_const = parse_constant(left)
    right_const = parse_constant(right)
    if left_const is None or right_const is None or operator is None:
        return None

    left_type, left_value = left_const
    right_type, right_value = right_const

    try:
        if operator in {"+", "-", "*", "/"} and left_type in {"int", "float"} and right_type in {"int", "float"}:
            if operator == "+":
                result = left_value + right_value
            elif operator == "-":
                result = left_value - right_value
            elif operator == "*":
                result = left_value * right_value
            else:
                if right_value == 0:
                    return None
                result = int(left_value / right_value) if left_type == right_type == "int" else left_value / right_value
            result_type = "float" if "float" in {left_type, right_type} else "int"
            return format_constant(result, result_type)

        if operator == "%" and left_type == "int" and right_type == "int":
            if right_value == 0:
                return None
            return format_constant(left_value % right_value, "int")

        if operator in {"<", "<=", ">", ">="} and left_type in {"int", "float"} and right_type in {"int", "float"}:
            result = {
                "<": left_value < right_value,
                "<=": left_value <= right_value,
                ">": left_value > right_value,
                ">=": left_value >= right_value,
            }[operator]
            return format_constant(result, "bool")

        if operator in {"==", "!="}:
            if left_type == right_type or {left_type, right_type} <= {"int", "float"}:
                result = left_value == right_value
                if operator == "!=":
                    result = not result
                return format_constant(result, "bool")

        if operator in {"&&", "||"} and left_type == "bool" and right_type == "bool":
            result = (left_value and right_value) if operator == "&&" else (left_value or right_value)
            return format_constant(result, "bool")
    except (TypeError, ZeroDivisionError):
        return None

    return None


def simplify_algebraic(operator: Optional[str], left: Optional[str], right: Optional[str]) -> Optional[str]:
    if operator == "+":
        if right == "0":
            return left
        if left == "0":
            return right
    if operator == "-":
        if right == "0":
            return left
    if operator == "*":
        if right == "1":
            return left
        if left == "1":
            return right
        if right == "0" or left == "0":
            return "0"
    if operator == "/":
        if right == "1":
            return left
    if operator == "&&":
        if left == "true":
            return right
        if right == "true":
            return left
        if left == "false" or right == "false":
            return "false"
    if operator == "||":
        if left == "false":
            return right
        if right == "false":
            return left
        if left == "true" or right == "true":
            return "true"
    return None
