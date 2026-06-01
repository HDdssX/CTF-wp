use base64::engine::general_purpose::STANDARD;
use base64::Engine;
use num_bigint::BigUint;
use num_traits::{One, ToPrimitive};
use std::env;
use std::time::Instant;

fn b64d_int(s: &str) -> BigUint {
    BigUint::from_bytes_be(&STANDARD.decode(s).expect("invalid base64"))
}

fn b64e_int(v: &BigUint) -> String {
    STANDARD.encode(v.to_bytes_be())
}

fn main() {
    let token = env::args().nth(1).expect("usage: pow_rust TOKEN");
    let parts = token.split('.').collect::<Vec<_>>();
    assert_eq!(parts.len(), 3);
    assert_eq!(parts[0], "s");

    let diff = b64d_int(parts[1]).to_usize().expect("difficulty too large");
    let mut x = b64d_int(parts[2]);
    let modulus = (BigUint::one() << 1279usize) - BigUint::one();
    let exponent = BigUint::one() << 1277usize;
    let one = BigUint::one();
    let start = Instant::now();

    for i in 0..diff {
        x = x.modpow(&exponent, &modulus) ^ &one;
        if i > 0 && i % 50_000 == 0 {
            eprintln!("pow {i}/{diff} {:.1}s", start.elapsed().as_secs_f64());
        }
    }

    eprintln!("pow done {diff} rounds in {:.1}s", start.elapsed().as_secs_f64());
    println!("s.{}", b64e_int(&x));
}
