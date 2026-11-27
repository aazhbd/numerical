from concurrent.futures import ProcessPoolExecutor, as_completed
import math
import os
import time
import gmpy2


def is_perfect_power(n: gmpy2.mpz) -> bool:
    """Step 1: Check if n = a^b for integer b > 1."""
    if n <= 3:
        return False
    max_b = int(gmpy2.log2(n)) + 1
    for b in range(2, max_b + 1):
        _, exact = gmpy2.iroot(n, b)
        if exact:
            return True
    return False


def multiplicative_order(n: gmpy2.mpz, r: int) -> int:
    """Find the multiplicative order of n modulo r: ord_r(n)."""
    if gmpy2.gcd(n, r) > 1:
        return 0
    k = 1
    n_mod_r = int(n % r)
    current = n_mod_r
    while current != 1:
        current = (current * n_mod_r) % r
        k += 1
        if k > r:
            return 0
    return k


def find_r(n: gmpy2.mpz) -> int:
    """Step 2: Find the smallest r such that ord_r(n) > log2(n)^2."""
    log_n = float(gmpy2.log2(n))
    limit = int(log_n**2) + 1
    r = 2
    while True:
        if gmpy2.gcd(n, r) == 1:
            if multiplicative_order(n, r) > limit:
                return r
        r += 1


def pack_poly(coeffs: list[gmpy2.mpz], bit_width: int) -> gmpy2.mpz:
    """Pack polynomial coefficients into a single big integer (Kronecker substitution)."""
    packed = gmpy2.mpz(0)
    for i, c in enumerate(coeffs):
        if c:
            packed |= gmpy2.mpz(c) << (i * bit_width)
    return packed


def unpack_and_reduce(
    packed: gmpy2.mpz, r: int, n: gmpy2.mpz, bit_width: int, mask: gmpy2.mpz
) -> list[gmpy2.mpz]:
    """Unpack integer product back into coefficients mod (x^r - 1, n)."""
    res = [gmpy2.mpz(0)] * r
    # Product of two degree < r polynomials has degree < 2r - 1
    for i in range(2 * r - 1):
        coeff = (packed >> (i * bit_width)) & mask
        if coeff:
            idx = i % r
            res[idx] = (res[idx] + coeff) % n
    return res


def poly_mul_mod_fast(
    p1: list[gmpy2.mpz],
    p2: list[gmpy2.mpz],
    r: int,
    n: gmpy2.mpz,
    bit_width: int,
    mask: gmpy2.mpz,
) -> list[gmpy2.mpz]:
    """Fast polynomial multiplication mod (x^r - 1, n) using GMP integer multiplication."""
    int_p1 = pack_poly(p1, bit_width)
    int_p2 = pack_poly(p2, bit_width)
    prod = int_p1 * int_p2
    return unpack_and_reduce(prod, r, n, bit_width, mask)


def poly_pow_mod_fast(
    base_poly: list[gmpy2.mpz], exp: gmpy2.mpz, r: int, n: gmpy2.mpz
) -> list[gmpy2.mpz]:
    """Binary exponentiation for polynomials mod (x^r - 1, n)."""
    # Each unreduced product coefficient is < r * n^2
    max_coeff_bound = gmpy2.mpz(r) * (n * n)
    bit_width = int(gmpy2.log2(max_coeff_bound)) + 2
    mask = (gmpy2.mpz(1) << bit_width) - 1

    result = [gmpy2.mpz(0)] * r
    result[0] = gmpy2.mpz(1)
    base = [c % n for c in base_poly]

    # Iterate through bits of exp from LSB to MSB
    num_bits = exp.bit_length()
    for bit_idx in range(num_bits):
        if exp.bit_test(bit_idx):
            result = poly_mul_mod_fast(result, base, r, n, bit_width, mask)
        if bit_idx + 1 < num_bits:
            base = poly_mul_mod_fast(base, base, r, n, bit_width, mask)

    return result


