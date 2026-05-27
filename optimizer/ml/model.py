"""
ML Model for Optimization Pass Selection.

Uses a RandomForestClassifier (when available) or a rule-based heuristic
fallback to predict the best combination of optimization passes for a
given TAC program based on extracted IR features.

The model predicts a 5-bit mask indicating which of the 5 passes to apply:
    [constant_folding, dead_code_elimination, cse, copy_propagation, loop_optimization]
"""

from __future__ import annotations
import sys
import os
import json
import copy
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimizer.ml.feature_extractor import IRFeatureExtractor
from ir.tac_generator import TACInstruction, count_instructions

# Try to import scikit-learn; fall back to heuristic if unavailable
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.multioutput import MultiOutputClassifier
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

PASS_NAMES = [
    'constant_folding',
    'dead_code_elimination',
    'cse',
    'copy_propagation',
    'loop_optimization',
]


class OptimizationMLModel:
    """ML model that selects the best optimization passes for a program.
    
    Uses RandomForestClassifier when scikit-learn is available, otherwise
    falls back to a rule-based heuristic that examines IR features.
    """

    def __init__(self):
        self.feature_extractor = IRFeatureExtractor()
        self.model = None
        self.is_trained = False
        self.use_sklearn = HAS_SKLEARN
        
        # Training data storage
        self.training_features: List[List[float]] = []
        self.training_labels: List[List[int]] = []

    def select_passes(self, tac_instructions: List[TACInstruction]) -> List[str]:
        """Select optimization passes for the given TAC instructions.
        
        Args:
            tac_instructions: TAC instructions to analyze.
            
        Returns:
            List of pass name strings to apply.
        """
        features = self.feature_extractor.extract(tac_instructions)
        
        if self.is_trained and self.model is not None and self.use_sklearn:
            return self._predict_sklearn(features)
        else:
            return self._predict_heuristic(features)

    def _predict_heuristic(self, features: Dict[str, float]) -> List[str]:
        """Rule-based heuristic for pass selection.
        
        Examines IR features and selects passes based on thresholds:
        - High constant count → constant folding
        - Many temps/assignments → dead code elimination
        - Many binary ops → CSE
        - Many assignments → copy propagation
        - Has loops → loop optimization
        """
        selected = []
        
        # Constant folding: beneficial when there are constant operands
        if features.get('constants_count', 0) >= 2:
            selected.append('constant_folding')
        
        # Dead code elimination: beneficial when there are many temporaries
        if features.get('temp_variables', 0) >= 2 or features.get('assignments', 0) >= 3:
            selected.append('dead_code_elimination')
        
        # CSE: beneficial when there are many binary operations
        if features.get('binary_ops', 0) >= 3:
            selected.append('cse')
        
        # Copy propagation: beneficial when there are copy assignments
        if features.get('assignments', 0) >= 2:
            selected.append('copy_propagation')
        
        # Loop optimization: beneficial when loops exist
        if features.get('loop_count', 0) >= 1:
            selected.append('loop_optimization')
        
        # Always include at least constant folding and dead code elim
        if not selected:
            selected = ['constant_folding', 'dead_code_elimination']
        
        return selected

    def _predict_sklearn(self, features: Dict[str, float]) -> List[str]:
        """Use trained sklearn model to predict pass selection."""
        vector = self.feature_extractor.to_vector(features)
        prediction = self.model.predict([vector])[0]
        
        selected = []
        for i, apply_pass in enumerate(prediction):
            if apply_pass and i < len(PASS_NAMES):
                selected.append(PASS_NAMES[i])
        
        return selected if selected else ['constant_folding', 'dead_code_elimination']

    def generate_training_data(
        self, sample_programs: List[str], optimizer=None
    ) -> Tuple[List[List[float]], List[List[int]]]:
        """Generate training data by trying all pass combinations.
        
        For each program:
        1. Parse → TAC
        2. Try all 32 combinations (2^5 passes)
        3. Record which gives best instruction reduction
        
        Args:
            sample_programs: List of Mini-C source code strings.
            optimizer: PassManager instance for applying passes.
            
        Returns:
            Tuple of (feature_vectors, labels).
        """
        if optimizer is None:
            from optimizer import PassManager
            optimizer = PassManager()
        
        features_list = []
        labels_list = []
        
        for source in sample_programs:
            try:
                from parser.parser import parse
                from ir.tac_generator import TACGenerator
                
                ast = parse(source)
                gen = TACGenerator()
                tac = gen.generate(ast)
                
                if not tac:
                    continue
                
                # Extract features
                features = self.feature_extractor.extract(tac)
                vector = self.feature_extractor.to_vector(features)
                
                original_count = count_instructions(tac)['total_instructions']
                if original_count == 0:
                    continue
                
                # Try all 32 combinations of 5 passes
                best_mask = [1, 1, 1, 1, 1]  # Default: all passes
                best_reduction = 0
                
                for combo in range(32):
                    mask = [(combo >> i) & 1 for i in range(5)]
                    pass_names = [PASS_NAMES[i] for i in range(5) if mask[i]]
                    
                    if not pass_names:
                        continue
                    
                    optimized = optimizer.apply_passes(tac, pass_names)
                    opt_count = count_instructions(optimized)['total_instructions']
                    reduction = original_count - opt_count
                    
                    if reduction > best_reduction:
                        best_reduction = reduction
                        best_mask = mask
                
                features_list.append(vector)
                labels_list.append(best_mask)
                
            except Exception:
                continue
        
        self.training_features = features_list
        self.training_labels = labels_list
        
        return features_list, labels_list

    def train(self, features: List[List[float]] = None, labels: List[List[int]] = None):
        """Train the ML model on the given data.
        
        Args:
            features: Feature vectors (uses stored data if None).
            labels: Pass masks (uses stored data if None).
        """
        features = features or self.training_features
        labels = labels or self.training_labels
        
        if not features or not labels:
            print("[ML Model] No training data available. Using heuristic mode.")
            return
        
        if not HAS_SKLEARN:
            print("[ML Model] scikit-learn not available. Using heuristic mode.")
            return
        
        X = np.array(features)
        y = np.array(labels)
        
        # Use MultiOutputClassifier for 5 binary outputs
        base_clf = RandomForestClassifier(
            n_estimators=50, max_depth=8, random_state=42
        )
        self.model = MultiOutputClassifier(base_clf)
        self.model.fit(X, y)
        self.is_trained = True
        
        print(f"[ML Model] Trained on {len(features)} samples")

    def save(self, filepath: str):
        """Save model and training data."""
        data = {
            'training_features': self.training_features,
            'training_labels': self.training_labels,
            'use_sklearn': self.use_sklearn,
            'is_trained': self.is_trained,
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save sklearn model separately if available
        if self.is_trained and self.model is not None and HAS_SKLEARN:
            try:
                import joblib
                model_path = filepath.replace('.json', '_model.pkl')
                joblib.dump(self.model, model_path)
            except ImportError:
                pass

    def load(self, filepath: str):
        """Load model and training data."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.training_features = data.get('training_features', [])
            self.training_labels = data.get('training_labels', [])
            
            # Try to load sklearn model
            if HAS_SKLEARN:
                try:
                    import joblib
                    model_path = filepath.replace('.json', '_model.pkl')
                    if os.path.exists(model_path):
                        self.model = joblib.load(model_path)
                        self.is_trained = True
                except (ImportError, FileNotFoundError):
                    # Retrain from saved data
                    if self.training_features and self.training_labels:
                        self.train()
        except FileNotFoundError:
            pass
