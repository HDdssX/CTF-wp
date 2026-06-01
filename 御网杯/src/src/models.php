<?php

class PromoManager {
    public $promo_credit;
    public $promo_code;

    public function __construct($code, $credit) {
        $this->promo_code = $code;
        $this->promo_credit = $credit;
    }

    function __destruct() {
        if(isset($this->promo_credit) && is_numeric($this->promo_credit)) {
            $_SESSION['balance'] += intval($this->promo_credit);
        }
    }
}
?>
