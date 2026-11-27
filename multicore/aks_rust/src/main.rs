use rayon::prelude::*;
use rug::Integer;
use std::error::Error;
use std::fs;
use std::path::Path;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

use rug::Complete;

fn is_perfect_power(n: &Integer) -> bool {
    if *n <= 3 {
        return false;
    }
    let max_b = n.significant_bits();
    for b in 2..=max_b {
        let (root, rem): (Integer, Integer) = n.root_rem_ref(b).complete();
        if rem == 0 && root >= 2 {
            return true;
        }
    }
    false
}

fn multiplicative_order(n: &Integer, r: u64) -> u64 {
    let r_int = Integer::from(r);
    if Integer::from(n.gcd_ref(&r_int)) > 1 {
        return 0;
    }
    let mut k: u64 = 1;
    let n_mod_r = Integer::from(n % &r_int).to_u64().unwrap_or(0) % r;
    let mut current = n_mod_r;
    while current != 1 {
        current = (current.saturating_mul(n_mod_r)) % r;
        k += 1;
        if k > r {
            return 0;
        }
    }
    k
}

fn find_r(n: &Integer) -> u64 {
    let log_n = n.significant_bits() as f64;
    let limit = (log_n * log_n) as u64;
    let mut r: u64 = 2;
    loop {
        let r_int = Integer::from(r);
        if Integer::from(n.gcd_ref(&r_int)) == 1 {
            let ord_val = multiplicative_order(n, r);
            if ord_val > limit {
                return r;
            }
        }
        r += 1;
    }
}

fn pack_poly(coeffs: &[Integer], bit_width: u32) -> Integer {
    let mut packed = Integer::from(0);
    for (i, c) in coeffs.iter().enumerate() {
        if *c != 0 {
            let shifted = Integer::from(c) << (i as u32 * bit_width);
            packed |= shifted;
        }
    }
    packed
}

fn unpack_and_reduce(
    packed: &Integer,
    r: usize,
    n: &Integer,
    bit_width: u32,
    mask: &Integer,
) -> Vec<Integer> {
    let mut res = vec![Integer::from(0); r];
    let total_terms = if r == 0 { 0 } else { 2 * r - 1 };
    for i in 0..total_terms {
        let shifted = Integer::from(packed >> (i as u32 * bit_width));
        let coeff: Integer = shifted & mask;
        if coeff != 0 {
            let idx = i % r;
            res[idx] = Integer::from(&res[idx] + &coeff) % n;
        }
    }
    res
}

fn poly_mul_mod_fast(
    p1: &[Integer],
    p2: &[Integer],
    r: usize,
    n: &Integer,
    bit_width: u32,
    mask: &Integer,
) -> Vec<Integer> {
    let int_p1 = pack_poly(p1, bit_width);
    let int_p2 = pack_poly(p2, bit_width);
    let prod: Integer = int_p1 * int_p2;
    unpack_and_reduce(&prod, r, n, bit_width, mask)
}

fn poly_pow_mod_fast(poly: &[Integer], exp: &Integer, r: usize, n: &Integer) -> Vec<Integer> {
    // Unreduced product coefficient is strictly < r * n^2
    let n_sq: Integer = Integer::from(n * n);
    let bound: Integer = Integer::from(r as u64) * n_sq;
    let bit_width: u32 = bound.significant_bits() + 2;
    let mask: Integer = (Integer::from(1) << bit_width) - 1;

    let mut result = vec![Integer::from(0); r];
    if r == 0 {
        return result;
    }
    result[0] = Integer::from(1) % n;

    let bits = exp.significant_bits();
    if bits == 0 {
        return result;
    }

    let base: Vec<Integer> = poly.iter().map(|c| Integer::from(c % n)).collect();
    let mut started = false;

    for i in (0..bits).rev() {
        if started {
            result = poly_mul_mod_fast(&result, &result, r, n, bit_width, &mask);
        }
        if exp.get_bit(i) {
            if !started {
                result = base.clone();
                started = true;
            } else {
                result = poly_mul_mod_fast(&result, &base, r, n, bit_width, &mask);
            }
        }
    }

    result
}

