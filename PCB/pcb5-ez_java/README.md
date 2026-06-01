附件：

```bash
RewriteCond %{QUERY_STRING} (^|&)path=([^&]+)
RewriteRule ^/download$ /%2 [B,L]
```