#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

using u8 = uint8_t;
using u32 = uint32_t;

static std::array<u32, 256> crc_table{};

static void init_crc_table() {
    for (u32 i = 0; i < 256; ++i) {
        u32 c = i;
        for (int j = 0; j < 8; ++j) {
            c = (c & 1) ? (0xedb88320u ^ (c >> 1)) : (c >> 1);
        }
        crc_table[i] = c;
    }
}

static inline u32 crc_update(u32 crc, u8 b) {
    return crc_table[(crc ^ b) & 0xffu] ^ (crc >> 8);
}

struct Keys {
    u32 k0 = 0x12345678u;
    u32 k1 = 0x23456789u;
    u32 k2 = 0x34567890u;

    inline void update(u8 p) {
        k0 = crc_update(k0, p);
        k1 = (k1 + (k0 & 0xffu)) * 134775813u + 1u;
        k2 = crc_update(k2, static_cast<u8>(k1 >> 24));
    }

    inline u8 decrypt_byte() const {
        u32 t = (k2 | 2u) & 0xffffu;
        return static_cast<u8>(((t * (t ^ 1u)) >> 8) & 0xffu);
    }
};

static constexpr std::array<u8, 12> enc_header = {
    0x5d, 0x81, 0x87, 0x1d, 0x8c, 0x4b, 0x2f, 0x2a, 0x4d, 0xaf, 0xf2, 0xf0
};

static constexpr std::array<u8, 20> enc_data = {
    0x3a, 0x1b, 0x95, 0x84, 0xf3, 0xb7, 0xa8, 0xc9, 0xbe, 0x77,
    0xcf, 0x1d, 0x92, 0x4a, 0xde, 0x9d, 0xeb, 0xe9, 0x95, 0xc3
};

static constexpr u8 check_byte = 0x75;
static constexpr u32 target_crc = 0x6f90de0fu;
static constexpr std::string_view prefix = "THEM?!CTF{";

static bool test_password(std::string_view password, std::string* plaintext_out = nullptr) {
    Keys keys;
    for (unsigned char ch : password) keys.update(ch);

    u8 p = 0;
    for (size_t i = 0; i < enc_header.size(); ++i) {
        p = enc_header[i] ^ keys.decrypt_byte();
        keys.update(p);
    }
    if (p != check_byte) return false;

    std::array<u8, enc_data.size()> plain{};
    for (size_t i = 0; i < enc_data.size(); ++i) {
        plain[i] = enc_data[i] ^ keys.decrypt_byte();
        keys.update(plain[i]);
        if (i < prefix.size() && plain[i] != static_cast<u8>(prefix[i])) return false;
    }
    if (plain.back() != static_cast<u8>('}')) return false;

    u32 crc = 0xffffffffu;
    for (u8 b : plain) crc = crc_update(crc, b);
    crc ^= 0xffffffffu;
    if (crc != target_crc) return false;

    if (plaintext_out) {
        plaintext_out->assign(reinterpret_cast<const char*>(plain.data()), plain.size());
    }
    return true;
}

static bool try_candidate(std::string_view s) {
    std::string plain;
    if (test_password(s, &plain)) {
        std::cout << "PASSWORD=" << s << "\n";
        std::cout << "PLAINTEXT=" << plain << "\n";
        return true;
    }
    return false;
}

static bool brute_charset(const std::string& charset, int min_len, int max_len) {
    std::string cur;
    uint64_t tested = 0;
    auto start = std::chrono::steady_clock::now();
    auto last = start;

    auto rec = [&](auto&& self, int len) -> bool {
        if (static_cast<int>(cur.size()) == len) {
            ++tested;
            if ((tested & 0xfffffu) == 0) {
                auto now = std::chrono::steady_clock::now();
                double sec = std::chrono::duration<double>(now - last).count();
                if (sec >= 2.0) {
                    double total = std::chrono::duration<double>(now - start).count();
                    std::cerr << "tested=" << tested << " rate=" << static_cast<uint64_t>(tested / std::max(total, 1e-9)) << "/s current=" << cur << "\n";
                    last = now;
                }
            }
            return try_candidate(cur);
        }
        for (char c : charset) {
            cur.push_back(c);
            if (self(self, len)) return true;
            cur.pop_back();
        }
        return false;
    };

    for (int len = min_len; len <= max_len; ++len) {
        cur.clear();
        std::cerr << "length " << len << "\n";
        if (rec(rec, len)) return true;
    }
    return false;
}

static std::vector<std::string> variants(const std::vector<std::string>& bases) {
    std::vector<std::string> out;
    for (const auto& b : bases) {
        out.push_back(b);
        std::string lower = b;
        std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
        out.push_back(lower);
        std::string upper = b;
        std::transform(upper.begin(), upper.end(), upper.begin(), [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
        out.push_back(upper);
        for (std::string s : {lower, upper, b}) {
            for (const auto& suffix : {"", "!", "!!", "?", "??", "123", "2026", "ctf", "CTF", "_", "-", "1"}) {
                out.push_back(s + suffix);
            }
        }
    }
    std::sort(out.begin(), out.end());
    out.erase(std::unique(out.begin(), out.end()), out.end());
    return out;
}

int main(int argc, char** argv) {
    init_crc_table();

    if (argc >= 2 && std::string_view(argv[1]) == "--test") {
        for (int i = 2; i < argc; ++i) {
            if (try_candidate(argv[i])) return 0;
        }
        return 1;
    }

    if (argc >= 3 && std::string_view(argv[1]) == "--wordlist") {
        std::ifstream in(argv[2], std::ios::binary);
        std::string line;
        while (std::getline(in, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            if (try_candidate(line)) return 0;
        }
        return 1;
    }

    std::vector<std::string> bases = {
        "hexdumb", "hexDumb", "h3xdumb", "hex_dumb", "h3x_dumb", "hexdump", "hex_dump",
        "zipcrypto", "zip_crypt", "ZipCrypto", "pkzip", "flag", "flagtxt", "flag.txt",
        "THEMCTF", "THEM?!CTF", "forensics", "knownplain", "known_plain", "plaintext",
        "ciphertext", "encrypted", "password", "crc32", "6f90de0f"
    };
    for (const auto& s : variants(bases)) {
        if (try_candidate(s)) return 0;
    }

    if (argc >= 5 && std::string_view(argv[1]) == "--brute") {
        return brute_charset(argv[2], std::stoi(argv[3]), std::stoi(argv[4])) ? 0 : 1;
    }

    return 1;
}
