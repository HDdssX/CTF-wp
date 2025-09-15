## 签个到吧
```php
<?php

$this->a = &$this->b
```
## not_ezphp
```php
<?php
# Try to read flag.php

if (isset($_POST['file'])){
  echo hash_file('md5', $_POST['file']);
}
```