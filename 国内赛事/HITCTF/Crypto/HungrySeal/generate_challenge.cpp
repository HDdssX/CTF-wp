#include "seal/seal.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <string>

using namespace std;
using namespace seal;
string flag = "";
void generate_challenge() {
    EncryptionParameters parms(scheme_type::ckks);
    size_t poly_modulus_degree = flag.size() * 2;
    parms.set_poly_modulus_degree(poly_modulus_degree);
    
    parms.set_coeff_modulus(CoeffModulus::Create(poly_modulus_degree, { 40, 40 }));
    
    SEALContext context(parms, true, sec_level_type::none);

    KeyGenerator keygen(context);
    SecretKey secret_key = keygen.secret_key();
    
    Encryptor encryptor(context, secret_key);
    CKKSEncoder encoder(context);


    vector<double> input;
    for(char c : flag) {
        input.push_back((double)c);
    }

    Plaintext plain;
    double scale = pow(2.0, 13);
    encoder.encode(input, scale, plain);

    Ciphertext encrypted;

    encryptor.encrypt_symmetric(plain, encrypted);


    ofstream fs("flag.enc", ios::binary);
    encrypted.save(fs);
    fs.close();

    cout << "Challenge generated: flag.enc" << endl;
}

int main() {
    generate_challenge();
    return 0;
}