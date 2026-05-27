"""
Compiler Pipeline for Mini-C.

Orchestrates the end-to-end compilation process:
    Source Code -> Lexer -> Parser -> AST -> TAC -> [Optimizer] -> Assembly -> Execute

Provides three compilation modes:
    1. Normal:  No optimization (baseline)
    2. ML:      ML model selects optimization passes
    3. RL:      RL agent selects optimization passes

Collects and compares metrics at each stage.
"""

from __future__ import annotations
import sys
import os
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexer.lexer import tokenize, format_tokens, build_lexer
from parser.parser import parse
from ast_nodes.nodes import ASTPrinter, Program
from ir.tac_generator import (
    TACGenerator, TACInstruction, format_tac, count_instructions, tac_to_dicts
)
from codegen.asm_generator import (
    AsmGenerator, format_assembly, count_asm_instructions
)


# =============================================================================
# Compilation Result
# =============================================================================

@dataclass
class CompilationResult:
    """Contains all outputs and metrics from a compilation run."""
    
    success: bool = False
    errors: List[str] = field(default_factory=list)
    mode: str = "normal"
    source_code: str = ""
    tokens: List[dict] = field(default_factory=list)
    token_count: int = 0
    ast_string: str = ""
    tac_original: str = ""
    tac_original_metrics: Dict[str, Any] = field(default_factory=dict)
    tac_optimized: str = ""
    tac_optimized_metrics: Dict[str, Any] = field(default_factory=dict)
    passes_applied: List[str] = field(default_factory=list)
    assembly: str = ""
    assembly_metrics: Dict[str, Any] = field(default_factory=dict)
    compile_time_ms: float = 0.0
    improvement: Dict[str, Any] = field(default_factory=dict)
    # Execution output (from interpreter)
    program_output: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'errors': self.errors,
            'mode': self.mode,
            'source_code': self.source_code,
            'token_count': self.token_count,
            'ast': self.ast_string,
            'tac_original': self.tac_original,
            'tac_original_metrics': self.tac_original_metrics,
            'tac_optimized': self.tac_optimized,
            'tac_optimized_metrics': self.tac_optimized_metrics,
            'passes_applied': self.passes_applied,
            'assembly': self.assembly,
            'assembly_metrics': self.assembly_metrics,
            'compile_time_ms': self.compile_time_ms,
            'improvement': self.improvement,
            'program_output': self.program_output,
        }


# =============================================================================
# Compiler Pipeline
# =============================================================================

