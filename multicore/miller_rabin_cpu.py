import time
import random
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import gmpy2

import sys

sys.set_int_max_str_digits(1500000)

def _worker_miller_rabin(args):
    """Worker function executed in parallel across CPU threads."""
    n_str, a_str, d_str, s = args
    n = gmpy2.mpz(n_str)
    a = gmpy2.mpz(a_str)
    d = gmpy2.mpz(d_str)
    
    # Modular exponentiation: x = a^d mod n (accelerated by GMP C-backend)
    x = gmpy2.powmod(a, d, n)
    if x == 1 or x == n - 1:
        return True
    for _ in range(s - 1):
        x = gmpy2.powmod(x, 2, n)
        if x == n - 1:
            return True
    return False

def is_prime_miller_rabin(n_mpz, k=2):
    """
    Parallel Miller-Rabin primality test for arbitrarily large integers.
    Takes full advantage of multi-core CPU and AVX2-accelerated GMP arithmetic.
    """
    if n_mpz < 2:
        return False
    if n_mpz == 2 or n_mpz == 3:
        return True
    if n_mpz % 2 == 0:
        return False
    
    # Write n - 1 as d * 2^s
    n_minus_1 = n_mpz - 1
    d = n_minus_1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
        
    n_str = str(n_mpz)
    d_str = str(d)
    
    # Generate k random bases between 2 and n - 2
    bases_args = []
    for _ in range(k):
        a = random.randint(2, int(n_mpz - 2))
        bases_args.append((n_str, str(a), d_str, s))
        
    # Utilize all available CPU threads (12 threads on Intel i7-10750H)
    num_workers = min(multiprocessing.cpu_count(), k)
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(_worker_miller_rabin, bases_args))
        
    return all(results)


def get_number_from_file() -> int:
    number = 1
    with open("/home/mahbub/Projects/primes/carmichael.txt", "r") as file:
        number = int(file.read().strip())

    return number



if __name__ == "__main__":
    # Generate base 600-digit number near 10^599 and find next prime using GMP
    # base_num = gmpy2.mpz(10)**599
    # prime_600 = gmpy2.next_prime(base_num)

    test_number = get_number_from_file()
    
    print(f"Number of digits: {len(str(test_number))}")
    print(f"Number (truncated): {str(test_number)[:40]}...{str(test_number)[-40:]}")
    
    print(f"\nRunning Miller-Rabin primality test across {multiprocessing.cpu_count()} CPU threads (k=2 bases)...")
    start_time = time.time()
    
    is_prime = is_prime_miller_rabin(test_number, k=2)
    
    elapsed = time.time() - start_time
    print(f"Result: Is Prime? {is_prime}")
    print(f"Execution Time: {elapsed:.4f} seconds")

