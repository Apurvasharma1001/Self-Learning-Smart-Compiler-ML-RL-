"""
Loop-Invariant Code Motion (LICM) Optimization Pass.

Detects loops in the TAC by finding back edges (GOTO to an earlier LABEL),
then identifies instructions inside the loop whose operands are all defined
outside the loop (or are constants). Such loop-invariant instructions are
hoisted before the loop header.

Example:
    BEFORE:                         AFTER:
    L0:                             t_inv = x * 2     ← hoisted
      t0 = x * 2                   L0:
      t1 = t0 + i                    t1 = t_inv + i
      i = i + 1                      i = i + 1
      if i < n goto L0               if i < n goto L0
"""

from __future__ import annotations
import sys
import os
import copy
from typing import List, Set, Dict, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ir.tac_generator import TACInstruction, TACOp


class LoopOptimizationPass:
    """Hoists loop-invariant computations out of loops."""

    name = "loop_optimization"

    def optimize(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Apply loop-invariant code motion.

        Args:
            instructions: Original TAC instruction list.

        Returns:
            New list with invariant code hoisted out of loops.
        """
        instructions = [copy.deepcopy(i) for i in instructions]

        # Find loops (back edges)
        loops = self._find_loops(instructions)

        if not loops:
            return instructions

        # Process each loop (from innermost to outermost for best results)
        # Sort by loop size — smallest first
        loops.sort(key=lambda l: l[1] - l[0])

        for header_idx, back_edge_idx in loops:
            instructions = self._hoist_invariants(
                instructions, header_idx, back_edge_idx
            )

        return instructions

    def _find_loops(self, instructions: List[TACInstruction]) -> List[Tuple[int, int]]:
        """Find loop back edges in the instruction list.

        A back edge is a GOTO instruction that jumps to a LABEL that
        appears earlier in the instruction list.

        Returns:
            List of (header_index, back_edge_index) tuples.
        """
        # Build label-to-index map
        label_map: Dict[str, int] = {}
        for idx, instr in enumerate(instructions):
            if instr.op == TACOp.LABEL and instr.label:
                label_map[instr.label] = idx

        loops = []
        for idx, instr in enumerate(instructions):
            if instr.op == TACOp.GOTO and instr.label:
                target_idx = label_map.get(instr.label)
                if target_idx is not None and target_idx < idx:
                    # Back edge found: this is a loop
                    loops.append((target_idx, idx))

        return loops

    def _hoist_invariants(
        self, instructions: List[TACInstruction],
        header_idx: int, back_edge_idx: int
    ) -> List[TACInstruction]:
        """Hoist loop-invariant instructions before the loop header.

        An instruction is loop-invariant if:
        1. It computes a value (BINOP, UNOP, ASSIGN)
        2. All its operands are either:
           a. Constants (numeric literals)
           b. Defined outside the loop
           c. Defined by other loop-invariant instructions
        3. Its result is not modified elsewhere in the loop
        """
        loop_body = instructions[header_idx:back_edge_idx + 1]

        # Find variables defined (written) inside the loop
        loop_defined: Set[str] = set()
        for instr in loop_body:
            if instr.result and instr.op not in (
                TACOp.LABEL, TACOp.GOTO, TACOp.IF_GOTO, TACOp.IF_FALSE,
                TACOp.PARAM, TACOp.FUNC_BEGIN, TACOp.FUNC_END
            ):
                loop_defined.add(instr.result)

        # Find loop-invariant instructions
        invariant_indices: List[int] = []  # Indices relative to header_idx

        for i, instr in enumerate(loop_body):
            if instr.op not in (TACOp.BINOP, TACOp.UNOP):
                continue

            # Check if all operands are invariant
            operands = []
            if instr.arg1:
                operands.append(instr.arg1)
            if instr.arg2:
                operands.append(instr.arg2)

            all_invariant = True
            for op in operands:
                if self._is_literal(op):
                    continue  # Constants are invariant
                if op not in loop_defined:
                    continue  # Defined outside loop — invariant
                # Defined inside loop — not invariant
                all_invariant = False
                break

            if not all_invariant:
                continue

            # Check that the result isn't used as a loop control variable
            # (e.g., loop counter). We check if result is modified more
            # than once in the loop.
            if instr.result:
                def_count = sum(
                    1 for li in loop_body
                    if li.result == instr.result and li.op not in (
                        TACOp.LABEL, TACOp.GOTO, TACOp.FUNC_BEGIN, TACOp.FUNC_END
                    )
                )
                if def_count > 1:
                    continue  # Modified multiple times — not safe to hoist

            invariant_indices.append(i)

        if not invariant_indices:
            return instructions

        # Extract invariant instructions
        hoisted = [loop_body[i] for i in invariant_indices]

        # Build new instruction list with invariants hoisted
        new_instructions = []

        # Everything before the loop header
        new_instructions.extend(instructions[:header_idx])

        # Insert hoisted instructions before the loop
        new_instructions.extend(hoisted)

        # Loop body without the hoisted instructions
        for i, instr in enumerate(loop_body):
            if i not in invariant_indices:
                new_instructions.append(instr)

        # Everything after the loop
        new_instructions.extend(instructions[back_edge_idx + 1:])

        return new_instructions

    @staticmethod
    def _is_literal(value: str) -> bool:
        """Check if a value is a literal constant."""
        if value is None:
            return False
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
