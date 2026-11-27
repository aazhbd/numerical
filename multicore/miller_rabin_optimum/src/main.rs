use rug::Integer;
use std::fs;
use std::time::Instant;

const MR_ROUNDS: usize = 2;

const SMALL_PRIMES: [u32; 25] = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
    53, 59, 61, 67, 71, 73, 79, 83, 89, 97,
];

struct InputNumber {
    value: Integer,
    digits: usize,
}

fn read_number(path: &str) -> Result<InputNumber, String> {
    let contents = fs::read_to_string(path)
        .map_err(|e| format!("Cannot read input file: {}", e))?;

    let input = contents.trim();
    if input.is_empty() {
        return Err("Input file is empty".to_string());
    }
    if !input.bytes().all(|b| b.is_ascii_digit()) {
        return Err("Input must contain only decimal digits".to_string());
    }

    let digits = input.len();
    let value = Integer::from_str_radix(input, 10)
        .map_err(|e| format!("Invalid integer: {}", e))?;

    Ok(InputNumber { value, digits })
}

struct WitnessSampler {
    bits: usize,
    bytes: Vec<u8>,
    upper_bound: Integer,
}

impl WitnessSampler {
    fn new(n: &Integer) -> Self {
        let bits = n.significant_bits() as usize;
        let byte_count = (bits + 7) / 8;
        let mut upper_bound = n.clone();
        upper_bound -= 3;

        Self {
            bits,
            bytes: vec![0u8; byte_count],
            upper_bound,
        }
    }

    fn next_witness(&mut self) -> Integer {
        let byte_count = self.bytes.len();
        let excess_bits = byte_count * 8 - self.bits;

        loop {
            getrandom::fill(&mut self.bytes)
                .expect("Failed to obtain secure random bytes");

            if excess_bits > 0 && byte_count > 0 {
                self.bytes[byte_count - 1] &= 0xFF >> excess_bits;
            }

            let candidate = Integer::from_digits(&self.bytes, rug::integer::Order::Lsf);
            if candidate < self.upper_bound {
                return candidate + 2;
            }
        }
    }
}

fn is_composite_witness(
    round_idx: usize,
    a: &Integer,
    n: &Integer,
    d: &Integer,
    s: u32,
    n_minus_one: &Integer,
) -> bool {
    let step_start = Instant::now();
    let mut x = a
        .clone()
        .pow_mod(d, n)
        .expect("Invalid modular exponentiation");
    println!(
        "  [Round {}] pow_mod finished in {:.2}s (s = {})",
        round_idx + 1,
        step_start.elapsed().as_secs_f64(),
        s
    );

    if x == 1 || x == *n_minus_one {
        return false;
    }

    for i in 1..s {
        x.square_mut();
        x %= n;

        if i % 10_000 == 0 {
            println!(
                "  [Round {}] squaring progress: {}/{} ({:.2}s elapsed)",
                round_idx + 1,
                i,
                s.saturating_sub(1),
                step_start.elapsed().as_secs_f64()
            );
        }

        if x == *n_minus_one {
            return false;
        }
        if x == 1 {
            return true;
        }
    }

    true
}

fn miller_rabin(n: &Integer, rounds: usize) -> bool {
    if n < &Integer::from(2) {
        return false;
    }

    for &p in SMALL_PRIMES.iter() {
        let prime = Integer::from(p);
        if n == &prime {
            return true;
        }
        if n.is_divisible_u(p) {
            return false;
        }
    }

    if n.is_even() {
        return false;
    }

    // Any nontrivial power a^b (b > 1) is composite
    if n.is_perfect_power() {
        println!("Detected perfect power -> COMPOSITE");
        return false;
    }

    let mut n_minus_one = n.clone();
    n_minus_one -= 1;

    let mut d = n_minus_one.clone();
    let mut s: u32 = 0;
    while d.is_even() {
        d >>= 1;
        s += 1;
    }

    let mut sampler = WitnessSampler::new(n);

    for round_idx in 0..rounds {
        let a = sampler.next_witness();
        if is_composite_witness(round_idx, &a, n, &d, s, &n_minus_one) {
            return false;
        }
    }

    true
}

fn main() {
    let total_start = Instant::now();
    let filename = "/home/mahbub/Projects/primes/carmichael.txt";

    println!("\nReading input file: {}", filename);
    let input = match read_number(filename) {
        Ok(value) => value,
        Err(error) => {
            eprintln!("ERROR: {}", error);
            std::process::exit(1);
        }
    };

    println!("Input digits: {}", input.digits);
    println!("Approx bits: {}", input.value.significant_bits());
    println!("Miller-Rabin rounds: {}", MR_ROUNDS);

    println!("\nStarting primality test...");
    let test_start = Instant::now();
    let is_prime = miller_rabin(&input.value, MR_ROUNDS);
    let test_duration = test_start.elapsed();

    if is_prime {
        println!("RESULT: PROBABLY PRIME");
    } else {
        println!("RESULT: COMPOSITE");
    }

    println!(
        "Primality test time: {:.3} seconds",
        test_duration.as_secs_f64()
    );
    println!(
        "Total execution time: {:.3} seconds",
        total_start.elapsed().as_secs_f64()
    );

    if is_prime {
        println!(
            "Worst-case random-base false-positive bound for {} rounds: 4^-{0} = 2^-{1}",
            MR_ROUNDS,
            MR_ROUNDS * 2
        );
    }
}