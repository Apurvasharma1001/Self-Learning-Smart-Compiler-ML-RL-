"""
Parser (Syntax Analyzer) package for the Mini Compiler.

This package implements syntax analysis — the second stage of the compilation
pipeline. It consumes tokens produced by the lexer and constructs an Abstract
Syntax Tree (AST) according to the language grammar, using PLY's yacc module.

Modules:
    grammar     - BNF grammar rules and parser configuration
    parse_tree  - Parse tree construction utilities
"""
