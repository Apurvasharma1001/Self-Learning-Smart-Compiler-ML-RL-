"""Test the TAC interpreter with print support."""
import sys
sys.path.insert(0, '.')

from parser.parser import parse
from ir.tac_generator import TACGenerator, format_tac
from runtime.interpreter import TACInterpreter

def test_print():
    print("=" * 60)
    print("TEST: PRINT + INTERPRETER")
    print("=" * 60)
    
    source = '''int main() {
    int a = 3 + 5;
    int b = a * 2;
    int c = 10 - 4;
    
    print(a);
    print(b);
    print(c);
    print(a + b + c);
    
    return a + b;
}'''
    
    ast = parse(source)
    gen = TACGenerator()
    tac = gen.generate(ast)
    
    print("TAC:")
    print(format_tac(tac))
    
    interp = TACInterpreter()
    output = interp.execute(tac)
    
    print("\nProgram Output:")
    print(output)
    
    # Verify
    assert "8" in output, "Expected 8 (3+5)"
    assert "16" in output, "Expected 16 (8*2)"
    assert "6" in output, "Expected 6 (10-4)"
    assert "30" in output, "Expected 30 (8+16+6)"
    assert "[Program returned: 24]" in output, "Expected return 24"
    
    print("\nPRINT TEST: PASS")


def test_factorial():
    print("\n" + "=" * 60)
    print("TEST: FACTORIAL WITH PRINT")
    print("=" * 60)
    
    source = '''int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; i = i + 1) {
        result = result * i;
    }
    return result;
}

int main() {
    int f = factorial(5);
    print(f);
    return f;
}'''
    
    ast = parse(source)
    gen = TACGenerator()
    tac = gen.generate(ast)
    
    interp = TACInterpreter()
    output = interp.execute(tac)
    
    print("Output:", output)
    assert "120" in output, "Expected 120 (5!)"
    print("FACTORIAL PRINT TEST: PASS")


def test_loop_print():
    print("\n" + "=" * 60)
    print("TEST: LOOP WITH PRINT")
    print("=" * 60)
    
    source = '''int main() {
    for (int i = 1; i <= 5; i = i + 1) {
        print(i);
    }
    return 0;
}'''
    
    ast = parse(source)
    gen = TACGenerator()
    tac = gen.generate(ast)
    
    interp = TACInterpreter()
    output = interp.execute(tac)
    
    print("Output:", output)
    lines = [l for l in output.split('\n') if l and not l.startswith('[')]
    assert lines == ['1', '2', '3', '4', '5'], "Expected 1,2,3,4,5 but got %s" % lines
    print("LOOP PRINT TEST: PASS")


def test_fib_print():
    print("\n" + "=" * 60)
    print("TEST: FIBONACCI WITH PRINT")
    print("=" * 60)
    
    source = '''int fib(int n) {
    if (n <= 1) { return n; }
    return fib(n - 1) + fib(n - 2);
}

int main() {
    print(fib(10));
    return 0;
}'''
    
    ast = parse(source)
    gen = TACGenerator()
    tac = gen.generate(ast)
    
    interp = TACInterpreter()
    output = interp.execute(tac)
    
    print("Output:", output)
    assert "55" in output, "Expected fib(10)=55"
    print("FIB PRINT TEST: PASS")


if __name__ == '__main__':
    test_print()
    test_factorial()
    test_loop_print()
    test_fib_print()
    print("\n" + "=" * 60)
    print("ALL INTERPRETER TESTS PASSED!")
    print("=" * 60)
