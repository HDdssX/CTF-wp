package com.rois.happy_shopping.entity;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

public class User {
   private String id;
   private String username;
   private String password;
   private String email;
   private BigDecimal balance;
   private LocalDateTime createTime;
   private LocalDateTime updateTime;

   public User() {
   }

   public User(String username, String password, String email) {
      this.id = UUID.randomUUID().toString();
      this.username = username;
      this.password = password;
      this.email = email;
      this.balance = new BigDecimal("10.00");
      this.createTime = LocalDateTime.now();
      this.updateTime = LocalDateTime.now();
   }

   public String getId() {
      return this.id;
   }

   public void setId(String id) {
      this.id = id;
   }

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

   public BigDecimal getBalance() {
      return this.balance;
   }

   public void setBalance(BigDecimal balance) {
      this.balance = balance;
   }

   public LocalDateTime getCreateTime() {
      return this.createTime;
   }

   public void setCreateTime(LocalDateTime createTime) {
      this.createTime = createTime;
   }

   public LocalDateTime getUpdateTime() {
      return this.updateTime;
   }

   public void setUpdateTime(LocalDateTime updateTime) {
      this.updateTime = updateTime;
   }
}
