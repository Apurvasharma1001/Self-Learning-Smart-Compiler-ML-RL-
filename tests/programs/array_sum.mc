// array_sum.mc — Array initialization and summation
// Tests: array declaration, for loop, array indexing, accumulation

int main() {
    int arr[10];
    int n = 10;

    // Initialize array: arr[i] = i * i
    for (int i = 0; i < n; i = i + 1) {
        arr[i] = i * i;
    }

    // Compute sum of all elements
    int sum = 0;
    for (int j = 0; j < n; j = j + 1) {
        sum = sum + arr[j];
    }

    // sum = 0 + 1 + 4 + 9 + 16 + 25 + 36 + 49 + 64 + 81 = 285
    return sum;
}
