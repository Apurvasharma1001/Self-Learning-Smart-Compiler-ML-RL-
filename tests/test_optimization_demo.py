"""Diagnostic: test which programs show optimization impact."""
import sys
sys.path.insert(0, '.')

from parser.parser import parse
from ir.tac_generator import TACGenerator, format_tac, count_instructions
from optimizer import PassManager

programs = {
    "Constant Folding Demo": '''int main() {
    int a = 3 + 5;
    int b = 10 * 2;
    int c = a + b;
    int d = 100 / 4;
    int e = d + c;
    return e;
}''',
    "Dead Code Demo": '''int main() {
    int used = 10;
    int dead1 = 20;
    int dead2 = 30;
    int dead3 = 40;
    int dead4 = 50;
    int dead5 = 60;
    return used;
}''',
    "Copy Chain Demo": '''int main() {
    int original = 42;
    int copy1 = original;
    int copy2 = copy1;
    int copy3 = copy2;
    int copy4 = copy3;
    return copy4;
}''',
    "CSE Demo": '''int main() {
    int a = 5;
    int b = 10;
    int x = a + b;
    int y = a + b;
    int z = a + b;
    int w = a * b;
    int v = a * b;
    return x + y + z + w + v;
}''',
    "Mixed Optimization": '''int compute() {
    int a = 2 + 3;
    int b = a * 4;
    int c = b;
    int d = c;
    int unused1 = 100;
    int unused2 = 200;
    int e = a + b;
    int f = a + b;
    int result = d + e;
    return result;
}
int main() {
    int r = compute();
    return r;
}''',
    "Bubble Sort": '''int main() {
    int arr[5];
    arr[0] = 5;
    arr[1] = 3;
    arr[2] = 8;
    arr[3] = 1;
    arr[4] = 2;
    for (int i = 0; i < 4; i = i + 1) {
        for (int j = 0; j < 4 - i; j = j + 1) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
    return arr[0];
}''',
}

pm = PassManager()

print("%-25s | %5s | %5s | %6s" % ("Program", "Orig", "Opt", "Reduc."))
print("-" * 55)

for name, code in programs.items():
    try:
        ast = parse(code)
        gen = TACGenerator()
        tac = gen.generate(ast)
        orig = count_instructions(tac)['total_instructions']
        optimized = pm.apply_all(tac)
        opt = count_instructions(optimized)['total_instructions']
        pct = ((orig - opt) / orig * 100) if orig > 0 else 0
        print("%-25s | %5d | %5d | %5.1f%%" % (name, orig, opt, pct))
        
        if pct > 0:
            print("  BEFORE:")
            for line in format_tac(tac).strip().split('\n'):
                if line.strip():
                    print("    " + line)
            print("  AFTER:")
            for line in format_tac(optimized).strip().split('\n'):
                if line.strip():
                    print("    " + line)
            print()
    except Exception as e:
        print("%-25s | ERROR: %s" % (name, e))
