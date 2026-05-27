"""
Optimizer Module for Mini-C Compiler.

Provides the PassManager that orchestrates optimization passes on TAC
(Three Address Code) instructions. Supports registering individual passes
and applying them in sequence.

Usage:
    from optimizer import PassManager

    pm = PassManager()
    optimized = pm.apply_all(tac_instructions)
    # or selectively:
    optimized = pm.apply_passes(tac_instructions, ['constant_folding', 'dead_code_elimination'])
"""

from __future__ import annotations
import sys
import os
import copy
from typing import List, Dict, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ir.tac_generator import TACInstruction


class PassManager:
    """Manages and orchestrates optimization passes on TAC instructions.
    
    Each registered pass must have:
        - A `.name` attribute (string identifier)
        - An `.optimize(instructions)` method that takes and returns List[TACInstruction]
    """

    def __init__(self):
        self._passes: Dict[str, Any] = {}
        self._pass_order: List[str] = []
        self._register_default_passes()

    def _register_default_passes(self):
        """Register all built-in optimization passes."""
        from optimizer.passes.constant_folding import ConstantFoldingPass
        from optimizer.passes.dead_code import DeadCodeEliminationPass
        from optimizer.passes.cse import CSEPass
        from optimizer.passes.copy_propagation import CopyPropagationPass
        from optimizer.passes.loop_optimization import LoopOptimizationPass

        for PassClass in [
            ConstantFoldingPass,
            DeadCodeEliminationPass,
            CSEPass,
            CopyPropagationPass,
            LoopOptimizationPass,
        ]:
            self.register_pass(PassClass())

    def register_pass(self, pass_obj):
        """Register a new optimization pass.
        
        Args:
            pass_obj: An optimization pass object with .name and .optimize() method.
        """
        self._passes[pass_obj.name] = pass_obj
        if pass_obj.name not in self._pass_order:
            self._pass_order.append(pass_obj.name)

    def get_pass(self, name: str):
        """Get a pass object by name."""
        return self._passes.get(name)

    def get_all_passes(self) -> List:
        """Get all registered pass objects in order."""
        return [self._passes[name] for name in self._pass_order]

    def get_pass_names(self) -> List[str]:
        """Get names of all registered passes."""
        return list(self._pass_order)

    def apply_passes(
        self, instructions: List[TACInstruction],
        pass_names: List[str]
    ) -> List[TACInstruction]:
        """Apply specific passes by name in the given order.
        
        Args:
            instructions: TAC instructions to optimize.
            pass_names: List of pass names to apply (in order).
            
        Returns:
            Optimized TAC instructions.
        """
        current = [copy.deepcopy(i) for i in instructions]

        for name in pass_names:
            if name in self._passes:
                current = self._passes[name].optimize(current)

        return current

    def apply_all(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Apply all registered passes in the default order.
        
        The recommended order is:
        1. Constant Folding (simplify constants first)
        2. Copy Propagation (propagate copies)
        3. CSE (eliminate common subexpressions)
        4. Loop Optimization (hoist invariants)
        5. Dead Code Elimination (clean up last — removes unused results)
        
        We run two iterations for better optimization (passes can enable each other).
        
        Args:
            instructions: TAC instructions to optimize.
            
        Returns:
            Optimized TAC instructions.
        """
        # Optimal ordering: constant fold → copy prop → CSE → loop opt → dead code
        optimal_order = [
            'constant_folding',
            'copy_propagation',
            'cse',
            'loop_optimization',
            'dead_code_elimination',
        ]

        # Filter to only passes that are registered
        order = [name for name in optimal_order if name in self._passes]

        # Run two iterations for cascading optimizations
        current = [copy.deepcopy(i) for i in instructions]
        for _iteration in range(2):
            for name in order:
                current = self._passes[name].optimize(current)

        return current

    def apply_by_mask(
        self, instructions: List[TACInstruction],
        mask: List[bool]
    ) -> List[TACInstruction]:
        """Apply passes selected by a boolean mask.
        
        Args:
            instructions: TAC instructions to optimize.
            mask: List of booleans, one per registered pass.
                  True = apply, False = skip.
            
        Returns:
            Optimized TAC instructions.
        """
        selected = []
        for i, name in enumerate(self._pass_order):
            if i < len(mask) and mask[i]:
                selected.append(name)

        return self.apply_passes(instructions, selected)
