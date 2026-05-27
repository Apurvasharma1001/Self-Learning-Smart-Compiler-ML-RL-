// bubble_sort.mc — Bubble Sort algorithm
// Tests: nested for loops, array element swapping, relational operators

void sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i = i + 1) {
        for (int j = 0; j < n - 1 - i; j = j + 1) {
            if (arr[j] > arr[j + 1]) {
                // Swap arr[j] and arr[j+1]
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

int main() {
    int data[8];
    data[0] = 64;
    data[1] = 34;
    data[2] = 25;
    data[3] = 12;
    data[4] = 22;
    data[5] = 11;
    data[6] = 90;
    data[7] = 1;

    sort(data, 8);

    // After sorting: 1, 11, 12, 22, 25, 34, 64, 90
    // Return smallest element to verify
    return data[0];    // should be 1
}
