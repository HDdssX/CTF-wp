#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

using u8 = uint8_t;
using u32 = uint32_t;

static std::array<u32, 256> crc_table{};
static std::array<u32, 256> inv_table{};

static void init_crc() {
    for (u32 i = 0; i < 256; ++i) {
        u32 c = i;
        for (int j = 0; j < 8; ++j) c = (c & 1) ? (0xedb88320u ^ (c >> 1)) : (c >> 1);
        crc_table[i] = c;
        inv_table[c >> 24] = c;
    }
}

static inline u32 crc_update(u32 state, u8 b) {
    return crc_table[(state ^ b) & 0xffu] ^ (state >> 8);
}

static inline u32 crc_reverse(u32 next, u8 b) {
    u32 table_entry = inv_table[next >> 24];
    return ((next ^ table_entry) << 8) | ((table_entry ^ b) & 0xffu);
}

int main(int argc, char** argv) {
    init_crc();
    std::string alphabet = "abcdefghijklmnopqrstuvwxyz0123456789_";
    if (argc > 1) alphabet = argv[1];

    constexpr u32 target = 0x6f90de0fu;
    const std::string prefix = "THEM?!CTF{";
    const u32 final_state = target ^ 0xffffffffu;

    std::unordered_multimap<u32, std::string> right;
    right.reserve(80000000);

    std::string s(5, '\0');
    uint64_t nright = 0;
    for (char a : alphabet) for (char b : alphabet) for (char c : alphabet) for (char d : alphabet) for (char e : alphabet) {
        s[0] = a; s[1] = b; s[2] = c; s[3] = d; s[4] = e;
        u32 state = final_state;
        state = crc_reverse(state, static_cast<u8>('}'));
        for (int i = 4; i >= 0; --i) state = crc_reverse(state, static_cast<u8>(s[i]));
        right.emplace(state, s);
        ++nright;
        if ((nright & 0xffffffu) == 0) std::cerr << "right=" << nright << "\n";
    }

    u32 base = 0xffffffffu;
    for (unsigned char c : prefix) base = crc_update(base, c);

    std::string l(4, '\0');
    uint64_t hits = 0;
    for (char a : alphabet) for (char b : alphabet) for (char c : alphabet) for (char d : alphabet) {
        l[0] = a; l[1] = b; l[2] = c; l[3] = d;
        u32 state = base;
        for (unsigned char x : l) state = crc_update(state, x);
        auto range = right.equal_range(state);
        for (auto it = range.first; it != range.second; ++it) {
            std::cout << prefix << l << it->second << "}\n";
            ++hits;
        }
    }
    std::cerr << "hits=" << hits << "\n";
    return 0;
}
