package com.rois.happy_shopping.controller;

import com.rois.happy_shopping.common.Result;
import com.rois.happy_shopping.dto.UserLoginDTO;
import com.rois.happy_shopping.dto.UserRegisterDTO;
import com.rois.happy_shopping.entity.User;
import com.rois.happy_shopping.service.UserService;
import com.rois.happy_shopping.util.JwtUtil;
import java.util.Map;
import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping({"/api/user"})
@CrossOrigin(
   origins = {"*"}
)
public class UserController {
   @Autowired
   private UserService userService;
   @Autowired
   private JwtUtil jwtUtil;

   @PostMapping({"/register"})
   public Result<?> register(@Valid @RequestBody UserRegisterDTO registerDTO) {
      Map<String, Object> result = this.userService.register(registerDTO);
      return (Boolean)result.get("success") ? Result.success("Registration successful", result) : Result.error((String)result.get("message"));
   }

   @PostMapping({"/login"})
   public Result<?> login(@Valid @RequestBody UserLoginDTO loginDTO) {
      Map<String, Object> result = this.userService.login(loginDTO);
      return (Boolean)result.get("success") ? Result.success("Login successful", result) : Result.error((String)result.get("message"));
   }

   @GetMapping({"/info"})
   public Result<User> getUserInfo(HttpServletRequest request) {
      String token = this.getTokenFromRequest(request);
      if (token != null && this.jwtUtil.validateToken(token)) {
         String userId = this.jwtUtil.getUserIdFromToken(token);
         User user = this.userService.findById(userId);
         if (user != null) {
            user.setPassword((String)null);
            return Result.success(user);
         } else {
            return Result.error("User not found");
         }
      } else {
         return Result.error(401, "Unauthorized access");
      }
   }

   private String getTokenFromRequest(HttpServletRequest request) {
      String bearerToken = request.getHeader("Authorization");
      return bearerToken != null && bearerToken.startsWith("Bearer ") ? bearerToken.substring(7) : null;
   }
}
