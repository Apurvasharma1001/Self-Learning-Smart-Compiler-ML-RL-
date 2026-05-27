"""
Common Subexpression Elimination (CSE) Optimization Pass.

Detects repeated computations of the same expression and replaces
duplicates with a reference to the first computation.

Example:
    BEFORE:  t0 = a + b; t1 = a + b
    AFTER:   t0 = a + b; t1 = t0
"""

from __future__ import annotations
import sys
import os
import copy
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ir.tac_generator import TACInstruction, TACOp


class CSEPass:
    """Eliminates redundant computations of the same expression."""

    name = "cse"

    def optimize(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Apply common subexpression elimination.

        Args:
            instructions: Original TAC instruction list.

        Returns:
            New list with duplicate expressions replaced.
        """
        result: List[TACInstruction] = []
        # Map: (operator, arg1, arg2) -> result variable name
        expr_cache: Dict[Tuple[str, str, str], str] = {}

        for instr in instructions:
            instr = copy.deepcopy(instr)

            # Clear cache at function and label boundaries (conservative)
            if instr.op in (TACOp.FUNC_BEGIN, TACOp.FUNC_END):
                expr_cache.clear()
                result.append(instr)
                continue

            if instr.op == TACOp.LABEL:
                # Labels are potential merge points — clear cache
                expr_cache.clear()
                result.append(instr)
                continue

            if instr.op == TACOp.BINOP:
                expr_key = (instr.operator, instr.arg1, instr.arg2)

                if expr_key in expr_cache:
                    # This expression was computed before — reuse!
                    prev_result = expr_cache[expr_key]
                    instr = TACInstruction(
                        op=TACOp.ASSIGN,
                        result=instr.result,
                        arg1=prev_result,
                        source_line=instr.source_line,
                    )
                else:
                    # First time seeing this expression — cache it
                    expr_cache[expr_key] = instr.result

                    # Also cache commutative expressions
                    if instr.operator in ('+', '*', '==', '!=', '&&', '||'):
                        comm_key = (instr.operator, instr.arg2, instr.arg1)
                        expr_cache[comm_key] = instr.result

            # Invalidate cache entries when a variable is reassigned
            if instr.result and instr.op in (TACOp.ASSIGN, TACOp.BINOP,
                                              TACOp.UNOP, TACOp.CALL,
                                              TACOp.ARRAY_LOAD, TACOp.MEMBER_LOAD,
                                              TACOp.DEREF_LOAD):
                self._invalidate_cache(expr_cache, instr.result)

            # Assignments and stores can invalidate cached expressions
            if instr.op in (TACOp.ARRAY_STORE, TACOp.MEMBER_STORE,
                            TACOp.DEREF_STORE):
                # Conservative: clear cache for any memory write
                # (we don't do alias analysis)
                expr_cache.clear()

            # Control flow changes require conservative invalidation
            if instr.op in (TACOp.GOTO, TACOp.IF_GOTO, TACOp.IF_FALSE):
                expr_cache.clear()

            result.append(instr)

        return result

    @staticmethod
    def _invalidate_cache(cache: Dict, var_name: str):
        """Remove cache entries that reference a reassigned variable."""
        keys_to_remove = []
        for key, val in cache.items():
            op, arg1, arg2 = key
            if arg1 == var_name or arg2 == var_name or val == var_name:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del cache[key]
