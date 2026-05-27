"""
Optimization Passes for Mini-C Compiler.

Exports all individual optimization pass classes:
    - ConstantFoldingPass
    - DeadCodeEliminationPass
    - CSEPass
    - CopyPropagationPass
    - LoopOptimizationPass
"""

from optimizer.passes.constant_folding import ConstantFoldingPass
from optimizer.passes.dead_code import DeadCodeEliminationPass
from optimizer.passes.cse import CSEPass
from optimizer.passes.copy_propagation import CopyPropagationPass
from optimizer.passes.loop_optimization import LoopOptimizationPass

ALL_PASSES = [
    ConstantFoldingPass,
    DeadCodeEliminationPass,
    CSEPass,
    CopyPropagationPass,
    LoopOptimizationPass,
]

__all__ = [
    'ConstantFoldingPass',
    'DeadCodeEliminationPass',
    'CSEPass',
    'CopyPropagationPass',
    'LoopOptimizationPass',
    'ALL_PASSES',
]
