呃也是拿到邀请码了啊，现在还差个 rce，可能要 vm2 3.11.2 逃逸，感觉更像是别的
[progress.md]
[AGENTS.md]

当前状态: 未拿到最终 flag，先整理已确认的利用链和排查过程
1. Reviewer 邀请码存在 Mongo 查询注入 Oracle
入口在 reviewer profile 导入逻辑。
[lib/profileImport.js](C:/Users/29703/Downloads/ACTF/AAA'26/paper-submission-system/lib/profileImport.js) 中：
JavaScript
return {
  queue: policy.queue,
  slotField: SERVICE_DESK_CREDENTIALS[policy.credential] || SERVICE_DESK_CREDENTIALS.invitation,
  slotValue: valueAtPath(record.retainedMetadata, fieldPath),
  recordId: record._id
};
继续往下：
JavaScript
return {
  used: false,
  track: submitted.track,
  kind: packet.queue,
  rubricId: rubric.rubricId,
  [packet.slotField]: packet.slotValue
};
这里 slotField 固定会变成 code，而 slotValue 来自上传的 JSON：
JavaScript
committee.registration.reference
这个值没有做类型限制，直接进入 Mongo 查询，所以可以传：
JSON
{
  "committee": {
    "registration": {
      "reference": {
        "$regex": "^abcd"
      }
    }
  }
}
然后调用 /reviewer/profile/service-sync，返回文案会区分：
• 匹配成功: Committee service desk has an available assignment slot.
• 匹配失败: Committee service desk has not found an assignment slot yet.
于是可以把 reviewer invite code 一位一位爆出来，但这不是爆破登录，而是利用题目自身的匹配 oracle。
2. Reviewer 邀请邮箱和规则可以从 seed 里直接确认
[lib/seed.js](C:/Users/29703/Downloads/ACTF/AAA'26/paper-submission-system/lib/seed.js) 中写死了：
• reviewer 邀请邮箱: committee-shadow@aaa26.big1
• code: crypto.randomBytes(18).toString('hex')
• track: systems
• kind: overflow
• rubricId: big1-overflow-systems
同时 rubric 要求：
• requiredAreas = ['systems', 'review process', 'artifact sanity']
• minimumScore = 37
所以 reviewer profile 需要满足：
• track=systems
• areas 包含 systems, review process, artifact sanity
• score >= 37
3. 真实复现结果
我已经在当时的在线环境里复现到 reviewer 身份，拿到了一个 reviewer 账号：
• 用户名: u20f4a707
• 密码: passw0rd!
并且当时在线环境里爆出来的真实 reviewer invite code 是：
Plain Text
e7a03bc28805ae19c04a9b6b655feb7b7896
拿到 code 后可正常走：
• /reviewer/claim
把普通用户升级成 reviewer。
升级成 reviewer 后能做什么
1. 可以查看 reviewer backlog
/api/reviewer/filter 能返回 reviewer 的分配论文和评分信息。
2. reviewer 对论文查看/打分的权限边界比较松
[routes/reviewer.js](C:/Users/29703/Downloads/ACTF/AAA'26/paper-submission-system/routes/reviewer.js)：
• /reviewer/papers/:id/review
• /reviewer/papers/:id/review POST
这里只检查了角色是 reviewer，没有检查该 reviewer 是否真的被分配到这篇论文。
[routes/papers.js](C:/Users/29703/Downloads/ACTF/AAA'26/paper-submission-system/routes/papers.js)：
• /papers/:id/view
只要是 reviewer，就能看任意 paper id。
所以可以直接枚举/猜测论文 ObjectId 查看内容。
已确认能看到种子论文，例如：
• 69ffdb9cd240969888697371
• 69ffdb9cd24096988869737a
但这些只带来了信息泄露，没有直接通向 admin 或 accepted。
后续主攻方向
1. Camera-ready 链
[routes/papers.js](C:/Users/29703/Downloads/ACTF/AAA'26/paper-submission-system/routes/papers.js) 中：
JavaScript
if (paper.ownerId.toString() !== request.user.id || paper.status !== 'Accepted') return reply.code(403).send('Forbidden');
只有 accepted paper 的 owner 才能走 camera-ready。
[lib/cameraReady.js](C:/Users/29703/Downloads/ACTF/AAA'26/paper-submission-system/lib/cameraReady.js) 会调用 pdf-image / ImageMagick / Ghostscript 处理 PDF，理论上这里很值得打，但前提是先拿到 accepted 权限。
2. Reviewer 搜索用了 vm2
[lib/filters.js](C:/Users/29703/Downloads/ACTF/AAA'26/paper-submission-system/lib/filters.js)：
JavaScript
const vm = new VM({
  timeout,
  sandbox: { item }
});
表达式来自 reviewer 可控输入：
JavaScript
Boolean((() => (${expression}))())
这显然是题目另一个高价值入口。
vm2 分析结果
1. 本地依赖版本
源码 package.json 标的是：
JSON
"vm2": "^3.11.2"
2. 本地对拍
我专门本地装了：
• vm2@3.11.1
• vm2@3.11.2
然后验证了多条官方 advisory 对应的 PoC。
结论：
• 3.11.1 上至少一条 null-proto PoC 能直接拿到 process
• 3.11.2 本地测试会被拦住
其中一个本地可用的 3.11.1 逃逸原型是：
JavaScript
const o = { __proto__: null };
try {
  throw o;
} catch (e) {
  e.f = Buffer.prototype.inspect;
  const p = o.f.constructor('return process')();
}
3. 远端现象
远端 reviewer 搜索环境中：
• typeof Buffer !== "undefined" 为真
• 一些 constructor("return this")() 级别探针是可触发的
• 但 constructor("return process")() / constructor("return require")() 这类关键跳板都失败
这说明线上环境和题目源码呈现出的 vm2@3.11.2 状态不完全一致，至少不能简单按附件里的依赖版本去套现成 exploit。
静态文件 / 路径穿越排查
还排查过：
• /flag
• /public/../flag
• 各种 %2e%2e 编码绕过
• 上传文件名里夹带 %2f%2e%2e 的静态路径变形
现象是：
• 部分路径会返回统一的应用层 404 页面
• 部分路径会被前置 openresty / 静态层直接 400 或 403
• 没有形成稳定可读 /flag 的穿越链
当前结论
这题已经稳定确认了一个真实漏洞链：
1.  利用 reviewer profile 导入的 Mongo 查询注入
2.  通过 service-sync 文案 oracle 爆出 reviewer invite code
3.  成功 claim reviewer 身份
但 reviewer 之后到最终 flag 的最后一步还没有闭合。
最可能的原因是：
• 线上依赖版本/补丁状态与附件源码不完全一致
• 题目的最终预期链大概率仍然和 vm2、accepted/camera-ready、或部署差异有关
目前可复用的价值

• 这份附件源码已经足够确认 reviewer 提权链是真实可打的
• 如果后面拿到更完整的部署依赖快照、node_modules、hint，应该能继续收敛
• 当前 reviewer 身份和线上行为差异，说明这题不能只按源码静态审计，必须结合远端实际环境继续验证

