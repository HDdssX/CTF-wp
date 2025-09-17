# Week 1

## headach3

in header

## 会赢吗

1. html中的注释

```html
<!-- flag第一部分：ZmxhZ3tXQTB3，开始你的新学期吧！:/4cqu1siti0n -->
```

2. `javascript`

```javascript
fetch('/api/flag/4cqu1siti0n', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    }
})
```
```json
{"flag":"IV95NF9yM2Fs","nextLevel":"s34l"}
```

3. 修改 html 元素

```html
<span id="state">解封</span>
```

`第三部分Flag: MXlfR3I0c1B, 你解救了五条悟！下一关: /Ap3x`

4. javascript

```javascript
document.querySelector('form').addEventListener('submit', function (event) {
    event.preventDefault();
    alert("宿傩的领域太强了，有什么办法让他的领域失效呢？");
});

(function () {
    const originalConsoleLog = console.log;
    console.log = function () {
        originalConsoleLog.apply(console, arguments);
        alert("你觉得你能这么简单地获取到线索？");
    };
})();
```

```http request
POST /api/flag/Ap3x HTTP/1.1
Host: 127.0.0.1:48461
Content-Type: application/x-www-form-urlencoded
Content-Length: 38

csrf_token=hfaousghashgfasbasiouwrda1_
```

Content-Type好像只能大于38（即当前长度）才能成功

```json
{"flag":"fSkpKcyF9","nextLevel":null}
```



















