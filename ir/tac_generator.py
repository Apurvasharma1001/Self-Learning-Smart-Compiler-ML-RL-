"""
Three Address Code (TAC) Generator for Mini-C Compiler.

Translates AST nodes into a linear sequence of TAC instructions.
Each instruction has at most three operands (result, arg1, arg2).

TAC Instruction Types:
    ASSIGN:       result = arg1
    BINOP:        result = arg1 op arg2
    UNOP:         result = op arg1
    LABEL:        label:
    GOTO:         goto label
    IF_GOTO:      if arg1 goto label
    IF_FALSE:     ifFalse arg1 goto label
    PARAM:        param arg1
    CALL:         result = call func, n_args
    RETURN:       return [arg1]
    ARRAY_LOAD:   result = arg1[arg2]
    ARRAY_STORE:  arg1[arg2] = result
    MEMBER_LOAD:  result = arg1.member
    MEMBER_STORE: arg1.member = result
    ADDR_OF:      result = &arg1
    DEREF_LOAD:   result = *arg1
    DEREF_STORE:  *arg1 = result
    FUNC_BEGIN:   func_begin name
    FUNC_END:     func_end name
"""

from __future__ import annotations
import sys
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum, auto

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ast_nodes.nodes import (
    ASTNode, ASTVisitor, Program, TypeSpec, VarDecl, ArrayDecl, StructField,
    StructDef, ParamDecl, FunctionDef, CompoundStmt, ExprStmt, IfStmt,
    WhileStmt, ForStmt, ReturnStmt, BinaryOp, UnaryOp, Assignment,
    FunctionCall, ArrayAccess, StructAccess, Identifier, IntLiteral,
    FloatLiteral, StringLiteral
)


# =============================================================================
# TAC Instruction Types
# =============================================================================

class TACOp(Enum):
    """Enumeration of all TAC operation types."""
    ASSIGN       = auto()   # result = arg1
    BINOP        = auto()   # result = arg1 op arg2
    UNOP         = auto()   # result = op arg1
    LABEL        = auto()   # label:
    GOTO         = auto()   # goto label
    IF_GOTO      = auto()   # if arg1 goto label
    IF_FALSE     = auto()   # ifFalse arg1 goto label
    PARAM        = auto()   # param arg1
    CALL         = auto()   # result = call func, n_args
    RETURN       = auto()   # return [arg1]
    ARRAY_LOAD   = auto()   # result = arg1[arg2]
    ARRAY_STORE  = auto()   # arg1[arg2] = result
    MEMBER_LOAD  = auto()   # result = arg1.member
    MEMBER_STORE = auto()   # arg1.member = result
    ADDR_OF      = auto()   # result = &arg1
    DEREF_LOAD   = auto()   # result = *arg1
    DEREF_STORE  = auto()   # *arg1 = result
    FUNC_BEGIN   = auto()   # func_begin name
    FUNC_END     = auto()   # func_end name
    NOP          = auto()   # no operation (for dead code elimination)


# =============================================================================
# TAC Instruction
# =============================================================================

