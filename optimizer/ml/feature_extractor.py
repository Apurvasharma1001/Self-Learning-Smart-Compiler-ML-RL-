"""
IR Feature Extractor for ML/RL-Based Optimization.

Extracts numerical features from TAC (Three Address Code) instructions
to characterize the program's structure and optimization potential.

Features extracted:
    - Instruction counts (total, by type)
    - Variable/temporary statistics
    - Control flow complexity (loops, branches)
    - Expression patterns (constants, array ops)
"""

from __future__ import annotations
import sys
import os
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ir.tac_generator import TACInstruction, TACOp


class IRFeatureExtractor:
    """Extracts feature vectors from TAC instructions for ML/RL models.
    
    Feature vector (12 dimensions):
        [0] total_instructions
        [1] binary_ops
        [2] unary_ops
        [3] temp_variables
        [4] labels
        [5] branches
        [6] constants_count
        [7] function_calls
        [8] array_ops
        [9] loop_count
        [10] assignments
        [11] has_recursion (0 or 1)
    """

    FEATURE_NAMES = [
        'total_instructions', 'binary_ops', 'unary_ops', 'temp_variables',
        'labels', 'branches', 'constants_count', 'function_calls',
        'array_ops', 'loop_count', 'assignments', 'has_recursion',
    ]

    def extract(self, instructions: List[TACInstruction]) -> Dict[str, float]:
        """Extract a feature dictionary from TAC instructions.
        
        Args:
            instructions: List of TAC instructions.
            
        Returns:
            Dictionary mapping feature names to values.
        """
        features = {name: 0 for name in self.FEATURE_NAMES}
        
        temps = set()
        label_positions = {}
        current_func = None
        func_calls_in_func = set()

        for idx, instr in enumerate(instructions):
            if instr.op in (TACOp.FUNC_BEGIN, TACOp.FUNC_END, TACOp.NOP):
                if instr.op == TACOp.FUNC_BEGIN:
                    current_func = instr.func_name
                    func_calls_in_func.clear()
                elif instr.op == TACOp.FUNC_END:
                    # Check if any function call in this function was recursive
                    if current_func and current_func in func_calls_in_func:
                        features['has_recursion'] = 1
                    current_func = None
                continue

            features['total_instructions'] += 1

            # Track temporaries
            if instr.result and instr.result.startswith('t') and instr.result[1:].isdigit():
                temps.add(instr.result)

            # Count by instruction type
            if instr.op == TACOp.BINOP:
                features['binary_ops'] += 1
            elif instr.op == TACOp.UNOP:
                features['unary_ops'] += 1
            elif instr.op == TACOp.ASSIGN:
                features['assignments'] += 1
            elif instr.op == TACOp.LABEL:
                features['labels'] += 1
                if instr.label:
                    label_positions[instr.label] = idx
            elif instr.op in (TACOp.GOTO, TACOp.IF_GOTO, TACOp.IF_FALSE):
                features['branches'] += 1
            elif instr.op == TACOp.CALL:
                features['function_calls'] += 1
                if instr.func_name:
                    func_calls_in_func.add(instr.func_name)
            elif instr.op in (TACOp.ARRAY_LOAD, TACOp.ARRAY_STORE):
                features['array_ops'] += 1

            # Count constants in operands
            if instr.arg1 and self._is_literal(instr.arg1):
                features['constants_count'] += 1
            if instr.arg2 and self._is_literal(instr.arg2):
                features['constants_count'] += 1

        features['temp_variables'] = len(temps)

        # Detect loops (back edges: GOTO to earlier label)
        loop_count = 0
        for instr in instructions:
            if instr.op == TACOp.GOTO and instr.label:
                target_pos = label_positions.get(instr.label)
                if target_pos is not None:
                    # Find the GOTO instruction's position
                    for i, check_instr in enumerate(instructions):
                        if check_instr is instr:
                            if target_pos < i:
                                loop_count += 1
                            break
        features['loop_count'] = loop_count

        return features

    def to_vector(self, features: Dict[str, float]) -> List[float]:
        """Convert feature dictionary to an ordered float vector.
        
        Args:
            features: Feature dictionary from extract().
            
        Returns:
            List of float values in standard order.
        """
        return [float(features.get(name, 0)) for name in self.FEATURE_NAMES]

    def discretize(self, features: Dict[str, float]) -> str:
        """Discretize features into a state string for Q-table lookup.
        
        Bins each feature into low/medium/high categories to create
        a manageable state space for tabular Q-learning.
        
        Args:
            features: Feature dictionary from extract().
            
        Returns:
            String key for Q-table (e.g., "H-M-L-L-M-H-L-L-L-L-M-0").
        """
        bins = []
        
        # Define thresholds for each feature
        thresholds = {
            'total_instructions': (5, 15),
            'binary_ops': (2, 6),
            'unary_ops': (1, 3),
            'temp_variables': (3, 8),
            'labels': (2, 5),
            'branches': (2, 5),
            'constants_count': (3, 8),
            'function_calls': (1, 3),
            'array_ops': (1, 4),
            'loop_count': (0, 2),
            'assignments': (2, 6),
            'has_recursion': (0, 1),
        }
        
        for name in self.FEATURE_NAMES:
            val = features.get(name, 0)
            low, high = thresholds.get(name, (1, 5))
            
            if name == 'has_recursion':
                bins.append(str(int(val)))
            elif val <= low:
                bins.append('L')
            elif val <= high:
                bins.append('M')
            else:
                bins.append('H')
        
        return '-'.join(bins)

    @staticmethod
    def _is_literal(value: str) -> bool:
        """Check if a value is a numeric literal."""
        if value is None:
            return False
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
