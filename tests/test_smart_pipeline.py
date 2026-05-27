"""Test Phases 6-9: Optimization + ML + RL + Smart Pipeline."""
import sys
sys.path.insert(0, '.')

def test_smart_pipeline():
    print('=' * 60)
    print('TEST: SMART PIPELINE (Normal vs ML vs RL)')
    print('=' * 60)
    
    from runtime.pipeline import CompilerPipeline
    
    source = '''int main() {
    int a = 3 + 5;
    int b = a * 2;
    int c = 10 - 4;
    int d = c;
    int unused = 42;
    int x = a + b;
    int y = a + b;
    return d;
}'''
    
    pipeline = CompilerPipeline(verbose=True)
    
    print('\n--- Mode: NORMAL ---')
    r_normal = pipeline.compile(source, mode='normal')
    assert r_normal.success, 'Normal compilation failed: ' + str(r_normal.errors)
    
    print('\n--- Mode: ML ---')
    pipeline.tac_gen = __import__('ir.tac_generator', fromlist=['TACGenerator']).TACGenerator()
    pipeline.asm_gen = __import__('codegen.asm_generator', fromlist=['AsmGenerator']).AsmGenerator()
    r_ml = pipeline.compile(source, mode='ml')
    assert r_ml.success, 'ML compilation failed: ' + str(r_ml.errors)
    
    print('\n--- Mode: RL ---')
    pipeline.tac_gen = __import__('ir.tac_generator', fromlist=['TACGenerator']).TACGenerator()
    pipeline.asm_gen = __import__('codegen.asm_generator', fromlist=['AsmGenerator']).AsmGenerator()
    r_rl = pipeline.compile(source, mode='rl')
    assert r_rl.success, 'RL compilation failed: ' + str(r_rl.errors)
    
    print('\n' + '=' * 60)
    print('COMPARISON RESULTS')
    print('=' * 60)
    normal_tac = r_normal.tac_original_metrics.get('total_instructions', 0)
    ml_tac = r_ml.tac_optimized_metrics.get('total_instructions', normal_tac)
    rl_tac = r_rl.tac_optimized_metrics.get('total_instructions', normal_tac)
    
    print('  Normal TAC instructions: %d' % normal_tac)
    print('  ML TAC instructions:     %d (passes: %s)' % (ml_tac, r_ml.passes_applied))
    print('  RL TAC instructions:     %d (passes: %s)' % (rl_tac, r_rl.passes_applied))
    
    if r_ml.improvement:
        print('  ML improvement: %.1f%%' % r_ml.improvement['percentage'])
    if r_rl.improvement:
        print('  RL improvement: %.1f%%' % r_rl.improvement['percentage'])
    
    print('\nSMART PIPELINE TEST: PASS')


def test_feature_extractor():
    print('\n' + '=' * 60)
    print('TEST: FEATURE EXTRACTOR')
    print('=' * 60)
    
    from parser.parser import parse
    from ir.tac_generator import TACGenerator
    from optimizer.ml.feature_extractor import IRFeatureExtractor
    
    source = '''int fib(int n) {
    if (n <= 1) { return n; }
    return fib(n - 1) + fib(n - 2);
}
int main() {
    int r = fib(10);
    return r;
}'''
    
    ast = parse(source)
    gen = TACGenerator()
    tac = gen.generate(ast)
    
    ext = IRFeatureExtractor()
    features = ext.extract(tac)
    vector = ext.to_vector(features)
    state = ext.discretize(features)
    
    print('  Features:', features)
    print('  Vector:', vector)
    print('  State:', state)
    print('\nFEATURE EXTRACTOR TEST: PASS')


if __name__ == '__main__':
    test_smart_pipeline()
    test_feature_extractor()
    print('\n' + '=' * 60)
    print('ALL PHASE 6-9 TESTS PASSED!')
    print('=' * 60)