@dataclass
class TACInstruction:
    """A single Three Address Code instruction.
    
    Attributes:
        op: The operation type (TACOp enum)
        result: The destination/result operand (variable or temp name)
        arg1: The first source operand
        arg2: The second source operand (for binary operations)
        label: Label name (for LABEL, GOTO, IF_GOTO, IF_FALSE)
        func_name: Function name (for CALL, FUNC_BEGIN, FUNC_END)
        member: Struct member name (for MEMBER_LOAD, MEMBER_STORE)
        operator: The operator string for BINOP/UNOP ('+', '-', '*', etc.)
        source_line: Original source line number for debugging
    """
    op: TACOp = TACOp.NOP
    result: Optional[str] = None
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    label: Optional[str] = None
    func_name: Optional[str] = None
    member: Optional[str] = None
    operator: Optional[str] = None
    source_line: int = 0

    def __str__(self) -> str:
        """Human-readable representation of this TAC instruction."""
        if self.op == TACOp.ASSIGN:
            return f"  {self.result} = {self.arg1}"
        elif self.op == TACOp.BINOP:
            return f"  {self.result} = {self.arg1} {self.operator} {self.arg2}"
        elif self.op == TACOp.UNOP:
            return f"  {self.result} = {self.operator}{self.arg1}"
        elif self.op == TACOp.LABEL:
            return f"{self.label}:"
        elif self.op == TACOp.GOTO:
            return f"  goto {self.label}"
        elif self.op == TACOp.IF_GOTO:
            return f"  if {self.arg1} goto {self.label}"
        elif self.op == TACOp.IF_FALSE:
            return f"  ifFalse {self.arg1} goto {self.label}"
        elif self.op == TACOp.PARAM:
            return f"  param {self.arg1}"
        elif self.op == TACOp.CALL:
            if self.result:
                return f"  {self.result} = call {self.func_name}, {self.arg1}"
            return f"  call {self.func_name}, {self.arg1}"
        elif self.op == TACOp.RETURN:
            if self.arg1:
                return f"  return {self.arg1}"
            return "  return"
        elif self.op == TACOp.ARRAY_LOAD:
            return f"  {self.result} = {self.arg1}[{self.arg2}]"
        elif self.op == TACOp.ARRAY_STORE:
            return f"  {self.arg1}[{self.arg2}] = {self.result}"
        elif self.op == TACOp.MEMBER_LOAD:
            return f"  {self.result} = {self.arg1}.{self.member}"
        elif self.op == TACOp.MEMBER_STORE:
            return f"  {self.arg1}.{self.member} = {self.result}"
        elif self.op == TACOp.ADDR_OF:
            return f"  {self.result} = &{self.arg1}"
        elif self.op == TACOp.DEREF_LOAD:
            return f"  {self.result} = *{self.arg1}"
        elif self.op == TACOp.DEREF_STORE:
            return f"  *{self.arg1} = {self.result}"
        elif self.op == TACOp.FUNC_BEGIN:
            return f"\nfunc_begin {self.func_name}"
        elif self.op == TACOp.FUNC_END:
            return f"func_end {self.func_name}\n"
        elif self.op == TACOp.NOP:
            return "  nop"
        return f"  <unknown: {self.op}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'op': self.op.name,
            'result': self.result,
            'arg1': self.arg1,
            'arg2': self.arg2,
            'label': self.label,
            'func_name': self.func_name,
            'member': self.member,
            'operator': self.operator,
            'source_line': self.source_line,
        }


# =============================================================================
# TAC Generator (AST Visitor)
# =============================================================================

