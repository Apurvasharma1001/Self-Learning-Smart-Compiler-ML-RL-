"""
Quick End-to-End Test for the Mini-C Compiler Pipeline.
Tests Phases 2-5: Lexer → Parser → AST → TAC → Assembly.
"""

import sys
sys.path.insert(0, '.')

def test_lexer():
    print('=' * 60)
    print('TEST 1: LEXER')
    print('=' * 60)
    from lexer.lexer import tokenize, format_tokens

    source = '''int main() {
    int a = 10;
    int b = 20;
    int c = a + b * 2;
    return c;
}'''

    tokens = tokenize(source)
    print(f'Tokens generated: {len(tokens)}')
    print(format_tokens(tokens[:15]))
    print('... (truncated)')
    assert len(tokens) > 0, "No tokens generated"
    print('LEXER: PASS\n')
    return source

def test_parser(source):
    print('=' * 60)
    print('TEST 2: PARSER')
    print('=' * 60)
    from parser.parser import parse
    from ast_nodes.nodes import ASTPrinter

    ast = parse(source)
    printer = ASTPrinter()
    tree_str = printer.print_tree(ast)
    print(tree_str)
    assert ast is not None, "AST is None"
    print('PARSER: PASS\n')
    return ast

def test_tac(ast):
    print('=' * 60)
    print('TEST 3: TAC GENERATOR')
    print('=' * 60)
    from ir.tac_generator import TACGenerator, format_tac, count_instructions

    gen = TACGenerator()
    tac = gen.generate(ast)
    print(format_tac(tac))
    metrics = count_instructions(tac)
    total = metrics['total_instructions']
    temps = metrics['temp_variable_count']
    print(f'\nMetrics: {total} instructions, {temps} temps')
    assert total > 0, "No TAC instructions generated"
    print('TAC GENERATOR: PASS\n')
    return tac

def test_codegen(tac):
    print('=' * 60)
    print('TEST 4: ASSEMBLY GENERATOR')
    print('=' * 60)
    from codegen.asm_generator import AsmGenerator, format_assembly, count_asm_instructions

    asm_gen = AsmGenerator()
    asm = asm_gen.generate(tac)
    print(format_assembly(asm))
    asm_metrics = count_asm_instructions(asm)
    print(f'\nASM Metrics: {asm_metrics}')
    assert asm_metrics['total_instructions'] > 0, "No assembly generated"
    print('ASSEMBLY GENERATOR: PASS\n')

def test_pipeline():
    print('=' * 60)
    print('TEST 5: FULL PIPELINE')
    print('=' * 60)
    from runtime.pipeline import CompilerPipeline

    source = '''int add(int a, int b) {
    return a + b;
}
int main() {
    int x = 5;
    int y = 10;
    int z = add(x, y);
    return z;
}'''

    pipeline = CompilerPipeline(verbose=True)
    result = pipeline.compile(source, mode='normal')
    print(f'Success: {result.success}')
    print(f'Tokens: {result.token_count}')
    total_tac = result.tac_original_metrics.get('total_instructions', 0)
    total_asm = result.assembly_metrics.get('total_instructions', 0)
    print(f'TAC instructions: {total_tac}')
    print(f'ASM instructions: {total_asm}')
    print(f'Compile time: {result.compile_time_ms}ms')
    assert result.success, f"Compilation failed: {result.errors}"
    print('FULL PIPELINE: PASS\n')

def test_complex_program():
    print('=' * 60)
    print('TEST 6: COMPLEX PROGRAM (Fibonacci)')
    print('=' * 60)
    from runtime.pipeline import CompilerPipeline

    source = '''int fib(int n) {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}
int main() {
    int result = fib(10);
    return result;
}'''

    pipeline = CompilerPipeline(verbose=True)
    result = pipeline.compile(source, mode='normal')
    print(f'Success: {result.success}')
    assert result.success, f"Compilation failed: {result.errors}"
    
    print('\n--- TAC ---')
    print(result.tac_original)
    print('COMPLEX PROGRAM: PASS\n')


if __name__ == '__main__':
    source = test_lexer()
    ast = test_parser(source)
    tac = test_tac(ast)
    test_codegen(tac)
    test_pipeline()
    test_complex_program()
    
    print('=' * 60)
    print('ALL TESTS PASSED!')
    print('=' * 60)
