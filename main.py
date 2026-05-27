#!/usr/bin/env python3
"""
Mini-C Compiler — Main CLI Entry Point.

A mini compiler for a C-like language with ML/RL-based adaptive optimization.

Usage:
    python main.py compile <file>                  # Normal compilation
    python main.py compile <file> --mode ml        # ML-optimized
    python main.py compile <file> --mode rl        # RL-optimized
    python main.py compare <file>                  # Compare all modes
    python main.py train                           # Train ML/RL models
    python main.py web                             # Start web interface
    python main.py test                            # Run all tests
"""

import sys
import os
import argparse

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_compile(args):
    """Compile a Mini-C source file."""
    from runtime.pipeline import CompilerPipeline
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)
    
    with open(args.file, 'r') as f:
        source = f.read()
    
    pipeline = CompilerPipeline(verbose=True)
    result = pipeline.compile(source, mode=args.mode)
    
    if result.success:
        print("\n--- TAC (Original) ---")
        print(result.tac_original)
        
        if result.tac_optimized:
            print("--- TAC (Optimized) ---")
            print(result.tac_optimized)
            if result.improvement:
                imp = result.improvement
                print(f"Improvement: {imp['percentage']}% "
                      f"({imp['original_count']} -> {imp['optimized_count']} instructions)")
        
        print("--- Assembly ---")
        print(result.assembly)
    else:
        print("\nCompilation Errors:")
        for err in result.errors:
            print(f"  - {err}")
        sys.exit(1)


def cmd_compare(args):
    """Compare all compilation modes on a file."""
    from runtime.pipeline import CompilerPipeline
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)
    
    with open(args.file, 'r') as f:
        source = f.read()
    
    pipeline = CompilerPipeline(verbose=False)
    results = pipeline.compile_and_compare(source)
    
    print("=" * 60)
    print("COMPILATION COMPARISON")
    print("=" * 60)
    
    for mode, result in results.items():
        print(f"\n--- {mode.upper()} ---")
        if result.success:
            orig = result.tac_original_metrics.get('total_instructions', '?')
            opt = result.tac_optimized_metrics.get('total_instructions', orig)
            asm = result.assembly_metrics.get('total_instructions', '?')
            print(f"  TAC: {orig} -> {opt} instructions")
            print(f"  ASM: {asm} instructions")
            print(f"  Time: {result.compile_time_ms}ms")
            if result.improvement:
                print(f"  Improvement: {result.improvement['percentage']}%")
            if result.passes_applied:
                print(f"  Passes: {', '.join(result.passes_applied)}")
        else:
            print(f"  FAILED: {result.errors}")


def cmd_train(args):
    """Train ML and RL models."""
    from train_models import train_ml_model, train_rl_agent
    train_ml_model()
    train_rl_agent()


def cmd_web(args):
    """Start the web interface."""
    from web.app import app
    port = args.port if hasattr(args, 'port') else 5000
    print(f"Starting Mini-C Compiler Web Interface on port {port}...")
    print(f"Open http://localhost:{port} in your browser")
    app.run(debug=True, port=port, host='0.0.0.0')


def cmd_test(args):
    """Run all test suites."""
    import subprocess
    test_files = [
        'tests/test_pipeline_quick.py',
        'tests/test_optimizer_quick.py',
        'tests/test_smart_pipeline.py',
    ]
    
    all_passed = True
    for tf in test_files:
        if os.path.exists(tf):
            print(f"\n{'='*60}")
            print(f"Running: {tf}")
            print('='*60)
            result = subprocess.run([sys.executable, tf], cwd=os.path.dirname(__file__) or '.')
            if result.returncode != 0:
                all_passed = False
                print(f"FAILED: {tf}")
    
    if all_passed:
        print(f"\n{'='*60}")
        print("ALL TESTS PASSED!")
        print('='*60)
    else:
        print(f"\n{'='*60}")
        print("SOME TESTS FAILED!")
        print('='*60)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Mini-C Compiler with ML/RL Adaptive Optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # compile
    p_compile = subparsers.add_parser('compile', help='Compile a Mini-C file')
    p_compile.add_argument('file', help='Source file path')
    p_compile.add_argument('--mode', choices=['normal', 'ml', 'rl'], default='normal',
                          help='Compilation mode (default: normal)')

    # compare
    p_compare = subparsers.add_parser('compare', help='Compare all compilation modes')
    p_compare.add_argument('file', help='Source file path')

    # train
    subparsers.add_parser('train', help='Train ML and RL models')

    # web
    p_web = subparsers.add_parser('web', help='Start web interface')
    p_web.add_argument('--port', type=int, default=5000, help='Server port (default: 5000)')

    # test
    subparsers.add_parser('test', help='Run all tests')

    args = parser.parse_args()

    if args.command == 'compile':
        cmd_compile(args)
    elif args.command == 'compare':
        cmd_compare(args)
    elif args.command == 'train':
        cmd_train(args)
    elif args.command == 'web':
        cmd_web(args)
    elif args.command == 'test':
        cmd_test(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
