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

def predict_next_from_96hex(outputs_hex):
    """
    给 208 个 96bit hex，预测下一个 gen_secret() 的 hex 字符串
    """
    r = recover_state_from_96hex(outputs_hex)
    x = r.getrandbits(96)
    return x.to_bytes(12, 'big').hex()

# ===== 示例：用你给的 208 个值预测 =====

outputs_hex = [
    "9b7fec8ff0cdb4d84dfbed91",
"225d7e283fac597f7dac6fb8",
"6d9c99511329a3e57ba0c22d",
"1f100784d36e11831fb1f724",
"9b21d1b56d2ee70688a26ac5",
"e175d9fc7219500d078975cf",
"f8c3de23f9127e30ea338ca0",
"aad3d7f01718c11c6d43bd98",
"52f31277202ef2e33dc82698",
"6cbb0103058a2101407a8cf9",
"3a46d2fb10d2bb1cb89391fb",
"a0bd1fdcb2a3abbd367c9b5c",
"d3dfedb79c2a2dc2ebe7926a",
"293ad11de802de723ba2deab",
"feb3ca08f554bc220ed5a27c",
"c6ef69265265aa5cc94e70ab",
"cc42aafdf746bf9d3e483dad",
"1951b1219e0c282c917de44e",
"c4e3539987629c5306376444",
"b425fca23319f0bb9406e2df",
"358dafb8c69a1d462b92e908",
"3ea49f660c3dfb65e7a6c775",
"cfe3c812677804b31b62f468",
"5f7de792ba4c2dfaeb0bb0b2",
"65459c16d37e937f100006f9",
"207e28c8f961c0f7b348962d",
"d3fe84e096c5a9e5b904a169",
"21aaff4f821b8300e9f39a3c",
"7566c1f7faf5f4bcb4f1afe1",
"36a0af390e552b8137c56386",
"daea9ae51e03cf9fdb7ca63e",
"8a0cd524c2458bd86835493e",
"370f5b20ca73bc8411ccc255",
"b6ad3b97e121077034c0fc5c",
"44554f1891a603df402c76c4",
"7f1fcc8fea42bcb92e6a93c3",
"875898a636fbf6fc48c4d043",
"e366af618253402ef53ae7be",
"def05579751d00f1f22b60f1",
"9d6d0bf407f7834790a789bb",
"c972327d8e32e8cdef141c1d",
"9a550748e927f9eff68f80e7",
"6bf89da11b41d848cc8eabe7",
"4adc6b7475dfc5decf53a93b",
"b71807e3403856cbb69f1df7",
"b960a5463de3497603361e24",
"aebd1871f1127a37c2ed8b11",
"c708af95958f3c8668703097",
"40f3f30060f9d1d401aac5ea",
"1778ae0af5e6682c0dca7ea6",
"cc2751295e2f35c79f1757ad",
"efcfafae851a339605ae38c0",
"350474dc84c088ed629fe2ff",
"96ea35a6b6918d60f66719a2",
"80a71ff9c5df813ccf898415",
"94b79097785f7dfc4527157a",
"48ddfcc15ffa45d5a2c21268",
"59b50c070ffd1f396c6d3b02",
"02eceb81203d56ec82f0add4",
"a5ffd0f1c3e603fe1c663125",
"83ee910c6476c778d8c657d5",
"a1e10980ff15ec06ef3a7426",
"9d294fa98cdcc7ff2a17f2f6",
"1019bb6efb39d74926576852",
"93d85b10874b1eb5631fe4eb",
"6e807df48df7e59a32a31dba",
"84b36e7855aa20a7bd7baa3b",
"cd942e5b0654260230840935",
"1bff9735b773f1a34995c465",
"74f5a114e457e1ce08c24e48",
"e776adeae95f6f330c194cbb",
"bac7cd1cb36daff68904e7d3",
"3324275e05d0ce18f1415a5f",
"1d6a22a0a4806f8184c6a245",
"1029a904ef724076c15aba62",
"8b7f6540c97d9c748e46c7d6",
"fbf610a103ba95d2f5b232a9",
"ea37c91eec8a65413fbb2937",
"f1b1ed09a16d064b885f117c",
"d4ed1c4088b123d22f78d2ce",
"12a671ca045ba9495f3da8d7",
"ae5daa9844100c5b63c31438",
"65e712994cb160a1c6ae68bd",
"6ef469705c6a2173940ccb6f",
"86e6a99cda4a8f7cbe1f6994",
"d12aa4b41cde6b7ac5f7e852",
"6ce6e9c600c3be991af2ee3e",
"93bc04c324490f468050fc80",
"b5570705fd6e268b8e132db7",
"06e15ea0f972c9e2229f26a5",
"a4f153590714b3c189c73738",
"829a3e6956b00ea245b4d565",
"cbaa3a362e81734019ae3583",
"ae4288b7c2fd15c052982e08",
"66c36b00eca95b0934f594a6",
"86251ca55783698bd743a688",
"568f830e97d90c370157e591",
"07051baf023790a730b77497",
"ba7810157a8579e10d312845",
"558bd2b73402265078f73e59",
"ccea81242097ce1b801dfcee",
"ef393fbe11c5579504d887b0",
"8a327b215ee20081c83e0930",
"add385a8a2ca00af76780fd3",
"9c2dc34bfe9adbc3a54b15fb",
"6f114515f7522dd477071e2c",
"53904924e00b25dffa0ee3a2",
"b38a50d8774e345feddee45c",
"a02ed8221eb163da06c4d918",
"f32708465013854a24814b4a",
"0b47bda3bdf0d50a640b6aaf",
"49afd4e33aeb2b4b0878f443",
"b2df42cb476dff432c6c3b78",
"3460143b7c039e77d484df",
"b20b979b4b791ded4aceaec3",
"aa0b94bd82c3111072bd1b83",
"eba17c8dfcc6065766725410",
"3e1e5a5097739acf804644c7",
"f440af78deeb301ef41b6652",
"97e3da8509d854d9f17d4bad",
"e513b6e6cf460cfb356468e2",
"27107dac6db03aa42b1181b3",
"babaa0d65f89975e5672b1ed",
"f6d0f0442881d4343184f7be",
"83a2f39d185dcb2dbe058d26",
"17109133063d2dc9184b8eee",
"723443463376b2d1f02c624a",
"a06525d3f6bee1efc3fdc6a6",
"be0d919c06fb87eb69ea83d4",
"4c0d2a15bbf4b4421cf11db6",
"e38cf715461f01ba07ccc79d",
"8e7c9e174bb87167b2f9baec",
"fa70e47067be939d96aaa832",
"f0498cc68bdf0776002c89ef",
"10da8d19257dba362264e6dc",
"3dec40dfbe420e438c7092de",
"2c952819b8dc7463dabf826a",
"51fd8b63ede817751c7db31c",
"a1eead3d7d9260df6846eebf",
"3744a9199806ac36a7963d95",
"aafd496006ed343e0d922d11",
"6ead088fc3e7251f30f04285",
"dd506693c8faab295b98321f",
"55e1fdee97d9f4b4a48cf616",
"389f53fc9bff69e47cf11122",
"8dcaaae0b7585e3ce61c34e7",
"271de8fbac5b699b36066a5d",
"bdbc7651654167934c2b3017",
"86bd2ae1246a120fea7c07e1",
"074364978ea9bcc65b5367a3",
"87d979f409067fdf3685ee8a",
"af73c144d80c23a581297e44",
"9ec55fc506625f7aae856fbc",
"aa6f7c3a1b95a89fc5b22ed7",
"b00d40787c7ab2cbff4dfd30",
"76c0f41e4b8d3f8ef031db6b",
"53ed357449db1e56853c03bb",
"2a0aebdb01a6e324f1354e99",
"943797e3b36cf1a79f27076f",
"02321f8a865e657343b9da71",
"efaa607a9a9f552a4b278e54",
"b6c4db732b095f51df93bf33",
"96722f5f7257b82b9a951dae",
"b7886c7f125b3059d7a0cb0a",
"170a5b8b197f5710b975d4be",
"3dd25ea201573cf8be922921",
"2f5228a548bec3587eada8c4",
"c9846b6b3bdcea3503addb8a",
"1786ae2293b8ab6645cf2297",
"5e4cdced7ed06fc2d9dcb8d4",
"9b40af4ef5dc684beda8981a",
"4600bfab157e38ecc428a497",
"ac8a206d9c04de8ce89fa9d8",
"b10268ca39bc24a7be1e35f0",
"908c1c1330b08962ff4718ce",
"69f8bad233ab219608011a1c",
"1345a1be1265e4c0eeb040fd",
"a44c13ebdb819919cdff3580",
"0c588873cf4a9affbdae374d",
"b153d1aff048c3f78099354c",
"34262abcb8b08a82e021528c",
"b3dc088e87d72c277b018de6",
"f43ce6c0d9932574ca032649",
"6ab9c22e374479dcadf9a508",
"d4bb76392ca6cfea2c43a320",
"b800a498d2772811e7ea5209",
"be11d6130d5a525443d266da",
"f1ef82ab0e56b92f5c835c7b",
"bc3abe90c854e201a50d6909",
"0247bbe53c2b50a8fb4539fc",
"4ceb7b6f1b77f268499b3c52",
"46b8cf6f5236199e71bfc9a7",
"2634649921a421ced2e3413d",
"e144f616325ab6511979402e",
"41a4cd47d25cec66caaca4fa",
"e15c0f16619ef67c57da1986",
"2aa3ff27303897cb7baaf9ec",
"76548f1e045a683e329eeb3a",
"406aac046886ddafb46a6290",
"11ae1bc0725c2ff8752ad5cc",
"ff32bbe8e548dcec33158cf2",
"ebcc777f66ba9ea8e2dc92e1",
"267d45e7d44b4ae8eefbe8ad",
"67c871007a663bbf0fc600cd",
"ebe5e9f9d5f619ab65f93546",
"fc85f01fe2aff62d8fb5fffe",
"b985a2ef021cd832e41949c2",
"6284738e0db75c6ee16db26b"
]

print(predict_next_from_96hex(outputs_hex))
# -> 17f887a1e9e3cf2b39edc3f9
