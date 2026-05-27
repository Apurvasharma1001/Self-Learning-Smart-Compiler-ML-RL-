// factorial.mc — Iterative and recursive factorial
// Tests: recursion, iteration, comparison of two approaches, multiple functions

/* Recursive factorial */
int fact_recursive(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * fact_recursive(n - 1);
}

/* Iterative factorial */
int fact_iterative(int n) {
    int result = 1;
    for (int i = 2; i <= n; i = i + 1) {
        result = result * i;
    }
    return result;
}

int main() {
    int r1 = fact_recursive(10);     // 3628800
    int r2 = fact_iterative(10);     // 3628800

    // Both should be equal; return 0 if they match, 1 otherwise
    if (r1 == r2) {
        return 0;
    }
    return 1;
}
