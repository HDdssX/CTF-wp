package com.hitctf.controller;

import com.hitctf.util.SecureObjectInputStream;
import java.io.ByteArrayInputStream;
import java.io.ObjectInputStream;
import java.util.Base64;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class IndexController {
   @GetMapping({"/"})
   @ResponseBody
   public String home() {
      return "Welcome to HitCTF!";
   }

   @PostMapping({"/unser"})
   @ResponseBody
   public String unserialize(@RequestParam("data") String data) throws Exception {
      ObjectInputStream ois = new SecureObjectInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(data.getBytes())));
      return ois.readObject().toString();
   }
}