class CompilerPipeline:
    """End-to-end Mini-C compiler pipeline.
    
    Usage:
        pipeline = CompilerPipeline()
        result = pipeline.compile(source_code, mode="normal")
        print(result.assembly)
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.tac_gen = TACGenerator()
        self.asm_gen = AsmGenerator()
        self._optimizer = None
        self._ml_model = None
        self._rl_agent = None

    def set_optimizer(self, optimizer):
        """Set the optimization pass manager."""
        self._optimizer = optimizer

    def set_ml_model(self, model):
        """Set the ML model for optimization selection."""
        self._ml_model = model

    def set_rl_agent(self, agent):
        """Set the RL agent for optimization selection."""
        self._rl_agent = agent

    def _auto_init(self):
        """Auto-initialize optimizer, ML model, and RL agent if needed."""
        if self._optimizer is None:
            try:
                from optimizer import PassManager
                self._optimizer = PassManager()
            except Exception:
                pass
        if self._ml_model is None:
            try:
                from optimizer.ml.model import OptimizationMLModel
                self._ml_model = OptimizationMLModel()
            except Exception:
                pass
        if self._rl_agent is None:
            try:
                from optimizer.rl.q_agent import CompilerRLAgent
                self._rl_agent = CompilerRLAgent()
            except Exception:
                pass

    def compile(self, source_code: str, mode: str = "normal") -> CompilationResult:
        """Compile Mini-C source code through the full pipeline.
        
        Args:
            source_code: The Mini-C source code string.
            mode: Compilation mode -- "normal", "ml", or "rl".
            
        Returns:
            CompilationResult with all outputs and metrics.
        """
        result = CompilationResult(source_code=source_code, mode=mode)
        start_time = time.time()

        try:
            # ---- Stage 1: Lexing ----
            if self.verbose:
                print("[Pipeline] Stage 1: Lexing...")
            tokens_list = tokenize(source_code)
            result.token_count = len(tokens_list)
            result.tokens = [
                {'type': t.type, 'value': str(t.value), 'line': t.lineno}
                for t in tokens_list
            ]
            if self.verbose:
                print(f"  -> {len(tokens_list)} tokens generated")

            # ---- Stage 2: Parsing -> AST ----
            if self.verbose:
                print("[Pipeline] Stage 2: Parsing...")
            ast = parse(source_code)
            printer = ASTPrinter()
            result.ast_string = printer.print_tree(ast)
            if self.verbose:
                print("  -> AST generated successfully")

            # ---- Stage 3: AST -> TAC (IR) ----
            if self.verbose:
                print("[Pipeline] Stage 3: Generating TAC...")
            tac_instructions = self.tac_gen.generate(ast)
            result.tac_original = format_tac(tac_instructions)
            result.tac_original_metrics = count_instructions(tac_instructions)
            if self.verbose:
                m = result.tac_original_metrics
                print(f"  -> {m['total_instructions']} TAC instructions")
                print(f"  -> {m['temp_variable_count']} temp variables")

            # ---- Stage 4: Optimization ----
            optimized_tac = tac_instructions

            if mode in ("ml", "rl"):
                self._auto_init()
                
                if self._optimizer:
                    if self.verbose:
                        print(f"[Pipeline] Stage 4: Optimization ({mode} mode)...")
                    
                    if mode == "ml" and self._ml_model:
                        passes = self._ml_model.select_passes(tac_instructions)
                    elif mode == "rl" and self._rl_agent:
                        passes = self._rl_agent.select_passes(tac_instructions)
                    else:
                        passes = self._optimizer.get_pass_names()
                    
                    optimized_tac = self._optimizer.apply_passes(tac_instructions, passes)
                    result.passes_applied = list(passes)
                    result.tac_optimized = format_tac(optimized_tac)
                    result.tac_optimized_metrics = count_instructions(optimized_tac)
                    
                    orig_count = result.tac_original_metrics['total_instructions']
                    opt_count = result.tac_optimized_metrics['total_instructions']
                    if orig_count > 0:
                        reduction = orig_count - opt_count
                        pct = (reduction / orig_count) * 100
                        result.improvement = {
                            'instruction_reduction': reduction,
                            'percentage': round(pct, 2),
                            'original_count': orig_count,
                            'optimized_count': opt_count,
                        }
                    
                    if self.verbose:
                        print(f"  -> Applied passes: {result.passes_applied}")
                        print(f"  -> {result.tac_optimized_metrics['total_instructions']} instructions after optimization")
                        if result.improvement:
                            print(f"  -> {result.improvement['percentage']}% reduction")

            # ---- Stage 5: Code Generation ----
            if self.verbose:
                print("[Pipeline] Stage 5: Code Generation...")
            asm_instructions = self.asm_gen.generate(optimized_tac)
            result.assembly = format_assembly(asm_instructions)
            result.assembly_metrics = count_asm_instructions(asm_instructions)
            if self.verbose:
                print(f"  -> {result.assembly_metrics['total_instructions']} assembly instructions")

            # ---- Stage 6: Execute (Interpret TAC) ----
            if self.verbose:
                print("[Pipeline] Stage 6: Executing...")
            try:
                from runtime.interpreter import TACInterpreter
                interp = TACInterpreter()
                result.program_output = interp.execute(optimized_tac)
                if self.verbose:
                    print(f"  -> Output: {result.program_output[:100]}")
            except Exception as e:
                result.program_output = "[Interpreter Error: %s]" % str(e)

            result.success = True

        except SyntaxError as e:
            result.errors.append(str(e))
            if self.verbose:
                print(f"[Pipeline] Syntax Error: {e}")

        except Exception as e:
            result.errors.append(f"Internal compiler error: {str(e)}")
            if self.verbose:
                print(f"[Pipeline] Internal Error: {e}")
                import traceback
                traceback.print_exc()

        result.compile_time_ms = round((time.time() - start_time) * 1000, 2)
        if self.verbose:
            status = 'succeeded' if result.success else 'failed'
            print(f"[Pipeline] Compilation {status} in {result.compile_time_ms}ms")

        return result

    def compile_and_compare(self, source_code: str) -> Dict[str, CompilationResult]:
        """Compile in all three modes and return comparison results."""
        self._auto_init()
        results = {}
        for mode in ["normal", "ml", "rl"]:
            self.tac_gen = TACGenerator()
            self.asm_gen = AsmGenerator()
            results[mode] = self.compile(source_code, mode=mode)
        return results
