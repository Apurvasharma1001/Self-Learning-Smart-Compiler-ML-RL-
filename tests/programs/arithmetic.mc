// arithmetic.mc — Basic arithmetic with integer and float variables
// Tests: variable declarations, assignment, +, -, *, /, % operators

int main() {
    // Integer arithmetic
    int a = 10;
    int b = 20;
    int c = a + b * 2;       // c = 50 (tests precedence: * before +)
    int d = (a + b) * 2;     // d = 60 (tests parenthesized grouping)
    int e = b / a;            // e = 2  (integer division)
    int f = b % 3;            // f = 2  (modulo)
    int g = a - b + c;       // g = 40 (left-to-right associativity)

    // Float arithmetic
    float pi = 3.14;
    float radius = 5.0;
    float area = pi * radius * radius;      // area = 78.5
    float half = area / 2.0;                // half = 39.25

    // Mixed int/float (int promoted to float)
    float mixed = a + pi;    // mixed = 13.14 (int a promoted to float)

    // Unary negation
    int neg = -a;             // neg = -10

    return c;
}
