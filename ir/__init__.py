"""
Intermediate Representation (IR) package for the Mini Compiler.

This package handles the generation and management of the compiler's
Intermediate Representation — a three-address code (TAC) format that
serves as a portable, optimization-friendly bridge between the AST
and the final target code.

Modules:
    ir_generator - AST-to-IR translation logic
    tac          - Three-address code instruction definitions
    cfg          - Control flow graph construction
"""
