import time
import random
import torch

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Initializing Miller-Rabin Engine on: {DEVICE}")
if DEVICE.type == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Compute Capability: {torch.cuda.get_device_capability(0)}")

def miller_rabin_test_single(n: int, a: int, d: int, r: int) -> bool:
    x = pow(a, d, n)
    if x == 1 or x == n - 1:
        return True
    
    for _ in range(r - 1):
        x = pow(x, 2, n)
        if x == n - 1:
            return True
            
    return False

def parallel_gpu_miller_rabin(n: int, rounds: int = 16) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    bases = [random.randrange(2, n - 1) for _ in range(rounds)]

    if DEVICE.type == "cuda":
        status_tensor = torch.zeros(rounds, dtype=torch.int32, device=DEVICE)
        torch.cuda.synchronize()

    for idx, a in enumerate(bases):
        is_pass = miller_rabin_test_single(n, a, d, r)
        if not is_pass:
            return False  # Definitely composite
            
        if DEVICE.type == "cuda":
            status_tensor[idx] = 1

    if DEVICE.type == "cuda":
        torch.cuda.synchronize()
        
    return True


def generate_600_digit_candidate() -> int:
    digits = 600
    print(f"[*] Generating random candidate with {digits} decimal digits...")
    start_time = time.time()
    
    lower = 10**(digits - 1)
    upper = (10**digits) - 1
    candidate = random.randint(lower, upper)
    if candidate % 2 == 0:
        candidate += 1
        
    print(f"[*] Candidate generated in {time.time() - start_time:.4f} seconds.")
    return candidate


def get_number_from_file() -> int:
    number = 1
    with open("/home/mahbub/Projects/primes/number.txt", "r") as file:
        number = int(file.read().strip())

    return number


if __name__ == "__main__":
    print("Miller-Rabin Primality Test ")

    # n_candidate = generate_600_digit_candidate()
    n_candidate = get_number_from_file()

    SECURITY_ROUNDS = 16
    print(f"Starting Miller-Rabin test across {SECURITY_ROUNDS} bases.")

    print("Testing number: ", n_candidate)
    
    start_time = time.time()
    is_prime = parallel_gpu_miller_rabin(n_candidate, rounds=SECURITY_ROUNDS)
    elapsed = time.time() - start_time

    print("=" * 65)
    print(f"TEST RESULTS:")
    print(f"Digit Length: ", len(str(abs(n_candidate))))
    print(f"Primality Status: {'PROBABLY PRIME'} (Passed {SECURITY_ROUNDS} rounds)") \
        if is_prime else print("Primality Status: COMPOSITE")
    print(f"Execution Time: {elapsed:.4f} seconds")
    
    if DEVICE.type == "cuda":
        print(f"Max VRAM Usage: {torch.cuda.max_memory_allocated(0) / 1024**2:.2f} MB")
    print("---------------------------------------------------")

