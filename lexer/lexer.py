"""
Mini-C Lexer using PLY (Python Lex-Yacc).

This module implements the tokenizer for the Mini-C language. It converts
source code text into a stream of tokens that the parser can consume.

Supports:
    - Keywords: int, float, void, if, else, for, while, return, struct
    - Identifiers: [a-zA-Z_][a-zA-Z0-9_]*
    - Literals: integers, floats, strings
    - Operators: arithmetic, relational, logical, assignment, pointer
    - Delimiters: parentheses, braces, brackets, semicolons, commas, dot
    - Comments: single-line (//) and multi-line (/* */)
"""

import ply.lex as lex
from typing import List, Optional, Tuple


# =============================================================================
# Reserved Keywords
# =============================================================================

reserved = {
    'int':    'INT',
    'float':  'FLOAT',
    'void':   'VOID',
    'if':     'IF',
    'else':   'ELSE',
    'for':    'FOR',
    'while':  'WHILE',
    'return': 'RETURN',
    'struct': 'STRUCT',
}

# =============================================================================
# Token List
# =============================================================================

tokens = [
    # Literals
    'INT_LITERAL',
    'FLOAT_LITERAL',
    'STRING_LITERAL',

    # Identifier
    'IDENTIFIER',

    # Arithmetic operators
    'PLUS',        # +
    'MINUS',       # -
    'TIMES',       # *
    'DIVIDE',      # /
    'MODULO',      # %

    # Relational operators
    'EQ',          # ==
    'NEQ',         # !=
    'LT',          # <
    'GT',          # >
    'LEQ',         # <=
    'GEQ',         # >=

    # Logical operators
    'AND',         # &&
    'OR',          # ||
    'NOT',         # !

    # Assignment
    'ASSIGN',      # =

    # Pointer / Address operators
    'AMPERSAND',   # &

    # Delimiters
    'LPAREN',      # (
    'RPAREN',      # )
    'LBRACE',      # {
    'RBRACE',      # }
    'LBRACKET',    # [
    'RBRACKET',    # ]
    'SEMICOLON',   # ;
    'COMMA',       # ,
    'DOT',         # .
] + list(reserved.values())


# =============================================================================
# Token Rules (ordered by specificity — functions first, then strings)
# =============================================================================

# Multi-character operators must be defined BEFORE single-character ones
# PLY matches function-defined tokens in order of definition, and
# string-defined tokens by longest match.

def t_FLOAT_LITERAL(t):
    r'[0-9]+\.[0-9]+'
    t.value = float(t.value)
    return t

def t_INT_LITERAL(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

def t_STRING_LITERAL(t):
    r'"[^"\n]*"'
    # Strip the surrounding quotes
    t.value = t.value[1:-1]
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Check if this identifier is a reserved keyword
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

# Multi-character operators (defined as functions for priority over single-char)
def t_EQ(t):
    r'=='
    return t

def t_NEQ(t):
    r'!='
    return t

def t_LEQ(t):
    r'<='
    return t

def t_GEQ(t):
    r'>='
    return t

def t_AND(t):
    r'&&'
    return t

def t_OR(t):
    r'\|\|'
    return t

# Single-character operators (string rules — longest match applies)
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_DIVIDE    = r'/'
t_MODULO    = r'%'
t_LT        = r'<'
t_GT        = r'>'
t_NOT       = r'!'
t_ASSIGN    = r'='
t_AMPERSAND = r'&'

# Delimiters
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_SEMICOLON = r';'
t_COMMA     = r','
t_DOT       = r'\.'


# =============================================================================
# Ignored Characters and Comments
# =============================================================================

# Whitespace (spaces and tabs)
t_ignore = ' \t'

def t_SINGLE_LINE_COMMENT(t):
    r'//[^\n]*'
    pass  # Discard single-line comments

def t_MULTI_LINE_COMMENT(t):
    r'/\*[\s\S]*?\*/'
    # Count newlines within multi-line comments for accurate line tracking
    t.lexer.lineno += t.value.count('\n')

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    """Handle illegal characters."""
    print(f"Lexer Error: Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)


# =============================================================================
# Lexer Builder
# =============================================================================

def build_lexer(**kwargs) -> lex.Lexer:
    """Build and return a new PLY lexer instance.
    
    Args:
        **kwargs: Additional arguments passed to ply.lex.lex()
        
    Returns:
        lex.Lexer: A configured lexer ready to tokenize Mini-C source code.
    """
    return lex.lex(**kwargs)


def tokenize(source_code: str) -> List[lex.LexToken]:
    """Tokenize source code and return a list of tokens.
    
    This is a convenience function for testing and debugging.
    
    Args:
        source_code: The Mini-C source code to tokenize.
        
    Returns:
        List of LexToken objects with type, value, lineno, and lexpos attributes.
    """
    lexer = build_lexer()
    lexer.input(source_code)
    
    tokens_list = []
    while True:
        tok = lexer.token()
        if tok is None:
            break
        tokens_list.append(tok)
    
    return tokens_list


def format_tokens(tokens_list: List[lex.LexToken]) -> str:
    """Format a list of tokens as a human-readable string.
    
    Args:
        tokens_list: List of LexToken objects.
        
    Returns:
        Formatted string showing each token's type, value, and line number.
    """
    lines = []
    for tok in tokens_list:
        lines.append(f"  Line {tok.lineno:3d} | {tok.type:15s} | {tok.value!r}")
    
    header = f"  {'Line':>8s} | {'Token Type':15s} | Value"
    separator = "  " + "-" * 45
    
    return "\n".join([header, separator] + lines)


# =============================================================================
# Module-level lexer instance (for direct use by parser)
# =============================================================================

# Build a default lexer instance that the parser module can import
lexer = build_lexer()
