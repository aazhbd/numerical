import math
import time
import torch

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LIMB_BITS = 24
LIMB_BASE = 1 << LIMB_BITS
LIMB_MASK = LIMB_BASE - 1
NUM_LIMBS = 6  # Supports up to 144-bit exact integers


def int_to_limbs_1d(val: int, num_limbs: int = NUM_LIMBS) -> list[int]:
    """Convert non-negative Python int to little-endian base-2^24 limbs."""
    limbs = []
    x = val
    for _ in range(num_limbs):
        limbs.append(x & LIMB_MASK)
        x >>= LIMB_BITS
    if x != 0:
        raise ValueError(f"Integer {val} exceeds {num_limbs * LIMB_BITS}-bit limb capacity.")
    return limbs


def limbs_to_int_1d(limbs: list[int]) -> int:
    """Convert little-endian base-2^24 limbs back to Python int."""
    res = 0
    for shift_idx, limb in enumerate(limbs):
        res += int(limb) << (shift_idx * LIMB_BITS)
    return res


def normalize_limbs_batch(raw: torch.Tensor, num_limbs: int = NUM_LIMBS) -> torch.Tensor:
    """
    Normalize arbitrary int64 limb sums into canonical base-2^24 limbs [0, 2^24 - 1].
    Input shape: (..., num_limbs) with int64 values.
    """
    out = torch.empty_like(raw, dtype=torch.int64)
    carry = torch.zeros(raw.shape[:-1], dtype=torch.int64, device=raw.device)
    for i in range(num_limbs):
        total = raw[..., i] + carry
        out[..., i] = total & LIMB_MASK
        carry = total >> LIMB_BITS
    return out


