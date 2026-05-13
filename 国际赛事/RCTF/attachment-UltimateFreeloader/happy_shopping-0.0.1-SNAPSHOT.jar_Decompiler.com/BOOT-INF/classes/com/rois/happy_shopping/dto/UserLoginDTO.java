package com.rois.happy_shopping.dto;

import javax.validation.constraints.NotBlank;

public class UserLoginDTO {
   @NotBlank(
      message = "username cannot be empty"
   )
   private String username;
   @NotBlank(
      message = "password cannot be empty"
   )
   private String password;

   public String getUsername() {
      return this.username;
   }

   public void setUsername(String username) {
      this.username = username;
   }

   public String getPassword() {
      return this.password;
   }

   public void setPassword(String password) {
      this.password = password;
   }
}
