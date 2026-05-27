"""
Q-Learning Reinforcement Learning Agent for Compiler Optimization.

Uses tabular Q-learning to learn which optimization passes to apply
based on the IR features of the program being compiled.

State:  Discretized IR feature vector (e.g., "H-M-L-L-M-H-L-L-L-L-M-0")
Action: A 5-bit combination of passes (32 possible actions)
Reward: Instruction count reduction ratio

The agent learns a policy mapping program characteristics to optimal
pass selections through repeated compilation episodes.
"""

from __future__ import annotations
import sys
import os
import json
import random
import copy
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimizer.ml.feature_extractor import IRFeatureExtractor
from ir.tac_generator import TACInstruction, count_instructions

PASS_NAMES = [
    'constant_folding',
    'dead_code_elimination',
    'cse',
    'copy_propagation',
    'loop_optimization',
]

# Generate all 32 possible actions (pass combinations)
ALL_ACTIONS = []
for combo in range(32):
    action = tuple((combo >> i) & 1 for i in range(5))
    ALL_ACTIONS.append(action)


class CompilerRLAgent:
    """Q-Learning agent for adaptive compiler optimization.
    
    The agent learns to select the best combination of optimization
    passes for different types of programs through trial and error.
    
    Attributes:
        q_table: Dictionary mapping state-action pairs to Q-values.
        lr: Learning rate (alpha).
        gamma: Discount factor.
        epsilon: Exploration rate (probability of random action).
        epsilon_decay: Rate at which epsilon decreases per episode.
        epsilon_min: Minimum exploration rate.
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        self.feature_extractor = IRFeatureExtractor()
        self.q_table: Dict[str, Dict[str, float]] = {}
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Training history for analysis
        self.training_history: List[Dict] = []

    def get_state(self, instructions: List[TACInstruction]) -> str:
        """Extract state representation from TAC instructions.
        
        Args:
            instructions: TAC instructions.
            
        Returns:
            Discretized state string for Q-table lookup.
        """
        features = self.feature_extractor.extract(instructions)
        return self.feature_extractor.discretize(features)

    def _get_action_key(self, action: Tuple[int, ...]) -> str:
        """Convert action tuple to string key for Q-table."""
        return ''.join(str(a) for a in action)

    def _ensure_state(self, state: str):
        """Initialize Q-values for a new state if not seen before."""
        if state not in self.q_table:
            self.q_table[state] = {}
            for action in ALL_ACTIONS:
                action_key = self._get_action_key(action)
                self.q_table[state][action_key] = 0.0

    def choose_action(self, state: str) -> Tuple[int, ...]:
        """Choose an action using epsilon-greedy strategy.
        
        With probability epsilon, choose a random action (explore).
        Otherwise, choose the action with highest Q-value (exploit).
        
        Args:
            state: Current state string.
            
        Returns:
            Action tuple (5 binary values).
        """
        self._ensure_state(state)
        
        if random.random() < self.epsilon:
            # Explore: random action
            return random.choice(ALL_ACTIONS)
        else:
            # Exploit: best known action
            q_values = self.q_table[state]
            max_q = max(q_values.values())
            best_actions = [
                a for a in ALL_ACTIONS
                if q_values[self._get_action_key(a)] == max_q
            ]
            return random.choice(best_actions)

    def calculate_reward(
        self, original_count: int, optimized_count: int
    ) -> float:
        """Calculate reward from instruction count reduction.
        
        Reward is the fractional reduction in instruction count,
        with a small penalty for no improvement.
        
        Args:
            original_count: Instruction count before optimization.
            optimized_count: Instruction count after optimization.
            
        Returns:
            Reward value (higher is better).
        """
        if original_count == 0:
            return 0.0
        
        reduction = original_count - optimized_count
        reward = reduction / original_count
        
        # Small penalty for no improvement to encourage exploration
        if reduction <= 0:
            reward = -0.1
        
        return reward

    def update(
        self, state: str, action: Tuple[int, ...],
        reward: float, next_state: str
    ):
        """Update Q-value using the Q-learning update rule.
        
        Q(s,a) = Q(s,a) + lr * [reward + gamma * max(Q(s',a')) - Q(s,a)]
        
        Args:
            state: Current state.
            action: Action taken.
            reward: Reward received.
            next_state: Resulting state.
        """
        self._ensure_state(state)
        self._ensure_state(next_state)
        
        action_key = self._get_action_key(action)
        
        current_q = self.q_table[state][action_key]
        max_future_q = max(self.q_table[next_state].values())
        
        new_q = current_q + self.lr * (reward + self.gamma * max_future_q - current_q)
        self.q_table[state][action_key] = new_q

    def decay_epsilon(self):
        """Reduce exploration rate after each episode."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def train(
        self, sample_programs: List[str],
        optimizer=None,
        num_episodes: int = 500,
        verbose: bool = False,
    ):
        """Train the agent on sample programs.
        
        Each episode:
        1. Pick a random program
        2. Parse → TAC
        3. Get state from IR features
        4. Choose action (pass combination)
        5. Apply selected passes
        6. Calculate reward (instruction reduction)
        7. Update Q-table
        8. Decay epsilon
        
        Args:
            sample_programs: List of Mini-C source code strings.
            optimizer: PassManager instance.
            num_episodes: Number of training episodes.
            verbose: Print progress during training.
        """
        if optimizer is None:
            from optimizer import PassManager
            optimizer = PassManager()
        
        # Pre-parse all programs to TAC for efficiency
        parsed_programs = []
        for source in sample_programs:
            try:
                from parser.parser import parse
                from ir.tac_generator import TACGenerator
                
                ast = parse(source)
                gen = TACGenerator()
                tac = gen.generate(ast)
                if tac:
                    parsed_programs.append(tac)
            except Exception:
                continue
        
        if not parsed_programs:
            print("[RL Agent] No valid programs for training.")
            return
        
        self.training_history = []
        
        for episode in range(num_episodes):
            # Pick a random program
            tac = random.choice(parsed_programs)
            tac_copy = [copy.deepcopy(i) for i in tac]
            
            # Get state
            state = self.get_state(tac_copy)
            original_count = count_instructions(tac_copy)['total_instructions']
            
            if original_count == 0:
                continue
            
            # Choose action
            action = self.choose_action(state)
            
            # Apply selected passes
            pass_names = [
                PASS_NAMES[i] for i in range(5) if action[i]
            ]
            
            if pass_names:
                optimized = optimizer.apply_passes(tac_copy, pass_names)
            else:
                optimized = tac_copy
            
            opt_count = count_instructions(optimized)['total_instructions']
            
            # Calculate reward
            reward = self.calculate_reward(original_count, opt_count)
            
            # Get next state (after optimization)
            next_state = self.get_state(optimized)
            
            # Update Q-table
            self.update(state, action, reward, next_state)
            
            # Decay exploration
            self.decay_epsilon()
            
            # Record history
            self.training_history.append({
                'episode': episode,
                'reward': reward,
                'epsilon': self.epsilon,
                'action': self._get_action_key(action),
                'original': original_count,
                'optimized': opt_count,
            })
            
            if verbose and episode % 50 == 0:
                avg_reward = sum(
                    h['reward'] for h in self.training_history[-50:]
                ) / min(50, len(self.training_history))
                print(
                    f"  Episode {episode:4d}: "
                    f"avg_reward={avg_reward:.3f}, "
                    f"epsilon={self.epsilon:.3f}, "
                    f"states={len(self.q_table)}"
                )

    def select_passes(self, tac_instructions: List[TACInstruction]) -> List[str]:
        """Select optimization passes using the learned Q-table.
        
        Args:
            tac_instructions: TAC instructions to optimize.
            
        Returns:
            List of pass name strings to apply.
        """
        state = self.get_state(tac_instructions)
        
        # Use greedy policy (no exploration during inference)
        old_epsilon = self.epsilon
        self.epsilon = 0.0
        action = self.choose_action(state)
        self.epsilon = old_epsilon
        
        selected = [PASS_NAMES[i] for i in range(5) if action[i]]
        
        # Fallback: if no passes selected, use basic set
        if not selected:
            selected = ['constant_folding', 'dead_code_elimination']
        
        return selected

    def save_q_table(self, filepath: str):
        """Save Q-table and training config to JSON file.
        
        Args:
            filepath: Path to save the Q-table.
        """
        data = {
            'q_table': self.q_table,
            'epsilon': self.epsilon,
            'lr': self.lr,
            'gamma': self.gamma,
            'training_episodes': len(self.training_history),
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_q_table(self, filepath: str):
        """Load Q-table from a JSON file.
        
        Args:
            filepath: Path to the saved Q-table.
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.q_table = data.get('q_table', {})
            self.epsilon = data.get('epsilon', self.epsilon_min)
            
        except FileNotFoundError:
            pass

    def get_policy_summary(self) -> Dict[str, str]:
        """Get a summary of the learned policy.
        
        Returns:
            Dictionary mapping states to their best actions.
        """
        summary = {}
        for state, actions in self.q_table.items():
            best_action_key = max(actions, key=actions.get)
            best_q = actions[best_action_key]
            
            # Decode action key to pass names
            pass_list = [
                PASS_NAMES[i] for i, c in enumerate(best_action_key) if c == '1'
            ]
            
            summary[state] = {
                'passes': pass_list,
                'q_value': round(best_q, 4),
            }
        
        return summary
