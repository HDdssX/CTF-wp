<?php
class FileLogger {
    public $logfile = "/tmp/notehub.log";
    public $content = "";

    public function __construct($f=null) {
        if ($f) {
            $this->logfile = $f;
        }
    }

    public function write($msg) {
        $this->content .= $msg . "\n";
        file_put_contents($this->logfile, $this->content, FILE_APPEND);
    }

    public function __destruct() {
        if ($this->content) {
            file_put_contents($this->logfile, $this->content, FILE_APPEND);
        }
    }
}

class ShitMountant {
    public $url;
    public $logger;

    public function __construct($url) {
        $this->url = $url;
        $this->logger = new FileLogger();
    }

    public function fetch() {
        $c = file_get_contents($this->url);
        if ($this->logger) {
            $this->logger->write("fetched ==> " . $this->url);
        }
        return $c;
    }

    public function __destruct() {
        $this->fetch();
    }
}
?>
