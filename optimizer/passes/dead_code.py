"""
Dead Code Elimination Optimization Pass.

Removes instructions whose results are never used by any subsequent
instruction. Runs iteratively until a fixed point is reached.

Example:
    BEFORE:  t0 = 3 + 5; t1 = 10; return t0
    AFTER:   t0 = 3 + 5; return t0       (t1 removed — never used)
"""

from __future__ import annotations
import sys
import os
import copy
from typing import List, Set

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ir.tac_generator import TACInstruction, TACOp

# Instructions that should NEVER be removed (they have side effects)
SIDE_EFFECT_OPS = {
    TACOp.LABEL, TACOp.GOTO, TACOp.IF_GOTO, TACOp.IF_FALSE,
    TACOp.PARAM, TACOp.CALL, TACOp.RETURN,
    TACOp.ARRAY_STORE, TACOp.MEMBER_STORE, TACOp.DEREF_STORE,
    TACOp.FUNC_BEGIN, TACOp.FUNC_END, TACOp.NOP,
}


class DeadCodeEliminationPass:
    """Removes instructions whose results are never used."""

    name = "dead_code_elimination"

    def optimize(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Apply dead code elimination iteratively.

        Args:
            instructions: Original TAC instruction list.

        Returns:
            New list with dead instructions removed.
        """
        current = [copy.deepcopy(i) for i in instructions]
        changed = True

        # Iterate until fixed point (no more removals)
        while changed:
            changed = False
            used_vars = self._collect_used_vars(current)
            new_instructions = []

            for instr in current:
                if self._is_dead(instr, used_vars):
                    changed = True  # Something was removed
                    continue
                new_instructions.append(instr)

            current = new_instructions

        return current

    def _collect_used_vars(self, instructions: List[TACInstruction]) -> Set[str]:
        """Collect all variables/temps that are actually read/used.

        A variable is "used" if it appears as:
        - arg1 or arg2 of any instruction
        - The condition in IF_GOTO / IF_FALSE
        - A PARAM argument
        - A RETURN value
        - An array index or base in ARRAY_STORE
        - A struct base in MEMBER_STORE
        - A pointer in DEREF_STORE
        """
        used: Set[str] = set()

        for instr in instructions:
            # arg1 is read in most instructions
            if instr.arg1 and not self._is_literal(instr.arg1):
                if instr.op != TACOp.FUNC_BEGIN:
                    used.add(instr.arg1)

            # arg2 is read in BINOP, ARRAY_LOAD, ARRAY_STORE
            if instr.arg2 and not self._is_literal(instr.arg2):
                used.add(instr.arg2)

            # For ARRAY_STORE: arg1[arg2] = result — result is also read
            if instr.op == TACOp.ARRAY_STORE:
                if instr.result and not self._is_literal(instr.result):
                    used.add(instr.result)

            # For MEMBER_STORE: arg1.member = result
            if instr.op == TACOp.MEMBER_STORE:
                if instr.result and not self._is_literal(instr.result):
                    used.add(instr.result)

            # For DEREF_STORE: *arg1 = result
            if instr.op == TACOp.DEREF_STORE:
                if instr.result and not self._is_literal(instr.result):
                    used.add(instr.result)

            # CALL: result is the return value, but the call has side effects
            # The function call itself uses its args (already pushed via PARAM)

        return used

    def _is_dead(self, instr: TACInstruction, used_vars: Set[str]) -> bool:
        """Check if an instruction is dead (result never used).

        An instruction is dead if:
        1. It has a result (writes to something)
        2. The result is never used by any other instruction
        3. It has no side effects
        """
        # Never remove side-effect instructions
        if instr.op in SIDE_EFFECT_OPS:
            return False

        # Instructions with a result that nobody reads are dead
        if instr.result and instr.result not in used_vars:
            return True

        return False

    @staticmethod
    def _is_literal(value: str) -> bool:
        """Check if a value is a literal (number or string)."""
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