def worker_check_congruence(
    args: tuple[str, int, int],
) -> tuple[int, bool]:
    """Worker checking (x + a)^n == x^n + a (mod x^r - 1, n)."""
    n_str, r, a = args
    n = gmpy2.mpz(n_str)

    # LHS: (x + a)^n mod (x^r - 1, n)
    lhs_poly = [gmpy2.mpz(0)] * r
    lhs_poly[0] = gmpy2.mpz(a) % n
    lhs_poly[1] = gmpy2.mpz(1)
    lhs_res = poly_pow_mod_fast(lhs_poly, n, r, n)

    # RHS: x^(n mod r) + a (mod n)
    rhs_res = [gmpy2.mpz(0)] * r
    n_mod_r = int(n % r)
    rhs_res[n_mod_r] = gmpy2.mpz(1)
    rhs_res[0] = (rhs_res[0] + gmpy2.mpz(a)) % n

    return a, (lhs_res == rhs_res)


def aks_primality_test(n_input: int | gmpy2.mpz) -> bool:
    """Optimized Full AKS Primality Test Algorithm."""
    n = gmpy2.mpz(n_input)

    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        print("-> Composite (Even number)")
        return False

    # Step 1: Perfect power check
    if is_perfect_power(n):
        print("-> Composite (Perfect Power)")
        return False

    # Step 2: Find smallest r with ord_r(n) > log2(n)^2
    print("-> Finding parameter r...")
    r = find_r(n)
    print(f"-> Found r = {r}")

    # Step 3: Check gcd(a, n) for 1 < a <= min(r, n)
    upper_gcd = min(r, int(n))
    for a in range(2, upper_gcd + 1):
        g = gmpy2.gcd(a, n)
        if 1 < g < n:
            print(f"-> Composite (Found factor via GCD: {g})")
            return False

    # Step 4: If n <= r, it is prime
    if n <= r:
        return True

    # Step 5: Parallel polynomial congruence checks
    log_n = float(gmpy2.log2(n))
    phi_r = sum(1 for i in range(1, r + 1) if gmpy2.gcd(i, r) == 1)
    limit = max(1, int(math.sqrt(phi_r) * log_n))

    # Utilize all 12 hardware threads on i7-10750H
    num_workers = min(12, os.cpu_count() or 6)
    print(
        f"-> Running AKS polynomial checks for a = 1..{limit} across {num_workers} threads..."
    )

    n_str = str(n)
    tasks = [(n_str, r, a) for a in range(1, limit + 1)]

    executor = ProcessPoolExecutor(max_workers=num_workers)
    try:
        futures = [
            executor.submit(worker_check_congruence, task) for task in tasks
        ]
        completed = 0
        report_interval = max(1, limit // 10)

        for fut in as_completed(futures):
            a_val, passed = fut.result()
            completed += 1
            if not passed:
                print(
                    f"-> Composite (Failed polynomial congruence at a = {a_val})"
                )
                executor.shutdown(wait=False, cancel_futures=True)
                return False
            if completed % report_interval == 0 or completed == limit:
                print(f"   Progress: {completed}/{limit} checks passed...")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    return True


def get_number_from_file(filepath: str = "/home/mahbub/Projects/primes/carmichael.txt") -> gmpy2.mpz:
    with open(filepath, "r", encoding="utf-8") as file:
        raw = file.read().strip()
        if not raw.isdigit():
            raise ValueError(f"Expected digits only in {filepath}, got: {raw[:30]!r}")
        return gmpy2.mpz(raw)


if __name__ == "__main__":
    print("Initializing Optimized AKS Primality Test...")
    test_num = get_number_from_file()
    print(f"Testing number ({len(str(test_num))} digits): {test_num}")

    start_time = time.perf_counter()
    result = aks_primality_test(test_num)
    elapsed = time.perf_counter() - start_time

    print(f"\nResult: Is Prime? {result}")
    print(f"Execution Time: {elapsed:.4f} seconds")