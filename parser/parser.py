"""
Mini-C Parser using PLY (Python Lex-Yacc).

This module implements the LALR(1) parser for the Mini-C language. It consumes
tokens from the lexer and constructs an Abstract Syntax Tree (AST).

The grammar follows the EBNF specification in docs/language_spec.md with
operator precedence handled via PLY's precedence declarations.

Grammar Structure:
    program → { top_level_decl }
    top_level_decl → struct_def | func_def | global_var_decl
    func_def → type_spec IDENTIFIER '(' params ')' compound_stmt
    statements → compound | if | while | for | return | expr_stmt
    expressions → assignment | binary_op | unary_op | postfix | primary
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ply.yacc as yacc
from lexer.lexer import tokens, build_lexer
from ast_nodes.nodes import (
    Program, TypeSpec, VarDecl, ArrayDecl, StructField, StructDef,
    ParamDecl, FunctionDef, CompoundStmt, ExprStmt, IfStmt, WhileStmt,
    ForStmt, ReturnStmt, BinaryOp, UnaryOp, Assignment, FunctionCall,
    ArrayAccess, StructAccess, Identifier, IntLiteral, FloatLiteral,
    StringLiteral
)


# =============================================================================
# Operator Precedence (lowest to highest)
# =============================================================================

precedence = (
    ('right', 'ASSIGN'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NEQ'),
    ('left', 'LT', 'GT', 'LEQ', 'GEQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MODULO'),
    ('right', 'UMINUS', 'UNOT', 'UADDR', 'UDEREF'),  # Unary operators
    ('left', 'LPAREN', 'LBRACKET', 'DOT'),              # Postfix
)


# =============================================================================
# Error collection
# =============================================================================

parse_errors = []


# =============================================================================
# Program (Root)
# =============================================================================

def p_program(p):
    '''program : top_level_list'''
    p[0] = Program(declarations=p[1], line=1)


def p_top_level_list(p):
    '''top_level_list : top_level_list top_level_decl
                      | top_level_decl
                      | empty'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    elif p[1] is None:
        p[0] = []
    else:
        p[0] = [p[1]]


def p_top_level_decl(p):
    '''top_level_decl : struct_def
                      | func_def
                      | global_var_decl'''
    p[0] = p[1]


# =============================================================================
# Struct Definition
# =============================================================================

def p_struct_def(p):
    '''struct_def : STRUCT IDENTIFIER LBRACE struct_field_list RBRACE SEMICOLON'''
    p[0] = StructDef(name=p[2], fields=p[4], line=p.lineno(1))


def p_struct_field_list(p):
    '''struct_field_list : struct_field_list struct_field
                         | struct_field
                         | empty'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    elif p[1] is None:
        p[0] = []
    else:
        p[0] = [p[1]]


def p_struct_field(p):
    '''struct_field : type_spec IDENTIFIER SEMICOLON
                    | type_spec IDENTIFIER LBRACKET INT_LITERAL RBRACKET SEMICOLON'''
    if len(p) == 4:
        p[0] = StructField(field_type=p[1], name=p[2], line=p.lineno(2))
    else:
        p[0] = StructField(field_type=p[1], name=p[2], array_size=p[4], line=p.lineno(2))


# =============================================================================
# Function Definition
# =============================================================================

def p_func_def(p):
    '''func_def : type_spec IDENTIFIER LPAREN param_list RPAREN compound_stmt'''
    p[0] = FunctionDef(
        return_type=p[1], name=p[2], params=p[4], body=p[6],
        line=p.lineno(2)
    )


def p_param_list(p):
    '''param_list : param_list_nonempty
                  | empty'''
    p[0] = p[1] if p[1] else []


def p_param_list_nonempty(p):
    '''param_list_nonempty : param_list_nonempty COMMA param
                           | param'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


def p_param(p):
    '''param : type_spec IDENTIFIER
             | type_spec IDENTIFIER LBRACKET RBRACKET'''
    if len(p) == 3:
        p[0] = ParamDecl(param_type=p[1], name=p[2], line=p.lineno(2))
    else:
        # Array parameter — mark the type as array
        arr_type = TypeSpec(
            base_type=p[1].base_type, is_pointer=p[1].is_pointer,
            is_struct=p[1].is_struct, is_array=True, line=p[1].line
        )
        p[0] = ParamDecl(param_type=arr_type, name=p[2], line=p.lineno(2))


# =============================================================================
# Global Variable Declaration
# =============================================================================

def p_global_var_decl(p):
    '''global_var_decl : type_spec IDENTIFIER SEMICOLON
                       | type_spec IDENTIFIER ASSIGN expression SEMICOLON
                       | type_spec IDENTIFIER LBRACKET INT_LITERAL RBRACKET SEMICOLON'''
    if len(p) == 4:
        # Simple declaration: int x;
        p[0] = VarDecl(var_type=p[1], name=p[2], line=p.lineno(2))
    elif len(p) == 6:
        # Declaration with init: int x = 5;
        p[0] = VarDecl(var_type=p[1], name=p[2], init_value=p[4], line=p.lineno(2))
    else:
        # Array declaration: int arr[10];
        p[0] = ArrayDecl(elem_type=p[1], name=p[2], size=p[4], line=p.lineno(2))


# =============================================================================
# Type Specification
# =============================================================================

def p_type_spec(p):
    '''type_spec : base_type
                 | base_type TIMES'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        # Pointer type
        p[1].is_pointer = True
        p[0] = p[1]


def p_base_type(p):
    '''base_type : INT
                 | FLOAT
                 | VOID
                 | STRUCT IDENTIFIER'''
    if len(p) == 2:
        p[0] = TypeSpec(base_type=p[1], line=p.lineno(1))
    else:
        p[0] = TypeSpec(base_type=p[2], is_struct=True, line=p.lineno(1))


# =============================================================================
# Statements
# =============================================================================

def p_compound_stmt(p):
    '''compound_stmt : LBRACE block_item_list RBRACE'''
    p[0] = CompoundStmt(items=p[2], line=p.lineno(1))


def p_block_item_list(p):
    '''block_item_list : block_item_list block_item
                       | empty'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = []


def p_block_item(p):
    '''block_item : local_var_decl
                  | statement'''
    p[0] = p[1]


def p_local_var_decl(p):
    '''local_var_decl : type_spec IDENTIFIER SEMICOLON
                      | type_spec IDENTIFIER ASSIGN expression SEMICOLON
                      | type_spec IDENTIFIER LBRACKET INT_LITERAL RBRACKET SEMICOLON'''
    if len(p) == 4:
        p[0] = VarDecl(var_type=p[1], name=p[2], line=p.lineno(2))
    elif len(p) == 6:
        p[0] = VarDecl(var_type=p[1], name=p[2], init_value=p[4], line=p.lineno(2))
    else:
        p[0] = ArrayDecl(elem_type=p[1], name=p[2], size=p[4], line=p.lineno(2))


def p_statement(p):
    '''statement : compound_stmt
                 | expression_stmt
                 | if_stmt
                 | while_stmt
                 | for_stmt
                 | return_stmt'''
    p[0] = p[1]


def p_expression_stmt(p):
    '''expression_stmt : expression SEMICOLON
                       | SEMICOLON'''
    if len(p) == 3:
        p[0] = ExprStmt(expr=p[1], line=p.lineno(2))
    else:
        p[0] = ExprStmt(expr=None, line=p.lineno(1))


def p_if_stmt(p):
    '''if_stmt : IF LPAREN expression RPAREN statement
               | IF LPAREN expression RPAREN statement ELSE statement'''
    if len(p) == 6:
        p[0] = IfStmt(condition=p[3], then_body=p[5], line=p.lineno(1))
    else:
        p[0] = IfStmt(condition=p[3], then_body=p[5], else_body=p[7], line=p.lineno(1))


def p_while_stmt(p):
    '''while_stmt : WHILE LPAREN expression RPAREN statement'''
    p[0] = WhileStmt(condition=p[3], body=p[5], line=p.lineno(1))


def p_for_stmt(p):
    '''for_stmt : FOR LPAREN for_init SEMICOLON for_cond SEMICOLON for_update RPAREN statement'''
    p[0] = ForStmt(init=p[3], condition=p[5], update=p[7], body=p[9], line=p.lineno(1))


def p_for_init(p):
    '''for_init : type_spec IDENTIFIER ASSIGN expression
                | expression
                | empty'''
    if len(p) == 5:
        # Variable declaration in for-init: for (int i = 0; ...)
        p[0] = VarDecl(var_type=p[1], name=p[2], init_value=p[4], line=p.lineno(2))
    elif p[1] is not None:
        p[0] = p[1]
    else:
        p[0] = None


def p_for_cond(p):
    '''for_cond : expression
               | empty'''
    p[0] = p[1]


def p_for_update(p):
    '''for_update : expression
                 | empty'''
    p[0] = p[1]


def p_return_stmt(p):
    '''return_stmt : RETURN expression SEMICOLON
                   | RETURN SEMICOLON'''
    if len(p) == 4:
        p[0] = ReturnStmt(value=p[2], line=p.lineno(1))
    else:
        p[0] = ReturnStmt(value=None, line=p.lineno(1))


# =============================================================================
# Expressions
# =============================================================================

def p_expression_assign(p):
    '''expression : postfix_expr ASSIGN expression'''
    p[0] = Assignment(target=p[1], value=p[3], line=p.lineno(2))


def p_expression_or(p):
    '''expression : expression OR expression'''
    p[0] = BinaryOp(op='||', left=p[1], right=p[3], line=p.lineno(2))


def p_expression_and(p):
    '''expression : expression AND expression'''
    p[0] = BinaryOp(op='&&', left=p[1], right=p[3], line=p.lineno(2))


def p_expression_eq(p):
    '''expression : expression EQ expression
                  | expression NEQ expression'''
    p[0] = BinaryOp(op=p[2], left=p[1], right=p[3], line=p.lineno(2))


def p_expression_rel(p):
    '''expression : expression LT expression
                  | expression GT expression
                  | expression LEQ expression
                  | expression GEQ expression'''
    p[0] = BinaryOp(op=p[2], left=p[1], right=p[3], line=p.lineno(2))


def p_expression_add(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression'''
    p[0] = BinaryOp(op=p[2], left=p[1], right=p[3], line=p.lineno(2))


def p_expression_mul(p):
    '''expression : expression TIMES expression
                  | expression DIVIDE expression
                  | expression MODULO expression'''
    p[0] = BinaryOp(op=p[2], left=p[1], right=p[3], line=p.lineno(2))


# Unary operators
def p_expression_uminus(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = UnaryOp(op='-', operand=p[2], line=p.lineno(1))


def p_expression_not(p):
    '''expression : NOT expression %prec UNOT'''
    p[0] = UnaryOp(op='!', operand=p[2], line=p.lineno(1))


def p_expression_addr(p):
    '''expression : AMPERSAND expression %prec UADDR'''
    p[0] = UnaryOp(op='&', operand=p[2], line=p.lineno(1))


def p_expression_deref(p):
    '''expression : TIMES expression %prec UDEREF'''
    p[0] = UnaryOp(op='*', operand=p[2], line=p.lineno(1))


# Postfix expressions
def p_postfix_expr(p):
    '''postfix_expr : primary_expr'''
    p[0] = p[1]


def p_expression_postfix(p):
    '''expression : postfix_expr'''
    p[0] = p[1]


def p_postfix_func_call(p):
    '''postfix_expr : IDENTIFIER LPAREN arg_list RPAREN'''
    p[0] = FunctionCall(name=p[1], arguments=p[3], line=p.lineno(1))


def p_postfix_array_access(p):
    '''postfix_expr : postfix_expr LBRACKET expression RBRACKET'''
    p[0] = ArrayAccess(array=p[1], index=p[3], line=p.lineno(2))


def p_postfix_struct_access(p):
    '''postfix_expr : postfix_expr DOT IDENTIFIER'''
    p[0] = StructAccess(struct_expr=p[1], member=p[3], line=p.lineno(2))


def p_arg_list(p):
    '''arg_list : arg_list_nonempty
               | empty'''
    p[0] = p[1] if p[1] else []


def p_arg_list_nonempty(p):
    '''arg_list_nonempty : arg_list_nonempty COMMA expression
                         | expression'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


# Primary expressions
def p_primary_identifier(p):
    '''primary_expr : IDENTIFIER'''
    p[0] = Identifier(name=p[1], line=p.lineno(1))


def p_primary_int(p):
    '''primary_expr : INT_LITERAL'''
    p[0] = IntLiteral(value=p[1], line=p.lineno(1))


def p_primary_float(p):
    '''primary_expr : FLOAT_LITERAL'''
    p[0] = FloatLiteral(value=p[1], line=p.lineno(1))


def p_primary_string(p):
    '''primary_expr : STRING_LITERAL'''
    p[0] = StringLiteral(value=p[1], line=p.lineno(1))


def p_primary_paren(p):
    '''primary_expr : LPAREN expression RPAREN'''
    p[0] = p[2]


# =============================================================================
# Empty Production
# =============================================================================

def p_empty(p):
    '''empty :'''
    p[0] = None


# =============================================================================
# Error Handling
# =============================================================================

def p_error(p):
    """Handle syntax errors with informative messages."""
    if p:
        error_msg = f"Syntax error at '{p.value}' (token {p.type}) on line {p.lineno}"
        parse_errors.append(error_msg)
        print(f"Parse Error: {error_msg}")
        # Try to recover by discarding the problematic token
        parser.errok()
    else:
        error_msg = "Syntax error at end of file (unexpected EOF)"
        parse_errors.append(error_msg)
        print(f"Parse Error: {error_msg}")


# =============================================================================
# Parser Builder
# =============================================================================

def build_parser(**kwargs):
    """Build and return a new PLY parser instance.
    
    Args:
        **kwargs: Additional arguments passed to ply.yacc.yacc()
        
    Returns:
        yacc.Parser: A configured parser ready to parse Mini-C source code.
    """
    return yacc.yacc(**kwargs)


def parse(source_code: str, debug: bool = False) -> Program:
    """Parse Mini-C source code and return an AST.
    
    Args:
        source_code: The Mini-C source code string.
        debug: If True, enable PLY debug output.
        
    Returns:
        Program AST node (root of the syntax tree).
        
    Raises:
        SyntaxError: If the source code contains syntax errors.
    """
    global parse_errors
    parse_errors = []
    
    # Create a fresh lexer for each parse
    lex = build_lexer()
    
    result = parser.parse(source_code, lexer=lex, debug=debug)
    
    if parse_errors:
        raise SyntaxError(
            f"Parse failed with {len(parse_errors)} error(s):\n" +
            "\n".join(f"  - {e}" for e in parse_errors)
        )
    
    return result


# =============================================================================
# Module-level parser instance
# =============================================================================

# Build the parser (generates parsetab.py on first run)
parser = build_parser(debug=False, write_tables=True, outputdir=os.path.dirname(os.path.abspath(__file__)))
