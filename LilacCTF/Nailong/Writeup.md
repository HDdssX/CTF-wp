# LilacCTF - Nailong CTF Writeup

## 题目信息 (Challenge Verification)
- **URL**: `http://1.95.143.126:8501/`
- **平台**: Python Streamlit Web App
- **核心机制**: 用户上传 PyTorch 模型文件 (`.pth` / `.pt`)，后端加载并显示模型结构或参数。
- **漏洞点**: PyTorch 的 `torch.load` 默认使用 `pickle` 反序列化，且 application 设置了 unsafe=True (或默认行为)，但后端部署了一个极其严格的静态/启发式扫描器 (Heuristic Scanner)。

## 路由与行为分析
1. **GET `/`**: 显示文件上传界面。
2. **POST `/upload` (推测)**: 处理上传的文件。
   - **Check 1**: 文件格式检查。如果不是标准的 PyTorch Zip 格式 (Magic Number mismatch)，报错 `Broken my detector!`。
   - **Check 2**: 安全扫描 (Security Scan)。解析 Pickle Opcode，检查黑名单 (Blacklist)。
     - 黑名单包括: `os`, `system`, `eval`, `exec`, `subprocess`, `platform`, `popen`, `timeit` 等危险函数和模块。
     - 如果检测到特征，报错 `Hacker detected!` 或 `Nice try...`。
   - **Execution**: 只有通过上述两步，才会调用 `torch.load()` 触发 RCE。

---

## 解题全过程 (Payload Iterations)

### 第一阶段：格式试探 (V1-V8)
此阶段主要尝试各种 RCE 方式，但由于上传的是 Raw Pickle Stream（普通 pickle dump），导致后端无法解析 PyTorch Zip 结构。
**报错**: `Broken my detector!`

*   **V1**: 基础 `os.system('id')`。
*   **V2**: `subprocess.Popen` 反弹 Shell。
*   **V3**: `posix.system` (尝试绕过 `os` 关键字)。
*   **V4**: `pdb.os` (利用调试器模块引入 os)。
*   **V5**: `timeit.timeit` (尝试执行代码字符串)。
*   **V6**: `builtins.exec` 直接执行。
*   **V7**: `builtins.eval` 执行配合 base64。
*   **V8**: 利用 `apply` opcode 调用函数。

### 第二阶段：格式修正与黑名单对抗 (V9-V14)
从 V9 开始，我们意识到必须封装为 PyTorch Zip 格式 (`torch.save` 或手动构造 Zip)。报错变为 `Hacker detected!`，进入真正的 WAF 对抗。

*   **V9**: 标准 `torch.save` 保存一个带 `__reduce__` 的恶意对象 (调用 `os.system`)。 -> **Detected**
*   **V10**: 尝试 `subprocess.check_output`。 -> **Detected**
*   **V11**: 手写 Pickle Opcode 并注入到 Zip 的 `archive/data.pkl` 中，避免产生不必要的 Python 字节码元数据。 -> **Detected**
*   **V12**: `platform.popen`。尝试生僻模块。 -> **Detected**
*   **V13**: `sys.modules['os']`。试图通过 `sys` 模块获取已加载的 `os` 对象。 -> **Detected**
*   **V14**: Hex String Encoding。将 "os" 和 "system" 字符串进行 Hex 编码，试图绕过字符串匹配，但 Opcode 里的模块引用 (`cimport`) 无法隐藏。 -> **Detected**

### 第三阶段：深度混淆与 Gadget 挖掘 (V15-V19)
尝试各种间接调用和逻辑绕过。

*   **V15**: `torch.os.system`。利用 `torch` 自身暴露的 `os` 模块 (在旧版本或特定环境下可行)。 -> **Detected** (扫描器可能对 `system` 敏感)
*   **V16**: 字符串拼接。在栈上通过 `('o'+'s')` 拼接模块名。但 `STACK_GLOBAL` 需要明确的 Module/Name。 -> **Fail**
*   **V17**: `pathlib.Path().write_text()`。尝试不执行命令，而是写 Webshell 或 SSH Key。 -> **Detected**
*   **V18**: `operator.attrgetter`。利用 `operator` 模块获取属性。 -> **Detected**
*   **V19**: `pydoc.locate` + `codecs.decode`。
    - 思路：`pydoc.locate` 可以根据字符串导入模块。
    - 结合：利用 `codecs.decode(hex, 'hex')` 动态生成 "os.system" 字符串。
    - 结果：依然被杀。推测扫描器 hook 了 `pydoc` 或者严查 `import` 行为。

### 第四阶段：最终解法 (V20) - 侧信道引入 (Side-channel Import)
利用 Python 标准库中必然会引入 `os` 的良性模块，通过 `__globals__` 偷渡。

*   **V20 Strategy**:
    1.  **宿主模块**: `logging`。这是一个极其常用的日志模块，几乎所有 Python 环境都会加载，且它内部必须使用 `os` 模块。
    2.  **获取路径**: `logging.getLogger` -> `__globals__` (字典) -> `'os'` (模块对象) -> `'system'` (函数)。
    3.  **字符串隐藏**: 全程不出现 `"os"`, `"system"`, `"__globals__"` 明文。
        - 使用 `codecs.decode('...hex...', 'hex')` 在运行时还原所有属性名和键名。
    4.  **Opcode 构造**: 手动编写 Pickle Opcode，实现上述逻辑链。
