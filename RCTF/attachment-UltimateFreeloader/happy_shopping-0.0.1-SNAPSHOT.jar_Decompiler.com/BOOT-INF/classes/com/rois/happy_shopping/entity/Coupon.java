package com.rois.happy_shopping.entity;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

public class Coupon {
   private String id;
   private String userId;
   private String name;
   private BigDecimal discountAmount;
   private Boolean isUsed;
   private LocalDateTime expireTime;
   private LocalDateTime createTime;
   private LocalDateTime updateTime;

   public Coupon() {
   }

   public Coupon(String userId, String name, BigDecimal discountAmount, LocalDateTime expireTime) {
      this.id = UUID.randomUUID().toString();
      this.userId = userId;
      this.name = name;
      this.discountAmount = discountAmount;
      this.isUsed = false;
      this.expireTime = expireTime;
      this.createTime = LocalDateTime.now();
      this.updateTime = LocalDateTime.now();
   }

   public String getId() {
      return this.id;
   }

   public void setId(String id) {
      this.id = id;
   }

   public String getUserId() {
      return this.userId;
   }

   public void setUserId(String userId) {
      this.userId = userId;
   }

   public String getName() {
      return this.name;
   }

   public void setName(String name) {
      this.name = name;
   }

   public BigDecimal getDiscountAmount() {
      return this.discountAmount;
   }

   public void setDiscountAmount(BigDecimal discountAmount) {
      this.discountAmount = discountAmount;
   }

   public Boolean getIsUsed() {
      return this.isUsed;
   }

   public void setIsUsed(Boolean isUsed) {
      this.isUsed = isUsed;
   }

   public LocalDateTime getExpireTime() {
      return this.expireTime;
   }

   public void setExpireTime(LocalDateTime expireTime) {
      this.expireTime = expireTime;
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
