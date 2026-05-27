"""
Pseudo-Assembly Code Generator for Mini-C Compiler.

Translates Three Address Code (TAC) into a pseudo-assembly language
targeting a simplified register machine. This generates human-readable
assembly-like output for educational and comparison purposes.

Register Model:
    R0-R15: General-purpose registers
    SP:     Stack pointer
    FP:     Frame pointer
    RV:     Return value register

Instruction Set:
    LOAD Rd, addr       - Load from memory to register
    STORE addr, Rs      - Store from register to memory
    MOV Rd, Rs          - Register-to-register move
    MOVI Rd, imm        - Load immediate value
    ADD Rd, Rs1, Rs2    - Addition
    SUB Rd, Rs1, Rs2    - Subtraction
    MUL Rd, Rs1, Rs2    - Multiplication
    DIV Rd, Rs1, Rs2    - Division
    MOD Rd, Rs1, Rs2    - Modulo
    NEG Rd, Rs          - Negate
    NOT Rd, Rs          - Logical NOT
    CMP Rs1, Rs2        - Compare (sets flags)
    JMP label           - Unconditional jump
    JEQ label           - Jump if equal
    JNE label           - Jump if not equal
    JLT label           - Jump if less than
    JGT label           - Jump if greater than
    JLE label           - Jump if less or equal
    JGE label           - Jump if greater or equal
    JZ label            - Jump if zero
    JNZ label           - Jump if not zero
    PUSH Rs             - Push register onto stack
    POP Rd              - Pop from stack to register
    CALL label          - Call function
    RET                 - Return from function
    LABEL:              - Label definition
"""

from __future__ import annotations
import sys
import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Set

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ir.tac_generator import TACInstruction, TACOp


# =============================================================================
# Assembly Instruction
# =============================================================================

@dataclass
class AsmInstruction:
    """A single pseudo-assembly instruction."""
    opcode: str              # e.g., 'LOAD', 'ADD', 'JMP'
    operands: List[str]      # Operand list
    comment: str = ""        # Optional comment
    is_label: bool = False   # True if this is a label definition

    def __str__(self) -> str:
        if self.is_label:
            line = f"{self.opcode}:"
        else:
            ops = ", ".join(self.operands)
            line = f"    {self.opcode:8s} {ops}"
        
        if self.comment:
            padding = max(1, 40 - len(line))
            line += " " * padding + f"; {self.comment}"
        
        return line


# =============================================================================
# Register Allocator (Simple Linear Scan)
# =============================================================================

class RegisterAllocator:
    """Simple register allocator mapping temporaries to registers.
    
    Uses a straightforward mapping: each temp/variable gets a register
    from the pool. When registers run out, values are spilled to memory.
    """

    NUM_REGISTERS = 16  # R0-R15

    def __init__(self):
        self._reg_map: Dict[str, str] = {}
        self._next_reg: int = 0
        self._spilled: Set[str] = set()

    def get_register(self, name: str) -> str:
        """Get the register allocated to a variable/temp.
        
        Args:
            name: Variable or temporary name.
            
        Returns:
            Register name (e.g., 'R0') or memory reference for spilled values.
        """
        if name in self._reg_map:
            return self._reg_map[name]
        
        if self._next_reg < self.NUM_REGISTERS:
            reg = f"R{self._next_reg}"
            self._reg_map[name] = reg
            self._next_reg += 1
            return reg
        else:
            # Spill to memory (stack)
            self._spilled.add(name)
            return f"[SP+{name}]"  # Memory reference

    def is_spilled(self, name: str) -> bool:
        """Check if a variable is spilled to memory."""
        return name in self._spilled

    def reset(self):
        """Reset allocator for a new function."""
        self._reg_map = {}
        self._next_reg = 0
        self._spilled = set()


# =============================================================================
# Assembly Generator
# =============================================================================

