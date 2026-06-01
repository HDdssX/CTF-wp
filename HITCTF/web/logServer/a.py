import random
import struct

MASK32 = 0xffffffff

# ===== 还原单个 32 bit 输出对应的内部 state 元素 =====

def unshift_right(x, shift):
    """逆运算: y = x ^ (x >> shift)"""
    res = x & MASK32
    for _ in range(32):
        res = (x ^ (res >> shift)) & MASK32
    return res

def unshift_left(x, shift, mask):
    """逆运算: y = x ^ ((x << shift) & mask)"""
    res = x & MASK32
    for _ in range(32):
        res = (x ^ ((res << shift) & mask)) & MASK32
    return res

def untemper(v):
    """逆向 CPython MT19937 的 temper 步骤"""
    v = unshift_right(v, 18)
    v = unshift_left(v, 15, 0xEFC60000)
    v = unshift_left(v, 7,  0x9D2C5680)
    v = unshift_right(v, 11)
    return v & MASK32

# ===== 96bit 输出拆成 3 个底层 32bit 输出 =====

def underlying_words_from_hex96(hexstr: str):
    """
    你的 gen_secret() 是:
        secret_int = random.getrandbits(96)
        secret_bits = secret_int.to_bytes(..., 'big')
        return secret_bits.hex()
    而 CPython getrandbits(96) 内部是按 little-endian 的 3 个 uint32 拼出来的，
    所以这里要把顺序反过来。
    """
    b = bytes.fromhex(hexstr)
    # big-endian 拆开是 [w2, w1, w0]
    w2, w1, w0 = struct.unpack(">III", b)
    # 实际底层生成顺序是 [w0, w1, w2]
    return (w0, w1, w2)

# ===== 从 208 个 96bit 输出还原随机状态并预测下一个 =====

def recover_state_from_96hex(outputs_hex):
    """
    outputs_hex: 至少 208 个 96bit 的十六进制字符串（208*3 = 624 个 32bit 输出）
    返回：一个 random.Random 实例，状态与原来的一致
    """
    assert len(outputs_hex) * 3 >= 624

    words = []
    for h in outputs_hex:
        w0, w1, w2 = underlying_words_from_hex96(h)
        words.extend([w0, w1, w2])

    # 只取前 624 个 32bit 输出
    words = words[:624]

    # 逆 temper 得到 624 个内部 state 元素
    mt_state = [untemper(w) for w in words]  # len == 624

    # CPython random.setstate 需要的内部格式:
    # (version, (mt[0], ..., mt[623], index), gauss_cache)
    inner_state = tuple(mt_state + [624])  # index=624, 下一次会先 twist
    state = (3, inner_state, None)

    r = random.Random()
    r.setstate(state)
    return r

def predict_after_n(outputs, n):
    r = recover_state_from_96hex(outputs)
    for _ in range(n):
        r.getrandbits(96)
    x = r.getrandbits(96)
    return x.to_bytes(12, "big").hex()


# ===== 使用：预测第 60000 个后续输出 =====

