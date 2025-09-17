package com.rois.happy_shopping.dto;

import javax.validation.constraints.Email;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Pattern;

public class UserRegisterDTO {
   @NotBlank(
      message = "username cannot be empty"
   )
   private String username;
   @NotBlank(
      message = "password cannot be empty"
   )
   @Pattern(
      regexp = "^[a-zA-Z0-9]+$",
      message = "Password can contain only letters (A–Z, a–z) and digits (0–9)"
   )
   private String password;
   @NotBlank(
      message = "email cannot be empty"
   )
   @Email(
      message = "incorrect format of email!"
   )
   private String email;

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

   public String getEmail() {
      return this.email;
   }

   public void setEmail(String email) {
      this.email = email;
   }
}
