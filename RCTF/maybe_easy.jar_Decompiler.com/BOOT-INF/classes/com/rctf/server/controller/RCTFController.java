package com.rctf.server.controller;

import com.rctf.server.tool.HessianFactory;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class RCTFController {
   @RequestMapping({"/hello"})
   public String hello(@RequestParam(name = "data",required = false) String data) throws Exception {
      Object obj = HessianFactory.deserialize(data);
      return "hello";
   }
}
