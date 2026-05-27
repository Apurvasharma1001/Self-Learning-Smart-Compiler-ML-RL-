"""
AST Nodes package for the Mini Compiler.

This package defines all Abstract Syntax Tree (AST) node types used to
represent the structure of parsed programs. Each node type is implemented
as a Python dataclass for clean, type-safe representation.

Note: This package is named 'ast_nodes' to avoid conflicts with Python's
built-in 'ast' module.

Modules:
    nodes       - Dataclass definitions for all AST node types
    visitor     - Visitor pattern base class for AST traversal
"""
