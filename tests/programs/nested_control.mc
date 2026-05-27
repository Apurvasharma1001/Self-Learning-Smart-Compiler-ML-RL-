// nested_control.mc — Deeply nested control flow
// Tests: nested if-else, nested loops, complex conditions, variable shadowing
// Designed to stress-test control flow graph construction and optimization passes

int classify(int x) {
    /* Classify a number into categories using nested conditionals */
    int category = 0;

    if (x > 0) {
        if (x < 10) {
            category = 1;           // small positive
        } else {
            if (x < 100) {
                category = 2;       // medium positive
            } else {
                if (x < 1000) {
                    category = 3;   // large positive
                } else {
                    category = 4;   // very large positive
                }
            }
        }
    } else {
        if (x == 0) {
            category = 0;           // zero
        } else {
            if (x > -100) {
                category = -1;      // small negative
            } else {
                category = -2;      // large negative
            }
        }
    }

    return category;
}

int main() {
    int total = 0;

    // Nested loops: compute a triangular sum with conditional accumulation
    for (int i = 0; i < 10; i = i + 1) {
        for (int j = 0; j <= i; j = j + 1) {
            if (i % 2 == 0) {
                if (j % 2 == 0) {
                    total = total + i + j;
                } else {
                    total = total + i - j;
                }
            } else {
                if (j > i / 2) {
                    total = total + j;
                } else {
                    total = total - j;
                }
            }
        }
    }

    // Nested while loops
    int a = 5;
    int b = 3;
    int product = 0;
    while (a > 0) {
        int temp = b;
        while (temp > 0) {
            product = product + 1;
            temp = temp - 1;
        }
        a = a - 1;
    }
    // product = 5 * 3 = 15

    // Test classify with various inputs
    int c1 = classify(5);       // 1
    int c2 = classify(50);      // 2
    int c3 = classify(500);     // 3
    int c4 = classify(5000);    // 4
    int c5 = classify(0);       // 0
    int c6 = classify(-50);     // -1

    return total + product + c1 + c2 + c3 + c4 + c5 + c6;
}
