"""
Code Generation package for the Mini Compiler.

This package implements the final stage of the compilation pipeline —
translating optimized IR (three-address code) into target code. The
code generator traverses the IR and emits executable output.

Modules:
    generator   - Main code generation logic (IR to target code)
    emitter     - Low-level code emission utilities
"""
