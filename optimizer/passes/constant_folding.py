"""
Constant Folding Optimization Pass.

Evaluates constant expressions at compile time, replacing BINOP/UNOP
instructions that operate on literal values with simple ASSIGN instructions
holding the computed result.

Example:
    BEFORE:  t0 = 3 + 5
    AFTER:   t0 = 8

Also propagates constants through simple assignments:
    BEFORE:  a = 8; t1 = a * 2
    AFTER:   a = 8; t1 = 16
"""

from __future__ import annotations
import sys
import os
import copy
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ir.tac_generator import TACInstruction, TACOp


class ConstantFoldingPass:
    """Folds constant expressions at compile time."""

    name = "constant_folding"

    def optimize(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Apply constant folding to a list of TAC instructions.

        Args:
            instructions: Original TAC instruction list.

        Returns:
            New list with constant expressions folded.
        """
        result: List[TACInstruction] = []
        # Map variable -> known constant value (string representation)
        constants: Dict[str, str] = {}

        for instr in instructions:
            instr = copy.deepcopy(instr)

            if instr.op == TACOp.FUNC_BEGIN:
                # Reset constant tracking at function boundaries
                constants.clear()
                result.append(instr)
                continue

            if instr.op == TACOp.FUNC_END:
                result.append(instr)
                continue

            # Propagate known constants into operands
            if instr.arg1 and instr.arg1 in constants:
                instr.arg1 = constants[instr.arg1]
            if instr.arg2 and instr.arg2 in constants:
                instr.arg2 = constants[instr.arg2]

            if instr.op == TACOp.BINOP:
                # Try to evaluate if both operands are numeric constants
                val1 = self._try_parse_number(instr.arg1)
                val2 = self._try_parse_number(instr.arg2)

                if val1 is not None and val2 is not None:
                    computed = self._evaluate(instr.operator, val1, val2)
                    if computed is not None:
                        folded_val = self._format_number(computed)
                        # Replace BINOP with ASSIGN of the computed constant
                        instr = TACInstruction(
                            op=TACOp.ASSIGN,
                            result=instr.result,
                            arg1=folded_val,
                            source_line=instr.source_line,
                        )
                        # Track the new constant
                        constants[instr.result] = folded_val
                        result.append(instr)
                        continue

            if instr.op == TACOp.UNOP:
                val = self._try_parse_number(instr.arg1)
                if val is not None:
                    computed = self._evaluate_unary(instr.operator, val)
                    if computed is not None:
                        folded_val = self._format_number(computed)
                        instr = TACInstruction(
                            op=TACOp.ASSIGN,
                            result=instr.result,
                            arg1=folded_val,
                            source_line=instr.source_line,
                        )
                        constants[instr.result] = folded_val
                        result.append(instr)
                        continue

            if instr.op == TACOp.ASSIGN:
                # Track constant assignments: x = <literal>
                val = self._try_parse_number(instr.arg1)
                if val is not None:
                    constants[instr.result] = instr.arg1
                else:
                    # Invalidate if assigning a non-constant
                    constants.pop(instr.result, None)

            # Invalidate constants on reassignment via BINOP/CALL etc.
            if instr.op in (TACOp.BINOP, TACOp.UNOP, TACOp.CALL,
                            TACOp.ARRAY_LOAD, TACOp.MEMBER_LOAD,
                            TACOp.DEREF_LOAD):
                if instr.result:
                    constants.pop(instr.result, None)

            # Labels and branches can change control flow — be conservative
            if instr.op in (TACOp.LABEL, TACOp.GOTO, TACOp.IF_GOTO,
                            TACOp.IF_FALSE):
                # Invalidate all constants at control flow merge points
                # (conservative approach for correctness)
                constants.clear()

            result.append(instr)

        return result

    @staticmethod
    def _try_parse_number(value: Optional[str]) -> Optional[float]:
        """Try to parse a string as a number."""
        if value is None:
            return None
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _format_number(value) -> str:
        """Format a computed value as a string."""
        if isinstance(value, float) and value == int(value):
            return str(int(value))
        return str(value)

    @staticmethod
    def _evaluate(op: str, left, right) -> Optional[float]:
        """Evaluate a binary operation on two numeric values."""
        try:
            if op == '+':
                return left + right
            elif op == '-':
                return left - right
            elif op == '*':
                return left * right
            elif op == '/':
                if right == 0:
                    return None  # Division by zero
                if isinstance(left, int) and isinstance(right, int):
                    return left // right  # Integer division
                return left / right
            elif op == '%':
                if right == 0:
                    return None
                return left % right
            elif op == '==':
                return 1 if left == right else 0
            elif op == '!=':
                return 1 if left != right else 0
            elif op == '<':
                return 1 if left < right else 0
            elif op == '>':
                return 1 if left > right else 0
            elif op == '<=':
                return 1 if left <= right else 0
            elif op == '>=':
                return 1 if left >= right else 0
            elif op == '&&':
                return 1 if (left and right) else 0
            elif op == '||':
                return 1 if (left or right) else 0
        except Exception:
            return None
        return None

    @staticmethod
    def _evaluate_unary(op: str, operand) -> Optional[float]:
        """Evaluate a unary operation."""
        try:
            if op == '-':
                return -operand
            elif op == '!':
                return 0 if operand else 1
        except Exception:
            return None
        return None
