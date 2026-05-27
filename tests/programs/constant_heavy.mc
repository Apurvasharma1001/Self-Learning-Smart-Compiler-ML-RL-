// constant_heavy.mc — Many constant expressions for constant folding testing
// Tests: constant propagation, constant folding, dead code elimination
// An optimizing compiler should reduce most of these at compile time

int main() {
    // ---- Pure constant expressions (should fold completely) ----
    int a = 2 + 3;                     // fold to 5
    int b = 10 * 20;                   // fold to 200
    int c = 100 / 4;                   // fold to 25
    int d = 17 % 5;                    // fold to 2
    int e = (3 + 4) * (5 - 2);        // fold to 21
    int f = 1 + 2 + 3 + 4 + 5;        // fold to 15

    // ---- Constant comparisons (should fold to 0 or 1) ----
    int g = 10 > 5;                    // fold to 1
    int h = 3 == 4;                    // fold to 0
    int i = 7 != 7;                    // fold to 0
    int j = 5 <= 5;                    // fold to 1

    // ---- Cascading constants (propagation then folding) ----
    int x = 10;
    int y = 20;
    int z = x + y;                     // propagate x=10, y=20 → fold to 30
    int w = z * 2;                     // propagate z=30 → fold to 60
    int v = w - z + x;                // propagate → fold to 60 - 30 + 10 = 40

    // ---- Dead code after constant condition ----
    int result = 0;
    if (1 > 0) {
        result = v + w;               // always taken → result = 40 + 60 = 100
    } else {
        result = -1;                   // dead code (never reached)
    }

    // ---- Constant loop bounds ----
    int sum = 0;
    for (int idx = 0; idx < 5; idx = idx + 1) {
        sum = sum + 10;                // loop runs 5 times → sum = 50
    }

    // ---- Algebraic identities (strength reduction opportunities) ----
    int p = a * 1;                     // identity: fold to a (= 5)
    int q = b + 0;                     // identity: fold to b (= 200)
    int r = c - 0;                     // identity: fold to c (= 25)
    int s = d * 0;                     // fold to 0

    // ---- Nested constant expressions ----
    int deep = ((2 + 3) * (4 + 5)) / (1 + 2);    // (5 * 9) / 3 = 15

    // Return a combination to prevent dead code elimination of everything
    return result + sum + p + q + r + s + deep;
    // = 100 + 50 + 5 + 200 + 25 + 0 + 15 = 395
}
