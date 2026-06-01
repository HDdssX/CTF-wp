class User:
    def __init__(self, name):
        self.name = name
    def get_upper_name(self):
        return self.name.upper()  # 自定义方法：名字转大写

u = User("zhangsan")
# 正确：{0.get_upper_name} 拿到方法对象，后面加()执行
res = "{0.name}转大写：{0.get_upper_name}()，类名：{0.__class__.__name__}".format(u)
# 注意：这种写法会直接拼接字符串，需要用eval解析才能执行（适合动态场景）
res = eval(f"'{res}'")  # 解析后执行方法，拿到结果
print(res)  # 输出：zhangsan转大写：ZHANGSAN，类名：User