fn euler_phi(r: u64) -> u64 {
    let r_int = Integer::from(r);
    let mut phi_r = 0;
    for i in 1..=r {
        let i_int = Integer::from(i);
        if Integer::from(i_int.gcd_ref(&r_int)) == 1 {
            phi_r += 1;
        }
    }
    phi_r
}

fn read_rug_integer<P: AsRef<Path>>(path: P) -> Result<Integer, Box<dyn Error>> {
    let contents = fs::read_to_string(path)?;
    let number = Integer::from_str_radix(contents.trim(), 10)?;
    Ok(number)
}

fn main() -> Result<(), Box<dyn Error>> {
    println!("Initializing Optimized AKS Primality Test in Rust...");

    let test_num = read_rug_integer("/home/mahbub/Projects/primes/number.txt")?;
    println!("Testing number with {} digits...", test_num.to_string().len());

    let start = Instant::now();

    if test_num < 2 {
        println!("Result: Is Prime? false");
        println!("Execution Time: {:.4?}", start.elapsed());
        return Ok(());
    }

    if test_num == 2 || test_num == 3 {
        println!("Result: Is Prime? true");
        println!("Execution Time: {:.4?}", start.elapsed());
        return Ok(());
    }

    if is_perfect_power(&test_num) {
        println!("Result: Composite (Perfect Power)");
        println!("Execution Time: {:.4?}", start.elapsed());
        return Ok(());
    }

    println!("Finding parameter r...");
    let r = find_r(&test_num);
    println!("Found r = {}", r);

    let r_usize = r as usize;
    let max_a = std::cmp::min(r, test_num.to_u64().unwrap_or(u64::MAX));
    for a in 2..=max_a {
        let a_int = Integer::from(a);
        let g = Integer::from(test_num.gcd_ref(&a_int));
        if g > 1 && g < test_num {
            println!("Result: Composite (Found factor via GCD: {})", g);
            println!("Execution Time: {:.4?}", start.elapsed());
            return Ok(());
        }
    }

    if test_num <= r_usize {
        println!("Result: Is Prime? true");
        println!("Execution Time: {:.4?}", start.elapsed());
        return Ok(());
    }

    let log_n = test_num.significant_bits() as f64;
    let phi_r = euler_phi(r);
    let limit_u64 = (((phi_r as f64).sqrt() * log_n) as u64).max(1);

    let n_mod_r = Integer::from(&test_num % r_usize).to_u64().unwrap_or(0) as usize;
    let one_mod_n = Integer::from(1) % &test_num;
    let completed = AtomicU64::new(0);
    let report_step = (limit_u64 / 10).max(1);

    println!(
        "Running parallel congruence loop up to a = {} across CPU cores...",
        limit_u64
    );

    let is_prime = (1..=limit_u64).into_par_iter().all(|a| {
        let a_mod_n = Integer::from(a) % &test_num;

        let mut lhs_poly = vec![Integer::from(0); r_usize];
        lhs_poly[0] = a_mod_n.clone();
        if r_usize > 1 {
            lhs_poly[1] = one_mod_n.clone();
        } else {
            lhs_poly[0] = Integer::from(&lhs_poly[0] + &one_mod_n) % &test_num;
        }

        let lhs_res = poly_pow_mod_fast(&lhs_poly, &test_num, r_usize, &test_num);

        let mut rhs_res = vec![Integer::from(0); r_usize];
        rhs_res[n_mod_r] = Integer::from(&rhs_res[n_mod_r] + &one_mod_n) % &test_num;
        rhs_res[0] = Integer::from(&rhs_res[0] + &a_mod_n) % &test_num;

        let ok = lhs_res == rhs_res;
        let done = completed.fetch_add(1, Ordering::Relaxed) + 1;
        if done % report_step == 0 || done == limit_u64 {
            println!("   Progress: {}/{} checks...", done, limit_u64);
        }
        ok
    });

    let duration = start.elapsed();
    println!("Result: Is Prime? {}", is_prime);
    println!("Execution Time: {:.4?}", duration);

    Ok(())
}