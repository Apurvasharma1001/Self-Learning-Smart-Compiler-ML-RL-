"""
Lexer (Tokenizer) package for the Mini Compiler.

This package implements lexical analysis — the first stage of the compilation
pipeline. It reads raw source code characters and produces a stream of tokens
(e.g., identifiers, keywords, literals, operators) using PLY (Python Lex-Yacc).

Modules:
    tokenizer   - Token definitions and lexer rules
    token_types - Enumeration of all supported token types
"""