outputs_hex = [
"99f48a2fbeb24860f1bc8c13",
"5b14bc7e783182a6537e833e",
"521e85244bbb49aca0d2131b",
"c668b974ea2aafbfc6dcb143",
"89742a0f47e010fbb82ab339",
"c855c20d9e77e5ec827c6eb6",
"fe95bdff0435b0b690b3a960",
"cbda9c3b1b877dcf40334c73",
"e486cd2363c3b2395bef71c0",
"434cf8fb3b0c784963a5bd28",
"c9f7210983256a0fb2e89370",
"95f50181894a9fe40204c64b",
"bd3e5bc39cc2dc90fbeb9920",
"35dfdbdc5e8846db84f7bde1",
"7c5ea0fc63de2acdb85b778c",
"3a77c31351c7e37c94faa7c2",
"73cc13e214dc6fc31dec6952",
"3d8f7f6f5b92bc33b9d34534",
"733be787d454b1fd08b3bb22",
"5c4e1c61c6c65408b73da5e6",
"e9a31d7afae3a4e4a4c92030",
"9979de5cb64202c9932e1c7c",
"d2b4a6a6bf9a86a2eda2826f",
"538feb89357b0de69d2bddc3",
"776c3fb57a5edce04bd60d21",
"224a7846ea0227f5a7c726ee",
"80bd34938b088c10cd5985e1",
"419945b82aad069a9f8f1f16",
"a068a305dde1db6c95174e5d",
"9e5239d801489029950ed424",
"d96e4bd5c499d50cf917bca5",
"e61ae61cfeb429a776b7cc0a",
"f78f68a79781fce82434c81b",
"2af3d3fb5950d6983b006da0",
"5f40f70817a1a2e2ba2ff3c2",
"2dda6f6f576f9a6b9bafd0bb",
"6f6b6be4cbdba000692fe143",
"6045917babfff59ac1d0b946",
"8244ce4f448bdaee9ab9fde5",
"35a738b4f480df30189e187a",
"8156d4060596c20d0bd47d82",
"cc79bdb78c5bbdddcc096aef",
"72c47383d03bf600b5df6661",
"845b3cefadcb835a96b40d7d",
"2119b893a86671149115a445",
"b86e170f155d33a33138e63b",
"583f8423969dc6e4f1926b8d",
"e515bd75a91ff5eb8e78d954",
"7d885ef4f0cb3525dabb1a5b",
"2b38297f799781cc6d54f86b",
"124609a2c29e66d57c4e7498",
"1b814eb46e60e6d55a2b5ef0",
"dee4f7b6819a42561ccae9b2",
"a88c3e6101b34df2532d5456",
"dfba7f1a75eab727f0e8da58",
"a163cf05547f78c036d65829",
"9ff62d9275d6666ccf1ed4d0",
"7c768de8e823b32baf5639c5",
"feb120318a809d0837018a43",
"7820594645dcb8323d7ff0ec",
"a0b91be1be29b7f115322d7f",
"54af3327e15b7f61ec8ce055",
"ed8b0baa7f233aeb774aeaa9",
"e6ca4a1d9634bc83254550b2",
"ff41d58370a5447e28cadeb1",
"beff8d1ab864673becbdba98",
"824fd3d2867d87550909672d",
"91274a197182741267e10aa8",
"a05a48fdf26fc59a7ac64f06",
"cef51bef4d022b4966004033",
"b51d96cdf1b6083bcfaee6bc",
"525a630c74f769b1dfc944a0",
"06f763a5e574e83f99ccd57d",
"76459be025dfa35a8ef0c0fa",
"d73ce40dd172da6c4ca2a7e1",
"f5dda507f86c337fb277d2bd",
"87648277adc4e4331dae7458",
"5a811ad23602d3fb5c14125e",
"4d150dadaff2e31dedd02d50",
"9bad7ce2cf71151cdfb855e2",
"59cac0aff042b5c08e86493b",
"e34ed72f4eaa7f3312ae7f31",
"ff68dbaed9b9b65360e507ca",
"c71327e2b82233ce93923126",
"83c4e3f01dad8f82c9e7e5be",
"ed2f4d3bd9361bf770cb1469",
"4321f83a5c36473d3b8204af",
"ee46e920ab6fb0a3b7bd52a0",
"835924be8e3808ecf9cd0d75",
"3ab4189bf619c779f0065b3c",
"50466532c504e8e37fe56623",
"a95a082a20ed5aa6e924f4cd",
"facf509959790ebfe0aace9a",
"7b592ee015604ca7fb6bdbb4",
"619fbd11f4755137bfb2859a",
"0f24080f66485fdca19a1999",
"15f44bfc856432de878a8ce6",
"75ab3c9ece0345476d94f0af",
"8d3d09576007ecbc48b83cf6",
"db412ea5d46a5a077d9c9d4b",
"5d96d61202c6a876e4e269e6",
"60424e9a49a8a8a59d164f83",
"da2cf0a3ed4f999b055b4c36",
"d8b248f4449459aa61bdf32a",
"bb4e3a874c143270381044b5",
"49001b2bd240137d282033f7",
"a36f66e624dee8756b09d74c",
"994f75c12550a841da164ec6",
"a7cb16c722e57780af08bef9",
"084a8217cbbf2b133f988dbb",
"c455af975770fb9919b09f3f",
"b665cf4f49c09a4a4f16c786",
"2d9ca0ddba85ea2519f50b78",
"99d85a6def55bc74aaed2dde",
"cd4b0cb15134036ba152de06",
"bb6f128211168fda91117cc3",
"801e39eaa51b223a947a6170",
"1152baa34437a191ca845db7",
"f6ab58382a71ca4059730932",
"304b5ebfcb10b05195a5e4a2",
"dac5b17c9894c06dd0cbdc75",
"83541a4e3d074ae0f3a2ea61",
"21c2306f564cbb9975189b44",
"6cd72ae3cd2eb03ff93b403e",
"3eebec0944df8aec8fdbd575",
"1e73cc3803c772dfc77351a4",
"14a3cffbe4940d6d013b2001",
"34c5fdebc580af3b140c097a",
"1b83b550b6dcc3dc4448acde",
"bc6c6db53b2a7436795094a7",
"86d7ba475c58db54fea9c06a",
"4f7e7a317d3ecc106318b9d4",
"1cca471911f428b1566d3563",
"c817d786bd74238f2877d977",
"712ababe3c27b36b17dad779",
"2a0a31312790c97b88e0b4ca",
"c11705652075c95a1b1905bb",
"58deb0e30a403ec5a33d9ce6",
"a9b2a950efa1b8bc83bcc671",
"47e164cfcf2c42725925af1f",
"0347e6bf750755d271aeb2b9",
"73e37e8960544a06965b5548",
"9185239aef00a6a8c91ec827",
"198b73b17fa67ab6e56dca7b",
"0f5f0f0386098d095cfcb0d3",
"5ef1f30a8ce8142703c627dd",
"af4d2e6a2667b5d7d99e8029",
"7f983c8dcd8b14a04c3f66e0",
"991f6ef3f505c959df532d7c",
"6c06381ef05647f6a1130bc1",
"7a4e091406524bc4bce7a0d8",
"b710938cd7df89c0361224f0",
"ff909f0fcd870a460ad281c3",
"5bb3f29ddb0fade4a3fd46e9",
"952ca807a30bee1842cfde4f",
"2e763d93577f8c3de960b238",
"b67d3d8c3943f500103a0b81",
"165df6ab8234dc768a98a43f",
"7bf79e1cca4a94618dea9ead",
"c10e11dfe13c46e10401e2e1",
"4df9be534bd919d5f613cc65",
"44e8bff05bc174a7a388f2b8",
"588b27f1635288cb5edacd0b",
"239408550a4d1e7a809342c0",
"7326bbb66227cb418ca36099",
"6d615f895fcfc3a5a6873a0b",
"6b9edbb36f8a615a831d6ab3",
"2689888b3ce9212c380222b8",
"5aea9893394ce5c57221d9c6",
"49462ccb7468aa05e91eda1b",
"6d10b1d66aec9804c73002d5",
"8b5ac86480a826c78f238759",
"c2fdd1b6d9057417b2ba83f8",
"f447275b19f07bf4c5c53393",
"ea809d740ed2877d25945eb3",
"a0e21d6a1828cdbfa1c5f17a",
"6304b2a0507f87010b335770",
"de111b61670b67512d8ed6ca",
"7bc19ddd3151ba73a1b6e509",
"9d8c0645d46cf44417657002",
"9be77f93eb85d2dad266810c",
"492118efdc7d29397ebc906f",
"bf6c4a3d1cb11bcb090ad8cd",
"59336383a0bd8ae5f0ed5e3b",
"0cdf9658713cfc091a70206f",
"83c8927d012f41ba8739b1c0",
"cc4041fbd0d876a52f198f64",
"cf8741e7d19df9a29d00c19d",
"3863af6772d67cb4a1cbeab9",
"b70950b7a67f3b13e0908d61",
"9d88181aaec0b91a5018d1b9",
"62c64d0d5ffc6c36efe20b1c",
"8f4f8979650c667597207c33",
"0652ef35d41e0e6ae6002169",
"cda7d887993a34cc859c1040",
"915d1b1e912b2246a75273b9",
"aefeb384d28f9699c2183094",
"2011b6db125d0e5d441c171b",
"6c764694bc50ce14ec6fbcf0",
"9b23a868c346f687ffe93310",
"0b94cc538830335c012aba88",
"534ef65f773ee8150913b084",
"bbe56bb77b2430f1d2a4a12c",
"03b8a212cab22c34d8da73f1",
"cd9be3932b05c679cd485d47",
"4557e9fc5c7e2bedb797aa7e",
"c9c3948bbd3be7d55df1eb4f",
"aa9e4f61d2ab637bc42469cd"
]
print(predict_after_n(outputs_hex, 90000))