class TACGenerator(ASTVisitor):
    """Generates Three Address Code from an AST.
    
    Walks the AST using the visitor pattern and emits TAC instructions
    into a linear list. Uses temporary variables (t0, t1, ...) for
    intermediate computations and labels (L0, L1, ...) for control flow.
    """

    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self._temp_counter: int = 0
        self._label_counter: int = 0
        self._current_function: Optional[str] = None

    def generate(self, program: Program) -> List[TACInstruction]:
        """Generate TAC for an entire program.
        
        Args:
            program: The root AST node (Program).
            
        Returns:
            List of TACInstruction objects.
        """
        self.instructions = []
        self._temp_counter = 0
        self._label_counter = 0
        program.accept(self)
        return self.instructions

    # ---- Helpers ----

    def _new_temp(self) -> str:
        """Generate a fresh temporary variable name."""
        name = f"t{self._temp_counter}"
        self._temp_counter += 1
        return name

    def _new_label(self) -> str:
        """Generate a fresh label name."""
        name = f"L{self._label_counter}"
        self._label_counter += 1
        return name

    def _emit(self, instr: TACInstruction):
        """Append an instruction to the output list."""
        self.instructions.append(instr)

    # ---- Visitors ----

    def visit_Program(self, node: Program):
        for decl in node.declarations:
            decl.accept(self)

    def visit_StructDef(self, node: StructDef):
        # Struct definitions don't generate TAC; they're metadata
        pass

    def visit_FunctionDef(self, node: FunctionDef):
        self._current_function = node.name
        self._emit(TACInstruction(
            op=TACOp.FUNC_BEGIN, func_name=node.name,
            source_line=node.line
        ))
        
        # Process function body
        if node.body:
            node.body.accept(self)
        
        self._emit(TACInstruction(
            op=TACOp.FUNC_END, func_name=node.name,
            source_line=node.line
        ))
        self._current_function = None

    def visit_VarDecl(self, node: VarDecl):
        if node.init_value:
            # Generate code for the initializer and assign to the variable
            val = node.init_value.accept(self)
            self._emit(TACInstruction(
                op=TACOp.ASSIGN, result=node.name, arg1=str(val),
                source_line=node.line
            ))

    def visit_ArrayDecl(self, node: ArrayDecl):
        # Array declarations allocate space; no TAC needed for allocation
        # in our simplified model
        pass

    def visit_CompoundStmt(self, node: CompoundStmt):
        for item in node.items:
            item.accept(self)

    def visit_ExprStmt(self, node: ExprStmt):
        if node.expr:
            node.expr.accept(self)

    def visit_IfStmt(self, node: IfStmt):
        # Generate condition
        cond = node.condition.accept(self)
        
        if node.else_body:
            # if (cond) { then } else { else }
            else_label = self._new_label()
            end_label = self._new_label()
            
            self._emit(TACInstruction(
                op=TACOp.IF_FALSE, arg1=str(cond), label=else_label,
                source_line=node.line
            ))
            
            node.then_body.accept(self)
            self._emit(TACInstruction(op=TACOp.GOTO, label=end_label))
            
            self._emit(TACInstruction(op=TACOp.LABEL, label=else_label))
            node.else_body.accept(self)
            
            self._emit(TACInstruction(op=TACOp.LABEL, label=end_label))
        else:
            # if (cond) { then }
            end_label = self._new_label()
            
            self._emit(TACInstruction(
                op=TACOp.IF_FALSE, arg1=str(cond), label=end_label,
                source_line=node.line
            ))
            
            node.then_body.accept(self)
            self._emit(TACInstruction(op=TACOp.LABEL, label=end_label))

    def visit_WhileStmt(self, node: WhileStmt):
        loop_start = self._new_label()
        loop_end = self._new_label()
        
        self._emit(TACInstruction(op=TACOp.LABEL, label=loop_start))
        
        cond = node.condition.accept(self)
        self._emit(TACInstruction(
            op=TACOp.IF_FALSE, arg1=str(cond), label=loop_end,
            source_line=node.line
        ))
        
        node.body.accept(self)
        self._emit(TACInstruction(op=TACOp.GOTO, label=loop_start))
        
        self._emit(TACInstruction(op=TACOp.LABEL, label=loop_end))

    def visit_ForStmt(self, node: ForStmt):
        # for (init; cond; update) body
        # → init; L_start: if(!cond) goto L_end; body; update; goto L_start; L_end:
        
        if node.init:
            node.init.accept(self)
        
        loop_start = self._new_label()
        loop_end = self._new_label()
        
        self._emit(TACInstruction(op=TACOp.LABEL, label=loop_start))
        
        if node.condition:
            cond = node.condition.accept(self)
            self._emit(TACInstruction(
                op=TACOp.IF_FALSE, arg1=str(cond), label=loop_end,
                source_line=node.line
            ))
        
        node.body.accept(self)
        
        if node.update:
            node.update.accept(self)
        
        self._emit(TACInstruction(op=TACOp.GOTO, label=loop_start))
        self._emit(TACInstruction(op=TACOp.LABEL, label=loop_end))

    def visit_ReturnStmt(self, node: ReturnStmt):
        if node.value:
            val = node.value.accept(self)
            self._emit(TACInstruction(
                op=TACOp.RETURN, arg1=str(val),
                source_line=node.line
            ))
        else:
            self._emit(TACInstruction(
                op=TACOp.RETURN, source_line=node.line
            ))

    def visit_BinaryOp(self, node: BinaryOp) -> str:
        left = node.left.accept(self)
        right = node.right.accept(self)
        result = self._new_temp()
        
        self._emit(TACInstruction(
            op=TACOp.BINOP, result=result,
            arg1=str(left), arg2=str(right),
            operator=node.op, source_line=node.line
        ))
        return result

    def visit_UnaryOp(self, node: UnaryOp) -> str:
        operand = node.operand.accept(self)
        
        if node.op == '&':
            # Address-of
            result = self._new_temp()
            self._emit(TACInstruction(
                op=TACOp.ADDR_OF, result=result, arg1=str(operand),
                source_line=node.line
            ))
            return result
        elif node.op == '*':
            # Dereference
            result = self._new_temp()
            self._emit(TACInstruction(
                op=TACOp.DEREF_LOAD, result=result, arg1=str(operand),
                source_line=node.line
            ))
            return result
        else:
            # Negation (-) or logical NOT (!)
            result = self._new_temp()
            self._emit(TACInstruction(
                op=TACOp.UNOP, result=result,
                arg1=str(operand), operator=node.op,
                source_line=node.line
            ))
            return result

    def visit_Assignment(self, node: Assignment) -> str:
        value = node.value.accept(self)
        
        # Check if target is an array access
        if isinstance(node.target, ArrayAccess):
            array_name = node.target.array.accept(self)
            index = node.target.index.accept(self)
            self._emit(TACInstruction(
                op=TACOp.ARRAY_STORE, result=str(value),
                arg1=str(array_name), arg2=str(index),
                source_line=node.line
            ))
            return str(value)
        
        # Check if target is a struct member
        elif isinstance(node.target, StructAccess):
            struct = node.target.struct_expr.accept(self)
            self._emit(TACInstruction(
                op=TACOp.MEMBER_STORE, result=str(value),
                arg1=str(struct), member=node.target.member,
                source_line=node.line
            ))
            return str(value)
        
        # Check if target is a pointer dereference
        elif isinstance(node.target, UnaryOp) and node.target.op == '*':
            ptr = node.target.operand.accept(self)
            self._emit(TACInstruction(
                op=TACOp.DEREF_STORE, result=str(value), arg1=str(ptr),
                source_line=node.line
            ))
            return str(value)
        
        # Simple variable assignment
        else:
            target_name = node.target.accept(self)
            self._emit(TACInstruction(
                op=TACOp.ASSIGN, result=str(target_name), arg1=str(value),
                source_line=node.line
            ))
            return str(target_name)

    def visit_FunctionCall(self, node: FunctionCall) -> str:
        # Evaluate arguments and emit PARAM instructions
        args = []
        for arg in node.arguments:
            val = arg.accept(self)
            args.append(str(val))
        
        for arg_val in args:
            self._emit(TACInstruction(
                op=TACOp.PARAM, arg1=arg_val,
                source_line=node.line
            ))
        
        result = self._new_temp()
        self._emit(TACInstruction(
            op=TACOp.CALL, result=result,
            func_name=node.name, arg1=str(len(args)),
            source_line=node.line
        ))
        return result

    def visit_ArrayAccess(self, node: ArrayAccess) -> str:
        array = node.array.accept(self)
        index = node.index.accept(self)
        result = self._new_temp()
        
        self._emit(TACInstruction(
            op=TACOp.ARRAY_LOAD, result=result,
            arg1=str(array), arg2=str(index),
            source_line=node.line
        ))
        return result

    def visit_StructAccess(self, node: StructAccess) -> str:
        struct = node.struct_expr.accept(self)
        result = self._new_temp()
        
        self._emit(TACInstruction(
            op=TACOp.MEMBER_LOAD, result=result,
            arg1=str(struct), member=node.member,
            source_line=node.line
        ))
        return result

    def visit_Identifier(self, node: Identifier) -> str:
        return node.name

    def visit_IntLiteral(self, node: IntLiteral) -> str:
        return str(node.value)

    def visit_FloatLiteral(self, node: FloatLiteral) -> str:
        return str(node.value)

    def visit_StringLiteral(self, node: StringLiteral) -> str:
        return f'"{node.value}"'

    def generic_visit(self, node: ASTNode):
        """Fallback for unhandled node types."""
        pass


