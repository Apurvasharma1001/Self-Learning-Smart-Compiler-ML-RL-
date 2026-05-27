"""
Flask Web Application for Mini-C Compiler.

Provides a web-based interface for compiling Mini-C programs with:
- Code editor with syntax highlighting (CodeMirror)
- Three compilation modes: Normal, ML-Optimized, RL-Optimized
- Side-by-side comparison of IR (before/after optimization)
- Metrics dashboard with improvement percentages
- Sample program selector
"""

from __future__ import annotations
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify
from runtime.pipeline import CompilerPipeline

app = Flask(__name__)

# Initialize a shared pipeline instance
pipeline = CompilerPipeline(verbose=False)

# Sample programs for the dropdown selector
# Programs at the top demonstrate the MOST optimization impact
SAMPLE_PROGRAMS = {
    "print_demo": {
        "name": "\U0001f4e2 Print Demo (see Output tab!)",
        "code": """int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; i = i + 1) {
        result = result * i;
    }
    return result;
}

int main() {
    print(42);
    print(100 + 200);

    int x = factorial(5);
    print(x);

    for (int i = 1; i <= 5; i = i + 1) {
        print(factorial(i));
    }
    return x;
}"""
    },
    "constant_folding_demo": {
        "name": "\u2b50 Constant Folding (90% reduction!)",
        "code": """int main() {
    int a = 3 + 5;
    int b = 10 * 2;
    int c = a + b;
    int d = 100 / 4;
    int e = d + c;
    return e;
}"""
    },
    "dead_code_demo": {
        "name": "\u2b50 Dead Code Elimination (85% reduction!)",
        "code": """int main() {
    int used = 10;
    int dead1 = 20;
    int dead2 = 30;
    int dead3 = 40;
    int dead4 = 50;
    int dead5 = 60;
    return used;
}"""
    },
    "cse_demo": {
        "name": "\u2b50 Common Subexpression Elim (94% reduction!)",
        "code": """int main() {
    int a = 5;
    int b = 10;
    int x = a + b;
    int y = a + b;
    int z = a + b;
    int w = a * b;
    int v = a * b;
    return x + y + z + w + v;
}"""
    },
    "copy_chain_demo": {
        "name": "\u2b50 Copy Propagation (83% reduction!)",
        "code": """int main() {
    int original = 42;
    int copy1 = original;
    int copy2 = copy1;
    int copy3 = copy2;
    int copy4 = copy3;
    return copy4;
}"""
    },
    "mixed_optimization": {
        "name": "\u2b50 Mixed Optimization (83% reduction!)",
        "code": """int compute() {
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
}"""
    },
    "all_passes_demo": {
        "name": "\u2b50 All Passes Combined (big reduction!)",
        "code": """int main() {
    int a = 4 + 6;
    int b = a;
    int c = b;
    int d = c * 2;
    int e = c * 2;
    int unused1 = 99;
    int unused2 = 88;
    int unused3 = 77;
    int f = a + d;
    int g = a + d;
    int result = f + g;
    return result;
}"""
    },
    "fibonacci": {
        "name": "Fibonacci (Recursive)",
        "code": """int fib(int n) {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

int main() {
    int result = fib(10);
    return result;
}"""
    },
    "factorial": {
        "name": "Factorial (Iterative)",
        "code": """int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; i = i + 1) {
        result = result * i;
    }
    return result;
}

int main() {
    int f = factorial(5);
    return f;
}"""
    },
    "gcd": {
        "name": "GCD (While Loop)",
        "code": """int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int main() {
    int result = gcd(48, 18);
    return result;
}"""
    },
    "bubble_sort": {
        "name": "Bubble Sort (minimal optimization)",
        "code": """int main() {
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
}"""
    },
}



@app.route('/')
def index():
    """Serve the main compiler playground page."""
    return render_template('index.html')


@app.route('/compile', methods=['POST'])
def compile_code():
    """API endpoint to compile Mini-C source code.
    
    Expects JSON: { "code": "...", "mode": "normal"|"ml"|"rl" }
    Returns JSON: CompilationResult as dictionary.
    """
    data = request.get_json()
    source_code = data.get('code', '')
    mode = data.get('mode', 'normal')
    
    if not source_code.strip():
        return jsonify({
            'success': False,
            'errors': ['No source code provided'],
        })
    
    # Reset pipeline generators for fresh compilation
    from ir.tac_generator import TACGenerator
    from codegen.asm_generator import AsmGenerator
    pipeline.tac_gen = TACGenerator()
    pipeline.asm_gen = AsmGenerator()
    
    result = pipeline.compile(source_code, mode=mode)
    return jsonify(result.to_dict())


@app.route('/compare', methods=['POST'])
def compare_modes():
    """API endpoint to compile in all modes and compare.
    
    Expects JSON: { "code": "..." }
    Returns JSON: { "normal": {...}, "ml": {...}, "rl": {...} }
    """
    data = request.get_json()
    source_code = data.get('code', '')
    
    if not source_code.strip():
        return jsonify({
            'success': False,
            'errors': ['No source code provided'],
        })
    
    results = pipeline.compile_and_compare(source_code)
    return jsonify({
        mode: res.to_dict() for mode, res in results.items()
    })


@app.route('/samples')
def get_samples():
    """API endpoint to get available sample programs."""
    return jsonify(SAMPLE_PROGRAMS)


if __name__ == '__main__':
    print("Starting Mini-C Compiler Web Interface...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
