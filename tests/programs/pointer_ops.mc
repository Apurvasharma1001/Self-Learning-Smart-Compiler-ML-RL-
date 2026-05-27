// pointer_ops.mc — Pointer operations
// Tests: pointer declaration, address-of (&), dereference (*), pointer parameters

/* Swap two integers via pointers */
void swap(int* a, int* b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

/* Increment a value through a pointer */
void increment(int* p) {
    *p = *p + 1;
}

/* Return the larger of two values via pointer to result */
void max_val(int a, int b, int* result) {
    if (a > b) {
        *result = a;
    } else {
        *result = b;
    }
}

int main() {
    int x = 10;
    int y = 20;

    // Pointer declaration and address-of
    int* px = &x;
    int* py = &y;

    // Dereference to read
    int val = *px;         // val = 10

    // Swap via pointers
    swap(&x, &y);
    // Now x = 20, y = 10

    // Increment via pointer
    increment(&x);
    // Now x = 21

    // Get max via output pointer
    int m = 0;
    max_val(x, y, &m);
    // m = 21 (since x=21 > y=10)

    return x + y + m;     // 21 + 10 + 21 = 52
}
