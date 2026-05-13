<?php
namespace Session;

class User
{
    private $username = "admin";
}

echo base64_encode(serialize(new User()));