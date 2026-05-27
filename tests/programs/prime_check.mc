// prime_check.mc — Check if a number is prime
// Tests: for loop, modulo, early return, logical operators, function calls

int is_prime(int n) {
    if (n <= 1) {
        return 0;     // not prime
    }
    if (n <= 3) {
        return 1;     // 2 and 3 are prime
    }
    if (n % 2 == 0) {
        return 0;     // even numbers > 2 are not prime
    }

    // Check odd divisors up to sqrt(n)
    // Since we don't have sqrt, check i*i <= n
    for (int i = 3; i * i <= n; i = i + 2) {
        if (n % i == 0) {
            return 0;
        }
    }
    return 1;
}

/* Count primes up to a limit */
int count_primes(int limit) {
    int count = 0;
    for (int n = 2; n <= limit; n = n + 1) {
        if (is_prime(n)) {
            count = count + 1;
        }
    }
    return count;
}

int main() {
    // There are 25 primes less than or equal to 100
    int result = count_primes(100);
    return result;    // should be 25
}
