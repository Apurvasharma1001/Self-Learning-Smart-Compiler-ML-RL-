"""
Training Script for ML and RL Models.

Generates training data from sample programs, trains the ML model,
and runs the RL agent through training episodes.

Usage:
    python -m optimizer.train
    python train_models.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser.parser import parse
from ir.tac_generator import TACGenerator, format_tac, count_instructions
from optimizer import PassManager
from optimizer.ml.model import OptimizationMLModel
from optimizer.rl.q_agent import CompilerRLAgent

# Collection of training programs covering different optimization scenarios
TRAINING_PROGRAMS = [
    # 1. Constant-heavy
    "int main() { int a = 3 + 5; int b = a * 2; int c = 10 - 4; return c; }",
    # 2. Dead code
    "int main() { int x = 10; int y = 20; int unused = 30; return x; }",
    # 3. Common subexpression
    "int main() { int a = 5; int b = 3; int c = a + b; int d = a + b; return c + d; }",
    # 4. Copy chain
    "int main() { int a = 10; int b = a; int c = b; int d = c; return d; }",
    # 5. Simple loop
    "int main() { int sum = 0; for (int i = 0; i < 10; i = i + 1) { sum = sum + i; } return sum; }",
    # 6. Nested constants
    "int main() { int a = 2 + 3; int b = a + 4; int c = b + 5; int d = c + 6; return d; }",
    # 7. Function call
    "int add(int x, int y) { return x + y; } int main() { int r = add(3, 5); return r; }",
    # 8. Fibonacci
    "int fib(int n) { if (n <= 1) { return n; } return fib(n - 1) + fib(n - 2); } int main() { return fib(10); }",
    # 9. Multiple dead vars
    "int main() { int a = 1; int b = 2; int c = 3; int d = 4; int e = 5; return a; }",
    # 10. Mixed ops
    "int main() { int x = 10; int y = x * 2 + 3; int z = y - x; return z; }",
    # 11. Conditional
    "int main() { int a = 10; if (a > 5) { a = a + 1; } else { a = a - 1; } return a; }",
    # 12. While loop with constants
    "int main() { int x = 0; int limit = 5 + 5; while (x < limit) { x = x + 1; } return x; }",
    # 13. GCD
    "int gcd(int a, int b) { while (b != 0) { int t = b; b = a % b; a = t; } return a; } int main() { return gcd(48, 18); }",
    # 14. Factorial
    "int fact(int n) { int r = 1; for (int i = 2; i <= n; i = i + 1) { r = r * i; } return r; } int main() { return fact(5); }",
    # 15. Complex expressions
    "int main() { int a = 2; int b = 3; int c = (a + b) * (a - b) + a * b; return c; }",
    # 16. Nested if
    "int main() { int x = 10; int y = 20; if (x < y) { if (x > 5) { return x; } } return y; }",
    # 17. Many unused with one used
    "int main() { int a=1; int b=2; int c=3; int d=4; int e=5; int f=6; int g=7; return g; }",
    # 18. All constants
    "int main() { return 1 + 2 + 3 + 4 + 5; }",
    # 19. Redundant computation
    "int main() { int a=5; int b=10; int c=a*b; int d=a*b; int e=c+d; return e; }",
    # 20. Deep copy chain
    "int main() { int a=42; int b=a; int c=b; int d=c; int e=d; int f=e; return f; }",
]


def train_ml_model():
    """Train the ML model and save it."""
    print("=" * 60)
    print("TRAINING ML MODEL")
    print("=" * 60)
    
    model = OptimizationMLModel()
    pm = PassManager()
    
    print(f"Generating training data from {len(TRAINING_PROGRAMS)} programs...")
    features, labels = model.generate_training_data(TRAINING_PROGRAMS, pm)
    print(f"Generated {len(features)} training samples")
    
    print("Training model...")
    model.train(features, labels)
    
    # Save model
    save_path = os.path.join(os.path.dirname(__file__), 'optimizer', 'ml', 'trained_model.json')
    model.save(save_path)
    print(f"Model saved to {save_path}")
    
    # Test on a sample
    print("\nTesting ML model:")
    test_code = "int main() { int a = 3 + 5; int b = a * 2; int unused = 99; return b; }"
    ast = parse(test_code)
    gen = TACGenerator()
    tac = gen.generate(ast)
    
    passes = model.select_passes(tac)
    print(f"  Selected passes: {passes}")
    
    optimized = pm.apply_passes(tac, passes)
    orig = count_instructions(tac)['total_instructions']
    opt = count_instructions(optimized)['total_instructions']
    print(f"  Original: {orig} instructions")
    print(f"  Optimized: {opt} instructions")
    print(f"  Reduction: {orig - opt} ({((orig - opt) / orig * 100):.1f}%)")
    
    return model


def train_rl_agent():
    """Train the RL agent and save Q-table."""
    print("\n" + "=" * 60)
    print("TRAINING RL AGENT")
    print("=" * 60)
    
    agent = CompilerRLAgent(
        learning_rate=0.2,
        discount_factor=0.95,
        epsilon=1.0,
        epsilon_decay=0.99,
        epsilon_min=0.05,
    )
    pm = PassManager()
    
    print(f"Training on {len(TRAINING_PROGRAMS)} programs for 300 episodes...")
    agent.train(TRAINING_PROGRAMS, pm, num_episodes=300, verbose=True)
    
    # Save Q-table
    save_path = os.path.join(os.path.dirname(__file__), 'optimizer', 'rl', 'q_table.json')
    agent.save_q_table(save_path)
    print(f"Q-table saved to {save_path}")
    print(f"States learned: {len(agent.q_table)}")
    
    # Show learned policy
    print("\nLearned Policy Summary:")
    summary = agent.get_policy_summary()
    for state, info in summary.items():
        if info['q_value'] > 0:
            print(f"  State {state}: {info['passes']} (Q={info['q_value']:.4f})")
    
    # Test
    print("\nTesting RL agent:")
    test_code = "int main() { int a = 3 + 5; int b = a * 2; int unused = 99; return b; }"
    ast = parse(test_code)
    gen = TACGenerator()
    tac = gen.generate(ast)
    
    passes = agent.select_passes(tac)
    print(f"  Selected passes: {passes}")
    
    optimized = pm.apply_passes(tac, passes)
    orig = count_instructions(tac)['total_instructions']
    opt = count_instructions(optimized)['total_instructions']
    print(f"  Original: {orig} instructions")
    print(f"  Optimized: {opt} instructions")
    print(f"  Reduction: {orig - opt} ({((orig - opt) / orig * 100):.1f}%)")
    
    return agent


if __name__ == '__main__':
    train_ml_model()
    train_rl_agent()
    print("\n" + "=" * 60)
    print("ALL TRAINING COMPLETE!")
    print("=" * 60)
