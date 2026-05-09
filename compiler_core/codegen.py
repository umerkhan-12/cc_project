from __future__ import annotations

from typing import List, Optional

from .icg import Instruction
from .optimizer import parse_constant


BINOP_TO_VM = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "%": "MOD",
    "<": "LT",
    "<=": "LE",
    ">": "GT",
    ">=": "GE",
    "==": "EQ",
    "!=": "NE",
    "&&": "AND",
    "||": "OR",
}

UNARY_TO_VM = {"-": "NEG", "!": "NOT"}


class CodeGenerationError(Exception):
    pass


class StackMachineGenerator:
    def generate(self, instructions: List[Instruction]) -> List[str]:
        output = [
            "; Lumina stack-machine target code",
            "; Instructions: PUSH/LOAD/STORE, arithmetic ops, jumps, and PRINT",
        ]

        for instruction in instructions:
            if instruction.op == "label":
                output.append(f"{instruction.result}:")
            elif instruction.op == "goto":
                output.append(f"    JMP {instruction.result}")
            elif instruction.op == "if_false":
                output.extend(self._push_operand(instruction.arg1))
                output.append(f"    JZ {instruction.result}")
            elif instruction.op == "print":
                output.extend(self._push_operand(instruction.arg1))
                output.append("    PRINT")
            elif instruction.op == "assign":
                output.extend(self._push_operand(instruction.arg1))
                output.append(f"    STORE {instruction.result}")
            elif instruction.op == "unary":
                if instruction.operator not in UNARY_TO_VM:
                    raise CodeGenerationError(f"Unsupported unary operator {instruction.operator!r}")
                output.extend(self._push_operand(instruction.arg1))
                output.append(f"    {UNARY_TO_VM[instruction.operator]}")
                output.append(f"    STORE {instruction.result}")
            elif instruction.op == "binop":
                if instruction.operator not in BINOP_TO_VM:
                    raise CodeGenerationError(f"Unsupported binary operator {instruction.operator!r}")
                output.extend(self._push_operand(instruction.arg1))
                output.extend(self._push_operand(instruction.arg2))
                output.append(f"    {BINOP_TO_VM[instruction.operator]}")
                output.append(f"    STORE {instruction.result}")
            else:
                raise CodeGenerationError(f"Unsupported TAC instruction {instruction.op!r}")

        return output

    def _push_operand(self, operand: Optional[str]) -> List[str]:
        if operand is None:
            raise CodeGenerationError("Missing operand")

        parsed = parse_constant(operand)
        if parsed is not None:
            data_type, value = parsed
            if data_type == "bool":
                return [f"    PUSH {1 if value else 0}"]
            if data_type == "char":
                return [f"    PUSH {ord(value)}    ; {operand}"]
            return [f"    PUSH {operand}"]

        return [f"    LOAD {operand}"]


def generate_target_code(instructions: List[Instruction]) -> str:
    return "\n".join(StackMachineGenerator().generate(instructions))

