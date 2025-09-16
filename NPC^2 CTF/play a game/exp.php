<?php
echo (md5($_GET['id']) == md5("114514") ? 1 : 2);
var_dump($_GET['id']);
