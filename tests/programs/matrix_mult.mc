// matrix_mult.mc — Simulated 2D matrix multiplication using 1D arrays
// Tests: triple-nested loops, array indexing with computed offsets, function params

/*
 * Matrices are stored in row-major order in a 1D array.
 * Element (i, j) of an N×N matrix is at index: i * N + j.
 *
 * C = A × B   where A is (N×N) and B is (N×N)
 */

void mat_mul(int A[], int B[], int C[], int N) {
    for (int i = 0; i < N; i = i + 1) {
        for (int j = 0; j < N; j = j + 1) {
            int sum = 0;
            for (int k = 0; k < N; k = k + 1) {
                sum = sum + A[i * N + k] * B[k * N + j];
            }
            C[i * N + j] = sum;
        }
    }
}

int main() {
    int N = 3;

    /* Matrix A (3×3):
     *   1 2 3
     *   4 5 6
     *   7 8 9
     */
    int A[9];
    A[0] = 1; A[1] = 2; A[2] = 3;
    A[3] = 4; A[4] = 5; A[5] = 6;
    A[6] = 7; A[7] = 8; A[8] = 9;

    /* Matrix B (3×3) — identity:
     *   1 0 0
     *   0 1 0
     *   0 0 1
     */
    int B[9];
    B[0] = 1; B[1] = 0; B[2] = 0;
    B[3] = 0; B[4] = 1; B[5] = 0;
    B[6] = 0; B[7] = 0; B[8] = 1;

    int C[9];

    mat_mul(A, B, C, N);

    // A × I = A, so C should equal A
    // Return C[0] + C[4] + C[8] = 1 + 5 + 9 = 15 (trace)
    int trace = C[0] + C[4] + C[8];
    return trace;
}
