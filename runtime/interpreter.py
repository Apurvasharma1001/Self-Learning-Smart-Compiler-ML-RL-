"""
TAC Interpreter for Mini-C Compiler.

Executes Three Address Code instructions in a virtual environment and
captures output from `print()` calls. Supports:
    - Variable assignment and arithmetic
    - Function calls (including recursion)
    - Array operations
    - Control flow (if/goto, loops)
    - Built-in print() function

Usage:
    from runtime.interpreter import TACInterpreter
    interp = TACInterpreter()
    output = interp.execute(tac_instructions)
"""

from __future__ import annotations
import sys
import os
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ir.tac_generator import TACInstruction, TACOp


class TACInterpreter:
    """Interprets TAC instructions and captures print output."""

    MAX_STEPS = 100000  # Safety limit to prevent infinite loops

    def __init__(self):
        self.output_lines: List[str] = []
        self._global_env: Dict[str, Any] = {}
        self._functions: Dict[str, dict] = {}  # name -> {start_idx, end_idx}
        self._call_stack: List[dict] = []
        self._return_value: Any = None
        self._step_count: int = 0

    def execute(self, instructions: List[TACInstruction]) -> str:
        """Execute TAC instructions and return captured print output.

        Args:
            instructions: List of TAC instructions.

        Returns:
            String of all print outputs joined by newlines.
        """
        self.output_lines = []
        self._global_env = {}
        self._functions = {}
        self._call_stack = []
        self._return_value = None
        self._step_count = 0

        # Phase 1: Index all functions
        self._index_functions(instructions)

        # Phase 2: Execute main()
        if 'main' in self._functions:
            try:
                self._return_value = self._execute_function(
                    'main', [], instructions
                )
                # Show the return value of main
                if self._return_value is not None:
                    self.output_lines.append(
                        "[Program returned: %s]" % str(self._return_value)
                    )
            except _ReturnException as e:
                self._return_value = e.value
                if self._return_value is not None:
                    self.output_lines.append(
                        "[Program returned: %s]" % str(self._return_value)
                    )
            except RuntimeError as e:
                self.output_lines.append("[Runtime Error: %s]" % str(e))
        else:
            self.output_lines.append("[Error: No main() function found]")

        return "\n".join(self.output_lines)

    def _index_functions(self, instructions: List[TACInstruction]):
        """Build an index of function name -> (start_idx, end_idx)."""
        i = 0
        while i < len(instructions):
            instr = instructions[i]
            if instr.op == TACOp.FUNC_BEGIN:
                start = i
                name = instr.func_name
                # Find matching FUNC_END
                j = i + 1
                while j < len(instructions):
                    if (instructions[j].op == TACOp.FUNC_END and
                            instructions[j].func_name == name):
                        break
                    j += 1
                self._functions[name] = {'start': start, 'end': j}
                i = j + 1
            else:
                i += 1

    def _execute_function(
        self, func_name: str, args: List[Any],
        instructions: List[TACInstruction]
    ) -> Any:
        """Execute a function and return its return value."""
        if func_name not in self._functions:
            raise RuntimeError("Undefined function: %s" % func_name)

        func_info = self._functions[func_name]
        start_idx = func_info['start']
        end_idx = func_info['end']

        # Create local environment
        env: Dict[str, Any] = {}

        # Detect parameter names: variables read before being written
        # in the function body. These are the formal parameters.
        param_names = self._detect_params(instructions, start_idx, end_idx)

        # Bind args to param names
        for i, pname in enumerate(param_names):
            if i < len(args):
                env[pname] = args[i]
            else:
                env[pname] = 0

        # Build label index for this function
        label_map: Dict[str, int] = {}
        for idx in range(start_idx, end_idx + 1):
            instr = instructions[idx]
            if instr.op == TACOp.LABEL and instr.label:
                label_map[instr.label] = idx

        # Push call frame
        self._call_stack.append(env)

        try:
            pc = start_idx + 1  # Skip FUNC_BEGIN

            while pc < end_idx:
                self._step_count += 1
                if self._step_count > self.MAX_STEPS:
                    raise RuntimeError("Execution limit exceeded (possible infinite loop)")

                instr = instructions[pc]
                pc = self._execute_instruction(
                    instr, env, instructions, label_map, args, pc
                )

            return self._return_value

        except _ReturnException as e:
            return e.value
        finally:
            self._call_stack.pop()

    def _detect_params(
        self, instructions: List[TACInstruction],
        start_idx: int, end_idx: int
    ) -> List[str]:
        """Detect function parameter names by finding variables used before assignment."""
        defined = set()
        params = []
        seen_params = set()

        for idx in range(start_idx + 1, end_idx):
            instr = instructions[idx]

            # Check reads first (arg1, arg2)
            for arg in [instr.arg1, instr.arg2]:
                if arg and not self._is_literal(arg) and arg not in defined and arg not in seen_params:
                    # This variable is used before any assignment — it's a parameter
                    params.append(arg)
                    seen_params.add(arg)

            # Then mark definitions (result)
            if instr.result and instr.op not in (TACOp.LABEL, TACOp.GOTO,
                                                   TACOp.IF_GOTO, TACOp.IF_FALSE,
                                                   TACOp.FUNC_BEGIN, TACOp.FUNC_END,
                                                   TACOp.PARAM, TACOp.NOP):
                defined.add(instr.result)

        return params

    @staticmethod
    def _is_literal(value: str) -> bool:
        """Check if a value is a literal (number or string)."""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            pass
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            pass
        if value.startswith('"') and value.endswith('"'):
            return True
        return False

    def _execute_instruction(
        self, instr: TACInstruction, env: Dict[str, Any],
        instructions: List[TACInstruction],
        label_map: Dict[str, int],
        args: List[Any],
        pc: int,
    ) -> int:
        """Execute a single TAC instruction. Returns next pc."""

        if instr.op == TACOp.ASSIGN:
            val = self._resolve_value(instr.arg1, env)
            env[instr.result] = val
            return pc + 1

        elif instr.op == TACOp.BINOP:
            v1 = self._resolve_value(instr.arg1, env)
            v2 = self._resolve_value(instr.arg2, env)
            env[instr.result] = self._eval_binop(instr.operator, v1, v2)
            return pc + 1

        elif instr.op == TACOp.UNOP:
            v = self._resolve_value(instr.arg1, env)
            env[instr.result] = self._eval_unop(instr.operator, v)
            return pc + 1

        elif instr.op == TACOp.LABEL:
            return pc + 1

        elif instr.op == TACOp.GOTO:
            return label_map.get(instr.label, pc + 1)

        elif instr.op == TACOp.IF_GOTO:
            cond = self._resolve_value(instr.arg1, env)
            if cond:
                return label_map.get(instr.label, pc + 1)
            return pc + 1

        elif instr.op == TACOp.IF_FALSE:
            cond = self._resolve_value(instr.arg1, env)
            if not cond:
                return label_map.get(instr.label, pc + 1)
            return pc + 1

        elif instr.op == TACOp.PARAM:
            # Collect parameters for upcoming CALL
            val = self._resolve_value(instr.arg1, env)
            if '_pending_params' not in env:
                env['_pending_params'] = []
            env['_pending_params'].append(val)
            return pc + 1

        elif instr.op == TACOp.CALL:
            func_name = instr.func_name
            num_args = int(instr.arg1) if instr.arg1 else 0
            call_args = env.pop('_pending_params', [])

            # Handle built-in print
            if func_name == 'print':
                for a in call_args:
                    self.output_lines.append(str(a))
                if instr.result:
                    env[instr.result] = 0
                return pc + 1

            # Recursive/user function call
            ret = self._execute_function(func_name, call_args, instructions)
            if instr.result:
                env[instr.result] = ret
            return pc + 1

        elif instr.op == TACOp.RETURN:
            val = self._resolve_value(instr.arg1, env) if instr.arg1 else None
            self._return_value = val
            raise _ReturnException(val)

        elif instr.op == TACOp.ARRAY_STORE:
            # arg1[arg2] = result
            arr_name = instr.arg1
            idx = self._resolve_value(instr.arg2, env)
            val = self._resolve_value(instr.result, env)
            key = "%s[%s]" % (arr_name, int(idx))
            env[key] = val
            return pc + 1

        elif instr.op == TACOp.ARRAY_LOAD:
            # result = arg1[arg2]
            arr_name = instr.arg1
            idx = self._resolve_value(instr.arg2, env)
            key = "%s[%s]" % (arr_name, int(idx))
            env[instr.result] = env.get(key, 0)
            return pc + 1

        elif instr.op == TACOp.NOP:
            return pc + 1

        elif instr.op == TACOp.FUNC_BEGIN:
            return pc + 1

        elif instr.op == TACOp.FUNC_END:
            return pc + 1

        else:
            # Skip unknown instructions
            return pc + 1

    def _resolve_value(self, value: Optional[str], env: Dict[str, Any]) -> Any:
        """Resolve a TAC operand to its actual value."""
        if value is None:
            return 0
        # Try as integer
        try:
            return int(value)
        except (ValueError, TypeError):
            pass
        # Try as float
        try:
            return float(value)
        except (ValueError, TypeError):
            pass
        # Try as string literal
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        # Look up in local env, then walk call stack
        if value in env:
            return env[value]
        # Check parent scopes
        for frame in reversed(self._call_stack):
            if value in frame:
                return frame[value]
        # Default to 0 for uninitialized variables
        return 0

    @staticmethod
    def _eval_binop(op: str, left: Any, right: Any) -> Any:
        """Evaluate a binary operation."""
        # Ensure numeric types
        try:
            if op == '+': return left + right
            if op == '-': return left - right
            if op == '*': return left * right
            if op == '/':
                if right == 0: return 0
                if isinstance(left, int) and isinstance(right, int):
                    return left // right
                return left / right
            if op == '%':
                if right == 0: return 0
                return left % right
            if op == '==': return 1 if left == right else 0
            if op == '!=': return 1 if left != right else 0
            if op == '<':  return 1 if left < right else 0
            if op == '>':  return 1 if left > right else 0
            if op == '<=': return 1 if left <= right else 0
            if op == '>=': return 1 if left >= right else 0
            if op == '&&': return 1 if (left and right) else 0
            if op == '||': return 1 if (left or right) else 0
        except Exception:
            return 0
        return 0

    @staticmethod
    def _eval_unop(op: str, operand: Any) -> Any:
        """Evaluate a unary operation."""
        if op == '-': return -operand
        if op == '!': return 0 if operand else 1
        return operand


class _ReturnException(Exception):
    """Internal exception used to handle return statements."""
    def __init__(self, value: Any = None):
        self.value = value
