<?php
define('DB_FILE', '/tmp/notehub.db');

if (!file_exists(DB_FILE)) {
    $db = new PDO('sqlite:' . DB_FILE);
    $db->exec("CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)");
} else {
    $db = new PDO('sqlite:' . DB_FILE);
}