# =============================================================================
# Utility Functions
# =============================================================================

def format_tac(instructions: List[TACInstruction]) -> str:
    """Format a list of TAC instructions as a human-readable string.
    
    Args:
        instructions: List of TACInstruction objects.
        
    Returns:
        Formatted string showing each instruction.
    """
    return "\n".join(str(instr) for instr in instructions)


def tac_to_dicts(instructions: List[TACInstruction]) -> List[dict]:
    """Convert TAC instructions to a list of dictionaries for JSON.
    
    Args:
        instructions: List of TACInstruction objects.
        
    Returns:
        List of dictionaries representing each instruction.
    """
    return [instr.to_dict() for instr in instructions]


def count_instructions(instructions: List[TACInstruction]) -> dict:
    """Count various metrics about the TAC instructions.
    
    Args:
        instructions: List of TACInstruction objects.
        
    Returns:
        Dictionary with counts of different instruction types and metrics.
    """
    metrics = {
        'total_instructions': 0,
        'temp_variables': set(),
        'labels': 0,
        'assignments': 0,
        'binary_ops': 0,
        'unary_ops': 0,
        'branches': 0,
        'function_calls': 0,
        'array_ops': 0,
        'returns': 0,
    }
    
    for instr in instructions:
        if instr.op == TACOp.NOP:
            continue
        if instr.op in (TACOp.FUNC_BEGIN, TACOp.FUNC_END):
            continue
            
        metrics['total_instructions'] += 1
        
        # Track temp variables
        if instr.result and instr.result.startswith('t') and instr.result[1:].isdigit():
            metrics['temp_variables'].add(instr.result)
        
        if instr.op == TACOp.LABEL:
            metrics['labels'] += 1
        elif instr.op == TACOp.ASSIGN:
            metrics['assignments'] += 1
        elif instr.op == TACOp.BINOP:
            metrics['binary_ops'] += 1
        elif instr.op == TACOp.UNOP:
            metrics['unary_ops'] += 1
        elif instr.op in (TACOp.GOTO, TACOp.IF_GOTO, TACOp.IF_FALSE):
            metrics['branches'] += 1
        elif instr.op == TACOp.CALL:
            metrics['function_calls'] += 1
        elif instr.op in (TACOp.ARRAY_LOAD, TACOp.ARRAY_STORE):
            metrics['array_ops'] += 1
        elif instr.op == TACOp.RETURN:
            metrics['returns'] += 1
    
    # Convert set to count
    metrics['temp_variable_count'] = len(metrics['temp_variables'])
    metrics['temp_variables'] = sorted(metrics['temp_variables'])
    
    return metrics