def limbs_ge_batch(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """Elementwise comparison a >= b for normalized limb tensors (..., L)."""
    ge = torch.ones(a.shape[:-1], dtype=torch.bool, device=a.device)
    decided = torch.zeros(a.shape[:-1], dtype=torch.bool, device=a.device)
    for i in range(a.shape[-1] - 1, -1, -1):
        gt_here = (~decided) & (a[..., i] > b[..., i])
        lt_here = (~decided) & (a[..., i] < b[..., i])
        ge = torch.where(gt_here, True, torch.where(lt_here, False, ge))
        decided = decided | gt_here | lt_here
    return ge


def limbs_sub_batch(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """Exact subtraction a - b assuming a >= b on normalized base-2^24 limbs."""
    out = torch.empty_like(a, dtype=torch.int64)
    borrow = torch.zeros(a.shape[:-1], dtype=torch.int64, device=a.device)
    for i in range(a.shape[-1]):
        diff = a[..., i] - b[..., i] - borrow
        need_borrow = diff < 0
        out[..., i] = torch.where(need_borrow, diff + LIMB_BASE, diff)
        borrow = need_borrow.to(torch.int64)
    return out


def limbs_mod_n_batch(val: torch.Tensor, n_limbs_1d: list[int], n_int: int) -> torch.Tensor:
    """
    Exact modular reduction modulo n_int on GPU limb tensors (..., L).
    Uses repeated subtraction / shift-and-subtract for exactness without float loss.
    """
    # For small remainders after multiplication, convert to exact Python/CPU or shift-subtract
    # Here we use bit-by-bit / limb-by-limb reduction via exact big-int lookup or shift-subtract:
    # Since n is ~73 bits and L=6 (144 bits), val < (2^24)^6 = 2^144.
    # Shift-and-subtract over at most (144 - n.bit_length() + 1) steps is exact and fast.
    n_tensor = torch.tensor(n_limbs_1d, dtype=torch.int64, device=val.device).expand_as(val)
    cur = normalize_limbs_batch(val)

    # Fast path: subtract n_tensor while cur >= n_tensor (bounded)
    # For products of two mod-n numbers, val < n^2; we reduce cleanly using binary shifts.
    val_bits = NUM_LIMBS * LIMB_BITS
    n_bits = n_int.bit_length()
    max_shift = max(0, val_bits - n_bits)

    # Convert n_int shifted by k into limbs
    for shift in range(max_shift, -1, -1):
        shifted_n_int = n_int << shift
        # Only test shifts that could be <= max possible value
        if shifted_n_int >= (1 << val_bits):
            continue
        sn_limbs = torch.tensor(
            int_to_limbs_1d(shifted_n_int), dtype=torch.int64, device=val.device
        ).expand_as(cur)
        mask = limbs_ge_batch(cur, sn_limbs)
        if torch.any(mask):
            sub_val = limbs_sub_batch(cur, sn_limbs)
            cur = torch.where(mask.unsqueeze(-1), sub_val, cur)

    return cur


def limbs_mul_mod_n_batch(
    x: torch.Tensor, y: torch.Tensor, n_limbs_1d: list[int], n_int: int
) -> torch.Tensor:
    """
    Multiply two batched limb tensors x, y of shape (..., NUM_LIMBS) modulo n_int.
    Product has up to 2*NUM_LIMBS - 1 = 11 limbs; each partial product < 2^48.
    """
    prod_len = 2 * NUM_LIMBS
    prod = torch.zeros((*x.shape[:-1], prod_len), dtype=torch.int64, device=x.device)
    for i in range(NUM_LIMBS):
        xi = x[..., i].unsqueeze(-1)  # (..., 1)
        # Multiply xi by all y limbs at once
        term = xi * y  # (..., NUM_LIMBS), max value < 2^48
        for j in range(NUM_LIMBS):
            prod[..., i + j] = prod[..., i + j] + term[..., j]

    # Carry propagate across prod_len limbs
    norm_prod = normalize_limbs_batch(prod, num_limbs=prod_len)

    # Reduce 12-limb value mod n_int by splitting into high (6 limbs * 2^144) and low (6 limbs)
    low = norm_prod[..., :NUM_LIMBS]
    high = norm_prod[..., NUM_LIMBS:]

    # High part represents high_val * (2^144 mod n_int)
    base_144_mod_n = (1 << (NUM_LIMBS * LIMB_BITS)) % n_int
    high_int_shift = base_144_mod_n

    # Accumulate high limbs * base_144_mod_n + low
    acc = low.clone()
    cur_weight = high_int_shift % n_int
    for k in range(NUM_LIMBS):
        w_limbs = torch.tensor(
            int_to_limbs_1d(cur_weight), dtype=torch.int64, device=x.device
        ).expand_as(low)
        hk = high[..., k].unsqueeze(-1)
        # hk < 2^24, w_limbs < 2^24 -> hk * w_limbs < 2^48
        part = hk * w_limbs
        part_norm = normalize_limbs_batch(part, num_limbs=NUM_LIMBS)
        acc = normalize_limbs_batch(acc + part_norm, num_limbs=NUM_LIMBS)
        acc = limbs_mod_n_batch(acc, n_limbs_1d, n_int)
        cur_weight = (cur_weight * LIMB_BASE) % n_int

    return acc


def poly_mul_mod_cuda_batch(
    p1: torch.Tensor,
    p2: torch.Tensor,
    r: int,
    n_limbs_1d: list[int],
    n_int: int,
) -> torch.Tensor:
    """
    Batched polynomial multiplication mod (x^r - 1, n) on CUDA.
    p1, p2 shape: (B, r, NUM_LIMBS) where B is batch size (number of 'a' values in parallel).
    """
    batch_size = p1.shape[0]
    device = p1.device
    res = torch.zeros((batch_size, r, NUM_LIMBS), dtype=torch.int64, device=device)

    for i in range(r):
        p1_i = p1[:, i, :].unsqueeze(1).expand(batch_size, r, NUM_LIMBS)  # (B, r, L)
        prod_ij = limbs_mul_mod_n_batch(p1_i, p2, n_limbs_1d, n_int)  # (B, r, L)
        for j in range(r):
            deg = (i + j) % r
            summed = normalize_limbs_batch(res[:, deg, :] + prod_ij[:, j, :], NUM_LIMBS)
            res[:, deg, :] = limbs_mod_n_batch(summed, n_limbs_1d, n_int)

    return res


def poly_pow_mod_cuda_batch(
    base_poly: torch.Tensor,
    exp_int: int,
    r: int,
    n_limbs_1d: list[int],
    n_int: int,
) -> torch.Tensor:
    """
    Batched binary exponentiation of polynomials mod (x^r - 1, n) on CUDA.
    base_poly shape: (B, r, NUM_LIMBS).
    """
    batch_size = base_poly.shape[0]
    device = base_poly.device

    result = torch.zeros((batch_size, r, NUM_LIMBS), dtype=torch.int64, device=device)
    one_limbs = torch.tensor(int_to_limbs_1d(1 % n_int), dtype=torch.int64, device=device)
    result[:, 0, :] = one_limbs.unsqueeze(0).expand(batch_size, NUM_LIMBS)

    cur_base = base_poly.clone()
    bits = exp_int.bit_length()

    for bit_idx in range(bits - 1, -1, -1):
        result = poly_mul_mod_cuda_batch(result, result, r, n_limbs_1d, n_int)
        if (exp_int >> bit_idx) & 1:
            result = poly_mul_mod_cuda_batch(result, cur_base, r, n_limbs_1d, n_int)

    return result


def is_perfect_power(n: int) -> bool:
    if n < 4:
        return False
    for b in range(2, n.bit_length() + 1):
        low, high = 2, n
        while low <= high:
            mid = (low + high) // 2
            val = pow(mid, b)
            if val == n:
                return True
            if val < n:
                low = mid + 1
            else:
                high = mid - 1
    return False


def gcd_int(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def order_mod(n: int, r: int) -> int:
    if gcd_int(n, r) != 1:
        return -1
    k = 1
    n_mod_r = n % r
    curr = n_mod_r
    while curr != 1:
        curr = (curr * n_mod_r) % r
        k += 1
        if k > r:
            return -1
    return k


def find_r(n: int) -> int:
    log_n = float(n.bit_length())
    limit = int(log_n * log_n)
    r = 2
    while True:
        if gcd_int(n, r) == 1:
            if order_mod(n, r) > limit:
                return r
        r += 1


def euler_phi(r: int) -> int:
    return sum(1 for i in range(1, r + 1) if gcd_int(i, r) == 1)


def aks_cuda_test(n: int, batch_size: int = 32) -> str:
    if n < 2:
        return "COMPOSITE (< 2)"
    if n in (2, 3):
        return "PRIME"
    if n % 2 == 0:
        return "COMPOSITE (Even)"

    if is_perfect_power(n):
        return "COMPOSITE (Step 1: Perfect Power)"

    r = find_r(n)
    print(f"[*] Found AKS parameter r = {r}")

    for a in range(2, min(r, n - 1) + 1):
        g = gcd_int(a, n)
        if 1 < g < n:
            return f"COMPOSITE (Step 3: GCD({a}, n) = {g})"

    if n <= r:
        return "PRIME (Step 4: n <= r)"

    log_n = float(n.bit_length())
    phi_r = euler_phi(r)
    limit = max(1, int(math.sqrt(phi_r) * log_n))
    n_mod_r = n % r
    n_limbs_1d = int_to_limbs_1d(n)

    print(
        f"[*] Running batched CUDA congruence checks for a = 1..{limit} "
        f"(batch_size={batch_size}) on {DEVICE}..."
    )

    for start_a in range(1, limit + 1, batch_size):
        end_a = min(limit, start_a + batch_size - 1)
        a_values = list(range(start_a, end_a + 1))
        b_len = len(a_values)

        # Build LHS base polynomials (x + a) of shape (B, r, NUM_LIMBS)
        lhs_base = torch.zeros((b_len, r, NUM_LIMBS), dtype=torch.int64, device=DEVICE)
        one_limbs = torch.tensor(int_to_limbs_1d(1 % n), dtype=torch.int64, device=DEVICE)

        for idx, a_val in enumerate(a_values):
            a_limbs = torch.tensor(int_to_limbs_1d(a_val % n), dtype=torch.int64, device=DEVICE)
            lhs_base[idx, 0, :] = a_limbs
            if r > 1:
                lhs_base[idx, 1, :] = one_limbs
            else:
                lhs_base[idx, 0, :] = limbs_mod_n_batch(
                    normalize_limbs_batch(lhs_base[idx, 0, :] + one_limbs, NUM_LIMBS),
                    n_limbs_1d,
                    n,
                )

        lhs_res = poly_pow_mod_cuda_batch(lhs_base, n, r, n_limbs_1d, n)

        # Build RHS polynomials x^(n mod r) + a of shape (B, r, NUM_LIMBS)
        rhs_res = torch.zeros((b_len, r, NUM_LIMBS), dtype=torch.int64, device=DEVICE)
        for idx, a_val in enumerate(a_values):
            a_limbs = torch.tensor(int_to_limbs_1d(a_val % n), dtype=torch.int64, device=DEVICE)
            rhs_res[idx, n_mod_r, :] = limbs_mod_n_batch(
                normalize_limbs_batch(rhs_res[idx, n_mod_r, :] + one_limbs, NUM_LIMBS),
                n_limbs_1d,
                n,
            )
            rhs_res[idx, 0, :] = limbs_mod_n_batch(
                normalize_limbs_batch(rhs_res[idx, 0, :] + a_limbs, NUM_LIMBS),
                n_limbs_1d,
                n,
            )

        # Compare across all r coefficients and all limbs for each item in batch
        matches = torch.all((lhs_res == rhs_res).view(b_len, -1), dim=1)
        if not torch.all(matches):
            fail_idx = int(torch.nonzero(~matches, as_tuple=False)[0].item())
            return f"COMPOSITE (Step 5: Congruence failed at a = {a_values[fail_idx]})"

        if DEVICE.type == "cuda":
            torch.cuda.synchronize()
        print(f"   Progress: {end_a}/{limit} checks passed...")

    return "PRIME (Full AKS Verification Passed)"


def get_number_from_file(filepath: str = "/home/mahbub/Projects/primes/small.txt") -> int:
    with open(filepath, "r", encoding="utf-8") as file:
        return int(file.read().strip())


if __name__ == "__main__":
    print("=" * 60)
    print(f" CUDA AKS Primality Test on {DEVICE}")
    if DEVICE.type == "cuda":
        print(f" GPU: {torch.cuda.get_device_name(0)}")
    print("=" * 60)

    candidate = get_number_from_file()
    print(f"Testing number with {len(str(candidate))} digits...")

    t0 = time.perf_counter()
    verdict = aks_cuda_test(candidate, batch_size=4)
    elapsed = time.perf_counter() - t0

    print("=" * 60)
    print(f"RESULT    : {verdict}")
    print(f"TIME      : {elapsed:.4f}s")
    if DEVICE.type == "cuda":
        print(f"VRAM Used : {torch.cuda.memory_allocated(0) / (1024 ** 2):.2f} MB")
    print("=" * 60)