// gcd.mc — Greatest Common Divisor using Euclidean algorithm
// Tests: while loop, modulo operator, function calls, multiple returns

int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

/* Also compute LCM to exercise more arithmetic */
int lcm(int a, int b) {
    return a / gcd(a, b) * b;
}

int main() {
    int g1 = gcd(48, 18);     // g1 = 6
    int g2 = gcd(100, 75);    // g2 = 25
    int g3 = gcd(17, 13);     // g3 = 1  (coprime)

    int l = lcm(12, 18);      // l = 36

    return g1 + g2 + g3;      // 6 + 25 + 1 = 32
}
