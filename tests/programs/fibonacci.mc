// fibonacci.mc — Recursive Fibonacci sequence
// Tests: recursive function calls, if-else, relational operators, return

int fib(int n) {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

int main() {
    int result = fib(10);     // result = 55
    return result;
}
