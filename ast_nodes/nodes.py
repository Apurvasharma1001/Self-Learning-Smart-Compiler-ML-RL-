"""
AST Node Definitions for Mini-C Compiler.

This module defines all Abstract Syntax Tree (AST) node types using Python
dataclasses. The AST is the central intermediate representation between
parsing and IR generation.

Node Hierarchy:
    ASTNode (base)
    ├── Program
    ├── Declarations
    │   ├── VarDecl, ArrayDecl, StructDef, FunctionDef, ParamDecl
    ├── Statements
    │   ├── CompoundStmt, ExprStmt, IfStmt, WhileStmt, ForStmt, ReturnStmt
    ├── Expressions
    │   ├── BinaryOp, UnaryOp, Assignment
    │   ├── FunctionCall, ArrayAccess, StructAccess
    │   ├── Identifier, IntLiteral, FloatLiteral, StringLiteral
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Union


# =============================================================================
# Base Node
# =============================================================================

@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0       # Source line number for error reporting
    col: int = 0        # Source column number

    def accept(self, visitor):
        """Visitor pattern dispatch."""
        method_name = f"visit_{type(self).__name__}"
        visitor_method = getattr(visitor, method_name, visitor.generic_visit)
        return visitor_method(self)


# =============================================================================
# Type Specifications
# =============================================================================

@dataclass
class TypeSpec(ASTNode):
    """Type specification (e.g., int, float, void, struct Point, int*)."""
    base_type: str = ""           # 'int', 'float', 'void', or struct name
    is_pointer: bool = False       # True if this is a pointer type (e.g., int*)
    is_struct: bool = False        # True if base_type is a struct name
    is_array: bool = False         # True for array parameter types (e.g., int[])
    array_size: Optional[int] = None  # For array declarations

    def __str__(self) -> str:
        prefix = "struct " if self.is_struct else ""
        suffix = "*" if self.is_pointer else ""
        arr = f"[{self.array_size}]" if self.is_array and self.array_size else ("[]" if self.is_array else "")
        return f"{prefix}{self.base_type}{suffix}{arr}"


# =============================================================================
# Program (Root Node)
# =============================================================================

@dataclass
class Program(ASTNode):
    """Root node representing an entire Mini-C program."""
    declarations: List[ASTNode] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Program({len(self.declarations)} declarations)"


# =============================================================================
# Declarations
# =============================================================================

@dataclass
class VarDecl(ASTNode):
    """Variable declaration: type name [= init_expr];"""
    var_type: TypeSpec = field(default_factory=TypeSpec)
    name: str = ""
    init_value: Optional[ASTNode] = None  # Optional initializer expression

    def __str__(self) -> str:
        init = f" = {self.init_value}" if self.init_value else ""
        return f"VarDecl({self.var_type} {self.name}{init})"


@dataclass
class ArrayDecl(ASTNode):
    """Array declaration: type name[size];"""
    elem_type: TypeSpec = field(default_factory=TypeSpec)
    name: str = ""
    size: int = 0  # Compile-time constant size

    def __str__(self) -> str:
        return f"ArrayDecl({self.elem_type} {self.name}[{self.size}])"


@dataclass
class StructField(ASTNode):
    """A single field within a struct definition."""
    field_type: TypeSpec = field(default_factory=TypeSpec)
    name: str = ""
    array_size: Optional[int] = None  # If this field is an array

    def __str__(self) -> str:
        arr = f"[{self.array_size}]" if self.array_size else ""
        return f"{self.field_type} {self.name}{arr}"


@dataclass
class StructDef(ASTNode):
    """Struct type definition: struct Name { fields };"""
    name: str = ""
    fields: List[StructField] = field(default_factory=list)

    def __str__(self) -> str:
        return f"StructDef({self.name}, {len(self.fields)} fields)"


@dataclass
class ParamDecl(ASTNode):
    """Function parameter declaration."""
    param_type: TypeSpec = field(default_factory=TypeSpec)
    name: str = ""

    def __str__(self) -> str:
        return f"Param({self.param_type} {self.name})"


@dataclass
class FunctionDef(ASTNode):
    """Function definition: type name(params) { body }"""
    return_type: TypeSpec = field(default_factory=TypeSpec)
    name: str = ""
    params: List[ParamDecl] = field(default_factory=list)
    body: Optional[CompoundStmt] = None

    def __str__(self) -> str:
        params = ", ".join(str(p) for p in self.params)
        return f"FunctionDef({self.return_type} {self.name}({params}))"


# =============================================================================
# Statements
# =============================================================================

@dataclass
class CompoundStmt(ASTNode):
    """Block statement: { items... }"""
    items: List[ASTNode] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Block({len(self.items)} items)"


@dataclass
class ExprStmt(ASTNode):
    """Expression statement: expr;"""
    expr: Optional[ASTNode] = None  # None for empty statement (;)

    def __str__(self) -> str:
        return f"ExprStmt({self.expr})" if self.expr else "EmptyStmt"


@dataclass
class IfStmt(ASTNode):
    """If statement: if (cond) then_body [else else_body]"""
    condition: ASTNode = field(default_factory=ASTNode)
    then_body: ASTNode = field(default_factory=ASTNode)
    else_body: Optional[ASTNode] = None

    def __str__(self) -> str:
        els = " else {...}" if self.else_body else ""
        return f"IfStmt({self.condition}){els}"


@dataclass
class WhileStmt(ASTNode):
    """While loop: while (cond) body"""
    condition: ASTNode = field(default_factory=ASTNode)
    body: ASTNode = field(default_factory=ASTNode)

    def __str__(self) -> str:
        return f"WhileStmt({self.condition})"


@dataclass
class ForStmt(ASTNode):
    """For loop: for (init; cond; update) body"""
    init: Optional[ASTNode] = None       # Init clause (VarDecl or expression)
    condition: Optional[ASTNode] = None   # Loop condition
    update: Optional[ASTNode] = None      # Update expression
    body: ASTNode = field(default_factory=ASTNode)

    def __str__(self) -> str:
        return f"ForStmt(init={self.init}, cond={self.condition}, update={self.update})"


@dataclass
class ReturnStmt(ASTNode):
    """Return statement: return [expr];"""
    value: Optional[ASTNode] = None

    def __str__(self) -> str:
        return f"ReturnStmt({self.value})" if self.value else "ReturnStmt(void)"


# =============================================================================
# Expressions
# =============================================================================

@dataclass
class BinaryOp(ASTNode):
    """Binary operation: left op right"""
    op: str = ""          # '+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||'
    left: ASTNode = field(default_factory=ASTNode)
    right: ASTNode = field(default_factory=ASTNode)

    def __str__(self) -> str:
        return f"({self.left} {self.op} {self.right})"


@dataclass
class UnaryOp(ASTNode):
    """Unary operation: op operand"""
    op: str = ""          # '-', '!', '&', '*'
    operand: ASTNode = field(default_factory=ASTNode)

    def __str__(self) -> str:
        return f"({self.op}{self.operand})"


@dataclass
class Assignment(ASTNode):
    """Assignment: target = value"""
    target: ASTNode = field(default_factory=ASTNode)
    value: ASTNode = field(default_factory=ASTNode)

    def __str__(self) -> str:
        return f"({self.target} = {self.value})"


@dataclass
class FunctionCall(ASTNode):
    """Function call: name(args...)"""
    name: str = ""
    arguments: List[ASTNode] = field(default_factory=list)

    def __str__(self) -> str:
        args = ", ".join(str(a) for a in self.arguments)
        return f"{self.name}({args})"


@dataclass
class ArrayAccess(ASTNode):
    """Array subscript: array[index]"""
    array: ASTNode = field(default_factory=ASTNode)
    index: ASTNode = field(default_factory=ASTNode)

    def __str__(self) -> str:
        return f"{self.array}[{self.index}]"


@dataclass
class StructAccess(ASTNode):
    """Struct member access: struct_expr.member"""
    struct_expr: ASTNode = field(default_factory=ASTNode)
    member: str = ""

    def __str__(self) -> str:
        return f"{self.struct_expr}.{self.member}"


@dataclass
class Identifier(ASTNode):
    """Variable/identifier reference."""
    name: str = ""

    def __str__(self) -> str:
        return self.name


@dataclass
class IntLiteral(ASTNode):
    """Integer literal value."""
    value: int = 0

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class FloatLiteral(ASTNode):
    """Floating-point literal value."""
    value: float = 0.0

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class StringLiteral(ASTNode):
    """String literal value."""
    value: str = ""

    def __str__(self) -> str:
        return f'"{self.value}"'


# =============================================================================
# AST Visitor Base Class
# =============================================================================

class ASTVisitor:
    """Base visitor class for traversing the AST.
    
    Subclasses override visit_NodeType methods for specific node types.
    """

    def generic_visit(self, node: ASTNode):
        """Default handler for unimplemented node types."""
        raise NotImplementedError(
            f"No visit method for {type(node).__name__}"
        )

    def visit_children(self, node: ASTNode):
        """Visit all child nodes of a given node."""
        for attr_name in vars(node):
            attr = getattr(node, attr_name)
            if isinstance(attr, ASTNode):
                attr.accept(self)
            elif isinstance(attr, list):
                for item in attr:
                    if isinstance(item, ASTNode):
                        item.accept(self)


# =============================================================================
# AST Pretty Printer (for debugging)
# =============================================================================

class ASTPrinter(ASTVisitor):
    """Pretty-prints the AST as an indented tree."""

    def __init__(self):
        self.indent = 0
        self.lines: List[str] = []

    def _emit(self, text: str):
        self.lines.append("  " * self.indent + text)

    def print_tree(self, node: ASTNode) -> str:
        """Generate a pretty-printed string of the AST."""
        self.lines = []
        self.indent = 0
        node.accept(self)
        return "\n".join(self.lines)

    def visit_Program(self, node: Program):
        self._emit("Program")
        self.indent += 1
        for decl in node.declarations:
            decl.accept(self)
        self.indent -= 1

    def visit_FunctionDef(self, node: FunctionDef):
        params = ", ".join(f"{p.param_type} {p.name}" for p in node.params)
        self._emit(f"FunctionDef: {node.return_type} {node.name}({params})")
        self.indent += 1
        if node.body:
            node.body.accept(self)
        self.indent -= 1

    def visit_VarDecl(self, node: VarDecl):
        init = ""
        if node.init_value:
            init = f" = ..."
        self._emit(f"VarDecl: {node.var_type} {node.name}{init}")
        if node.init_value:
            self.indent += 1
            node.init_value.accept(self)
            self.indent -= 1

    def visit_ArrayDecl(self, node: ArrayDecl):
        self._emit(f"ArrayDecl: {node.elem_type} {node.name}[{node.size}]")

    def visit_StructDef(self, node: StructDef):
        self._emit(f"StructDef: {node.name}")
        self.indent += 1
        for f in node.fields:
            self._emit(f"Field: {f}")
        self.indent -= 1

    def visit_CompoundStmt(self, node: CompoundStmt):
        self._emit("Block")
        self.indent += 1
        for item in node.items:
            item.accept(self)
        self.indent -= 1

    def visit_ExprStmt(self, node: ExprStmt):
        self._emit("ExprStmt")
        if node.expr:
            self.indent += 1
            node.expr.accept(self)
            self.indent -= 1

    def visit_IfStmt(self, node: IfStmt):
        self._emit("IfStmt")
        self.indent += 1
        self._emit("Condition:")
        self.indent += 1
        node.condition.accept(self)
        self.indent -= 1
        self._emit("Then:")
        self.indent += 1
        node.then_body.accept(self)
        self.indent -= 1
        if node.else_body:
            self._emit("Else:")
            self.indent += 1
            node.else_body.accept(self)
            self.indent -= 1
        self.indent -= 1

    def visit_WhileStmt(self, node: WhileStmt):
        self._emit("WhileStmt")
        self.indent += 1
        self._emit("Condition:")
        self.indent += 1
        node.condition.accept(self)
        self.indent -= 1
        self._emit("Body:")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
        self.indent -= 1

    def visit_ForStmt(self, node: ForStmt):
        self._emit("ForStmt")
        self.indent += 1
        if node.init:
            self._emit("Init:")
            self.indent += 1
            node.init.accept(self)
            self.indent -= 1
        if node.condition:
            self._emit("Condition:")
            self.indent += 1
            node.condition.accept(self)
            self.indent -= 1
        if node.update:
            self._emit("Update:")
            self.indent += 1
            node.update.accept(self)
            self.indent -= 1
        self._emit("Body:")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
        self.indent -= 1

    def visit_ReturnStmt(self, node: ReturnStmt):
        self._emit("ReturnStmt")
        if node.value:
            self.indent += 1
            node.value.accept(self)
            self.indent -= 1

    def visit_BinaryOp(self, node: BinaryOp):
        self._emit(f"BinaryOp: {node.op}")
        self.indent += 1
        node.left.accept(self)
        node.right.accept(self)
        self.indent -= 1

    def visit_UnaryOp(self, node: UnaryOp):
        self._emit(f"UnaryOp: {node.op}")
        self.indent += 1
        node.operand.accept(self)
        self.indent -= 1

    def visit_Assignment(self, node: Assignment):
        self._emit("Assignment")
        self.indent += 1
        self._emit("Target:")
        self.indent += 1
        node.target.accept(self)
        self.indent -= 1
        self._emit("Value:")
        self.indent += 1
        node.value.accept(self)
        self.indent -= 1
        self.indent -= 1

    def visit_FunctionCall(self, node: FunctionCall):
        self._emit(f"FunctionCall: {node.name}")
        self.indent += 1
        for arg in node.arguments:
            arg.accept(self)
        self.indent -= 1

    def visit_ArrayAccess(self, node: ArrayAccess):
        self._emit("ArrayAccess")
        self.indent += 1
        node.array.accept(self)
        self._emit("Index:")
        self.indent += 1
        node.index.accept(self)
        self.indent -= 1
        self.indent -= 1

    def visit_StructAccess(self, node: StructAccess):
        self._emit(f"StructAccess: .{node.member}")
        self.indent += 1
        node.struct_expr.accept(self)
        self.indent -= 1

    def visit_Identifier(self, node: Identifier):
        self._emit(f"Identifier: {node.name}")

    def visit_IntLiteral(self, node: IntLiteral):
        self._emit(f"IntLiteral: {node.value}")

    def visit_FloatLiteral(self, node: FloatLiteral):
        self._emit(f"FloatLiteral: {node.value}")

    def visit_StringLiteral(self, node: StringLiteral):
        self._emit(f"StringLiteral: \"{node.value}\"")

    def generic_visit(self, node: ASTNode):
        self._emit(f"<{type(node).__name__}>")
