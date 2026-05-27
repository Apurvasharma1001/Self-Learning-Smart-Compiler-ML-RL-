"""
Copy Propagation Optimization Pass.

When a simple copy assignment `x = y` exists, replaces subsequent uses
of `x` with `y` directly, potentially enabling further dead code elimination.

Example:
    BEFORE:  t0 = a + b; c = t0; return c
    AFTER:   t0 = a + b; c = t0; return t0
"""

from __future__ import annotations
import sys
import os
import copy
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ir.tac_generator import TACInstruction, TACOp


class CopyPropagationPass:
    """Propagates copies to eliminate redundant variable references."""

    name = "copy_propagation"

    def optimize(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Apply copy propagation.

        Args:
            instructions: Original TAC instruction list.

        Returns:
            New list with copy references propagated.
        """
        result: List[TACInstruction] = []
        # Map: copy_target -> original_source
        # e.g., if we see `c = t0`, then copies['c'] = 't0'
        copies: Dict[str, str] = {}

        for instr in instructions:
            instr = copy.deepcopy(instr)

            # Reset copy tracking at function boundaries
            if instr.op in (TACOp.FUNC_BEGIN, TACOp.FUNC_END):
                copies.clear()
                result.append(instr)
                continue

            # Reset at labels (conservative — control flow merge)
            if instr.op == TACOp.LABEL:
                copies.clear()
                result.append(instr)
                continue

            # Propagate copies into operands before processing
            if instr.arg1 and instr.arg1 in copies:
                instr.arg1 = self._resolve(copies, instr.arg1)
            if instr.arg2 and instr.arg2 in copies:
                instr.arg2 = self._resolve(copies, instr.arg2)

            # Also propagate into result for ARRAY_STORE, MEMBER_STORE, DEREF_STORE
            if instr.op in (TACOp.ARRAY_STORE, TACOp.MEMBER_STORE, TACOp.DEREF_STORE):
                if instr.result and instr.result in copies:
                    instr.result = self._resolve(copies, instr.result)

            # Track new copies
            if instr.op == TACOp.ASSIGN:
                # x = y (simple copy, not a constant)
                if instr.arg1 and not self._is_literal(instr.arg1):
                    copies[instr.result] = instr.arg1
                else:
                    # x = <constant> — invalidate any copy for x
                    self._invalidate(copies, instr.result)

            elif instr.op in (TACOp.BINOP, TACOp.UNOP, TACOp.CALL,
                              TACOp.ARRAY_LOAD, TACOp.MEMBER_LOAD,
                              TACOp.DEREF_LOAD):
                # Result is recomputed — invalidate any copy tracking for it
                if instr.result:
                    self._invalidate(copies, instr.result)

            # Control flow changes — conservative invalidation
            if instr.op in (TACOp.GOTO, TACOp.IF_GOTO, TACOp.IF_FALSE):
                copies.clear()

            result.append(instr)

        return result

    @staticmethod
    def _resolve(copies: Dict[str, str], var: str) -> str:
        """Follow the copy chain to find the original source.

        Handles transitive copies: if a=b and b=c, then a resolves to c.
        Guards against cycles with a depth limit.
        """
        visited = set()
        current = var
        while current in copies and current not in visited:
            visited.add(current)
            current = copies[current]
        return current

    @staticmethod
    def _invalidate(copies: Dict[str, str], var: str):
        """Remove all copy entries involving a variable."""
        # Remove the entry for var itself
        copies.pop(var, None)
        # Remove entries where var is the source
        keys_to_remove = [k for k, v in copies.items() if v == var]
        for k in keys_to_remove:
            del copies[k]

    @staticmethod
    def _is_literal(value: str) -> bool:
        """Check if a value is a literal constant."""
        if value is None:
            return False
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            pass
        if value.startswith('"') and value.endswith('"'):
            return True
        return False
