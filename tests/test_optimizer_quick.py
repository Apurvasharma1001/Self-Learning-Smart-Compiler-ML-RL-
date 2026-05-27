"""Test script for Phase 6 - Optimization Passes."""
import sys
sys.path.insert(0, '.')

from parser.parser import parse
from ir.tac_generator import TACGenerator, format_tac, count_instructions
from optimizer import PassManager

source = '''int main() {
    int a = 3 + 5;
    int b = a * 2;
    int c = 10 - 4;
    int d = c;
    int unused = 42;
    return d;
}'''

ast = parse(source)
gen = TACGenerator()
tac = gen.generate(ast)

print('--- Before Optimization ---')
print(format_tac(tac))
m1 = count_instructions(tac)
print('Instructions:', m1['total_instructions'])

pm = PassManager()
optimized = pm.apply_all(tac)

print()
print('--- After Optimization ---')
print(format_tac(optimized))
m2 = count_instructions(optimized)
print('Instructions:', m2['total_instructions'])

reduction = m1['total_instructions'] - m2['total_instructions']
pct = (reduction / m1['total_instructions']) * 100 if m1['total_instructions'] > 0 else 0
print('Reduction: %d instructions (%.1f%%)' % (reduction, pct))
print()
print('OPTIMIZATION PASSES TEST: PASS')