class AsmGenerator:
    """Generates pseudo-assembly from Three Address Code.
    
    Translates each TAC instruction into one or more assembly instructions,
    handling register allocation, function calling conventions, and
    control flow.
    """

    def __init__(self):
        self.instructions: List[AsmInstruction] = []
        self.reg_alloc = RegisterAllocator()

    def generate(self, tac_instructions: List[TACInstruction]) -> List[AsmInstruction]:
        """Generate pseudo-assembly from TAC instructions.
        
        Args:
            tac_instructions: List of TAC instructions to translate.
            
        Returns:
            List of AsmInstruction objects.
        """
        self.instructions = []
        
        # Header
        self._emit_comment("═" * 50)
        self._emit_comment("Mini-C Compiler — Pseudo-Assembly Output")
        self._emit_comment("═" * 50)
        self._emit_blank()
        
        for tac in tac_instructions:
            self._translate(tac)
        
        return self.instructions

    def _emit(self, opcode: str, operands: List[str] = None, comment: str = ""):
        """Emit a single assembly instruction."""
        self.instructions.append(AsmInstruction(
            opcode=opcode, operands=operands or [], comment=comment
        ))

    def _emit_label(self, label: str, comment: str = ""):
        """Emit a label definition."""
        self.instructions.append(AsmInstruction(
            opcode=label, operands=[], comment=comment, is_label=True
        ))

    def _emit_comment(self, text: str):
        """Emit a comment-only line."""
        self.instructions.append(AsmInstruction(
            opcode="", operands=[], comment=text, is_label=True
        ))

    def _emit_blank(self):
        """Emit a blank line."""
        self.instructions.append(AsmInstruction(
            opcode="", operands=[], is_label=True
        ))

    def _is_immediate(self, value: str) -> bool:
        """Check if a value is an immediate (literal number)."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def _load_operand(self, value: str, target_reg: str) -> str:
        """Load an operand into a register, returning the register name.
        
        If the value is an immediate, uses MOVI.
        If it's a variable/temp, uses LOAD or returns its register.
        """
        if value is None:
            return target_reg
            
        if self._is_immediate(value):
            self._emit("MOVI", [target_reg, value], f"load immediate {value}")
            return target_reg
        else:
            reg = self.reg_alloc.get_register(value)
            if self.reg_alloc.is_spilled(value):
                self._emit("LOAD", [target_reg, reg], f"load spilled {value}")
                return target_reg
            return reg

    def _translate(self, tac: TACInstruction):
        """Translate a single TAC instruction to assembly."""
        
        if tac.op == TACOp.FUNC_BEGIN:
            self._emit_blank()
            self._emit_comment(f"Function: {tac.func_name}")
            self._emit_label(tac.func_name)
            self._emit("PUSH", ["FP"], "save frame pointer")
            self._emit("MOV", ["FP", "SP"], "set frame pointer")
            self.reg_alloc.reset()  # New register scope for each function

        elif tac.op == TACOp.FUNC_END:
            self._emit_label(f"_{tac.func_name}_end")
            self._emit("MOV", ["SP", "FP"], "restore stack pointer")
            self._emit("POP", ["FP"], "restore frame pointer")
            self._emit("RET", [], f"return from {tac.func_name}")
            self._emit_blank()

        elif tac.op == TACOp.ASSIGN:
            # result = arg1
            if self._is_immediate(tac.arg1):
                rd = self.reg_alloc.get_register(tac.result)
                self._emit("MOVI", [rd, tac.arg1], f"{tac.result} = {tac.arg1}")
            else:
                rs = self.reg_alloc.get_register(tac.arg1)
                rd = self.reg_alloc.get_register(tac.result)
                self._emit("MOV", [rd, rs], f"{tac.result} = {tac.arg1}")

        elif tac.op == TACOp.BINOP:
            # result = arg1 op arg2
            r1 = self._load_operand(tac.arg1, "R14")
            r2 = self._load_operand(tac.arg2, "R15")
            rd = self.reg_alloc.get_register(tac.result)
            
            op_map = {
                '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '%': 'MOD',
                '==': 'SEQ', '!=': 'SNE', '<': 'SLT', '>': 'SGT',
                '<=': 'SLE', '>=': 'SGE', '&&': 'AND', '||': 'OR'
            }
            asm_op = op_map.get(tac.operator, 'NOP')
            self._emit(asm_op, [rd, r1, r2],
                      f"{tac.result} = {tac.arg1} {tac.operator} {tac.arg2}")

        elif tac.op == TACOp.UNOP:
            # result = op arg1
            rs = self._load_operand(tac.arg1, "R14")
            rd = self.reg_alloc.get_register(tac.result)
            
            if tac.operator == '-':
                self._emit("NEG", [rd, rs], f"{tac.result} = -{tac.arg1}")
            elif tac.operator == '!':
                self._emit("NOT", [rd, rs], f"{tac.result} = !{tac.arg1}")

        elif tac.op == TACOp.LABEL:
            self._emit_label(tac.label)

        elif tac.op == TACOp.GOTO:
            self._emit("JMP", [tac.label], f"goto {tac.label}")

        elif tac.op == TACOp.IF_GOTO:
            rs = self._load_operand(tac.arg1, "R14")
            self._emit("JNZ", [rs, tac.label], f"if {tac.arg1} goto {tac.label}")

        elif tac.op == TACOp.IF_FALSE:
            rs = self._load_operand(tac.arg1, "R14")
            self._emit("JZ", [rs, tac.label], f"ifFalse {tac.arg1} goto {tac.label}")

        elif tac.op == TACOp.PARAM:
            rs = self._load_operand(tac.arg1, "R14")
            self._emit("PUSH", [rs], f"param {tac.arg1}")

        elif tac.op == TACOp.CALL:
            self._emit("CALL", [tac.func_name], f"call {tac.func_name}, {tac.arg1} args")
            if tac.result:
                rd = self.reg_alloc.get_register(tac.result)
                self._emit("MOV", [rd, "RV"], f"{tac.result} = return value")
            # Clean up parameters from stack
            if tac.arg1 and int(tac.arg1) > 0:
                self._emit("ADD", ["SP", "SP", str(int(tac.arg1) * 4)],
                          f"clean {tac.arg1} params")

        elif tac.op == TACOp.RETURN:
            if tac.arg1:
                rs = self._load_operand(tac.arg1, "R14")
                self._emit("MOV", ["RV", rs], f"return {tac.arg1}")
            self._emit("JMP", [f"_{self._get_current_func(tac)}_end"], "jump to epilogue")

        elif tac.op == TACOp.ARRAY_LOAD:
            # result = arg1[arg2]
            ra = self._load_operand(tac.arg1, "R14")
            ri = self._load_operand(tac.arg2, "R15")
            rd = self.reg_alloc.get_register(tac.result)
            self._emit("MUL", ["R15", ri, "4"], "index * element_size")
            self._emit("ADD", ["R15", ra, "R15"], "base + offset")
            self._emit("LOAD", [rd, "[R15]"], f"{tac.result} = {tac.arg1}[{tac.arg2}]")

        elif tac.op == TACOp.ARRAY_STORE:
            # arg1[arg2] = result
            ra = self._load_operand(tac.arg1, "R13")
            ri = self._load_operand(tac.arg2, "R14")
            rs = self._load_operand(tac.result, "R15")
            self._emit("MUL", ["R14", ri, "4"], "index * element_size")
            self._emit("ADD", ["R14", ra, "R14"], "base + offset")
            self._emit("STORE", ["[R14]", rs], f"{tac.arg1}[{tac.arg2}] = {tac.result}")

        elif tac.op == TACOp.ADDR_OF:
            rd = self.reg_alloc.get_register(tac.result)
            self._emit("LEA", [rd, tac.arg1], f"{tac.result} = &{tac.arg1}")

        elif tac.op == TACOp.DEREF_LOAD:
            rs = self._load_operand(tac.arg1, "R14")
            rd = self.reg_alloc.get_register(tac.result)
            self._emit("LOAD", [rd, f"[{rs}]"], f"{tac.result} = *{tac.arg1}")

        elif tac.op == TACOp.DEREF_STORE:
            rs = self._load_operand(tac.result, "R14")
            ra = self._load_operand(tac.arg1, "R15")
            self._emit("STORE", [f"[{ra}]", rs], f"*{tac.arg1} = {tac.result}")

        elif tac.op == TACOp.MEMBER_LOAD:
            rs = self._load_operand(tac.arg1, "R14")
            rd = self.reg_alloc.get_register(tac.result)
            self._emit("LOAD", [rd, f"[{rs}+{tac.member}]"],
                      f"{tac.result} = {tac.arg1}.{tac.member}")

        elif tac.op == TACOp.MEMBER_STORE:
            rs = self._load_operand(tac.result, "R14")
            ra = self._load_operand(tac.arg1, "R15")
            self._emit("STORE", [f"[{ra}+{tac.member}]", rs],
                      f"{tac.arg1}.{tac.member} = {tac.result}")

        elif tac.op == TACOp.NOP:
            self._emit("NOP", [], "no operation")

    def _get_current_func(self, tac: TACInstruction) -> str:
        """Find the function name for the current context by scanning backwards."""
        idx = self.instructions.__len__()  # approximate
        # Search backwards through TAC instructions for the nearest FUNC_BEGIN
        # For simplicity, we'll use a stored value
        for asm in reversed(self.instructions):
            if asm.is_label and not asm.opcode.startswith("_") and not asm.opcode.startswith("L"):
                if asm.opcode and asm.opcode not in ('', ):
                    return asm.opcode
        return "unknown"


# =============================================================================
# Utility Functions
# =============================================================================

def format_assembly(instructions: List[AsmInstruction]) -> str:
    """Format assembly instructions as a human-readable string.
    
    Args:
        instructions: List of AsmInstruction objects.
        
    Returns:
        Formatted assembly string.
    """
    return "\n".join(str(instr) for instr in instructions)


def count_asm_instructions(instructions: List[AsmInstruction]) -> dict:
    """Count assembly instruction metrics.
    
    Args:
        instructions: List of AsmInstruction objects.
        
    Returns:
        Dictionary with instruction counts.
    """
    total = 0
    loads = 0
    stores = 0
    branches = 0
    arithmetic = 0
    
    for instr in instructions:
        if instr.is_label or not instr.opcode:
            continue
        total += 1
        
        if instr.opcode in ('LOAD', 'MOVI'):
            loads += 1
        elif instr.opcode == 'STORE':
            stores += 1
        elif instr.opcode in ('JMP', 'JZ', 'JNZ', 'JEQ', 'JNE', 'JLT', 'JGT', 'JLE', 'JGE'):
            branches += 1
        elif instr.opcode in ('ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'NEG', 'NOT',
                             'SEQ', 'SNE', 'SLT', 'SGT', 'SLE', 'SGE', 'AND', 'OR'):
            arithmetic += 1
    
    return {
        'total_instructions': total,
        'loads': loads,
        'stores': stores,
        'branches': branches,
        'arithmetic': arithmetic,
        'other': total - loads - stores - branches - arithmetic,
    }
